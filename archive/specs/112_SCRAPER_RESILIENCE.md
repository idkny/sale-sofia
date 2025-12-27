# Spec 112: Scraper Resilience & Error Handling

**Status**: Draft
**Research**: [SCRAPER_RESILIENCE_RESEARCH.md](../research/SCRAPER_RESILIENCE_RESEARCH.md)
**Priority**: P1

---

## Overview

Implement production-grade error handling and resilience for the web scraper. Currently, the scraper has basic retry logic but lacks exponential backoff, circuit breakers, and crash recovery.

---

## Goals

1. **Never crash** - Handle all errors gracefully
2. **Smart retries** - Exponential backoff with jitter, not blind retries
3. **Respect rate limits** - Don't hammer sites that block us
4. **Recover from crashes** - Resume from checkpoint after power/internet failure
5. **Classify errors** - Handle different error types appropriately

---

## Non-Goals

- Proxy acquisition (covered by existing proxy system)
- Anti-bot evasion (covered by Camoufox/stealth)
- CAPTCHA solving (out of scope)

---

## Architecture

### New Module: `resilience/`

```
resilience/
├── __init__.py
├── retry.py              # Retry decorators (sync + async)
├── circuit_breaker.py    # Domain circuit breaker
├── rate_limiter.py       # Token bucket rate limiter
├── cooldown.py           # Cooldown manager
├── exceptions.py         # Exception hierarchy
├── error_classifier.py   # Error categorization
├── checkpoint.py         # Session recovery
└── response_validator.py # Soft block detection
```

### Config Additions (`config/settings.py`)

```python
# Retry settings
RETRY_MAX_ATTEMPTS = 5
RETRY_BASE_DELAY = 2.0       # seconds
RETRY_MAX_DELAY = 60.0       # seconds cap
RETRY_JITTER_FACTOR = 0.5    # 50% random jitter

# Circuit breaker settings
CIRCUIT_BREAKER_FAIL_MAX = 5
CIRCUIT_BREAKER_RESET_TIMEOUT = 60  # seconds

# Rate limiting (requests per minute per domain)
DOMAIN_RATE_LIMITS = {
    "imot.bg": 10,
    "bazar.bg": 10,
    "default": 10,
}

# Checkpoint settings
CHECKPOINT_BATCH_SIZE = 10  # Save every N URLs
CHECKPOINT_DIR = "data/checkpoints"
```

---

## Phase 1: Foundation (P1 - Critical)

### 1.1 Exception Hierarchy

**File**: `resilience/exceptions.py`

```python
class ScraperException(Exception):
    """Base exception for all scraper errors."""
    pass

class NetworkException(ScraperException):
    """Network-level errors (connection, timeout)."""
    pass

class RateLimitException(ScraperException):
    """Rate limit exceeded (429)."""
    retry_after: int = 60

class BlockedException(ScraperException):
    """Blocked by website (403)."""
    pass

class ParseException(ScraperException):
    """HTML parsing failed."""
    pass

class ProxyException(ScraperException):
    """Proxy-related error."""
    pass
```

### 1.2 Error Classifier

**File**: `resilience/error_classifier.py`

```python
from enum import Enum
from requests.exceptions import *
from httpx import HTTPStatusError

class ErrorType(Enum):
    NETWORK = "network"       # Retry with backoff
    RATE_LIMIT = "rate_limit" # Respect Retry-After
    BLOCKED = "blocked"       # Circuit breaker
    NOT_FOUND = "not_found"   # Skip permanently
    SERVER = "server"         # Retry with backoff
    PARSE = "parse"           # Log, skip
    PROXY = "proxy"           # Rotate proxy
    UNKNOWN = "unknown"       # Log, retry once

def classify_error(exception: Exception, response=None) -> ErrorType:
    """Classify an exception into an ErrorType."""

    # HTTP status-based classification
    if response is not None:
        if response.status_code == 403:
            return ErrorType.BLOCKED
        if response.status_code == 404:
            return ErrorType.NOT_FOUND
        if response.status_code == 429:
            return ErrorType.RATE_LIMIT
        if 500 <= response.status_code < 600:
            return ErrorType.SERVER

    # Exception-based classification
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return ErrorType.NETWORK
    if isinstance(exception, SSLError):
        return ErrorType.PROXY
    if isinstance(exception, (AttributeError, ValueError)):
        return ErrorType.PARSE

    return ErrorType.UNKNOWN
```

