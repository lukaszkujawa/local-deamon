#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [url to fetch]"
  exit 1
fi

URL="$1"
ENCODED_URL=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$URL")

curl -sS "http://127.0.0.1:8000/fetch_content?url=${ENCODED_URL}&text_only=true"
echo