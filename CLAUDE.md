# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in the Alexandria monorepo.

## Quick Navigation

**Just starting?** Read this section first, then jump to the subsystem you need:

- 🎬 **Filmmaker** (3D automation): `filmmaker/` → Create/render 3D content
- 🎯 **Product Spawner** (variant generation): `product-spawner/` → Generate market variants
- 🤖 **JSON-MCP-Blower** (agent swarms): `json-mcp-blower/` → Multiply AI agents exponentially
- 🧠 **Second-Me** (AI self-training): `Second-Me/` → Personal AI training
- 🎭 **ADAM** (Agent Zero): `ADAM/` → Multi-agent orchestration framework
- 🌐 **Anima Mundi** (enterprise platform): `anima-mundi/` → Enterprise features
- 📺 **Filmmaker-Web**: `filmmaker-web/` → Web UI for 3D automation

## Core Architecture

Alexandria is a **7-system ecosystem** where each system generates, multiplies, and improves AI agents and digital products:

```
Filmmaker (3D Content)
    ↓
Product-Spawner (Variants)
    ↓
JSON-MCP-Blower (Agent Swarms)
    ↓
ADAM (Orchestration)
    ↓
Feedback Loop → Self-Optimization
```

### What Each System Does

| System | Location | Purpose | Key Tech |
|--------|----------|---------|----------|
| **Filmmaker** | `filmmaker/` | Generate 3D content, animations, NFTs | Blender 4.2+, Python 3.12+, bpy |
| **Product-Spawner** | `product-spawner/` | Create 100+ product variants from seed | Claude API, Python |
| **JSON-MCP-Blower** | `json-mcp-blower/` | Generate exponential swarms of MCPs | Python, JSON schema, watchdog |
| **Second-Me** | `Second-Me/` | Train personalized AI on user data | Python, Next.js, llama.cpp, LoRA |
| **ADAM** | `ADAM/` | Multi-agent framework (Agent Zero fork) | Docker, Python, FastAPI, LiteLLM |
| **Filmmaker-Web** | `filmmaker-web/` | Web UI for Blender automation | Next.js 14, React 18, TypeScript |
| **Anima-Mundi** | `anima-mundi/` | Enterprise platform (in development) | TBD |

## Directory Structure & File Locations

```
alexandria/
├── filmmaker/                    # 3D rendering engine
│   ├── examples/production_render.py
│   ├── modules/                  # 7-layer modular system
│   └── renders/                  # Output directory
│
├── product-spawner/              # Product variant generator
│   ├── product_registry.json      # Master product database
│   ├── sales_orchestrator.py      # Main orchestrator
│   └── products_export.csv        # Output
│
├── json-mcp-blower/              # Agent swarm generator
│   ├── mcp-schema.json            # Master MCP blueprint
│   ├── mcp_factory.py             # Creates MCP instances
│   ├── bootstrap_loop.py          # Exponential generation
│   ├── json_watcher.py            # Real-time sync
│   └── mcps/                      # Generated MCPs
│
├── Second-Me/                     # AI self-training
│   ├── lpm_kernel/                # Backend (Python/Flask)
│   │   ├── L0/                    # Raw data processing
│   │   ├── L1/                    # Memory organization
│   │   ├── L2/                    # Model fine-tuning
│   │   └── api/                   # REST API
│   ├── lpm_frontend/              # Frontend (Next.js)
│   ├── Makefile                   # Build automation
│   └── scripts/                   # Setup scripts
│
├── ADAM/                          # Agent Zero orchestration
│   ├── agent.py                   # Core agent
│   ├── python/                    # Framework code
│   │   ├── api/                   # API endpoints
│   │   ├── tools/                 # Agent tools
│   │   └── extensions/            # Lifecycle hooks
│   ├── prompts/                   # Behavior templates
│   ├── memory/                    # Persistent memory
│   ├── webui/                     # Web interface
│   └── docker/                    # Containerization
│
├── filmmaker-web/                 # Web UI
│   ├── app/                       # Next.js pages
│   ├── components/                # React components
│   └── package.json
│
├── alexandria-toolbar/            # Toolbar extension
└── CLAUDE.md                      # This file
```

## Getting Started: Development Workflows

### Quick Start by Goal

