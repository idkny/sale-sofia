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

# Quick validation timeout (shorter than scraping for fast preflight checks)
PROXY_VALIDATION_TIMEOUT = 10  # seconds

# =============================================================================
# PROXY SCORING SETTINGS
# =============================================================================

# Score multipliers for success/failure
SCORE_SUCCESS_MULTIPLIER = 1.1  # +10% reward on success
SCORE_FAILURE_MULTIPLIER = 0.5  # -50% penalty on failure

# Thresholds for auto-removal
MAX_PROXY_FAILURES = 3   # Auto-remove after this many consecutive failures
MIN_PROXY_SCORE = 0.01   # Auto-remove if score drops below this

# =============================================================================
# RESILIENCE SETTINGS
# =============================================================================

# Retry settings
RETRY_MAX_ATTEMPTS = 5
RETRY_BASE_DELAY = 2.0       # seconds
RETRY_MAX_DELAY = 60.0       # seconds cap
RETRY_JITTER_FACTOR = 0.5    # 50% random jitter

# Circuit breaker settings
CIRCUIT_BREAKER_FAIL_MAX = 5
CIRCUIT_BREAKER_RESET_TIMEOUT = 60  # seconds
CIRCUIT_BREAKER_HALF_OPEN_CALLS = 2
CIRCUIT_BREAKER_ENABLED = True

# Rate limiting (requests per minute per domain)
DOMAIN_RATE_LIMITS = {
    "imot.bg": 10,
    "bazar.bg": 10,
    "default": 10,
}

# Checkpoint settings
CHECKPOINT_BATCH_SIZE = 10  # Save every N URLs
CHECKPOINT_DIR = "data/checkpoints"
