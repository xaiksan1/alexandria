#!/usr/bin/env bash
# Regenerates the self-signed TLS cert used by the RAM Couche 0 nginx gateway.
# Never committed (see .gitignore) — run this once per machine before build-and-scan.sh.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p certs
openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
  -keyout certs/guacamole.key \
  -out certs/guacamole.crt \
  -subj "/CN=localhost/O=Alexandria RAM Gateway"
chmod 600 certs/guacamole.key
echo "Certs (re)generated in $(pwd)/certs/"
