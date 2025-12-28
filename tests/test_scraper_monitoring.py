"""
Tests for scraper monitoring metrics and session reports.

Tests:
- MetricsCollector: request/response tracking, counters, health status
- SessionReportGenerator: report generation, persistence, baseline comparison
- Helper functions: percentile calculation, health assessment
"""

import json
import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.metrics import (
    MetricsCollector,
    RequestStatus,
    RunMetrics,
    RequestMetric,
)
from scraping.session_report import (
    SessionReportGenerator,
    SessionReport,
    _calculate_percentile,
    _assess_health,
)


# =============================================================================
# METRICS COLLECTOR TESTS
# =============================================================================


def test_metrics_collector_init_default_run_id():
    """Test MetricsCollector generates run_id if not provided."""
    collector = MetricsCollector()

    assert collector._run_id is not None
    assert collector._run_id.startswith("scrape_")
    assert len(collector._run_id) > 20  # timestamp + uuid


def test_metrics_collector_init_custom_run_id():
    """Test MetricsCollector accepts custom run_id."""
    custom_id = "test_run_123"
    collector = MetricsCollector(run_id=custom_id)

    assert collector._run_id == custom_id


def test_metrics_collector_init_track_individual_flag():
    """Test track_individual flag controls request tracking."""
    collector_with = MetricsCollector(track_individual=True)
    collector_without = MetricsCollector(track_individual=False)

    assert collector_with._track_individual is True
    assert collector_without._track_individual is False


def test_record_request_increments_total():
    """Test record_request increments total_requests counter."""
    collector = MetricsCollector()

    collector.record_request("https://example.com/1", "example.com")
    collector.record_request("https://example.com/2", "example.com")

    assert collector._metrics.total_requests == 2


def test_record_response_updates_counters_success():
    """Test record_response updates successful counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.SUCCESS,
        response_code=200,
        response_time_ms=150.0,
    )

    assert collector._metrics.successful == 1
    assert collector._metrics.failed == 0


def test_record_response_updates_counters_failed():
    """Test record_response updates failed counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.FAILED,
        error_type="ConnectionError",
    )

    assert collector._metrics.successful == 0
    assert collector._metrics.failed == 1


def test_record_response_updates_counters_blocked():
    """Test record_response updates blocked counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.BLOCKED,
        response_code=403,
    )

    assert collector._metrics.blocked == 1


def test_record_response_updates_counters_timeout():
    """Test record_response updates timeouts counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.TIMEOUT,
        error_type="TimeoutError",
    )

    assert collector._metrics.timeouts == 1


