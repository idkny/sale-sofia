# data/data_store_main.py
"""
SQLite database for storing apartment listings with full evaluation support.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from paths import DB_PATH

# SQLite concurrency settings with fallback defaults
try:
    from config.settings import SQLITE_TIMEOUT, SQLITE_WAL_MODE
except ImportError:
    SQLITE_TIMEOUT = 30.0
    SQLITE_WAL_MODE = True


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with concurrency settings."""
    conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if SQLITE_WAL_MODE:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(f"PRAGMA busy_timeout = {int(SQLITE_TIMEOUT * 1000)}")
    return conn


def init_db():
    """Initialize database with listings table."""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Identifiers
            external_id TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source_site TEXT NOT NULL,

            -- Basic info
            title TEXT,
            description TEXT,

            -- Price (EUR only)
            price_eur REAL,
            price_per_sqm_eur REAL,

            -- Size
            sqm_total REAL,
            sqm_net REAL,

            -- Layout
            rooms_count INTEGER,
            bathrooms_count INTEGER,

            -- Floor
            floor_number INTEGER,
            floor_total INTEGER,
            has_elevator BOOLEAN,

            -- Building
            building_type TEXT,
            construction_year INTEGER,
            act_status TEXT,

            -- Location
            district TEXT,
            neighborhood TEXT,
            address TEXT,
            metro_station TEXT,
            metro_distance_m INTEGER,

            -- Features
            orientation TEXT,
            has_balcony BOOLEAN,
            has_garden BOOLEAN,
            has_parking BOOLEAN,
            has_storage BOOLEAN,
            heating_type TEXT,
            condition TEXT,

            -- Media
            main_image_url TEXT,
            image_urls TEXT,  -- JSON array

            -- Contact
            agency TEXT,
            agent_phone TEXT,

            -- Metadata
            listing_date TEXT,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Index for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_district ON listings(district)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price_eur)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source_site)")

    conn.commit()
    conn.close()
    logger.info("Database initialized")


