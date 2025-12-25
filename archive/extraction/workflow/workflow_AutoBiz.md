---
id: 20251201_workflow_autobiz
type: extraction
subject: workflow
source_repo: Auto-Biz
description: "CLI orchestration, argparse patterns, command handlers from Auto-Biz"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [workflow, cli, argparse, orchestration, auto-biz]
---

# SUBJECT: workflow/

**Source Repository**: Auto-Biz (https://github.com/idkny/Auto-Biz)
**Extracted From**: `main.py` (469 lines)

---

## 1. EXTRACTED CODE

### 1.1 CLI Structure with argparse

```python
"""Main command-line interface for the Auto-Biz Scraper."""

import argparse
import asyncio
import subprocess
from pathlib import Path
from typing import Any, Optional, Union

from dotenv import load_dotenv
from loguru import logger

import requests
from browsers.browsers_main import create_instance
from paths import LOGS_DIR
from proxies.proxies_main import (
    check_proxies,
    get_live_free_proxies,
    get_paid_proxy,
    scrape_proxies,
    setup_mubeng_rotator,
    stop_mubeng_rotator,
)
from search_engine import search_engines
from utils.log_config import setup_logging

MUBENG_EXECUTABLE_PATH = "mubeng"
parser: argparse.ArgumentParser


def main() -> None:
    """Run the Auto-Biz Scraper CLI."""
    load_dotenv()
    setup_logging(LOGS_DIR)

    global parser
    parser = argparse.ArgumentParser(description="Auto-Biz Scraper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Search Command ---
    search_parser = subparsers.add_parser("search", help="Search engine operations")
    search_parser.set_defaults(func=handle_search_command)
    search_parser.add_argument("--all", action="store_true", help="Search all available engines")
    search_parser.add_argument("--ddg", action="store_true", help="Search DuckDuckGo only")
    search_parser.add_argument("--serp", action="store_true", help="Search SerpAPI only")

    # --- Proxy Command ---
    proxy_parser = subparsers.add_parser("proxy", help="Proxy management")
    proxy_parser.set_defaults(func=handle_proxy_command)
    proxy_subparsers = proxy_parser.add_subparsers(dest="proxy_command_action", required=True)
    proxy_subparsers.add_parser("refresh", help="Scrape a new list of potential proxies.")
    proxy_subparsers.add_parser("check", help="Check the scraped proxies for liveness and quality.")
    serve_parser = proxy_subparsers.add_parser("serve", help="Start Mubeng proxy server with live proxies.")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port for the proxy server.")
    serve_parser.add_argument("--protocols", nargs="+", help="Filter by proxy protocol(s).")
    serve_parser.add_argument("--anonymity", nargs="+", help="Filter by anonymity level(s).")
    serve_parser.add_argument("--countries", nargs="+", help="Filter by country code(s).")

    # --- URL Command ---
    url_parser = subparsers.add_parser("url", help="URL management")
    url_parser.set_defaults(func=handle_url_command)
    url_subparsers = url_parser.add_subparsers(dest="url_command_action", required=True)
    add_url_parser = url_subparsers.add_parser("add", help="Add URLs to the database.")
    add_url_parser.add_argument("--url", help="A single URL to add.")
    add_url_parser.add_argument("--file", help="A file containing a list of URLs to add.")

    # --- Common Browser Arguments ---
    def add_common_browser_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("browser", choices=["chromium", "firefox", "webkit"])
        subparser.add_argument("--gui", action="store_true")
        subparser.add_argument("--proxy-type", choices=["free", "paid", "none"], default="none")
        subparser.add_argument("--filters", nargs="*")
        subparser.add_argument("--session-type", choices=["sticky", "random"], default="sticky")

    # --- Launch Command ---
    launch_parser = subparsers.add_parser("launch", help="Launch browser and navigate.")
    launch_parser.set_defaults(func=handle_launch_command)
    launch_parser.add_argument("url", help="URL to navigate to.")
    add_common_browser_args(launch_parser)

    # --- Validate Command ---
    validate_parser = subparsers.add_parser("validate", help="Run fingerprint validation.")
    validate_parser.set_defaults(func=handle_validate_command)
    add_common_browser_args(validate_parser)

    # --- Parse and Execute ---
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
```

### 1.2 Command Handler Pattern

```python
def handle_search_command(args: argparse.Namespace) -> None:
    """Handle the 'search' command."""
    if args.all:
        search_engines.search_all()
    elif args.ddg:
        search_engines.search_ddg()
    elif args.serp:
        search_engines.search_serp()
    else:
        # Print subparser help
        for sp_action in parser._subparsers._actions:
            if isinstance(sp_action, argparse._SubParsersAction):
                for choice, subparser in sp_action.choices.items():
                    if choice == "search":
                        subparser.print_help()
                        return


def handle_proxy_command(args: argparse.Namespace) -> None:
    """Handle the 'proxy' command."""
    if args.proxy_command_action == "refresh":
        logger.info("Manual proxy refresh triggered via CLI.")
        try:
            message = scrape_proxies()
            print(message)
        except Exception as e:
            logger.error(f"Error during proxy refresh: {e}", exc_info=True)
            print(f"[ERROR] Proxy refresh failed: {e}")
    elif args.proxy_command_action == "check":
        logger.info("Manual proxy check triggered via CLI.")
        try:
            message = check_proxies()
            print(message)
        except Exception as e:
            logger.error(f"Error during proxy check: {e}", exc_info=True)
            print(f"[ERROR] Proxy check failed: {e}")
    elif args.proxy_command_action == "serve":
        serve_proxies(args)
```

### 1.3 Async Browser Launch with Cleanup

```python
def handle_launch_command(args: argparse.Namespace) -> None:
    """Handle the 'launch' command."""
    asyncio.run(launch_browser_with_proxy(args))


async def launch_browser_with_proxy(args: argparse.Namespace) -> None:
    """Launch a browser with specified proxy and filters."""
    mubeng_process = None
    temp_file = None
    browser_handle = None

    try:
        proxy_config, mubeng_process, temp_file = await _setup_proxy_for_launch(args)
        browser_type = f"{args.browser}gui" if args.gui else args.browser

        if not proxy_config and args.proxy_type != "none":
            print(f"[ERROR] {args.proxy_type.capitalize()} proxy setup failed.")
            return

        browser_handle, content = await _launch_and_get_content(
            browser_type=browser_type,
            proxy_for_playwright=proxy_config,
            url=args.url,
            ignore_https_errors=True if proxy_config else False,
        )
        print("[CONTENT_START]")
        print(content)
        print("[CONTENT_END]")

        if args.gui:
            await asyncio.sleep(5)

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    finally:
        print("[INFO] Cleaning up resources...")
        if browser_handle:
            await browser_handle.close()
        if mubeng_process:
            stop_mubeng_rotator(mubeng_process, temp_file)
```

### 1.4 Proxy Liveness Check Pattern

```python
def _check_proxy_liveness(proxy_url: str) -> bool:
    """Performs a quick liveness check on a single proxy URL."""
    try:
        response = requests.get(
            "https://api.ipify.org?format=json",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        logger.debug(f"Pre-flight liveness check failed for proxy: {proxy_url}")
        return False


def _get_validated_free_proxy(filter_dict: dict, google_passed: Optional[bool]) -> Optional[str]:
    """Gets pre-vetted proxies and returns first one passing liveness check."""
    proxy_urls = get_live_free_proxies(
        protocols=filter_dict.get("protocol"),
        anonymity_levels=filter_dict.get("anonymity"),
        country_codes=filter_dict.get("country"),
        google_passed=google_passed,
    )
    if not proxy_urls:
        return None

    for proxy_url in proxy_urls:
        if _check_proxy_liveness(proxy_url):
            return proxy_url
    return None
```

---

## 2. CONCLUSIONS

### What is Good / Usable

1. **CLI Structure**: Clean argparse with subparsers, `set_defaults(func=...)` pattern
2. **Reusable Arguments**: `add_common_browser_args()` helper
3. **Async Integration**: Proper `asyncio.run()` bridge
4. **Resource Cleanup**: try/finally pattern
5. **Liveness Check**: Pre-flight validation before using proxies

### What is Outdated

1. **Global parser**: Using global variable for parser (minor)
2. **Hardcoded messages**: Print statements mixed with logger

### What Must Be Rewritten

1. **Filter parsing**: While-loop parsing is fragile
2. **Error handling**: Inconsistent patterns

### How it Fits into AutoBiz

- **DIRECT PORT**: CLI structure, command handler pattern
- **ADAPT**: Filter parsing should be more robust
- **KEEP**: Async browser launch pattern with cleanup

### Conflicts or Duplicates with Previous Repos

| Pattern | Auto-Biz | Others | Best |
|---------|----------|--------|------|
| CLI | Full argparse | None | **Auto-Biz** |
| Subparsers | Yes | No | **Auto-Biz** |
| Async bridge | Yes | No | **Auto-Biz** |

### Best Version Recommendation

**Auto-Biz is BEST for CLI orchestration** - most comprehensive, production-tested
