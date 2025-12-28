"""Tests for Scraper Health Dashboard data loading and display logic.

Tests the core data logic used in app/pages/5_Scraper_Health.py without testing
the Streamlit UI directly. Validates data loading, calculations, and transformations.

Reference: Spec 114 Phase 3 (Dashboard)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pytest

from config.settings import SCRAPER_HEALTH_THRESHOLDS
from scraping.session_report import SessionReport, SessionReportGenerator


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_reports_dir(tmp_path: Path) -> Path:
    """Create a temporary reports directory."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir


@pytest.fixture
def report_generator(temp_reports_dir: Path) -> SessionReportGenerator:
    """Create a SessionReportGenerator with temp directory."""
    return SessionReportGenerator(reports_dir=temp_reports_dir)


@pytest.fixture
def sample_report_data() -> Dict:
    """Sample report data with known values for testing."""
    return {
        "run_id": "test-run-001",
        "start_time": "2025-01-15T10:00:00",
        "end_time": "2025-01-15T10:10:00",
        "duration_seconds": 600.0,
        "summary": {
            "total_urls": 100,
            "successful": 85,
            "failed": 15,
            "success_rate": 85.0,
            "health_status": "degraded",
        },
        "status_breakdown": {
            "success": 85,
            "failed": 5,
            "blocked": 3,
            "timeout": 4,
            "parse_error": 3,
            "skipped": 0,
        },
        "domain_breakdown": {
            "imot.bg": {
                "total": 50,
                "successful": 45,
                "failed": 5,
                "success_rate": 90.0,
                "avg_response_ms": 1500.0,
                "p95_response_ms": 2500.0,
            },
            "bazar.bg": {
                "total": 50,
                "successful": 40,
                "failed": 10,
                "success_rate": 80.0,
                "avg_response_ms": 2500.0,
                "p95_response_ms": 4000.0,
            },
        },
        "error_breakdown": {
            "connection_error": 5,
            "timeout": 4,
            "blocked": 3,
            "parse_error": 3,
        },
        "top_errors": [
            {"error_type": "connection_error", "count": 5, "sample_url": "http://example.com/1"},
            {"error_type": "timeout", "count": 4, "sample_url": "http://example.com/2"},
            {"error_type": "blocked", "count": 3, "sample_url": "http://example.com/3"},
        ],
        "performance": {
            "avg_response_ms": 2000.0,
            "p50_response_ms": 1800.0,
            "p95_response_ms": 3200.0,
            "p99_response_ms": 4500.0,
        },
        "health_issues": ["High error rate: 12.0"],
        "proxy_stats": None,
        "circuit_states": None,
        "vs_baseline": None,
    }


@pytest.fixture
def create_sample_reports(report_generator: SessionReportGenerator, sample_report_data: Dict):
    """Fixture that creates multiple sample reports with different timestamps."""
    def _create(count: int = 5, start_time: datetime = None) -> List[Path]:
        """Create N sample reports with sequential timestamps.

        Args:
            count: Number of reports to create
            start_time: Starting timestamp (defaults to now - count hours)

        Returns:
            List of paths to created report files
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=count)

        paths = []
        for i in range(count):
            # Create report with incrementing timestamp
            report_time = start_time + timedelta(hours=i)
            data = sample_report_data.copy()
            data["run_id"] = f"test-run-{i:03d}"
            data["start_time"] = report_time.isoformat()
            data["end_time"] = (report_time + timedelta(minutes=10)).isoformat()

            # Vary metrics slightly for trend testing
            data["summary"]["success_rate"] = 85.0 + (i % 5)  # 85-89%
            data["performance"]["avg_response_ms"] = 2000.0 + (i * 100)  # Increasing response time

            # Save report using generator
            report = report_generator._from_json_schema(data)
            path = report_generator.save(report)
            paths.append(path)

        return paths

    return _create


# =============================================================================
# TEST: DATA LOADING
# =============================================================================


def test_dashboard_data_loading_returns_newest_first(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test that get_recent_reports() returns reports in correct order (newest first)."""
    # Create 5 reports with sequential timestamps
    create_sample_reports(count=5)

    # Load reports
    reports = report_generator.get_recent_reports(limit=30)

    # Verify we got all 5
    assert len(reports) == 5

    # Verify order: newest first
    for i in range(len(reports) - 1):
        current = datetime.fromisoformat(reports[i].start_time)
        next_report = datetime.fromisoformat(reports[i + 1].start_time)
        assert current > next_report, "Reports should be in descending order (newest first)"


