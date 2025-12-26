# Instance 1 - Session 9 (Archived)

**Date**: 2025-12-26
**Title**: Chord Timeout Bug Fix

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

**Note**: time_per_chunk was later updated from 90s to 400s in Session 12 based on production data.
