---
id: instance_002
type: session_file
project: sale-sofia
instance: 2
created_at: 2025-12-24
updated_at: 2025-12-28
---

# Instance 2 Session

**You are Instance 2.** Work independently.

---

## IMMEDIATE NEXT SESSION TASK

**BLOCKING TASK**: Review orchestration research and write Phase 4.3 spec.

### What Happened This Session (Session 39)

1. Read `docs/research/orchestration_research_prompt.md` - guidance for Phase 4.3 research
2. Previous session had already launched research agents (8 docs in `docs/research/orchestration_*.md`)
3. This session launched **6 validation agents** to audit module correctness (not just describe how they work)
4. All 6 agents completed and findings were synthesized into 7 documents

### Documents Created This Session

| File | Content |
|------|---------|
| `docs/research/validation_scraping.md` | Scraping module ready for Celery wrapping |
| `docs/research/validation_resilience.md` | Circuit breaker/rate limiter BROKEN for distributed |
| `docs/research/validation_data.md` | SQLite race conditions, fix before 10+ workers |
| `docs/research/validation_proxies.md` | Celery patterns CORRECT, template for 4.3 |
| `docs/research/validation_orchestrator.md` | One timeout bug, needs site registry |
| `docs/research/validation_llm.md` | No rate limiting, needs semaphore |
| `docs/research/validation_synthesis.md` | **READ THIS FIRST** - consolidated findings |

### Critical Issues Found

1. **`orchestrator.py:522`** - timeout not forwarded to `wait_for_refresh_completion()`
   - Can cause infinite loop in Redis polling fallback
   - Fix: Add `timeout=timeout` parameter

2. **`data_store_main.py:1316-1320`** - module-level init race condition
   - 10 workers run `init_db()` simultaneously on import
   - Fix: Move to explicit startup script with file lock

3. **Read functions unprotected** - all `get_*` functions in data_store_main.py
   - No `@retry_on_busy()` decorator
   - Can fail during write contention

### Modules Needing Redis Backing

| Module | Current State | Problem |
|--------|---------------|---------|
| Circuit Breaker | In-memory singleton | Worker A blocks domain, Worker B doesn't know |
| Rate Limiter | In-memory singleton | 4 workers x 10 req/min = 40 req/min |
| LLM | No rate limiting | 10 workers flood Ollama |

### Next Session TODO

1. **Read `docs/research/validation_synthesis.md`** - has full implementation roadmap
2. **Review other 6 validation docs** for details
3. **Write Phase 4.3 spec** based on findings:
   - Include critical fixes as pre-requisites
   - Define scraping/tasks.py structure (copy from proxies/tasks.py)
   - Define Redis backing approach for resilience module
   - Define LLM rate limiting approach
4. **Update TASKS.md** Phase 4.3 tasks if needed
5. **Unblock other tasks** once complete

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

### 2025-12-28 (Session 39 - Orchestration Validation)

| Task | Status |
|------|--------|
| Launch 6 validation agents | Complete |
| Validate Scraping Module | Complete |
| Validate Resilience Module | Complete |
| Validate Data Module | Complete |
| Validate Proxy/Celery Patterns | Complete |
| Validate Orchestrator | Complete |
| Validate LLM Integration | Complete |
| Synthesize validation findings | Complete |

**Summary**: Launched 6 architect-review agents to validate module correctness (not just describe). Found 3 critical issues and 3 modules needing Redis backing. Created 7 validation documents. Added BLOCKING task to TASKS.md for next session.

**Files Created**:
- `docs/research/validation_scraping.md`
- `docs/research/validation_resilience.md`
- `docs/research/validation_data.md`
- `docs/research/validation_proxies.md`
- `docs/research/validation_orchestrator.md`
- `docs/research/validation_llm.md`
- `docs/research/validation_synthesis.md`

**Files Modified**:
- `docs/tasks/TASKS.md` - Added BLOCKING task for research review
- `docs/tasks/instance_002.md` - Updated for session continuity

---

### 2025-12-27 (Session 37 - Phase 4.2 Async Implementation)

| Task | Status |
|------|--------|
| Add `acquire_async()` to rate_limiter.py | Complete |
| Update scrapers to sync (remove fake async) | Complete |
| Create `scraping/async_fetcher.py` | Complete |
| Update main.py for sync consistency | Complete |
| Write 11 async fetcher tests (100% coverage) | Complete |
| Run Phase Completion Checklist | Complete |

**Summary**: Implemented Phase 4.2 Async Implementation. Fixed fake async patterns, created true async fetcher with httpx.AsyncClient for future Celery integration. 563 tests passing.

---

### 2025-12-27 (Session 34 - Phase 4.1 Scraping Configuration + Integration)

| Task | Status |
|------|--------|
| Research scraper settings (Scrapy/Colly/Crawlee) | Complete |
| Create spec 113 | Complete |
| Create `config/scraping_defaults.yaml` | Complete |
| Create `config/sites/*.yaml` per-site overrides | Complete |
| Create `config/scraping_config.py` loader | Complete |
| Write 7 unit tests (99% coverage) | Complete |
| Integrate into main.py | Complete |
| Remove old `DEFAULT_SCRAPE_DELAY` | Complete |
| Update `SCRAPER_GUIDE.md` | Complete |
| Archive spec 113 | Complete |

**Summary**: Implemented Phase 4.1 Scraping Configuration. Created 2-level config system (global defaults + per-site overrides) based on Scrapy/Colly/Crawlee best practices. Integrated into main.py, removed old settings. 37 tests passing.

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_001.md](instance_001.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
