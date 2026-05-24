#!/usr/bin/env bash
# Bootstrap the venv that docs/demo.tape replays against.
#
# Usage:
#   ./scripts/bootstrap-demo.sh
#
# After this, regenerate the README hero with:
#   vhs docs/demo.tape && cp docs/demo.gif pip-skill-demo.gif
set -euo pipefail

VENV=/tmp/pip-skill-demo-env

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install: https://docs.astral.sh/uv/" >&2
  exit 1
fi

if ! command -v vhs >/dev/null 2>&1; then
  echo "vhs not found. Install: brew install vhs (or see https://github.com/charmbracelet/vhs)" >&2
  exit 1
fi

rm -rf "$VENV"
uv venv "$VENV" --python 3.11
# shellcheck disable=SC1091
source "$VENV/bin/activate"
uv pip install requests
# Editable install of the local pip-skill checkout.
uv pip install -e "$(cd "$(dirname "$0")/.." && pwd)"

echo
echo "Demo venv ready at $VENV"
echo "Now run: vhs docs/demo.tape"