def test_record_response_updates_counters_parse_error():
    """Test record_response updates parse_errors counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.PARSE_ERROR,
        error_type="ParseError",
    )

    assert collector._metrics.parse_errors == 1


def test_record_response_updates_counters_skipped():
    """Test record_response updates skipped counter."""
    collector = MetricsCollector()
    collector.record_request("https://example.com", "example.com")

    collector.record_response(
        "https://example.com",
        RequestStatus.SKIPPED,
    )

    assert collector._metrics.skipped == 1


def test_record_response_tracks_domain_stats():
    """Test record_response tracks per-domain breakdown."""
    collector = MetricsCollector()

    collector.record_request("https://imot.bg/1", "imot.bg")
    collector.record_response(
        "https://imot.bg/1",
        RequestStatus.SUCCESS,
        response_time_ms=200.0,
    )

    collector.record_request("https://imot.bg/2", "imot.bg")
    collector.record_response(
        "https://imot.bg/2",
        RequestStatus.FAILED,
    )

    collector.record_request("https://homes.bg/1", "homes.bg")
    collector.record_response(
        "https://homes.bg/1",
        RequestStatus.SUCCESS,
        response_time_ms=150.0,
    )

    assert "imot.bg" in collector._metrics.domain_stats
    assert "homes.bg" in collector._metrics.domain_stats

    imot_stats = collector._metrics.domain_stats["imot.bg"]
    assert imot_stats["total"] == 2
    assert imot_stats["successful"] == 1
    assert imot_stats["failed"] == 1

    homes_stats = collector._metrics.domain_stats["homes.bg"]
    assert homes_stats["total"] == 1
    assert homes_stats["successful"] == 1


def test_record_response_tracks_response_times():
    """Test record_response tracks response_times list."""
    collector = MetricsCollector()

    collector.record_request("https://example.com/1", "example.com")
    collector.record_response(
        "https://example.com/1",
        RequestStatus.SUCCESS,
        response_time_ms=150.0,
    )

    collector.record_request("https://example.com/2", "example.com")
    collector.record_response(
        "https://example.com/2",
        RequestStatus.SUCCESS,
        response_time_ms=250.0,
    )

    assert len(collector._metrics.response_times) == 2
    assert 150.0 in collector._metrics.response_times
    assert 250.0 in collector._metrics.response_times


def test_record_response_tracks_errors():
    """Test record_response tracks error_counts dict."""
    collector = MetricsCollector()

    collector.record_request("https://example.com/1", "example.com")
    collector.record_response(
        "https://example.com/1",
        RequestStatus.FAILED,
        error_type="ConnectionError",
    )

    collector.record_request("https://example.com/2", "example.com")
    collector.record_response(
        "https://example.com/2",
        RequestStatus.FAILED,
        error_type="ConnectionError",
    )

    collector.record_request("https://example.com/3", "example.com")
    collector.record_response(
        "https://example.com/3",
        RequestStatus.TIMEOUT,
        error_type="TimeoutError",
    )

    assert collector._metrics.error_counts["ConnectionError"] == 2
    assert collector._metrics.error_counts["TimeoutError"] == 1


def test_record_listing_saved():
    """Test record_listing_saved increments listings_saved counter."""
    collector = MetricsCollector()

    collector.record_listing_saved("https://example.com/1", "listing_1")
    collector.record_listing_saved("https://example.com/2", "listing_2")

    assert collector._metrics.listings_saved == 2


def test_record_listing_skipped():
    """Test record_listing_skipped increments counter and tracks reasons."""
    collector = MetricsCollector()

    collector.record_listing_skipped("https://example.com/1", "duplicate")
    collector.record_listing_skipped("https://example.com/2", "duplicate")
    collector.record_listing_skipped("https://example.com/3", "unchanged")

    assert collector._metrics.listings_skipped == 3
    assert collector._metrics.skip_reasons["duplicate"] == 2
    assert collector._metrics.skip_reasons["unchanged"] == 1


def test_success_rate_property_calculation():
    """Test success_rate property calculates percentage correctly."""
    collector = MetricsCollector()

    # Record 7 successful out of 10 requests
    for i in range(10):
        collector.record_request(f"https://example.com/{i}", "example.com")
        status = RequestStatus.SUCCESS if i < 7 else RequestStatus.FAILED
        collector.record_response(f"https://example.com/{i}", status)

    assert collector.success_rate == 70.0


def test_success_rate_zero_requests():
    """Test success_rate returns 100.0 when no requests made."""
    collector = MetricsCollector()

    assert collector.success_rate == 100.0


def test_health_status_healthy():
    """Test health_status returns 'healthy' when >= 90% success."""
    collector = MetricsCollector()

    # 9 successful out of 10 = 90%
    for i in range(10):
        collector.record_request(f"https://example.com/{i}", "example.com")
        status = RequestStatus.SUCCESS if i < 9 else RequestStatus.FAILED
        collector.record_response(f"https://example.com/{i}", status)

    assert collector.health_status == "healthy"


def test_health_status_degraded():
    """Test health_status returns 'degraded' when 75-90% success."""
    collector = MetricsCollector()

    # 8 successful out of 10 = 80%
    for i in range(10):
        collector.record_request(f"https://example.com/{i}", "example.com")
        status = RequestStatus.SUCCESS if i < 8 else RequestStatus.FAILED
        collector.record_response(f"https://example.com/{i}", status)

    assert collector.health_status == "degraded"


def test_health_status_critical():
    """Test health_status returns 'critical' when < 75% success."""
    collector = MetricsCollector()

    # 5 successful out of 10 = 50%
    for i in range(10):
        collector.record_request(f"https://example.com/{i}", "example.com")
        status = RequestStatus.SUCCESS if i < 5 else RequestStatus.FAILED
        collector.record_response(f"https://example.com/{i}", status)

    assert collector.health_status == "critical"


def test_end_run_returns_metrics():
    """Test end_run sets end_time and returns RunMetrics."""
    collector = MetricsCollector()

    collector.record_request("https://example.com", "example.com")
    collector.record_response("https://example.com", RequestStatus.SUCCESS)

    metrics = collector.end_run()

    assert isinstance(metrics, RunMetrics)
    assert metrics.end_time is not None
    assert metrics.total_requests == 1


def test_get_current_stats():
    """Test get_current_stats returns dict snapshot."""
    collector = MetricsCollector(run_id="test_123")

    collector.record_request("https://example.com", "example.com")
    collector.record_response("https://example.com", RequestStatus.SUCCESS)
    collector.record_listing_saved("https://example.com", "listing_1")

    stats = collector.get_current_stats()

    assert stats["run_id"] == "test_123"
    assert stats["total_requests"] == 1
    assert stats["successful"] == 1
    assert stats["success_rate"] == 100.0
    assert stats["health_status"] == "healthy"
    assert stats["listings_saved"] == 1
    assert stats["listings_skipped"] == 0


def test_track_individual_metric_enabled():
    """Test individual request metrics are tracked when enabled."""
    collector = MetricsCollector(track_individual=True)

    collector.record_request("https://example.com", "example.com")
    collector.record_response(
        "https://example.com",
        RequestStatus.SUCCESS,
        response_code=200,
        response_time_ms=150.0,
    )

    assert len(collector._metrics.requests) == 1
    assert collector._metrics.requests[0].url == "https://example.com"
    assert collector._metrics.requests[0].status == RequestStatus.SUCCESS


def test_track_individual_metric_disabled():
    """Test individual request metrics are not tracked when disabled."""
    collector = MetricsCollector(track_individual=False)

    collector.record_request("https://example.com", "example.com")
    collector.record_response(
        "https://example.com",
        RequestStatus.SUCCESS,
    )

    assert len(collector._metrics.requests) == 0


# =============================================================================
# SESSION REPORT GENERATOR TESTS
# =============================================================================


def test_generate_from_metrics():
    """Test generate creates SessionReport from RunMetrics."""
    generator = SessionReportGenerator()

    start = datetime.now()
    end = start + timedelta(minutes=5)
    metrics = RunMetrics(
        run_id="test_run",
        start_time=start,
        end_time=end,
        total_requests=100,
        successful=95,
        failed=3,
        blocked=2,
    )
    metrics.response_times = [100.0, 150.0, 200.0]

    report = generator.generate(metrics)

    assert isinstance(report, SessionReport)
    assert report.run_id == "test_run"
    assert report.total_urls == 100
    assert report.successful == 95
    assert report.success_rate == 95.0


def test_generate_calculates_percentiles():
    """Test generate calculates p50, p95, p99 response times."""
    generator = SessionReportGenerator()

    metrics = RunMetrics(
        run_id="test_run",
        start_time=datetime.now(),
        total_requests=10,
        successful=10,
    )
    # Response times: 100, 200, 300, ..., 1000
    metrics.response_times = [float(i * 100) for i in range(1, 11)]

    report = generator.generate(metrics)

    assert report.p50_response_time_ms > 0
    assert report.p95_response_time_ms > report.p50_response_time_ms
    assert report.p99_response_time_ms > report.p95_response_time_ms


def test_generate_builds_domain_breakdown():
    """Test generate builds per-domain statistics."""
    generator = SessionReportGenerator()

    metrics = RunMetrics(
        run_id="test_run",
        start_time=datetime.now(),
        total_requests=20,
        successful=18,
    )
    metrics.domain_stats = {
        "imot.bg": {
            "total": 10,
            "successful": 9,
            "failed": 1,
            "response_times": [100.0, 150.0, 200.0],
        },
        "homes.bg": {
            "total": 10,
            "successful": 9,
            "failed": 1,
            "response_times": [120.0, 160.0],
        },
    }

    report = generator.generate(metrics)

    assert "imot.bg" in report.domain_breakdown
    assert "homes.bg" in report.domain_breakdown

    imot = report.domain_breakdown["imot.bg"]
    assert imot["total"] == 10
    assert imot["successful"] == 9
    assert imot["success_rate"] == 90.0
    assert imot["avg_response_ms"] > 0


def test_generate_assesses_health():
    """Test generate assesses health_status and health_issues."""
    generator = SessionReportGenerator()

    # Healthy metrics
    metrics = RunMetrics(
        run_id="test_run",
        start_time=datetime.now(),
        total_requests=100,
        successful=95,
        failed=5,
    )
    metrics.response_times = [100.0] * 100

    report = generator.generate(metrics)

    assert report.health_status in ["healthy", "degraded", "critical"]
    assert isinstance(report.health_issues, list)


def test_save_creates_json_file(tmp_path):
    """Test save creates JSON file in reports directory."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    start = datetime(2025, 1, 15, 10, 30, 0)
    report = SessionReport(
        run_id="test_run",
        start_time=start.isoformat(),
        end_time=start.isoformat(),
        duration_seconds=300.0,
        total_urls=100,
        successful=95,
        failed=5,
        success_rate=95.0,
        status_breakdown={"success": 95, "failed": 5},
        domain_breakdown={},
        error_breakdown={},
        top_errors=[],
        avg_response_time_ms=150.0,
        p50_response_time_ms=140.0,
        p95_response_time_ms=200.0,
        p99_response_time_ms=250.0,
        health_status="healthy",
        health_issues=[],
    )

    filepath = generator.save(report)

    assert filepath.exists()
    assert filepath.parent == tmp_path


