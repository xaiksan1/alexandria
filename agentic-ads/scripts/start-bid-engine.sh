#!/usr/bin/env bash
cd /home/ichigo/alexandria/agentic-ads
source .venv/bin/activate
set -a
source .env
set +a
cd bid-engine
exec uvicorn bid_engine_api:app --port 3045 --host 0.0.0.0
