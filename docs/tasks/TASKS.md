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

**Session 4 Handoff (2025-12-25)**: Phase 1 tests complete. See specs 103/104 for reference implementations and format issues to investigate.

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

**Spec**: [105_CHUNK_PROCESSING_TIMING_BUG.md](../specs/105_CHUNK_PROCESSING_TIMING_BUG.md)

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
- [ ] Review `orchestrator.py` for hardcoded timeouts
- [ ] Review `tasks.py` for any code that waits on dispatcher result
- [ ] Implement dynamic timeout: `timeout = (chunks / workers) * time_per_chunk * 1.5`
- [ ] Add progress monitoring (Redis counter or log-based)
- [ ] Test with 5,000+ proxy mock data

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
- [ ] Test 2.3: Full pipeline end-to-end

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
