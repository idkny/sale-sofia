"""
Centralized settings for the scraper.

This module contains constants that are shared across multiple files.
"""

# Proxy response timeout in seconds
# Used for: preflight checks, Fetcher requests, StealthyFetcher, mubeng, quality checks
# Free proxies are slow - 45 seconds is the minimum acceptable response time
PROXY_TIMEOUT_SECONDS = 45

# Mubeng timeout as string (for CLI argument)
PROXY_TIMEOUT_MUBENG = f"{PROXY_TIMEOUT_SECONDS}s"

# Milliseconds version (for APIs that use ms like StealthyFetcher)
PROXY_TIMEOUT_MS = PROXY_TIMEOUT_SECONDS * 1000
