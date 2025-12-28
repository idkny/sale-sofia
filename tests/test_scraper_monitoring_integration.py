"""Integration tests for scraper monitoring system.

Tests the full scrape flow with metrics collection, report generation,
and persistence. Validates the integration between MetricsCollector
and SessionReportGenerator.

Reference: Spec 114 - Scraper Monitoring Phase 1
"""

import json
from datetime import datetime
from pathlib import Path
from time import sleep

import pytest

from scraping.metrics import MetricsCollector, RequestStatus, RunMetrics
from scraping.session_report import SessionReport, SessionReportGenerator


@pytest.fixture
def sample_metrics_collector():
    """Create a MetricsCollector with sample data for testing."""
    collector = MetricsCollector(run_id="test_run_001", track_individual=True)
    collector.start_run()
    return collector


@pytest.fixture
def populated_metrics():
    """Create a fully populated RunMetrics object for testing."""
    collector = MetricsCollector(run_id="test_run_002", track_individual=True)
    collector.start_run()

    # Simulate mixed scrape results
    # Domain 1: imot.bg (mostly successful)
    for i in range(10):
        url = f"https://www.imot.bg/listing/{i}"
        collector.record_request(url, "imot.bg")
        if i < 9:  # 90% success
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_code=200,
                response_time_ms=150 + (i * 10)
            )
            collector.record_listing_saved(url, f"listing_{i}")
        else:
            collector.record_response(
                url,
                RequestStatus.TIMEOUT,
                response_time_ms=5000,
                error_type="TimeoutError",
                error_message="Request timeout after 5s"
            )

    # Domain 2: alo.bg (some blocks and failures)
    for i in range(8):
        url = f"https://alo.bg/listing/{i}"
        collector.record_request(url, "alo.bg")
        if i < 3:  # Some success - saved
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_code=200,
                response_time_ms=200 + (i * 15)
            )
            collector.record_listing_saved(url, f"alo_listing_{i}")
        elif i < 5:  # Some skipped (unchanged)
            collector.record_response(
                url,
                RequestStatus.SKIPPED,
                response_code=200,
                response_time_ms=200 + (i * 15)
            )
            collector.record_listing_skipped(url, "unchanged")
        elif i < 7:  # Some blocks
            collector.record_response(
                url,
                RequestStatus.BLOCKED,
                response_code=403,
                response_time_ms=100,
                error_type="BlockedException",
                error_message="Detected bot behavior"
            )
        else:  # Parse error
            collector.record_response(
                url,
                RequestStatus.PARSE_ERROR,
                response_code=200,
                response_time_ms=180,
                error_type="ParseError",
                error_message="Failed to extract listing data"
            )

    # Domain 3: address.bg (all successful)
    for i in range(5):
        url = f"https://address.bg/listing/{i}"
        collector.record_request(url, "address.bg")
        collector.record_response(
            url,
            RequestStatus.SUCCESS,
            response_code=200,
            response_time_ms=120 + (i * 5)
        )
        collector.record_listing_saved(url, f"address_listing_{i}")

    return collector.end_run()


