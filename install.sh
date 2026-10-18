#!/bin/bash
set -euo pipefail
kit_root="$(cd "$(dirname "$0")" && pwd)"
kit_python="${CLAUDE_KIT_PYTHON:-python3}"
if ! command -v "$kit_python" >/dev/null 2>&1; then
  echo 'Instale Python 3.12+ (python.org ou brew install python@3.12) e execute novamente.' >&2
  exit 1
fi
"$kit_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)'
if [[ " ${*:-} " == *' --dry-run '* ]]; then
  exec "$kit_python" "$kit_root/install.py" "$@"
fi
if [[ "$(uname -s)" != 'Darwin' ]]; then echo 'Este instalador destina-se ao macOS.' >&2; exit 1; fi
if ! command -v node >/dev/null 2>&1; then echo 'Instale Node.js LTS 22+ (nodejs.org ou brew install node@22).' >&2; exit 1; fi
node -e 'const v=process.versions.node.split(".").map(Number);process.exit(v[0]>22||(v[0]===22&&v[1]>=19)?0:1)'
kit_native="$HOME/.local/bin/claude"
if [[ ! -x "$kit_native" ]]; then
  kit_download="$(mktemp)"
  trap 'rm -f "$kit_download"' EXIT
  curl -fSL https://claude.ai/install.sh -o "$kit_download"
  bash "$kit_download"
  rm -f "$kit_download"
  trap - EXIT
fi
if ! command -v omniroute >/dev/null 2>&1; then npm install -g omniroute@3.8.51; fi
"$kit_python" "$kit_root/install.py" "$@"
"$kit_python" "$kit_root/scripts/configure_omniroute.py"
