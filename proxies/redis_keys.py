"""Redis key constants for proxy refresh operations.

Centralizes all Redis key patterns used for job progress tracking.
All keys follow the pattern: proxy_refresh:{job_id}:{suffix}
"""

# Key prefix
PREFIX = "proxy_refresh"


def job_total_chunks_key(job_id: str) -> str:
    """Key for total chunks in a job."""
    return f"{PREFIX}:{job_id}:total_chunks"


def job_completed_chunks_key(job_id: str) -> str:
    """Key for completed chunks counter."""
    return f"{PREFIX}:{job_id}:completed_chunks"


def job_status_key(job_id: str) -> str:
    """Key for job status (DISPATCHED, PROCESSING, COMPLETE, FAILED)."""
    return f"{PREFIX}:{job_id}:status"


def job_started_at_key(job_id: str) -> str:
    """Key for job start timestamp (Unix epoch)."""
    return f"{PREFIX}:{job_id}:started_at"


def job_completed_at_key(job_id: str) -> str:
    """Key for job completion timestamp (Unix epoch)."""
    return f"{PREFIX}:{job_id}:completed_at"


def job_result_count_key(job_id: str) -> str:
    """Key for final proxy result count."""
    return f"{PREFIX}:{job_id}:result_count"
