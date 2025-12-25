# app/pages/3_Compare.py
"""Compare page for side-by-side analysis of shortlisted apartments."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compare", page_icon="⚖️", layout="wide")

st.title("⚖️ Compare Apartments")
st.markdown("Side-by-side comparison of shortlisted apartments")

try:
    from data.data_store_main import get_shortlisted_listings, get_listings, get_listing_by_id
    from app.scoring import (
        calculate_score, check_deal_breakers, passes_all_deal_breakers,
        listing_to_dict, calculate_total_investment, MAX_TOTAL_BUDGET
    )

    # Get shortlisted and all listings for selection
    shortlisted = get_shortlisted_listings()
    all_listings = get_listings(limit=100)

    if not all_listings:
        st.info("No listings available. Scrape some listings first.")
    else:
        # Selection mode
        st.sidebar.header("Selection Mode")
        mode = st.sidebar.radio(
            "Compare from:",
            ["Shortlisted Only", "All Listings"]
        )

        listings_pool = shortlisted if mode == "Shortlisted Only" else all_listings

        if not listings_pool:
            st.info("No shortlisted apartments. Go to Listings page to shortlist apartments.")
        else:
            # Select apartments to compare (max 3)
            st.sidebar.header("Select Apartments")

            options = {
                l["id"]: f"#{l['id']} - {l['title'][:30]}... (€{l['price_eur']:,.0f})"
                if l["title"] else f"#{l['id']} - €{l['price_eur']:,.0f}"
                for l in listings_pool
            }

            selected_ids = st.sidebar.multiselect(
                "Choose 2-3 apartments",
                list(options.keys()),
                format_func=lambda x: options[x],
                max_selections=3
            )

            if len(selected_ids) < 2:
                st.info("Select at least 2 apartments to compare.")
            else:
                # Fetch selected listings
                selected_listings = [get_listing_by_id(id) for id in selected_ids]
                selected_dicts = [listing_to_dict(l) for l in selected_listings]

                # Create comparison columns
                cols = st.columns(len(selected_ids))

                # Header row with titles and images
                for col, listing in zip(cols, selected_listings):
                    with col:
                        st.markdown(f"### {listing['title'][:40] if listing['title'] else 'Untitled'}...")
                        if listing["main_image_url"]:
                            st.image(listing["main_image_url"], use_container_width=True)
                        else:
                            st.markdown("*No image*")

                st.markdown("---")

                # Price section
                st.subheader("💰 Price & Budget")
                cols = st.columns(len(selected_ids))
                for col, listing, listing_dict in zip(cols, selected_listings, selected_dicts):
                    with col:
                        price = listing["price_eur"] or 0
                        reno = listing.get("estimated_renovation_eur") or 0
                        total = calculate_total_investment(listing_dict)
                        budget_ok = total <= MAX_TOTAL_BUDGET

                        st.metric("Price", f"€{price:,.0f}")
                        st.metric("Price/sqm", f"€{listing['price_per_sqm_eur']:,.0f}" if listing['price_per_sqm_eur'] else "N/A")
                        st.metric("Est. Renovation", f"€{reno:,.0f}")
                        st.metric(
                            "Total Investment",
                            f"€{total:,.0f}",
                            delta=f"€{MAX_TOTAL_BUDGET - total:,.0f} under budget" if budget_ok else f"€{total - MAX_TOTAL_BUDGET:,.0f} over budget",
                            delta_color="normal" if budget_ok else "inverse"
                        )

                st.markdown("---")

                # Size & Layout section
                st.subheader("📐 Size & Layout")
                cols = st.columns(len(selected_ids))
                for col, listing in zip(cols, selected_listings):
                    with col:
                        st.metric("Total sqm", listing["sqm_total"] or "N/A")
                        st.metric("Net sqm", listing["sqm_net"] or "N/A")
                        st.metric("Rooms", listing["rooms_count"] or "N/A")
                        st.metric("Bathrooms", listing["bathrooms_count"] or "N/A")
                        st.metric("Floor", f"{listing['floor_number']}/{listing['floor_total']}" if listing['floor_number'] else "N/A")
                        st.markdown(f"**Elevator:** {'✅' if listing['has_elevator'] else '❌'}")

                st.markdown("---")

                # Location section
                st.subheader("📍 Location")
                cols = st.columns(len(selected_ids))
                for col, listing in zip(cols, selected_listings):
                    with col:
                        st.markdown(f"**District:** {listing['district'] or 'N/A'}")
                        st.markdown(f"**Neighborhood:** {listing['neighborhood'] or 'N/A'}")
                        metro_dist = listing["metro_distance_m"]
                        metro_ok = metro_dist and metro_dist <= 600
                        st.markdown(f"**Metro:** {listing['metro_station'] or 'N/A'}")
                        if metro_dist:
                            st.metric("Metro Distance", f"{metro_dist}m", delta="OK" if metro_ok else "Too far", delta_color="normal" if metro_ok else "inverse")
                        st.markdown(f"**Orientation:** {listing['orientation'] or 'N/A'}")

                st.markdown("---")

                # Building section
                st.subheader("🏗️ Building")
                cols = st.columns(len(selected_ids))
                for col, listing in zip(cols, selected_listings):
                    with col:
                        building_type = listing["building_type"] or "N/A"
                        is_panel = "panel" in building_type.lower() if building_type != "N/A" else False
                        st.markdown(f"**Type:** {building_type} {'❌' if is_panel else ''}")
                        st.markdown(f"**Year:** {listing['construction_year'] or 'N/A'}")
                        st.markdown(f"**Act Status:** {listing['act_status'] or 'N/A'}")
                        st.markdown(f"**Condition:** {listing['condition'] or 'N/A'}")

                st.markdown("---")

                # Scores section
                st.subheader("📊 Scores")
                scores = [calculate_score(d) for d in selected_dicts]

                # Score comparison table
                score_data = {
                    "Criterion": ["Location (25%)", "Price/sqm (20%)", "Condition (15%)", "Layout (15%)", "Building (10%)", "Rental (10%)", "Extras (5%)", "**TOTAL**"],
                }
                for i, (listing, score) in enumerate(zip(selected_listings, scores)):
                    col_name = f"#{listing['id']}"
                    score_data[col_name] = [
                        f"{score.location:.1f}",
                        f"{score.price_sqm:.1f}",
                        f"{score.condition:.1f}",
                        f"{score.layout:.1f}",
                        f"{score.building:.1f}",
                        f"{score.rental:.1f}",
                        f"{score.extras:.1f}",
                        f"**{score.total_weighted:.2f}/5**"
                    ]

                df_scores = pd.DataFrame(score_data)
                st.dataframe(df_scores, hide_index=True, use_container_width=True)

                # Score bar chart comparison
                chart_data = pd.DataFrame({
                    f"#{l['id']}": [s.location, s.price_sqm, s.condition, s.layout, s.building, s.rental, s.extras]
                    for l, s in zip(selected_listings, scores)
                }, index=["Location", "Price/sqm", "Condition", "Layout", "Building", "Rental", "Extras"])

                st.bar_chart(chart_data)

                st.markdown("---")

                # Deal Breakers section
                st.subheader("🚫 Deal Breakers")
                cols = st.columns(len(selected_ids))
                for col, listing, listing_dict in zip(cols, selected_listings, selected_dicts):
                    with col:
                        passes, failed = passes_all_deal_breakers(listing_dict)
                        if passes:
                            st.success("✅ Passes all deal breakers")
                        else:
                            st.error(f"❌ Fails {len(failed)} deal breaker(s)")
                            for f in failed:
                                st.markdown(f"- {f}")

                st.markdown("---")

                # Features comparison
                st.subheader("🏠 Features")
                feature_list = [
                    ("has_balcony", "Balcony"),
                    ("has_garden", "Garden"),
                    ("has_terrace", "Terrace"),
                    ("has_parking", "Parking"),
                    ("has_storage", "Storage"),
                    ("has_garage", "Garage"),
                    ("has_ac_preinstalled", "AC"),
                    ("is_furnished", "Furnished"),
                    ("has_separate_kitchen", "Separate Kitchen"),
                    ("near_park", "Near Park"),
                    ("near_schools", "Near Schools"),
                    ("near_supermarket", "Near Supermarket"),
                ]

                feature_data = {"Feature": [f[1] for f in feature_list]}
                for listing in selected_listings:
                    col_name = f"#{listing['id']}"
                    feature_data[col_name] = [
                        "✅" if listing.get(f[0]) else "❌" for f in feature_list
                    ]

                df_features = pd.DataFrame(feature_data)
                st.dataframe(df_features, hide_index=True, use_container_width=True)

                st.markdown("---")

                # Links
                st.subheader("🔗 Listing Links")
                cols = st.columns(len(selected_ids))
                for col, listing in zip(cols, selected_listings):
                    with col:
                        if listing["url"]:
                            st.markdown(f"[View Original Listing]({listing['url']})")
                        else:
                            st.markdown("*No URL*")

                # Summary recommendation
                st.markdown("---")
                st.subheader("🏆 Recommendation")

                best_score_idx = max(range(len(scores)), key=lambda i: scores[i].total_weighted)
                best_listing = selected_listings[best_score_idx]
                best_score = scores[best_score_idx]

                # Check if best also passes all deal breakers
                best_passes, _ = passes_all_deal_breakers(selected_dicts[best_score_idx])

                if best_passes:
                    st.success(f"""
                    **Best Choice: #{best_listing['id']} - {best_listing['title'][:40]}...**

                    - Highest score: {best_score.total_weighted:.2f}/5.0
                    - Passes all deal breakers
                    - Price: €{best_listing['price_eur']:,.0f}
                    """)
                else:
                    # Find best that passes
                    passing_indices = [i for i, d in enumerate(selected_dicts) if passes_all_deal_breakers(d)[0]]
                    if passing_indices:
                        best_passing_idx = max(passing_indices, key=lambda i: scores[i].total_weighted)
                        best_passing = selected_listings[best_passing_idx]
                        best_passing_score = scores[best_passing_idx]
                        st.warning(f"""
                        **Highest score (#{best_listing['id']}) fails deal breakers.**

                        **Recommended: #{best_passing['id']} - {best_passing['title'][:40]}...**
                        - Score: {best_passing_score.total_weighted:.2f}/5.0
                        - Passes all deal breakers
                        - Price: €{best_passing['price_eur']:,.0f}
                        """)
                    else:
                        st.error("⚠️ None of the selected apartments pass all deal breakers!")

except ImportError as e:
    st.error(f"Import error: {e}")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