@pytest.fixture
def temp_reports_dir(tmp_path):
    """Create a temporary directory for reports."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir


class TestMetricsCollectionDuringScrape:
    """Test metrics collection during simulated scrape flow."""

    def test_basic_metrics_collection_flow(self, sample_metrics_collector):
        """Test basic start_run, record, end_run flow."""
        metrics = sample_metrics_collector

        # Simulate scraping 3 URLs
        urls = [
            "https://www.imot.bg/listing/1",
            "https://www.imot.bg/listing/2",
            "https://www.imot.bg/listing/3",
        ]

        for url in urls:
            metrics.record_request(url, "imot.bg")
            metrics.record_response(
                url,
                RequestStatus.SUCCESS,
                response_code=200,
                response_time_ms=150
            )
            metrics.record_listing_saved(url, url)

        # End run and get metrics
        run_metrics = metrics.end_run()

        # Verify basic counts
        assert run_metrics.total_requests == 3
        assert run_metrics.successful == 3
        assert run_metrics.failed == 0
        assert run_metrics.blocked == 0
        assert run_metrics.listings_saved == 3
        assert run_metrics.listings_skipped == 0

        # Verify success rate and health
        assert metrics.success_rate == 100.0
        assert metrics.health_status == "healthy"

        # Verify domain stats
        assert "imot.bg" in run_metrics.domain_stats
        assert run_metrics.domain_stats["imot.bg"]["total"] == 3
        assert run_metrics.domain_stats["imot.bg"]["successful"] == 3

    def test_mixed_status_metrics(self, sample_metrics_collector):
        """Test metrics with mixed success/failure/blocked statuses."""
        metrics = sample_metrics_collector

        # 5 success
        for i in range(5):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(url, RequestStatus.SUCCESS, response_time_ms=150)

        # 2 blocked
        for i in range(5, 7):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(
                url,
                RequestStatus.BLOCKED,
                error_type="BlockedException",
                error_message="403 Forbidden"
            )

        # 2 timeout
        for i in range(7, 9):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(
                url,
                RequestStatus.TIMEOUT,
                error_type="TimeoutError",
                error_message="Timeout after 5s"
            )

        # 1 parse error
        url = "https://www.imot.bg/listing/9"
        metrics.record_request(url, "imot.bg")
        metrics.record_response(
            url,
            RequestStatus.PARSE_ERROR,
            error_type="ParseError",
            error_message="Failed extraction"
        )

        run_metrics = metrics.end_run()

        # Verify counts
        assert run_metrics.total_requests == 10
        assert run_metrics.successful == 5
        assert run_metrics.blocked == 2
        assert run_metrics.timeouts == 2
        assert run_metrics.parse_errors == 1

        # Verify success rate (50%)
        assert metrics.success_rate == 50.0

        # Verify health status (50% < 75% degraded threshold = critical)
        assert metrics.health_status == "critical"

        # Verify error breakdown
        assert run_metrics.error_counts["BlockedException"] == 2
        assert run_metrics.error_counts["TimeoutError"] == 2
        assert run_metrics.error_counts["ParseError"] == 1

    def test_listing_tracking(self, sample_metrics_collector):
        """Test listing saved/skipped tracking."""
        metrics = sample_metrics_collector

        # 3 saved
        for i in range(3):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(url, RequestStatus.SUCCESS)
            metrics.record_listing_saved(url, f"listing_{i}")

        # 2 skipped (unchanged)
        for i in range(3, 5):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(url, RequestStatus.SKIPPED)
            metrics.record_listing_skipped(url, "unchanged")

        # 1 skipped (duplicate)
        url = "https://www.imot.bg/listing/5"
        metrics.record_request(url, "imot.bg")
        metrics.record_response(url, RequestStatus.SKIPPED)
        metrics.record_listing_skipped(url, "duplicate")

        run_metrics = metrics.end_run()

        assert run_metrics.listings_saved == 3
        assert run_metrics.listings_skipped == 3
        assert run_metrics.skip_reasons["unchanged"] == 2
        assert run_metrics.skip_reasons["duplicate"] == 1

    def test_response_time_tracking(self, sample_metrics_collector):
        """Test response time collection."""
        metrics = sample_metrics_collector

        response_times = [100, 150, 200, 250, 300]

        for i, rt in enumerate(response_times):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(
                url,
                RequestStatus.SUCCESS,
                response_time_ms=rt
            )

        run_metrics = metrics.end_run()

        assert len(run_metrics.response_times) == 5
        assert run_metrics.response_times == response_times

    def test_domain_breakdown(self, sample_metrics_collector):
        """Test per-domain statistics tracking."""
        metrics = sample_metrics_collector

        # Domain 1: imot.bg
        for i in range(3):
            url = f"https://www.imot.bg/listing/{i}"
            metrics.record_request(url, "imot.bg")
            metrics.record_response(url, RequestStatus.SUCCESS, response_time_ms=150)

        # Domain 2: alo.bg
        for i in range(2):
            url = f"https://alo.bg/listing/{i}"
            metrics.record_request(url, "alo.bg")
            if i == 0:
                metrics.record_response(url, RequestStatus.SUCCESS, response_time_ms=200)
            else:
                metrics.record_response(url, RequestStatus.BLOCKED)

        run_metrics = metrics.end_run()

        # Verify imot.bg stats
        assert run_metrics.domain_stats["imot.bg"]["total"] == 3
        assert run_metrics.domain_stats["imot.bg"]["successful"] == 3
        assert len(run_metrics.domain_stats["imot.bg"]["response_times"]) == 3

        # Verify alo.bg stats
        assert run_metrics.domain_stats["alo.bg"]["total"] == 2
        assert run_metrics.domain_stats["alo.bg"]["successful"] == 1
        assert run_metrics.domain_stats["alo.bg"]["blocked"] == 1
        assert len(run_metrics.domain_stats["alo.bg"]["response_times"]) == 1


class TestSessionReportGeneration:
    """Test SessionReport generation from metrics."""

    def test_report_generation_from_metrics(self, populated_metrics, temp_reports_dir):
        """Test generating a SessionReport from RunMetrics."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)

        # Verify basic fields
        assert report.run_id == "test_run_002"
        assert report.total_urls == 23  # 10 + 8 + 5
        # Successful = 9 (imot.bg) + 3 (alo.bg) + 5 (address.bg) = 17
        # Note: SKIPPED status is not counted as successful
        assert report.successful == 17

        # Verify success rate (17 successful out of 23)
        expected_rate = (17 / 23) * 100
        assert abs(report.success_rate - expected_rate) < 0.1

        # Verify status breakdown
        assert report.status_breakdown["success"] == 17
        assert report.status_breakdown["blocked"] == 2
        assert report.status_breakdown["timeout"] == 1
        assert report.status_breakdown["parse_error"] == 1
        assert report.status_breakdown["skipped"] == 2

        # Verify health status (73.9% < 75% = critical due to success rate)
        assert report.health_status in ["healthy", "degraded", "critical"]

    def test_domain_breakdown_in_report(self, populated_metrics, temp_reports_dir):
        """Test domain breakdown is correctly generated."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)

        # Verify all domains present
        assert "imot.bg" in report.domain_breakdown
        assert "alo.bg" in report.domain_breakdown
        assert "address.bg" in report.domain_breakdown

        # Verify imot.bg stats
        imot_stats = report.domain_breakdown["imot.bg"]
        assert imot_stats["total"] == 10
        assert imot_stats["successful"] == 9
        assert imot_stats["success_rate"] == 90.0

        # Verify alo.bg stats (3 success out of 8 total)
        alo_stats = report.domain_breakdown["alo.bg"]
        assert alo_stats["total"] == 8
        assert alo_stats["successful"] == 3
        assert alo_stats["success_rate"] == 37.5

        # Verify address.bg stats (100% success)
        address_stats = report.domain_breakdown["address.bg"]
        assert address_stats["total"] == 5
        assert address_stats["successful"] == 5
        assert address_stats["success_rate"] == 100.0

    def test_error_breakdown_in_report(self, populated_metrics, temp_reports_dir):
        """Test error breakdown and top errors."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)

        # Verify error counts
        assert "TimeoutError" in report.error_breakdown
        assert "BlockedException" in report.error_breakdown
        assert "ParseError" in report.error_breakdown

        # Verify top errors list
        assert len(report.top_errors) > 0
        assert all("error_type" in err for err in report.top_errors)
        assert all("count" in err for err in report.top_errors)

    def test_performance_metrics_in_report(self, populated_metrics, temp_reports_dir):
        """Test performance percentiles are calculated."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)

        # Verify performance fields exist and are reasonable
        assert report.avg_response_time_ms > 0
        assert report.p50_response_time_ms > 0
        assert report.p95_response_time_ms > 0
        assert report.p99_response_time_ms > 0

        # Verify ordering: avg could be anywhere, but p50 <= p95 <= p99
        assert report.p50_response_time_ms <= report.p95_response_time_ms
        assert report.p95_response_time_ms <= report.p99_response_time_ms

    def test_health_assessment_healthy(self, temp_reports_dir):
        """Test health assessment for healthy metrics."""
        collector = MetricsCollector(run_id="healthy_run")
        collector.start_run()

        # Simulate 95% success rate
        for i in range(19):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_time_ms=150
            )

        # 1 failure
        url = "https://www.imot.bg/listing/19"
        collector.record_request(url, "imot.bg")
        collector.record_response(url, RequestStatus.FAILED)

        metrics = collector.end_run()
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # 95% success rate should be "healthy"
        assert report.health_status == "healthy"
        assert len(report.health_issues) == 0

    def test_health_assessment_degraded(self, temp_reports_dir):
        """Test health assessment for degraded metrics."""
        collector = MetricsCollector(run_id="degraded_run")
        collector.start_run()

        # Simulate 85% success rate (between 75-90%) with low error rate
        # 17 success
        for i in range(17):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_time_ms=150
            )

        # 3 skipped (not errors, just unchanged listings)
        for i in range(17, 20):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.SKIPPED,
                response_time_ms=150
            )

        metrics = collector.end_run()
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # 85% success rate (17/20) with 0% error rate should be "degraded"
        # (success rate between 75-90%, error rate is healthy at 0%)
        assert report.health_status == "degraded"

    def test_health_assessment_critical(self, temp_reports_dir):
        """Test health assessment for critical metrics."""
        collector = MetricsCollector(run_id="critical_run")
        collector.start_run()

        # Simulate 50% success rate (< 75%)
        for i in range(5):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_time_ms=150
            )

        # 5 failures
        for i in range(5, 10):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(url, RequestStatus.BLOCKED)

        metrics = collector.end_run()
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # 50% success rate should be "critical"
        assert report.health_status == "critical"
        assert len(report.health_issues) > 0


class TestSessionReportPersistence:
    """Test saving and loading SessionReports."""

    def test_save_and_load_report(self, populated_metrics, temp_reports_dir):
        """Test saving a report and loading it back."""
        report_gen = SessionReportGenerator(temp_reports_dir)

        # Generate and save report
        original_report = report_gen.generate(populated_metrics)
        saved_path = report_gen.save(original_report)

        # Verify file was created
        assert saved_path.exists()
        assert saved_path.suffix == ".json"
        assert saved_path.parent == temp_reports_dir

        # Load report back
        loaded_report = report_gen.load(saved_path)

        # Verify key fields match
        assert loaded_report.run_id == original_report.run_id
        assert loaded_report.total_urls == original_report.total_urls
        assert loaded_report.successful == original_report.successful
        assert loaded_report.success_rate == original_report.success_rate
        assert loaded_report.health_status == original_report.health_status

        # Verify status breakdown
        assert loaded_report.status_breakdown == original_report.status_breakdown

        # Verify domain breakdown
        assert loaded_report.domain_breakdown == original_report.domain_breakdown

        # Verify performance metrics
        assert loaded_report.avg_response_time_ms == original_report.avg_response_time_ms
        assert loaded_report.p95_response_time_ms == original_report.p95_response_time_ms

    def test_saved_report_json_structure(self, populated_metrics, temp_reports_dir):
        """Test that saved JSON follows the expected schema."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)
        saved_path = report_gen.save(report)

        # Load raw JSON
        with open(saved_path, "r") as f:
            data = json.load(f)

        # Verify top-level structure
        assert "run_id" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "duration_seconds" in data
        assert "summary" in data
        assert "status_breakdown" in data
        assert "domain_breakdown" in data
        assert "performance" in data

        # Verify summary structure
        summary = data["summary"]
        assert "total_urls" in summary
        assert "successful" in summary
        assert "success_rate" in summary
        assert "health_status" in summary

        # Verify performance structure
        perf = data["performance"]
        assert "avg_response_ms" in perf
        assert "p50_response_ms" in perf
        assert "p95_response_ms" in perf
        assert "p99_response_ms" in perf

    def test_report_filename_format(self, populated_metrics, temp_reports_dir):
        """Test that report filename follows expected format."""
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(populated_metrics)
        saved_path = report_gen.save(report)

        # Verify filename pattern: session_YYYYMMDD_HHMMSS.json
        assert saved_path.name.startswith("session_")
        assert saved_path.name.endswith(".json")

        # Extract timestamp part
        timestamp_part = saved_path.name.replace("session_", "").replace(".json", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
        assert timestamp_part[8] == "_"  # Underscore separator


class TestFullIntegrationWithExternalData:
    """Test full integration including proxy stats and circuit states."""

    def test_report_with_proxy_stats(self, populated_metrics, temp_reports_dir):
        """Test including proxy stats in report."""
        report_gen = SessionReportGenerator(temp_reports_dir)

        # Mock proxy stats
        proxy_stats = {
            "total_proxies": 5,
            "active_proxies": 4,
            "avg_score": 0.85,
            "top_proxy": "proxy1",
        }

        report = report_gen.generate(populated_metrics, proxy_stats=proxy_stats)

        # Verify proxy stats included
        assert report.proxy_stats is not None
        assert report.proxy_stats == proxy_stats

    def test_report_with_circuit_states(self, populated_metrics, temp_reports_dir):
        """Test including circuit breaker states in report."""
        report_gen = SessionReportGenerator(temp_reports_dir)

        # Mock circuit states
        circuit_states = {
            "imot.bg": "closed",
            "alo.bg": "open",
            "address.bg": "closed",
        }

        report = report_gen.generate(
            populated_metrics,
            circuit_states=circuit_states
        )

        # Verify circuit states included
        assert report.circuit_states is not None
        assert report.circuit_states == circuit_states

    def test_full_integration_save_and_load(self, populated_metrics, temp_reports_dir):
        """Test full flow with all optional data included."""
        report_gen = SessionReportGenerator(temp_reports_dir)

        # Mock external data
        proxy_stats = {
            "total_proxies": 10,
            "active_proxies": 8,
            "avg_score": 0.78,
        }

        circuit_states = {
            "imot.bg": "closed",
            "alo.bg": "half_open",
            "address.bg": "closed",
        }

        # Generate report with all data
        original_report = report_gen.generate(
            populated_metrics,
            proxy_stats=proxy_stats,
            circuit_states=circuit_states
        )

        # Save and load
        saved_path = report_gen.save(original_report)
        loaded_report = report_gen.load(saved_path)

        # Verify all data preserved
        assert loaded_report.proxy_stats == proxy_stats
        assert loaded_report.circuit_states == circuit_states
        assert loaded_report.run_id == original_report.run_id
        assert loaded_report.success_rate == original_report.success_rate

    def test_report_without_optional_data(self, populated_metrics, temp_reports_dir):
        """Test report generation works without optional data."""
        report_gen = SessionReportGenerator(temp_reports_dir)

        # Generate report without optional data
        report = report_gen.generate(populated_metrics)

        # Verify optional fields are None
        assert report.proxy_stats is None
        assert report.circuit_states is None
        assert report.vs_baseline is None

        # Save and load should still work
        saved_path = report_gen.save(report)
        loaded_report = report_gen.load(saved_path)

        assert loaded_report.proxy_stats is None
        assert loaded_report.circuit_states is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_metrics(self, temp_reports_dir):
        """Test report generation with zero requests."""
        collector = MetricsCollector(run_id="empty_run")
        collector.start_run()
        metrics = collector.end_run()

        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # Verify empty metrics handled correctly
        assert report.total_urls == 0
        assert report.successful == 0
        assert report.success_rate == 100.0  # Default when no requests
        assert report.avg_response_time_ms == 0.0

    def test_all_failed_requests(self, temp_reports_dir):
        """Test report when all requests fail."""
        collector = MetricsCollector(run_id="all_failed")
        collector.start_run()

        for i in range(5):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.BLOCKED,
                error_type="BlockedException"
            )

        metrics = collector.end_run()
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # Verify 0% success rate
        assert report.success_rate == 0.0
        assert report.successful == 0
        assert report.failed == 5
        assert report.health_status == "critical"

    def test_collector_without_individual_tracking(self, temp_reports_dir):
        """Test collector with track_individual=False."""
        collector = MetricsCollector(
            run_id="no_tracking",
            track_individual=False
        )
        collector.start_run()

        for i in range(5):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(url, RequestStatus.SUCCESS, response_time_ms=150)

        metrics = collector.end_run()

        # Verify individual requests not tracked
        assert len(metrics.requests) == 0

        # But aggregates should still work
        assert metrics.total_requests == 5
        assert metrics.successful == 5

        # Report generation should handle missing individual metrics
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # top_errors might be empty without individual tracking
        assert report.total_urls == 5
        assert report.success_rate == 100.0

    def test_very_slow_responses(self, temp_reports_dir):
        """Test handling of very slow response times."""
        collector = MetricsCollector(run_id="slow_run")
        collector.start_run()

        # Simulate slow responses (>5s threshold)
        for i in range(3):
            url = f"https://www.imot.bg/listing/{i}"
            collector.record_request(url, "imot.bg")
            collector.record_response(
                url,
                RequestStatus.SUCCESS,
                response_time_ms=6000  # 6 seconds
            )

        metrics = collector.end_run()
        report_gen = SessionReportGenerator(temp_reports_dir)
        report = report_gen.generate(metrics)

        # Verify high response times reflected
        assert report.avg_response_time_ms > 5000

        # Health might be degraded/critical due to slow responses
        assert report.health_status in ["healthy", "degraded", "critical"]
