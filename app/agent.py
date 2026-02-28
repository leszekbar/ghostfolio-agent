from datetime import datetime, timedelta, timezone
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.schemas import ToolResult
from app.tools import ToolContext, get_performance, get_portfolio_summary, get_transactions

DISCLAIMER = (
    "Disclaimer: This is not financial advice and is provided for informational purposes only."
)

ToolName = Literal[
    "get_portfolio_summary",
    "get_performance",
    "get_transactions",
    "compare_holdings_performance",
]


class AgentState(TypedDict):
    query: str
    session_history: list[dict[str, str]]
    selected_tool: ToolName
    tool_args: dict[str, Any]
    tool_context: ToolContext
    tool_result: ToolResult
    response: str
    tool_calls: list[str]
    verification: dict[str, Any]
    confidence: float


def _extract_range(query: str) -> str:
    query_lower = query.lower()
    if "1d" in query_lower or "today" in query_lower:
        return "1d"
    if "5y" in query_lower or "five year" in query_lower:
        return "5y"
    if "1y" in query_lower or "last year" in query_lower or "one year" in query_lower:
        return "1y"
    if "max" in query_lower or "all time" in query_lower:
        return "max"
    return "ytd"


def _route_tool(query: str, session_history: list[dict[str, str]]) -> tuple[ToolName, dict[str, Any]]:
    query_lower = query.lower()
    # Follow-up prompts should prefer previous analytical context.
    if any(phrase in query_lower for phrase in ["what about", "and for", "how about"]):
        for item in reversed(session_history):
            previous_tool = item.get("tool")
            if previous_tool in {"get_performance", "compare_holdings_performance"}:
                return "get_performance", {"query_range": _extract_range(query)}

    if "compare" in query_lower and any(word in query_lower for word in ["holding", "holdings", "portfolio"]):
        if any(word in query_lower for word in ["perform", "performance", "return", "gain"]):
            return "compare_holdings_performance", {"query_range": _extract_range(query)}

    if any(word in query_lower for word in ["transaction", "buy", "sell", "activity"]):
        return "get_transactions", {"limit": 5}
    if any(word in query_lower for word in ["perform", "return", "ytd", "year", "gain"]):
        return "get_performance", {"query_range": _extract_range(query)}

    return "get_portfolio_summary", {}


