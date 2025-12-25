# app/streamlit_app.py
"""
Sofia Apartment Search - Streamlit Dashboard

Run with: streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Sofia Apartment Search",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main entry point for Streamlit app."""
    st.title("🏠 Sofia Apartment Search")
    st.markdown("---")

    st.markdown("""
    Welcome to the Sofia Apartment Search Dashboard.

    Use the sidebar to navigate between pages:

    - **Dashboard**: Overview statistics and charts
    - **Listings**: Browse and filter all listings
    - **Compare**: Side-by-side comparison of shortlisted apartments
    - **Analytics**: Price trends and district analysis

    ### Quick Stats

    Navigate to the **Dashboard** page to see:
    - Total active listings
    - Status breakdown (New/Contacted/Viewed/Shortlisted)
    - Price distribution
    - District analysis
    """)

    # Import data module to test connection
    try:
        from data.data_store_main import get_listing_count, get_listings_stats

        count = get_listing_count()
        st.metric("Total Active Listings", count)

        if count > 0:
            stats = get_listings_stats()
            cols = st.columns(4)

            with cols[0]:
                st.metric("Average Price", f"€{stats['price']['avg']:,.0f}" if stats['price']['avg'] else "N/A")

            with cols[1]:
                st.metric("Avg Price/sqm", f"€{stats['price']['avg_per_sqm']:,.0f}" if stats['price']['avg_per_sqm'] else "N/A")

            with cols[2]:
                shortlisted = stats.get("by_decision", {}).get("Shortlist", 0)
                st.metric("Shortlisted", shortlisted)

            with cols[3]:
                viewed = stats.get("by_status", {}).get("Viewed", 0)
                st.metric("Viewed", viewed)

    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Make sure the database is initialized. Run: `python -c 'from data.data_store_main import init_db'`")


if __name__ == "__main__":
    main()
