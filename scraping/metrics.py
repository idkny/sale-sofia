"""Metrics collection for scraper monitoring and observability.

Collects request/response metrics during scrape runs for health tracking,
performance analysis, and historical comparison.

Reference: Spec 114 Section 1 (MetricsCollector)
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

# Import settings with fallback defaults
try:
    from config.settings import SCRAPER_HEALTH_THRESHOLDS
except ImportError:
    SCRAPER_HEALTH_THRESHOLDS = {
        "success_rate": {
            "healthy": 90.0,
            "degraded": 75.0,
        },
    }


class RequestStatus(Enum):
    """Status of a scrape request."""

    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    SKIPPED = "skipped"


@dataclass
class RequestMetric:
    """Metric data for a single request."""

    url: str
    domain: str
    status: RequestStatus
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RunMetrics:
    """Aggregated metrics for a complete scrape run."""

    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Counters
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    blocked: int = 0
    timeouts: int = 0
    parse_errors: int = 0
    skipped: int = 0

    # Per-domain breakdown
    domain_stats: Dict[str, Dict] = field(default_factory=dict)

    # Error breakdown
    error_counts: Dict[str, int] = field(default_factory=dict)

    # Response times (for percentile calculation)
    response_times: List[float] = field(default_factory=list)

    # Individual request metrics (optional, can be disabled for large runs)
    requests: List[RequestMetric] = field(default_factory=list)

    # Listing tracking
    listings_saved: int = 0
    listings_skipped: int = 0
    skip_reasons: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """Collects metrics during a scrape run.

    Thread-safe collector that tracks request counts, response times,
    and error breakdowns for monitoring and health assessment.
    """

    def __init__(
        self, run_id: Optional[str] = None, track_individual: bool = True
    ):
        """
        Initialize metrics collector.

        Args:
            run_id: Unique identifier for this run (auto-generated if None)
            track_individual: Whether to track individual request metrics
        """
        self._run_id = run_id or self._generate_run_id()
        self._track_individual = track_individual
        self._metrics = RunMetrics(
            run_id=self._run_id,
            start_time=datetime.now(),
        )
        self._pending_requests: Dict[str, str] = {}  # url -> domain

    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"scrape_{timestamp}_{short_uuid}"

    def start_run(self) -> None:
        """Mark the start of a scrape run."""
        self._metrics.start_time = datetime.now()

    def record_request(self, url: str, domain: str) -> None:
        """Record that a request is being made.

        Args:
            url: URL being requested
            domain: Domain of the URL
        """
        self._metrics.total_requests += 1
        self._pending_requests[url] = domain
        self._ensure_domain_stats(domain)

    def _ensure_domain_stats(self, domain: str) -> None:
        """Ensure domain_stats entry exists for domain."""
        if domain not in self._metrics.domain_stats:
            self._metrics.domain_stats[domain] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "blocked": 0,
                "timeouts": 0,
                "parse_errors": 0,
                "skipped": 0,
                "response_times": [],
            }

    def record_response(
        self,
        url: str,
        status: RequestStatus,
        response_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record the result of a request.

        Args:
            url: URL that was requested
            status: Result status of the request
            response_code: HTTP status code (if applicable)
            response_time_ms: Response time in milliseconds
            error_type: Type of error (if failed)
            error_message: Error message (if failed)
        """
        domain = self._pending_requests.pop(url, "unknown")
        self._update_counters(status)
        self._update_domain_stats(domain, status, response_time_ms)
        self._track_response_time(response_time_ms)
        self._track_error(error_type)
        self._track_individual_metric(
            url, domain, status, response_code,
            response_time_ms, error_type, error_message
        )

    def _update_counters(self, status: RequestStatus) -> None:
        """Update global counters based on status."""
        counter_map = {
            RequestStatus.SUCCESS: "successful",
            RequestStatus.FAILED: "failed",
            RequestStatus.BLOCKED: "blocked",
            RequestStatus.TIMEOUT: "timeouts",
            RequestStatus.PARSE_ERROR: "parse_errors",
            RequestStatus.SKIPPED: "skipped",
        }
        counter_name = counter_map.get(status)
        if counter_name:
            current = getattr(self._metrics, counter_name)
            setattr(self._metrics, counter_name, current + 1)

    def _update_domain_stats(
        self, domain: str, status: RequestStatus, response_time_ms: Optional[float]
    ) -> None:
        """Update per-domain statistics."""
        self._ensure_domain_stats(domain)
        stats = self._metrics.domain_stats[domain]
        stats["total"] += 1

        status_key_map = {
            RequestStatus.SUCCESS: "successful",
            RequestStatus.FAILED: "failed",
            RequestStatus.BLOCKED: "blocked",
            RequestStatus.TIMEOUT: "timeouts",
            RequestStatus.PARSE_ERROR: "parse_errors",
            RequestStatus.SKIPPED: "skipped",
        }
        status_key = status_key_map.get(status)
        if status_key:
            stats[status_key] += 1

        if response_time_ms is not None:
            stats["response_times"].append(response_time_ms)

    def _track_response_time(self, response_time_ms: Optional[float]) -> None:
        """Track response time for percentile calculation."""
        if response_time_ms is not None:
            self._metrics.response_times.append(response_time_ms)

    def _track_error(self, error_type: Optional[str]) -> None:
        """Track error type for breakdown."""
        if error_type:
            self._metrics.error_counts[error_type] = (
                self._metrics.error_counts.get(error_type, 0) + 1
            )

    def _track_individual_metric(
        self,
        url: str,
        domain: str,
        status: RequestStatus,
        response_code: Optional[int],
        response_time_ms: Optional[float],
        error_type: Optional[str],
        error_message: Optional[str],
    ) -> None:
        """Track individual request metric if enabled."""
        if not self._track_individual:
            return

        metric = RequestMetric(
            url=url,
            domain=domain,
            status=status,
            response_code=response_code,
            response_time_ms=response_time_ms,
            error_type=error_type,
            error_message=error_message,
        )
        self._metrics.requests.append(metric)

    def record_listing_saved(self, url: str, listing_id: str) -> None:
        """Record that a listing was successfully saved.

        Args:
            url: URL of the listing
            listing_id: ID of the saved listing
        """
        self._metrics.listings_saved += 1

    def record_listing_skipped(self, url: str, reason: str) -> None:
        """Record that a listing was skipped.

        Args:
            url: URL of the listing
            reason: Reason for skipping (duplicate, unchanged, etc.)
        """
        self._metrics.listings_skipped += 1
        self._metrics.skip_reasons[reason] = (
            self._metrics.skip_reasons.get(reason, 0) + 1
        )

    def end_run(self) -> RunMetrics:
        """Mark the end of a scrape run and return final metrics.

        Returns:
            RunMetrics with all collected data
        """
        self._metrics.end_time = datetime.now()
        return self._metrics

    def get_current_stats(self) -> Dict:
        """Get current stats mid-run (for progress display).

        Returns:
            Dict with current metrics snapshot
        """
        return {
            "run_id": self._metrics.run_id,
            "total_requests": self._metrics.total_requests,
            "successful": self._metrics.successful,
            "failed": self._metrics.failed,
            "blocked": self._metrics.blocked,
            "timeouts": self._metrics.timeouts,
            "parse_errors": self._metrics.parse_errors,
            "skipped": self._metrics.skipped,
            "success_rate": self.success_rate,
            "health_status": self.health_status,
            "listings_saved": self._metrics.listings_saved,
            "listings_skipped": self._metrics.listings_skipped,
        }

    @property
    def success_rate(self) -> float:
        """Calculate current success rate as percentage.

        Returns:
            Success rate from 0.0 to 100.0
        """
        if self._metrics.total_requests == 0:
            return 100.0
        return (self._metrics.successful / self._metrics.total_requests) * 100.0

    @property
    def health_status(self) -> str:
        """Return health status based on success rate thresholds.

        Returns:
            'healthy', 'degraded', or 'critical'
        """
        rate = self.success_rate
        thresholds = SCRAPER_HEALTH_THRESHOLDS.get("success_rate", {})
        healthy_threshold = thresholds.get("healthy", 90.0)
        degraded_threshold = thresholds.get("degraded", 75.0)

        if rate >= healthy_threshold:
            return "healthy"
        elif rate >= degraded_threshold:
            return "degraded"
        else:
            return "critical"
