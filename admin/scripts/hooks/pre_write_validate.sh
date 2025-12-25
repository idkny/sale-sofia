#!/bin/bash
# Pre-write validation hook for Claude Code
#
# Called before Write/Edit operations to validate file placement.
# Reads JSON from stdin, validates file path, returns exit code.
#
# Exit codes:
#   0 - Allowed (continue with operation)
#   2 - Blocked (stop operation)

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Read stdin into variable
INPUT=$(cat)

# Extract tool name
TOOL=$(echo "$INPUT" | jq -r '.tool // empty' 2>/dev/null || echo "")

# Only validate Write and Edit operations
if [[ "$TOOL" != "Write" && "$TOOL" != "Edit" ]]; then
    exit 0
fi

# Extract file_path from tool_input
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // empty' 2>/dev/null || echo "")

# tool_input might be a string (JSON) or object
if echo "$TOOL_INPUT" | jq -e 'type == "object"' > /dev/null 2>&1; then
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty' 2>/dev/null || echo "")
else
    # Try parsing as JSON string
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '. | fromjson? | .file_path // empty' 2>/dev/null || echo "")
fi

# If no file path found, allow operation
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip validation for files outside project
if [[ ! "$FILE_PATH" == "$PROJECT_ROOT"* && ! "$FILE_PATH" == "./"* ]]; then
    # Check if it's a relative path within project
    if [[ "$FILE_PATH" != /* ]]; then
        FILE_PATH="$PROJECT_ROOT/$FILE_PATH"
    else
        # Absolute path outside project - skip
        exit 0
    fi
fi

# Skip .claude/ files (protected but allowed)
if [[ "$FILE_PATH" == *"/.claude/"* ]]; then
    exit 0
fi

# Skip tmp directories
if [[ "$FILE_PATH" == */tmp/* || "$FILE_PATH" == /tmp/* ]]; then
    exit 0
fi

# Run Python validator
VALIDATOR="$SCRIPT_DIR/validate_file_placement.py"

if [[ ! -f "$VALIDATOR" ]]; then
    echo "WARNING: Validator script not found at $VALIDATOR" >&2
    exit 0
fi

# Pass file path to validator
if python3 "$VALIDATOR" --file-path "$FILE_PATH"; then
    exit 0
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 2 ]]; then
        # Blocked - validator already printed message
        exit 2
    fi
    # Other errors - warn but allow
    exit 0
fi
