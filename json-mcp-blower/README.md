# JSON-MCP-Blower: Exponential Agent Swarm Generation

**JSON-MCP-Blower** generates exponential swarms of Claude agents (MCPs) from a central JSON schema. Real-time synchronization via watchdog monitoring.

## Quick Start

```bash
cd /home/ichigo/alexandria/json-mcp-blower
./start.sh
# Monitors mcp-schema.json for changes, generates MCPs in real-time
```

## Architecture

- **mcp-schema.json** — Master MCP blueprint (source of truth)
- **mcp_factory.py** — Creates MCP instances from templates
- **bootstrap_loop.py** — Exponential generation (N → N*growth_rate)
- **json_watcher.py** — Real-time file sync (< 100ms)
- **agents/** — Generated MCP instances

## Exponential Growth Model

```
Generation 0: 3 agents
Generation 1: 3 × 2.0 = 6 agents
Generation 2: 6 × 2.0 = 12 agents
Generation 3: 12 × 2.0 = 24 agents
...
Generation 10: 1,536 agents
```

## Configuration

**mcp-schema.json** defines:
- Initial agent count and specializations
- Growth rate (exponential factor)
- Max iterations
- Agent roles (architect, developer, analyst, collaborator)
- MCP payload structure

## Integration

MCPs deploy to:
- **ADAM** — Multi-agent orchestration
- **Hot-Rod** — Quality gamification (NFT stats, arena battles)
- **Energy-Tech** — Energon ledger tracking

## Status

✅ Production Ready (integrated with energy-tech system)

---

**Part of Alexandria Energy-Tech Ecosystem**