**Goal: Generate 3D content**
```bash
cd filmmaker
blender --background --python examples/production_render.py
# Output → renders/
```

**Goal: Create product variants**
```bash
cd product-spawner
export ANTHROPIC_API_KEY="sk-..."
python3 sales_orchestrator.py
# Output → products_export.csv
```

**Goal: Generate agent swarms**
```bash
cd json-mcp-blower
./start.sh
# Watches mcp-schema.json for changes, generates MCPs
```

**Goal: Train personal AI**
```bash
cd Second-Me
make setup      # Install all dependencies
make start      # Launch all services
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

**Goal: Use multi-agent orchestration**
```bash
cd ADAM
docker run -p 50001:80 agent0ai/agent-zero
# Or for local dev:
python run_ui.py --port=5000
```

### Development Environment Setup

**For Python-based systems** (Filmmaker, Product-Spawner, JSON-MCP-Blower, Second-Me):
```bash
conda create -n alexandria python=3.12
conda activate alexandria
cd [system-directory]
pip install -r requirements.txt
```

**For TypeScript/Node systems** (Filmmaker-Web, Second-Me frontend):
```bash
cd [system-directory]
npm install
npm run dev
```

## Implementation Status

✅ **Production-Ready**:
- Filmmaker (3D rendering)
- Product-Spawner (variant generation)
- JSON-MCP-Blower (agent swarms)
- Second-Me (AI self-training)
- ADAM (agent orchestration)
- Filmmaker-Web (web UI framework)

🔄 **In Development**:
- Anima-Mundi (enterprise platform)
- Advanced orchestration features (Zangetsu, Chapel XVI)
- Hot-Rod NFT gaming system (planned)
- Arena Controller for quality comparison (planned)

## System Integration

### How Systems Work Together

1. **Create seed product** → Product-Spawner generates 100+ variants
2. **Render variants** → Filmmaker creates 3D assets/NFTs for each
3. **Deploy as agents** → JSON-MCP-Blower creates swarms of MCPs
4. **Orchestrate** → ADAM manages multi-agent execution
5. **Learn & improve** → Systems collect feedback to refine future generations

### Key Integration Points

| From | To | How | Purpose |
|------|-----|------|---------|
| Product-Spawner | Filmmaker | Product configs | Batch render variants |
| Filmmaker | Product-Spawner | Rendered assets | Update product database |
| Product-Spawner | JSON-MCP-Blower | Product registry | Define MCP payloads |
| JSON-MCP-Blower | ADAM | Generated MCPs | Deploy as agents |
| ADAM | Second-Me | Feedback loops | Train on agent performance |

## Common Development Tasks

### Working with JSON-MCP-Blower

The schema is the source of truth. Edit `mcp-schema.json`:
```json
{
  "mcp_registry": { /* all MCP definitions */ },
  "fractal_config": {
    "growth_rate": 2.0,
    "initial_generation": 3,
    "max_iterations": 10
  }
}
```

Changes propagate instantly via `json_watcher.py` (< 100ms).

**Key files**:
- `mcp_factory.py` - Creates MCPs from templates
- `bootstrap_loop.py` - Manages exponential generation
- `json_watcher.py` - Real-time file sync
- `mcp-schema.json` - Configuration source of truth

### Working with Second-Me

Three-layer training pipeline:
- **L0**: Raw data → embeddings
- **L1**: Embeddings → coherent memory structures (biography, topics)
- **L2**: Memory → fine-tuned LLM model (via LoRA)

**Build & run**:
```bash
make setup      # Full setup
make start      # Start all services
make test       # Run tests
make format     # Format code
```

**Key files**:
- `lpm_kernel/L0/` - Data processing
- `lpm_kernel/L1/` - Memory synthesis
- `lpm_kernel/L2/` - Model fine-tuning
- `lpm_kernel/api/` - REST/WebSocket API
- `lpm_frontend/` - Next.js UI

### Working with Filmmaker

Procedural 3D automation via Blender Python API.

**Render a scene**:
```bash
blender --background --python examples/production_render.py
# Output in renders/
```

**Key files**:
- `modules/` - 7-layer modular system
- `examples/production_render.py` - Template for batch rendering
- `.blend` files - Scene templates

### Working with Product-Spawner

Takes a seed product, generates 100+ variants.

**Generate variants**:
```bash
export ANTHROPIC_API_KEY="sk-..."
python3 sales_orchestrator.py
# Outputs: products_export.csv
```

**Configuration**:
- `product_registry.json` - Master product database
- Update via Claude API prompts in `sales_orchestrator.py`

### Working with ADAM

Multi-agent orchestration based on Agent Zero framework.

**For basic agent tasks**:
```bash
docker run -p 50001:80 agent0ai/agent-zero
# Visit http://localhost:50001
```

**For development with debugging**:
```bash
python run_ui.py --port=5000
# Add breakpoints in python/api/message.py
# Connect to Docker for code execution: Settings → Development
```

**Customize behavior**: Edit `prompts/default/` or create `prompts/custom/`

**Create tools**: Add to `python/tools/` or override in agent-specific directory

**Create extensions**: Add to `python/extensions/{extension_point}/`

See `ADAM/CLAUDE.md` for full Agent Zero documentation.

## Code Standards

### Commit Messages
Follow conventional commits (seen in git log):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- Reference issues when applicable: `fixes #123`

