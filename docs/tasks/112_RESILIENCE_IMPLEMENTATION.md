# Spec 112: Implementation Tasks

**Spec**: [112_SCRAPER_RESILIENCE.md](../specs/112_SCRAPER_RESILIENCE.md)
**Research**: [SCRAPER_RESILIENCE_RESEARCH.md](../research/SCRAPER_RESILIENCE_RESEARCH.md)
**Status**: Ready for Implementation

---

## AutoBiz Reference Files

| Sale-Sofia Target | AutoBiz Source | Lines |
|-------------------|----------------|-------|
| `error_classifier.py` | `core/_scraper_errors.py` | 34-394 |
| `circuit_breaker.py` | `core/_domain_circuit_breaker.py` | Full |
| `rate_limiter.py` | `tools/scraping/_rate_limiter.py` | Full |

**AutoBiz Path**: `/home/wow/Documents/ZohoCentral/autobiz/`

---

## Phase 1: Foundation (P1 - Critical)

- [ ] **1.1** Create `resilience/` module structure
  - Spec: [Architecture section](../specs/112_SCRAPER_RESILIENCE.md#architecture)
  - Create: `resilience/__init__.py`, `exceptions.py`, `error_classifier.py`, `retry.py`

- [ ] **1.2** Implement `resilience/exceptions.py`
  - Spec: [1.1 Exception Hierarchy](../specs/112_SCRAPER_RESILIENCE.md#11-exception-hierarchy)
  - Classes: ScraperException, NetworkException, RateLimitException, BlockedException, ParseException, ProxyException

- [ ] **1.3** Implement `resilience/error_classifier.py`
  - Spec: [1.2 Error Classifier](../specs/112_SCRAPER_RESILIENCE.md#12-error-classifier)
  - AutoBiz: `core/_scraper_errors.py:34-129` (ErrorType, RecoveryAction, ERROR_RECOVERY_MAP)
  - Functions: classify_error(), get_recovery_info()

- [ ] **1.4** Implement `resilience/retry.py`
  - Spec: [1.3 Retry Decorator](../specs/112_SCRAPER_RESILIENCE.md#13-retry-decorator-with-backoff)
  - Functions: _calculate_delay(), retry_with_backoff(), retry_with_backoff_async()
  - Features: exponential backoff, jitter, skip non-retryable errors

- [ ] **1.5** Add resilience settings to `config/settings.py`
  - Spec: [Config Additions](../specs/112_SCRAPER_RESILIENCE.md#config-additions-configsettingspy)
  - Settings: RETRY_*, CIRCUIT_BREAKER_*, DOMAIN_RATE_LIMITS, CHECKPOINT_*

- [ ] **1.6** Integrate retry decorator into `main.py`
  - Spec: [1.4 Integration](../specs/112_SCRAPER_RESILIENCE.md#14-integration-with-mainpy)
  - Replace: lines 117-150 (`_collect_listing_urls` retry loop)
  - Replace: lines 210-269 (`_scrape_listings` retry loop)

- [ ] **1.7** Write unit tests for Phase 1
  - Location: `tests/test_resilience_phase1.py`
  - Cover: retry decorator, error classifier, backoff calculation

---

## Phase 2: Domain Protection (P2)

- [ ] **2.1** Implement `resilience/circuit_breaker.py`
  - Spec: [2.1 Circuit Breaker](../specs/112_SCRAPER_RESILIENCE.md#21-circuit-breaker)
  - AutoBiz: `core/_domain_circuit_breaker.py` (full port)
  - Classes: CircuitState, DomainCircuitStatus, DomainCircuitBreaker
  - CRITICAL: Keep fail-open design

- [ ] **2.2** Implement `resilience/rate_limiter.py`
  - Spec: [2.2 Rate Limiter](../specs/112_SCRAPER_RESILIENCE.md#22-rate-limiter)
  - AutoBiz: `tools/scraping/_rate_limiter.py` (adapt)
  - Class: DomainRateLimiter (token bucket)

- [ ] **2.3** Integrate circuit breaker into `main.py`
  - Check before request, record success/failure after
  - Extract domain from URL for tracking

- [ ] **2.4** Integrate rate limiter into `main.py`
  - Replace `time.sleep(delay)` at lines 184, 276
  - Use: `limiter.acquire(domain)` before each request

- [ ] **2.5** Write unit tests for Phase 2
  - Location: `tests/test_resilience_phase2.py`
  - Cover: state transitions, fail-open, token bucket

---

## Phase 3: Session Recovery (P2)

- [ ] **3.1** Implement `resilience/checkpoint.py`
  - Spec: [3.1 Checkpoint Manager](../specs/112_SCRAPER_RESILIENCE.md#31-checkpoint-manager)
  - Class: CheckpointManager with save(), load(), clear()
  - Features: JSON format, batched saves

- [ ] **3.2** Add checkpoint to `main.py` flow
  - Spec: [3.2 Graceful Shutdown](../specs/112_SCRAPER_RESILIENCE.md#32-graceful-shutdown)
  - Load checkpoint on startup, save after each URL, clear on success

- [ ] **3.3** Add SIGTERM/SIGINT handlers to `main.py`
  - Spec: [3.2 Graceful Shutdown](../specs/112_SCRAPER_RESILIENCE.md#32-graceful-shutdown)
  - Force save checkpoint on signal, then exit

- [ ] **3.4** Write unit tests for Phase 3
  - Location: `tests/test_resilience_phase3.py`
  - Cover: save/load, batched saves, clear

---

## Phase 4: Detection (P3)

- [ ] **4.1** Implement `resilience/response_validator.py`
  - Spec: [4.1 Soft Block Detector](../specs/112_SCRAPER_RESILIENCE.md#41-soft-block-detector)
  - Patterns: CAPTCHA, block messages, short content
  - Function: detect_soft_block(html) -> (is_blocked, reason)

- [ ] **4.2** Add 429/Retry-After header handling to `retry.py`
  - Parse Retry-After header, override calculated delay

- [ ] **4.3** Integrate response validation into `main.py`
  - Check for soft blocks before extraction, notify circuit breaker

- [ ] **4.4** Write unit tests for Phase 4
  - Location: `tests/test_resilience_phase4.py`
  - Cover: pattern detection, Retry-After parsing

---

## Verification

- [ ] **5.1** End-to-end live test
  - Run full scraping pipeline
  - Verify: backoff delays in logs, circuit breaker opens, checkpoint works
  - Test Ctrl+C → checkpoint saved → restart → resumes

---

## Summary

| Phase | Tasks | Priority |
|-------|-------|----------|
| Phase 1: Foundation | 7 | P1 (Critical) |
| Phase 2: Domain Protection | 5 | P2 |
| Phase 3: Session Recovery | 4 | P2 |
| Phase 4: Detection | 4 | P3 |
| Verification | 1 | P1 |
| **Total** | **21** | |

---

*Created: 2025-12-27*
