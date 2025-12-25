# Proxy System Implementation Tasks

> Status: PHASE 1 COMPLETE - Runtime scoring, quality checks, pipeline integration done
> Specs: `docs/PROXY_SYSTEM_SPECS.md`
> Last Updated: 2025-12-23 (Session 11)

---

## Investigation Tasks

### Completed

- [x] Read extraction/proxies/proxies_Scraper.md
- [x] Read extraction/proxies/proxies_AutoBiz.md
- [x] Read extraction/proxies/proxies_CompetitorIntel.md
- [x] Clone and analyze idkny/Scraper repo
- [x] Clone and analyze idkny/Auto-Biz repo
- [x] Clone and analyze idkny/Competitor-Intel repo
- [x] Create comparison matrix
- [x] Document recommended architecture
- [x] **ORCHESTRATION: Map how tools work together in each repo**
- [x] **ORCHESTRATION: Document data flow between tools**
- [x] **ORCHESTRATION: Analyze timing and wait mechanisms**
- [x] **ORCHESTRATION: Identify gaps in sale-sofia**

### Key Orchestration Findings

| Repo | Pattern | Strength | Weakness |
|------|---------|----------|----------|
| Scraper | Sequential + sleep(10) | Simple | No completion detection |
| AutoBiz | Empty (skeleton) | N/A | Not implemented |
| Competitor-Intel | asyncio.gather + scoring | Parallel + adaptive | No persistence |
| sale-sofia | Celery + file mtime | Task queue | Fragile sync |

### Pending Investigation

- [ ] Review mubeng documentation for advanced features
- [ ] Test current proxy-scraper-checker output format
- [ ] Profile actual timing of each stage

---

## Bug Fixes (Completed This Session)

- [x] Fix pre-flight check scoring rotator URL (was tracking localhost:8089)
- [x] Fix wait_for_proxies not waiting for refresh completion
- [x] Add wait_for_refresh_completion() method with mtime tracking
- [x] Clean up proxy_scores.json (remove bogus localhost entry)
- [x] Update /ltst skill with correct paths and venv activation

---

## Implementation Tasks (Future)

### Phase 0: Orchestration Fixes (COMPLETED 2025-12-23)

> These fix the gaps identified in orchestration investigation

#### 0.1 Fix Fire-and-Forget Auto-Trigger ✅
- [x] Removed `auto_check` param and `.delay()` from `scrape_new_proxies_task`
- [x] Added `scrape_and_check_chain_task` for proper chaining
- [x] Both tasks now accept `_previous_result` param for chain compatibility

#### 0.2 Fix Beat Schedule Conflicts ✅
- [x] Removed `check-proxies-every-2h` from beat schedule
- [x] Beat now uses `scrape_and_check_chain_task` which chains properly
- [ ] Test: Run for 24h, verify no stale data issues

#### 0.3 Add Task Result Validation ✅
- [x] `trigger_proxy_refresh()` now returns `(mtime, task_id)` tuple
- [x] Added `get_task_state()` method to query Celery task state
- [x] `wait_for_refresh_completion()` now checks task state (SUCCESS/FAILURE)
- [x] Early exit on task FAILURE with error message

#### 0.4 Add Progress Reporting ✅
- [x] Added `self.update_state()` in `check_proxy_chunk_task`
- [x] Reports CHECKING state during liveness check
- [x] Reports ANONYMITY state during anonymity check with progress
- [ ] UI display not yet implemented (low priority)

#### 0.5 Improve Mubeng Recovery ✅
- [x] Level 1: 6 pre-flight attempts (mubeng auto-rotates via --rotate-on-error)
- [x] Level 2: Soft restart mubeng with same proxy file (~30 sec)
- [x] Level 3: Full refresh only as last resort (5-10 min)
- [x] Recovery time reduced from 10 min to ~30 sec for soft restart

---

### Phase 1: Core Improvements (COMPLETED 2025-12-23)

#### 1.1 Runtime Proxy Scorer ✅
- [x] Create `proxies/proxy_scorer.py`
- [x] Implement weighted random selection (`ScoredProxyPool.select_proxy()`)
- [x] Implement score update (success *= 1.1, failure *= 0.5)
- [x] Implement auto-pruning (failures >= 3 OR score < 0.01)
- [x] Add score persistence to JSON file (`proxy_scores.json`)
- [x] Add score loading on startup (`load_scores()`)
- [x] Thread-safe implementation with locks
- [x] Integrated into `main.py` with session-level tracking
- [ ] Write unit tests (deferred)

