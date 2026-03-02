# Ghostfolio AI Agent — Cost Analysis

## Development Costs

| Item | Hours | Notes |
|------|-------|-------|
| Architecture & design | 2 | Agent graph, data source protocol, verification layer |
| P0 tools + agent | 4 | Portfolio summary, performance, transactions |
| P1 tools | 2 | Account details, market data, allocation, risk rules |
| LLM integration | 3 | Dual-mode agent, tool schemas, fallback logic |
| Verification hardening | 2 | Trade advice refusal, injection defense, output validation |
| Eval suite | 2 | 50+ test cases, runner, LLM judge |
| Observability | 1 | Langfuse integration |
| UI + deployment | 2 | Streamlit, Railway, CI/CD |
| Documentation | 1 | Architecture, cost analysis, README |
| **Total** | **19** | |

## Per-Request Cost Projections

### LLM Costs (GPT-4.1)

Based on GPT-4.1 pricing (as of 2026):
- Input: $2.00 / 1M tokens
- Output: $8.00 / 1M tokens

Average request profile:
- System prompt: ~400 tokens
- User message + history: ~200 tokens
- Tool schemas: ~800 tokens (7 tools)
- LLM response: ~150 tokens
- **Total per request**: ~1,550 tokens input + ~150 output

| Metric | Per Request |
|--------|------------|
| Input tokens | ~1,550 |
| Output tokens | ~150 |
| Input cost | $0.0031 |
| Output cost | $0.0012 |
| **Total LLM cost** | **~$0.0043** |

### Ghostfolio API Costs
- Self-hosted: $0 (your own server)
- Ghostfolio Cloud: Free tier available, paid plans for additional features

### Langfuse Costs
- Free tier: 50K observations/month
- Pro: $59/month for higher volume

### Infrastructure (Railway)
- Hobby plan: $5/month (adequate for demo)
- Pro: $20/month (for production with more resources)

## Scaling Projections

| Users/Month | Requests/Month | LLM Cost | Infra | Langfuse | Total |
|-------------|---------------|----------|-------|----------|-------|
| 100 | 1,000 | $4.30 | $5 | $0 | **$9.30** |
| 1,000 | 10,000 | $43 | $20 | $0 | **$63** |
| 10,000 | 100,000 | $430 | $50 | $59 | **$539** |
| 100,000 | 1,000,000 | $4,300 | $200 | $159 | **$4,659** |

### Assumptions
- Average 10 requests per user per month
- 100% of requests use LLM (real-world: some may use rule-based fallback)
- Single Railway instance up to 10K users, horizontal scaling beyond

## Cost Optimization Strategies

1. **Rule-based fallback**: Simple queries (80%+ of traffic) can be handled without LLM calls, reducing costs by 4-5x
2. **Response caching**: Cache identical queries within a session to avoid duplicate LLM calls
3. **Smaller model for simple queries**: Use GPT-4.1-mini for straightforward tool routing, GPT-4.1 only for complex multi-step queries
4. **Batch eval runs**: Run LLM judge evaluations on schedule rather than per-commit
5. **Langfuse sampling**: At high volume, sample 10-20% of traces rather than logging all

## Break-Even Analysis

At $10/month subscription per user:
- Break-even at ~$0.10/user/month costs
- At 10 requests/user/month: $0.043/user in LLM costs
- **Profitable from day one** with substantial margin for infrastructure