def test_save_filename_format(tmp_path):
    """Test save uses correct filename pattern session_YYYYMMDD_HHMMSS.json."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    start = datetime(2025, 1, 15, 10, 30, 45)
    report = SessionReport(
        run_id="test_run",
        start_time=start.isoformat(),
        end_time=start.isoformat(),
        duration_seconds=300.0,
        total_urls=100,
        successful=95,
        failed=5,
        success_rate=95.0,
        status_breakdown={},
        domain_breakdown={},
        error_breakdown={},
        top_errors=[],
        avg_response_time_ms=150.0,
        p50_response_time_ms=140.0,
        p95_response_time_ms=200.0,
        p99_response_time_ms=250.0,
        health_status="healthy",
        health_issues=[],
    )

    filepath = generator.save(report)

    assert filepath.name == "session_20250115_103045.json"


def test_load_returns_session_report(tmp_path):
    """Test load returns SessionReport from saved file."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    start = datetime(2025, 1, 15, 10, 30, 0)
    original_report = SessionReport(
        run_id="test_run",
        start_time=start.isoformat(),
        end_time=start.isoformat(),
        duration_seconds=300.0,
        total_urls=100,
        successful=95,
        failed=5,
        success_rate=95.0,
        status_breakdown={"success": 95},
        domain_breakdown={},
        error_breakdown={},
        top_errors=[],
        avg_response_time_ms=150.0,
        p50_response_time_ms=140.0,
        p95_response_time_ms=200.0,
        p99_response_time_ms=250.0,
        health_status="healthy",
        health_issues=[],
    )

    filepath = generator.save(original_report)
    loaded_report = generator.load(filepath)

    assert loaded_report.run_id == original_report.run_id
    assert loaded_report.total_urls == original_report.total_urls
    assert loaded_report.success_rate == original_report.success_rate


