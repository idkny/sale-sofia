# Tasks - Single Source of Truth

**RULES:**
1. Claim tasks with `[Instance N]` before starting
2. Mark complete with `[x]` when done
3. Unclaim if not finishing this session

---

## Instance Coordination

| Instance | Current Task |
|----------|--------------|
| 1 | Available |
| 2 | Available |
| 3 | Available |

**Session 24 (2025-12-27)**: Instance 2 - Implemented Page Change Detection (Spec 111) Phases 1-2. Created `data/change_detector.py` with compute_hash, has_changed, track_price_change. Added 5 DB columns (content_hash, last_change_at, change_count, price_history, consecutive_unchanged). Integrated into main.py via `_check_and_save_listing()`. 24 unit tests pass. Unchanged listings now skipped, price changes logged with history.

**Session 23 (2025-12-26)**: Instance 3 - Completed Solution F Phase 7 (Edge Cases & Hardening). Added MIN_PROXIES check with auto-refresh, fcntl file locking, 200ms delay after file write, reload_proxies() hook for order sync. All 15 Solution F tests pass. Solution F complete.

**Session 22 (2025-12-26)**: Instance 2 - Completed Ollama Phase 5 (Production Hardening). Added extraction cache (Redis, 7-day TTL), confidence threshold config, metrics logging (get_metrics/reset_metrics), performance test. Researched page change detection from autobiz, created Spec 111. Updated SCRAPER_GUIDE.md with LLM documentation.

**Session 21 (2025-12-26)**: Instance 3 - Completed Solution F Phase 6 (Integration Testing). Created 6 integration tests, all pass. Fixed deadlock bug (Lock→RLock). Also increased mubeng liveness timeout 10s→45s for slow proxies. Solution F Phases 0-6 complete. Next: Phase 7 (edge cases).

**Session 20 (2025-12-26)**: Instance 1 - Implemented automatic service lifecycle management (cleanup_stale_processes, health checks). Fixed TimeLimitExceeded bug: quality timeout 60s→45s, task time_limit 8min→15min. Both chords completed (38/38, 33/33). Pre-flight still failing - proxies pass liveness but fail HTTP.

**Session 19 (2025-12-26)**: Instance 3 - Completed Solution F Phase 4 + Phase 5. Phase 4: X-Proxy-Offset header in main.py, fixed Fetcher API. Phase 5: Retry logic with MAX_PROXY_RETRIES=3, different proxy each attempt. All 9 tests pass.

**Session 18 (2025-12-26)**: Instance 3 - Implemented Solution F Phases 0-3. Created mubeng test script, updated mubeng config (-w flag, removed --rotate-on-error), added proxy order tracking to proxies_main.py and proxy_scorer.py, implemented persistence on removal. All phases verified with tests.

**Session 17 (2025-12-26)**: Instance 2 - Completed Phase 4 Scrapling Integration. Added `use_llm` flag, integrated LLM extraction into imot_scraper.py. LLM fills gaps where CSS returns None (e.g., orientation). Tested end-to-end, confidence 0.95.

**Session 16 (2025-12-26)**: Instance 3 - Created detailed 7-phase implementation plan for Solution F with ~30 atomic, testable steps. Verified mubeng `--watch` flag, `X-Proxy-Offset` header, and Scrapling `extra_headers` support. Plan documented in TASKS.md.

**Session 15 (2025-12-26)**: Instance 2 - Tested Phase 3 (temperature=0). No effect on accuracy (97.4% unchanged). `has_elevator` still fails - not a temperature issue.

**Session 14 (2025-12-26)**: Instance 3 - Investigated proxy scoring fix options. Discovered mubeng `--watch` flag for live-reload + `X-Proxy-Offset` header for proxy selection. Designed Solution F that keeps mubeng while enabling proper tracking.

