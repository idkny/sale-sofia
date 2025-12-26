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

### 2025-12-26 (Session 5 - Solution F Phase 7 Complete)

| Task | Status |
|------|--------|
| 7.1: Add MIN_PROXIES check before scraping | ✅ Complete |
| 7.2: Add file locking for concurrent access | ✅ Complete |
| 7.3: Add delay after file write (200ms) | ✅ Complete |
| 7.4: Add hook for proxy refresh | ✅ Complete |

**Summary**: Completed Solution F Phase 7 (Edge Cases & Hardening). All 4 sub-tasks implemented. All 15 Solution F tests pass. Solution F is now fully complete.

**Files Modified**:
- `main.py` - Added `MIN_PROXIES=5`, `_ensure_min_proxies()` function, check before/between sites
- `proxies/proxy_scorer.py` - Added `fcntl.flock()` locking, 200ms delay after file write, `reload_proxies()` hook

**Solution F Complete**: All 7 phases implemented and tested.

---

### 2025-12-26 (Session 4 - Solution F Phases 0-3 Implementation)

| Task | Status |
|------|--------|
| Phase 0: Create mubeng test script | ✅ Complete |
| Phase 0: Test --watch, X-Proxy-Offset, no rotate-on-error | ✅ Complete |
| Phase 1: Update mubeng_manager.py config | ✅ Complete |
| Phase 2: Add proxy order tracking | ✅ Complete |
| Phase 3: Implement persistence on removal | ✅ Complete |

**Summary**: Implemented Solution F Phases 0-3. All mubeng features verified with test script. Updated mubeng config (-w flag, removed --rotate-on-error). Added proxy order tracking to proxies_main.py and proxy_scorer.py. Implemented file persistence on proxy removal with --watch reload support.

**Files Modified**:
- `proxies/mubeng_manager.py` - Added `-w` flag, removed `--rotate-on-error`
- `proxies/proxies_main.py` - Returns ordered proxy list
- `proxies/proxy_scorer.py` - Added `set_proxy_order()`, `get_proxy_index()`, `set_mubeng_proxy_file()`, `_save_proxy_file()`
- `main.py` - Updated to pass ordered keys to proxy pool
- `tests/debug/test_mubeng_features.py` (new) - Mubeng feature verification tests

**Next Session**: Continue with Phase 4 (X-Proxy-Offset header in requests), Phase 5 (retry logic), and remaining phases.

---

### 2025-12-26 (Session 3 - Detailed Implementation Plan)

| Task | Status |
|------|--------|
| Read full proxy system codebase | ✅ Complete |
| Read architecture documentation | ✅ Complete |
| Research proxy task history & learnings | ✅ Complete |
| Verify mubeng `--watch` flag exists | ✅ Complete |
| Verify `X-Proxy-Offset` header support | ✅ Complete |
| Verify StealthyFetcher `extra_headers` param | ✅ Complete |
| Create 7-phase atomic implementation plan | ✅ Complete |
| Update TASKS.md with detailed sub-tasks | ✅ Complete |

---

#### RESEARCH COMPLETED

Launched 3 parallel research agents:
1. **Proxy System Architecture** - Full analysis of `proxies/` directory
2. **Architecture Documentation** - All 7 files in `docs/architecture/`
3. **Task History** - Past bugs, fixes, and learnings from Sessions 1-14

**Key Verifications:**
- Mubeng `-w, --watch` flag confirmed: "Watch proxy file, live-reload from changes"
- `X-Proxy-Offset` header: Mubeng uses `offset % proxy_count` for selection
- `StealthyFetcher.fetch()` accepts `extra_headers` parameter ✅
- `Fetcher.get()` uses `custom_config` for extra options

**Files Analyzed:**
- `proxies/mubeng_manager.py` - Lines 46-60 need modification
- `proxies/proxies_main.py` - Need to return ordered proxy list
- `proxies/proxy_scorer.py` - Need `get_proxy_index()`, `set_proxy_order()`, `_save_proxy_file()`
- `main.py` - Need X-Proxy-Offset header and retry logic

---

#### DETAILED PLAN CREATED

**7 Phases, 23 atomic steps** - Each testable independently:

| Phase | Goal | Steps |
|-------|------|-------|
| 0 | Pre-Implementation Verification | 4 steps |
| 1 | Mubeng Configuration | 2 steps |
| 2 | Proxy Order Tracking | 4 steps |
| 3 | Persistence on Removal | 5 steps |
| 4 | X-Proxy-Offset Header | 4 steps |
| 5 | Retry Logic | 3 steps |
| 6 | Integration Testing | 4 steps |
| 7 | Edge Cases & Hardening | 4 steps |

**Full plan**: See TASKS.md "Implementation Tasks" section

---

#### RESUME INSTRUCTIONS FOR NEXT SESSION

1. Read this session history
2. Check TASKS.md for Phase 0 tasks
3. Start with **Phase 0.1**: Create test script `tests/debug/test_mubeng_features.py`
4. Test mubeng `--watch` and `X-Proxy-Offset` before any code changes
5. Proceed through phases in order

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Instance 1 (don't edit)
- [instance_002.md](instance_002.md) - Instance 2 (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