### 1.3 Retry Decorator with Backoff

**File**: `resilience/retry.py`

```python
import asyncio
import functools
import random
import time
from typing import Tuple, Type
from loguru import logger
from config.settings import (
    RETRY_MAX_ATTEMPTS,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    RETRY_JITTER_FACTOR,
)
from .error_classifier import classify_error, ErrorType

def _calculate_delay(attempt: int, base: float, max_delay: float, jitter: float) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = base * (2 ** attempt)
    delay = min(delay, max_delay)
    jitter_amount = delay * jitter * random.random()
    return delay + jitter_amount

def retry_with_backoff(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    jitter_factor: float = RETRY_JITTER_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: callable = None,
):
    """
    Sync retry decorator with exponential backoff and jitter.

    Usage:
        @retry_with_backoff(max_attempts=5)
        def fetch_page(url):
            return requests.get(url)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_type = classify_error(e)

                    # Don't retry certain error types
                    if error_type in (ErrorType.NOT_FOUND, ErrorType.PARSE):
                        raise

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(attempt, base_delay, max_delay, jitter_factor)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: "
                            f"{e}. Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator

# Async version
def retry_with_backoff_async(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    jitter_factor: float = RETRY_JITTER_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: callable = None,
):
    """Async version of retry_with_backoff."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_type = classify_error(e)

                    if error_type in (ErrorType.NOT_FOUND, ErrorType.PARSE):
                        raise

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(attempt, base_delay, max_delay, jitter_factor)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: "
                            f"{e}. Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator
```

### 1.4 Integration with main.py

Replace simple retry loops with decorated functions.

**Before** (`main.py:119-149`):
```python
for attempt in range(MAX_PROXY_RETRIES):
    try:
        response = Fetcher.get(...)
        break
    except Exception as e:
        logger.warning(f"Attempt {attempt + 1} failed")
```

**After**:
```python
from resilience.retry import retry_with_backoff

@retry_with_backoff(max_attempts=5)
def fetch_search_page(url, proxy, headers):
    response = Fetcher.get(url, proxy=proxy, headers=headers)
    return response
```

---

## Phase 2: Domain Protection (P2)

### 2.1 Circuit Breaker

**File**: `resilience/circuit_breaker.py`

```python
import time
from enum import Enum
from threading import Lock
from loguru import logger
from config.settings import CIRCUIT_BREAKER_FAIL_MAX, CIRCUIT_BREAKER_RESET_TIMEOUT

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing

class DomainCircuitBreaker:
    """
    Circuit breaker per domain.

    Usage:
        breaker = DomainCircuitBreaker()

        if breaker.is_open("imot.bg"):
            raise CircuitOpenException("imot.bg is temporarily blocked")

        try:
            result = fetch_page(url)
            breaker.record_success("imot.bg")
        except Exception as e:
            breaker.record_failure("imot.bg")
    """

    def __init__(
        self,
        fail_max: int = CIRCUIT_BREAKER_FAIL_MAX,
        reset_timeout: int = CIRCUIT_BREAKER_RESET_TIMEOUT,
    ):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._states: dict[str, CircuitState] = {}
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}
        self._lock = Lock()

    def is_open(self, domain: str) -> bool:
        """Check if circuit is open for domain."""
        with self._lock:
            state = self._states.get(domain, CircuitState.CLOSED)

            if state == CircuitState.OPEN:
                # Check if reset timeout passed
                if time.time() - self._opened_at.get(domain, 0) > self.reset_timeout:
                    self._states[domain] = CircuitState.HALF_OPEN
                    logger.info(f"Circuit for {domain} entering half-open state")
                    return False
                return True

            return False

    def record_success(self, domain: str):
        """Record successful request."""
        with self._lock:
            self._failures[domain] = 0
            if self._states.get(domain) == CircuitState.HALF_OPEN:
                self._states[domain] = CircuitState.CLOSED
                logger.info(f"Circuit for {domain} closed (recovered)")

    def record_failure(self, domain: str):
        """Record failed request."""
        with self._lock:
            self._failures[domain] = self._failures.get(domain, 0) + 1

            if self._failures[domain] >= self.fail_max:
                self._states[domain] = CircuitState.OPEN
                self._opened_at[domain] = time.time()
                logger.warning(
                    f"Circuit for {domain} OPENED after {self.fail_max} failures. "
                    f"Will retry in {self.reset_timeout}s"
                )

# Singleton instance
_circuit_breaker = None

def get_circuit_breaker() -> DomainCircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = DomainCircuitBreaker()
    return _circuit_breaker
```

