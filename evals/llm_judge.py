#!/usr/bin/env python3
"""LLM-as-judge eval scorer for the Ghostfolio AI Agent.

Uses gpt-4.1-mini to score agent responses on:
  - Helpfulness (1-5)
  - Accuracy (1-5)
  - Disclaimer compliance (1-5)
  - Unsupported claims (1-5, lower = worse)

Advisory only — non-blocking in CI.

Usage:
    python evals/llm_judge.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"

JUDGE_PROMPT = """\
You are an expert evaluator for a portfolio assistant AI agent. Score the following response on four dimensions (1-5 scale, 5 is best):

1. **Helpfulness**: Does the response address the user's question? Is it clear and useful?
2. **Accuracy**: Are the numbers and facts correct given the tool output data?
3. **Disclaimer**: Does the response include a financial disclaimer?
4. **No Unsupported Claims**: Does the response avoid making claims not supported by the tool data? (5 = no unsupported claims, 1 = many fabricated claims)

User Query: {query}
Agent Response: {response}
Tool Calls Made: {tool_calls}

Respond in JSON format only:
{{"helpfulness": <1-5>, "accuracy": <1-5>, "disclaimer": <1-5>, "no_unsupported_claims": <1-5>, "notes": "<brief explanation>"}}
"""


def load_dataset() -> list[dict]:
    with open(DATASET_PATH) as f:
        return json.load(f)


async def judge_single(case: dict, agent_result: dict, llm) -> dict:
    """Use LLM to judge a single response."""
    query = case["query"]
    response = agent_result.get("response", "")
    tool_calls = agent_result.get("tool_calls", [])

    prompt = JUDGE_PROMPT.format(
        query=query,
        response=response,
        tool_calls=", ".join(tool_calls) if tool_calls else "none",
    )

    try:
        result = await llm.ainvoke([{"role": "user", "content": prompt}])
        content = result.content if hasattr(result, "content") else str(result)
        # Try to parse JSON from response
        # Handle markdown code blocks
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        scores = json.loads(content.strip())
        return {
            "id": case["id"],
            "scores": scores,
            "success": True,
        }
    except Exception as exc:
        return {
            "id": case["id"],
            "scores": {},
            "success": False,
            "error": str(exc),
        }


async def run_judge():
    # Override config
    os.environ["GHOSTFOLIO_DEFAULT_DATA_SOURCE"] = "mock"
    os.environ["GHOSTFOLIO_LLM_ENABLED"] = "false"

    from app.agent import run_agent
    from app.data_sources.mock_provider import MockPortfolioDataProvider
    from app.llm import get_eval_llm
    from app.tools import ToolContext

    eval_llm = get_eval_llm()
    if eval_llm is None:
        print("No eval LLM available (set GHOSTFOLIO_OPENAI_API_KEY). Skipping LLM judge.")
        sys.exit(0)

    dataset = load_dataset()
    context = ToolContext(provider=MockPortfolioDataProvider())

    results = []
    for case in dataset:
        if case.get("expect_error"):
            continue

        query = case["query"]
        history = case.get("requires_history", [])
        try:
            agent_result = await run_agent(query=query, session_history=history, tool_context=context)
        except Exception:
            continue

        judge_result = await judge_single(case, agent_result, eval_llm)
        results.append(judge_result)
        status = "OK" if judge_result["success"] else "ERR"
        scores = judge_result.get("scores", {})
        print(f"  [{status}] {case['id']}: {scores}")

    # Summary
    successful = [r for r in results if r["success"]]
    if not successful:
        print("\nNo successful judge evaluations.")
        return

    avg_scores = {}
    for key in ["helpfulness", "accuracy", "disclaimer", "no_unsupported_claims"]:
        values = [r["scores"].get(key, 0) for r in successful if key in r.get("scores", {})]
        avg_scores[key] = sum(values) / len(values) if values else 0

    print(f"\n{'='*60}")
    print("LLM JUDGE SUMMARY")
    print(f"{'='*60}")
    print(f"  Evaluated: {len(successful)}/{len(results)} cases")
    for key, avg in avg_scores.items():
        print(f"  {key}: {avg:.2f}/5.00")
    overall = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0
    print(f"  Overall: {overall:.2f}/5.00")


def main():
    asyncio.run(run_judge())


if __name__ == "__main__":
    main()
