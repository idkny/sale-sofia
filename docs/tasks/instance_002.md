---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-27
---

# Instance 2 Session

**You are Instance 2.** Work independently.

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

### 2025-12-27 (Session 31 - Phase 3 Change Detection + Phase 1 Finish)

| Task | Status |
|------|--------|
| Finish Crawler Validation Phase 1 | Complete |
| Create validation matrix | Complete |
| Run Phase 1 checklist | Complete |
| Create `scrape_history` table | Complete |
| Create `listing_changes` table | Complete |
| Add 7 CRUD functions | Complete |
| Add `detect_all_changes()` | Complete |
| Write 30 tests | Complete (100% pass) |
| Run Phase 3 checklist | Complete |

**Summary**: Finished Crawler Validation Phase 1 (validation matrix, checklist). Implemented Phase 3 Change Detection: added `scrape_history` and `listing_changes` tables, 7 CRUD functions, `detect_all_changes()` with SKIP_FIELDS, 30 tests.

**Files Modified**:
- `data/data_store_main.py` - added tables, init function, 7 CRUD functions
- `data/change_detector.py` - added SKIP_FIELDS, detect_all_changes()
- `docs/specs/106_CRAWLER_VALIDATION_PLAN.md` - updated Phase 1 + Phase 3 status
- `docs/specs/106A_CRAWLER_VALIDATION_MATRIX.md` - created validation matrix

**Files Created**:
- `tests/test_change_detection.py` - 30 tests for change detection

---

### 2025-12-27 (Session 30 - Crawler Validation Phase 1 Complete)

| Task | Status |
|------|--------|
| Create test harness (`tests/scrapers/`) | Complete |
| Fix floor extraction patterns (imot.bg + bazar.bg) | Complete |
| Fix price JS patterns (bazar.bg) | Complete |
| Fix sqm patterns (bazar.bg) | Complete |
| Fix test fixtures (bazar.bg) | Complete |
| Validate imot.bg scraper | Complete (23/23) |
| Validate bazar.bg scraper | Complete (23/23) |

**Summary**: Fixed all 13 failing scraper tests. All 46 tests now passing. Fixed floor extraction patterns to handle `Етаж: 3/6` and `Етаж 3` formats. Fixed bazar.bg price JS patterns (single/double quotes, decimals), sqm patterns (Площ + flexible spacing), and test fixtures (proper CSS classes).

**Files Modified**:
- `websites/imot_bg/selectors.py` - floor patterns for slash format and number-only
- `websites/bazar_bg/selectors.py` - floor patterns (Cyrillic Е), price JS, sqm patterns
- `websites/bazar_bg/bazar_scraper.py` - handle EUR text in price fallback
- `tests/scrapers/conftest.py` - fixed bazar_search_html fixture with proper CSS classes

---

### 2025-12-27 (Session 29 - Task Archiving)

| Task | Status |
|------|--------|
| Archive completed TASKS.md sections | Complete |
| Archive completed REFACTORING_TASKS.md sections | Complete |
| Create archive/tasks/ directory | Complete |
| Streamline active task files | Complete |

**Summary**: Archived completed task sections following ZohoCentral pattern. Created `archive/tasks/TASKS_COMPLETED_2025-12-27.md` (353 lines) and `archive/tasks/REFACTORING_TASKS_COMPLETED_2025-12-27.md` (406 lines). Reduced TASKS.md from 765 to 129 lines and REFACTORING_TASKS.md from 740 to 65 lines.

**Files Created**:
- `archive/tasks/TASKS_COMPLETED_2025-12-27.md` - archived Bugs, Solution F, Chunk Timing, Celery/Mubeng, Page Change Detection, Ollama, Historical Work
- `archive/tasks/REFACTORING_TASKS_COMPLETED_2025-12-27.md` - archived all 26 refactoring tasks (22 complete, 2 skipped, 2 superseded)

**Files Modified**:
- `docs/tasks/TASKS.md` - streamlined with summary table + pending tasks only
- `docs/tasks/REFACTORING_TASKS.md` - streamlined with summary + optional follow-up tests

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
