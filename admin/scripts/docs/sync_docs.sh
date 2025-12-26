#!/bin/bash
# Wrapper script to run docs_scraper.py with project venv
# Usage: ./sync_docs.sh [args]
# Examples:
#   ./sync_docs.sh --list
#   ./sync_docs.sh --lib scrapling
#   ./sync_docs.sh  # sync all

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "Error: venv not found at $PROJECT_ROOT/venv"
    echo "Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/docs_scraper.py" "$@"
