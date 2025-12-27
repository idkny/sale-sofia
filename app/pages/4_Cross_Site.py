# app/pages/4_Cross_Site.py
"""Cross-site comparison page for duplicate detection and price discrepancies."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cross-Site Comparison", page_icon="🔄", layout="wide")

st.title("🔄 Cross-Site Comparison")
st.markdown("Compare listings for the same property across different sites")

try:
    from data.data_store_main import get_properties_with_multiple_sources, get_price_discrepancies
    from config.settings import PRICE_DISCREPANCY_THRESHOLD_PCT, PRICE_DISCREPANCY_HIGH_PCT

    # Get data
    multi_source_properties = get_properties_with_multiple_sources()

    # Sidebar filters
    st.sidebar.header("Filters")
    min_discrepancy = st.sidebar.slider(
        "Min Discrepancy %",
        min_value=0,
        max_value=50,
        value=int(PRICE_DISCREPANCY_THRESHOLD_PCT),
        step=1,
        help="Filter properties with price discrepancy above this percentage"
    )

    # Get unique neighborhoods from all sources
    all_neighborhoods = set()
    for prop in multi_source_properties:
        for source in prop.get("sources", []):
            # Extract neighborhood from URL if available (heuristic)
            pass  # Neighborhoods not directly available in sources

    # Get discrepancies with filter
    discrepancies = get_price_discrepancies(min_pct=float(min_discrepancy))

    # Calculate metrics
    total_multi_source = len(multi_source_properties)
    properties_with_discrepancy = len([p for p in multi_source_properties
                                       if p.get("price_discrepancy") and
                                       p["price_discrepancy"]["discrepancy_pct"] > PRICE_DISCREPANCY_THRESHOLD_PCT])

    if discrepancies:
        avg_discrepancy = sum(d["discrepancy_pct"] for d in discrepancies) / len(discrepancies)
        max_discrepancy = max(d["discrepancy_pct"] for d in discrepancies)
    else:
        avg_discrepancy = 0
        max_discrepancy = 0

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Properties on 2+ Sites", total_multi_source)

    with col2:
        st.metric("With >5% Discrepancy", properties_with_discrepancy)

    with col3:
        st.metric("Avg Discrepancy %", f"{avg_discrepancy:.1f}%" if avg_discrepancy else "N/A")

    with col4:
        st.metric("Max Discrepancy %", f"{max_discrepancy:.1f}%" if max_discrepancy else "N/A")

    st.markdown("---")

    # Main content - Price Discrepancies table
    st.subheader("📊 Price Discrepancies")

    if discrepancies:
        # Build table data
        table_data = []
        for disc in discrepancies:
            sites = ", ".join([s["source_site"] for s in disc["sources"]])
            table_data.append({
                "Fingerprint": disc["fingerprint"][:8],
                "Sites": sites,
                "Min Price": f"€{disc['min_price']:,.0f}",
                "Max Price": f"€{disc['max_price']:,.0f}",
                "Discrepancy %": disc["discrepancy_pct"],
                "_fingerprint_full": disc["fingerprint"],
                "_sources": disc["sources"],
            })

        df = pd.DataFrame(table_data)

        # Display table without internal columns
        display_df = df[["Fingerprint", "Sites", "Min Price", "Max Price", "Discrepancy %"]].copy()

        # Style rows with high discrepancy
        def highlight_high_discrepancy(row):
            if row["Discrepancy %"] > PRICE_DISCREPANCY_HIGH_PCT:
                return ["background-color: #ffcccc"] * len(row)
            return [""] * len(row)

        styled_df = display_df.style.apply(highlight_high_discrepancy, axis=1)
        styled_df = styled_df.format({"Discrepancy %": "{:.1f}%"})

        st.dataframe(
            styled_df,
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")

        # Expandable details for each property
        st.subheader("📋 Property Details")

        for disc in discrepancies:
            fingerprint_short = disc["fingerprint"][:8]
            sources = disc["sources"]

            # Find cheapest source
            prices_with_sites = [
                (s["source_site"], s["source_price_eur"])
                for s in sources
                if s["source_price_eur"] is not None
            ]

            if prices_with_sites:
                cheapest_site = min(prices_with_sites, key=lambda x: x[1])[0]
            else:
                cheapest_site = None

            with st.expander(
                f"**{fingerprint_short}** - {len(sources)} sources | "
                f"Discrepancy: {disc['discrepancy_pct']:.1f}%"
            ):
                # Sources table
                source_data = []
                for source in sources:
                    # Get first_seen and last_seen from the full property data
                    full_prop = next(
                        (p for p in multi_source_properties
                         if p["fingerprint"] == disc["fingerprint"]),
                        None
                    )

                    full_source = None
                    if full_prop:
                        full_source = next(
                            (s for s in full_prop["sources"]
                             if s["source_site"] == source["source_site"]),
                            None
                        )

                    first_seen = full_source.get("first_seen", "N/A") if full_source else "N/A"
                    last_seen = full_source.get("last_seen", "N/A") if full_source else "N/A"

                    # Format dates (remove time portion)
                    if first_seen and first_seen != "N/A":
                        first_seen = first_seen[:10]
                    if last_seen and last_seen != "N/A":
                        last_seen = last_seen[:10]

                    price = source.get("source_price_eur")
                    price_str = f"€{price:,.0f}" if price else "N/A"

                    url = full_source.get("source_url", "#") if full_source else "#"

                    source_data.append({
                        "Site": source["source_site"],
                        "Price": price_str,
                        "First Seen": first_seen,
                        "Last Seen": last_seen,
                        "URL": url,
                    })

                source_df = pd.DataFrame(source_data)

                # Display as table with links
                cols = st.columns([1, 1, 1, 1, 2])
                cols[0].markdown("**Site**")
                cols[1].markdown("**Price**")
                cols[2].markdown("**First Seen**")
                cols[3].markdown("**Last Seen**")
                cols[4].markdown("**Link**")

                for _, row in source_df.iterrows():
                    cols = st.columns([1, 1, 1, 1, 2])
                    cols[0].write(row["Site"])
                    cols[1].write(row["Price"])
                    cols[2].write(row["First Seen"])
                    cols[3].write(row["Last Seen"])
                    if row["URL"] != "#":
                        cols[4].markdown(f"[View Listing]({row['URL']})")
                    else:
                        cols[4].write("N/A")

                # Recommendation
                if cheapest_site:
                    st.info(f"**Recommendation:** Consider contacting **{cheapest_site}** first (lowest price)")
    else:
        st.info(
            f"No properties found with price discrepancy above {min_discrepancy}%. "
            "Try lowering the minimum discrepancy filter."
        )

    # Additional info section
    if total_multi_source == 0:
        st.markdown("---")
        st.warning(
            "No properties found on multiple sites yet. "
            "This may indicate:\n"
            "- Limited data has been scraped\n"
            "- No duplicate listings exist across sites\n"
            "- Property fingerprinting needs tuning"
        )

except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure all dependencies are installed.")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
