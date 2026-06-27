# Alexandria → GCP Migration State
# VM cible: e2-standard-4 · us-central1-a · Debian 12
# Projet GCP : enhanced-scion-6nhr3 (express-mode)
# IP publique : 34.121.61.249
# IP Tailscale : 100.92.251.116
# Hostname Tailscale : alexandria-vm

## Phase 0 — Préparation Crostini ✓ COMPLÈTE
## Phase 1 — VM GCP + IP statique + firewall ✓ COMPLÈTE
## Phase 2 — Setup base (uv, bun, Docker, Node.js, pm2, Tailscale) ✓ COMPLÈTE
## Phase 3 — Clone repo GitHub ✓ COMPLÈTE
## Phase 4 — Cloud SQL ✓ COMPLÈTE
# Cloud SQL IP : 34.31.72.136
# Instance     : alexandria-db (Postgres 17 · Enterprise · db-custom-1-3840)
# Databases    : bifrost_db · activepieces_db
# Users        : bifrost_user · ap_user

### Processus pm2 (39 total)
- Online: 30 | Stopped: 9 | RAM totale: ~2.4 GB

### Services à migrer sur GCP (VM)
| Service | Port | Type | Priorité |
|---------|------|------|----------|
| phoenix_observer | 8000 | Python FastAPI | 1 — bus d'événements |
| seshat | 5013 | Python FastAPI | 2 — MCP graph |
| seshat-ui | 5014 | Node.js | 2 |
| aegis | 4400 | Python | 3 |
| chapel_xvi_vault | 4600 | Python | 3 |
| jarvis | 5055 | Python FastAPI | 4 — orchestrateur |
| sentinelle | 4444 | Python | 4 |
| tartarus_prison | 4343 | Python | 4 |
| floatilla_agent | 4242 | Python | 4 |
| paint_shop | 4141 | Python | 4 |
| labyrinthe_navigator | — | Python | 5 |
| minotaure_gatekeeper | — | Python | 5 |
| iothackbot_agent | — | Python | 5 |
| zangetsu_guardian | — | Python | 5 |
| zangetsu_security | — | Python | 5 |
| commerce | 5050 | Python | 3 — Tim-Burner |
| bifrost | 8090 | Docker | 2 — LLM proxy |
| instant-lee | 4112 | Node.js | 3 |
| mini-adam-router | — | Node.js | 4 |
| mini-adam-runner | — | Node.js | 4 |
| ghost-listener | — | Bun | 4 |
| ghost-writer | — | Bun | 4 |
| ads-bid-engine | — | Python | 5 |
| ads-cache | — | Python | 5 |
| inspector | — | Python | 5 |
| engine-v5 | — | Python | 5 |
| cpu-bridge | — | Python | 5 |
| envii-connector | — | Node.js | 4 |
| cortex-v3 | — | Python | 4 |
| serena_agent | — | Python | 4 |
| alexandria-orbit | — | Python | 5 |
| alexa_api | — | Python | 5 |
| multilspy_server | — | Python | 5 |
| free-claude-proxy | 8082 | Node.js | 4 |
| pheromone-mcp | 5012 | Node.js | 3 |
| tunnel-pheromone | — | — | ✗ SUPPRIMER (Vercel remplace) |

### Docker sur GCP (reconstituer)
| Container | Migration |
|-----------|-----------|
| bifrost | docker compose up — même config |
| bifrost-db | → Cloud SQL Postgres 17 |
| activepieces | docker compose up |
| activepieces-postgres | → Cloud SQL Postgres 17 |
| activepieces-redis | reste Docker (petit) |
| alexandria-tidb | ✗ ne PAS migrer — TiDB Cloud est le vrai backend |

### Reste LOCAL (ne migre JAMAIS)
| Service | Raison |
|---------|--------|
| chromium-cdp | DISPLAY=:0 requis |
| paperclip | dépend du CDP local |
| claude-context-mode | stdio MCP local |
| tunnel-pheromone | remplacé par Vercel |

### Secrets à migrer → GCP Secret Manager
- [ ] `/home/ichigo/.config/alexandria/tidb.env` → template: env-templates/tidb.env.template
- [ ] `/home/ichigo/.config/free-claude-code/.env` → template: env-templates/free-claude-code.env.template
- [ ] `/home/ichigo/alexandria/ADAM/.env` → template: env-templates/adam.env.template
- [ ] `/home/ichigo/alexandria/ADAM/FORGE/activepieces/.env` → template: env-templates/activepieces.env.template
- [ ] `/home/ichigo/alexandria/ADAM/bifrost/.env` → template: env-templates/bifrost.env.template
- [ ] `/home/ichigo/alexandria/paperclip/.env` → template: env-templates/paperclip.env.template
- [ ] `/home/ichigo/alexandria/mini-adam/.env` (JWT_SECRET)

## Checklist Phase 0

- [x] pm2 dump (`~/.pm2/dump.pm2` — 39 processus)
- [x] Audit .env — 7 fichiers identifiés, templates créés
- [x] Audit Docker — 6 containers, plan Cloud SQL défini
- [x] RAM inventaire — 2.4 GB → `e2-standard-4` confortable
- [ ] Push git propre (alexandria/ uniquement)
- [ ] Vérifier .gitignore couvre bien les .env

## Phases suivantes

- Phase 1: Créer VM GCP + IP statique + firewall
- Phase 2: Setup base (uv, bun, Docker, pm2, Tailscale)
- Phase 3: Clone repo GitHub → VM
- Phase 4: Cloud SQL (Postgres bifrost + activepieces)
- Phase 5: Docker services
- Phase 6: pm2 resurrect (ordre: Phoenix → SESHAT → AEGIS → Jarvis → modules)
- Phase 7: Validation santé
- Phase 8: Pointer ~/.claude.json + DNS
