# Second-Me: Personal AI Self-Training System

**Second-Me** is a three-layer training pipeline (L0/L1/L2) that creates a personalized AI digital twin trained on your expertise, writing style, and problem-solving approaches.

## Architecture

```
L0: Raw Data → Unstructured inputs (CV, code, docs, communications)
  ↓
L1: Memory Synthesis → Structured knowledge (biography, expertise, patterns)
  ↓
L2: Model Fine-tuning → LoRA adapters for Claude/GPT-4 (4 specialized models)
```

## Quick Start

```bash
cd /home/ichigo/alexandria/Second-Me
make setup              # Install dependencies
make start              # Launch services
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

## Layers

### L0 (Raw Data)
- CV and professional profile
- Code samples and repositories
- Project documentation
- Problem-solving patterns
- Communication samples

### L1 (Memory Synthesis)
- Biography generation
- Expertise domain mapping
- Problem-solving pattern extraction
- Preference identification

### L2 (Model Fine-tuning)
- Architect model (system design)
- Developer model (code generation)
- Analyst model (problem analysis)
- Collaborator model (communication)

## Integration

Your digital twin integrates with:
- **ADAM** → Autonomous multi-agent orchestration
- **JSON-MCP-Blower** → 101 agent deployment
- **Energon Ledger** → Energy-aware operations
- **Hot-Rod** → Quality gamification

## Status

✅ Production Ready (integrated with energy-tech system)

---

**Part of Alexandria Energy-Tech Ecosystem**
