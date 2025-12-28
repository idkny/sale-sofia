# Instance 3 Session

**You are Instance 3.** Work independently.

---

## Workflow: Research → Specs → Code

**Single source of truth at each stage:**

```
docs/research/  →  docs/specs/  →  TASKS.md  →  code
(discovery)        (blueprint)     (tracking)    (truth)
      ↓                 ↓                           ↓
archive/research/  archive/specs/          (code supersedes)
```

**Rules:**
1. Research done → create spec + task → archive research
2. Spec done → implement code → archive spec
3. Code is source of truth (specs become historical)
4. New features = new specs (don't update archived)

---

## How to Work

1. Read [TASKS.md](TASKS.md) coordination table
2. Claim task with `[Instance 3]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 3] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 3] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 3] Implement proxy rotation
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# After complete (spec archived, link removed)
- [x] Implement proxy rotation
```

---

## CRITICAL RULES

1. **NEVER WRITE "NEXT STEPS" IN THIS FILE**
2. **TASKS.md IS THE SINGLE SOURCE OF TRUTH FOR TASKS**
3. **THIS FILE IS FOR SESSION HISTORY ONLY**
4. **KEEP ONLY LAST 3 SESSIONS**
5. **CODE IS SOURCE OF TRUTH, NOT SPECS**

---

## Instance Rules

1. **One task at a time** - Finish before claiming another
2. **Check coordination table FIRST** - Re-read TASKS.md before claiming
3. **Claim in TASKS.md** - Add `[Instance 3]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_001.md or instance_002.md** - Other instance files are off-limits

---

## Session History

### 2025-12-28 (Session 8 - Phase 4.4 Integration Testing)

| Task | Status |
|------|--------|
| 4.3.4.3 Add new settings to config/settings.py | ✅ Complete |
| 4.4.1 Test parallel scraping with 2+ sites | ✅ Complete |
| 4.4.4 Test circuit breaker + Celery interaction | ✅ Complete |
| Remove alerting task from Phase 5 | ✅ Complete |

**Summary**: Completed Phase 4.4 Integration Testing tasks. Added Celery site task settings (PARALLEL_SCRAPING_ENABLED, SCRAPING_CHUNK_SIZE, time limits). Created 39 new integration tests (15 parallel scraping + 24 circuit breaker). Removed email/Slack alerting from Phase 5 per user request. Phase 4.4 now complete with 81 tests total.

**Files Created**:
- `tests/test_parallel_scraping_integration.py` - 15 tests for concurrent execution, rate limiting, progress tracking
- `tests/test_circuit_breaker_celery_integration.py` - 24 tests for circuit breaker + Celery interaction

**Files Modified**:
- `config/settings.py` - Added PARALLEL_SCRAPING_ENABLED, SCRAPING_CHUNK_SIZE, SCRAPING_SOFT/HARD_TIME_LIMIT
- `docs/specs/106_CRAWLER_VALIDATION_PLAN.md` - Removed alerting references

**Test Count**: 870 tests total

---

### 2025-12-28 (Session 7 - Spec 114 Implementation Complete)

| Task | Status |
|------|--------|
| 3.1 Create Scraper Health dashboard (basic layout) | ✅ Complete |
| 3.2 Add trend charts (success rate over time) | ✅ Complete |
| 3.3 Add health indicators and run history table | ✅ Complete |
| 4.1 Integration test: full scrape with metrics | ✅ Complete |
| 4.2 Dashboard test: verify report loading | ✅ Complete |
| Archive Spec 114 | ✅ Complete |

**Summary**: Completed Spec 114 Phases 3-4 (Dashboard + Testing). Created Scraper Health dashboard page with health metric cards, trend charts, domain health table, and run history table. Added 47 new tests (23 integration + 24 dashboard). Spec 114 fully implemented and archived.

**Files Created**:
- `app/pages/5_Scraper_Health.py` - Scraper health dashboard
- `tests/test_scraper_monitoring_integration.py` - 23 integration tests
- `tests/test_scraper_health_dashboard.py` - 24 dashboard logic tests

**Files Archived**:
- `docs/specs/114_SCRAPER_MONITORING.md` → `archive/specs/114_SCRAPER_MONITORING.md`

---

### 2025-12-27 (Session 6 - Spec 114: Scraper Monitoring)

| Task | Status |
|------|--------|
| Research codebase monitoring gaps | ✅ Complete |
| Research industry best practices | ✅ Complete |
| Read architecture documentation | ✅ Complete |
| Create Spec 114: Scraper Monitoring | ✅ Complete |
| Add task to TASKS.md | ✅ Complete |

**Summary**: Created comprehensive Spec 114 for Scraper Monitoring & Observability. Launched 3 parallel research agents to analyze: (1) existing monitoring in codebase, (2) architecture docs, (3) industry best practices. Designed 4-phase implementation with 12 tasks. Spec ready for implementation.

**Files Created**:
- `docs/specs/114_SCRAPER_MONITORING.md` - Full spec with MetricsCollector, SessionReportGenerator, and dashboard design

**Key Findings**:
- Good foundation exists: Loguru logging, error classification, retry, circuit breaker, rate limiter
- Missing: Metrics persistence, session reports, health dashboard, trend analysis
- Industry standard: Track success rate >90%, error rate <5%, block rate <2%

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Instance 1 (don't edit)
- [instance_002.md](instance_002.md) - Instance 2 (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
