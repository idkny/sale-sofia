# Orchestration Research - Context & Guidance

## Goal
We're preparing for Phase 4.3 (Celery Site Tasks) - the final orchestration phase before production. We need deep understanding of how all modules work and interact before implementing.

## What We Need
Research documents in `docs/research/` that capture:
- How each module works individually
- What each module needs from an orchestrator
- Gaps between current state and production-ready parallel scraping

## Key Context

**Architecture principle**: Modules are decoupled. Everything flows through `main.py`. Scrapers don't talk to proxies directly - they request resources from main.py.

**Important**: The project already has orchestration infrastructure. Don't assume we're starting from scratch:
- `orchestrator.py` (34KB) - already manages Redis, Celery workers, proxy refresh
- `proxies/tasks.py` - already has Celery tasks with chord pattern, Redis progress tracking

Phase 4.3 should **extend** these patterns, not reinvent them.

---

## Key Files Reference

Use this as a starting point, but explore beyond these:

| Area | Key Files |
|------|-----------|
| Orchestration | `orchestrator.py`, `main.py` |
| Scraping | `websites/` (NOT `scrapers/`), `scraping/async_fetcher.py` |
| Proxies | `proxies/` (especially `tasks.py` for Celery patterns) |
| Resilience | `resilience/` (circuit breaker, rate limiter, checkpoint) |
| Data | `data/` (data_store_main.py, db_retry.py) |
| Config | `config/` (scraping_defaults.yaml, sites/*.yaml, settings.py, start_urls.yaml) |
| LLM | `llm/` (extraction per listing) |

**Note**: There is NO `scrapers/` or `browsers/` directory. Browser handling is via Scrapling library in `websites/scrapling_base.py`.

---

## Suggested Approach

### Phase 1: Module Investigation
Launch parallel agents to explore each area. Let each agent:
- Read the relevant files
- Understand how the module works
- Identify what an orchestrator needs to know
- Document findings in `docs/research/orchestration_<module>.md`

Suggested areas (adapt as needed):
1. Scraping & Fetching (`websites/`, `scraping/`)
2. Existing Orchestrator (`orchestrator.py` - understand what exists)
3. Proxy Module (`proxies/` - learn from existing Celery patterns)
4. Resilience Module (`resilience/`)
5. Data Module (`data/`)
6. Celery & Main Flow (`celery_app.py`, `main.py`)
7. LLM Module (`llm/`)

### Phase 2: Configuration Analysis
After understanding modules, synthesize the configuration landscape:
- What rules exist?
- What rules are missing?
- What must the orchestrator enforce?

### Phase 3: Synthesis
Bring all findings together:
- Module dependencies and initialization order
- Gap analysis vs current Phase 4.3/4.4 design in `docs/tasks/TASKS.md`
- Recommendations for implementation

---

## Output

Research documents in `docs/research/`:
- One per module investigated
- One synthesis document

Format and structure are up to the agent - capture what's important.

---

## Questions to Keep in Mind

These might be useful, but don't treat as a checklist:

- What does each module need to start? To stop? To recover from crash?
- Where are the boundaries between modules?
- What existing patterns (in orchestrator.py, proxies/tasks.py) can we reuse?
- What's missing for parallel site scraping?
- How do resilience features (circuit breaker, rate limiter, checkpoint) affect orchestration?
- How does LLM extraction fit into the flow?

---

## Reference

- Current task design: `docs/tasks/TASKS.md` (Phase 4.3, 4.4)
- Existing Celery patterns: `proxies/tasks.py` (chord, group, Redis tracking)
- Existing orchestrator: `orchestrator.py` (context manager, health checks, cleanup)
