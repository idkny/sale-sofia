# Instance 1 Session

**You are Instance 1.** Work independently.

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
2. Claim task with `[Instance 1]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 1] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 1] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 1] Implement proxy rotation
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
3. **Claim in TASKS.md** - Add `[Instance 1]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_002.md** - Other instance file is off-limits

---

## Session History

### 2025-12-28 (Session 41 - Scraper Monitoring Phase 2 Integration)

| Task | Status |
|------|--------|
| 1.4 Verify scraper monitoring tests | ✅ Complete |
| 2.1 Add `get_all_states()` to circuit_breaker.py | ✅ Complete |
| 2.2 Add `get_stats()` to proxy_scorer.py | ✅ Complete |
| 2.3 Integrate MetricsCollector into main.py | ✅ Complete |

**Summary**: Completed Scraper Monitoring Phase 1 (verified 48 tests) and Phase 2 (Integration). Added `get_all_states()` to circuit breaker, updated `get_stats()` in proxy scorer to match spec format, and integrated MetricsCollector into main.py scraping flow with request/response tracking and session report generation.

**Files Modified**:
- `resilience/circuit_breaker.py` - Added `get_all_states()` method
- `proxies/proxy_scorer.py` - Updated `get_stats()` to return spec-compliant format
- `main.py` - Integrated MetricsCollector with record_request/record_response calls
- `tests/test_proxy_scorer.py` - Updated test for new get_stats format

**Test Results**: 675 passed, 8 skipped

---

### 2025-12-28 (Session 40 - Scraper Monitoring Phase 1)

| Task | Status |
|------|--------|
| 1.1 Create `scraping/metrics.py` with MetricsCollector | ✅ Complete |
| 1.2 Create `scraping/session_report.py` with SessionReportGenerator | ✅ Complete |
| 1.3 Add health thresholds to `config/settings.py` | ✅ Complete |
| 1.4 Write unit tests for metrics and reports | ✅ Complete |

**Summary**: Implemented Scraper Monitoring Phase 1 (Core Metrics). Created MetricsCollector class for tracking request/response metrics, SessionReportGenerator for persisting JSON reports, and added health thresholds to settings.

**Files Created**:
- `scraping/metrics.py` - MetricsCollector, RequestStatus enum, RunMetrics dataclass
- `scraping/session_report.py` - SessionReportGenerator, SessionReport dataclass
- `tests/test_scraper_monitoring.py` - 48 unit tests

---

### 2025-12-28 (Session 39 - Pre-Production Hardening Implementation)

| Task | Status |
|------|--------|
| Phase 1: Add field allowlist to update_listing_evaluation() | ✅ Complete |
| Phase 2: Deploy impact analysis agents (6 items) | ✅ Complete |
| Phase 3: Implement confirmed-safe changes | ✅ Complete |
| Archive completed tasks to TASKS_COMPLETED | ✅ Complete |

**Summary**: Implemented Pre-Production Hardening. Phase 1: Added ALLOWED_UPDATE_FIELDS (37 fields) for SQL injection prevention. Phase 2: Deployed 2 agents - analyzed 6 recommendations, cancelled 3 (keep duplicates separate), implemented 3. Phase 3: Consolidated extract_domain() to resilience/, removed update_listing_features(), documented agency_store.py in FILE_STRUCTURE.md.

**Files Modified**:
- `data/data_store_main.py` - Added field allowlist, removed update_listing_features()
- `resilience/circuit_breaker.py` - Added extract_domain() function
- `main.py` - Import extract_domain from resilience
- `scraping/async_fetcher.py` - Import extract_domain from resilience
- `docs/architecture/FILE_STRUCTURE.md` - Documented agency_store.py purpose
- `docs/tasks/TASKS.md` - Archived Pre-Production Hardening section
- `archive/tasks/TASKS_COMPLETED_2025-12-27.md` - Added completed tasks

**Test Results**: 563 passed, 8 skipped

---

*(Sessions 38 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
