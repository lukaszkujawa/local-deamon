#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [search query]"
  exit 1
fi

QUERY="$*"
ENCODED_Q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$QUERY")

curl -sS "http://127.0.0.1:8001/search?q=${ENCODED_Q}&max_results=10"
echo