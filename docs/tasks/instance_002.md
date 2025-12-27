---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-26
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

### 2025-12-27 (Session 28 - Dictionary-First Extraction)

| Task | Status |
|------|--------|
| Investigate has_elevator 0% accuracy | Complete |
| Fix has_elevator with dictionary bypass | Complete |
| Implement dictionary-first for all fields | Complete |
| Cleanup unused code and tests | Complete |
| Update documentation (specs 107, 110) | Complete |

**Summary**: Fixed has_elevator extraction (was 0%, now 100%) by using dictionary directly. Implemented full dictionary-first approach where dictionary extracts ALL field types (numeric, boolean, enum) and LLM is only a fallback. Overall accuracy now 100%. Cleaned up deprecated code and orphaned tests.

**Files Modified**:
- `llm/dictionary.py` - enum extraction, removed unused log_unknown()
- `llm/llm_main.py` - dictionary-first override for all fields
- `llm/prompts.py` - removed deprecated EXTRACTION_PROMPT
- `docs/specs/107_OLLAMA_INTEGRATION.md` - status: Implemented
- `docs/specs/110_DYNAMIC_BULGARIAN_DICTIONARY.md` - status: Implemented
- Deleted: `tests/llm/test_model_comparison.py`

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

### 2025-12-27 (Session 27 - Consolidate Scoring Constants)

| Task | Status |
|------|--------|
| Fix min_count=5 bug in main.py | Complete |
| Fix min_count=5 defaults in orchestrator.py | Complete |
| Add scoring constants to config/settings.py | Complete |
| Update proxy_scorer.py to import from settings | Complete |
| Update proxy_validator.py to import from settings | Complete |

**Summary**: Fixed min_count inconsistency bug (was hardcoded as 5, should use MIN_PROXIES_FOR_SCRAPING=10). Consolidated duplicate scoring constants (SCORE_SUCCESS_MULTIPLIER, SCORE_FAILURE_MULTIPLIER, MAX_PROXY_FAILURES, MIN_PROXY_SCORE) into config/settings.py. Both proxy_scorer.py and proxy_validator.py now import from settings. Fixed edge case in test_auto_prune_on_low_score test.

**Files Modified**:
- `config/settings.py` - added scoring constants section
- `main.py:359,453` - use MIN_PROXIES_FOR_SCRAPING instead of hardcoded 5
- `orchestrator.py:35,491,527` - import and use MIN_PROXIES_FOR_SCRAPING as defaults
- `proxies/proxy_scorer.py:32-43` - import from settings, keep aliases for backward compat
- `proxies/proxy_validator.py:29-51` - import from settings, keep aliases for backward compat
- `tests/test_proxy_scorer.py:235-237` - fix edge case test (MIN_SCORE * 1.9 instead of * 2)

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
