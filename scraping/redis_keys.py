"""Redis key patterns for scraping progress tracking."""


class ScrapingKeys:
    """Redis key builders for scraping job progress."""

    PREFIX = "scraping"

    @classmethod
    def status(cls, job_id: str) -> str:
        """Job status: DISPATCHED, PROCESSING, AGGREGATING, COMPLETE, FAILED"""
        return f"{cls.PREFIX}:{job_id}:status"

    @classmethod
    def total_chunks(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:total_chunks"

    @classmethod
    def completed_chunks(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:completed_chunks"

    @classmethod
    def total_urls(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:total_urls"

    @classmethod
    def result_count(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:result_count"

    @classmethod
    def error_count(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:error_count"

    @classmethod
    def started_at(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:started_at"

    @classmethod
    def completed_at(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:completed_at"
