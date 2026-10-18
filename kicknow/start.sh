#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8080}"

echo "KickNow Server starting on port $PORT"
echo "Local access: http://localhost:$PORT"
echo "iPhone access in local network:"
ip -4 addr show scope global | awk -v p="$PORT" '/inet / {sub(/\/.*/, "", $2); print "  http://" $2 ":" p}'
echo ""
echo "Press Ctrl+C to stop the server."

exec python3 -m http.server "$PORT" --directory "$DIR"