**Session 13 (2025-12-26)**: Instance 3 - Found 2 CRITICAL issues: (1) Proxy scoring broken (tracks mubeng URL, not actual proxy; removal doesn't persist), (2) No JIT proxy validation (no pre-check, no retry, dead proxies waste time). Both block automatic threshold refresh.

**Session 10 (2025-12-26)**: Instance 2 - Tested Phase 2 few-shot examples. Caused regressions (heating_type, orientation dropped). Skipped Phase 2 - 97.4% already exceeds target, remaining options in Phase 3-5.

**Session 9 (2025-12-26)**: Instance 2 - Verified + fixed Phase 1 dictionary implementation. Fixed `heating` → `heating_type` field mismatch, removed single-letter false positives (И/Ю/С/З), fixed `парк` matching in `паркомясто`. Accuracy: 69% → **97.4%** (exceeds 95% target).

**Session 8 (2025-12-26)**: Instance 2 - Research + implement dynamic Bulgarian dictionary for LLM extraction (Spec 110). Created comprehensive dictionary with 400+ terms from 4 research agents. Implementation complete.

**Session 12 (2025-12-26)**: Fixed `wait_for_proxies` blind polling bug + increased dynamic timeout (90s→400s per chunk) + added task time limits (7min soft, 8min hard).

**Session 11 (2025-12-26)**: Fixed false positive fallback msg + proxy overwrite bug. Found new bug: `wait_for_proxies` uses blind polling instead of chord wait.

**Session 10 (2025-12-26)**: Verified chord timeout fix works. Chord completes successfully, no hangs.

**Session 9 (2025-12-26)**: Fixed chord.get() infinite block bug. Added dynamic timeout calculation + Redis fallback.

**Claim**: Add `[Instance N]` next to task before starting
**Complete**: Add `[x]` and remove `[Instance N]` when done

---

## Bugs (P0)

- [x] Run stress tests - Test 5 PASSED: no orphan mubeng processes

- [x] Proxy-level real IP protection (verified implemented)
  - quality_checker.py:143-155 - rejects if exit_ip matches /24 subnet
  - tasks.py:160-173 - filters /24 subnet matches
  - tasks.py:223-226 - removes Transparent proxies
  - anonymity_checker.py - detects Elite/Anonymous/Transparent

- [x] Browser-level proxy enforcement (implemented)
  - browsers_main.py:147-152 - rejects if validated_proxy=None
  - firefox.py:17-19 - rejects if proxy=None
  - chromium.py:19-21 - rejects if proxy=None

---

## CRITICAL BUG: Proxy Scoring System Broken (P0) ✅ FIXED

**Found by**: Instance 3 (Session 1, 2025-12-26)
**Status**: ✅ Complete (Solution F - Sessions 14-23)
**Unblocks**: Automatic threshold-based proxy refresh

### Finding 1: Wrong Proxy Being Tracked

**Location**: `main.py:148-160`

**Problem**: `main.py` uses mubeng as an auto-rotating proxy (`http://localhost:8089`). When recording success/failure, it passes this mubeng URL to `proxy_pool.record_result()` instead of the actual underlying proxy.

```python
# main.py - What happens:
proxy = "http://localhost:8089"  # MUBENG_PROXY
proxy_pool.record_result(proxy, success=True)  # Records "localhost:8089"!

# proxy_scorer.py - What it expects:
# "1.2.3.4:8080" - actual proxy from live_proxies.json
```

**Evidence**:
- `main.py:35` - `MUBENG_PROXY = "http://localhost:8089"`
- `main.py:135` - `proxy=proxy or MUBENG_PROXY`
- `main.py:148-160` - `proxy_pool.record_result(proxy, success=...)` where proxy is mubeng URL
- `proxy_scorer.py:270-271` - Logs warning "Proxy localhost:8089 not found in scores"

**Impact**: The entire scoring system does nothing because it's tracking "localhost:8089" which doesn't exist in `live_proxies.json`.

### Finding 2: Proxy Removal Doesn't Persist

**Location**: `proxies/proxy_scorer.py:306-344`

**Problem**: When `remove_proxy()` is called (after 3 failures or score < 0.01), it removes the proxy from in-memory lists but does NOT update `live_proxies.json`.

```python
def remove_proxy(self, proxy_key: str) -> bool:
    with self.lock:
        del self.scores[proxy_key]           # ✅ Removes from scores dict
        self.proxies = [p for p in ...]      # ✅ Removes from memory list
        self.save_scores()                    # ✅ Saves proxy_scores.json
        # ❌ MISSING: Does NOT save to live_proxies.json!
```

**Impact**:
1. Bad proxy removed from memory (won't be used this session)
2. Next session: `live_proxies.json` is reloaded → bad proxy is back!
3. `_initialize_scores()` gives it a fresh score → starts over

### Conclusion

The `ScoredProxyPool` was designed for **direct proxy usage**, but the system uses **mubeng as an intermediary** that hides actual proxy identity. This architectural mismatch makes the scoring system non-functional.

**Current state**:
- ❌ Proxy scoring: Not working (wrong proxy tracked)
- ❌ Auto-removal: Not persisted (bad proxies return next session)
- ❌ Threshold-based refresh: Cannot work until above are fixed

### Chosen Solution: Solution F - Mubeng with --watch + X-Proxy-Offset

**Decision Date**: 2025-12-26 (Session 14)
**Decided By**: Instance 3

#### Key Discovery

Mubeng supports two features that solve our problems:
1. `--watch` flag: Live-reload proxy file when it changes
2. `X-Proxy-Offset: N` header: Select specific proxy by index

#### How Solution F Works

```
┌─────────────────────────────────────────────────────────────┐
│ START: mubeng --watch -f proxies.txt (NO --rotate-on-error) │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ SCRAPING:                                                   │
│ 1. proxy = pool.select_proxy()       # Weighted selection   │
│ 2. index = find_index(proxy)         # Position in file     │
│ 3. request with X-Proxy-Offset: index                       │
│ 4. Mubeng uses EXACTLY that proxy (no silent rotation)      │
│ 5. record_result(proxy, success)     # Track correct proxy! │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ REMOVING BAD PROXY:                                         │
│ 1. pool.remove_proxy(bad_proxy)                             │
│ 2. Update proxies.txt file                                  │
│ 3. Mubeng detects change → auto-reloads                     │
│ 4. Lists stay in sync!                                      │
└─────────────────────────────────────────────────────────────┘
```

#### Why This Works for All Phases

| Phase | Works? | How |
|-------|--------|-----|
| **1. Proxy Tracking** | ✅ | X-Proxy-Offset + no silent rotation |
| **2. Persistence** | ✅ | Update file → mubeng reloads via --watch |
| **3. JIT Validation** | ✅ | We control retries, know which proxy failed |
| **4. Threshold Refresh** | ✅ | Accurate count, update file triggers reload |

#### Key Mubeng Flags

| Flag | Purpose |
|------|---------|
| `--watch` | Auto-reload proxy file when changed |
| (omit `--rotate-on-error`) | No silent rotation - we control retries |
| `-t 15s` | Timeout per request |
| `-s` | Sync mode for predictable behavior |

#### What We Keep vs Replace

| Mubeng Feature | Status |
|----------------|--------|
| Proxy forwarding | ✅ Keep |
| Timeout handling | ✅ Keep |
| SSL/TLS handling | ✅ Keep |
| `--rotate-on-error` | ❌ Remove (we handle retries) |
| Random rotation | ❌ Replace with X-Proxy-Offset |

### Implementation Tasks

**DETAILED PLAN** (Session 16, 2025-12-26)
Each step is atomic and testable. Must complete in order.

---

#### Phase 0: Pre-Implementation Verification ✅

**Goal**: Verify mubeng features work as documented before writing any code.

- [x] **0.1** Create test script `tests/debug/test_mubeng_features.py`
- [x] **0.2** Test `--watch` flag: Start mubeng, modify proxy file, verify reload
- [x] **0.3** Test `X-Proxy-Offset` header: Send requests with specific offsets
- [x] **0.4** Test behavior without `--rotate-on-error`

---

#### Phase 1: Mubeng Configuration ✅

**Goal**: Update mubeng startup to enable `--watch` and disable silent rotation.

- [x] **1.1** Edit `proxies/mubeng_manager.py` - Added `-w` flag, removed `--rotate-on-error` and `--max-errors`
- [x] **1.2** Test: Mubeng starts correctly with new flags

---

#### Phase 2: Proxy Order Tracking ✅

**Goal**: Maintain ordered list matching mubeng's loaded order for X-Proxy-Offset mapping.

- [x] **2.1** Edit `proxies/proxies_main.py` - `get_and_filter_proxies()` now returns `Tuple[Path, List[str]]`
- [x] **2.2** Edit `proxies/proxies_main.py` - `setup_mubeng_rotator()` returns 4-tuple with ordered keys
- [x] **2.3** Edit `proxies/proxy_scorer.py` - Added `set_proxy_order()` and `get_proxy_index()` methods
- [x] **2.4** Test: Index mapping works correctly (verified with unit test)

---

#### Phase 3: Persistence on Removal ✅

**Goal**: When proxy is removed, update file so mubeng reloads via `--watch`.

- [x] **3.1** Edit `proxies/proxy_scorer.py` - Added `_mubeng_proxy_file` attr + `set_mubeng_proxy_file()` method
- [x] **3.2** Edit `proxies/proxy_scorer.py` - Added `_save_proxy_file()` method
- [x] **3.3** Edit `proxies/proxy_scorer.py` - Updated `remove_proxy()` to persist + rebuild index
- [x] **3.4** Test: Removal persists to file (verified - indexes shift correctly)
- [x] **3.5** Test: Mubeng stays running after file modification (--watch reload verified)

---

#### Phase 4: X-Proxy-Offset Header in Requests ✅

**Goal**: Add header to all fetch requests so we know which proxy is used.

- [x] **4.1** Verify Scrapling supports `extra_headers`
  - `StealthyFetcher.fetch()` accepts `extra_headers` parameter
  - `Fetcher.get()` accepts `headers` kwarg (passed to httpx)

- [x] **4.2** Edit `main.py` - Update `_scrape_listings()` function
  - Added proxy selection with `proxy_pool.select_proxy()`
  - Added `extra_headers={"X-Proxy-Offset": str(index)}`
  - Changed `record_result(proxy_key, ...)` to use actual proxy key

- [x] **4.3** Edit `main.py` - Update `_collect_listing_urls()` function
  - Changed `Fetcher.fetch()` to `Fetcher.get()` (correct API)
  - Added `headers={"X-Proxy-Offset": str(index)}`
  - Changed `record_result(proxy_key, ...)` to use actual proxy key

- [x] **4.4** Test: Verify correct proxy is tracked
  - Created `tests/debug/test_phase4_proxy_tracking.py`
  - All 4 tests pass: proxy key format, header logic, no localhost tracking, pool integration

---

#### Phase 5: Retry Logic ✅

**Goal**: On failure, try different proxy instead of giving up immediately.

- [x] **5.1** Edit `main.py` - Add retry loop to `_scrape_listings()`
  - Added `MAX_PROXY_RETRIES = 3` constant
  - Retry loop selects NEW proxy each attempt
  - Network errors trigger retry, extraction failures don't
  - Logs attempt number on each failure

- [x] **5.2** Edit `main.py` - Add retry to `_collect_listing_urls()`
  - Same pattern with `page_success` tracking
  - Breaks pagination if all retries fail

- [x] **5.3** Test: Verify retry logic
  - Created `tests/debug/test_phase5_retry_logic.py`
  - All 5 tests pass: constant exists, retry loops, no retry on extraction, stats tracking

---

#### Phase 6: Integration Testing ✅

**Goal**: End-to-end verification of all components working together.

- [x] **6.1** Create integration test: `tests/debug/test_solution_f_integration.py`

- [x] **6.2** Test scenario: Mixed proxy pool (6 tests, all pass)
  - Bad proxies auto-removed after 3 failures
  - Good proxies retain higher scores

- [x] **6.3** Test scenario: Persistence across sessions
  - Removed proxy stays removed in new pool

- [x] **6.4** Test scenario: Index synchronization
  - Indexes shift correctly after removal

**Bug Fixed**: `threading.Lock()` → `threading.RLock()` in proxy_scorer.py (deadlock fix)

---

#### Phase 7: Edge Cases & Hardening ✅

**Goal**: Handle edge cases to prevent bugs in production.

- [x] **7.1** Add MIN_PROXIES check before scraping
  - Added `MIN_PROXIES = 5` constant and `_ensure_min_proxies()` function
  - Called before crawl starts and after each site completes

- [x] **7.2** Add file locking for concurrent access
  - Added `fcntl.flock(LOCK_EX/LOCK_UN)` in `_save_proxy_file()`
  - Prevents race condition with Celery refresh

- [x] **7.3** Add delay after file write
  - Added `time.sleep(0.2)` after `_save_proxy_file()` in `remove_proxy()`
  - Gives mubeng time to detect and reload

- [x] **7.4** Add hook for proxy refresh
  - Updated `reload_proxies()` to rebuild `_proxy_order` and `_index_map`
  - Keeps index map synchronized after Celery refresh

---

### Rollback Plan

If Solution F causes regressions:
1. Revert `mubeng_manager.py`: Re-add `--rotate-on-error`, remove `-w`
2. Revert `main.py`: Remove `X-Proxy-Offset` header, remove retry loop
3. Keep `proxy_scorer.py` improvements (they're additive, don't break anything)

**Result**: Scraping continues as before (just without working proxy scoring)

### References

- [Mubeng GitHub](https://github.com/mubeng/mubeng)
- [X-Proxy-Offset Issue #82](https://github.com/kitabisa/mubeng/issues/82)
- [Mubeng README](https://github.com/mubeng/mubeng/blob/master/README.md)

### Dependency

**After this is fixed**, we can implement:
- [ ] Automatic threshold-based proxy refresh (check count every N minutes, refresh if < X)

---

## CRITICAL BUG: Chunk Processing Timing (P1)

**Spec**: [105_CHUNK_PROCESSING_TIMING_BUG.md](../../archive/specs/105_CHUNK_PROCESSING_TIMING_BUG.md) *(archived - all tasks complete)*

**Bug Found During Test 2.2.6**: The test terminated BEFORE chunks finished processing because of hardcoded timeout.

### The Problem
```
Dispatcher returns immediately: "Dispatched 29 chunks"
But chunks take 45-95 seconds EACH
29 chunks ÷ 4 workers × 70s average = ~8 rounds × 70s = ~10 minutes
Test only waited 5 minutes → FAIL
```

### Why This Matters for Production
1. **Hardcoded timeouts don't scale** - if PSC scrapes 10,000 proxies, it needs 35+ min
2. **Dispatcher returns immediately** - waiting on its result doesn't wait for chunks
3. **Production code may have same bug** - check orchestrator.py, any monitoring code

### Scaling Reality
| Proxies | Chunks | Time Needed |
|---------|--------|-------------|
| 2,897 | 29 | ~11 min |
| 5,000 | 50 | ~18 min |
| 10,000 | 100 | ~35 min |

### Tasks Before Production
- [x] Review `orchestrator.py` for hardcoded timeouts (wait_for_refresh_completion:445-461 only waits 30s)
- [x] Review `tasks.py` for dispatcher wait patterns (dispatcher returns immediately)
- [x] Implement Redis progress tracking
  - `proxies/tasks.py`: Redis keys for progress tracking
  - `orchestrator.py`: `get_refresh_progress()` method
- [x] Switch to event-based completion (CRITICAL - next step)
  - Dispatcher returns chord_id: `proxies/tasks.py:124-127`
  - Orchestrator uses `AsyncResult(chord_id).get()`: `orchestrator.py:533-597`
  - Background thread shows progress during wait
- [x] Test full pipeline end-to-end with event-based completion
  - test_orchestrator_event_based.py: 35 chunks, 21min, chord_id verified
  - Proof: `[INFO] Using chord_id ... for event-based wait`
- [x] Fix chord.get() infinite block bug (Session 9)
  - Bug: `chord_result.get(timeout=None)` blocked forever if any chunk failed
  - Fix: Dynamic timeout calculation + fallback to Redis polling
  - `orchestrator.py:504-514` - fallback logic
  - `orchestrator.py:594-600` - dynamic timeout: `max((chunks/8)*400*1.5, 600)` (updated Session 12)
- [x] Verify chord timeout fix with full live test (Session 10)
  - Verified: Dynamic timeout active, chord completes without hanging
- [x] Fix false positive fallback message (Session 11, commit 5b71300)
  - Changed `_wait_via_chord` return: `None`=timeout, `True/False`=completed
- [x] Fix proxy file overwrite bug (Session 11, commit 9d5d3ad)
  - `_save_proxy_files` now merges instead of overwrites
- [x] Fix `wait_for_proxies` blind polling bug (Session 12)
  - `wait_for_proxies` now calls `wait_for_refresh_completion(task_id)`
  - Uses signal-based wait (chord/Redis) instead of blind polling
  - Dynamic timeout based on chunk count (per spec 105/107)

---

## Debugging: Celery + Mubeng + PSC Integration (P1)

**Spec**: [101_DEBUG_CELERY_MUBENG_PROXIES.md](../specs/101_DEBUG_CELERY_MUBENG_PROXIES.md)
**Goal**: Make tools work together reliably to always provide fresh working proxies

### Phase 1: Isolated Component Tests (2025-12-25 - ALL PASSED)
- [x] Test 1.1: Redis connectivity - v7.0.15, standalone mode
- [x] Test 1.2: Celery worker start/stop - 5 tasks registered, ping OK
- [x] Test 1.3: Mubeng SERVER mode - loads 123 proxies, auto-rotates, routes requests
- [x] Test 1.4: Mubeng CHECKER mode - 16/20 alive, filters dead proxies correctly
- [x] Test 1.5: PSC binary - scraped 2,847 proxies, valid JSON output

### Phase 2: Integration Tests
- [x] Test 2.1: Celery + Redis integration - ALL PASSED (import, worker start, task execution, worker stop, orphan detection)
- [x] Test 2.2: Celery + Mubeng - PASSED (task executed 0.037s, warm shutdown, no orphans, fixed pgrep false positive)
- [x] Test 2.2.5: Celery + PSC - PASSED (scraped 2,897 proxies in 180s, graceful shutdown, no orphans)
- [x] Test 2.2.6: PSC → Dispatcher → Mubeng - PASSED (2897→48 proxies, 29 chunks, 11min, enrichment verified)
  - **Why**: Previous tests verified tools run, but not that DATA flows correctly between them
  - **What it tests**: PSC output format → Dispatcher parsing → Chunk splitting → Mubeng parallel workers → Result aggregation
  - **How it helps**: If Test 2.3 fails, we'll know it's NOT a data format or dispatcher issue
  - **File**: `tests/stress/test_psc_dispatcher_mubeng.py`
- [x] Test 2.3: Full pipeline end-to-end - PASSED (5000 proxies → 79 live, 16min chunk phase)
  - **File**: `tests/stress/test_full_pipeline.py`
  - **What it tests**: scrape_and_check_chain_task (PSC + dispatcher + mubeng + callback)
  - **Timing**: PSC ~3min, chunks ~16min, total ~20min for 5000 proxies

### Phase 3: Stress Tests
- [x] Test 3.1: Run `bash tests/stress/run_all_stress_tests.sh` - PASSED
- [ ] Test 3.2: Concurrent task handling

### Reference Implementations
- [automation_AutoBiz.md](../../archive/extraction/automation/automation_AutoBiz.md) - Celery chord patterns
- [proxies_AutoBiz.md](../../archive/extraction/proxies/proxies_AutoBiz.md) - Mubeng integration

---

## Testing (P1)

- [ ] Test full proxy refresh + quality detection flow
- [ ] Test imot.bg scraper with real listings
- [ ] Debug/refine extraction logic

---

## Page Change Detection (P2)

**Spec**: [111_PAGE_CHANGE_DETECTION.md](../specs/111_PAGE_CHANGE_DETECTION.md)
**Research**: [page_change_detection.md](../../archive/research/page_change_detection.md) *(archived)*

**Problem**: Every scrape re-processes all listings, even if unchanged. Wastes bandwidth/CPU/proxies.

### Phase 1: Basic Hash Detection ✅
- [x] Add DB columns via migration (content_hash, last_change_at, change_count, price_history, consecutive_unchanged)
- [x] Create `data/change_detector.py` (compute_hash, has_changed, track_price_change)
- [x] Integrate into `main.py` scraping loop (`_check_and_save_listing()`)
- [x] Test: 24 unit tests pass (`tests/test_change_detector.py`)

### Phase 2: Price Tracking ✅
- [x] Implement `track_price_change()` with history (JSON array, 10 entries max)
- [x] Log price changes (logger.info for drops/increases)
- [x] Price history stored in `price_history` column

### Phase 3: Dashboard Integration (Optional) ✅
- [x] Show price history chart in Streamlit
- [x] Filter by "recently changed"

---

## Ollama Integration (P1)

**Spec**: [107_OLLAMA_INTEGRATION.md](../specs/107_OLLAMA_INTEGRATION.md)
**Reference**: ZohoCentral `/home/wow/Documents/ZohoCentral/autobiz/tools/ai/`
**Pattern**: Same as `proxies/proxies_main.py` (facade with 4 files)

**Use Cases**:
1. Page content → DB field mapping
2. Description text → structured data extraction

### Phase 1: Foundation + Health Check
- [x] Update manifest.json and FILE_STRUCTURE.md for `llm/` folder
- [x] Create `llm/` with 4 files (\_\_init\_\_.py, llm_main.py, prompts.py, schemas.py)
- [x] Create `config/ollama.yaml`
- [x] Implement OllamaClient in llm_main.py (check_health, kill_port, start_server, ensure_ready)
- [x] Test: Ollama start/stop/restart
- [x] Pull model: `ollama pull qwen2.5:1.5b` (already installed)

### Phase 2: API + Field Mapping
- [x] Implement `_call_ollama()` REST API
- [x] Implement `_parse_response()` JSON extraction
- [x] Add FIELD_MAPPING_PROMPT to prompts.py
- [x] Add MappedFields to schemas.py
- [x] Implement `map_fields()` public function
- [x] Test: Map 5 imot.bg pages - **100% extraction** (price, area, floor, construction)

### Phase 3: Description Extraction
- [x] Add EXTRACTION_PROMPT to prompts.py
- [x] Add ExtractedDescription to schemas.py
- [x] Implement `extract_description()` public function
- [x] Test: Extract from 5 descriptions - **78% extraction** (7/9 fields avg)

### Phase 3.5: Prompt Accuracy Improvements

**Spec**: [108_OLLAMA_PROMPT_IMPROVEMENTS.md](../specs/108_OLLAMA_PROMPT_IMPROVEMENTS.md)
**Research**: [ollama_language_behavior.md](../research/ollama_language_behavior.md)

**Problem**: Bulgarian prompts → 40% accuracy. English prompts → 100% accuracy.

#### Research (Complete)
- [x] Investigate why model returns Bulgarian despite English prompt constraints
- [x] Research Ollama's `format: json` behavior (only syntax, not values)
- [x] Test prompt language impact (English prompts = 5/5, Bulgarian = 2/5)
- [x] Create test script: `tests/llm/test_ollama_prompts.py`

#### Implementation Tasks (Complete - Session 7)
- [x] Phase 1: Switch prompts to English with "RESPOND IN ENGLISH ONLY"
  - Modified `llm/prompts.py`: FIELD_MAPPING_PROMPT, EXTRACTION_PROMPT
- [x] Phase 2: Add JSON schema enforcement
  - Modified `llm/llm_main.py`: Uses `schema_class.model_json_schema()` in format
- [x] Phase 3: Configure OLLAMA_KEEP_ALIVE for batch processing
  - Added `keep_alive: 1h` to `config/ollama.yaml`
  - Modified `llm/llm_main.py`: Passes keep_alive to API
- [x] Run test suite: **100% accuracy** on enum fields (V4 pattern)
- [x] Keep `_translate_values()` as safety fallback (unchanged)

### Phase 3.6: Achieve 95%+ Extraction Accuracy (P1)

**Spec**: [110_DYNAMIC_BULGARIAN_DICTIONARY.md](../specs/110_DYNAMIC_BULGARIAN_DICTIONARY.md)
**Research**: [extraction_accuracy_analysis.md](../research/extraction_accuracy_analysis.md)

**Problem**: Current 69% accuracy - missing Bulgarian hints for many fields.
**Target**: 95%+ accuracy.
**Finding**: Model size is NOT the problem (3b worse than 1.5b). Solution is dynamic dictionary.
**Result**: 97.4% accuracy achieved (Session 9, 2025-12-26)

#### Research (Complete - 2025-12-26)
- [x] Analyze extraction failures - which fields fail most?
  - bathrooms: 0%, has_elevator: 0%, heating_type: 33%, orientation: 75%
- [x] Test with larger model (qwen2.5:3b vs 1.5b)
  - Result: 1.5b (61%) > 3b (30%) - smaller is better
- [x] Identify root cause: Missing Bulgarian hints for low-accuracy fields
- [x] Design solution: Dynamic dictionary with regex pre-scan

#### Phase 1: Dynamic Dictionary (Target: 85-95%) - COMPLETE
- [x] Create `config/bulgarian_dictionary.yaml` (600+ lines, 400+ terms)
- [x] Create `llm/dictionary.py` (scanner + hint builder)
- [x] Update `llm/prompts.py` with base templates + `{hints}` placeholder
- [x] Update `llm/llm_main.py` to use dictionary via `scan_and_build_hints()`
- [x] Create `tests/llm/test_extraction_accuracy.py`
- [x] Run accuracy test - **97.4% achieved** (exceeds 95% target)
  - Fixed: `heating` → `heating_type` field name mismatch
  - Fixed: Single-letter false positives (И, Ю, С, З)
  - Fixed: `парк` matching in `паркомясто`
  - Remaining: `has_elevator` (0%) - LLM ignores hint (Phase 2 candidate)

#### Phase 2: Few-Shot Examples - SKIPPED
- [x] Tested few-shot examples for boolean fields
- **Result**: Caused regressions (heating_type, orientation dropped to 67-75%)
- **Reason**: Examples made model too conservative, returned null for working fields
- **Decision**: Skip - 97.4% already exceeds 95% target, remaining options in Phase 3-5

#### Phase 3: Temperature = 0 (Quick Win) - NO EFFECT
- [x] Change description_extraction temperature: 0.1 → 0.0
- [x] Re-run accuracy test
- **Result**: No change (97.4% → 97.4%). Temperature had no effect on `has_elevator` issue.

#### Phase 4: Hybrid CSS/LLM (If < 95%)
- [ ] Extract structured fields with Scrapling CSS selectors
- [ ] Use LLM only for free-text description
- [ ] Re-run accuracy test

#### Phase 5: Field-Specific Prompts (If < 98%)
- [ ] Create focused prompts for problematic fields
- [ ] Implement confidence-based retry

#### Acceptance Criteria
- [x] Overall accuracy ≥ 95% (target 99%) - **97.4% achieved**
- [ ] No field below 80% accuracy - has_elevator at 0% (1 sample)
- [x] All existing tests pass
- [x] Unknown words logged for future updates (via `log_unknown()`)

#### Scrapling + LLM Synergy (Future)
- [ ] Research element-aware prompts vs raw text prompts
- [ ] Implement hybrid extraction: Scrapling CSS → LLM fallback

### Phase 4: Scrapling Integration - COMPLETE (Session 17)
- [x] Add `use_llm` flag to ScraplingMixin (`websites/scrapling_base.py:216`)
- [x] Add LLM calls in extraction flow (`websites/imot_bg/imot_scraper.py:92-118`)
- [x] CSS primary, LLM fills gaps when confidence ≥ 0.7
- [x] Test: End-to-end extraction verified (orientation filled by LLM)

### Phase 5: Production Hardening
- [x] Add extraction cache (`llm/llm_main.py:340-382`, Redis-based, 7-day TTL)
- [x] Add confidence threshold to config (`config/ollama.yaml:11`)
- [x] Add metrics logging (`llm/llm_main.py:36-45, 413-441`)
- [x] Performance test (`tests/llm/test_performance.py` - 100% success, 0.95 confidence)

---

## Crawler Validation & Enhancement (P1)

**Spec**: [106_CRAWLER_VALIDATION_PLAN.md](../specs/106_CRAWLER_VALIDATION_PLAN.md)

### Phase 0: Scrapling Integration (Complete)
- [x] Install Scrapling and verify setup (v0.2.99)
- [x] Create `websites/scrapling_base.py` adapter
- [x] Test with imot.bg (price: 170400 EUR, area: 71 sqm, floor: 4/6)
- [x] Migrate imot_scraper.py to Scrapling (2025-12-25, 17 tests pass)
- [x] Migrate bazar_scraper.py to Scrapling (2025-12-25)
- [x] Enable adaptive mode with baseline selectors (2025-12-25)
- [x] Test StealthyFetcher with mubeng proxy (2025-12-25)

### Phase 1: Scraper Validation
- [ ] Create test harness (`tests/scrapers/`)
- [ ] Validate imot.bg scraper (pagination, extraction, save)
- [ ] Validate bazar.bg scraper (pagination, extraction, save)
- [ ] Create validation matrix (document what works)

### Phase 2: Description Extraction
- [x] Build `DescriptionExtractor` class (regex patterns)
  - **Note**: Implemented via LLM instead of regex. See `llm/llm_main.py:extract_description()`
- [x] Test extraction accuracy (target: >70%)
  - **Note**: 97.4% accuracy achieved via LLM. See `tests/llm/test_extraction_accuracy.py`
- [x] Optional: Add LLM fallback for complex descriptions
  - **Note**: LLM is now PRIMARY method, not fallback. CSS extracts first, LLM fills gaps.

### Phase 3: Change Detection & History
- [ ] Create `scrape_history` table
- [ ] Create `listing_changes` table (track ALL field changes)
- [x] Build `ChangeDetector` class
  - **Note**: Implemented as `data/change_detector.py` with `compute_hash()`, `has_changed()`, `track_price_change()`
- [x] Integrate into scraper flow
  - **Note**: Done in `main.py:_check_and_save_listing()`. Unchanged listings skipped.
- [x] Add dashboard timeline view
  - **Note**: Price history chart + "recently changed" filter in Streamlit dashboard

### Phase 3.5: Cross-Site Duplicate Detection & Merging
- [ ] Create `listing_sources` table (track which sites list property)
- [ ] Build `PropertyFingerprinter` class (identify duplicates)
- [ ] Build `PropertyMerger` class (smart data merging)
- [ ] Track price discrepancies across sites
- [ ] Add cross-site comparison view to dashboard

### Phase 4: Rate Limiting & Orchestration
- [ ] Define rate limit config per site
- [ ] Build Redis-backed `SiteRateLimiter`
- [ ] Build async orchestrator (parallel sites)
- [ ] Integrate with Celery

### Phase 5: Full Pipeline
- [ ] E2E testing (full pipeline)
- [ ] Add monitoring/alerting

---

## Features (P2)

- [ ] Improve floor extraction in bazar.bg scraper
- [ ] Populate dashboard with scraped data

---

## Completed

### Scraper Development
- [x] Set up scraper project structure
- [x] Simplify architecture (EUR only, BG only, no filtering)
- [x] Create database schema for listings
- [x] Build scoring system (7 weighted criteria + deal breakers)
- [x] Build Streamlit dashboard
- [x] Implement imot.bg scraper (extraction + pagination)
- [x] Implement bazar.bg scraper (tested with live data)
- [x] Create orchestrator.py - Redis/Celery/proxy lifecycle
- [x] Create proxy_validator.py - pre-flight check
- [x] Create anonymity_checker.py
- [x] Create runtime proxy scorer
- [x] Create quality checker
- [x] Integrate quality check into Celery pipeline

### Research
- [x] Map Sofia districts and neighborhoods
- [x] Understand public transport (metro lines)
- [x] Identify "up and coming" areas
- [x] Learn typical price ranges per neighborhood
- [x] Track metro expansion plans
- [x] List top real estate agencies (6 in DB)

### Project Setup (2025-12-24)
- [x] Clean root directory, organize files
- [x] Create README.md and .gitignore
- [x] Create multi-instance coordination system
- [x] Create research → specs → code workflow
- [x] Create /lss and /ess commands

### Session 3 (2025-12-24)
- [x] Run stress tests - Test 5 PASSED (no orphan mubeng)
- [x] Verify proxy-level real IP protection
- [x] Implement browser-level proxy enforcement
- [x] Create debugging workflow for Celery/Mubeng/PSC
- [x] Organize docs into workflow structure (specs/, archive/docs/)

### Architecture Documentation (2025-12-24)
- [x] Document project architecture (docs/architecture/ARCHITECTURE.md)
  - Layered Architecture with Pipeline Processing pattern
  - 8 design patterns documented (Strategy, Template Method, Factory, etc.)
  - Project structure with 769-line comprehensive guide
  - Adding new components guide (scrapers, browsers, proxies)
  - Conventions and coding patterns
  - Known gaps and future improvements identified

### File Structure Rules (2025-12-25)
- [x] Create file placement rules (docs/architecture/FILE_STRUCTURE.md)
  - Decision tree for where files go
  - Allowed root files list
  - Directory structure with purposes
  - File type → location mapping
  - Forbidden patterns at root
- [x] Update CLAUDE.md with FILE PLACEMENT RULES section
- [x] Clean up misplaced files (moved stress_test_results.md to tests/stress/)

### Automated File Placement Enforcement (2025-12-25)
- [x] Implement manifest.json with file rules (`admin/config/project_structure_manifest.json`)
  - Allowed root files whitelist
  - Forbidden patterns at root
  - Directory-specific rules (extensions, subdirs)
  - File type routing suggestions
- [x] Create validation script (`admin/scripts/hooks/validate_file_placement.py`)
  - Blocks wrong file placements with helpful error messages
  - Suggests correct locations based on file type
  - Warns on implicit directory creation
- [x] Create hook wrapper (`admin/scripts/hooks/pre_write_validate.sh`)
  - Integrates with Claude Code hooks
  - Validates Write/Edit operations before execution
- [x] Configure Claude Code hooks (`.claude/settings.json`)
  - PreToolUse hook for Write|Edit operations
  - Deny dangerous commands (rm -rf, sudo, force push)
- [x] Add max_depth (3) and block_root_files rules to manifest
  - Blocks files directly in docs/ (must use subdirs)
  - Blocks paths deeper than 3 directories
- [x] Split ARCHITECTURE.md into focused documents
  - `ARCHITECTURE.md` - 131 lines (was 821)
  - `DESIGN_PATTERNS.md` - 187 lines
  - `DATA_FLOW.md` - 190 lines
  - `ADDING_COMPONENTS.md` - 168 lines
  - `CONVENTIONS.md` - 125 lines
- [x] Initialize git repository
  - Enhanced .gitignore (secrets, db, logs, proxies)
  - Initial commit: 253 files
  - Branch: main
