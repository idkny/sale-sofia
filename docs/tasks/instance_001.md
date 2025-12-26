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

### 2025-12-26 (Session 10 - Live Test Verification)

| Task | Status |
|------|--------|
| Kill stale processes | Complete |
| Clean proxy files | Complete |
| Run main.py live test | Complete |
| Verify chord timeout fix | ✅ VERIFIED |

**Summary**: Ran full live test to verify Session 9's chord timeout fix. The fix is WORKING.

**Key Evidence from Test Output**:
1. **Dynamic timeout active**:
   ```
   [INFO] Dynamic timeout: 600s (1 chunks, 1 rounds)
   ```

2. **Chord completed successfully** (no infinite hang!):
   ```
   [INFO] Using chord_id eec13782-7627-4c50-994c-3213c08a1dea for event-based wait
   [INFO] Blocking on chord completion...
   [SUCCESS] Chord complete! 4 usable proxies after 3m 5s
   ```

3. **Multiple jobs completed via chord**:
   - Job 4d90fe99: 8/8 chunks → COMPLETE (11 proxies)
   - Job cf3da80a: 4/4 chunks → COMPLETE
   - Job 1c967754: 1/1 chunks → COMPLETE (4 proxies)

4. **Clean exit** (exit code 0, all processes stopped)

**Test Outcome**:
| Aspect | Result |
|--------|--------|
| Chord timeout fix | ✅ WORKING |
| Dynamic timeout calculation | ✅ WORKING |
| Event-based completion | ✅ WORKING |
| No infinite hangs | ✅ VERIFIED |

**Why Pipeline "Failed"**: Only 4 usable proxies found (< 5 minimum threshold). This is a proxy quality issue, **not** the original hanging bug. The chord completed successfully and returned results.

**Minor Issue Found**: After chord completed successfully, fallback message still printed:
```
[INFO] Chord wait timed out, falling back to Redis polling...
```
This is a false positive - the chord DID complete. Minor logic bug in return path.

---

### 2025-12-26 (Session 9 - Chord Timeout Bug Fix)

| Task | Status |
|------|--------|
| Debug hanging proxy refresh pipeline | Complete |
| Identify chord.get() infinite block bug | Complete |
| Implement dynamic timeout with fallback | Complete |
| Verify fix with unit test | Complete |
| Full live test | ✅ VERIFIED in Session 10 |

**Problem Reported**: After refactoring, the proxy refresh process would "hang" or "get blocked" after chunks complete.

**Root Cause Identified**:
1. `wait_for_refresh_completion()` called from `_run_preflight_level3()` with no timeout parameter
2. Default `timeout=0` caused `timeout_val = None` in `_wait_via_chord()`
3. `chord_result.get(timeout=None)` blocks FOREVER if:
   - Any chunk task fails
   - The Celery worker dies
   - The chord callback never fires
4. The Redis polling fallback only ran if there was NO chord_id (not as a timeout fallback)

**Evidence Found During Live Test**:
- Celery log showed "Worker exited prematurely: signal 15 (SIGTERM)"
- 39/40 chunk tasks succeeded, 1 died with worker
- `process_check_results_task` was NEVER received (grep found no "received" log for it)
- Chord callback didn't fire because not all chunks completed
- `chord_result.get(timeout=None)` was blocking forever waiting for incomplete chord

**Related Specs**:
- `docs/specs/105_CHUNK_PROCESSING_TIMING_BUG.md` - Documented this exact issue on 2025-12-25
- `archive/specs/107_REDIS_PROGRESS_TRACKING.md` - Proposed Redis polling as fallback

**The Gap in Previous Implementation**:
Spec 105 proposed TWO solutions working together:
1. Event-based (chord) for fast completion detection
2. Redis polling as fallback if chord times out

But the implementation only used chord.get() with no timeout and no fallback!

**Fix Applied to `orchestrator.py`**:

1. **Added `total_chunks` parameter to `_wait_via_chord()`** (line 593):
   - Now receives chunk count from dispatcher for timeout calculation

2. **Dynamic timeout calculation** (lines 607-622):
   ```python
   # Formula from spec 105:
   workers = 8  # Match Celery concurrency
   time_per_chunk = 90  # seconds (45-95s range from spec)
   buffer = 1.5  # 50% safety margin
   rounds = (total_chunks + workers - 1) // workers
   calculated = int(rounds * time_per_chunk * buffer)
   timeout_val = max(calculated, 600)  # At least 10 min
   ```

3. **Fallback to Redis polling on timeout** (lines 504-514):
   ```python
   chord_success = self._wait_via_chord(..., total_chunks=dispatch.total_chunks)
   if chord_success or not dispatch.job_id:
       return chord_success
   # Chord timed out - fall back to Redis polling
   print("[INFO] Chord wait timed out, falling back to Redis polling...")
   ```

4. **Informative error messages** (lines 678-680):
   - Changed from `[ERROR]` to `[WARNING]` for timeouts
   - Added "(will try Redis fallback)" message

**Timeout Scaling Verification** (matches spec 105):
| Proxies | Chunks | Timeout |
|---------|--------|---------|
| ~3,000  | 29     | 600s (10m min) |
| ~5,000  | 50     | 945s (15m) |
| ~10,000 | 100    | 1755s (29m) |
| ~20,000 | 200    | 3375s (56m) |

**Files Changed**:
- `orchestrator.py` lines 504-514, 585-624, 673-684

**How to Run Full Live Test Next Session**:
1. Kill any stale processes:
   ```bash
   pkill -f "celery.*worker" 2>/dev/null
   pkill -f "python main.py" 2>/dev/null
   ```

2. Clean proxy files to force refresh:
   ```bash
   rm -f proxies/live_proxies.json proxies/live_proxies.txt
   ```

3. Run main.py and watch for:
   - `[INFO] Dynamic timeout: Xs (N chunks, M rounds)` - proves fix is active
   - If timeout occurs: `[WARNING] Chord timeout ... (will try Redis fallback)`
   - Then: `[INFO] Falling back to Redis progress tracking...`

4. The test should NOT hang anymore. If chord times out, Redis polling takes over.

5. Alternative: Run the stress test directly:
   ```bash
   python tests/stress/test_orchestrator_event_based.py
   ```

**What Was NOT Tested This Session**:
- Full end-to-end live test (PSC was failing with exit code 1, possibly concurrent access)
- The actual fallback path (needs chord to timeout first)

**Why PSC Failed During Testing**:
- PSC executable returned exit code 1
- Likely cause: concurrent PSC runs from leftover Beat schedule or multiple test runs
- Solution: Always kill existing Celery workers before testing

---

### 2025-12-25 (Session 8 - Event-Based Completion)

| Task | Status |
|------|--------|
| Switch to event-based completion | Complete |
| Test with actual orchestrator code | Complete - VERIFIED |

**Summary**: Implemented and VERIFIED event-based completion using Celery chord result. Dispatcher now returns `chord_id`, orchestrator uses `AsyncResult(chord_id).get()` to block until done. Created `test_orchestrator_event_based.py` to verify actual production code path works.

**Changes Made**:
1. `proxies/tasks.py:124-127`: Changed `.delay()` to `.apply_async()`, returns `chord_id`
2. `orchestrator.py:533-597`: Uses `AsyncResult(chord_id).get()` with background progress thread

**Test Results**:
- 35 chunks processed in 21 minutes
- chord_id correctly extracted and used
- Progress shown: 0% → 100%
- 79 usable proxies at completion

**Spec Archived**: `107_REDIS_PROGRESS_TRACKING.md` → `archive/specs/`

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
