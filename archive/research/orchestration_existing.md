# Orchestration Research: Existing Orchestrator

## Executive Summary

The current `orchestrator.py` (854 lines) is a **unified orchestrator** for managing Redis/Celery/Proxy infrastructure. It's designed as a **context manager** with built-in health checks, error recovery, and multi-stage job tracking. Phase 4.3 should **extend patterns, not replace them**.

---

## 1. What Orchestrator.py Already Manages

### A. Redis Management
- **Health checks**: `_health_check_redis()` using Redis PING
- **Startup logic**: Detects already-running instances
- **Error handling**: Connection errors, timeouts
- **Recovery**: 10 attempts, 0.5s sleep between

### B. Celery Worker Management
- **Health checks**: `_health_check_celery()` using celery_app.control.inspect().ping()
- **Startup**: Spawns worker with beat scheduler (concurrency=8)
- **Logging**: Writes to `data/logs/celery_worker.log`
- **Process reuse**: Won't start duplicates
- **Recovery**: `restart_celery_if_dead()` watches for crashes

### C. Proxy Refresh Management
- **Trigger logic**: `trigger_proxy_refresh()` sends chain to Celery
- **Progress tracking**: Redis keys for job_id, total_chunks, status
- **Counting**: `get_proxy_count()` and `get_usable_proxy_count()`
- **Thresholds**: Uses `MIN_PROXIES_FOR_SCRAPING` (default: 10)

### D. Process Cleanup
- **Stale process killing**: `cleanup_stale_processes()`
- **Graceful shutdown**: `stop_all()` terminates Celery → Redis
- **Signal handlers**: SIGINT/SIGTERM for Ctrl+C

---

## 2. Structural Patterns (Context Manager)

```python
with Orchestrator() as orch:           # __enter__: cleanup + register handlers
    orch.start_redis()                 # Idempotent
    orch.start_celery()                # Idempotent
    orch.wait_for_proxies()            # Blocking wait
    # ... do scraping ...
# __exit__: stop_all() guaranteed
```

**Key characteristics**:
- **Idempotent startup**: Checks if running before starting
- **Guaranteed cleanup**: Context manager ensures stop_all() runs
- **Health-before-action**: Always check health first
- **Lazy client**: `_redis_client` cached on first use

---

## 3. Existing Health Checks

| Component | Check Method | Timeout | Recovery |
|-----------|--------------|---------|----------|
| Redis | PING command | 2s | 10 retries × 0.5s |
| Celery | inspect().ping() | 5s | Reuse or start new |
| Process | poll() is None | N/A | Auto-restart |
| Proxy count | JSON file count | N/A | Trigger refresh |

---

## 4. Cleanup & Shutdown Logic

```python
def stop_all(self):
    # 1. Stop Celery first (depends on Redis)
    # 2. Close Celery log handle
    # 3. Stop Redis
    # 4. Signal handlers + atexit registered
```

**Order matters**: Dependent services first (Celery before Redis)

---

## 5. Error & Recovery Patterns

### Health-Check-Before-Action
```python
if self._health_check_redis():
    return True  # Already good
else:
    # Start new instance
```

### Process Monitoring with Auto-Restart
```python
def restart_celery_if_dead(self) -> bool:
    if self.is_celery_alive():
        return True
    logger.warning("Celery worker died! Restarting...")
    return self.start_celery()
```

### Graceful Degradation
```python
if dispatch.chord_id:
    result = self._wait_via_chord(...)  # Preferred
    if result is not None:
        return result
return self._wait_via_redis_polling(...)  # Fallback
```

### Dynamic Timeouts
```python
if total_chunks > 0:
    rounds = (total_chunks + workers - 1) // workers
    timeout_val = int(rounds * time_per_chunk * buffer)
else:
    timeout_val = 1800  # 30 min default
```

---

## 6. Multi-Stage Job Tracking (Proxy Refresh Pattern)

