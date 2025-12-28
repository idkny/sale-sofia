"""Session report generation for scraper monitoring.

Generates structured reports from run metrics for historical analysis,
health assessment, and baseline comparison.

Reference: Spec 114 Section 2 (SessionReportGenerator)
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scraping.metrics import RunMetrics

# Import settings with fallback defaults
try:
    from config.settings import SCRAPER_HEALTH_THRESHOLDS
except ImportError:
    SCRAPER_HEALTH_THRESHOLDS = {
        "success_rate": {"healthy": 90.0, "degraded": 75.0},
        "error_rate": {"healthy": 5.0, "degraded": 15.0},
        "block_rate": {"healthy": 2.0, "degraded": 5.0},
        "avg_response_ms": {"healthy": 2000, "degraded": 5000},
    }

# Default reports directory
DEFAULT_REPORTS_DIR = Path("data/reports")


def _calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile value from a list of floats.

    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)

    Returns:
        Percentile value, or 0.0 if list is empty
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = (percentile / 100.0) * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = index - lower

    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])


def _assess_health(
    success_rate: float,
    error_rate: float,
    block_rate: float,
    avg_response_ms: float,
) -> Tuple[str, List[str]]:
    """Assess overall health and collect issues.

    Args:
        success_rate: Success percentage (0-100)
        error_rate: Error percentage (0-100)
        block_rate: Block percentage (0-100)
        avg_response_ms: Average response time in milliseconds

    Returns:
        Tuple of (status, issues_list) where status is healthy/degraded/critical
    """
    issues: List[str] = []
    worst_status = "healthy"

    checks = [
        ("success_rate", success_rate, True, "Low success rate"),
        ("error_rate", error_rate, False, "High error rate"),
        ("block_rate", block_rate, False, "High block rate"),
        ("avg_response_ms", avg_response_ms, False, "Slow response time"),
    ]

    for metric_name, value, higher_is_better, issue_prefix in checks:
        status = _check_threshold(metric_name, value, higher_is_better)
        if status != "healthy":
            issues.append(f"{issue_prefix}: {value:.1f}")
        worst_status = _worse_status(worst_status, status)

    return worst_status, issues


def _check_threshold(metric_name: str, value: float, higher_is_better: bool) -> str:
    """Check a metric against its thresholds."""
    thresholds = SCRAPER_HEALTH_THRESHOLDS.get(metric_name, {})
    healthy = thresholds.get("healthy", 90.0 if higher_is_better else 5.0)
    degraded = thresholds.get("degraded", 75.0 if higher_is_better else 15.0)

    if higher_is_better:
        if value >= healthy:
            return "healthy"
        elif value >= degraded:
            return "degraded"
        return "critical"
    else:
        if value <= healthy:
            return "healthy"
        elif value <= degraded:
            return "degraded"
        return "critical"


def _worse_status(current: str, new: str) -> str:
    """Return the worse of two status values."""
    order = {"healthy": 0, "degraded": 1, "critical": 2}
    return current if order.get(current, 0) >= order.get(new, 0) else new


@dataclass
class SessionReport:
    """Complete report for a scrape session."""

    # Run identification
    run_id: str
    start_time: str  # ISO format
    end_time: str  # ISO format
    duration_seconds: float

    # Summary metrics
    total_urls: int
    successful: int
    failed: int
    success_rate: float

    # Breakdown by status
    status_breakdown: Dict[str, int]

    # Breakdown by domain
    domain_breakdown: Dict[str, Dict]

    # Error analysis
    error_breakdown: Dict[str, int]
    top_errors: List[Dict]

    # Performance metrics
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float

    # Health assessment
    health_status: str
    health_issues: List[str]

    # Optional external data
    proxy_stats: Optional[Dict] = None
    circuit_states: Optional[Dict[str, str]] = None
    vs_baseline: Optional[Dict] = None


class SessionReportGenerator:
    """Generates and persists session reports."""

    def __init__(self, reports_dir: Optional[Path] = None):
        """Initialize report generator.

        Args:
            reports_dir: Directory to save reports (default: data/reports/)
        """
        self._reports_dir = reports_dir or DEFAULT_REPORTS_DIR
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        metrics: RunMetrics,
        proxy_stats: Optional[Dict] = None,
        circuit_states: Optional[Dict] = None,
    ) -> SessionReport:
        """Generate a complete session report from run metrics.

        Args:
            metrics: Collected run metrics
            proxy_stats: Optional proxy health statistics
            circuit_states: Optional circuit breaker states

        Returns:
            SessionReport with all metrics processed
        """
        duration = self._calculate_duration(metrics)
        success_rate = self._calculate_success_rate(metrics)
        status_breakdown = self._build_status_breakdown(metrics)
        domain_breakdown = self._build_domain_breakdown(metrics)
        top_errors = self._build_top_errors(metrics)
        perf = self._calculate_performance(metrics.response_times)
        error_rate = self._calculate_error_rate(metrics)
        block_rate = self._calculate_block_rate(metrics)

        health_status, health_issues = _assess_health(
            success_rate, error_rate, block_rate, perf["avg"]
        )

        return SessionReport(
            run_id=metrics.run_id,
            start_time=metrics.start_time.isoformat(),
            end_time=(metrics.end_time or datetime.now()).isoformat(),
            duration_seconds=duration,
            total_urls=metrics.total_requests,
            successful=metrics.successful,
            failed=metrics.failed + metrics.blocked + metrics.timeouts + metrics.parse_errors,
            success_rate=success_rate,
            status_breakdown=status_breakdown,
            domain_breakdown=domain_breakdown,
            error_breakdown=dict(metrics.error_counts),
            top_errors=top_errors,
            avg_response_time_ms=perf["avg"],
            p50_response_time_ms=perf["p50"],
            p95_response_time_ms=perf["p95"],
            p99_response_time_ms=perf["p99"],
            health_status=health_status,
            health_issues=health_issues,
            proxy_stats=proxy_stats,
            circuit_states=circuit_states,
        )

    def _calculate_duration(self, metrics: RunMetrics) -> float:
        """Calculate run duration in seconds."""
        end = metrics.end_time or datetime.now()
        return (end - metrics.start_time).total_seconds()

    def _calculate_success_rate(self, metrics: RunMetrics) -> float:
        """Calculate success rate as percentage."""
        if metrics.total_requests == 0:
            return 100.0
        return (metrics.successful / metrics.total_requests) * 100.0

    def _calculate_error_rate(self, metrics: RunMetrics) -> float:
        """Calculate error rate as percentage."""
        if metrics.total_requests == 0:
            return 0.0
        errors = metrics.failed + metrics.timeouts + metrics.parse_errors
        return (errors / metrics.total_requests) * 100.0

    def _calculate_block_rate(self, metrics: RunMetrics) -> float:
        """Calculate block rate as percentage."""
        if metrics.total_requests == 0:
            return 0.0
        return (metrics.blocked / metrics.total_requests) * 100.0

    def _build_status_breakdown(self, metrics: RunMetrics) -> Dict[str, int]:
        """Build status count breakdown."""
        return {
            "success": metrics.successful,
            "failed": metrics.failed,
            "blocked": metrics.blocked,
            "timeout": metrics.timeouts,
            "parse_error": metrics.parse_errors,
            "skipped": metrics.skipped,
        }

    def _build_domain_breakdown(self, metrics: RunMetrics) -> Dict[str, Dict]:
        """Build per-domain statistics."""
        result = {}
        for domain, stats in metrics.domain_stats.items():
            response_times = stats.get("response_times", [])
            total = stats.get("total", 0)
            successful = stats.get("successful", 0)

            result[domain] = {
                "total": total,
                "successful": successful,
                "failed": stats.get("failed", 0),
                "success_rate": (successful / total * 100.0) if total > 0 else 0.0,
                "avg_response_ms": sum(response_times) / len(response_times) if response_times else 0.0,
                "p95_response_ms": _calculate_percentile(response_times, 95),
            }
        return result

    def _build_top_errors(self, metrics: RunMetrics, limit: int = 5) -> List[Dict]:
        """Build list of top errors with sample URLs."""
        error_urls: Dict[str, str] = {}

        for req in metrics.requests:
            if req.error_type and req.error_type not in error_urls:
                error_urls[req.error_type] = req.url

        sorted_errors = sorted(
            metrics.error_counts.items(), key=lambda x: x[1], reverse=True
        )

        return [
            {
                "error_type": error_type,
                "count": count,
                "sample_url": error_urls.get(error_type, ""),
            }
            for error_type, count in sorted_errors[:limit]
        ]

    def _calculate_performance(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate performance percentiles."""
        avg = sum(response_times) / len(response_times) if response_times else 0.0
        return {
            "avg": avg,
            "p50": _calculate_percentile(response_times, 50),
            "p95": _calculate_percentile(response_times, 95),
            "p99": _calculate_percentile(response_times, 99),
        }

    def save(self, report: SessionReport) -> Path:
        """Save report to JSON file.

        Args:
            report: SessionReport to save

        Returns:
            Path to saved file
        """
        timestamp = datetime.fromisoformat(report.start_time)
        filename = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self._reports_dir / filename

        report_dict = self._to_json_schema(report)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        return filepath

    def _to_json_schema(self, report: SessionReport) -> Dict:
        """Convert SessionReport to JSON schema format from spec."""
        return {
            "run_id": report.run_id,
            "start_time": report.start_time,
            "end_time": report.end_time,
            "duration_seconds": report.duration_seconds,
            "summary": {
                "total_urls": report.total_urls,
                "successful": report.successful,
                "failed": report.failed,
                "success_rate": report.success_rate,
                "health_status": report.health_status,
            },
            "status_breakdown": report.status_breakdown,
            "domain_breakdown": report.domain_breakdown,
            "error_breakdown": report.error_breakdown,
            "top_errors": report.top_errors,
            "performance": {
                "avg_response_ms": report.avg_response_time_ms,
                "p50_response_ms": report.p50_response_time_ms,
                "p95_response_ms": report.p95_response_time_ms,
                "p99_response_ms": report.p99_response_time_ms,
            },
            "proxy_stats": report.proxy_stats,
            "circuit_states": report.circuit_states,
            "health_issues": report.health_issues,
            "vs_baseline": report.vs_baseline,
        }

    def load(self, report_path: Path) -> SessionReport:
        """Load a report from file.

        Args:
            report_path: Path to report JSON file

        Returns:
            SessionReport loaded from file
        """
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self._from_json_schema(data)

    def _from_json_schema(self, data: Dict) -> SessionReport:
        """Convert JSON schema format back to SessionReport."""
        summary = data.get("summary", {})
        performance = data.get("performance", {})

        return SessionReport(
            run_id=data["run_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            duration_seconds=data["duration_seconds"],
            total_urls=summary.get("total_urls", 0),
            successful=summary.get("successful", 0),
            failed=summary.get("failed", 0),
            success_rate=summary.get("success_rate", 0.0),
            status_breakdown=data.get("status_breakdown", {}),
            domain_breakdown=data.get("domain_breakdown", {}),
            error_breakdown=data.get("error_breakdown", {}),
            top_errors=data.get("top_errors", []),
            avg_response_time_ms=performance.get("avg_response_ms", 0.0),
            p50_response_time_ms=performance.get("p50_response_ms", 0.0),
            p95_response_time_ms=performance.get("p95_response_ms", 0.0),
            p99_response_time_ms=performance.get("p99_response_ms", 0.0),
            health_status=summary.get("health_status", "unknown"),
            health_issues=data.get("health_issues", []),
            proxy_stats=data.get("proxy_stats"),
            circuit_states=data.get("circuit_states"),
            vs_baseline=data.get("vs_baseline"),
        )

    def get_recent_reports(self, limit: int = 30) -> List[SessionReport]:
        """Load the N most recent reports.

        Args:
            limit: Maximum number of reports to load

        Returns:
            List of SessionReport objects, newest first
        """
        pattern = "session_*.json"
        report_files = sorted(
            self._reports_dir.glob(pattern), key=lambda p: p.name, reverse=True
        )

        reports = []
        for filepath in report_files[:limit]:
            try:
                reports.append(self.load(filepath))
            except (json.JSONDecodeError, KeyError):
                continue

        return reports

    def calculate_baseline(self, days: int = 7) -> Dict:
        """Calculate baseline metrics from last N days of reports.

        Args:
            days: Number of days to include in baseline

        Returns:
            Dict with baseline metrics (averages)
        """
        cutoff = datetime.now() - timedelta(days=days)
        reports = self.get_recent_reports(limit=100)

        recent = [
            r for r in reports
            if datetime.fromisoformat(r.start_time) >= cutoff
        ]

        if not recent:
            return {}

        return {
            "success_rate": sum(r.success_rate for r in recent) / len(recent),
            "avg_response_ms": sum(r.avg_response_time_ms for r in recent) / len(recent),
            "p95_response_ms": sum(r.p95_response_time_ms for r in recent) / len(recent),
            "total_urls_avg": sum(r.total_urls for r in recent) / len(recent),
            "report_count": len(recent),
            "calculated_at": datetime.now().isoformat(),
        }

    def compare_to_baseline(self, report: SessionReport, baseline: Dict) -> Dict:
        """Compare a report to baseline metrics.

        Args:
            report: SessionReport to compare
            baseline: Baseline metrics from calculate_baseline()

        Returns:
            Dict with delta values for each metric
        """
        if not baseline:
            return {}

        return {
            "success_rate_delta": report.success_rate - baseline.get("success_rate", 0),
            "avg_response_delta": report.avg_response_time_ms - baseline.get("avg_response_ms", 0),
            "p95_response_delta": report.p95_response_time_ms - baseline.get("p95_response_ms", 0),
            "total_urls_delta": report.total_urls - baseline.get("total_urls_avg", 0),
            "baseline_report_count": baseline.get("report_count", 0),
        }
