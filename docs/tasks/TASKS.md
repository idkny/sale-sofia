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

#### Vocabulary Approach (Deferred - English prompts work better)
- [ ] Create `llm/vocabulary.py` if needed after Phase 1-2

#### Scrapling + LLM Synergy (Future)
- [ ] Research element-aware prompts vs raw text prompts
- [ ] Implement hybrid extraction: Scrapling CSS → LLM fallback

### Phase 4: Scrapling Integration
- [ ] Add `use_llm` flag to ScraplingMixin
- [ ] Add LLM calls in extraction flow
- [ ] Add CSS selector fallback when confidence < 0.7
- [ ] Test: End-to-end scrape → LLM → save to DB

### Phase 5: Production Hardening
- [ ] Add extraction cache
- [ ] Add confidence threshold to config
- [ ] Add metrics logging
- [ ] Performance test: 100 listings batch

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
- [ ] Build `DescriptionExtractor` class (regex patterns)
- [ ] Test extraction accuracy (target: >70%)
- [ ] Optional: Add LLM fallback for complex descriptions

### Phase 3: Change Detection & History
- [ ] Create `scrape_history` table
- [ ] Create `listing_changes` table (track ALL field changes)
- [ ] Build `ChangeDetector` class
- [ ] Integrate into scraper flow
- [ ] Add dashboard timeline view

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
- [ ] Implement homes.bg scraper
- [ ] E2E testing (full pipeline)
- [ ] Add monitoring/alerting

---

## Features (P2)

- [ ] Implement homes.bg scraper
- [ ] Improve floor extraction in bazar.bg scraper
- [ ] Populate dashboard with scraped data

---

## Research (P3)

- [ ] Deep dive: Hadji Dimitar (street-level)
- [ ] Deep dive: Krastova Vada (street-level)
- [ ] Deep dive: Ovcha Kupel (street-level)
- [ ] Contact agencies and get quotes

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