def migrate_listings_schema():
    """
    Add new columns to listings table for evaluation features.
    SQLite supports ALTER TABLE ADD COLUMN, so we add each missing column.
    """
    conn = get_db_connection()

    # Get existing columns
    cursor = conn.execute("PRAGMA table_info(listings)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # New columns to add with their definitions
    new_columns = [
        # User Evaluation
        ("status", "TEXT DEFAULT 'New'"),  # New/Contacted/Viewed/Rejected/Shortlist
        ("date_found", "TEXT"),
        ("decision", "TEXT"),  # Reject/Maybe/Shortlist/Offer Made
        ("decision_reason", "TEXT"),
        ("follow_up_actions", "TEXT"),

        # Budget
        ("estimated_renovation_eur", "REAL"),

        # Media
        ("floor_plan_url", "TEXT"),

        # Legal
        ("has_legal_issues", "BOOLEAN DEFAULT 0"),

        # Extended Building Features
        ("has_security_entrance", "BOOLEAN"),
        ("building_condition_notes", "TEXT"),

        # Extended Apartment Features
        ("has_ac_preinstalled", "BOOLEAN"),
        ("has_central_heating", "BOOLEAN"),
        ("has_gas_heating", "BOOLEAN"),
        ("has_double_glazing", "BOOLEAN"),
        ("has_security_door", "BOOLEAN"),
        ("has_video_intercom", "BOOLEAN"),
        ("has_separate_kitchen", "BOOLEAN"),

        # Furnishing & Appliances
        ("is_furnished", "BOOLEAN"),
        ("has_builtin_wardrobes", "BOOLEAN"),
        ("has_appliances", "BOOLEAN"),
        ("is_recently_renovated", "BOOLEAN"),

        # Outdoor Features
        ("has_terrace", "BOOLEAN"),
        ("has_multiple_balconies", "BOOLEAN"),
        ("has_laundry_space", "BOOLEAN"),
        ("has_garage", "BOOLEAN"),

        # Location Amenities
        ("near_park", "BOOLEAN"),
        ("near_schools", "BOOLEAN"),
        ("near_supermarket", "BOOLEAN"),
        ("near_restaurants", "BOOLEAN"),
        ("is_quiet_street", "BOOLEAN"),

        # Notes
        ("user_notes", "TEXT"),

        # Change Detection (Spec 111)
        ("content_hash", "TEXT"),              # SHA256 of key content
        ("last_change_at", "TIMESTAMP"),       # When content last changed
        ("change_count", "INTEGER DEFAULT 0"), # How many times changed
        ("price_history", "TEXT"),             # JSON: [{"price": 150000, "date": "..."}]
        ("consecutive_unchanged", "INTEGER DEFAULT 0"),  # For adaptive scheduling
    ]

    added = 0
    for col_name, col_def in new_columns:
        if col_name not in existing_columns:
            try:
                conn.execute(f"ALTER TABLE listings ADD COLUMN {col_name} {col_def}")
                logger.debug(f"Added column: {col_name}")
                added += 1
            except sqlite3.Error as e:
                logger.error(f"Error adding column {col_name}: {e}")

    if added > 0:
        conn.commit()
        logger.info(f"Migration complete: added {added} new columns to listings")
    else:
        logger.debug("No new columns to add")

    # Create index for change detection (after column exists)
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_hash ON listings(content_hash)")
        conn.commit()
    except sqlite3.Error:
        pass  # Index already exists or column doesn't exist yet (first run)

    conn.close()


def init_viewings_table():
    """Create listing_viewings table for tracking property viewings."""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS listing_viewings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,

            -- Viewing info
            date_viewed TEXT NOT NULL,
            agent_contact TEXT,

            -- Notes
            first_impressions TEXT,
            positives TEXT,  -- JSON array
            negatives TEXT,  -- JSON array
            questions TEXT,
            answers TEXT,

            -- Metadata
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_viewings_listing ON listing_viewings(listing_id)")
    conn.commit()
    conn.close()
    logger.info("Viewings table initialized")


def save_listing(
    listing, content_hash: str = None, price_history: str = None
) -> Optional[int]:
    """
    Save a listing to the database.

    Args:
        listing: ListingData object from scraper
        content_hash: SHA256 hash of key listing fields (for change detection)
        price_history: JSON string of price history array

    Returns:
        Listing ID or None if failed
    """
    conn = get_db_connection()

    try:
        # Convert image_urls list to JSON string
        import json
        image_urls_json = json.dumps(listing.image_urls) if listing.image_urls else None

        cursor = conn.execute("""
            INSERT INTO listings (
                external_id, url, source_site, title, description,
                price_eur, price_per_sqm_eur, sqm_total, sqm_net,
                rooms_count, bathrooms_count, floor_number, floor_total, has_elevator,
                building_type, construction_year, act_status,
                district, neighborhood, address, metro_station, metro_distance_m,
                orientation, has_balcony, has_garden, has_parking, has_storage,
                heating_type, condition, main_image_url, image_urls,
                agency, agent_phone, listing_date,
                content_hash, price_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                price_eur = excluded.price_eur,
                content_hash = excluded.content_hash,
                price_history = COALESCE(excluded.price_history, price_history),
                last_change_at = CASE
                    WHEN content_hash IS NULL OR content_hash != excluded.content_hash
                    THEN CURRENT_TIMESTAMP
                    ELSE last_change_at
                END,
                change_count = CASE
                    WHEN content_hash IS NULL OR content_hash != excluded.content_hash
                    THEN COALESCE(change_count, 0) + 1
                    ELSE change_count
                END,
                consecutive_unchanged = 0,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
        """, (
            listing.external_id, listing.url, listing.source_site,
            listing.title, listing.description,
            listing.price_eur, listing.price_per_sqm_eur,
            listing.sqm_total, listing.sqm_net,
            listing.rooms_count, listing.bathrooms_count,
            listing.floor_number, listing.floor_total, listing.has_elevator,
            listing.building_type, listing.construction_year, listing.act_status,
            listing.district, listing.neighborhood, listing.address,
            listing.metro_station, listing.metro_distance_m,
            listing.orientation, listing.has_balcony, listing.has_garden,
            listing.has_parking, listing.has_storage,
            listing.heating_type, listing.condition,
            listing.main_image_url, image_urls_json,
            listing.agency, listing.agent_phone,
            listing.listing_date.isoformat() if listing.listing_date else None,
            content_hash, price_history
        ))

        conn.commit()
        listing_id = cursor.lastrowid
        logger.info(f"Saved listing {listing.external_id} from {listing.source_site}")
        return listing_id

    except sqlite3.Error as e:
        logger.error(f"Database error saving listing: {e}")
        return None
    finally:
        conn.close()


def get_listing_by_url(url: str) -> Optional[sqlite3.Row]:
    """Get a listing by URL."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM listings WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    return row


def increment_unchanged_counter(url: str) -> bool:
    """
    Increment consecutive_unchanged counter for a listing.

    Called when a listing is scraped but content hasn't changed.

    Args:
        url: Listing URL

    Returns:
        True if updated successfully, False otherwise
    """
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE listings
            SET consecutive_unchanged = COALESCE(consecutive_unchanged, 0) + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE url = ?
        """,
            (url,),
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating unchanged counter: {e}")
        return False
    finally:
        conn.close()


def get_listings(
    district: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_rooms: Optional[int] = None,
    limit: int = 100
) -> List[sqlite3.Row]:
    """
    Get listings with optional filters.
    """
    conn = get_db_connection()

    query = "SELECT * FROM listings WHERE is_active = 1"
    params = []

    if district:
        query += " AND district LIKE ?"
        params.append(f"%{district}%")

    if min_price:
        query += " AND price_eur >= ?"
        params.append(min_price)

    if max_price:
        query += " AND price_eur <= ?"
        params.append(max_price)

    if min_rooms:
        query += " AND rooms_count >= ?"
        params.append(min_rooms)

    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_listing_count() -> int:
    """Get total number of active listings."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def mark_listing_inactive(url: str):
    """Mark a listing as inactive (removed from site)."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE listings SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE url = ?",
        (url,)
    )
    conn.commit()
    conn.close()


