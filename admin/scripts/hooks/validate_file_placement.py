#!/usr/bin/env python3
"""
File Placement Validator for sale-sofia project.

Validates file operations against project_structure_manifest.json rules.
Called by Claude Code hooks before file writes.

Exit codes:
    0 - Validation passed
    1 - Error (missing manifest, etc.)
    2 - Validation failed (blocks operation)

Usage:
    echo '{"tool":"Write","file_path":"/path/to/file.py"}' | python validate_file_placement.py
    python validate_file_placement.py --file-path /path/to/file.py
"""

import json
import sys
import os
import fnmatch
from pathlib import Path
from typing import Optional

# Project root detection
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]  # admin/scripts/hooks -> project root
MANIFEST_PATH = PROJECT_ROOT / "admin" / "config" / "project_structure_manifest.json"


def load_manifest() -> dict:
    """Load the project structure manifest."""
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_relative_path(file_path: str) -> Path:
    """Convert absolute path to relative path from project root."""
    abs_path = Path(file_path).resolve()
    try:
        return abs_path.relative_to(PROJECT_ROOT)
    except ValueError:
        # File is outside project
        return abs_path


def is_root_file(rel_path: Path) -> bool:
    """Check if file is at project root."""
    return len(rel_path.parts) == 1


def check_root_file_allowed(rel_path: Path, manifest: dict) -> tuple[bool, str]:
    """Check if a root file is in the allowed list."""
    filename = rel_path.name
    allowed = manifest["allowed_root_files"]

    # Check exact matches
    if filename in allowed["exact"]:
        return True, ""

    # Check patterns
    for pattern in allowed.get("patterns", []):
        if fnmatch.fnmatch(filename, pattern):
            return True, ""

    # Not allowed
    suggested = suggest_location(rel_path, manifest)
    return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: File not allowed at project root
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {filename}

Allowed root files:
  {chr(10).join('• ' + f for f in allowed['exact'])}

Suggested location: {suggested}

