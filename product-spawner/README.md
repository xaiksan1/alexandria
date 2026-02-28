# Product-Spawner: Algorithmic Product Variant Generation

**Product-Spawner** generates 100+ market-targeted product variants from a single seed product using Claude API. Each variant is optimized for specific market niches, customer segments, and revenue channels.

## Quick Start

```bash
cd /home/ichigo/alexandria/product-spawner
export ANTHROPIC_API_KEY="sk-..."
python3 sales_orchestrator.py --seed "Your Product Idea"
```

Output: `products_export.csv` with 100+ variants

## Architecture

- **sales_orchestrator.py** - Main orchestrator (variant generation pipeline)
- **product_registry.json** - Master product database
- **products_export.csv** - Generated variants (output)
- **energy_integration.py** - Energon ledger tracking

## Integration

Product variants feed into:
- **Filmmaker** → Render 3D assets for each variant
- **JSON-MCP-Blower** → Deploy as agent swarms
- **ADAM** → Orchestrate variant distribution
- **Energon Ledger** → Track energy cost per variant

## Configuration

Edit `product_registry.json` to customize:
- Market segments
- Price ranges
- Feature combinations
- Revenue channels
- Customer personas

## Status

✅ Production Ready (integrated with energy-tech system)

---

**Part of Alexandria Energy-Tech Ecosystem**
