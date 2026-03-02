# Full Project Completion Plan

Plan to meet all PRD requirements beyond the Section 10 MVP. Ordered by dependency and impact.

---

## Phase 1: Observability & CI (foundation)

**Why first:** Langfuse and lint are required for AC-4, AC-13, AC-14, AC-24 and unblock confident iteration.

| Task | PRD ref | Notes |
|------|---------|--------|
| **1.1 Add Langfuse integration** | AC-4, AC-13, §4.1 | Instrument agent: trace each request, log tool calls, tool duration, and (once LLM is added) token usage and cost. Use env vars for Langfuse URL/key; no-op if not configured. |
| **1.2 Add lint to CI** | §4.1, §6.4 | Add a lint job (e.g. `ruff check .`) to GitHub Actions; keep pytest as the gate. |
| **1.3 Expand evals to 20+** | AC-14 | Grow from current ~11 agent tests to 20+ (happy path + edge cases). Add edge cases: empty portfolio, single holding, currency mismatch. |

**Deliverables:** Langfuse optional integration, CI with lint + tests, 20+ eval cases.

---

## Phase 2: Verification & safety (domain constraints)

**Why next:** AC-16 (all 4 verification checks), AC-18 (adversarial). Ensures no buy/sell advice and no prompt-injection bypass.

| Task | PRD ref | Notes |
|------|---------|--------|
| **2.1 No buy/sell advice** | §3.3, AC-16, AC-18 | Before responding: detect queries asking for trades, price targets, or timing. Return a polite refusal + disclaimer; never recommend specific buys/sells. |
| **2.2 Output validation** | §3.3, AC-16 | Validate: symbols in response exist in portfolio; allocation %s sum to ~100% (with tolerance); log and degrade gracefully on failure. |
| **2.3 Adversarial test suite** | AC-18, §5.2 | Add 10+ tests: prompt injection (“Ignore previous instructions…”), “Tell me to buy X”, “What’s the API key?”, etc. Assert agent refuses or does not comply. |

**Deliverables:** Domain checks in verification layer, adversarial tests in CI.

---

## Phase 3: P1 tools (4 new tools)

**Why:** AC-7, AC-12, user stories US-4–US-7. Requires Ghostfolio API discovery for accounts and market data.

| Tool | PRD spec | Implementation approach |
|------|----------|-------------------------|
| **3.1 get_account_details** | GET /api/v1/account | Add `GhostfolioClient.get_accounts()`, provider method, tool in `tools.py`. Mock in mock provider. Wire into agent routing/synthesis. |
| **3.2 get_market_data** | Yahoo Finance via Ghostfolio | Find Ghostfolio endpoint for symbol quotes (e.g. market data or symbol endpoint). Add client method, provider, tool; return `{ symbol, price, change_pct, currency, last_updated }`. Mock for evals. |
| **3.3 analyze_allocation** | Derived from holdings + market data | No single API: call get_portfolio_summary (and optionally get_market_data). Compute by_sector, by_region, by_asset_class from holdings; add simple risk_flags. Return PRD schema. |
| **3.4 check_risk_rules** | Ghostfolio X-ray rules | If Ghostfolio exposes an X-ray/risk API, add client + tool. Otherwise implement a minimal rule set (e.g. concentration limits) from holdings data and return pass/fail/warn. |

**Deliverables:** All 7 tools implemented, unit-tested with mocks, integrated into agent (routing + synthesis).

---

## Phase 4: Agent intelligence (LLM vs rules)

**Why:** PRD §4.1 specifies GPT-5 for production; Section 10 says “via GPT-5”. Improves tool selection and multi-step handling.

| Task | PRD ref | Notes |
|------|---------|--------|
| **4.1 Optional LLM tool selection** | §4.1, §6.2 AC-9 | Add optional path: call LLM (e.g. OpenAI/Anthropic) with tool descriptions and user query; use response to pick tool(s) and args. Keep rule-based as fallback when no API key. Config-driven (env). |
| **4.2 Multi-step patterns** | AC-10, US-8 | Support at least 3 multi-step patterns (e.g. “compare tech to S&P this year” → summary + performance + market data). Either extend rule router or let LLM propose a chain. |
| **4.3 Tool selection accuracy** | AC-9 | Ensure eval suite asserts correct tool(s) per query; aim >90% on happy-path + multi-step cases. |

**Deliverables:** Optional LLM-based routing, 3+ multi-step patterns, evals for tool selection.

---

## Phase 5: Evals to 50+ and LLM-as-judge (advisory)

**Why:** AC-17, AC-15, §5.2.

| Task | PRD ref | Notes |
|------|---------|--------|
| **5.1 Expand to 50+ test cases** | AC-17, §5.2 | Add: more happy-path (20+), edge (10+), adversarial (10+), multi-step (10+). Use mock data for deterministic assertions. |
| **5.2 LLM-as-judge (advisory)** | AC-15 | Optional CI job: run a subset of evals, send prompt+response to GPT-5 Mini (temperature=0), get score/reason. Post as PR comment; do not block merge. |

**Deliverables:** 50+ tests in CI, optional LLM-as-judge job with PR comment.

---

## Phase 6: Packaging and docs

**Why:** AC-19–AC-21.

| Task | PRD ref | Notes |
|------|---------|--------|
| **6.1 PyPI-ready package** | AC-19 | Ensure `pyproject.toml` is complete; add `MANIFEST.in` if needed. Document `pip install ghostfolio-agent` (or publish when ready). |
| **6.2 Public eval dataset** | AC-20 | Add `eval_dataset/` (or similar) with documented test cases/inputs and expected outcomes; README in repo. |
| **6.3 README and architecture** | AC-21 | README: architecture diagram (e.g. Mermaid), setup, env vars, contribution guide. |

**Deliverables:** Package publishable, eval dataset on GitHub, README with diagram and contribution guide.

---

## Phase 7: Polish and submission

**Why:** AC-22–AC-24; deployment already done.

| Task | PRD ref | Notes |
|------|---------|--------|
| **7.1 Demo recording** | AC-23 | Record a short demo showing 6 use cases (portfolio worth, performance, transactions, diversification, risk, accounts/market if implemented). |
| **7.2 Langfuse dashboard** | AC-24 | Document or screenshot: latency, cost per query, tool success rate, eval pass rate. |
| **7.3 Final checklist** | §10 | Re-run Section 10 checklist and all AC items; fix any regressions. |

**Deliverables:** Demo video, Langfuse metrics documented, submission checklist green.

---

## Dependency summary

```
Phase 1 (Observability + CI) ──► Phase 2 (Verification) ──► Phase 5 (50+ evals, LLM-judge)
         │                                    │
         └────────────────────────────────────┼──────────────────► Phase 4 (LLM optional)
                                              │
Phase 3 (P1 tools) ───────────────────────────┴──────────────────► Phase 6 (Packaging + docs)
                                                                        │
                                                                        └──► Phase 7 (Polish)
```

**Suggested order:** 1 → 2 → 3 (can parallelize 3.1–3.4) → 4 → 5 → 6 → 7.

---

## Out of scope (per PRD §7)

- Trade execution; rebalancing recommendations  
- Multi-user auth; cross-session persistence  
- FIRE/retirement projections; real-time streaming; mobile UI  
- Changes to Ghostfolio codebase; self-hosted Ghostfolio