def get_listing_by_id(listing_id: int) -> Optional[sqlite3.Row]:
    """Get a listing by ID."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_listing_evaluation(
    listing_id: int,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    decision_reason: Optional[str] = None,
    follow_up_actions: Optional[str] = None,
    estimated_renovation_eur: Optional[float] = None,
    user_notes: Optional[str] = None,
    **kwargs
) -> bool:
    """
    Update user evaluation fields for a listing.
    Accepts additional kwargs for any column updates.
    """
    conn = get_db_connection()

    # Build dynamic update query
    updates = []
    params = []

    # Standard evaluation fields
    field_map = {
        "status": status,
        "decision": decision,
        "decision_reason": decision_reason,
        "follow_up_actions": follow_up_actions,
        "estimated_renovation_eur": estimated_renovation_eur,
        "user_notes": user_notes,
    }

    # Add any kwargs (for feature flags, etc.)
    field_map.update(kwargs)

    for field, value in field_map.items():
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(listing_id)

    query = f"UPDATE listings SET {', '.join(updates)} WHERE id = ?"

    try:
        conn.execute(query, params)
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating listing {listing_id}: {e}")
        return False
    finally:
        conn.close()


def update_listing_features(listing_id: int, features: Dict[str, Any]) -> bool:
    """
    Update feature boolean flags for a listing.

    Args:
        listing_id: Listing ID
        features: Dict of feature column names to boolean values
    """
    return update_listing_evaluation(listing_id, **features)


# ============================================================
# Viewings Functions
# ============================================================

def add_viewing(
    listing_id: int,
    date_viewed: str,
    agent_contact: Optional[str] = None,
    first_impressions: Optional[str] = None,
    positives: Optional[List[str]] = None,
    negatives: Optional[List[str]] = None,
    questions: Optional[str] = None,
    answers: Optional[str] = None
) -> Optional[int]:
    """
    Add a viewing record for a listing.

    Returns:
        Viewing ID or None if failed
    """
    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO listing_viewings (
                listing_id, date_viewed, agent_contact,
                first_impressions, positives, negatives,
                questions, answers
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_id, date_viewed, agent_contact,
            first_impressions,
            json.dumps(positives) if positives else None,
            json.dumps(negatives) if negatives else None,
            questions, answers
        ))

        conn.commit()
        viewing_id = cursor.lastrowid

        # Update listing status to Viewed
        conn.execute(
            "UPDATE listings SET status = 'Viewed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (listing_id,)
        )
        conn.commit()

        logger.info(f"Added viewing for listing {listing_id}")
        return viewing_id

    except sqlite3.Error as e:
        logger.error(f"Error adding viewing: {e}")
        return None
    finally:
        conn.close()


def get_viewings_for_listing(listing_id: int) -> List[sqlite3.Row]:
    """Get all viewings for a listing."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM listing_viewings WHERE listing_id = ? ORDER BY date_viewed DESC",
        (listing_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_viewing(
    viewing_id: int,
    first_impressions: Optional[str] = None,
    positives: Optional[List[str]] = None,
    negatives: Optional[List[str]] = None,
    questions: Optional[str] = None,
    answers: Optional[str] = None
) -> bool:
    """Update a viewing record."""
    conn = get_db_connection()

    updates = []
    params = []

    if first_impressions is not None:
        updates.append("first_impressions = ?")
        params.append(first_impressions)
    if positives is not None:
        updates.append("positives = ?")
        params.append(json.dumps(positives))
    if negatives is not None:
        updates.append("negatives = ?")
        params.append(json.dumps(negatives))
    if questions is not None:
        updates.append("questions = ?")
        params.append(questions)
    if answers is not None:
        updates.append("answers = ?")
        params.append(answers)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(viewing_id)

    query = f"UPDATE listing_viewings SET {', '.join(updates)} WHERE id = ?"

    try:
        conn.execute(query, params)
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating viewing {viewing_id}: {e}")
        return False
    finally:
        conn.close()


def delete_viewing(viewing_id: int) -> bool:
    """Delete a viewing record."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM listing_viewings WHERE id = ?", (viewing_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error deleting viewing {viewing_id}: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# Statistics Functions (for Streamlit dashboard)
# ============================================================

def get_listings_stats() -> Dict[str, Any]:
    """Get aggregate statistics for dashboard."""
    conn = get_db_connection()

    stats = {}

    # Total counts
    cursor = conn.execute("SELECT COUNT(*) FROM listings WHERE is_active = 1")
    stats["total_active"] = cursor.fetchone()[0]

    # By status
    cursor = conn.execute("""
        SELECT status, COUNT(*) as count
        FROM listings WHERE is_active = 1
        GROUP BY status
    """)
    stats["by_status"] = {row["status"] or "New": row["count"] for row in cursor.fetchall()}

    # Price stats
    cursor = conn.execute("""
        SELECT
            AVG(price_eur) as avg_price,
            MIN(price_eur) as min_price,
            MAX(price_eur) as max_price,
            AVG(price_per_sqm_eur) as avg_price_sqm
        FROM listings WHERE is_active = 1 AND price_eur IS NOT NULL
    """)
    row = cursor.fetchone()
    stats["price"] = {
        "avg": row["avg_price"],
        "min": row["min_price"],
        "max": row["max_price"],
        "avg_per_sqm": row["avg_price_sqm"],
    }

    # By district
    cursor = conn.execute("""
        SELECT district, COUNT(*) as count, AVG(price_per_sqm_eur) as avg_sqm_price
        FROM listings WHERE is_active = 1 AND district IS NOT NULL
        GROUP BY district ORDER BY count DESC
    """)
    stats["by_district"] = [
        {"district": row["district"], "count": row["count"], "avg_sqm_price": row["avg_sqm_price"]}
        for row in cursor.fetchall()
    ]

    # By decision
    cursor = conn.execute("""
        SELECT decision, COUNT(*) as count
        FROM listings WHERE is_active = 1 AND decision IS NOT NULL
        GROUP BY decision
    """)
    stats["by_decision"] = {row["decision"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return stats


def get_shortlisted_listings() -> List[sqlite3.Row]:
    """Get all shortlisted listings for comparison."""
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT * FROM listings
        WHERE is_active = 1 AND (decision = 'Shortlist' OR status = 'Shortlist')
        ORDER BY price_eur ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# Change Detection Tables (Spec 112)
# ============================================================


def init_change_detection_tables():
    """Create scrape_history and listing_changes tables if not exist."""
    conn = get_db_connection()

    # Track scrape metadata per URL
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scrape_history (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            content_hash TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            last_changed TEXT,
            scrape_count INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scrape_history_url ON scrape_history(url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scrape_history_status ON scrape_history(status)")

    # Track ALL field changes over time
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listing_changes (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER NOT NULL REFERENCES listings(id),
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_at TEXT NOT NULL,
            source_site TEXT NOT NULL,
            UNIQUE(listing_id, field_name, changed_at)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_changes_listing ON listing_changes(listing_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_changes_field ON listing_changes(field_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_changes_date ON listing_changes(changed_at)")

    conn.commit()
    conn.close()
    logger.info("Change detection tables initialized")


def upsert_scrape_history(url: str, content_hash: str) -> bool:
    """
    Insert or update scrape history for a URL.

    Returns:
        True if content changed, False if unchanged
    """
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()

    try:
        existing = conn.execute(
            "SELECT content_hash FROM scrape_history WHERE url = ?", (url,)
        ).fetchone()

        if existing is None:
            conn.execute("""
                INSERT INTO scrape_history (url, content_hash, first_seen, last_seen)
                VALUES (?, ?, ?, ?)
            """, (url, content_hash, now, now))
            conn.commit()
            return True  # New URL

        changed = existing["content_hash"] != content_hash
        if changed:
            conn.execute("""
                UPDATE scrape_history
                SET content_hash = ?, last_seen = ?, last_changed = ?,
                    scrape_count = scrape_count + 1
                WHERE url = ?
            """, (content_hash, now, now, url))
        else:
            conn.execute("""
                UPDATE scrape_history
                SET last_seen = ?, scrape_count = scrape_count + 1
                WHERE url = ?
            """, (now, url))
        conn.commit()
        return changed

    except sqlite3.Error as e:
        logger.error(f"Error upserting scrape history: {e}")
        return False
    finally:
        conn.close()


def record_field_change(
    listing_id: int,
    field_name: str,
    old_value: Any,
    new_value: Any,
    source_site: str,
) -> Optional[int]:
    """
    Record a single field change.

    Args:
        listing_id: ID of the listing
        field_name: Name of the changed field
        old_value: Previous value (will be JSON-serialized if complex)
        new_value: New value (will be JSON-serialized if complex)
        source_site: Source website name

    Returns:
        Change record ID or None if failed
    """
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()

    # JSON-serialize non-string values
    old_str = json.dumps(old_value) if not isinstance(old_value, (str, type(None))) else old_value
    new_str = json.dumps(new_value) if not isinstance(new_value, (str, type(None))) else new_value

    try:
        cursor = conn.execute("""
            INSERT INTO listing_changes
                (listing_id, field_name, old_value, new_value, changed_at, source_site)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (listing_id, field_name, old_str, new_str, now, source_site))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Duplicate entry (same listing, field, timestamp)
        return None
    except sqlite3.Error as e:
        logger.error(f"Error recording field change: {e}")
        return None
    finally:
        conn.close()