#### 1.2 Enhanced Anonymity Checker ✅
- [x] Update `proxies/anonymity_checker.py`
- [x] Add full header inspection (all PRIVACY_HEADERS)
- [x] Add multiple judge URL support with fallback (5 URLs)
- [x] Cache real IP to avoid repeated lookups (`_real_ip_cache`)
- [x] Add `anonymity_verified_at` timestamp
- [x] Already integrated into `tasks.py` pipeline
- [ ] Write unit tests (deferred)

#### 1.3 Quality Checker ✅
- [x] Create `proxies/quality_checker.py`
- [x] Implement Google check (detect captcha via indicators)
- [x] Implement target site check (imot.bg with content validation)
- [x] Add `google_passed` / `target_passed` flags
- [x] Add `quality_checked_at` timestamp
- [x] Integrated into `tasks.py` pipeline (QUALITY stage)
- [ ] Write unit tests (deferred)

### Phase 2: Celery Task Improvements (PARTIALLY COMPLETED)

#### 2.1 Multi-Stage Pipeline ✅
- [x] Update `proxies/tasks.py` for 4-stage pipeline
- [x] Stage 1: Scraping (existing)
- [x] Stage 2: Mubeng liveness (existing)
- [x] Stage 3: Anonymity verification ✅
- [x] Stage 4: Quality check ✅
- [x] Progress states: CHECKING → ANONYMITY → QUALITY
- [x] Update chord/chain structure (group + callback)

#### 2.2 Task Monitoring (PARTIAL)
- [x] Add task progress tracking (`self.update_state()`)
- [x] Add completion callbacks (`process_check_results_task`)
- [ ] Implement proper error handling per stage
- [ ] Add retry logic for transient failures

### Phase 3: Configuration & Observability

#### 3.1 Configuration
- [ ] Create `proxies/config.py` with all thresholds
- [ ] Move hardcoded values to config
- [ ] Support environment variable overrides
- [ ] Document all config options

#### 3.2 Logging & Metrics
- [ ] Add structured logging throughout
- [ ] Track proxy pool health metrics
- [ ] Track success/failure rates per proxy
- [ ] Add alerts for low proxy count

### Phase 4: Integration (PARTIALLY COMPLETED)

#### 4.1 Main Pipeline Integration ✅
- [x] Integrate `ScoredProxyPool` into `main.py`
- [x] Initialize pool after proxies are available
- [x] Track success/failure per scraping attempt
- [x] Reload pool after proxy refresh
- [x] Save scores on session end
- [x] Display session statistics (scraped, failed, success rate)
- [ ] Add fallback to paid proxies on failure
- [ ] Test full flow end-to-end

#### 4.2 Browser Integration
- [ ] Pass scoring info to browser
- [ ] Record success/failure from browser requests
- [ ] Implement automatic proxy rotation on error

**Note:** Mubeng hides which proxy is used, so scoring currently tracks
session-level success/failure via the mubeng endpoint. Future improvement:
replace mubeng with direct `ScoredProxyPool.select_proxy()` for true per-proxy scoring.

---

## Open Questions to Resolve

- [ ] Decide: Redis vs JSON for score persistence
- [ ] Decide: Integrate scoring into mubeng or separate
- [ ] Decide: Frequency of anonymity re-verification
- [ ] Decide: Test against imot.bg or just Google
- [ ] Decide: Should paid proxies have scoring

---

## Dependencies

### External Tools (Already Have)
- mubeng v0.22.0
- proxy-scraper-checker (Rust binary)

### Python Packages (Already Have)
- celery
- redis
- requests
- httpx (may need to add for async)

### May Need to Add
- aiohttp (for async validation)
- pycurl (for low-level validation like Scraper)

---

## Notes

### Session 10 Progress (2025-12-23)
- Fixed pre-flight check scoring bug
- Fixed wait_for_proxies not waiting for refresh
- Investigated 3 repos (Scraper, AutoBiz, Competitor-Intel)
- Created specs document with recommended architecture
- Investigation still in progress

### Key Findings
1. **Scraper** has best anonymity detection (header inspection)
2. **AutoBiz** has best Celery patterns (multi-stage chord)
3. **Competitor-Intel** has best runtime scoring (weighted selection + auto-prune)
4. All 3 are missing proper wait-for-refresh logic (we fixed this)

### Recommended Priority
1. First: Make current system work (proxy quality issue)
2. Second: Add runtime scoring from Competitor-Intel
3. Third: Add quality checks from AutoBiz
4. Fourth: Improve anonymity detection from Scraper
