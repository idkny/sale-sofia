"""
Centralized settings for the scraper.

This module contains constants that are shared across multiple files.
"""

# =============================================================================
# PROXY SETTINGS
# =============================================================================

# Minimum proxies for scraping (triggers refresh if below this)
# Used in: main.py _ensure_min_proxies(), orchestrator.wait_for_proxies()
MIN_PROXIES_FOR_SCRAPING = 10

# Maximum retries per URL before giving up on that URL
MAX_URL_RETRIES = 3

# Proxy response timeout in seconds
# Used for: liveness checks, Fetcher requests, mubeng, quality checks
# Free proxies are slow - 45 seconds is the minimum acceptable response time
PROXY_TIMEOUT_SECONDS = 45

# Mubeng timeout as string (for CLI argument)
PROXY_TIMEOUT_MUBENG = f"{PROXY_TIMEOUT_SECONDS}s"

# Milliseconds version (for APIs that use ms like StealthyFetcher)
PROXY_TIMEOUT_MS = PROXY_TIMEOUT_SECONDS * 1000

# PSC (proxy-scraper-checker) timeout in seconds
# PSC scrapes 70+ sources and checks thousands of proxies - takes 20-40 minutes
PSC_TIMEOUT_SECONDS = 3000  # 50 minutes

# =============================================================================
# PROXY SCORING SETTINGS
# =============================================================================

# Thresholds for auto-removal
MAX_CONSECUTIVE_PROXY_FAILURES = 3   # Auto-remove after this many consecutive failures

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

# Redis-backed circuit breaker (for distributed Celery workers)
# When True: uses Redis for shared state across workers
# When False: uses in-memory circuit breaker (single-process only)
REDIS_CIRCUIT_BREAKER_ENABLED = False

# Redis-backed rate limiter (for distributed Celery workers)
# When True: uses Redis for shared rate limiting across workers
# When False: uses in-memory rate limiter (single-process only)
REDIS_RATE_LIMITER_ENABLED = False

# =============================================================================
# FLOWER SETTINGS (Celery monitoring UI)
# =============================================================================
# Run: celery -A celery_app flower --port=$FLOWER_PORT
# Or use: scripts/start_flower.sh

FLOWER_PORT = 5555
FLOWER_BROKER_API = "redis://localhost:6379/0"

# Rate limiting (requests per minute per domain)
# Computed from YAML configs: rate = 60 / delay_seconds
# imot.bg: 1.5s delay -> 40 req/min
# bazar.bg: 3.0s delay -> 20 req/min
from config.scraping_config import get_domain_rate_limits

DOMAIN_RATE_LIMITS = get_domain_rate_limits()

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
SQLITE_BUSY_RETRIES = 5       # Number of retry attempts on "database is locked"
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

# =============================================================================
# SCRAPER MONITORING SETTINGS
# =============================================================================
# Used in: scraping/metrics.py, scraping/session_report.py
# Spec: 114_SCRAPER_MONITORING.md

# Health status thresholds
SCRAPER_HEALTH_THRESHOLDS = {
    "success_rate": {
        "healthy": 90.0,      # >= 90% is healthy
        "degraded": 75.0,     # >= 75% is degraded, < 75% is critical
    },
    "error_rate": {
        "healthy": 5.0,       # <= 5% is healthy
        "degraded": 15.0,     # <= 15% is degraded, > 15% is critical
    },
    "block_rate": {
        "healthy": 2.0,       # <= 2% is healthy
        "degraded": 5.0,      # <= 5% is degraded, > 5% is critical
    },
    "avg_response_ms": {
        "healthy": 2000,      # <= 2s is healthy
        "degraded": 5000,     # <= 5s is degraded, > 5s is critical
    },
}

# Alert thresholds (for dashboard indicators)
SCRAPER_ALERT_THRESHOLDS = {
    "min_proxies": 10,              # Alert if proxy count drops below
    "max_consecutive_failures": 5,  # Alert after N consecutive failures
    "baseline_deviation": 20.0,     # Alert if >20% worse than 7-day baseline
}

# Report retention
SCRAPER_REPORTS_RETENTION_DAYS = 30
SCRAPER_REPORTS_DIR = "data/reports"

# =============================================================================
# CELERY SITE TASKS SETTINGS
# =============================================================================
# Used in: scraping/tasks.py, main.py
# Spec: 115_CELERY_SITE_TASKS.md

# Feature flag for parallel scraping via Celery
# When True: sites scraped in parallel via Celery workers
# When False: sequential scraping (current behavior)
PARALLEL_SCRAPING_ENABLED = False

# Number of URLs per worker task chunk
SCRAPING_CHUNK_SIZE = 25

# Celery task time limits (seconds)
SCRAPING_SOFT_TIME_LIMIT = 600   # 10 min - task receives SoftTimeLimitExceeded
SCRAPING_HARD_TIME_LIMIT = 720   # 12 min - task forcefully terminated