def get_scrape_history(url: str) -> Optional[sqlite3.Row]:
    """Get scrape history for a URL."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM scrape_history WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_listing_changes(
    listing_id: int, field: Optional[str] = None
) -> List[sqlite3.Row]:
    """
    Get changes for a listing, optionally filtered by field.

    Args:
        listing_id: ID of the listing
        field: Optional field name to filter by

    Returns:
        List of change records ordered by date descending
    """
    conn = get_db_connection()

    if field:
        cursor = conn.execute("""
            SELECT * FROM listing_changes
            WHERE listing_id = ? AND field_name = ?
            ORDER BY changed_at DESC
        """, (listing_id, field))
    else:
        cursor = conn.execute("""
            SELECT * FROM listing_changes
            WHERE listing_id = ?
            ORDER BY changed_at DESC
        """, (listing_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_price_history_from_changes(listing_id: int) -> List[Dict[str, Any]]:
    """
    Get price history from listing_changes table.

    Returns:
        List of dicts with 'old_value', 'new_value', 'changed_at'
    """
    changes = get_listing_changes(listing_id, field="price_eur")
    return [
        {
            "old_value": row["old_value"],
            "new_value": row["new_value"],
            "changed_at": row["changed_at"],
        }
        for row in changes
    ]


def mark_url_status(url: str, status: str) -> bool:
    """
    Mark URL status in scrape_history.

    Args:
        url: Listing URL
        status: One of 'active', 'removed', 'sold'

    Returns:
        True if updated successfully
    """
    if status not in ("active", "removed", "sold"):
        logger.warning(f"Invalid status '{status}', must be active/removed/sold")
        return False

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE scrape_history SET status = ? WHERE url = ?",
            (status, url)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error marking URL status: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# Cross-Site Deduplication Tables (Spec 106B)
# ============================================================


def init_listing_sources_table():
    """Create listing_sources table for cross-site duplicate tracking."""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS listing_sources (
            id INTEGER PRIMARY KEY,
            property_fingerprint TEXT NOT NULL,
            listing_id INTEGER NOT NULL REFERENCES listings(id),
            source_site TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_price_eur REAL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            UNIQUE(property_fingerprint, source_site)
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_fingerprint ON listing_sources(property_fingerprint)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_listing ON listing_sources(listing_id)")

    conn.commit()
    conn.close()
    logger.info("Listing sources table initialized")


def add_listing_source(
    property_fingerprint: str,
    listing_id: int,
    source_site: str,
    source_url: str,
    source_price_eur: Optional[float] = None,
) -> Optional[int]:
    """
    Add or update a listing source record.

    Args:
        property_fingerprint: SHA256 fingerprint of property characteristics
        listing_id: ID of the listing in listings table
        source_site: Source website (e.g., 'imot.bg', 'bazar.bg')
        source_url: URL of the listing on the source site
        source_price_eur: Price in EUR from this source

    Returns:
        Source record ID or None if failed
    """
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()

    try:
        cursor = conn.execute("""
            INSERT INTO listing_sources
                (property_fingerprint, listing_id, source_site, source_url,
                 source_price_eur, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(property_fingerprint, source_site) DO UPDATE SET
                listing_id = excluded.listing_id,
                source_url = excluded.source_url,
                source_price_eur = excluded.source_price_eur,
                last_seen = excluded.last_seen
        """, (property_fingerprint, listing_id, source_site, source_url,
              source_price_eur, now, now))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Error adding listing source: {e}")
        return None
    finally:
        conn.close()


def get_sources_by_fingerprint(fingerprint: str) -> List[sqlite3.Row]:
    """
    Get all sources for a property fingerprint.

    Args:
        fingerprint: Property fingerprint

    Returns:
        List of source records
    """
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM listing_sources WHERE property_fingerprint = ? ORDER BY is_primary DESC, first_seen ASC",
        (fingerprint,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_sources_by_listing(listing_id: int) -> List[sqlite3.Row]:
    """
    Get all sources for a listing ID.

    Args:
        listing_id: Listing ID

    Returns:
        List of source records
    """
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM listing_sources WHERE listing_id = ? ORDER BY is_primary DESC, first_seen ASC",
        (listing_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_source_price(fingerprint: str, source_site: str, price: float) -> bool:
    """
    Update price for a specific source.

    Args:
        fingerprint: Property fingerprint
        source_site: Source website
        price: New price in EUR

    Returns:
        True if updated successfully
    """
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()

    try:
        conn.execute("""
            UPDATE listing_sources
            SET source_price_eur = ?, last_seen = ?
            WHERE property_fingerprint = ? AND source_site = ?
        """, (price, now, fingerprint, source_site))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating source price: {e}")
        return False
    finally:
        conn.close()


def set_primary_source(fingerprint: str, source_site: str) -> bool:
    """
    Mark a source as primary for a property (unmarks others).

    Args:
        fingerprint: Property fingerprint
        source_site: Source website to mark as primary

    Returns:
        True if updated successfully
    """
    conn = get_db_connection()

    try:
        # First, unmark all sources for this fingerprint
        conn.execute("""
            UPDATE listing_sources
            SET is_primary = 0
            WHERE property_fingerprint = ?
        """, (fingerprint,))

        # Then mark the specified source as primary
        conn.execute("""
            UPDATE listing_sources
            SET is_primary = 1
            WHERE property_fingerprint = ? AND source_site = ?
        """, (fingerprint, source_site))

        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error setting primary source: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# Cross-Site Duplicate Detection (Spec 106B)
# ============================================================


def get_properties_with_multiple_sources() -> List[Dict]:
    """
    Get properties that appear on 2+ sites.

    Queries listing_sources grouped by property_fingerprint,
    returns only fingerprints with multiple sources.

    Returns:
        List of dicts with:
        - fingerprint: str
        - sources: List[Dict] with source_site, source_url, source_price_eur
        - price_discrepancy: Dict or None (from PropertyMerger.get_price_discrepancy)
    """
    from data.property_merger import PropertyMerger

    conn = get_db_connection()
    merger = PropertyMerger()

    # Get fingerprints with 2+ sources
    cursor = conn.execute("""
        SELECT property_fingerprint, COUNT(*) as source_count
        FROM listing_sources
        GROUP BY property_fingerprint
        HAVING COUNT(*) >= 2
        ORDER BY source_count DESC
    """)

    fingerprints = cursor.fetchall()
    results = []

    for row in fingerprints:
        fingerprint = row["property_fingerprint"]

        # Get all sources for this fingerprint
        sources_cursor = conn.execute("""
            SELECT source_site, source_url, source_price_eur, is_primary,
                   first_seen, last_seen
            FROM listing_sources
            WHERE property_fingerprint = ?
            ORDER BY is_primary DESC, first_seen ASC
        """, (fingerprint,))

        sources = [dict(s) for s in sources_cursor.fetchall()]

        # Build listing-like dicts for price discrepancy calculation
        listings_for_discrepancy = [
            {"source_site": s["source_site"], "price_eur": s["source_price_eur"]}
            for s in sources
            if s["source_price_eur"] is not None
        ]

        price_discrepancy = merger.get_price_discrepancy(listings_for_discrepancy)

        results.append({
            "fingerprint": fingerprint,
            "sources": sources,
            "price_discrepancy": price_discrepancy,
        })

    conn.close()
    return results


def get_price_discrepancies(min_pct: float = 5.0) -> List[Dict]:
    """
    Get all properties where price difference exceeds threshold.

    Args:
        min_pct: Minimum price discrepancy percentage (default 5.0%)

    Returns:
        List of dicts sorted by discrepancy_pct descending, with:
        - fingerprint: str
        - min_price: float
        - max_price: float
        - discrepancy_pct: float
        - sources: List[Dict] with source_site and source_price_eur
    """
    # Get all properties with multiple sources
    multi_source_properties = get_properties_with_multiple_sources()

    discrepancies = []

    for prop in multi_source_properties:
        disc = prop.get("price_discrepancy")
        if disc is None:
            continue

        if disc["discrepancy_pct"] >= min_pct:
            discrepancies.append({
                "fingerprint": prop["fingerprint"],
                "min_price": disc["min_price"],
                "max_price": disc["max_price"],
                "discrepancy_pct": disc["discrepancy_pct"],
                "sources": [
                    {"source_site": s["source_site"], "source_price_eur": s["source_price_eur"]}
                    for s in prop["sources"]
                ],
            })

    # Sort by discrepancy_pct descending
    discrepancies.sort(key=lambda x: x["discrepancy_pct"], reverse=True)

    return discrepancies


def link_listing_to_sources(
    listing_id: int,
    fingerprint: str,
    source_site: str,
    url: str,
    price: float,
) -> bool:
    """
    Convenience function to add a listing to sources and check for duplicates.

    If fingerprint exists with a different source_site, logs duplicate detection.

    Args:
        listing_id: ID of the listing in listings table
        fingerprint: Property fingerprint (SHA256)
        source_site: Source website (e.g., 'imot.bg')
        url: Listing URL
        price: Price in EUR

    Returns:
        True if this is a new duplicate (same fingerprint, different site),
        False if new property or same site update
    """
    conn = get_db_connection()

    # Check for existing sources with same fingerprint but different site
    cursor = conn.execute("""
        SELECT source_site, source_url, source_price_eur
        FROM listing_sources
        WHERE property_fingerprint = ? AND source_site != ?
    """, (fingerprint, source_site))

    existing_sources = cursor.fetchall()
    is_new_duplicate = len(existing_sources) > 0

    conn.close()

    if is_new_duplicate:
        existing_sites = [s["source_site"] for s in existing_sources]
        logger.info(
            f"Duplicate detected: {source_site} listing matches existing sources: "
            f"{existing_sites} (fingerprint: {fingerprint[:16]}...)"
        )

    # Add or update the source record
    add_listing_source(
        property_fingerprint=fingerprint,
        listing_id=listing_id,
        source_site=source_site,
        source_url=url,
        source_price_eur=price,
    )

    return is_new_duplicate


# Initialize database on import
init_db()
migrate_listings_schema()
init_viewings_table()
init_change_detection_tables()
init_listing_sources_table()
