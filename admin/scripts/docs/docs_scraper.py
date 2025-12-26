#!/usr/bin/env python3
"""
id: 20251208_153700_docs_scraper
type: script
subject: documentation-sync
description: |
    GitHub Documentation Scraper for local LLM context.
    Fetches markdown docs from GitHub repos and combines into single files.
    Similar to Context7 but fully local and free.
created_at: 2025-12-08
updated_at: 2025-12-08
tags: [documentation, github, scraper, llm]

Usage:
    python docs_scraper.py                    # Sync all libraries
    python docs_scraper.py --lib fastapi      # Sync specific library
    python docs_scraper.py --list             # List configured libraries
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


# HTTP Status Codes
HTTP_OK = 200
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
CONFIG_FILE = SCRIPT_DIR / "libs_config.json"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "libs"
CACHE_FILE = OUTPUT_DIR / ".sync_cache.json"

# GitHub API
GITHUB_API = "https://api.github.com"


class TokenHolder:
    """Holds GitHub token to avoid global state."""

    token: str = ""


def load_config() -> dict[str, Any]:
    """Load library configuration."""
    if not CONFIG_FILE.exists():
        print(f"Config file not found: {CONFIG_FILE}")
        sys.exit(1)
    with CONFIG_FILE.open() as f:
        return json.load(f)


def load_cache() -> dict[str, Any]:
    """Load sync cache."""
    if CACHE_FILE.exists():
        with CACHE_FILE.open() as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    """Save sync cache."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w") as f:
        json.dump(cache, f, indent=2)


