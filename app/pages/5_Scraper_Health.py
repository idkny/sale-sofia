# app/pages/5_Scraper_Health.py
"""Scraper Health Dashboard - monitoring scraper performance and health status.

Reference: Spec 114 Phase 3 (Dashboard)
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

st.set_page_config(page_title="Scraper Health", page_icon="🔧", layout="wide")

st.title("Scraper Health Dashboard")
st.markdown("Monitor scraper performance, health metrics, and run history")

try:
    from config.settings import SCRAPER_HEALTH_THRESHOLDS
    from scraping.session_report import SessionReportGenerator

    # Load recent reports
    generator = SessionReportGenerator()
    reports = generator.get_recent_reports(limit=30)

    if not reports:
        st.info("No scraper reports found. Run the scraper to generate reports.")
    else:
        # Get the most recent report
        latest = reports[0]

        # Calculate error rate and block rate from status breakdown
        total = latest.total_urls if latest.total_urls > 0 else 1
        status = latest.status_breakdown
        error_count = status.get("failed", 0) + status.get("timeout", 0) + status.get("parse_error", 0)
        block_count = status.get("blocked", 0)
        error_rate = (error_count / total) * 100.0
        block_rate = (block_count / total) * 100.0

        # Health status helper
        def get_health_status(metric_name: str, value: float, higher_is_better: bool = True) -> str:
            """Determine health status for a metric."""
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

        def status_emoji(status: str) -> str:
            """Get emoji for health status."""
            return {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}.get(status, "⚪")

        # Health metric cards row
        st.markdown("### Health Metrics")
        col1, col2, col3, col4 = st.columns(4)

        # Success Rate
        success_status = get_health_status("success_rate", latest.success_rate, higher_is_better=True)
        with col1:
            st.metric(
                label=f"{status_emoji(success_status)} Success Rate",
                value=f"{latest.success_rate:.1f}%",
                delta="vs 90% baseline" if latest.success_rate >= 90 else f"{latest.success_rate - 90:.1f}% vs baseline",
                delta_color="normal" if latest.success_rate >= 90 else "inverse",
            )

        # Error Rate
        error_status = get_health_status("error_rate", error_rate, higher_is_better=False)
        with col2:
            st.metric(
                label=f"{status_emoji(error_status)} Error Rate",
                value=f"{error_rate:.1f}%",
                delta="vs 5% baseline" if error_rate <= 5 else f"+{error_rate - 5:.1f}% vs baseline",
                delta_color="normal" if error_rate <= 5 else "inverse",
            )

        # Block Rate
        block_status = get_health_status("block_rate", block_rate, higher_is_better=False)
        with col3:
            st.metric(
                label=f"{status_emoji(block_status)} Block Rate",
                value=f"{block_rate:.1f}%",
                delta="vs 2% baseline" if block_rate <= 2 else f"+{block_rate - 2:.1f}% vs baseline",
                delta_color="normal" if block_rate <= 2 else "inverse",
            )

        # Avg Response Time
        response_status = get_health_status("avg_response_ms", latest.avg_response_time_ms, higher_is_better=False)
        with col4:
            st.metric(
                label=f"{status_emoji(response_status)} Avg Response",
                value=f"{latest.avg_response_time_ms:.0f}ms",
                delta="vs 2000ms baseline" if latest.avg_response_time_ms <= 2000 else f"+{latest.avg_response_time_ms - 2000:.0f}ms vs baseline",
                delta_color="normal" if latest.avg_response_time_ms <= 2000 else "inverse",
            )

        st.markdown("---")

        # Last run info bar
        st.markdown("### Last Run Info")
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)

        with info_col1:
            st.markdown(f"**Run ID:** `{latest.run_id[:8]}...`" if len(latest.run_id) > 8 else f"**Run ID:** `{latest.run_id}`")

        with info_col2:
            st.markdown(f"**Date:** {latest.start_time[:19].replace('T', ' ')}")

        with info_col3:
            duration_mins = latest.duration_seconds / 60
            st.markdown(f"**Duration:** {duration_mins:.1f} min")

        with info_col4:
            st.markdown(f"**Total URLs:** {latest.total_urls}")

        # Overall health status
        st.markdown(f"**Overall Health:** {status_emoji(latest.health_status)} {latest.health_status.upper()}")
        if latest.health_issues:
            st.warning(f"Issues: {', '.join(latest.health_issues)}")

        st.markdown("---")

        # Trend charts (Phase 3.2)
        st.subheader("Trend Charts")

        if len(reports) < 2:
            st.info("Need at least 2 reports to show trends. Run more scraper sessions.")
        else:
            import pandas as pd

            # Prepare data: reverse to chronological order (oldest first)
            chronological = list(reversed(reports))

            # Build DataFrame
            trend_data = []
            for r in chronological:
                trend_data.append({
                    "time": r.start_time[:16].replace("T", " "),
                    "Success Rate (%)": r.success_rate,
                    "Avg Response (ms)": r.avg_response_time_ms,
                })
            df = pd.DataFrame(trend_data)
            df = df.set_index("time")

            # Two columns for side-by-side charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("**Success Rate Trend**")
                st.line_chart(df[["Success Rate (%)"]])

            with chart_col2:
                st.markdown("**Response Time Trend**")
                st.line_chart(df[["Avg Response (ms)"]])

        # Run History and Domain Health tables (Phase 3.3)
        st.subheader("Run History & Domain Health")

        table_col1, table_col2 = st.columns(2)

        # Domain Health Table (left column)
        with table_col1:
            st.markdown("**Domain Health (Latest Run)**")
            domain_breakdown = latest.domain_breakdown if hasattr(latest, "domain_breakdown") else {}

            if domain_breakdown:
                domain_data = []
                for domain, stats in domain_breakdown.items():
                    success_rate = stats.get("success_rate", 0.0)
                    avg_response = stats.get("avg_response_ms", 0)
                    domain_data.append({
                        "Domain": domain,
                        "Success Rate": f"{success_rate:.1f}%",
                        "Avg Response": f"{avg_response:.0f}ms",
                    })
                domain_df = pd.DataFrame(domain_data)
                st.dataframe(domain_df, use_container_width=True, hide_index=True)
            else:
                st.info("No domain breakdown available.")

        # Run History Table (right column)
        with table_col2:
            st.markdown("**Run History (Last 10 Runs)**")
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
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True, hide_index=True)

except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure all dependencies are installed.")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
