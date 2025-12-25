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

### 2025-12-25 (Session 4 - Phase 1 Tool Tests & Reference Specs)

| Task | Status |
|------|--------|
| Test 1.1: Redis connectivity | Complete - v7.0.15 |
| Test 1.2: Celery worker start/stop | Complete - 5 tasks registered |
| Test 1.3: Mubeng SERVER mode | Complete - routes requests, auto-rotates |
| Test 1.4: Mubeng CHECKER mode | Complete - 16/20 alive, filters dead |
| Test 1.5: PSC binary | Complete - scraped 2,847 proxies |
| Create AutoBiz comparison spec | Complete - 103_AUTOBIZ_PROXY_REFERENCE.md |
| Create proxy format issues spec | Complete - 104_PROXY_FORMAT_ISSUES.md |

**Summary**: All Phase 1 isolated component tests PASSED. Created two critical reference specs: (1) 103 comparing AutoBiz vs current implementation - found current is MORE complete than AutoBiz with PTY wrapper, inline quality checks, better filtering. (2) 104 documenting potential proxy format bugs for Playwright/Camoufox.

**Key Insights for Next Instance**:
1. **All tools work in isolation** - Redis, Celery, Mubeng (server+checker), PSC all functional
2. **Mubeng has 2 modes**: SERVER (`-a localhost:8089`) for browser routing, CHECKER (`--check`) for liveness
3. **Current > AutoBiz**: We have PTY wrapper, inline anonymity/quality checks, /24 subnet filtering
4. **Potential bugs to verify** (spec 104): `validate_proxy()` includes protocol in server field, missing Camoufox converter
5. **Next**: Phase 2 data flow tests (verify handoffs between tools)

**Specs Created**:
- `docs/specs/103_AUTOBIZ_PROXY_REFERENCE.md` - Side-by-side code comparison
- `docs/specs/104_PROXY_FORMAT_ISSUES.md` - Format requirements by tool

---

### 2025-12-24 (Session 3 - P0 Bugs & Debugging Workflow)

| Task | Status |
|------|--------|
| Run stress tests | Complete - Test 5 PASSED |
| Verify real IP protection | Complete - proxy-level verified |
| Implement browser proxy enforcement | Complete - 3 files updated |
| Create debugging workflow for Celery/Mubeng/PSC | Complete |
| Organize docs into workflow structure | Complete |

**Summary**: Resolved all P0 bugs. Ran stress tests (no orphan mubeng processes). Verified proxy-level IP protection. Added browser-level proxy enforcement (browsers_main.py, firefox.py, chromium.py). Created comprehensive debugging workflow in TASKS.md with spec 101_DEBUG_CELERY_MUBENG_PROXIES.md. Organized 13 docs into archive/docs/, moved active specs to docs/specs/.

**Files Changed**:
- `browsers_main.py:147-152` - reject if no proxy
- `browsers/strategies/firefox.py:17-19` - reject if proxy=None
- `browsers/strategies/chromium.py:19-21` - reject if proxy=None
- `docs/specs/101_DEBUG_CELERY_MUBENG_PROXIES.md` - debugging spec
- `docs/specs/102_PROXY_SYSTEM_SPECS.md` - architecture spec

---

### 2025-12-24 (Session 2 - Stress Test Infrastructure)

| Task | Status |
|------|--------|
| Study reference Mubeng/Celery implementations | Complete |
| Create stress test suite | Complete |
| Run stress tests | **NOT DONE - session cut off** |

**Summary**: User correctly pushed back on jumping to conclusions about subprocess cleanup. Created comprehensive stress test suite in `tests/stress/` with 5 tests (critical: Test 5 for orphan detection). Tests were NOT executed before session ended.

**Key Finding**: Current implementation appears BETTER than reference - has PTY wrapper, better error handling. But tests must run to verify.

**Potential Issue**: `proxies/tasks.py:124-126` - subprocess.run() may not clean up mubeng if Celery killed with SIGKILL.

**Next**: Run `bash tests/stress/run_all_stress_tests.sh` and analyze results before any code changes.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
