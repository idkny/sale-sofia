#!/usr/bin/env python3
"""
Function Length Validator for sale-sofia project.

Validates Python files to ensure functions don't exceed length limits.
Called by Claude Code hooks before file writes.

Exit codes:
    0 - Validation passed
    1 - Error (not a Python file, parse error, etc.)
    2 - Validation failed (blocks operation)

Usage:
    python validate_function_length.py --file-path /path/to/file.py
    python validate_function_length.py --file-path /path/to/file.py --content "$(cat file.py)"

Environment variables:
    SKIP_FUNCTION_LENGTH_CHECK=1  - Skip validation (for refactoring existing violations)
    FUNCTION_LENGTH_WARN_ONLY=1   - Warn but don't block (for legacy files)
"""

import ast
import os
import sys
from pathlib import Path
from typing import Optional


# Limits from CONVENTIONS.md
HARD_LIMIT = 50  # Maximum allowed - exceeding blocks the write
SOFT_LIMIT = 30  # Warning threshold

# Files with known violations (legacy) - warn only, don't block
# Remove from this list after refactoring
# NOTE: Cleared 2025-12-26 after completing all refactoring tasks
LEGACY_FILES: set[str] = set()

# Project root detection
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]  # admin/scripts/hooks -> project root


def get_relative_path(file_path: str) -> Path:
    """Convert absolute path to relative path from project root."""
    abs_path = Path(file_path).resolve()
    try:
        return abs_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return abs_path


def parse_python_file(content: str) -> Optional[ast.AST]:
    """Parse Python content into AST."""
    try:
        return ast.parse(content)
    except SyntaxError:
        return None


def get_function_length(node: ast.AST) -> int:
    """Calculate the line count of a function."""
    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
        return node.end_lineno - node.lineno + 1
    return 0


def find_long_functions(tree: ast.AST, file_path: str) -> tuple[list, list]:
    """
    Find functions exceeding length limits.

    Returns:
        (violations: list of functions > HARD_LIMIT,
         warnings: list of functions > SOFT_LIMIT but <= HARD_LIMIT)
    """
    violations = []
    warnings = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = get_function_length(node)

            # Get class context if any
            class_name = None
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef):
                    for child in ast.iter_child_nodes(parent):
                        if child is node:
                            class_name = parent.name
                            break

            func_info = {
                'name': node.name,
                'class': class_name,
                'start_line': node.lineno,
                'end_line': node.end_lineno,
                'length': length,
                'full_name': f"{class_name}.{node.name}" if class_name else node.name,
            }

            if length > HARD_LIMIT:
                violations.append(func_info)
            elif length > SOFT_LIMIT:
                warnings.append(func_info)

    return violations, warnings


def format_violation_message(violations: list, warnings: list, rel_path: Path) -> str:
    """Format the error message for violations."""
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "❌ BLOCKED: Function length exceeds limit",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"File: {rel_path}",
        f"Hard limit: {HARD_LIMIT} lines | Soft limit: {SOFT_LIMIT} lines",
        "",
    ]

    if violations:
        lines.append("VIOLATIONS (must fix):")
        for v in violations:
            lines.append(f"  • {v['full_name']}() - {v['length']} lines (lines {v['start_line']}-{v['end_line']})")
            lines.append(f"    Exceeds limit by {v['length'] - HARD_LIMIT} lines")
        lines.append("")

    if warnings:
        lines.append("WARNINGS (consider refactoring):")
        for w in warnings:
            lines.append(f"  • {w['full_name']}() - {w['length']} lines (lines {w['start_line']}-{w['end_line']})")
        lines.append("")

    lines.extend([
        "How to fix:",
        "  1. Split into smaller helper functions (prefix with _)",
        "  2. Extract repeated logic into separate functions",
        "  3. Group related operations into helper functions",
        "",
        "See: docs/architecture/CONVENTIONS.md (Code Quality Standards)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])

    return "\n".join(lines)


def format_warning_message(warnings: list, rel_path: Path) -> str:
    """Format warning message (no violations, just warnings)."""
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️  WARNING: Functions approaching length limit",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"File: {rel_path}",
        f"Soft limit: {SOFT_LIMIT} lines | Hard limit: {HARD_LIMIT} lines",
        "",
        "Consider refactoring:",
    ]

    for w in warnings:
        lines.append(f"  • {w['full_name']}() - {w['length']} lines")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])

    return "\n".join(lines)


def is_legacy_file(rel_path: Path) -> bool:
    """Check if file is in the legacy list (known violations)."""
    rel_str = str(rel_path)
    for legacy in LEGACY_FILES:
        if rel_str == legacy or rel_str.endswith("/" + legacy):
            return True
    return False


def validate_file(file_path: str, content: Optional[str] = None) -> tuple[bool, str]:
    """
    Validate a Python file for function length.

    Args:
        file_path: Path to the Python file
        content: Optional content (for validating before write)

    Returns:
        (passed: bool, message: str)
    """
    # Check for skip environment variable
    if os.environ.get("SKIP_FUNCTION_LENGTH_CHECK") == "1":
        return True, ""

    path = Path(file_path)
    rel_path = get_relative_path(file_path)

    # Only validate Python files
    if path.suffix.lower() != '.py':
        return True, ""

    # Skip test files - they often have long test functions
    if path.name.startswith('test_') or '/tests/' in str(path):
        return True, ""

    # Check if this is a legacy file (warn only, don't block)
    warn_only = os.environ.get("FUNCTION_LENGTH_WARN_ONLY") == "1" or is_legacy_file(rel_path)

    # Get content
    if content is None:
        if not path.exists():
            return True, ""  # New file, will validate on actual write
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            return True, f"Warning: Could not read file: {e}"

    # Parse Python
    tree = parse_python_file(content)
    if tree is None:
        # Syntax error - let Python handle it, not our job
        return True, ""

    # Find long functions
    violations, warnings = find_long_functions(tree, file_path)

    # Block if violations (unless warn_only mode)
    if violations:
        if warn_only:
            # Legacy file - warn but allow
            msg = format_violation_message(violations, warnings, rel_path)
            # Replace "BLOCKED" with "WARNING (legacy file)"
            msg = msg.replace("❌ BLOCKED:", "⚠️  WARNING (legacy file):")
            msg = msg.replace("VIOLATIONS (must fix):", "VIOLATIONS (fix when refactoring):")
            print(msg, file=sys.stderr)
            return True, ""  # Allow but warn
        else:
            return False, format_violation_message(violations, warnings, rel_path)

    # Warn if approaching limit (but don't block)
    if warnings:
        print(format_warning_message(warnings, rel_path), file=sys.stderr)

    return True, ""


def parse_args() -> tuple[str, Optional[str]]:
    """Parse command line arguments."""
    file_path = ""
    content = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--file-path" and i + 1 < len(sys.argv):
            file_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--content" and i + 1 < len(sys.argv):
            content = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    return file_path, content


def main():
    """Main entry point."""
    file_path, content = parse_args()

    if not file_path:
        print("Usage: validate_function_length.py --file-path /path/to/file.py", file=sys.stderr)
        print("       validate_function_length.py --file-path /path/to/file.py --content '...'", file=sys.stderr)
        sys.exit(1)

    passed, message = validate_file(file_path, content)

    if not passed:
        print(message, file=sys.stderr)
        sys.exit(2)  # Block the operation

    sys.exit(0)


if __name__ == "__main__":
    main()
