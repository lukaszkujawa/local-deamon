#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [url to fetch]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [[ -f "$ENV_FILE" ]]; then
  HOST_GET_URL=$(grep '^HOST_GET_URL=' "$ENV_FILE" | cut -d= -f2)
fi

HOST_GET_URL="${HOST_GET_URL:-http://127.0.0.1:8000}"

URL="$1"
ENCODED_URL=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$URL")

curl -sS "${HOST_GET_URL}/fetch_content?url=${ENCODED_URL}&text_only=true"
echo