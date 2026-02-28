#!/usr/bin/env bash

set -euo pipefail

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
STREAMLIT_PORT="${PORT:-8501}"

export GHOSTFOLIO_DEFAULT_DATA_SOURCE=ghostfolio_api
export GHOSTFOLIO_BASE_URL="https://ghostfol.io"
export GHOSTFOLIO_LOG_LEVEL="DEBUG"

uvicorn app.main:app --host "$API_HOST" --port "$API_PORT"