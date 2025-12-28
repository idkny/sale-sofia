---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-28
---

# Instance 2 Session

**You are Instance 2.** Work independently.

---

## IMMEDIATE NEXT SESSION TASK

**Phase 4.3 COMPLETE** - Spec 115 archived.

Continue with **Phase 4.4: Integration Testing** (real Celery workers):
- [ ] 4.4.1 Test parallel scraping with 2+ sites
- [ ] 4.4.2 Test site-specific config overrides
- [ ] 4.4.3 Test crash recovery with checkpoints
- [ ] 4.4.4 Test circuit breaker + Celery interaction
- [ ] 4.4.5 Run Phase Completion Checklist

**Note**: 781 tests passing. Code is source of truth.

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
2. Claim task with `[Instance 2]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 2] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 2] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 2] Implement proxy rotation
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
3. **Claim in TASKS.md** - Add `[Instance 2]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_001.md** - Other instance file is off-limits

---

## Session History

### 2025-12-28 (Session 44 - Phase 4.3.3 + 4.3.4 COMPLETE)

| Task | Status |
|------|--------|
| 4.3.3.3 Update celery_app.py | Complete |
| 4.3.4.1 Add orchestrator methods | Complete |
| 4.3.4.2 Update main.py PARALLEL_SCRAPING | Complete |
| 4.3.4.4 Integration tests | Complete |
| 4.3.4.5 Phase Completion Checklist | Complete |

**Summary**: Completed remaining Phase 4.3.3 (celery_app registration) and all Phase 4.3.4 Integration tasks. Added 3 orchestrator methods, PARALLEL_SCRAPING mode to main.py, 12 integration tests. Fixed hardcoded values in scraping/tasks.py to use settings. Archived spec 115. 781 tests passing.

**Files Created**:
- `tests/test_scraping_integration.py` - 12 integration tests

**Files Modified**:
- `celery_app.py` - Added `scraping.tasks` to include list
- `orchestrator.py` - Added 3 scraping orchestration methods
- `main.py` - Added PARALLEL_SCRAPING mode with `_wait_for_parallel_scraping()`
- `scraping/tasks.py` - Fixed hardcoded values to use settings

---

### 2025-12-28 (Session 43 - Phase 4.3.2 Redis Rate Limiter COMPLETE)

| Task | Status |
|------|--------|
| 4.3.2.1 Create redis_rate_limiter.py | Complete |
| 4.3.2.2 Add REDIS_RATE_LIMITER_ENABLED flag | Complete |
| 4.3.2.3 Update factory function | Complete |
| 4.3.2.4 Write unit tests | Complete |

**Summary**: Completed Phase 4.3.2: Created `resilience/redis_rate_limiter.py` with Lua script for atomic token acquisition. Added feature flag, updated factory function. 29 new tests, 675 total passing.

---

### 2025-12-28 (Session 42 - Phase 4.3.1 Redis Circuit Breaker COMPLETE)

| Task | Status |
|------|--------|
| 4.3.1.1-4.3.1.4 Redis Circuit Breaker | Complete |

**Summary**: Fixed pytest path issue, completed Phase 4.3.1. 35 new tests, 646 total passing.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