def github_request(endpoint: str) -> dict[str, Any] | list | None:
    """Make authenticated GitHub API request."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if TokenHolder.token:
        headers["Authorization"] = f"token {TokenHolder.token}"

    url = f"{GITHUB_API}{endpoint}"
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == HTTP_FORBIDDEN:
        print("Rate limited. Set GITHUB_TOKEN environment variable.")
        return None
    if response.status_code == HTTP_NOT_FOUND:
        print(f"Not found: {endpoint}")
        return None
    if response.status_code != HTTP_OK:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return response.json()


def get_repo_tree(owner: str, repo: str, branch: str = "main") -> list[dict] | None:
    """Get full repository tree."""
    endpoint = f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    result = github_request(endpoint)
    if result and "tree" in result:
        return result["tree"]
    return None


def get_file_content(owner: str, repo: str, path: str, branch: str = "main") -> str | None:
    """Get file content from GitHub."""
    endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    result = github_request(endpoint)
    if result and "content" in result:
        content = base64.b64decode(result["content"]).decode("utf-8")
        return content
    return None


def find_markdown_files(tree: list[dict], docs_path: str) -> list[str]:
    """Filter tree for markdown files in docs path."""
    md_files = []
    docs_path = docs_path.rstrip("/")
    is_root = docs_path == "."

    for item in tree:
        if item["type"] != "blob":
            continue
        path = item["path"]
        if not path.endswith((".md", ".mdx")):
            continue

        # Handle root-level docs (no subdirectory filtering)
        if is_root:
            # Only include root-level markdown files (no / in path)
            if "/" not in path:
                md_files.append(path)
        elif path.startswith(docs_path):
            md_files.append(path)

    return sorted(md_files)


def scrape_library(lib_name: str, lib_config: dict) -> bool:
    """Scrape documentation for a single library."""
    owner = lib_config["owner"]
    repo = lib_config["repo"]
    docs_path = lib_config.get("docs_path", "docs")
    branch = lib_config.get("branch", "main")

    print(f"\n{'=' * 50}")
    print(f"Syncing: {lib_name}")
    print(f"  Repo: {owner}/{repo}")
    print(f"  Docs: {docs_path}")
    print(f"  Branch: {branch}")
    print("=" * 50)

    # Get repo tree
    tree = get_repo_tree(owner, repo, branch)
    if not tree:
        print("  Failed to get repo tree")
        return False

    # Find markdown files
    md_files = find_markdown_files(tree, docs_path)
    if not md_files:
        print(f"  No markdown files found in {docs_path}/")
        return False

    print(f"  Found {len(md_files)} markdown files")

    # Fetch and combine content
    combined_content = []
    combined_content.append(f"# {lib_name} Documentation")
    combined_content.append(f"\nSource: https://github.com/{owner}/{repo}")
    combined_content.append(f"Branch: {branch}")
    combined_content.append(f"Synced: {datetime.now().isoformat()}")
    combined_content.append("\n" + "=" * 60 + "\n")

    for i, file_path in enumerate(md_files, 1):
        print(f"  [{i}/{len(md_files)}] {file_path}")
        content = get_file_content(owner, repo, file_path, branch)
        if content:
            # Add file header
            if docs_path == ".":
                relative_path = file_path
            else:
                relative_path = file_path[len(docs_path) :].lstrip("/")
            combined_content.append(f"\n## File: {relative_path}")
            combined_content.append(f"<!-- Source: {file_path} -->")
            combined_content.append("")
            combined_content.append(content)
            combined_content.append("\n" + "-" * 40 + "\n")

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{lib_name}.md"
    with output_file.open("w") as f:
        f.write("\n".join(combined_content))

    print(f"  Saved: {output_file}")
    return True


def sync_all(config: dict) -> None:
    """Sync all configured libraries."""
    libraries = config.get("libraries", {})
    cache = load_cache()

    success = 0
    failed = 0

    for lib_name, lib_config in libraries.items():
        if lib_config.get("enabled", True):
            if scrape_library(lib_name, lib_config):
                cache[lib_name] = {
                    "last_sync": datetime.now().isoformat(),
                    "status": "success",
                }
                success += 1
            else:
                cache[lib_name] = {
                    "last_sync": datetime.now().isoformat(),
                    "status": "failed",
                }
                failed += 1

    save_cache(cache)
    print("\n" + "=" * 50)
    print(f"Sync complete: {success} succeeded, {failed} failed")


def sync_library(lib_name: str, config: dict) -> None:
    """Sync a specific library."""
    libraries = config.get("libraries", {})
    if lib_name not in libraries:
        print(f"Library not found: {lib_name}")
        print(f"Available: {', '.join(libraries.keys())}")
        sys.exit(1)

    cache = load_cache()
    if scrape_library(lib_name, libraries[lib_name]):
        cache[lib_name] = {
            "last_sync": datetime.now().isoformat(),
            "status": "success",
        }
    else:
        cache[lib_name] = {
            "last_sync": datetime.now().isoformat(),
            "status": "failed",
        }
    save_cache(cache)


def list_libraries(config: dict) -> None:
    """List configured libraries."""
    libraries = config.get("libraries", {})
    cache = load_cache()

    print(f"\nConfigured Libraries ({len(libraries)}):")
    print("-" * 60)

    for lib_name, lib_config in sorted(libraries.items()):
        owner = lib_config["owner"]
        repo = lib_config["repo"]
        enabled = lib_config.get("enabled", True)
        status = "enabled" if enabled else "disabled"

        last_sync = cache.get(lib_name, {}).get("last_sync", "never")
        if last_sync != "never":
            last_sync = last_sync[:19].replace("T", " ")

        print(f"  {lib_name:<20} {owner}/{repo:<30} [{status}]")
        print(f"    Last sync: {last_sync}")


def main() -> None:
    """Entry point for the documentation scraper CLI."""
    parser = argparse.ArgumentParser(description="GitHub Documentation Scraper")
    parser.add_argument("--lib", "-l", help="Sync specific library")
    parser.add_argument("--list", action="store_true", help="List configured libraries")
    parser.add_argument("--token", "-t", help="GitHub token (or set GITHUB_TOKEN env)")

    args = parser.parse_args()

    # Set token from arg or environment
    TokenHolder.token = args.token or os.environ.get("GITHUB_TOKEN", "")

    if not TokenHolder.token:
        print("Warning: No GitHub token. Rate limits apply (60 req/hour).")
        print("Set GITHUB_TOKEN env var or use --token flag.\n")

    config = load_config()

    if args.list:
        list_libraries(config)
    elif args.lib:
        sync_library(args.lib, config)
    else:
        sync_all(config)


if __name__ == "__main__":
    main()