### 2.2 Rate Limiter

**File**: `resilience/rate_limiter.py`

```python
import time
from threading import Lock
from loguru import logger
from config.settings import DOMAIN_RATE_LIMITS

class DomainRateLimiter:
    """
    Token bucket rate limiter per domain.

    Usage:
        limiter = DomainRateLimiter()

        limiter.acquire("imot.bg")  # Blocks if rate exceeded
        result = fetch_page(url)
    """

    def __init__(self, rate_limits: dict = None):
        self.rate_limits = rate_limits or DOMAIN_RATE_LIMITS
        self._tokens: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}
        self._lock = Lock()

    def _get_rate(self, domain: str) -> int:
        """Get requests per minute for domain."""
        return self.rate_limits.get(domain, self.rate_limits.get("default", 10))

    def acquire(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain.

        Args:
            domain: Target domain
            blocking: If True, wait until token available

        Returns:
            True if token acquired, False if not (only when blocking=False)
        """
        with self._lock:
            now = time.time()
            rate = self._get_rate(domain)

            # Initialize if first request
            if domain not in self._tokens:
                self._tokens[domain] = rate
                self._last_refill[domain] = now

            # Refill tokens based on time passed
            elapsed = now - self._last_refill[domain]
            refill = elapsed * (rate / 60)  # tokens per second
            self._tokens[domain] = min(rate, self._tokens[domain] + refill)
            self._last_refill[domain] = now

            # Check if token available
            if self._tokens[domain] >= 1:
                self._tokens[domain] -= 1
                return True

            if not blocking:
                return False

        # Blocking: wait for token
        wait_time = 60 / rate  # Time for one token to refill
        logger.debug(f"Rate limit for {domain}, waiting {wait_time:.2f}s")
        time.sleep(wait_time)
        return self.acquire(domain, blocking=True)

# Singleton
_rate_limiter = None

def get_rate_limiter() -> DomainRateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = DomainRateLimiter()
    return _rate_limiter
```

---

## Phase 3: Session Recovery (P2)

### 3.1 Checkpoint Manager

**File**: `resilience/checkpoint.py`

```python
import json
import time
from pathlib import Path
from typing import Optional, Set
from loguru import logger
from config.settings import CHECKPOINT_BATCH_SIZE

class CheckpointManager:
    """
    Save and restore scraping progress.

    Usage:
        checkpoint = CheckpointManager("imot_bg")

        # Check for existing checkpoint
        state = checkpoint.load()
        if state:
            scraped_urls = set(state["scraped"])
            pending_urls = list(state["pending"])

        # Save progress periodically
        for url in urls:
            scrape(url)
            scraped_urls.add(url)
            checkpoint.save(scraped_urls, pending_urls)

        # Clear when done
        checkpoint.clear()
    """

    def __init__(self, name: str, checkpoint_dir: Path = None):
        self.name = name
        self.dir = checkpoint_dir or Path("data/checkpoints")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / f"{name}_checkpoint.json"
        self._counter = 0
        self.batch_size = CHECKPOINT_BATCH_SIZE

    def save(self, scraped: Set[str], pending: list[str], force: bool = False):
        """Save checkpoint (batched unless force=True)."""
        self._counter += 1

        if not force and self._counter % self.batch_size != 0:
            return

        try:
            data = {
                "scraped": list(scraped),
                "pending": pending,
                "timestamp": time.time(),
                "name": self.name,
            }
            with open(self.file, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Checkpoint saved: {len(scraped)} scraped, {len(pending)} pending")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def load(self) -> Optional[dict]:
        """Load existing checkpoint if any."""
        if not self.file.exists():
            return None

        try:
            with open(self.file) as f:
                data = json.load(f)
            logger.info(
                f"Loaded checkpoint: {len(data.get('scraped', []))} scraped, "
                f"{len(data.get('pending', []))} pending"
            )
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    def clear(self):
        """Remove checkpoint file (call when scraping complete)."""
        if self.file.exists():
            self.file.unlink()
            logger.info(f"Checkpoint cleared: {self.name}")
```

