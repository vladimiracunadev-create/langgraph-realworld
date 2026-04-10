#!/usr/bin/env bash
# nginx/scripts/gen-certs.sh
# Generates a self-signed TLS certificate for local development.
#
# Output: nginx/certs/server.crt + nginx/certs/server.key
#
# Usage:
#   bash nginx/scripts/gen-certs.sh
#
# For production, replace nginx/certs/ with real certificates from:
#   - Let's Encrypt (certbot) — recommended for public demos
#   - Your organization's CA
#
# Requires: openssl

set -euo pipefail

CERTS_DIR="$(dirname "$0")/../certs"
mkdir -p "$CERTS_DIR"

echo "Generating self-signed TLS certificate (dev only)..."

openssl req -x509 -nodes \
  -newkey rsa:2048 \
  -keyout "$CERTS_DIR/server.key" \
  -out    "$CERTS_DIR/server.crt" \
  -days   365 \
  -subj   "/C=US/ST=Dev/L=Local/O=LangGraph-Realworld/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERTS_DIR/server.key"
chmod 644 "$CERTS_DIR/server.crt"

echo ""
echo "Certificates written to $CERTS_DIR/"
echo "  server.crt  (public certificate)"
echo "  server.key  (private key — keep secret)"
echo ""
echo "WARNING: This is a self-signed certificate for development only."
echo "Browsers will show a security warning. Accept it to proceed."
echo "For public demos use a real cert (Let's Encrypt / certbot)."