### Stage 1: Chain Dispatch
- Waits for Celery task to complete
- Extracts `job_id` and `chord_id` from result
- Handles PENDING → STARTED → SUCCESS

### Stage 2: Chord-Based Wait
- Uses `AsyncResult(chord_id).get(timeout=X)`
- Event-based (preferred): signals when all workers complete
- Returns 3 states: True (success), False (not enough), None (timeout)

### Stage 3: Redis Progress Polling
- Fallback if chord times out
- Polls `job_status_key(job_id)` every 15 seconds
- Tracks: DISPATCHED, PROCESSING, COMPLETE, FAILED

### Stage 4: File Monitoring
- Last resort if job_id unavailable
- Watches `live_proxies.json` mtime

---

## 7. Redis Key Namespace

**Pattern** (from proxies/redis_keys.py):
```
proxy_refresh:{job_id}:total_chunks
proxy_refresh:{job_id}:completed_chunks
proxy_refresh:{job_id}:status
proxy_refresh:{job_id}:started_at
proxy_refresh:{job_id}:completed_at
proxy_refresh:{job_id}:result_count
```

All progress keys namespaced by `job_id`. Allows multiple concurrent jobs.

---

## 8. What's Missing for Parallel Site Scraping

| Gap | Current | Needed |
|-----|---------|--------|
| Per-Site Tracking | Single namespace | `scrape_{site}:{job_id}` |
| Site Concurrency | Single refresh chain | Multiple concurrent site tasks |
| Site Health Checks | Global checks only | Per-site progress, error rates |
| Aggregated Progress | Single job progress | Dashboard across all sites |
| Dependency Management | Wait for proxies → scrape | Inter-site dependencies |
| Resource Limits | Fixed concurrency=8 | Per-site limits, memory checks |

---

## 9. Patterns to Reuse for Phase 4.3

| Pattern | Location | Why Reuse |
|---------|----------|-----------|
| Context Manager Lifecycle | Lines 118-128 | Guaranteed cleanup |
| Health-Before-Action | Lines 216-227 | Don't assume state |
| Process Auto-Restart | Lines 370-383 | Auto-recovery |
| Multi-Stage Fallback | Lines 524-579 | Resilient to failures |
| Dynamic Timeouts | Lines 668-682 | Realistic waits |
| Progress Thread | Lines 705-726 | Non-blocking progress |
| Signal Handlers | Lines 149-162 | Clean shutdown |
| Redis Namespacing | redis_keys.py | Concurrent jobs |

---

## 10. Recommendations for Phase 4.3 Design

### Extension Strategy (Non-Breaking)
1. **Add site registry**: `self.sites = {}` to track active sites
2. **Add site-specific tracking**: `self.site_progress[site_name]`
3. **Extend health checks**: `_health_check_site(site_name)`
4. **Add site lifecycle methods**: `start_site_scraper()`, `stop_site_scraper()`
5. **Extend shutdown pattern**: Let `stop_all()` iterate over sites
6. **Extend Redis keys**: `scrape_{site}:{job_id}:{suffix}` pattern

### Thread-Safe Considerations
- Current orchestrator is single-threaded (used in main.py)
- If adding concurrent site operations, need locks around `self.sites`
- Progress thread already uses `threading.Event` (thread-safe)

---

## Conclusion

**The existing orchestrator is well-architected for Phase 4.3 extension:**

- Clean context manager pattern (easy to extend)
- Idempotent health checks (safe to call multiple times)
- Auto-restart capability (resilient)
- Multi-stage job tracking (fallback-friendly)
- Signal handling already registered (can reuse)
- Redis key namespacing supports multiple jobs (extendable)

**Phase 4.3 should:**
1. Add per-site task tracking alongside existing proxy tracking
2. Extend progress thread to show multiple sites
3. Add site-specific health checks
4. Use same Redis key patterns for site jobs
5. Extend `stop_all()` to gracefully shut down all active sites
6. Keep existing proxy refresh logic intact (it works!)
