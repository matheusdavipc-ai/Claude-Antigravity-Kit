#!/bin/bash
set -euo pipefail
kit_root="$(cd "$(dirname "$0")" && pwd)"
bash "$kit_root/install.sh" "$@"
