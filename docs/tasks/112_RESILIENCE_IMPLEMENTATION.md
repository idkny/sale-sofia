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

## Mandatory Phase Tasks

### Opening Task (BEFORE implementation)

**CTO Review** - Read ALL architecture docs before delegating to agents:
- `docs/architecture/ARCHITECTURE.md` - Project structure overview
- `docs/architecture/CONVENTIONS.md` - Coding standards
- `docs/architecture/DESIGN_PATTERNS.md` - Patterns used in project
- `docs/architecture/FILE_STRUCTURE.md` - Where files go
- `docs/architecture/DATA_FLOW.md` - How data moves
- `docs/architecture/ADDING_COMPONENTS.md` - How to add new components
- `config/settings.py` - Centralized settings pattern

**Pass to agents**: Single responsibility, 30-line functions, proper naming, import from config.settings, reference prior phase code for consistency.

### Closing Tasks (BEFORE marking done)

1. **Consistency Check** - Audit for hardcoded values
   - All timeouts, thresholds, limits must be in `config/settings.py`
   - All files must import from settings (with fallback defaults)
   - No magic numbers in code

2. **Integration Validation** - Check harmony with project
   - Verify task is up-to-date with latest project features (LLM, resilience, scrapling, etc.)
   - Check if this phase duplicates or conflicts with other modules
   - Ensure new code integrates properly with existing tools
   - Update related tasks in TASKS.md if needed

---

## Phase 1: Foundation (P1 - Critical) - COMPLETE

- [x] **1.0** CTO Review: Read architecture docs before implementation
  - Read: ALL files in `docs/architecture/` + `config/settings.py`
  - Pass to agents: Project conventions, patterns, file structure

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

- [x] **1.9** Integration validation: Check harmony with project
  - Verified retry decorator integrates with existing main.py flow
  - No conflicts with proxy scoring or scrapling modules
  - Updated architecture docs

---

## Phase 2: Domain Protection (P2) - COMPLETE

- [x] **2.0** CTO Review: Read architecture docs before implementation
  - Read: ALL files in `docs/architecture/` + `config/settings.py`
  - Pass to agents: Single responsibility, 30-line functions, proper naming, import from config.settings
  - Reference: Phase 1 code as example for consistency

