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

# =============================================================================
# ERROR-SPECIFIC RETRY LIMITS
# =============================================================================
# Used in: resilience/error_classifier.py ERROR_RECOVERY_MAP
# These override RETRY_MAX_ATTEMPTS for specific error types

ERROR_RETRY_NETWORK = 3       # Network timeout/connection errors
ERROR_RETRY_RATE_LIMIT = 5    # HTTP 429 rate limit errors
ERROR_RETRY_BLOCKED = 2       # HTTP 403 blocked errors (less retries - likely permanent)
ERROR_RETRY_SERVER = 3        # HTTP 5xx server errors
ERROR_RETRY_PROXY = 5         # Proxy-related errors

# Default retry-after for rate limit exceptions (seconds)
RATE_LIMIT_DEFAULT_RETRY_AFTER = 60

# =============================================================================
# PREFLIGHT CHECK SETTINGS
# =============================================================================
# Used in: main.py preflight check functions

PREFLIGHT_MAX_ATTEMPTS_L1 = 6   # Level 1: Auto-rotation attempts
PREFLIGHT_MAX_ATTEMPTS_L2 = 3   # Level 2: Soft restart attempts
PREFLIGHT_MAX_ATTEMPTS_L3 = 3   # Level 3: Full refresh attempts
PREFLIGHT_RETRY_DELAY = 1       # Seconds between preflight retries

# Timeout waiting for proxies to be available (seconds)
PROXY_WAIT_TIMEOUT = 600

# =============================================================================
# SOFT BLOCK DETECTION SETTINGS
# =============================================================================
# Used in: resilience/response_validator.py

# Minimum content length - pages shorter than this are suspicious
MIN_CONTENT_LENGTH = 1000

# =============================================================================
# CROSS-SITE DEDUPLICATION SETTINGS
# =============================================================================
# Used in: data/property_fingerprinter.py, data/property_merger.py
# Spec: 106B_CROSS_SITE_DEDUPLICATION.md

# Fields used to generate property fingerprint
FINGERPRINT_FIELDS = ["neighborhood", "sqm_total", "rooms_count", "floor_number", "building_type"]

# Price discrepancy threshold (highlight if above this percentage)
PRICE_DISCREPANCY_THRESHOLD_PCT = 5.0

# High discrepancy threshold (red highlight in dashboard)
PRICE_DISCREPANCY_HIGH_PCT = 10.0

# =============================================================================
# DATABASE CONCURRENCY SETTINGS
# =============================================================================
# Used in: data/data_store_main.py, data/db_retry.py
# Prevents "database is locked" errors under parallel Celery worker load

# SQLite connection timeout (seconds to wait for lock)
SQLITE_TIMEOUT = 30.0

# Retry settings for database write operations
SQLITE_BUSY_RETRIES = 3       # Number of retry attempts on "database is locked"
SQLITE_BUSY_DELAY = 0.5       # Base delay between retries (seconds)
SQLITE_BUSY_MAX_DELAY = 5.0   # Maximum delay cap (seconds)

# Enable Write-Ahead Logging for better concurrent access
SQLITE_WAL_MODE = True

# =============================================================================
# ASYNC FETCHER SETTINGS
# =============================================================================
# Used in: scraping/async_fetcher.py

# Maximum concurrent requests when fetching multiple URLs
ASYNC_FETCHER_MAX_CONCURRENT = 5

# =============================================================================
# SCRAPING DEFAULTS
# =============================================================================
# Scraping behavior settings moved to:
# - config/scraping_defaults.yaml (global defaults)
# - config/sites/<site>.yaml (per-site overrides)
# Use load_scraping_config() from config.scraping_config
