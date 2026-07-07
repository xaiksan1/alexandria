#!/usr/bin/env bash
cd /home/ichigo/alexandria/agentic-ads
source .venv/bin/activate
set -a
source .env
set +a
exec uvicorn cache.cache_api:app --port 3044 --host 0.0.0.0