def test_get_recent_reports(tmp_path):
    """Test get_recent_reports loads N most recent, sorted."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    # Create 3 reports with different timestamps
    for i in range(3):
        start = datetime(2025, 1, 15, 10, i, 0)
        report = SessionReport(
            run_id=f"run_{i}",
            start_time=start.isoformat(),
            end_time=start.isoformat(),
            duration_seconds=300.0,
            total_urls=100,
            successful=95,
            failed=5,
            success_rate=95.0,
            status_breakdown={},
            domain_breakdown={},
            error_breakdown={},
            top_errors=[],
            avg_response_time_ms=150.0,
            p50_response_time_ms=140.0,
            p95_response_time_ms=200.0,
            p99_response_time_ms=250.0,
            health_status="healthy",
            health_issues=[],
        )
        generator.save(report)

    recent = generator.get_recent_reports(limit=2)

    assert len(recent) == 2
    # Should be newest first
    assert recent[0].run_id == "run_2"
    assert recent[1].run_id == "run_1"


def test_calculate_baseline(tmp_path):
    """Test calculate_baseline averages from recent reports."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    # Create reports within the last 7 days
    now = datetime.now()
    for i in range(3):
        start = now - timedelta(days=i)
        report = SessionReport(
            run_id=f"run_{i}",
            start_time=start.isoformat(),
            end_time=start.isoformat(),
            duration_seconds=300.0,
            total_urls=100 + i * 10,  # 100, 110, 120
            successful=90 + i,  # 90, 91, 92
            failed=10 - i,  # 10, 9, 8
            success_rate=90.0 + i,  # 90%, 91%, 92%
            status_breakdown={},
            domain_breakdown={},
            error_breakdown={},
            top_errors=[],
            avg_response_time_ms=150.0 + i * 10,  # 150, 160, 170
            p50_response_time_ms=140.0,
            p95_response_time_ms=200.0 + i * 10,  # 200, 210, 220
            p99_response_time_ms=250.0,
            health_status="healthy",
            health_issues=[],
        )
        generator.save(report)

    baseline = generator.calculate_baseline(days=7)

    assert baseline["report_count"] == 3
    assert baseline["success_rate"] == pytest.approx(91.0, rel=0.1)
    assert baseline["avg_response_ms"] == pytest.approx(160.0, rel=0.1)
    assert "calculated_at" in baseline


