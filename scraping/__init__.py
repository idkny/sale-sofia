"""Scraping module for async HTTP fetching and metrics collection."""

from scraping.async_fetcher import fetch_page, fetch_pages_concurrent
from scraping.metrics import (
    MetricsCollector,
    RequestMetric,
    RequestStatus,
    RunMetrics,
)
from scraping.session_report import SessionReport, SessionReportGenerator

__all__ = [
    # Async fetcher
    "fetch_page",
    "fetch_pages_concurrent",
    # Metrics
    "MetricsCollector",
    "RequestMetric",
    "RequestStatus",
    "RunMetrics",
    # Session reports
    "SessionReport",
    "SessionReportGenerator",
]
