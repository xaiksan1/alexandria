# CLAUDE.md — agentic-ads

## Port Map (do not change)
| Service | Port |
|---------|------|
| UI Next.js | 3043 |
| Cache API | 3044 |
| Bid Engine API | 3045 |
| Redis hot-cache | 6380 |
| cortex-ws (read-only subscribe) | 8083 |

## Critical Rules
1. NEVER write directly to `energon_ledger.json` — use cortex-v3 API port 3001
2. NEVER kill or modify any running ADAM service
3. `pending_revenue.json` writes: write to `.tmp` then `os.replace()` — atomic only
4. Souffle `agentic_ads_campaign.json` uses timer:3600s only — no file_trigger
5. Revenue only after `payment_confirmed = TRUE` in bid_history

## Quick Start
```bash
# Start Redis
redis-server --port 6380 --daemonize yes

# Start cache API
cd cache && uvicorn cache_api:app --port 3044

# Start bid engine API
cd bid-engine && uvicorn bid_engine_api:app --port 3045

# Start UI
cd ui && bun dev
```

## Architecture Phases
- **Phase 1**: Cache API + Bid Engine (current)
- **Phase 2**: Crypto MCP server + payment integration
- **Phase 3**: Action layer + souffles
- **Phase 4**: Cloud, Immo, IA-Tools verticals