def _format_currency(value: float, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def _synthesize_response(state: AgentState) -> tuple[str, bool]:
    result = state["tool_result"]
    if not result.success:
        error_message = result.error.message if result.error else "Unknown tool error"
        return (
            f"I could not complete that request due to a tool error: {error_message}\n\n{DISCLAIMER}",
            False,
        )

    data = result.data or {}
    tool_name = state["selected_tool"]
    fact_grounded = True

    if tool_name == "get_portfolio_summary":
        total = float(data["total_value"])
        currency = str(data["currency"])
        count = int(data["holdings_count"])
        response = (
            f"Your portfolio value is {_format_currency(total, currency)} across {count} holdings. "
            "I can also break down top allocations if you want.\n\n"
            f"{DISCLAIMER}"
        )
        fact_grounded = (
            f"{count} holdings" in response and _format_currency(total, currency) in response
        )
        return response, fact_grounded

    if tool_name == "get_performance":
        perf_range = str(data["range"]).upper()
        return_pct = float(data["return_pct"])
        gain = float(data["absolute_gain"])
        currency = str(data["currency"])
        response = (
            f"Your {perf_range} portfolio return is {return_pct:.2f}% "
            f"({ _format_currency(gain, currency) } absolute).\n\n{DISCLAIMER}"
        )
        fact_grounded = (
            f"{return_pct:.2f}%" in response and _format_currency(gain, currency) in response
        )
        return response, fact_grounded

    if tool_name == "compare_holdings_performance":
        summary = data.get("summary", {})
        perf = data.get("performance", {})
        total = float(summary["total_value"])
        currency = str(summary["currency"])
        count = int(summary["holdings_count"])
        perf_range = str(perf["range"]).upper()
        return_pct = float(perf["return_pct"])
        gain = float(perf["absolute_gain"])
        response = (
            f"Compared to your total portfolio value of {_format_currency(total, currency)} "
            f"across {count} holdings, your {perf_range} return is {return_pct:.2f}% "
            f"({_format_currency(gain, currency)} absolute).\n\n{DISCLAIMER}"
        )
        fact_grounded = (
            _format_currency(total, currency) in response
            and f"{return_pct:.2f}%" in response
            and _format_currency(gain, currency) in response
        )
        return response, fact_grounded

    txs = data.get("transactions", [])
    total_count = int(data.get("total_count", 0))
    if not txs:
        response = f"I did not find matching recent transactions.\n\n{DISCLAIMER}"
        return response, True

    first = txs[0]
    snippet = (
        f"Most recent transaction: {first.get('type')} {first.get('quantity')} "
        f"{first.get('symbol')} at {first.get('currency')} {first.get('unit_price')} on {first.get('date')}."
    )
    response = f"I found {total_count} recent transactions. {snippet}\n\n{DISCLAIMER}"
    fact_grounded = f"I found {total_count} recent transactions." in response
    return response, fact_grounded


def _extract_last_updated(data: dict[str, Any]) -> str | None:
    if "last_updated" in data and isinstance(data["last_updated"], str):
        return data["last_updated"]
    performance = data.get("performance")
    if isinstance(performance, dict) and isinstance(performance.get("last_updated"), str):
        return performance["last_updated"]
    return None


def _is_stale(last_updated: str | None) -> bool:
    if not last_updated:
        return False
    try:
        parsed = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - parsed > timedelta(hours=6)
    except ValueError:
        return False


def _build_graph():
    async def route_node(state: AgentState) -> dict[str, Any]:
        tool_name, tool_args = _route_tool(state["query"], state["session_history"])
        return {"selected_tool": tool_name, "tool_args": tool_args}

    async def tool_node(state: AgentState) -> dict[str, Any]:
        context = state["tool_context"]
        tool_name = state["selected_tool"]
        if tool_name == "get_portfolio_summary":
            result = await get_portfolio_summary(context, account_id=state["tool_args"].get("account_id"))
        elif tool_name == "get_performance":
            result = await get_performance(context, query_range=state["tool_args"].get("query_range", "ytd"))
        elif tool_name == "compare_holdings_performance":
            summary = await get_portfolio_summary(context, account_id=state["tool_args"].get("account_id"))
            performance = await get_performance(
                context, query_range=state["tool_args"].get("query_range", "ytd")
            )
            if not summary.success:
                result = summary
            elif not performance.success:
                result = performance
            else:
                result = ToolResult(
                    success=True,
                    data={
                        "summary": summary.data,
                        "performance": performance.data,
                    },
                )
            return {
                "tool_result": result,
                "tool_calls": ["get_portfolio_summary", "get_performance"],
            }
        else:
            result = await get_transactions(
                context,
                symbol=state["tool_args"].get("symbol"),
                tx_type=state["tool_args"].get("tx_type"),
                limit=state["tool_args"].get("limit", 5),
            )
        return {"tool_result": result, "tool_calls": [tool_name]}

    async def verify_and_respond_node(state: AgentState) -> dict[str, Any]:
        response, fact_grounded = _synthesize_response(state)
        disclaimer_present = DISCLAIMER in response
        data = state["tool_result"].data or {}
        stale_data_warning = _is_stale(_extract_last_updated(data))
        if state["tool_result"].success and fact_grounded and not stale_data_warning:
            confidence = 0.9
            confidence_level = "high"
        elif state["tool_result"].success and fact_grounded:
            confidence = 0.65
            confidence_level = "medium"
            response = (
                f"{response}\n\nWarning: Market data appears older than 6 hours and may be stale."
            )
        else:
            confidence = 0.4
            confidence_level = "low"
        verification = {
            "fact_grounded": fact_grounded,
            "disclaimer_present": disclaimer_present,
            "no_trade_advice": True,
            "stale_data_warning": stale_data_warning,
            "confidence_level": confidence_level,
        }
        return {
            "response": response,
            "verification": verification,
            "confidence": confidence,
        }

    graph = StateGraph(AgentState)
    graph.add_node("route", route_node)
    graph.add_node("run_tool", tool_node)
    graph.add_node("verify_and_respond", verify_and_respond_node)
    graph.set_entry_point("route")
    graph.add_edge("route", "run_tool")
    graph.add_edge("run_tool", "verify_and_respond")
    graph.add_edge("verify_and_respond", END)
    return graph.compile()


_GRAPH = _build_graph()


async def run_agent(
    query: str,
    session_history: list[dict[str, str]],
    tool_context: ToolContext,
) -> dict[str, Any]:
    result = await _GRAPH.ainvoke(
        {
            "query": query,
            "session_history": session_history,
            "tool_context": tool_context,
        }
    )
    return {
        "response": result["response"],
        "tool_calls": result["tool_calls"],
        "verification": result["verification"],
        "confidence": result["confidence"],
        "selected_tool": result["selected_tool"],
    }
