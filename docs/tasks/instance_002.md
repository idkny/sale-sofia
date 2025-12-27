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

### 2025-12-27 (Session 25 - Dashboard Integration + Unified Timeout)

| Task | Status |
|------|--------|
| Add price history chart component | Complete |
| Add "recently changed" filter | Complete |
| Create unified PROXY_TIMEOUT_SECONDS | Complete |
| Update all proxy timeout usages | Complete |

**Summary**: Implemented Dashboard Integration (Spec 111 Phase 3) and unified proxy timeout settings. Added price history chart tab and "recently changed" filter to Listings page. Created `config/settings.py` with `PROXY_TIMEOUT_SECONDS=45` to fix inconsistent 15s/30s/45s timeouts across codebase.

**Files Created**:
- `config/settings.py` - unified proxy timeout constants (PROXY_TIMEOUT_SECONDS, PROXY_TIMEOUT_MS, PROXY_TIMEOUT_MUBENG)

**Files Modified**:
- `app/pages/2_Listings.py` - price history tab, recently changed filter
- `main.py` - import and use PROXY_TIMEOUT_SECONDS/MS
- `proxies/mubeng_manager.py` - use PROXY_TIMEOUT_MUBENG
- `proxies/quality_checker.py` - use PROXY_TIMEOUT_SECONDS
- `proxies/tasks.py` - use PROXY_TIMEOUT_SECONDS

---

### 2025-12-27 (Session 24 - Page Change Detection Phases 1-2)

| Task | Status |
|------|--------|
| Create data/change_detector.py | Complete |
| Add 5 DB columns (migration) | Complete |
| Update save_listing() | Complete |
| Integrate into main.py | Complete |
| Create unit tests (24 tests) | Complete |

**Summary**: Implemented Page Change Detection (Spec 111) Phases 1-2. Created `data/change_detector.py` with compute_hash (SHA256 of key fields), has_changed (comparison), and track_price_change (history with 10-entry max). Added 5 DB columns. Integrated via `_check_and_save_listing()` in main.py. Unchanged listings now skipped, price changes logged.

**Files Created**:
- `data/change_detector.py` - core change detection (compute_hash, has_changed, track_price_change)
- `tests/test_change_detector.py` - 24 unit tests

**Files Modified**:
- `data/data_store_main.py` - migration (5 columns), save_listing(), increment_unchanged_counter()
- `main.py:25,45-92,206,241-253,602-604` - import, helper, stats, integration, summary

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
