#!/bin/bash
# Génère les .env sur la VM GCP — à exécuter depuis ~/alexandria sur la VM
# Remplir les valeurs marquées FILL_ME depuis les .env locaux Crostini
# Cloud SQL IP: 34.31.72.136

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[1/2] Bifrost .env"
cat > "$REPO_DIR/ADAM/bifrost/.env" <<'EOF'
NVIDIA_NIM_API_KEY=FILL_ME
OPENROUTER_API_KEY=FILL_ME
DEEPSEEK_API_KEY=FILL_ME
BIFROST_PG_PASSWORD=bifrost2026!
POSTGRES_HOST=34.31.72.136
POSTGRES_PORT=5432
POSTGRES_USER=bifrost_user
POSTGRES_DB=bifrost_db
EOF

echo "[2/2] Activepieces .env"
cat > "$REPO_DIR/ADAM/FORGE/activepieces/.env" <<'EOF'
AP_ENGINE_EXECUTABLE_PATH=dist/packages/engine/main.js
AP_QUEUE_MODE=REDIS
AP_REDIS_URL=redis://activepieces-redis:6379
AP_POSTGRES_DATABASE=activepieces_db
AP_POSTGRES_USERNAME=ap_user
AP_POSTGRES_PASSWORD=activepieces2026!
AP_POSTGRES_HOST=34.31.72.136
AP_POSTGRES_PORT=5432
AP_FRONTEND_URL=http://34.121.61.249:9030
AP_TELEMETRY_ENABLED=false
AP_SIGN_UP_ENABLED=false
AP_EXECUTION_MODE=UNSANDBOXED
AP_ENCRYPTION_KEY=d4704cece845834189d65fca4f484243
AP_JWT_SECRET=-mXB53E3kVR6oCtogXbb5o2Tm-BaT5CT7BX2i8jYAIM
EOF

echo "✓ .env créés — remplir les FILL_ME dans ADAM/bifrost/.env"