def test_calculate_baseline_empty_reports(tmp_path):
    """Test calculate_baseline returns empty dict when no reports."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    baseline = generator.calculate_baseline(days=7)

    assert baseline == {}


def test_compare_to_baseline(tmp_path):
    """Test compare_to_baseline calculates delta values."""
    generator = SessionReportGenerator(reports_dir=tmp_path)

    baseline = {
        "success_rate": 90.0,
        "avg_response_ms": 150.0,
        "p95_response_ms": 200.0,
        "total_urls_avg": 100.0,
        "report_count": 5,
    }

    start = datetime.now()
    report = SessionReport(
        run_id="test_run",
        start_time=start.isoformat(),
        end_time=start.isoformat(),
        duration_seconds=300.0,
        total_urls=120,
        successful=110,
        failed=10,
        success_rate=95.0,
        status_breakdown={},
        domain_breakdown={},
        error_breakdown={},
        top_errors=[],
        avg_response_time_ms=160.0,
        p50_response_time_ms=140.0,
        p95_response_time_ms=210.0,
        p99_response_time_ms=250.0,
        health_status="healthy",
        health_issues=[],
    )

    comparison = generator.compare_to_baseline(report, baseline)

    assert comparison["success_rate_delta"] == pytest.approx(5.0, rel=0.1)
    assert comparison["avg_response_delta"] == pytest.approx(10.0, rel=0.1)
    assert comparison["p95_response_delta"] == pytest.approx(10.0, rel=0.1)
    assert comparison["total_urls_delta"] == pytest.approx(20.0, rel=0.1)
    assert comparison["baseline_report_count"] == 5


def test_compare_to_baseline_empty_baseline():
    """Test compare_to_baseline returns empty dict when no baseline."""
    generator = SessionReportGenerator()

    start = datetime.now()
    report = SessionReport(
        run_id="test_run",
        start_time=start.isoformat(),
        end_time=start.isoformat(),
        duration_seconds=300.0,
        total_urls=100,
        successful=95,
        failed=5,
        success_rate=95.0,
        status_breakdown={},
        domain_breakdown={},
        error_breakdown={},
        top_errors=[],
        avg_response_time_ms=150.0,
        p50_response_time_ms=140.0,
        p95_response_time_ms=200.0,
        p99_response_time_ms=250.0,
        health_status="healthy",
        health_issues=[],
    )

    comparison = generator.compare_to_baseline(report, {})

    assert comparison == {}


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


def test_calculate_percentile_p50():
    """Test calculate_percentile returns correct p50 value."""
    values = [100.0, 200.0, 300.0, 400.0, 500.0]
    p50 = _calculate_percentile(values, 50)

    assert p50 == pytest.approx(300.0, rel=0.1)


def test_calculate_percentile_p95():
    """Test calculate_percentile returns correct p95 value."""
    values = [float(i) for i in range(1, 101)]  # 1 to 100
    p95 = _calculate_percentile(values, 95)

    assert p95 >= 95.0


def test_calculate_percentile_p99():
    """Test calculate_percentile returns correct p99 value."""
    values = [float(i) for i in range(1, 101)]  # 1 to 100
    p99 = _calculate_percentile(values, 99)

    assert p99 >= 99.0


def test_calculate_percentile_empty_list():
    """Test calculate_percentile returns 0.0 for empty list."""
    assert _calculate_percentile([], 50) == 0.0
    assert _calculate_percentile([], 95) == 0.0
    assert _calculate_percentile([], 99) == 0.0


def test_calculate_percentile_single_value():
    """Test calculate_percentile with single value."""
    assert _calculate_percentile([100.0], 50) == 100.0
    assert _calculate_percentile([100.0], 95) == 100.0


def test_assess_health_all_good():
    """Test assess_health returns healthy with no issues."""
    status, issues = _assess_health(
        success_rate=95.0,
        error_rate=2.0,
        block_rate=1.0,
        avg_response_ms=1000.0,
    )

    assert status == "healthy"
    assert len(issues) == 0


def test_assess_health_with_issues():
    """Test assess_health returns issues list when metrics degraded."""
    status, issues = _assess_health(
        success_rate=70.0,  # Below healthy threshold
        error_rate=20.0,  # High error rate
        block_rate=1.0,
        avg_response_ms=1000.0,
    )

    assert status in ["degraded", "critical"]
    assert len(issues) > 0
    assert any("success rate" in issue.lower() for issue in issues)


def test_assess_health_slow_response():
    """Test assess_health detects slow response times."""
    status, issues = _assess_health(
        success_rate=95.0,
        error_rate=2.0,
        block_rate=1.0,
        avg_response_ms=6000.0,  # Very slow
    )

    assert status in ["degraded", "critical"]
    assert any("response time" in issue.lower() for issue in issues)


def test_assess_health_high_block_rate():
    """Test assess_health detects high block rate."""
    status, issues = _assess_health(
        success_rate=95.0,
        error_rate=2.0,
        block_rate=10.0,  # High block rate
        avg_response_ms=1000.0,
    )

    assert status in ["degraded", "critical"]
    assert any("block rate" in issue.lower() for issue in issues)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_full_workflow_metrics_to_report(tmp_path):
    """Test complete workflow from metrics collection to report generation."""
    # Collect metrics
    collector = MetricsCollector(run_id="integration_test")

    for i in range(10):
        collector.record_request(f"https://example.com/{i}", "example.com")
        status = RequestStatus.SUCCESS if i < 9 else RequestStatus.FAILED
        collector.record_response(
            f"https://example.com/{i}",
            status,
            response_time_ms=100.0 + i * 10,
        )

    collector.record_listing_saved("https://example.com/0", "listing_0")

    metrics = collector.end_run()

    # Generate report
    generator = SessionReportGenerator(reports_dir=tmp_path)
    report = generator.generate(metrics)

    assert report.run_id == "integration_test"
    assert report.total_urls == 10
    assert report.successful == 9
    assert report.success_rate == 90.0

    # Save and load
    filepath = generator.save(report)
    loaded_report = generator.load(filepath)

    assert loaded_report.run_id == report.run_id
    assert loaded_report.success_rate == report.success_rate


def test_domain_stats_with_response_times():
    """Test domain statistics include response time percentiles."""
    generator = SessionReportGenerator()

    metrics = RunMetrics(
        run_id="test_run",
        start_time=datetime.now(),
        total_requests=5,
        successful=5,
    )
    metrics.domain_stats = {
        "example.com": {
            "total": 5,
            "successful": 5,
            "failed": 0,
            "response_times": [100.0, 200.0, 300.0, 400.0, 500.0],
        },
    }

    report = generator.generate(metrics)

    domain = report.domain_breakdown["example.com"]
    assert domain["avg_response_ms"] == pytest.approx(300.0, rel=0.1)
    assert domain["p95_response_ms"] > 0


def test_error_breakdown_with_top_errors():
    """Test error breakdown includes top errors with sample URLs."""
    generator = SessionReportGenerator()

    start = datetime.now()
    metrics = RunMetrics(
        run_id="test_run",
        start_time=start,
        total_requests=5,
        successful=2,
        failed=3,
    )
    metrics.error_counts = {
        "ConnectionError": 2,
        "TimeoutError": 1,
    }
    metrics.requests = [
        RequestMetric(
            url="https://example.com/1",
            domain="example.com",
            status=RequestStatus.FAILED,
            error_type="ConnectionError",
            timestamp=start,
        ),
        RequestMetric(
            url="https://example.com/2",
            domain="example.com",
            status=RequestStatus.TIMEOUT,
            error_type="TimeoutError",
            timestamp=start,
        ),
    ]

    report = generator.generate(metrics)

    assert report.error_breakdown["ConnectionError"] == 2
    assert report.error_breakdown["TimeoutError"] == 1
    assert len(report.top_errors) == 2
    assert report.top_errors[0]["error_type"] == "ConnectionError"
    assert report.top_errors[0]["count"] == 2
    assert "example.com/1" in report.top_errors[0]["sample_url"]
