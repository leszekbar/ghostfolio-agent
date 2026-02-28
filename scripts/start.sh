#!/usr/bin/env bash
set -euo pipefail

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
STREAMLIT_PORT="${PORT:-8501}"

uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" &
API_PID=$!

cleanup() {
  kill "$API_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

streamlit run ui/streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "$STREAMLIT_PORT" \
  --browser.gatherUsageStats false