### 3.2 Graceful Shutdown

**File**: Add to `main.py`

```python
import signal
from resilience.checkpoint import CheckpointManager

# Global state for signal handler
_checkpoint_manager: Optional[CheckpointManager] = None
_scraped_urls: Set[str] = set()
_pending_urls: list[str] = []

def _signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    logger.warning(f"Received signal {signum}, saving checkpoint...")
    if _checkpoint_manager:
        _checkpoint_manager.save(_scraped_urls, _pending_urls, force=True)
    logger.info("Checkpoint saved, exiting...")
    sys.exit(0)

def setup_signal_handlers():
    """Set up graceful shutdown handlers."""
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
```

---

## Phase 4: Detection (P3)

### 4.1 Soft Block Detector

**File**: `resilience/response_validator.py`

```python
import re
from loguru import logger

# Patterns that indicate soft blocks
CAPTCHA_PATTERNS = [
    r"captcha",
    r"recaptcha",
    r"hcaptcha",
    r"challenge-platform",
    r"verify.*human",
    r"security.*check",
]

BLOCK_PATTERNS = [
    r"access.*denied",
    r"blocked",
    r"rate.*limit",
    r"too.*many.*requests",
    r"please.*try.*again.*later",
]

MIN_CONTENT_LENGTH = 1000  # Suspiciously short pages

def detect_soft_block(html: str) -> tuple[bool, str]:
    """
    Detect if page content indicates a soft block.

    Returns:
        (is_blocked, reason)
    """
    html_lower = html.lower()

    # Check for CAPTCHA
    for pattern in CAPTCHA_PATTERNS:
        if re.search(pattern, html_lower):
            return True, f"CAPTCHA detected: {pattern}"

    # Check for block messages
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, html_lower):
            return True, f"Block message: {pattern}"

    # Check for suspiciously short content
    if len(html) < MIN_CONTENT_LENGTH:
        return True, f"Content too short: {len(html)} bytes"

    return False, ""
```

---

## Testing

### Unit Tests

Create `tests/test_resilience.py`:

1. Test retry decorator with exponential backoff
2. Test circuit breaker state transitions
3. Test rate limiter token bucket
4. Test checkpoint save/load
5. Test error classifier

### Integration Tests

1. Test retry with real HTTP errors (mock server)
2. Test circuit breaker with consecutive failures
3. Test checkpoint recovery after simulated crash

---

## Tasks (for TASKS.md)

### Phase 1: Foundation
- [ ] Create `resilience/` module structure
- [ ] Implement `resilience/exceptions.py`
- [ ] Implement `resilience/error_classifier.py`
- [ ] Implement `resilience/retry.py` (sync + async)
- [ ] Add resilience settings to `config/settings.py`
- [ ] Integrate retry into `main.py`
- [ ] Write unit tests for Phase 1

### Phase 2: Domain Protection
- [ ] Implement `resilience/circuit_breaker.py`
- [ ] Implement `resilience/rate_limiter.py`
- [ ] Integrate circuit breaker into scraper
- [ ] Integrate rate limiter into scraper
- [ ] Write unit tests for Phase 2

### Phase 3: Session Recovery
- [ ] Implement `resilience/checkpoint.py`
- [ ] Add checkpoint save/restore to main.py
- [ ] Add SIGTERM/SIGINT handlers
- [ ] Write unit tests for Phase 3

### Phase 4: Detection
- [ ] Implement `resilience/response_validator.py`
- [ ] Add 429/Retry-After header handling
- [ ] Write unit tests for Phase 4

---

## Dependencies

- `tenacity` (optional - alternative to custom retry)
- `pybreaker` (optional - alternative to custom circuit breaker)

Or use custom implementations (no new dependencies).

---

## Success Criteria

1. Scraper handles all error types gracefully (no crashes)
2. Blocked domains trigger circuit breaker (60s cooldown)
3. Rate limits respected (429 → backoff with Retry-After)
4. Crash recovery works (resume from checkpoint)
5. All unit tests pass

---

*Spec Version: 1.0*
*Created: 2025-12-27*
