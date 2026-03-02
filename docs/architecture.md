# Ghostfolio AI Agent — Architecture

## Overview

The Ghostfolio AI Agent is a conversational portfolio assistant that connects to [Ghostfolio](https://ghostfol.io), an open-source personal finance management tool. It answers natural-language questions about portfolios using real-time data, with built-in verification, safety guardrails, and observability.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Chat UI                   │
│           (ui/streamlit_app.py, port 8501)           │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP (POST /chat, /session/start)
┌───────────────────────▼─────────────────────────────┐
│                   FastAPI Server                     │
│              (app/main.py, port 8000)                │
│  ┌─────────────────────────────────────────────┐    │
│  │          Session Management                  │    │
│  │  SESSION_STORE (history) + SESSION_TOKENS    │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │            Agent (app/agent.py)              │    │
│  │                                              │    │
│  │  ┌─────────────────────────────────────┐     │    │
│  │  │   LLM Mode (primary)                │     │    │
│  │  │   llm_init → llm_reason →           │     │    │
│  │  │   llm_execute → llm_verify → END    │     │    │
│  │  └─────────────┬───────────────────────┘     │    │
│  │                │ fallback on error            │    │
│  │  ┌─────────────▼───────────────────────┐     │    │
│  │  │   Rule-Based Mode (fallback)        │     │    │
│  │  │   route → run_tool →                │     │    │
│  │  │   verify_and_respond → END          │     │    │
│  │  └─────────────────────────────────────┘     │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │          Tool Layer (app/tools.py)           │    │
│  │  7 tools with ToolContext + ToolResult       │    │
│  │                                              │    │
│  │  P0: get_portfolio_summary                   │    │
│  │      get_performance                         │    │
│  │      get_transactions                        │    │
│  │  P1: get_account_details                     │    │
│  │      get_market_data                         │    │
│  │      analyze_allocation                      │    │
│  │      check_risk_rules                        │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │     Data Source Layer (app/data_sources/)    │    │
│  │  PortfolioDataProvider protocol              │    │
│  │  ├── MockPortfolioDataProvider (testing)     │    │
│  │  └── GhostfolioAPIDataProvider (production)  │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│  ┌──────────────────▼──────────────────────────┐    │
│  │    Ghostfolio Client (app/ghostfolio_client) │    │
│  │    HTTP client with retry logic              │    │
│  └──────────────────┬──────────────────────────┘    │
└─────────────────────┼───────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────┐
│            Ghostfolio API (external)                 │
│            ghostfol.io or self-hosted                │
└─────────────────────────────────────────────────────┘
```

## Agent Dual-Mode Design

### LLM Mode (Primary)
When an LLM API key is configured, the agent uses OpenAI (or Anthropic as fallback) for:
1. **Intent classification** — understanding what the user wants
2. **Tool selection** — choosing which tool(s) to call via function calling
3. **Parameter extraction** — extracting arguments from natural language

The LLM graph has 4 nodes:
- `llm_init`: Input sanitization, trade advice detection, prompt injection detection
- `llm_reason`: LLM decides tool call (or direct response)
- `llm_execute`: Dispatches to tool functions
- `llm_verify`: Fact grounding, disclaimer enforcement, confidence scoring

### Rule-Based Mode (Fallback)
When no LLM is available (or LLM fails), a keyword-based router selects tools:
- Keyword matching for tool selection
- Session history for follow-up context
- Same verification layer as LLM mode

## Verification Layer

Every response passes through verification before reaching the user:

| Check | Description |
|-------|-------------|
| **Fact Grounding** | All numerical claims must trace back to tool output |
| **Disclaimer** | Every response must include financial disclaimer |
| **No Trade Advice** | Trade advisory queries are refused with explanation |
| **Prompt Injection** | Common injection patterns are detected and blocked |
| **Data Freshness** | Warns if data is >6 hours old |
| **Confidence Scoring** | 0.4 (low) to 0.95 (high) based on data quality |
| **Output Validation** | Checks allocation sums, symbol references |

## Data Flow

```
User Query
  → Input Sanitization (strip injection markers)
  → Trade Advice Check (regex patterns → refusal)
  → Prompt Injection Check (regex patterns → block)
  → Tool Selection (LLM function calling or keyword routing)
  → Tool Execution (async, with error handling)
  → Response Synthesis (format tool data into natural language)
  → Verification (fact grounding, disclaimer, freshness)
  → Confidence Scoring
  → User Response
```

## Observability (Langfuse)

When Langfuse keys are configured, the agent traces:
- Full agent runs (trace per request)
- Individual tool calls (span per tool)
- LLM invocations (generation with token counts)
- Verification results (span with metadata)

All observability is opt-in and no-ops gracefully when keys are absent.

## Security

- **Input sanitization**: Strips `<system>` tags, null bytes
- **Prompt injection defense**: Regex detection of override attempts
- **Trade advice refusal**: Pattern-based detection with polite refusal
- **Token security**: Bearer tokens redacted in logs
- **Session isolation**: Per-session token storage

## Configuration

All settings use environment variables with `GHOSTFOLIO_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `GHOSTFOLIO_OPENAI_API_KEY` | — | OpenAI API key for LLM mode |
| `GHOSTFOLIO_ANTHROPIC_API_KEY` | — | Anthropic API key (fallback) |
| `GHOSTFOLIO_LLM_ENABLED` | `true` | Enable/disable LLM mode |
| `GHOSTFOLIO_DEFAULT_DATA_SOURCE` | `mock` | `mock` or `ghostfolio_api` |
| `GHOSTFOLIO_LANGFUSE_PUBLIC_KEY` | — | Langfuse public key |
| `GHOSTFOLIO_LANGFUSE_SECRET_KEY` | — | Langfuse secret key |

## Evaluation

- **50+ deterministic test cases** covering happy path, edge cases, adversarial, and multi-step queries
- **LLM-as-judge** scoring on helpfulness, accuracy, disclaimer compliance, and unsupported claims
- **CI integration** with hard gate on deterministic evals and advisory LLM judge