- [x] **2.1** Implement `resilience/circuit_breaker.py`
  - Spec: [2.1 Circuit Breaker](../specs/112_SCRAPER_RESILIENCE.md#21-circuit-breaker)
  - AutoBiz: `core/_domain_circuit_breaker.py` (full port)
  - Classes: CircuitState, DomainCircuitStatus, DomainCircuitBreaker
  - CRITICAL: Keep fail-open design

- [x] **2.2** Implement `resilience/rate_limiter.py`
  - Spec: [2.2 Rate Limiter](../specs/112_SCRAPER_RESILIENCE.md#22-rate-limiter)
  - AutoBiz: `tools/scraping/_rate_limiter.py` (adapt)
  - Class: DomainRateLimiter (token bucket)

- [x] **2.3** Integrate circuit breaker into `main.py`
  - Check before request, record success/failure after
  - Extract domain from URL for tracking

- [x] **2.4** Integrate rate limiter into `main.py`
  - Added rate limiter.acquire() before each request
  - Kept existing time.sleep(delay) for additional politeness

- [x] **2.5** Write unit tests for Phase 2
  - Location: `tests/test_resilience_phase2.py`
  - 42 tests covering: state transitions, fail-open, token bucket, thread safety

- [x] **2.6** Consistency check: Settings imported from config/settings.py
  - Circuit breaker uses CIRCUIT_BREAKER_* settings
  - Rate limiter uses DOMAIN_RATE_LIMITS setting
  - Fixed: error_classifier.py ERROR_RECOVERY_MAP → uses ERROR_RETRY_* settings
  - Fixed: exceptions.py retry_after → uses RATE_LIMIT_DEFAULT_RETRY_AFTER
  - Fixed: main.py preflight → uses PREFLIGHT_* and PROXY_WAIT_TIMEOUT settings
  - Fixed: main.py delay → uses DEFAULT_SCRAPE_DELAY setting
  - Added 12 new settings to config/settings.py for consistency

- [x] **2.7** Integration validation: Check harmony with project
  - Rate limiter now used by Crawler Validation Phase 4 (updated TASKS.md)
  - Circuit breaker integrates with existing proxy scoring system
  - Updated DESIGN_PATTERNS.md with patterns 12-13
  - Updated FILE_STRUCTURE.md with new files
  - No conflicts with LLM extraction or other modules

---

## Phase 3: Session Recovery (P2) - COMPLETE

- [x] **3.0** CTO Review: Read architecture docs before implementation
  - Read: ALL files in `docs/architecture/` + `config/settings.py`
  - Review: `resilience/__init__.py` for export patterns
  - Pass to agents: Single responsibility, 30-line functions, proper naming, import from config.settings
  - Reference: Phase 1-2 code as examples for consistency

- [x] **3.1** Implement `resilience/checkpoint.py`
  - Spec: [3.1 Checkpoint Manager](../specs/112_SCRAPER_RESILIENCE.md#31-checkpoint-manager)
  - Class: CheckpointManager with save(), load(), clear()
  - Features: JSON format, batched saves (every CHECKPOINT_BATCH_SIZE URLs)

- [x] **3.2** Add checkpoint to `main.py` flow
  - Spec: [3.2 Graceful Shutdown](../specs/112_SCRAPER_RESILIENCE.md#32-graceful-shutdown)
  - Load checkpoint on startup, save after each URL, clear on success
  - Per-site checkpoints with date-based naming

- [x] **3.3** Add SIGTERM/SIGINT handlers to `main.py`
  - Spec: [3.2 Graceful Shutdown](../specs/112_SCRAPER_RESILIENCE.md#32-graceful-shutdown)
  - Force save checkpoint on signal, then exit
  - Global state for signal handler access

- [x] **3.4** Write unit tests for Phase 3
  - Location: `tests/test_resilience_phase3.py`
  - 18 tests covering: save/load, batched saves, clear, edge cases

- [x] **3.5** Consistency check: Audit for hardcoded values
  - checkpoint.py uses CHECKPOINT_BATCH_SIZE, CHECKPOINT_DIR from settings
  - No hardcoded paths or batch sizes
  - Settings already existed in config/settings.py

- [x] **3.6** Integration validation: Check harmony with project
  - Checkpoint uses separate data/checkpoints/ directory (no conflicts)
  - Celery tasks have own state management (no integration needed)
  - Signal handlers work with orchestrator exit flow
  - Updated: FILE_STRUCTURE.md, DESIGN_PATTERNS.md, manifest.json

---

## Phase 4: Detection (P3)

- [ ] **4.0** CTO Review: Read architecture docs before implementation
  - Read: ALL files in `docs/architecture/` + `config/settings.py`
  - Review: `resilience/__init__.py` for export patterns
  - Pass to agents: Single responsibility, 30-line functions, proper naming, import from config.settings
  - Reference: Phase 1-2-3 code as examples for consistency

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
  - Add any new settings to config/settings.py

- [ ] **4.6** Integration validation: Check harmony with project
  - Verify soft block detection integrates with circuit breaker
  - Check if LLM extraction needs soft block awareness
  - Ensure 429/Retry-After handling works with rate limiter
  - Update related tasks in TASKS.md if detection enables new features

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
| Phase 1: Foundation | 10 | P1 (Critical) | COMPLETE |
| Phase 2: Domain Protection | 8 | P2 | COMPLETE |
| Phase 3: Session Recovery | 7 | P2 | COMPLETE |
| Phase 4: Detection | 7 | P3 | Pending |
| Verification | 1 | P1 | Pending |
| **Total** | **33** | |

**Note**: Each phase includes THREE mandatory tasks:
1. **CTO Review** (opening) - Read ALL `docs/architecture/` files before delegating
2. **Consistency check** (closing) - Audit for hardcoded values, add to config/settings.py
3. **Integration validation** (closing) - Check harmony with other project features

---

*Created: 2025-12-27*
