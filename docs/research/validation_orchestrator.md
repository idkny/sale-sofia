# Orchestrator Validation Report

**Date**: 2025-12-28
**Scope**: Pre-Phase 4.3 validation
**Verdict**: Correct for sequential operation, needs extension for parallel

---

## Executive Summary

The orchestrator is **correctly implemented for sequential operation**. Context manager pattern, health checks, and fallback mechanisms are well-designed. One bug to fix: forward the timeout parameter. For parallel site scraping, key gaps are in-memory state sharing and lack of per-site tracking.

---

## Correctly Implemented

| Component | Location | Notes |
|-----------|----------|-------|
| Context manager | Lines 118-128 | `__enter__` initializes, `__exit__` cleans up |
| Stale process cleanup | Lines 130-147 | Kills orphan celery/mubeng on startup |
| Signal handlers | Lines 149-162 | SIGINT/SIGTERM trigger `stop_all()` |
| Idempotent startup | Lines 216-266 | Checks health before starting |
| Auto-restart | Lines 370-383 | `restart_celery_if_dead()` monitors Celery |
| Multi-stage fallback | Lines 524-579 | Chord -> Redis polling -> File monitoring |
| Dynamic timeout | Lines 668-682 | Based on chunk count and worker count |
| Progress thread | Lines 705-726 | Background progress display |

---

## BUG: Timeout Not Forwarded

**Location**: `orchestrator.py` line 522

```python
# Current (broken):
return self.wait_for_refresh_completion(mtime_before, min_count, task_id=task_id)

# Should be:
return self.wait_for_refresh_completion(mtime_before, min_count, timeout=timeout, task_id=task_id)
```

**Impact**: Redis polling fallback can loop infinitely with `timeout=0`.

---

## Gaps for Parallel Site Scraping

| Component | Current State | Needed |
|-----------|---------------|--------|
| Proxy scoring | In-memory | Redis-backed |
| Rate limiting | In-memory per-process | Redis coordination |
| Circuit breaker | In-memory per-process | Redis coordination |
| Site tracking | None | Per-site task registry |
| Checkpoint | File-based, one at a time | Distributed strategy |

---

## Recommendations

### Before Phase 4.3

**Fix timeout forwarding** (line 522 in orchestrator.py)

### For Phase 4.3

1. Add site registry: `self.active_sites: Dict[str, SiteJobInfo]`
2. Add site lifecycle methods: `start_site_scraper()`, `get_site_progress()`, `stop_site_scraper()`
3. Extend `stop_all()` to iterate over active sites
