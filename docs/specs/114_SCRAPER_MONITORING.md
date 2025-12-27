# Spec 114: Scraper Monitoring & Observability

**Status**: Draft
**Author**: Instance 3
**Created**: 2025-12-27
**Priority**: P1 (Final project phase)

---

## Problem Statement

The scraper lacks visibility into its health and performance. Currently:
- Stats are printed to console but **not saved**
- No way to compare runs over time
- No aggregated error view (errors scattered in logs)
- No alert thresholds for degradation detection
- No dashboard showing scraper health

**Impact**: Cannot identify failing patterns, degrading proxies, or site-specific issues until complete failure.

---

## Goals

1. **Track**: Collect metrics during scrape runs
2. **Persist**: Save session reports for historical analysis
3. **Visualize**: Dashboard showing scraper health
4. **Alert**: Threshold-based indicators (not external alerts)

**Non-Goals**:
- External monitoring infrastructure (Prometheus/Grafana)
- Real-time alerting (Slack/email)
- Distributed tracing

---

## Design Principles

Following project motto: **Simplicity & Efficiency**

1. **File-based storage** - JSON reports in `data/reports/`
2. **Minimal dependencies** - Use existing libraries only
3. **Incremental adoption** - Works alongside existing code
4. **Single source of truth** - Metrics collector is authoritative

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      SCRAPING FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  main.py                                                    │
│     │                                                       │
│     ├──► MetricsCollector.start_run()                      │
│     │                                                       │
│     │    ┌─────────────────────────────────────────┐       │
│     │    │  For each URL:                          │       │
│     │    │    ├─► record_request(url, domain)      │       │
│     │    │    ├─► [fetch page]                     │       │
│     │    │    ├─► record_response(url, status, ms) │       │
│     │    │    ├─► [parse data]                     │       │
│     │    │    └─► record_result(url, success/fail) │       │
│     │    └─────────────────────────────────────────┘       │
│     │                                                       │
│     ├──► MetricsCollector.end_run()                        │
│     │                                                       │
│     └──► SessionReportGenerator.save()                     │
│              │                                              │
│              └──► data/reports/session_YYYYMMDD_HHMMSS.json│
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD VIEW                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  app/pages/5_Scraper_Health.py                             │
│     │                                                       │
│     ├──► Load reports from data/reports/                   │
│     ├──► Calculate trends (7-day moving average)           │
│     ├──► Display metrics tables and charts                 │
│     └──► Show health indicators (green/yellow/red)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. MetricsCollector (`scraping/metrics.py`)

Central class for collecting metrics during a scrape run.

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class RequestStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    SKIPPED = "skipped"

@dataclass
class RequestMetric:
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