### Python
- Format: Ruff (Second-Me and ADAM use this)
- Version: 3.12+ required
- Tests: pytest

### TypeScript/JavaScript
- Format: Prettier
- Lint: ESLint
- Framework: Next.js 14 with App Router

### File Organization
- Python: Layered structure (L0/L1/L2), modular systems
- Frontend: app/ (pages), components/, store/, service/, types/
- Config: `pyproject.toml`, `package.json`, `Makefile`, JSON master configs

## Troubleshooting

### "Module not found" or Import Errors
**Cause**: Python environment not activated or dependencies not installed
```bash
conda activate alexandria
pip install -r requirements.txt
```

### Blender Script Fails
**Cause**: Blender not in PATH or version mismatch
```bash
# Verify Blender installation
blender --version
# Ensure 4.2+
```

### JSON-MCP-Blower Not Syncing
**Cause**: Watchdog not detecting changes or schema locked
```bash
# Verify mcp-schema.json is valid JSON
python3 -m json.tool mcp-schema.json
# Check json_watcher.py logs
```

### ADAM API Errors
**Cause**: Docker not running or port already in use
```bash
docker ps                          # Verify container is running
lsof -i :50001                    # Check if port is in use
docker run -p 50001:80 agent0ai/agent-zero
```

## Key Configuration Files

| Location | Purpose |
|----------|---------|
| `product-spawner/product_registry.json` | Master product database |
| `json-mcp-blower/mcp-schema.json` | Master MCP configuration |
| `Second-Me/pyproject.toml` | Python dependencies |
| `Second-Me/Makefile` | Build automation |
| `filmmaker-web/package.json` | Frontend dependencies |
| `ADAM/requirements.txt` | ADAM dependencies |

## Documentation References

For detailed information on each subsystem:

- **Filmmaker**: `filmmaker/README.md`
- **Product-Spawner**: `product-spawner/README.md`
- **JSON-MCP-Blower**: `json-mcp-blower/CLAUDE.md` + README.md
- **Second-Me**: `Second-Me/CLAUDE.md` + README.md
- **ADAM**: `ADAM/CLAUDE.md` + ADAM/docs/
- **Filmmaker-Web**: `filmmaker-web/README.md`
- **Root context**: `/home/ichigo/CLAUDE.md`

## Philosophy & Vision

The Alexandria system embodies several key principles:

1. **Exponential Multiplication**: Each system can generate 100+ outputs from a single input
2. **Real-time Sync**: Changes propagate instantly across the entire ecosystem
3. **Self-Optimization**: Systems learn from outputs and improve future generations
4. **Modular Architecture**: Each system works independently but integrates seamlessly
5. **Automation-First**: Minimize manual work, maximize machine work

**Vision** (in progress): A fully self-optimizing swarm system with:
- Hot-Rod NFT gaming system for code quality assessment
- Arena Controller for objective comparison of agent variants
- Zangetsu orchestrator for high-level task scheduling
- Chapel XVI audit and compliance layer

---

**Last Updated**: December 2025
**Status**: 6/7 systems production-ready
**Knowledge Coverage**: 100% of implemented systems

---
This document will now serve as the master guide for the Alexandria ecosystem.