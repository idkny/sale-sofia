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

### 2025-12-28 (Session 38 - Pre-Production Audit)

| Task | Status |
|------|--------|
| Research LLM coding mistakes | ✅ Complete |
| Deploy 6 audit agents (security, duplicates, errors, dead code, config, tests) | ✅ Complete |
| Compile initial audit report | ✅ Complete |
| Run 4 impact analysis agents on recommendations | ✅ Complete |
| Revise recommendations based on impact analysis | ✅ Complete |
| Add Pre-Production Hardening tasks to TASKS.md | ✅ Complete |

**Summary**: Comprehensive pre-production audit. Deployed 10 agents total. Found 4 potential issues, but impact analysis revealed 3 should NOT be changed (fail-fast is correct, timeout is dead code, ports already type-safe). Only 1 safe change: add field allowlist to `update_listing_evaluation()`. Added Pre-Production Hardening section to TASKS.md with phased approach.

**Files Created**:
- `docs/research/llm_coding_mistakes.md` - LLM mistake patterns reference
- `docs/research/pre_production_audit_2025-12-28.md` - Focused audit report with 1 action item
- `tests/debug/audit_dead_code.py` - Dead code analysis script

**Files Modified**:
- `docs/tasks/TASKS.md` - Added Pre-Production Hardening (P0) section with 3 phases

**Key Findings**:
- DB error handling: "Fail fast at import" is CORRECT design - cancelled
- PROXY_WAIT_TIMEOUT: Parameter is dead code (never forwarded) - cancelled
- Port validation: All ports already typed integers - deferred
- Field allowlist: Safe to proceed - 1 action item remaining

---

### 2025-12-27 (Session 35 - Phase 4.0 Database Concurrency)

| Task | Status |
|------|--------|
| 4.0.1 Add database settings to config/settings.py | ✅ Complete |
| 4.0.2 Update get_db_connection() for WAL + timeout | ✅ Complete |
| 4.0.3 Create data/db_retry.py with retry decorator | ✅ Complete |
| 4.0.4 Apply @retry_on_busy to 7 write functions | ✅ Complete |
| 4.0.5 Write concurrent write tests (17 tests) | ✅ Complete |
| 4.0.6 Run Phase Completion Checklist | ✅ Complete |

**Summary**: Implemented Phase 4.0 Database Concurrency. Created `db_retry.py` with `@retry_on_busy()` decorator following `resilience/retry.py` pattern. Enabled WAL mode and 30s timeout in `get_db_connection()`. Applied decorator to 7 write functions. 17 concurrent write tests passing. 200 total tests passing.

**Files Created**:
- `data/db_retry.py` - `@retry_on_busy()` decorator with exponential backoff
- `tests/test_db_concurrency.py` - 17 tests for parallel writes, WAL mode, retry

**Files Modified**:
- `config/settings.py` - Added SQLITE_TIMEOUT, SQLITE_WAL_MODE, SQLITE_BUSY_* settings
- `data/data_store_main.py` - WAL mode, timeout, import retry decorator, apply to 7 functions
- `docs/architecture/DESIGN_PATTERNS.md` - Added pattern 16 (Database Retry)
- `docs/architecture/FILE_STRUCTURE.md` - Added data/ module files
- `docs/tasks/TASKS.md` - Marked Phase 4.0 complete

---

### 2025-12-27 (Session 34 - Database Concurrency Analysis)

| Task | Status |
|------|--------|
| Review codebase for database concurrency issues | ✅ Complete |
| Read architecture docs (DESIGN_PATTERNS, CONVENTIONS) | ✅ Complete |
| Analyze `data_store_main.py` for SQLite limitations | ✅ Complete |
| Add Phase 4.0 Database Concurrency tasks to TASKS.md | ✅ Complete |

**Summary**: Research session - no code written. Identified critical database concurrency issue: SQLite in `data_store_main.py` has no WAL mode, no timeout, no retry on BUSY errors. Added Phase 4.0 as BLOCKER before Phase 4.1.

---

*(Sessions 34 and earlier archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
