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

## Phase 1: Foundation (P1 - Critical) - COMPLETE

- [x] **1.1** Create `resilience/` module structure
- [x] **1.2** Implement `resilience/exceptions.py`
- [x] **1.3** Implement `resilience/error_classifier.py`
- [x] **1.4** Implement `resilience/retry.py`
- [x] **1.5** Add resilience settings to `config/settings.py`
- [x] **1.6** Integrate retry decorator into `main.py`
- [x] **1.7** Write unit tests for Phase 1 (45 tests, 100% pass)
- [x] **1.8** Consistency check: Audit for hardcoded values
  - Fixed: `scrapling_base.py` timeouts → use PROXY_TIMEOUT_SECONDS/MS
  - Fixed: `proxy_validator.py` → use PROXY_VALIDATION_TIMEOUT
  - Added: `PROXY_VALIDATION_TIMEOUT = 10` to settings

---

## Phase 2: Domain Protection (P2)

- [ ] **2.0** CTO Review: Read architecture docs before implementation
  - Read: `docs/architecture/ARCHITECTURE.md`, `CONVENTIONS.md`, `DESIGN_PATTERNS.md`
  - Ensure agents follow: single responsibility, 30-line functions, proper naming
  - Pass relevant context to agents

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

- [ ] **2.6** Consistency check: Audit for hardcoded values
  - Check circuit breaker/rate limiter use settings from config/settings.py
  - No magic numbers for timeouts, thresholds, or limits

---

## Phase 3: Session Recovery (P2)

- [ ] **3.0** CTO Review: Read architecture docs before implementation
  - Read: `docs/architecture/ARCHITECTURE.md`, `CONVENTIONS.md`
  - Review checkpoint patterns in existing code
  - Pass relevant context to agents

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

- [ ] **3.5** Consistency check: Audit for hardcoded values
  - Check checkpoint uses CHECKPOINT_BATCH_SIZE, CHECKPOINT_DIR from settings
  - No hardcoded paths or batch sizes

---

## Phase 4: Detection (P3)

- [ ] **4.0** CTO Review: Read architecture docs before implementation
  - Read: `docs/architecture/ARCHITECTURE.md`, `CONVENTIONS.md`
  - Review response handling patterns in existing scrapers
  - Pass relevant context to agents

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

- [ ] **4.5** Consistency check: Audit for hardcoded values
  - Check response validator uses settings for thresholds (MIN_CONTENT_LENGTH, etc.)
  - No hardcoded detection patterns that should be configurable

---

## Verification

- [ ] **5.1** End-to-end live test
  - Run full scraping pipeline
  - Verify: backoff delays in logs, circuit breaker opens, checkpoint works
  - Test Ctrl+C → checkpoint saved → restart → resumes

---

## Summary

| Phase | Tasks | Priority | Status |
|-------|-------|----------|--------|
| Phase 1: Foundation | 8 | P1 (Critical) | COMPLETE |
| Phase 2: Domain Protection | 7 | P2 | Pending |
| Phase 3: Session Recovery | 6 | P2 | Pending |
| Phase 4: Detection | 6 | P3 | Pending |
| Verification | 1 | P1 | Pending |
| **Total** | **28** | |

**Note**: Each phase includes a consistency check task to audit for hardcoded values.

---

*Created: 2025-12-27*