class MetricsCollector:
    """Collects metrics during a scrape run."""

    def __init__(self, run_id: Optional[str] = None, track_individual: bool = True):
        """
        Args:
            run_id: Unique identifier for this run (auto-generated if None)
            track_individual: Whether to track individual request metrics
        """
        pass

    def start_run(self) -> None:
        """Mark the start of a scrape run."""
        pass

    def record_request(self, url: str, domain: str) -> None:
        """Record that a request is being made."""
        pass

    def record_response(
        self,
        url: str,
        status: RequestStatus,
        response_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record the result of a request."""
        pass

    def record_listing_saved(self, url: str, listing_id: str) -> None:
        """Record that a listing was successfully saved."""
        pass

    def record_listing_skipped(self, url: str, reason: str) -> None:
        """Record that a listing was skipped (duplicate, unchanged, etc.)."""
        pass

    def end_run(self) -> RunMetrics:
        """Mark the end of a scrape run and return final metrics."""
        pass

    def get_current_stats(self) -> Dict:
        """Get current stats mid-run (for progress display)."""
        pass

    @property
    def success_rate(self) -> float:
        """Calculate current success rate as percentage."""
        pass

    @property
    def health_status(self) -> str:
        """Return 'healthy', 'degraded', or 'critical' based on thresholds."""
        pass
```

### 2. SessionReportGenerator (`scraping/session_report.py`)

Generates and saves structured session reports.

```python
from pathlib import Path
from typing import Optional
import json

@dataclass
class SessionReport:
    """Complete report for a scrape session."""

    # Run identification
    run_id: str
    start_time: str  # ISO format
    end_time: str
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
    # Example: {"imot.bg": {"total": 100, "success": 95, "failed": 5, "avg_response_ms": 450}}

    # Error analysis
    error_breakdown: Dict[str, int]
    top_errors: List[Dict]  # [{error_type, count, sample_url}]

    # Performance metrics
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float

    # Proxy metrics (from proxy_scorer)
    proxy_stats: Dict
    # Example: {"total": 50, "active": 45, "avg_score": 0.8, "top_5": [...], "bottom_5": [...]}

    # Circuit breaker states
    circuit_states: Dict[str, str]
    # Example: {"imot.bg": "closed", "bazar.bg": "half_open"}

    # Health assessment
    health_status: str  # "healthy", "degraded", "critical"
    health_issues: List[str]  # ["High error rate on bazar.bg (15%)", "3 proxies removed"]

    # Comparison to baseline (if available)
    vs_baseline: Optional[Dict]
    # Example: {"success_rate_delta": -5.2, "avg_response_delta": +120}


class SessionReportGenerator:
    """Generates and persists session reports."""

    def __init__(self, reports_dir: Path):
        """
        Args:
            reports_dir: Directory to save reports (default: data/reports/)
        """
        pass

    def generate(
        self,
        metrics: RunMetrics,
        proxy_stats: Optional[Dict] = None,
        circuit_states: Optional[Dict] = None
    ) -> SessionReport:
        """Generate a complete session report from run metrics."""
        pass

    def save(self, report: SessionReport) -> Path:
        """Save report to JSON file. Returns path to saved file."""
        pass

    def load(self, report_path: Path) -> SessionReport:
        """Load a report from file."""
        pass

    def get_recent_reports(self, limit: int = 30) -> List[SessionReport]:
        """Load the N most recent reports."""
        pass

    def calculate_baseline(self, days: int = 7) -> Dict:
        """Calculate baseline metrics from last N days of reports."""
        pass

    def compare_to_baseline(self, report: SessionReport, baseline: Dict) -> Dict:
        """Compare a report to baseline metrics."""
        pass
```

### 3. Health Thresholds (`config/settings.py`)

Add to existing settings file:

```python
# =============================================================================
# SCRAPER MONITORING SETTINGS
# =============================================================================

# Health status thresholds
SCRAPER_HEALTH_THRESHOLDS = {
    "success_rate": {
        "healthy": 90.0,      # >= 90% is healthy
        "degraded": 75.0,     # >= 75% is degraded, < 75% is critical
    },
    "error_rate": {
        "healthy": 5.0,       # <= 5% is healthy
        "degraded": 15.0,     # <= 15% is degraded, > 15% is critical
    },
    "block_rate": {
        "healthy": 2.0,       # <= 2% is healthy
        "degraded": 5.0,      # <= 5% is degraded, > 5% is critical
    },
    "avg_response_ms": {
        "healthy": 2000,      # <= 2s is healthy
        "degraded": 5000,     # <= 5s is degraded, > 5s is critical
    },
}

# Alert thresholds (for dashboard indicators)
SCRAPER_ALERT_THRESHOLDS = {
    "min_proxies": 10,              # Alert if proxy count drops below
    "max_consecutive_failures": 5,  # Alert after N consecutive failures
    "baseline_deviation": 20.0,     # Alert if >20% worse than 7-day baseline
}

# Report retention
SCRAPER_REPORTS_RETENTION_DAYS = 30
SCRAPER_REPORTS_DIR = "data/reports"
```

### 4. Dashboard Page (`app/pages/5_Scraper_Health.py`)

Streamlit page for visualizing scraper health.

**Layout**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  SCRAPER HEALTH DASHBOARD                              [Refresh]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ SUCCESS RATE │ │  ERROR RATE  │ │  BLOCK RATE  │ │  AVG RESP  │ │
│  │    92.5%     │ │     4.2%     │ │     1.8%     │ │   1.2s     │ │
│  │   [GREEN]    │ │   [GREEN]    │ │   [GREEN]    │ │  [GREEN]   │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  LAST RUN: 2025-12-27 14:30:00 | Duration: 45m | URLs: 1,234       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SUCCESS RATE TREND (Last 30 Days)                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  100% ─┬──────────────────────────────────────────────────    │ │
│  │   90% ─┤  ████████████████████  ██████████████████████████    │ │
│  │   80% ─┤                      ██                              │ │
│  │   70% ─┤                                                      │ │
│  │        └──────────────────────────────────────────────────    │ │
│  │          Dec 1                Dec 15               Dec 27     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DOMAIN HEALTH                           ERROR BREAKDOWN            │
│  ┌─────────────────────────────┐        ┌─────────────────────────┐│
│  │ Domain    │ Success │ Avg   │        │ Error Type    │ Count   ││
│  │───────────┼─────────┼───────│        │───────────────┼─────────││
│  │ imot.bg   │  95.2%  │ 1.1s  │        │ TIMEOUT       │   23    ││
│  │ bazar.bg  │  88.1%  │ 1.8s  │        │ PARSE_ERROR   │   12    ││
│  │───────────┼─────────┼───────│        │ BLOCKED       │    8    ││
│  │ TOTAL     │  92.5%  │ 1.2s  │        │ HTTP_ERROR    │    5    ││
│  └─────────────────────────────┘        └─────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PROXY HEALTH                            CIRCUIT BREAKERS           │
│  ┌─────────────────────────────┐        ┌─────────────────────────┐│
│  │ Active Proxies: 45/50       │        │ imot.bg    │ [CLOSED]  ││
│  │ Avg Score: 0.82             │        │ bazar.bg   │ [CLOSED]  ││
│  │                             │        │                         ││
│  │ Top 3:                      │        │ All circuits healthy    ││
│  │  • 192.168.1.1 (0.95)      │        │                         ││
│  │  • 192.168.1.2 (0.92)      │        │                         ││
│  │  • 192.168.1.3 (0.89)      │        │                         ││
│  │                             │        │                         ││
│  │ Bottom 3 (watch):           │        │                         ││
│  │  • 192.168.1.48 (0.12)     │        │                         ││
│  │  • 192.168.1.49 (0.08)     │        │                         ││
│  │  • 192.168.1.50 (0.05)     │        │                         ││
│  └─────────────────────────────┘        └─────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RUN HISTORY (Last 10 Runs)                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Date       │ Duration │ URLs  │ Success │ Errors │ Status    │ │
│  │────────────┼──────────┼───────┼─────────┼────────┼───────────│ │
│  │ 12-27 14:30│   45m    │ 1,234 │  92.5%  │   48   │ [GREEN]   │ │
│  │ 12-27 08:00│   42m    │ 1,198 │  94.1%  │   35   │ [GREEN]   │ │
│  │ 12-26 20:00│   51m    │ 1,302 │  87.2%  │   89   │ [YELLOW]  │ │
│  │ 12-26 14:00│   44m    │ 1,215 │  93.8%  │   41   │ [GREEN]   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Features**:
1. **Health Cards**: Color-coded metrics (green/yellow/red)
2. **Trend Chart**: Success rate over time with 7-day moving average
3. **Domain Table**: Per-site performance breakdown
4. **Error Breakdown**: Top error types with counts
5. **Proxy Health**: Active count, scores, top/bottom performers
6. **Circuit States**: Current state of each domain's circuit breaker
7. **Run History**: Recent runs with key metrics

---

## Integration Points

### 1. main.py Integration

```python
# At start of scrape_site()
from scraping.metrics import MetricsCollector, RequestStatus
from scraping.session_report import SessionReportGenerator

metrics = MetricsCollector(run_id=f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
metrics.start_run()

# In the scraping loop
for url in urls:
    start_time = time.time()
    metrics.record_request(url, domain)

    try:
        response = await fetch(url)
        response_time = (time.time() - start_time) * 1000

        if response.ok:
            metrics.record_response(url, RequestStatus.SUCCESS,
                                   response.status_code, response_time)
            # ... parse and save
            metrics.record_listing_saved(url, listing_id)
        else:
            metrics.record_response(url, RequestStatus.FAILED,
                                   response.status_code, response_time)
    except TimeoutError:
        metrics.record_response(url, RequestStatus.TIMEOUT,
                               error_type="NETWORK_TIMEOUT")
    except BlockedError:
        metrics.record_response(url, RequestStatus.BLOCKED,
                               error_type="HTTP_BLOCKED")

# At end of scrape
run_metrics = metrics.end_run()

# Generate and save report
report_gen = SessionReportGenerator(Path(SCRAPER_REPORTS_DIR))
report = report_gen.generate(
    metrics=run_metrics,
    proxy_stats=proxy_scorer.get_stats(),
    circuit_states=circuit_breaker.get_all_states()
)
report_path = report_gen.save(report)
logger.info(f"Session report saved: {report_path}")
```

### 2. Circuit Breaker Integration

Add method to `resilience/circuit_breaker.py`:

```python
def get_all_states(self) -> Dict[str, Dict]:
    """Export all circuit breaker states for reporting."""
    return {
        domain: {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
            "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None,
            "block_type": cb.block_type
        }
        for domain, cb in self._breakers.items()
    }
```

### 3. Proxy Scorer Integration

Add method to `proxies/proxy_scorer.py`:

```python
def get_stats(self) -> Dict:
    """Export proxy statistics for reporting."""
    scores = list(self._scores.values())
    sorted_proxies = sorted(self._scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "total": len(scores),
        "active": len([s for s in scores if s >= MIN_PROXY_SCORE]),
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "top_5": [{"proxy": p, "score": s} for p, s in sorted_proxies[:5]],
        "bottom_5": [{"proxy": p, "score": s} for p, s in sorted_proxies[-5:]],
    }
```

---

## File Structure

```
sale-sofia/
├── config/
│   └── settings.py              # Add SCRAPER_HEALTH_THRESHOLDS
├── scraping/
│   ├── __init__.py
│   ├── metrics.py               # NEW: MetricsCollector
│   └── session_report.py        # NEW: SessionReportGenerator
├── data/
│   └── reports/                 # NEW: Session report storage
│       └── session_20251227_143000.json
├── app/
│   └── pages/
│       └── 5_Scraper_Health.py  # NEW: Dashboard page
└── tests/
    └── test_scraper_monitoring.py  # NEW: Tests
```

---

## Report JSON Schema

```json
{
  "run_id": "scrape_20251227_143000",
  "start_time": "2025-12-27T14:30:00",
  "end_time": "2025-12-27T15:15:00",
  "duration_seconds": 2700,

  "summary": {
    "total_urls": 1234,
    "successful": 1142,
    "failed": 48,
    "skipped": 44,
    "success_rate": 92.5,
    "health_status": "healthy"
  },

  "status_breakdown": {
    "success": 1142,
    "failed": 23,
    "blocked": 8,
    "timeout": 12,
    "parse_error": 5,
    "skipped": 44
  },

  "domain_breakdown": {
    "imot.bg": {
      "total": 734,
      "successful": 698,
      "failed": 18,
      "success_rate": 95.2,
      "avg_response_ms": 1100,
      "p95_response_ms": 2300
    },
    "bazar.bg": {
      "total": 500,
      "successful": 444,
      "failed": 30,
      "success_rate": 88.1,
      "avg_response_ms": 1800,
      "p95_response_ms": 3500
    }
  },

  "error_breakdown": {
    "NETWORK_TIMEOUT": 12,
    "HTTP_BLOCKED": 8,
    "PARSE_ERROR": 5,
    "HTTP_SERVER_ERROR": 3
  },

  "performance": {
    "avg_response_ms": 1245,
    "p50_response_ms": 1100,
    "p95_response_ms": 2800,
    "p99_response_ms": 4200
  },

  "proxy_stats": {
    "total": 50,
    "active": 45,
    "avg_score": 0.82,
    "removed_this_run": 2
  },

  "circuit_states": {
    "imot.bg": "closed",
    "bazar.bg": "closed"
  },

  "health_issues": [],

  "vs_baseline": {
    "success_rate_delta": -1.2,
    "avg_response_delta": 45
  }
}
```

---

## Implementation Tasks

### Phase 1: Core Metrics (4 tasks)
- [ ] 1.1 Create `scraping/metrics.py` with MetricsCollector class
- [ ] 1.2 Create `scraping/session_report.py` with SessionReportGenerator
- [ ] 1.3 Add health thresholds to `config/settings.py`
- [ ] 1.4 Write unit tests for metrics and reports

### Phase 2: Integration (3 tasks)
- [ ] 2.1 Add `get_all_states()` to circuit_breaker.py
- [ ] 2.2 Add `get_stats()` to proxy_scorer.py
- [ ] 2.3 Integrate MetricsCollector into main.py scraping flow

### Phase 3: Dashboard (3 tasks)
- [ ] 3.1 Create `app/pages/5_Scraper_Health.py` with basic layout
- [ ] 3.2 Add trend charts (success rate over time)
- [ ] 3.3 Add health indicators and run history table

### Phase 4: Testing (2 tasks)
- [ ] 4.1 Integration test: full scrape with metrics collection
- [ ] 4.2 Dashboard test: verify report loading and display

---

## Testing Strategy

1. **Unit Tests**:
   - MetricsCollector: record/calculate/export
   - SessionReportGenerator: generate/save/load
   - Health threshold calculations

2. **Integration Tests**:
   - Mock scrape with metrics collection
   - Report generation with all components
   - Dashboard loads and displays data

3. **Manual Validation**:
   - Run real scrape, verify report generated
   - Check dashboard displays correctly

---

## Success Criteria

1. **Metrics collected**: Every scrape run produces a JSON report
2. **Reports persisted**: Reports saved to `data/reports/` with 30-day retention
3. **Dashboard functional**: Can view last 30 runs with trends
4. **Health visible**: Clear green/yellow/red indicators
5. **Actionable insights**: Can identify which domain/proxy is problematic

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance overhead | Slows scraping | Batch metrics writes, async where possible |
| Large report files | Disk usage | Limit individual request tracking, compress old reports |
| Dashboard slow to load | UX | Pagination, lazy loading, caching |

---

## Future Enhancements (Out of Scope)

- Real-time metrics streaming
- External alerting (Slack/email)
- Prometheus/Grafana integration
- API endpoints for health checks
- Automated remediation (restart on critical)

---

## References

- Research: Industry best practices for scraper monitoring
- Existing: `resilience/` module patterns
- Existing: `app/pages/1_Dashboard.py` (Streamlit patterns)
