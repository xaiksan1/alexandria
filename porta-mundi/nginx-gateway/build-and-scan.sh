#!/usr/bin/env bash
# RAM Couche 0 nginx gateway — build + Snyk gate.
# Blocks (non-zero exit) on high/critical vulns BEFORE the image is used or
# any change here is pushed to GitHub. Snyk already scans the repo after
# publish; this catches container-level CVEs before that point, since nginx
# is a frequent attack target and this gateway runs unattended (agents, not
# a human watching it).
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="alexandria/ram-nginx-gateway:latest"
SEVERITY_THRESHOLD="high"

if [ ! -f certs/guacamole.crt ] || [ ! -f certs/guacamole.key ]; then
  echo "[build-and-scan] No certs found — generating..."
  ./generate-certs.sh
fi

echo "[build-and-scan] Building ${IMAGE}..."
docker build -t "${IMAGE}" .

echo "[build-and-scan] Running Snyk container scan (severity >= ${SEVERITY_THRESHOLD})..."
if ! snyk container test "${IMAGE}" --severity-threshold="${SEVERITY_THRESHOLD}" --file=Dockerfile; then
  echo ""
  echo "[build-and-scan] ❌ BLOCKED — Snyk found ${SEVERITY_THRESHOLD}+ severity vulnerabilities."
  echo "[build-and-scan] Fix the base image/config (or bump nginx:alpine tag) before deploying or pushing."
  exit 1
fi

echo "[build-and-scan] ✅ Snyk scan clean (< ${SEVERITY_THRESHOLD} severity). Image ready: ${IMAGE}"
