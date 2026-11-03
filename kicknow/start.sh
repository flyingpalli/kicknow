#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8080}"
ALT_PORT=$((PORT + 1))

echo "KickNow Server starting..."
echo "Local access: http://localhost:$PORT"
echo "Network access (HTTP):"
ip -4 addr show scope global | awk -v p="$PORT" -v ap="$ALT_PORT" '/inet / {sub(/\/.*/, "", $2); print "  http://" $2 ":" p "  (or http://" $2 ":" ap ")"}'
echo "Network access (HTTPS for iOS GPS):"
ip -4 addr show scope global | awk -v p="$PORT" '/inet / {sub(/\/.*/, "", $2); print "  https://" $2 ":" p}'
echo ""
echo "Press Ctrl+C to stop the server."

exec python3 "$DIR/server/server.py" "$PORT" "$DIR"