Reason: {allowed['reason']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def check_forbidden_at_root(rel_path: Path, manifest: dict) -> tuple[bool, str]:
    """Check if file matches forbidden patterns at root."""
    if not is_root_file(rel_path):
        return True, ""

    filename = rel_path.name
    forbidden = manifest["forbidden_at_root"]

    # Check exceptions first
    if filename in forbidden.get("except", []):
        return True, ""

    # Check forbidden extensions
    ext = rel_path.suffix.lower()
    if ext in forbidden["extensions"]:
        suggested = suggest_location(rel_path, manifest)
        return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: Extension {ext} forbidden at root
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {filename}
Suggested location: {suggested}

Reason: {forbidden['reason']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Check forbidden patterns
    for pattern in forbidden["patterns"]:
        if fnmatch.fnmatch(filename, pattern):
            suggested = suggest_location(rel_path, manifest)
            return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: Pattern '{pattern}' forbidden at root
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {filename}
Matched pattern: {pattern}
Suggested location: {suggested}

Reason: {forbidden['reason']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return True, ""


def get_directory_key(rel_path: Path) -> Optional[str]:
    """Find the manifest directory key for a file path."""
    # Build path from parts to find matching directory
    for i in range(len(rel_path.parts) - 1, 0, -1):
        dir_path = "/".join(rel_path.parts[:i]) + "/"
        if dir_path in ["./", ""]:
            continue
        # Return most specific match
        return dir_path if dir_path else None
    return None


def find_matching_directory(rel_path: Path, manifest: dict) -> Optional[tuple[str, dict]]:
    """Find the most specific matching directory rule."""
    directories = manifest["directories"]

    # Try progressively shorter paths
    parts = rel_path.parts[:-1]  # Exclude filename

    for i in range(len(parts), 0, -1):
        dir_key = "/".join(parts[:i]) + "/"
        if dir_key in directories:
            return dir_key, directories[dir_key]

    return None, None


def check_max_depth(rel_path: Path, manifest: dict) -> tuple[bool, str]:
    """Check if file path exceeds maximum allowed depth."""
    global_rules = manifest.get("global_rules", {})
    max_depth = global_rules.get("max_depth")

    if max_depth is None:
        return True, ""

    # Count directory depth (excluding filename)
    parts = rel_path.parts[:-1]  # Exclude filename
    depth = len(parts)

    if depth > max_depth:
        return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: Directory depth exceeds maximum
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {rel_path}
Current depth: {depth} directories
Maximum allowed: {max_depth} directories

Path breakdown:
  {' / '.join(parts)} / {rel_path.name}
  {'─' * 3} {'───' * (depth - max_depth)} ← Too deep

Reason: {global_rules.get('max_depth_reason', 'Keeps project structure flat')}

Move file to a shallower location.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return True, ""


def check_directory_blocks_files(rel_path: Path, dir_key: str, dir_rules: dict) -> tuple[bool, str]:
    """Check if directory blocks direct file placement (requires subdirectory)."""
    if not dir_rules.get("block_root_files", False):
        return True, ""

    # Check if file is directly in this directory (not in a subdirectory)
    parts = rel_path.parts[:-1]  # Exclude filename
    dir_parts = dir_key.rstrip("/").split("/")

    # If file is exactly one level deep in this directory, it's blocked
    if len(parts) == len(dir_parts):
        allowed_subdirs = dir_rules.get("allowed_subdirs", [])
        return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: Files not allowed directly in {dir_key}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {rel_path}
Directory: {dir_key}

This directory should only contain subdirectories, not files.

Required subdirectories:
  {chr(10).join('• ' + dir_key + s + '/' for s in allowed_subdirs)}

Move file to one of the subdirectories above.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return True, ""


def check_extension_allowed(rel_path: Path, dir_key: str, dir_rules: dict) -> tuple[bool, str]:
    """Check if file extension is allowed in this directory."""
    # First check if directory blocks all files
    if dir_rules.get("block_root_files", False):
        parts = rel_path.parts[:-1]
        dir_parts = dir_key.rstrip("/").split("/")
        if len(parts) == len(dir_parts):
            # This will be caught by check_directory_blocks_files
            return True, ""

    ext = rel_path.suffix.lower()
    allowed_exts = dir_rules.get("allowed_extensions", [])

    if not allowed_exts:  # Empty means NO extensions allowed (block all)
        if dir_rules.get("block_root_files", False):
            return True, ""  # Handled by check_directory_blocks_files
        return True, ""  # Otherwise allow all

    if ext in allowed_exts:
        return True, ""

    return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ BLOCKED: Extension not allowed in directory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {rel_path}
Extension: {ext}
Directory: {dir_key}

Allowed extensions: {', '.join(allowed_exts) if allowed_exts else '(none - files not allowed)'}
Purpose: {dir_rules.get('purpose', 'N/A')}

Move file to appropriate directory or use allowed extension.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def check_implicit_mkdir(rel_path: Path, manifest: dict) -> tuple[bool, str]:
    """Check if this write would create directories not in manifest."""
    directories = manifest["directories"]
    parts = rel_path.parts[:-1]  # Exclude filename

    if not parts:
        return True, ""  # Root file, no dirs to create

    # Check each parent directory level
    for i in range(1, len(parts) + 1):
        dir_path = "/".join(parts[:i]) + "/"
        parent_path = "/".join(parts[:i-1]) + "/" if i > 1 else None

        # Check if this directory exists in manifest
        if dir_path not in directories:
            # Check if parent allows new subdirs
            if parent_path and parent_path in directories:
                parent_rules = directories[parent_path]
                allowed_subdirs = parent_rules.get("allowed_subdirs", [])
                block_new = parent_rules.get("block_new_subdirs", False)

                subdir_name = parts[i-1]

                if block_new and subdir_name not in allowed_subdirs:
                    return False, f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  WARNING: Would create new subdirectory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {rel_path}
Would create: {dir_path}
Parent: {parent_path}

Allowed subdirectories in {parent_path}:
  {chr(10).join('• ' + s for s in allowed_subdirs) if allowed_subdirs else '  (none)'}

This directory is not in manifest.
Use an existing directory or ask user to confirm.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return True, ""


def suggest_location(rel_path: Path, manifest: dict) -> str:
    """Suggest where a file should go based on its type."""
    filename = rel_path.name
    ext = rel_path.suffix.lower()

    routing = manifest.get("file_type_routing", {})

    if ext in routing:
        rules = routing[ext]

        # Check exceptions first
        for pattern, location in rules.get("exceptions", {}).items():
            if fnmatch.fnmatch(filename, pattern):
                if location == "ROOT":
                    return "project root (allowed exception)"
                return location

        # Return default
        default = rules.get("default", "CONTEXT_DEPENDENT")
        if default != "CONTEXT_DEPENDENT":
            return default

    # Fallback suggestions based on common patterns
    if ext == ".md":
        if "test" in filename.lower() or "result" in filename.lower():
            return "tests/stress/ or tests/debug/"
        return "docs/<appropriate_subfolder>/"
    elif ext == ".py":
        if filename.startswith("test_"):
            return "tests/"
        return "appropriate module folder"
    elif ext == ".json":
        return "config/ or module folder"
    elif ext == ".log":
        return "data/logs/"
    elif ext in [".db", ".sqlite"]:
        return "data/"

    return "appropriate subdirectory"


def validate_file_path(file_path: str, manifest: dict) -> tuple[bool, str]:
    """
    Main validation function.

    Returns:
        (passed: bool, message: str)
    """
    rel_path = get_relative_path(file_path)

    # Skip validation for files outside project
    if rel_path.is_absolute():
        return True, ""

    # 1. Check max depth FIRST (applies to all files)
    passed, msg = check_max_depth(rel_path, manifest)
    if not passed:
        return False, msg

    # 2. Check root files
    if is_root_file(rel_path):
        # Check if forbidden pattern
        passed, msg = check_forbidden_at_root(rel_path, manifest)
        if not passed:
            return False, msg

        # Check if allowed
        passed, msg = check_root_file_allowed(rel_path, manifest)
        if not passed:
            return False, msg

        return True, ""

    # 3. Find matching directory rule
    dir_key, dir_rules = find_matching_directory(rel_path, manifest)

    if dir_rules:
        # 4. Check if directory blocks direct files (requires subdirectory)
        passed, msg = check_directory_blocks_files(rel_path, dir_key, dir_rules)
        if not passed:
            return False, msg

        # 5. Check extension allowed
        passed, msg = check_extension_allowed(rel_path, dir_key, dir_rules)
        if not passed:
            return False, msg

    # 6. Check implicit mkdir
    passed, msg = check_implicit_mkdir(rel_path, manifest)
    if not passed:
        # This is a warning, not a block
        print(msg, file=sys.stderr)
        # Still allow but warn

    return True, ""


def parse_input() -> str:
    """Parse input from stdin (JSON) or command line."""
    # Check command line args
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--file-path" and i + 1 < len(sys.argv):
                return sys.argv[i + 1]

    # Try stdin
    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            # Handle Claude Code hook format
            if "tool_input" in data:
                tool_input = data["tool_input"]
                if isinstance(tool_input, str):
                    tool_input = json.loads(tool_input)
                return tool_input.get("file_path", "")
            return data.get("file_path", "")
        except json.JSONDecodeError:
            pass

    return ""


def main():
    """Main entry point."""
    file_path = parse_input()

    if not file_path:
        print("Usage: validate_file_placement.py --file-path /path/to/file", file=sys.stderr)
        print("   or: echo '{\"file_path\":\"/path\"}' | validate_file_placement.py", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest()

    passed, message = validate_file_path(file_path, manifest)

    if not passed:
        print(message, file=sys.stderr)
        sys.exit(2)  # Block the operation

    # Passed
    sys.exit(0)


if __name__ == "__main__":
    main()
