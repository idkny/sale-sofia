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

### 2025-12-26 (Session 2 - Solution F Design) - COMPREHENSIVE

| Task | Status |
|------|--------|
| Investigate mubeng benefits | ✅ Complete |
| Check if mubeng exposes proxy used | ✅ Complete |
| Analyze current proxy flow | ✅ Complete |
| Explore alternatives to bypass | ✅ Complete |
| Design Solution F | ✅ Complete |
| Document in TASKS.md | ✅ Complete |

---

#### THE PROBLEM WE'RE SOLVING

Two critical bugs found in Session 1 make proxy scoring non-functional:

**Bug 1: Wrong Proxy Tracked**
```python
# main.py currently does:
proxy = "http://localhost:8089"  # MUBENG_PROXY
response = StealthyFetcher.fetch(url, proxy=proxy)
proxy_pool.record_result(proxy, success=True)  # Records "localhost:8089"!

# But proxy_scorer.py expects:
# "1.2.3.4:8080" - actual proxy from live_proxies.json
```
Result: Scoring system tracks mubeng URL which doesn't exist in scores → does nothing.

**Bug 2: Removal Doesn't Persist**
```python
# proxy_scorer.py:remove_proxy() does:
del self.scores[proxy_key]      # ✅ Removes from memory
self.proxies = [filtered]       # ✅ Removes from list
self.save_scores()              # ✅ Saves proxy_scores.json
# ❌ MISSING: Does NOT update live_proxies.json!
```
Result: Bad proxies return on next session reload.

**Why This Matters**: These bugs block ALL downstream features:
- Automatic threshold-based proxy refresh
- Just-in-time proxy validation
- Retry with different proxy on failure

---

#### WHY WE REJECTED OTHER SOLUTIONS

**Solution A: Bypass Mubeng Completely**
- Problem: User asked "are we losing mubeng error handling?"
- Mubeng provides: timeout handling, SSL/TLS, connection management
- Concern: Don't want to reimplement these features

**Solution B: Get Proxy from Mubeng Headers**
- Research showed: Mubeng does NOT expose which proxy it used in response headers
- Dead end

**Solution C: Dual Mode (Mubeng for checking, direct for scraping)**
- Too complex: Two different proxy usage patterns
- Maintenance burden

**Solution D: Fix Persistence Only**
- Partial fix: Still tracks wrong proxy (Bug 1 unsolved)
- Only half the problem

**Solution E: Use X-Proxy-Offset Header**
- Initial idea: Use `X-Proxy-Offset: N` to select specific proxy
- Problem discovered: `--rotate-on-error` conflicts!
  - We send X-Proxy-Offset: 5 (want proxy 5)
  - Proxy 5 fails → mubeng silently rotates to proxy 6
  - Response succeeds → we think proxy 5 worked (WRONG!)
- Also: List synchronization issue when removing proxies mid-session

---

#### WHY SOLUTION F WORKS

**Key Discovery**: Mubeng has TWO features we can combine:

