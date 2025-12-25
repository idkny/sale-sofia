# app/pages/1_Dashboard.py
"""Dashboard page with overview statistics and charts."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")
st.markdown("Overview of your apartment search progress")

try:
    from data.data_store_main import get_listings_stats, get_listings, get_shortlisted_listings
    from app.scoring import calculate_score, passes_all_deal_breakers, listing_to_dict

    # Get statistics
    stats = get_listings_stats()

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Listings", stats["total_active"])

    with col2:
        shortlisted = stats.get("by_decision", {}).get("Shortlist", 0)
        st.metric("Shortlisted", shortlisted)

    with col3:
        viewed = stats.get("by_status", {}).get("Viewed", 0)
        st.metric("Viewed", viewed)

    with col4:
        avg_price = stats["price"]["avg"]
        st.metric("Avg Price", f"€{avg_price:,.0f}" if avg_price else "N/A")

    with col5:
        avg_sqm = stats["price"]["avg_per_sqm"]
        st.metric("Avg €/sqm", f"€{avg_sqm:,.0f}" if avg_sqm else "N/A")

    st.markdown("---")

    # Two column layout for charts
    left_col, right_col = st.columns(2)

    with left_col:
        # Status distribution
        st.subheader("📋 Status Distribution")
        status_data = stats.get("by_status", {})
        if status_data:
            df_status = pd.DataFrame(
                list(status_data.items()),
                columns=["Status", "Count"]
            )
            st.bar_chart(df_status.set_index("Status"))
        else:
            st.info("No status data available")

        # Decision distribution
        st.subheader("🎯 Decisions Made")
        decision_data = stats.get("by_decision", {})
        if decision_data:
            df_decision = pd.DataFrame(
                list(decision_data.items()),
                columns=["Decision", "Count"]
            )
            st.bar_chart(df_decision.set_index("Decision"))
        else:
            st.info("No decisions recorded yet")

    with right_col:
        # District breakdown
        st.subheader("🗺️ Listings by District")
        district_data = stats.get("by_district", [])
        if district_data:
            df_district = pd.DataFrame(district_data)
            df_district = df_district.head(10)  # Top 10

            # Bar chart of counts
            st.bar_chart(df_district.set_index("district")["count"])

            # Table with avg price
            st.markdown("**Avg Price/sqm by District**")
            df_district["avg_sqm_price"] = df_district["avg_sqm_price"].apply(
                lambda x: f"€{x:,.0f}" if x else "N/A"
            )
            st.dataframe(
                df_district[["district", "count", "avg_sqm_price"]],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No district data available")

    st.markdown("---")

    # Shortlisted apartments section
    st.subheader("⭐ Shortlisted Apartments")

    shortlisted_listings = get_shortlisted_listings()

    if shortlisted_listings:
        for listing in shortlisted_listings:
            listing_dict = listing_to_dict(listing)
            score = calculate_score(listing_dict)
            passes, failed = passes_all_deal_breakers(listing_dict)

            with st.expander(
                f"**{listing['title'] or 'Untitled'}** - €{listing['price_eur']:,.0f} | "
                f"Score: {score.total_weighted}/5.0 | "
                f"{'✅ Passes' if passes else '❌ Fails'}"
            ):
                cols = st.columns([2, 1, 1])

                with cols[0]:
                    st.markdown(f"**District:** {listing['district'] or 'N/A'}")
                    st.markdown(f"**Rooms:** {listing['rooms_count']} | **Bathrooms:** {listing['bathrooms_count']}")
                    st.markdown(f"**Size:** {listing['sqm_total']}m² | **Floor:** {listing['floor_number']}/{listing['floor_total']}")
                    st.markdown(f"**Metro:** {listing['metro_distance_m']}m to {listing['metro_station'] or 'N/A'}")

                with cols[1]:
                    st.markdown("**Score Breakdown:**")
                    st.markdown(f"- Location: {score.location}/5")
                    st.markdown(f"- Price/sqm: {score.price_sqm}/5")
                    st.markdown(f"- Layout: {score.layout}/5")
                    st.markdown(f"- Building: {score.building}/5")

                with cols[2]:
                    if failed:
                        st.markdown("**Failed Deal Breakers:**")
                        for f in failed:
                            st.markdown(f"- ❌ {f}")
                    else:
                        st.success("All deal breakers passed!")

                if listing["url"]:
                    st.markdown(f"[🔗 View Listing]({listing['url']})")
    else:
        st.info("No shortlisted apartments yet. Go to Listings to shortlist apartments.")

    # Price range analysis
    st.markdown("---")
    st.subheader("💰 Price Analysis")

    listings = get_listings(limit=500)
    if listings:
        df = pd.DataFrame([dict(l) for l in listings])

        if "price_eur" in df.columns and not df["price_eur"].isna().all():
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Price Distribution**")
                price_counts = pd.cut(
                    df["price_eur"].dropna(),
                    bins=[0, 150000, 200000, 250000, 270000, 300000, float("inf")],
                    labels=["<150k", "150-200k", "200-250k", "250-270k", "270-300k", ">300k"]
                ).value_counts().sort_index()
                st.bar_chart(price_counts)

            with col2:
                st.markdown("**Price/sqm Distribution**")
                if "price_per_sqm_eur" in df.columns:
                    sqm_counts = pd.cut(
                        df["price_per_sqm_eur"].dropna(),
                        bins=[0, 1500, 2000, 2500, 3000, float("inf")],
                        labels=["<1500", "1500-2000", "2000-2500", "2500-3000", ">3000"]
                    ).value_counts().sort_index()
                    st.bar_chart(sqm_counts)

except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Make sure all dependencies are installed.")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
