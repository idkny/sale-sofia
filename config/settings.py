"""
Centralized settings for the scraper.

This module contains constants that are shared across multiple files.
"""

# =============================================================================
# PROXY SETTINGS
# =============================================================================

# Mubeng proxy endpoint - ALWAYS use proxy for scraping
MUBENG_PROXY = "http://localhost:8089"

# Minimum proxies to START mubeng rotator (just need at least one working)
# Used in: proxies_main.py get_and_filter_proxies(), setup_mubeng_rotator()
MIN_PROXIES_TO_START = 1

# Minimum proxies for RELIABLE SCRAPING (triggers refresh if below this)
# Used in: main.py _ensure_min_proxies(), setup calls from main.py
MIN_PROXIES_FOR_SCRAPING = 10

# Maximum retries per URL when proxy fails
MAX_PROXY_RETRIES = 3

# Proxy response timeout in seconds
# Used for: preflight checks, Fetcher requests, StealthyFetcher, mubeng, quality checks
# Free proxies are slow - 45 seconds is the minimum acceptable response time
PROXY_TIMEOUT_SECONDS = 45

# Mubeng timeout as string (for CLI argument)
PROXY_TIMEOUT_MUBENG = f"{PROXY_TIMEOUT_SECONDS}s"

# Milliseconds version (for APIs that use ms like StealthyFetcher)
PROXY_TIMEOUT_MS = PROXY_TIMEOUT_SECONDS * 1000

# =============================================================================
# PROXY SCORING SETTINGS
# =============================================================================

# Score multipliers for success/failure
SCORE_SUCCESS_MULTIPLIER = 1.1  # +10% reward on success
SCORE_FAILURE_MULTIPLIER = 0.5  # -50% penalty on failure

# Thresholds for auto-removal
MAX_PROXY_FAILURES = 3   # Auto-remove after this many consecutive failures
MIN_PROXY_SCORE = 0.01   # Auto-remove if score drops below this
