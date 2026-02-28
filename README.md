# ghostfolio-agent

P0 implementation of a Ghostfolio conversational finance agent using:
- `FastAPI` for API
- `LangGraph` for orchestration
- `Streamlit` for chat UI
- 3 P0 tools: `get_portfolio_summary`, `get_performance`, `get_transactions`
- Verification: fact grounding + mandatory financial disclaimer

## Quick Start

1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[dev]"`

2. Run the API:
   - `uvicorn app.main:app --reload`

3. Run the chat UI (in a second terminal):
   - `streamlit run ui/streamlit_app.py`

4. Test chat endpoint:
   - `curl -X POST http://127.0.0.1:8000/chat -H "content-type: application/json" -d '{"message":"What'\''s my portfolio worth?","session_id":"demo","data_source":"mock"}'`

5. Run tests:
   - `pytest`

## Configuration

Environment variables (optional):
- `GHOSTFOLIO_BASE_URL` (default: `https://ghostfol.io`)
- `GHOSTFOLIO_TOKEN`
- `GHOSTFOLIO_REQUEST_TIMEOUT_SECONDS` (default: `10`)
- `GHOSTFOLIO_DEFAULT_DATA_SOURCE` (`mock` or `ghostfolio_api`, default: `mock`)

The app supports both Ghostfolio Cloud and self-hosted instances by setting `GHOSTFOLIO_BASE_URL`.

## Deployment (Railway)

This repo includes a `Procfile` that starts:
- FastAPI backend on `127.0.0.1:8000`
- Streamlit UI on `0.0.0.0:$PORT` (public entrypoint)

Railway steps:
1. Create a new Railway project from this repo.
2. Set environment variables as needed:
   - `GHOSTFOLIO_DEFAULT_DATA_SOURCE=mock` (or `ghostfolio_api`)
   - `GHOSTFOLIO_BASE_URL`
   - `GHOSTFOLIO_TOKEN` (for live API mode)
   - optionally `BACKEND_URL=http://127.0.0.1:8000`
3. Deploy. Railway uses `Procfile` command: `web: bash scripts/start.sh`.