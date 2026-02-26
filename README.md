# ghostfolio-agent

P0 implementation of a Ghostfolio conversational finance agent using:
- `FastAPI` for API
- `LangGraph` for orchestration
- 3 P0 tools: `get_portfolio_summary`, `get_performance`, `get_transactions`
- Verification: fact grounding + mandatory financial disclaimer

## Quick Start

1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[dev]"`

2. Run the API:
   - `uvicorn app.main:app --reload`

3. Test chat endpoint:
   - `curl -X POST http://127.0.0.1:8000/chat -H "content-type: application/json" -d '{"message":"What'\''s my portfolio worth?","session_id":"demo","data_source":"mock"}'`

4. Run tests:
   - `pytest`

## Configuration

Environment variables (optional):
- `GHOSTFOLIO_BASE_URL` (default: `https://ghostfol.io`)
- `GHOSTFOLIO_TOKEN`
- `GHOSTFOLIO_REQUEST_TIMEOUT_SECONDS` (default: `10`)
- `GHOSTFOLIO_DEFAULT_DATA_SOURCE` (`mock` or `ghostfolio_api`, default: `mock`)

The app supports both Ghostfolio Cloud and self-hosted instances by setting `GHOSTFOLIO_BASE_URL`.