1. **`--watch` flag**: Auto-reload proxy file when it changes on disk
   - Source: [Mubeng README](https://github.com/mubeng/mubeng)
   - When we update the proxy file, mubeng reloads automatically
   - Lists stay in sync without restarting mubeng!

2. **`X-Proxy-Offset: N` header**: Select specific proxy by index
   - Source: [GitHub Issue #82](https://github.com/kitabisa/mubeng/issues/82)
   - Client sends header, mubeng uses `N % proxy_count` to select
   - We control exactly which proxy is used

3. **Omit `--rotate-on-error`**: Disable silent rotation
   - Without this flag, mubeng does NOT auto-retry on failure
   - We handle retries ourselves → know exactly which proxy failed

**How It Solves Each Bug**:

| Problem | How Solution F Fixes It |
|---------|------------------------|
| Wrong proxy tracked | X-Proxy-Offset selects exact proxy, we pass key to record_result() |
| Removal doesn't persist | Update proxy file → mubeng reloads via --watch |
| No retry logic | We control retries, select different proxy each attempt |
| List sync issues | --watch keeps mubeng in sync with file changes |

---

#### IMPLEMENTATION DETAILS

**Files to Modify**:

1. `proxies/mubeng_manager.py` (line 46-60):
   - Add `-w` or `--watch` flag to mubeng_command
   - REMOVE `--rotate-on-error` from mubeng_command
   - Keep: `-t 15s`, `-s`, `-m random`

2. `proxies/proxies_main.py` (line 94-102):
   - When creating temp proxy file, also store ordered list
   - Return ordered list alongside proxy_url and process
   - This list maps index → proxy_key for X-Proxy-Offset

3. `proxies/proxy_scorer.py`:
   - Add `get_proxy_index(proxy_key)` method
   - Add `_save_proxies()` method to persist to live_proxies.json
   - Call `_save_proxies()` inside `remove_proxy()`

4. `main.py` (line 133-140, 148-160):
   - Get proxy via `proxy_pool.select_proxy()`
   - Get index via `proxy_pool.get_proxy_index(proxy_key)`
   - Add `headers={"X-Proxy-Offset": str(index)}` to fetch
   - Add retry loop (max 3 proxies per URL)

**Current Mubeng Command** (`mubeng_manager.py:46-60`):
```python
mubeng_command = [
    str(MUBENG_EXECUTABLE_PATH),
    "-a", f"localhost:{desired_port}",
    "-f", str(live_proxy_file),
    "--rotate-on-error",  # ❌ REMOVE THIS
    "--max-errors", str(max_errors),
    "-m", "random",
    "-t", mubeng_timeout,
    "-s",
]
```

**New Mubeng Command**:
```python
mubeng_command = [
    str(MUBENG_EXECUTABLE_PATH),
    "-a", f"localhost:{desired_port}",
    "-f", str(live_proxy_file),
    "-w",  # ✅ ADD: Watch for file changes
    # REMOVED: --rotate-on-error
    "-m", "random",
    "-t", mubeng_timeout,
    "-s",
]
```

---

#### REFERENCES

- [TASKS.md - Solution F Section](TASKS.md#chosen-solution-solution-f---mubeng-with---watch--x-proxy-offset)
- [Mubeng GitHub](https://github.com/mubeng/mubeng)
- [Mubeng README](https://github.com/mubeng/mubeng/blob/master/README.md)
- [X-Proxy-Offset Issue #82](https://github.com/kitabisa/mubeng/issues/82)

**Key Files**:
- `proxies/mubeng_manager.py` - Mubeng command construction
- `proxies/proxies_main.py` - Proxy file creation + mubeng setup
- `proxies/proxy_scorer.py` - Scoring, selection, removal
- `main.py` - Scraping flow that uses proxies

---

#### RESUME INSTRUCTIONS FOR NEXT SESSION

1. Read this session history
2. Check TASKS.md for Phase 1 tasks (claimed by Instance 3)
3. Start with `mubeng_manager.py`: Add `-w`, remove `--rotate-on-error`
4. Test that mubeng starts correctly with new flags
5. Continue with remaining Phase 1 tasks

---

### 2025-12-26 (Session 1 - Proxy Scoring System Analysis)

| Task | Status |
|------|--------|
| Set up Instance 3 | ✅ Complete |
| Analyze main.py and orchestrator.py | ✅ Complete |
| Investigate automatic proxy refresh | ✅ Complete |
| Investigate proxy removal on failure | ✅ Complete |
| Investigate JIT proxy validation | ✅ Complete |
| Document findings in TASKS.md | ✅ Complete |

**Summary**: Deep analysis of proxy management system revealed two critical bugs that make the scoring system non-functional.

**Finding 1: Wrong Proxy Being Tracked**
- `main.py` uses mubeng (`localhost:8089`) as proxy
- `record_result()` receives mubeng URL, not actual proxy
- Scoring system tracks wrong entity → does nothing

**Finding 2: Proxy Removal Doesn't Persist**
- `remove_proxy()` removes from memory only
- Does NOT update `live_proxies.json`
- Bad proxies return on next session reload

**Root Cause**: Architecture mismatch - `ScoredProxyPool` designed for direct proxy usage, but system uses mubeng as intermediary.

**Finding 3: No Just-In-Time Proxy Validation**
- No liveness check before using proxy for scraping
- Dead proxies waste 15-30s per request
- No retry with different proxy on failure
- Mubeng's `--rotate-on-error` is reactive, not proactive

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Instance 1 (don't edit)
- [instance_002.md](instance_002.md) - Instance 2 (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
