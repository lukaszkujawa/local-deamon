#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [search query]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [[ -f "$ENV_FILE" ]]; then
  HOST_WEB_SEARCH=$(grep '^HOST_WEB_SEARCH=' "$ENV_FILE" | cut -d= -f2)
fi

HOST_WEB_SEARCH="${HOST_WEB_SEARCH:-http://127.0.0.1:8001}"

QUERY="$*"
ENCODED_Q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$QUERY")

curl -sS "${HOST_WEB_SEARCH}/search?q=${ENCODED_Q}&max_results=8"
echo
