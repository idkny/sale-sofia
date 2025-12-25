# Spec 107: Redis Progress Tracking for Chunk Processing

**Created**: 2025-12-25
**Status**: APPROVED - Ready for implementation
**Priority**: P1 - Fixes critical timing bug (spec 105)
**Implements**: Permanent solution for chunk processing timing

---

## 1. Problem Statement

The current implementation has a timing bug where callers cannot reliably know when chunk processing is complete:

```
Chain task returns SUCCESS → But chunks still processing (10-20 min)
Dispatcher returns immediately → "Dispatched 29 chunks" (0.1s)
Actual completion → When process_check_results_task runs (10-20 min later)
```

**Result**: Code waiting on task_id gets SUCCESS prematurely.

---

## 2. Solution: Redis Progress Tracking

Use Redis counters to track chunk processing progress in real-time.

### Redis Keys

| Key | Type | Purpose |
|-----|------|---------|
| `proxy_refresh:{job_id}:total_chunks` | STRING | Total chunks dispatched |
| `proxy_refresh:{job_id}:completed_chunks` | STRING | Chunks completed (incr by each worker) |
| `proxy_refresh:{job_id}:status` | STRING | Job status: DISPATCHED, PROCESSING, COMPLETE, FAILED |
| `proxy_refresh:{job_id}:started_at` | STRING | Unix timestamp when job started |
| `proxy_refresh:{job_id}:completed_at` | STRING | Unix timestamp when job completed |

**Key TTL**: 1 hour (auto-cleanup)

### Job ID

Use the dispatcher task_id as job_id for correlation:
```python
job_id = self.request.id  # Celery task ID
```

---

## 3. Implementation Changes

### 3.1 tasks.py - Dispatcher (check_scraped_proxies_task)

```python
@celery_app.task(bind=True)  # Add bind=True to access self.request.id
def check_scraped_proxies_task(self, _previous_result=None):
    job_id = self.request.id
    redis_client = get_redis_client()

    # ... existing chunk split logic ...

    # Set initial progress state
    redis_client.setex(f"proxy_refresh:{job_id}:total_chunks", 3600, len(proxy_chunks))
    redis_client.setex(f"proxy_refresh:{job_id}:completed_chunks", 3600, 0)
    redis_client.setex(f"proxy_refresh:{job_id}:status", 3600, "DISPATCHED")
    redis_client.setex(f"proxy_refresh:{job_id}:started_at", 3600, int(time.time()))

    # Pass job_id to chunk tasks and callback
    parallel_tasks = group(check_proxy_chunk_task.s(chunk, job_id) for chunk in proxy_chunks)
    callback = process_check_results_task.s(job_id)
    (parallel_tasks | callback).delay()

    return {"job_id": job_id, "total_chunks": len(proxy_chunks)}
```

### 3.2 tasks.py - Chunk Worker (check_proxy_chunk_task)

```python
@celery_app.task
def check_proxy_chunk_task(proxy_chunk: List[Dict], job_id: str) -> List[Dict]:
    # ... existing processing logic ...

    # Increment completed counter at the END
    redis_client = get_redis_client()
    redis_client.incr(f"proxy_refresh:{job_id}:completed_chunks")

    return live_proxies_in_chunk
```

### 3.3 tasks.py - Callback (process_check_results_task)

```python
@celery_app.task
def process_check_results_task(results: List[List[Dict]], job_id: str):
    # ... existing aggregation logic ...

    # Mark job complete
    redis_client = get_redis_client()
    redis_client.setex(f"proxy_refresh:{job_id}:status", 3600, "COMPLETE")
    redis_client.setex(f"proxy_refresh:{job_id}:completed_at", 3600, int(time.time()))

    return f"Completed: Saved {len(all_live_proxies)} live proxies."
```

### 3.4 orchestrator.py - Progress Monitor

```python
def get_refresh_progress(self, job_id: str) -> dict:
    """Get progress of a proxy refresh job."""
    redis_client = get_redis_client()

    total = redis_client.get(f"proxy_refresh:{job_id}:total_chunks")
    completed = redis_client.get(f"proxy_refresh:{job_id}:completed_chunks")
    status = redis_client.get(f"proxy_refresh:{job_id}:status")

    return {
        "job_id": job_id,
        "total_chunks": int(total) if total else 0,
        "completed_chunks": int(completed) if completed else 0,
        "status": status.decode() if status else "UNKNOWN",
        "progress_pct": (int(completed) / int(total) * 100) if total and completed else 0,
    }

def wait_for_refresh_completion(self, job_id: str, min_count: int = 5) -> bool:
    """Wait for proxy refresh to complete using Redis progress tracking."""
    check_interval = 15

    while True:
        progress = self.get_refresh_progress(job_id)

        if progress["status"] == "COMPLETE":
            usable_count = self.get_usable_proxy_count()
            if usable_count >= min_count:
                print(f"[SUCCESS] Refresh complete! {usable_count} usable proxies")
                return True
            else:
                print(f"[WARNING] Complete but only {usable_count} usable proxies")
                return False

        elif progress["status"] == "FAILED":
            print("[ERROR] Refresh job failed")
            return False

        # Show progress
        pct = progress["progress_pct"]
        completed = progress["completed_chunks"]
        total = progress["total_chunks"]
        print(f"[PROGRESS] {completed}/{total} chunks ({pct:.0f}%)")

        time.sleep(check_interval)
```

---

## 4. Redis Client Helper

Add to `proxies/tasks.py` or create `utils/redis_client.py`:

```python
import redis
import os

_redis_client = None

def get_redis_client():
    """Get shared Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_BROKER_DB", "0")),
            decode_responses=True,
        )
    return _redis_client
```

---

## 5. Backward Compatibility

The changes are backward compatible:
- Old code can still trigger refresh without job_id tracking
- `trigger_proxy_refresh` will return job_id from dispatcher result
- File-based fallback still works if Redis tracking fails

---

## 6. Testing Plan

1. **Unit test**: Redis key creation/increment
2. **Integration test**: Full pipeline with progress monitoring
3. **Stress test**: Multiple concurrent refresh jobs

Test command:
```bash
python tests/stress/test_full_pipeline.py
```

Verify:
- Progress percentage increases monotonically
- Status transitions: DISPATCHED → PROCESSING → COMPLETE
- Keys auto-expire after 1 hour

---

## 7. Files to Modify

| File | Changes |
|------|---------|
| `proxies/tasks.py` | Add Redis progress tracking to 3 tasks |
| `orchestrator.py` | Add `get_refresh_progress()`, update `wait_for_refresh_completion()` |

---

## 8. Estimated Effort

- Implementation: 30-45 minutes
- Testing: 20-30 minutes (full pipeline takes ~20 min)
- Total: ~1 hour

---

## 9. Success Criteria

1. `get_refresh_progress()` returns accurate chunk counts
2. `wait_for_refresh_completion()` waits until ALL chunks done
3. No premature SUCCESS returns
4. Progress visible in logs: "15/50 chunks (30%)"
