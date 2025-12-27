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

### 2025-12-27 (Session 34 - Database Concurrency Analysis)

| Task | Status |
|------|--------|
| Review codebase for database concurrency issues | ✅ Complete |
| Read architecture docs (DESIGN_PATTERNS, CONVENTIONS) | ✅ Complete |
| Analyze `data_store_main.py` for SQLite limitations | ✅ Complete |
| Add Phase 4.0 Database Concurrency tasks to TASKS.md | ✅ Complete |

**Summary**: Research session - no code written. Identified critical database concurrency issue: SQLite in `data_store_main.py` has no WAL mode, no timeout, no retry on BUSY errors. When Phase 4 enables parallel Celery workers, `save_listing()` calls will collide causing "database is locked" errors and data loss. Added Phase 4.0 as BLOCKER before Phase 4.1.

**Files Modified**:
- `docs/tasks/TASKS.md` - Added Phase 4.0 Database Concurrency (6 tasks)

**Key Findings**:
- Current scraping is sequential (no issue today)
- Celery `worker_concurrency=8` means 8 parallel workers
- SQLite default timeout is 5 seconds (too short under contention)
- No WAL mode = single-writer lock
- Solution: WAL + timeout + retry decorator (following `resilience/retry.py` pattern)

---

### 2025-12-27 (Session 33 - Phase 4 Task Consolidation)

| Task | Status |
|------|--------|
| Analyze async/parallel patterns in codebase | ✅ Complete |
| Research Celery best practices (via agents) | ✅ Complete |
| Consolidate duplicate tasks in TASKS.md | ✅ Complete |
| Create Phase 4 sub-phases (4.1-4.4) | ✅ Complete |

**Summary**: Planning session - no code written. Analyzed current "fake async" pattern (async def with blocking time.sleep). Researched Celery best practices for web scraping. Consolidated "Build async orchestrator" + "Integrate with Celery" into unified Phase 4: Celery Site Orchestration with 4 sub-phases (22 total tasks). Defined 2-level config structure (general defaults + per-site overrides).

**Files Modified**:
- `docs/tasks/TASKS.md` - Consolidated Phase 4, added 22 detailed tasks in logical order

**Key Decisions**:
- Settings first (4.1), then async cleanup (4.2), then Celery tasks (4.3), then testing (4.4)
- Keep `config/settings.py` for infrastructure, add `config/scraping_*.yaml` for scraping behavior
- One Celery task per site with internal asyncio for concurrent URL fetching

---

### 2025-12-27 (Session 32 - Spec 112 Phase 4: Detection)

| Task | Status |
|------|--------|
| CTO Review: Read architecture docs | ✅ Complete |
| Implement resilience/response_validator.py | ✅ Complete |
| Add 429/Retry-After handling to retry.py | ✅ Complete |
| Integrate response validation into main.py | ✅ Complete |
| Write unit tests for Phase 4 | ✅ Complete |
| Run Phase Completion Checklist | ✅ Complete |

**Summary**: Implemented Spec 112 Phase 4 (Detection). Created response_validator.py for soft block detection (CAPTCHA, block messages, short content). Added Retry-After header handling to retry.py. Integrated soft block detection into main.py fetch functions. All 153 resilience tests passing (45 Phase 1 + 42 Phase 2 + 18 Phase 3 + 48 Phase 4).

**Files Created**:
- `resilience/response_validator.py` - detect_soft_block() with pre-compiled regex patterns
- `tests/test_resilience_phase4.py` (48 tests)

**Files Modified**:
- `resilience/retry.py` - Added Retry-After handling
- `resilience/error_classifier.py` - Enhanced custom exception recognition
- `resilience/__init__.py` - Exports detect_soft_block, CAPTCHA_PATTERNS, BLOCK_PATTERNS
- `main.py` - Soft block detection in _fetch_search_page and _fetch_listing_page
- `config/settings.py` - Added MIN_CONTENT_LENGTH
- `docs/architecture/DESIGN_PATTERNS.md` - Added pattern 15 (Response Validator)
- `docs/architecture/FILE_STRUCTURE.md` - Added response_validator.py
- `admin/config/project_structure_manifest.json` - Added response_validator.py
- `docs/tasks/112_RESILIENCE_IMPLEMENTATION.md` - Marked Phase 4 complete
- `docs/tasks/TASKS.md` - Marked Phase 4 complete

---

*(Sessions 31 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
