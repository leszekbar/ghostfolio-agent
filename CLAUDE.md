# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (dev)
pip install -e ".[dev]"

# Run FastAPI server (port 8000)
uvicorn app.main:app --reload

# Run Streamlit UI (port 8501)
streamlit run ui/streamlit_app.py

# Tests
pytest -v                          # all tests
pytest tests/test_agent.py         # single file
pytest -k "test_portfolio"         # by keyword

# Lint & format
ruff check app/ tests/ evals/
ruff format app/ tests/ evals/

# Deterministic evals (53 cases, >80% gate)
GHOSTFOLIO_DEFAULT_DATA_SOURCE=mock GHOSTFOLIO_LLM_ENABLED=false python evals/run_evals.py

# LLM-as-judge (advisory, needs OpenAI key)
python evals/llm_judge.py
```

## Architecture

**Dual-mode LangGraph agent** for Ghostfolio portfolio queries:

- **LLM mode** (primary): OpenAI GPT-4.1 with function calling, Anthropic Claude fallback. Graph: `llm_init → llm_reason → llm_execute → llm_verify → END` (loops up to 5 tool calls).
- **Rule-based mode** (fallback): Keyword routing when LLM is disabled or no API keys. Graph: `route → run_tool → verify_and_respond → END`.
- Selection: `app/agent.py:run_agent()` tries LLM mode first, catches errors, falls back to rule-based.

**Data layer** uses a `PortfolioDataProvider` protocol (`app/data_sources/base.py`) with two implementations:
- `MockPortfolioDataProvider` — frozen test data, used in tests and evals
- `GhostfolioAPIDataProvider` — wraps Ghostfolio REST API via `app/ghostfolio_client.py`

Switched via `GHOSTFOLIO_DEFAULT_DATA_SOURCE` env var (`mock` or `ghostfolio_api`).

**7 tools** in `app/tools.py` with `TOOL_REGISTRY` dict for dispatch. LLM tool schemas defined in `app/tool_defs.py`.

**Verification layer** runs on every response: fact grounding, disclaimer enforcement, trade advice refusal (regex in `_is_trade_advice_query`), prompt injection defense (regex in `_is_prompt_injection`), data freshness check, confidence scoring (0.4–0.95).

**Key flow**: Streamlit UI → FastAPI `/chat` endpoint (`app/main.py`) → `run_agent()` (`app/agent.py`) → tool execution → verification → response.

**Config**: All env vars use `GHOSTFOLIO_` prefix via pydantic-settings (`app/config.py`).

**Observability**: Langfuse tracing (`app/observability.py`) — no-ops gracefully when keys are absent.

## Rules

- Never push to main without explicit user permission.
- Never add dependencies unless there is existing code that imports them. Add both code and dependency together.
- Never modify `PRD.md` without explicit user permission.
- Tests in `test_agent.py` use an autouse `_disable_llm` fixture to force rule-based routing for deterministic assertions.

## CI Pipeline

Lint → Test → Evals (hard gate) → LLM Judge (advisory, main only). See `.github/workflows/ci.yml`.
