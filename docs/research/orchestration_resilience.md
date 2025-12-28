# Orchestration Research: Resilience Module

## Executive Summary

The resilience module (`resilience/`) contains 7 components for fault tolerance. **Critical finding**: All state is in-memory (single-process). For multi-worker Celery, circuit breaker and rate limiter need Redis backing.

---

## 1. Resilience Components

| Component | File | Purpose |
|-----------|------|---------|
| Circuit Breaker | `circuit_breaker.py` | Domain-level protection |
| Rate Limiter | `rate_limiter.py` | Token bucket per domain |
| Checkpoint Manager | `checkpoint.py` | Session recovery |
| Error Classifier | `error_classifier.py` | Error type detection |
| Exceptions | `exceptions.py` | Custom exception hierarchy |
| Response Validator | `response_validator.py` | Soft block detection |
| Retry Decorators | `retry.py` | Exponential backoff |

---

## 2. Circuit Breaker Mechanics

### State Machine
```
CLOSED (normal) → OPEN (blocked) → HALF_OPEN (testing) → CLOSED
```

### Trip Conditions
- Opens after 5 consecutive failures (`CIRCUIT_BREAKER_FAIL_MAX`)
- Tracks `last_block_type` (cloudflare, captcha, rate_limit)
- Records `failure_count`, `success_count`, `opened_at`

### Reset Mechanism
- OPEN → HALF_OPEN after 60s timeout
- Allows 2 test requests in HALF_OPEN
- Success → closes circuit, resets counters
- Failure → re-opens circuit

### Implementation
- Thread-safe with `threading.Lock()`
- Singleton pattern via `get_circuit_breaker()`
- Fail-open design: defaults to allowing requests on errors
- Tracks metrics: blocked requests, allowed requests

---

## 3. Rate Limiter Design

### Algorithm
Token bucket with per-domain tracking:
```python
tokens_to_add = elapsed_seconds * (rate_per_minute / 60)
```

### Configuration
```python
DOMAIN_RATE_LIMITS = {
    "imot.bg": 10,      # 10 requests/minute
    "bazar.bg": 10,
    "default": 10,
}
```

### Async Support
- **Full async support** via `acquire_async()` using `asyncio.sleep()`
- Sync version blocks with `time.sleep()`
- Both use internal lock for thread safety

### Behavior
- `acquire(blocking=True)`: Waits if no token available
- `acquire(blocking=False)`: Returns False immediately
- Waits outside lock for parallel domain access

---

## 4. Checkpoint System

### Purpose
Resume scraping after crash without re-scraping completed URLs.

### Usage Pattern
```python
checkpoint = CheckpointManager("imot_bg_2025-01-15")
state = checkpoint.load()  # Recover from crash
if state:
    scraped_urls = set(state["scraped"])
    pending_urls = list(state["pending"])

for url in urls:
    scrape(url)
    scraped_urls.add(url)
    checkpoint.save(scraped_urls, pending_urls)  # Batched

checkpoint.clear()  # Remove on completion
```

### Batching
- Saves every N URLs (`CHECKPOINT_BATCH_SIZE = 10`)
- Force immediate write with `force=True`

### Storage
- JSON files in `data/checkpoints/`
- Filename: `{name}_checkpoint.json`
- Contents: scraped list, pending list, timestamp, name

---

## 5. State Sharing Mechanism

### In-Memory State (Current)
- Circuit breaker: `_circuits: dict[str, DomainCircuitStatus]`
- Rate limiter: `_tokens`, `_last_refill` dicts
- Both protected by threading locks

### No Redis Integration
- Current implementation is single-process only
- Data stored in Python process memory
- **Critical for orchestration**: Won't work for multi-worker Celery!

### Checkpoint Persistence
- JSON files on disk (survives crash/restart)
- No Redis dependency

---

## 6. Integration with Current Code

### Used in `scraping/async_fetcher.py`
```python
# Circuit breaker check
if not circuit_breaker.can_request(domain):
    raise CircuitOpenException(...)

# Rate limiting (async)
await rate_limiter.acquire_async(domain)

# Soft block detection
is_blocked, reason = detect_soft_block(html)
if is_blocked:
    circuit_breaker.record_failure(domain, block_type=reason)
    raise BlockedException(...)

# Success recording
circuit_breaker.record_success(domain)
```

### Error Classifier
- 10 error types: NETWORK_TIMEOUT, HTTP_RATE_LIMIT, HTTP_BLOCKED, etc.
- Maps to actions: RETRY_IMMEDIATE, RETRY_WITH_BACKOFF, SKIP, CIRCUIT_BREAK

### Retry Decorator
- Available: `@retry_with_backoff()`, `@retry_with_backoff_async()`
- Currently unused in production (decorators commented out)

---

## 7. Impact on Parallel Scraping

### Current Limitations

| Issue | Impact | Solution |
|-------|--------|----------|
| In-memory state | Each worker has own circuit breaker | Redis-backed state |
| Rate limiter per-process | 10 workers × 10 req/min = 100 req/min | Global Redis limiter |
| Checkpoint batching | Counter not thread-safe across processes | Coordinate writes |
| Soft block detection | Stateless (OK) | No change needed |

### With 10 Celery Workers
- Worker A might retry domain while Worker B has it blocked
- Rate limit is 10× intended (each worker has own limit)
- Inconsistent circuit breaker states

---

## 8. What an Orchestrator Needs

### Must Implement

1. **Redis-Backed Circuit Breaker** (for multi-worker)
   - Store state in Redis instead of process memory
   - Workers read from Redis before making request
   - Workers update Redis on success/failure

2. **Redis-Backed Rate Limiter** (for multi-worker)
   - Global token bucket in Redis per domain
   - All workers acquire from same bucket
   - Redis atomic operations for safety

3. **Checkpoint Coordination**
   - Single worker writes checkpoints (avoid races)
   - Or: Write to temp file, rename atomically
   - Track batching counter in Redis

4. **Initialization**
   - Start all resilience components before first request
   - Clear old checkpoints on session start
   - Initialize circuit breakers for all domains

5. **Monitoring** (for dashboard)
   - Get metrics: open circuits, half-open count, blocked requests
   - Track rate limiter state per domain
   - Report last block type per domain

6. **Graceful Shutdown**
   - Clear checkpoints on successful completion
   - Preserve checkpoints on error for recovery

---

## Key Findings Summary

| Component | Status | For Orchestration |
|-----------|--------|-------------------|
| Circuit Breaker | Thread-safe | Needs Redis backing |
| Rate Limiter | Async-ready | Needs Redis backing |
| Checkpoint | Batched | Needs coordination |
| Error Classifier | Stateless | Ready as-is |
| Response Validator | Stateless | Ready as-is |
| Retry Decorators | Unused | Consider enabling |

---

## Critical Gap for Phase 4.3

**The resilience module is built for single-process scraping.**

For parallel Celery workers, we must:
1. Migrate circuit breaker to Redis
2. Migrate rate limiter to Redis
3. Add monitoring/metrics collection
4. Coordinate checkpoint writes

This should be a design priority before implementing Phase 4.3 task distribution.