def test_dashboard_data_loading_limit_parameter(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test that limit parameter works correctly."""
    # Create 10 reports
    create_sample_reports(count=10)

    # Request only 5
    reports = report_generator.get_recent_reports(limit=5)

    # Verify we got exactly 5
    assert len(reports) == 5

    # Verify they are the 5 newest (run IDs 009, 008, 007, 006, 005)
    run_ids = [r.run_id for r in reports]
    expected_newest = ["test-run-009", "test-run-008", "test-run-007", "test-run-006", "test-run-005"]
    assert run_ids == expected_newest


def test_dashboard_data_loading_empty_directory(report_generator: SessionReportGenerator):
    """Test loading from empty directory returns empty list."""
    reports = report_generator.get_recent_reports(limit=30)
    assert reports == []


# =============================================================================
# TEST: HEALTH METRICS CALCULATION
# =============================================================================


def test_health_metrics_calculation_error_rate(report_generator: SessionReportGenerator, sample_report_data: Dict):
    """Test error_rate calculation matches dashboard logic."""
    # Create report from sample data
    report = report_generator._from_json_schema(sample_report_data)

    # Dashboard calculation logic:
    total = report.total_urls if report.total_urls > 0 else 1
    status = report.status_breakdown
    error_count = status.get("failed", 0) + status.get("timeout", 0) + status.get("parse_error", 0)
    error_rate = (error_count / total) * 100.0

    # Expected: failed(5) + timeout(4) + parse_error(3) = 12 / 100 = 12.0%
    assert error_count == 12
    assert error_rate == 12.0


def test_health_metrics_calculation_block_rate(report_generator: SessionReportGenerator, sample_report_data: Dict):
    """Test block_rate calculation matches dashboard logic."""
    # Create report from sample data
    report = report_generator._from_json_schema(sample_report_data)

    # Dashboard calculation logic:
    total = report.total_urls if report.total_urls > 0 else 1
    status = report.status_breakdown
    block_count = status.get("blocked", 0)
    block_rate = (block_count / total) * 100.0

    # Expected: blocked(3) / 100 = 3.0%
    assert block_count == 3
    assert block_rate == 3.0


def test_health_metrics_calculation_zero_urls(report_generator: SessionReportGenerator, sample_report_data: Dict):
    """Test calculations handle zero total_urls gracefully."""
    # Modify sample data to have zero URLs
    sample_report_data["summary"]["total_urls"] = 0
    report = report_generator._from_json_schema(sample_report_data)

    # Dashboard logic uses 1 as fallback to avoid division by zero
    total = report.total_urls if report.total_urls > 0 else 1
    status = report.status_breakdown
    error_count = status.get("failed", 0) + status.get("timeout", 0) + status.get("parse_error", 0)
    block_count = status.get("blocked", 0)

    error_rate = (error_count / total) * 100.0
    block_rate = (block_count / total) * 100.0

    # With total=1 (fallback), error_count=12, block_count=3
    assert error_rate == 1200.0  # 12/1 * 100
    assert block_rate == 300.0   # 3/1 * 100


# =============================================================================
# TEST: HEALTH STATUS DETERMINATION
# =============================================================================


def test_health_status_determination_success_rate_healthy():
    """Test health status for success_rate >= 90 (healthy)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test success_rate >= 90 → healthy
    status = get_health_status("success_rate", 95.0, higher_is_better=True)
    assert status == "healthy"

    status = get_health_status("success_rate", 90.0, higher_is_better=True)
    assert status == "healthy"


def test_health_status_determination_success_rate_degraded():
    """Test health status for success_rate >= 75 and < 90 (degraded)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test success_rate >= 75 and < 90 → degraded
    status = get_health_status("success_rate", 85.0, higher_is_better=True)
    assert status == "degraded"

    status = get_health_status("success_rate", 75.0, higher_is_better=True)
    assert status == "degraded"


def test_health_status_determination_success_rate_critical():
    """Test health status for success_rate < 75 (critical)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test success_rate < 75 → critical
    status = get_health_status("success_rate", 70.0, higher_is_better=True)
    assert status == "critical"

    status = get_health_status("success_rate", 50.0, higher_is_better=True)
    assert status == "critical"


def test_health_status_determination_error_rate_healthy():
    """Test health status for error_rate <= 5 (healthy), lower is better."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test error_rate <= 5 → healthy
    status = get_health_status("error_rate", 3.0, higher_is_better=False)
    assert status == "healthy"

    status = get_health_status("error_rate", 5.0, higher_is_better=False)
    assert status == "healthy"


def test_health_status_determination_error_rate_degraded():
    """Test health status for error_rate <= 15 and > 5 (degraded)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test error_rate <= 15 and > 5 → degraded
    status = get_health_status("error_rate", 10.0, higher_is_better=False)
    assert status == "degraded"

    status = get_health_status("error_rate", 15.0, higher_is_better=False)
    assert status == "degraded"


def test_health_status_determination_error_rate_critical():
    """Test health status for error_rate > 15 (critical)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test error_rate > 15 → critical
    status = get_health_status("error_rate", 20.0, higher_is_better=False)
    assert status == "critical"

    status = get_health_status("error_rate", 25.0, higher_is_better=False)
    assert status == "critical"


def test_health_status_determination_avg_response_healthy():
    """Test health status for avg_response_ms <= 2000 (healthy)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test avg_response_ms <= 2000 → healthy
    status = get_health_status("avg_response_ms", 1500.0, higher_is_better=False)
    assert status == "healthy"

    status = get_health_status("avg_response_ms", 2000.0, higher_is_better=False)
    assert status == "healthy"


def test_health_status_determination_avg_response_degraded():
    """Test health status for avg_response_ms <= 5000 and > 2000 (degraded)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test avg_response_ms <= 5000 and > 2000 → degraded
    status = get_health_status("avg_response_ms", 3500.0, higher_is_better=False)
    assert status == "degraded"

    status = get_health_status("avg_response_ms", 5000.0, higher_is_better=False)
    assert status == "degraded"


def test_health_status_determination_avg_response_critical():
    """Test health status for avg_response_ms > 5000 (critical)."""
    def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
        """Dashboard's health status logic."""
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

    # Test avg_response_ms > 5000 → critical
    status = get_health_status("avg_response_ms", 6000.0, higher_is_better=False)
    assert status == "critical"

    status = get_health_status("avg_response_ms", 8000.0, higher_is_better=False)
    assert status == "critical"


# =============================================================================
# TEST: TREND DATA PREPARATION
# =============================================================================


def test_trend_data_preparation_chronological_order(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test that trend data is prepared in chronological order (oldest first)."""
    # Create 5 reports
    create_sample_reports(count=5)

    # Load reports (newest first)
    reports = report_generator.get_recent_reports(limit=30)

    # Dashboard reverses for chronological order
    chronological = list(reversed(reports))

    # Verify order: oldest first
    for i in range(len(chronological) - 1):
        current = datetime.fromisoformat(chronological[i].start_time)
        next_report = datetime.fromisoformat(chronological[i + 1].start_time)
        assert current < next_report, "Chronological list should be ascending order (oldest first)"


def test_trend_data_preparation_data_extraction(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test extraction of trend chart data: start_time, success_rate, avg_response_time_ms."""
    # Create 3 reports
    create_sample_reports(count=3)

    # Load and reverse to chronological
    reports = report_generator.get_recent_reports(limit=30)
    chronological = list(reversed(reports))

    # Extract data like dashboard does
    trend_data = []
    for r in chronological:
        trend_data.append({
            "time": r.start_time[:16].replace("T", " "),
            "Success Rate (%)": r.success_rate,
            "Avg Response (ms)": r.avg_response_time_ms,
        })

    # Verify we have 3 data points
    assert len(trend_data) == 3

    # Verify each point has required fields
    for point in trend_data:
        assert "time" in point
        assert "Success Rate (%)" in point
        assert "Avg Response (ms)" in point
        assert isinstance(point["Success Rate (%)"], float)
        assert isinstance(point["Avg Response (ms)"], float)

    # Verify time formatting (no 'T', just space)
    for point in trend_data:
        assert "T" not in point["time"]
        assert " " in point["time"]


def test_trend_data_preparation_varying_metrics(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test that varying metrics across reports are correctly extracted."""
    # Create 5 reports (fixture varies success_rate and avg_response_ms)
    create_sample_reports(count=5)

    # Load and prepare trend data
    reports = report_generator.get_recent_reports(limit=30)
    chronological = list(reversed(reports))

    trend_data = []
    for r in chronological:
        trend_data.append({
            "time": r.start_time[:16].replace("T", " "),
            "Success Rate (%)": r.success_rate,
            "Avg Response (ms)": r.avg_response_time_ms,
        })

    # Verify success_rate increases (85, 86, 87, 88, 89)
    success_rates = [point["Success Rate (%)"] for point in trend_data]
    assert success_rates == [85.0, 86.0, 87.0, 88.0, 89.0]

    # Verify avg_response_ms increases (2000, 2100, 2200, 2300, 2400)
    response_times = [point["Avg Response (ms)"] for point in trend_data]
    assert response_times == [2000.0, 2100.0, 2200.0, 2300.0, 2400.0]


# =============================================================================
# TEST: RUN HISTORY DATA PREPARATION
# =============================================================================


def test_run_history_data_preparation(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test extraction of run history table data."""
    # Create 10 reports
    create_sample_reports(count=10)

    # Load reports
    reports = report_generator.get_recent_reports(limit=30)

    # Dashboard shows last 10 runs
    history_data = []
    for r in reports[:10]:
        # Format date nicely
        date_str = r.start_time[:16].replace("T", " ")
        # Duration in minutes
        duration_str = f"{r.duration_seconds / 60:.1f}m"
        # Success rate
        success_str = f"{r.success_rate:.1f}%"
        # Status emoji
        health_emoji = {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}.get(r.health_status, "⚪")

        history_data.append({
            "Date": date_str,
            "Duration": duration_str,
            "URLs": r.total_urls,
            "Success Rate": success_str,
            "Errors": r.failed,
            "Status": f"{health_emoji} {r.health_status}",
        })

    # Verify we have 10 entries
    assert len(history_data) == 10

    # Verify each entry has required fields
    for entry in history_data:
        assert "Date" in entry
        assert "Duration" in entry
        assert "URLs" in entry
        assert "Success Rate" in entry
        assert "Errors" in entry
        assert "Status" in entry

        # Verify formatting
        assert "T" not in entry["Date"]
        assert entry["Duration"].endswith("m")
        assert entry["Success Rate"].endswith("%")
        assert entry["Status"].startswith(("🟢", "🟡", "🔴", "⚪"))


def test_run_history_data_preparation_duration_formatting(
    report_generator: SessionReportGenerator,
    sample_report_data: Dict,
):
    """Test duration formatting in run history."""
    # Create report with 600 seconds = 10 minutes
    sample_report_data["duration_seconds"] = 600.0
    report = report_generator._from_json_schema(sample_report_data)
    report_generator.save(report)

    # Load and format
    reports = report_generator.get_recent_reports(limit=1)
    r = reports[0]
    duration_str = f"{r.duration_seconds / 60:.1f}m"

    assert duration_str == "10.0m"

    # Test with 90 seconds = 1.5 minutes
    sample_report_data["duration_seconds"] = 90.0
    report = report_generator._from_json_schema(sample_report_data)
    report_generator.save(report)

    reports = report_generator.get_recent_reports(limit=1)
    r = reports[0]
    duration_str = f"{r.duration_seconds / 60:.1f}m"

    assert duration_str == "1.5m"


# =============================================================================
# TEST: DOMAIN BREAKDOWN DATA PREPARATION
# =============================================================================


def test_domain_breakdown_data_preparation(
    report_generator: SessionReportGenerator,
    sample_report_data: Dict,
):
    """Test extraction of domain health table data."""
    # Create report with domain breakdown
    report = report_generator._from_json_schema(sample_report_data)

    # Dashboard extracts domain breakdown
    domain_breakdown = report.domain_breakdown if hasattr(report, "domain_breakdown") else {}

    domain_data = []
    for domain, stats in domain_breakdown.items():
        success_rate = stats.get("success_rate", 0.0)
        avg_response = stats.get("avg_response_ms", 0)
        domain_data.append({
            "Domain": domain,
            "Success Rate": f"{success_rate:.1f}%",
            "Avg Response": f"{avg_response:.0f}ms",
        })

    # Verify we have 2 domains
    assert len(domain_data) == 2

    # Verify imot.bg entry
    imot_entry = next(d for d in domain_data if d["Domain"] == "imot.bg")
    assert imot_entry["Success Rate"] == "90.0%"
    assert imot_entry["Avg Response"] == "1500ms"

    # Verify bazar.bg entry
    bazar_entry = next(d for d in domain_data if d["Domain"] == "bazar.bg")
    assert bazar_entry["Success Rate"] == "80.0%"
    assert bazar_entry["Avg Response"] == "2500ms"


def test_domain_breakdown_data_preparation_no_breakdown(
    report_generator: SessionReportGenerator,
    sample_report_data: Dict,
):
    """Test handling when no domain breakdown is available."""
    # Create report without domain breakdown
    sample_report_data["domain_breakdown"] = {}
    report = report_generator._from_json_schema(sample_report_data)

    # Dashboard extracts domain breakdown
    domain_breakdown = report.domain_breakdown if hasattr(report, "domain_breakdown") else {}

    # Verify it's empty
    assert domain_breakdown == {}

    # Dashboard would show "No domain breakdown available."
    if not domain_breakdown:
        message = "No domain breakdown available."

    assert message == "No domain breakdown available."


def test_domain_breakdown_data_preparation_formatting(
    report_generator: SessionReportGenerator,
    sample_report_data: Dict,
):
    """Test formatting of domain breakdown values."""
    # Modify domain stats for edge cases
    sample_report_data["domain_breakdown"] = {
        "example.com": {
            "total": 100,
            "successful": 100,
            "failed": 0,
            "success_rate": 100.0,
            "avg_response_ms": 999.7,
            "p95_response_ms": 1500.0,
        },
        "slow.com": {
            "total": 50,
            "successful": 25,
            "failed": 25,
            "success_rate": 50.0,
            "avg_response_ms": 5432.1,
            "p95_response_ms": 8000.0,
        },
    }

    report = report_generator._from_json_schema(sample_report_data)

    # Extract data
    domain_data = []
    for domain, stats in report.domain_breakdown.items():
        success_rate = stats.get("success_rate", 0.0)
        avg_response = stats.get("avg_response_ms", 0)
        domain_data.append({
            "Domain": domain,
            "Success Rate": f"{success_rate:.1f}%",
            "Avg Response": f"{avg_response:.0f}ms",
        })

    # Verify formatting
    example_entry = next(d for d in domain_data if d["Domain"] == "example.com")
    assert example_entry["Success Rate"] == "100.0%"
    assert example_entry["Avg Response"] == "1000ms"  # 999.7 rounds to 1000

    slow_entry = next(d for d in domain_data if d["Domain"] == "slow.com")
    assert slow_entry["Success Rate"] == "50.0%"
    assert slow_entry["Avg Response"] == "5432ms"


# =============================================================================
# TEST: INTEGRATION
# =============================================================================


def test_dashboard_full_workflow(
    report_generator: SessionReportGenerator,
    create_sample_reports,
):
    """Test complete dashboard workflow: load → calculate → format."""
    # Create 5 reports
    create_sample_reports(count=5)

    # Step 1: Load reports (like dashboard does)
    reports = report_generator.get_recent_reports(limit=30)
    assert len(reports) == 5

    # Step 2: Get latest report
    latest = reports[0]
    assert latest is not None

    # Step 3: Calculate metrics
    total = latest.total_urls if latest.total_urls > 0 else 1
    status = latest.status_breakdown
    error_count = status.get("failed", 0) + status.get("timeout", 0) + status.get("parse_error", 0)
    block_count = status.get("blocked", 0)
    error_rate = (error_count / total) * 100.0
    block_rate = (block_count / total) * 100.0

    # Verify calculations work
    assert isinstance(error_rate, float)
    assert isinstance(block_rate, float)
    assert error_rate >= 0.0
    assert block_rate >= 0.0

    # Step 4: Prepare trend data (if enough reports)
    if len(reports) >= 2:
        chronological = list(reversed(reports))
        trend_data = []
        for r in chronological:
            trend_data.append({
                "time": r.start_time[:16].replace("T", " "),
                "Success Rate (%)": r.success_rate,
                "Avg Response (ms)": r.avg_response_time_ms,
            })

        assert len(trend_data) == 5

    # Step 5: Prepare domain breakdown
    domain_breakdown = latest.domain_breakdown if hasattr(latest, "domain_breakdown") else {}
    domain_data = []
    for domain, stats in domain_breakdown.items():
        success_rate = stats.get("success_rate", 0.0)
        avg_response = stats.get("avg_response_ms", 0)
        domain_data.append({
            "Domain": domain,
            "Success Rate": f"{success_rate:.1f}%",
            "Avg Response": f"{avg_response:.0f}ms",
        })

    assert len(domain_data) == 2  # imot.bg and bazar.bg

    # Step 6: Prepare run history
    history_data = []
    for r in reports[:10]:
        date_str = r.start_time[:16].replace("T", " ")
        duration_str = f"{r.duration_seconds / 60:.1f}m"
        success_str = f"{r.success_rate:.1f}%"
        health_emoji = {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}.get(r.health_status, "⚪")

        history_data.append({
            "Date": date_str,
            "Duration": duration_str,
            "URLs": r.total_urls,
            "Success Rate": success_str,
            "Errors": r.failed,
            "Status": f"{health_emoji} {r.health_status}",
        })

    assert len(history_data) == 5  # Only 5 reports created
