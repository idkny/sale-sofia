# app/pages/2_Listings.py
"""Listings page with filterable table and detail views."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Listings", page_icon="🏢", layout="wide")

st.title("🏢 Listings")

try:
    from data.data_store_main import (
        get_listings, get_listing_by_id, update_listing_evaluation,
        get_viewings_for_listing, add_viewing, get_listings_stats
    )
    from app.scoring import (
        calculate_score, check_deal_breakers, passes_all_deal_breakers,
        listing_to_dict, calculate_total_investment, MAX_TOTAL_BUDGET
    )

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Get stats for filter options
    stats = get_listings_stats()
    districts = [d["district"] for d in stats.get("by_district", []) if d["district"]]

    # District filter
    selected_district = st.sidebar.selectbox(
        "District",
        ["All"] + districts,
        index=0
    )

    # Price range filter
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_price = st.number_input("Min Price (€)", value=0, step=10000)
    with col2:
        max_price = st.number_input("Max Price (€)", value=300000, step=10000)

    # Rooms filter
    min_rooms = st.sidebar.selectbox("Min Rooms", [1, 2, 3, 4], index=2)

    # Status filter
    status_filter = st.sidebar.multiselect(
        "Status",
        ["New", "Contacted", "Viewed", "Shortlist", "Rejected"],
        default=["New", "Contacted", "Viewed", "Shortlist"]
    )

    # Deal breaker filter
    only_passing = st.sidebar.checkbox("Only show apartments passing all deal breakers", value=False)

    # Fetch listings
    district_param = None if selected_district == "All" else selected_district
    listings = get_listings(
        district=district_param,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price < 300000 else None,
        min_rooms=min_rooms,
        limit=200
    )

    # Convert to dataframe and apply additional filters
    if listings:
        df = pd.DataFrame([dict(l) for l in listings])

        # Apply status filter
        if status_filter:
            df = df[df["status"].fillna("New").isin(status_filter)]

        # Apply deal breaker filter
        if only_passing:
            passing_ids = []
            for _, row in df.iterrows():
                passes, _ = passes_all_deal_breakers(row.to_dict())
                if passes:
                    passing_ids.append(row["id"])
            df = df[df["id"].isin(passing_ids)]

        st.markdown(f"**Showing {len(df)} listings**")

        # Add calculated columns
        df["score"] = df.apply(
            lambda row: calculate_score(row.to_dict()).total_weighted,
            axis=1
        )
        df["total_investment"] = df.apply(
            lambda row: calculate_total_investment(row.to_dict()),
            axis=1
        )

        # Table view
        st.subheader("📋 Listings Table")

        # Select columns to display
        display_cols = [
            "id", "title", "district", "price_eur", "sqm_total",
            "rooms_count", "bathrooms_count", "floor_number",
            "metro_distance_m", "status", "decision", "score"
        ]
        display_cols = [c for c in display_cols if c in df.columns]

        # Format columns
        df_display = df[display_cols].copy()
        if "price_eur" in df_display.columns:
            df_display["price_eur"] = df_display["price_eur"].apply(
                lambda x: f"€{x:,.0f}" if pd.notna(x) else "N/A"
            )
        if "score" in df_display.columns:
            df_display["score"] = df_display["score"].apply(lambda x: f"{x:.2f}/5")

        # Rename columns for display
        df_display.columns = [
            "ID", "Title", "District", "Price", "Sqm", "Rooms", "Bath",
            "Floor", "Metro (m)", "Status", "Decision", "Score"
        ][:len(display_cols)]

        # Show as dataframe with selection
        st.dataframe(df_display, hide_index=True, use_container_width=True)

        # Detail view section
        st.markdown("---")
        st.subheader("🔎 Listing Detail")

        listing_id = st.selectbox(
            "Select listing to view details",
            df["id"].tolist(),
            format_func=lambda x: f"#{x} - {df[df['id']==x]['title'].iloc[0][:50]}..."
                if df[df['id']==x]['title'].iloc[0] else f"#{x}"
        )

        if listing_id:
            listing = get_listing_by_id(listing_id)
            if listing:
                listing_dict = listing_to_dict(listing)
                score = calculate_score(listing_dict)
                deal_breakers = check_deal_breakers(listing_dict)
                passes, failed = passes_all_deal_breakers(listing_dict)

                # Header with key info
                st.markdown(f"### {listing['title'] or 'Untitled Listing'}")

                # Status badge
                status = listing["status"] or "New"
                decision = listing["decision"]
                if passes:
                    st.success(f"✅ Passes all deal breakers | Status: {status} | Decision: {decision or 'None'}")
                else:
                    st.warning(f"❌ Fails {len(failed)} deal breaker(s) | Status: {status} | Decision: {decision or 'None'}")

                # Main content in tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📋 Details", "📊 Scoring", "🚫 Deal Breakers", "📝 Notes & Viewings", "✏️ Edit"
                ])

                with tab1:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**💰 Price & Budget**")
                        st.markdown(f"- Price: **€{listing['price_eur']:,.0f}**" if listing['price_eur'] else "- Price: N/A")
                        st.markdown(f"- Price/sqm: €{listing['price_per_sqm_eur']:,.0f}" if listing['price_per_sqm_eur'] else "- Price/sqm: N/A")
                        reno = listing['estimated_renovation_eur'] or 0
                        st.markdown(f"- Est. Renovation: €{reno:,.0f}")
                        total = calculate_total_investment(listing_dict)
                        budget_status = "✅" if total <= MAX_TOTAL_BUDGET else "❌"
                        st.markdown(f"- **Total: €{total:,.0f}** {budget_status}")

                    with col2:
                        st.markdown("**📐 Size & Layout**")
                        st.markdown(f"- Total sqm: {listing['sqm_total']}")
                        st.markdown(f"- Net sqm: {listing['sqm_net'] or 'N/A'}")
                        st.markdown(f"- Rooms: {listing['rooms_count']}")
                        st.markdown(f"- Bathrooms: {listing['bathrooms_count']}")
                        st.markdown(f"- Floor: {listing['floor_number']}/{listing['floor_total']}")
                        st.markdown(f"- Elevator: {'Yes' if listing['has_elevator'] else 'No'}")

                    with col3:
                        st.markdown("**🏗️ Building**")
                        st.markdown(f"- Type: {listing['building_type'] or 'N/A'}")
                        st.markdown(f"- Year: {listing['construction_year'] or 'N/A'}")
                        st.markdown(f"- Act Status: {listing['act_status'] or 'N/A'}")
                        st.markdown(f"- Condition: {listing['condition'] or 'N/A'}")

                    st.markdown("---")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**📍 Location**")
                        st.markdown(f"- District: {listing['district'] or 'N/A'}")
                        st.markdown(f"- Neighborhood: {listing['neighborhood'] or 'N/A'}")
                        st.markdown(f"- Address: {listing['address'] or 'N/A'}")
                        st.markdown(f"- Metro: {listing['metro_station'] or 'N/A'} ({listing['metro_distance_m']}m)" if listing['metro_distance_m'] else "- Metro: N/A")
                        st.markdown(f"- Orientation: {listing['orientation'] or 'N/A'}")

                    with col2:
                        st.markdown("**🏠 Features**")
                        features = []
                        if listing.get("has_balcony"): features.append("Balcony")
                        if listing.get("has_garden"): features.append("Garden")
                        if listing.get("has_terrace"): features.append("Terrace")
                        if listing.get("has_parking"): features.append("Parking")
                        if listing.get("has_storage"): features.append("Storage")
                        if listing.get("has_garage"): features.append("Garage")
                        if listing.get("has_elevator"): features.append("Elevator")
                        if listing.get("has_ac_preinstalled"): features.append("AC")
                        if listing.get("is_furnished"): features.append("Furnished")

                        st.markdown(", ".join(features) if features else "No features recorded")

                    # Link to original listing
                    if listing["url"]:
                        st.markdown(f"[🔗 View Original Listing]({listing['url']})")

                with tab2:
                    st.markdown("### Score Breakdown")

                    # Score metrics
                    cols = st.columns(7)
                    metrics = [
                        ("Location", score.location, 25),
                        ("Price/sqm", score.price_sqm, 20),
                        ("Condition", score.condition, 15),
                        ("Layout", score.layout, 15),
                        ("Building", score.building, 10),
                        ("Rental", score.rental, 10),
                        ("Extras", score.extras, 5),
                    ]

                    for col, (name, value, weight) in zip(cols, metrics):
                        with col:
                            st.metric(f"{name} ({weight}%)", f"{value:.1f}/5")

                    st.markdown("---")
                    st.metric("**Total Weighted Score**", f"{score.total_weighted:.2f}/5.0")

                    # Score bar chart
                    score_data = {
                        "Criterion": ["Location", "Price/sqm", "Condition", "Layout", "Building", "Rental", "Extras"],
                        "Score": [score.location, score.price_sqm, score.condition, score.layout, score.building, score.rental, score.extras]
                    }
                    st.bar_chart(pd.DataFrame(score_data).set_index("Criterion"))

                with tab3:
                    st.markdown("### Deal Breaker Check")

                    for db in deal_breakers:
                        icon = "✅" if db.passed else "❌"
                        color = "green" if db.passed else "red"
                        st.markdown(f"{icon} **{db.name}**: {db.reason}")

                with tab4:
                    st.markdown("### Notes")
                    st.text_area(
                        "User Notes",
                        value=listing.get("user_notes") or "",
                        key="view_notes",
                        disabled=True
                    )

                    st.markdown("### Viewing History")
                    viewings = get_viewings_for_listing(listing_id)

                    if viewings:
                        for v in viewings:
                            with st.expander(f"📅 Viewing on {v['date_viewed']}"):
                                st.markdown(f"**Agent:** {v['agent_contact'] or 'N/A'}")
                                st.markdown(f"**First Impressions:** {v['first_impressions'] or 'N/A'}")

                                if v['positives']:
                                    positives = json.loads(v['positives']) if isinstance(v['positives'], str) else v['positives']
                                    st.markdown("**Positives:**")
                                    for p in positives:
                                        st.markdown(f"- ✅ {p}")

                                if v['negatives']:
                                    negatives = json.loads(v['negatives']) if isinstance(v['negatives'], str) else v['negatives']
                                    st.markdown("**Negatives:**")
                                    for n in negatives:
                                        st.markdown(f"- ❌ {n}")
                    else:
                        st.info("No viewings recorded yet")

                with tab5:
                    st.markdown("### Update Listing")

                    with st.form(key="update_form"):
                        new_status = st.selectbox(
                            "Status",
                            ["New", "Contacted", "Viewed", "Shortlist", "Rejected"],
                            index=["New", "Contacted", "Viewed", "Shortlist", "Rejected"].index(listing["status"]) if listing["status"] in ["New", "Contacted", "Viewed", "Shortlist", "Rejected"] else 0
                        )

                        new_decision = st.selectbox(
                            "Decision",
                            ["None", "Maybe", "Shortlist", "Reject", "Offer Made"],
                            index=["None", "Maybe", "Shortlist", "Reject", "Offer Made"].index(listing["decision"]) if listing["decision"] in ["None", "Maybe", "Shortlist", "Reject", "Offer Made"] else 0
                        )

                        new_reason = st.text_area(
                            "Decision Reason",
                            value=listing.get("decision_reason") or ""
                        )

                        new_renovation = st.number_input(
                            "Estimated Renovation (€)",
                            value=float(listing.get("estimated_renovation_eur") or 0),
                            step=1000.0
                        )

                        new_notes = st.text_area(
                            "User Notes",
                            value=listing.get("user_notes") or ""
                        )

                        submit = st.form_submit_button("Save Changes")

                        if submit:
                            success = update_listing_evaluation(
                                listing_id,
                                status=new_status,
                                decision=None if new_decision == "None" else new_decision,
                                decision_reason=new_reason if new_reason else None,
                                estimated_renovation_eur=new_renovation if new_renovation > 0 else None,
                                user_notes=new_notes if new_notes else None
                            )
                            if success:
                                st.success("Listing updated!")
                                st.rerun()
                            else:
                                st.error("Failed to update listing")

                    # Add viewing form
                    st.markdown("---")
                    st.markdown("### Add Viewing")

                    with st.form(key="add_viewing_form"):
                        view_date = st.date_input("Date Viewed")
                        view_agent = st.text_input("Agent Contact")
                        view_impressions = st.text_area("First Impressions")
                        view_positives = st.text_area("Positives (one per line)")
                        view_negatives = st.text_area("Negatives (one per line)")

                        add_viewing_btn = st.form_submit_button("Add Viewing")

                        if add_viewing_btn:
                            positives_list = [p.strip() for p in view_positives.split("\n") if p.strip()]
                            negatives_list = [n.strip() for n in view_negatives.split("\n") if n.strip()]

                            result = add_viewing(
                                listing_id=listing_id,
                                date_viewed=str(view_date),
                                agent_contact=view_agent if view_agent else None,
                                first_impressions=view_impressions if view_impressions else None,
                                positives=positives_list if positives_list else None,
                                negatives=negatives_list if negatives_list else None
                            )
                            if result:
                                st.success("Viewing added!")
                                st.rerun()
                            else:
                                st.error("Failed to add viewing")

    else:
        st.info("No listings found. Try adjusting your filters or scrape some listings first.")

except ImportError as e:
    st.error(f"Import error: {e}")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
