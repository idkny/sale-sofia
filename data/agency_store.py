# data/agency_store.py
"""
Agency database management for storing and querying real estate agencies.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from paths import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_agencies_table():
    """Create agencies table if it doesn't exist."""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS agencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Basic info
            name TEXT UNIQUE NOT NULL,
            website TEXT,

            -- Commission
            commission TEXT,
            min_commission_eur REAL,

            -- Languages & Service
            english_level TEXT,
            other_languages TEXT,

            -- Coverage
            coverage_areas TEXT,

            -- Reputation
            reputation TEXT,
            notes TEXT,

            -- Tier (recommended, neutral, avoid)
            tier TEXT DEFAULT 'neutral',

            -- Metadata
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_agencies_name ON agencies(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agencies_tier ON agencies(tier)")

    conn.commit()
    conn.close()
    logger.info("Agencies table initialized")


def add_agency_id_to_listings():
    """Add agency_id foreign key column to listings table if not exists."""
    conn = get_db_connection()

    # Check if column exists
    cursor = conn.execute("PRAGMA table_info(listings)")
    columns = [row[1] for row in cursor.fetchall()]

    if "agency_id" not in columns:
        conn.execute("ALTER TABLE listings ADD COLUMN agency_id INTEGER REFERENCES agencies(id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_agency_id ON listings(agency_id)")
        conn.commit()
        logger.info("Added agency_id column to listings table")
    else:
        logger.debug("agency_id column already exists in listings")

    conn.close()


def save_agency(
    name: str,
    website: Optional[str] = None,
    commission: Optional[str] = None,
    min_commission_eur: Optional[float] = None,
    english_level: Optional[str] = None,
    other_languages: Optional[str] = None,
    coverage_areas: Optional[str] = None,
    reputation: Optional[str] = None,
    notes: Optional[str] = None,
    tier: str = "neutral"
) -> Optional[int]:
    """
    Save or update an agency in the database.

    Returns:
        Agency ID or None if failed
    """
    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO agencies (
                name, website, commission, min_commission_eur,
                english_level, other_languages, coverage_areas,
                reputation, notes, tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                website = COALESCE(excluded.website, agencies.website),
                commission = COALESCE(excluded.commission, agencies.commission),
                min_commission_eur = COALESCE(excluded.min_commission_eur, agencies.min_commission_eur),
                english_level = COALESCE(excluded.english_level, agencies.english_level),
                other_languages = COALESCE(excluded.other_languages, agencies.other_languages),
                coverage_areas = COALESCE(excluded.coverage_areas, agencies.coverage_areas),
                reputation = COALESCE(excluded.reputation, agencies.reputation),
                notes = COALESCE(excluded.notes, agencies.notes),
                tier = excluded.tier,
                updated_at = CURRENT_TIMESTAMP
        """, (
            name, website, commission, min_commission_eur,
            english_level, other_languages, coverage_areas,
            reputation, notes, tier
        ))

        conn.commit()
        agency_id = cursor.lastrowid
        logger.info(f"Saved agency: {name}")
        return agency_id

    except sqlite3.Error as e:
        logger.error(f"Database error saving agency: {e}")
        return None
    finally:
        conn.close()


def get_agency_by_name(name: str) -> Optional[sqlite3.Row]:
    """Get an agency by name (case-insensitive partial match)."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM agencies WHERE LOWER(name) LIKE LOWER(?)",
        (f"%{name}%",)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_agency_by_id(agency_id: int) -> Optional[sqlite3.Row]:
    """Get an agency by ID."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM agencies WHERE id = ?", (agency_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_all_agencies(tier: Optional[str] = None) -> List[sqlite3.Row]:
    """Get all agencies, optionally filtered by tier."""
    conn = get_db_connection()

    if tier:
        cursor = conn.execute(
            "SELECT * FROM agencies WHERE tier = ? ORDER BY name",
            (tier,)
        )
    else:
        cursor = conn.execute("SELECT * FROM agencies ORDER BY tier, name")

    rows = cursor.fetchall()
    conn.close()
    return rows


def link_listing_to_agency(listing_id: int, agency_id: int) -> bool:
    """Link a listing to an agency."""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE listings SET agency_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (agency_id, listing_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error linking listing {listing_id} to agency {agency_id}: {e}")
        return False
    finally:
        conn.close()


def get_listings_by_agency(agency_id: int) -> List[sqlite3.Row]:
    """Get all listings for a specific agency."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM listings WHERE agency_id = ? AND is_active = 1 ORDER BY scraped_at DESC",
        (agency_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def import_agencies_from_markdown(markdown_content: str) -> int:
    """
    Parse agencies from markdown content and import to database.

    Returns:
        Number of agencies imported
    """
    import re

    agencies_data = []

    # Parse the "Top Agencies" section
    # Pattern: ### Agency Name followed by table with | Field | Info |
    agency_pattern = r"### (.+?)\n\| Field \| Info \|\n\|[-\|]+\|\n((?:\| .+ \| .+ \|\n)+)"

    matches = re.findall(agency_pattern, markdown_content)

    for name, table_content in matches:
        agency = {"name": name.strip(), "tier": "recommended"}

        # Parse table rows
        rows = re.findall(r"\| (.+?) \| (.+?) \|", table_content)
        for field, info in rows:
            field = field.strip().lower()
            info = info.strip()

            if field == "website":
                agency["website"] = info
            elif field == "commission":
                agency["commission"] = info
                # Try to extract min commission
                min_match = re.search(r"min[:\s]+(\d+(?:,\d+)?)\s*EUR", info, re.IGNORECASE)
                if min_match:
                    agency["min_commission_eur"] = float(min_match.group(1).replace(",", ""))
            elif field == "english":
                agency["english_level"] = info
            elif "language" in field:
                agency["other_languages"] = info
            elif field == "coverage":
                agency["coverage_areas"] = info
            elif field == "reputation":
                agency["reputation"] = info

        agencies_data.append(agency)

    # Import to database
    count = 0
    for agency in agencies_data:
        result = save_agency(
            name=agency["name"],
            website=agency.get("website"),
            commission=agency.get("commission"),
            min_commission_eur=agency.get("min_commission_eur"),
            english_level=agency.get("english_level"),
            other_languages=agency.get("other_languages"),
            coverage_areas=agency.get("coverage_areas"),
            reputation=agency.get("reputation"),
            tier=agency.get("tier", "neutral")
        )
        if result:
            count += 1

    logger.info(f"Imported {count} agencies from markdown")
    return count


def print_agencies_summary():
    """Print a summary of all agencies in the database."""
    agencies = get_all_agencies()

    if not agencies:
        print("No agencies in database.")
        return

    print(f"\n{'='*60}")
    print(f"{'AGENCIES DATABASE':^60}")
    print(f"{'='*60}\n")

    for agency in agencies:
        print(f"[{agency['tier'].upper()}] {agency['name']}")
        if agency['website']:
            print(f"  Website: {agency['website']}")
        if agency['commission']:
            print(f"  Commission: {agency['commission']}")
        if agency['coverage_areas']:
            print(f"  Coverage: {agency['coverage_areas']}")
        print()


# Initialize tables on import
init_agencies_table()
add_agency_id_to_listings()


if __name__ == "__main__":
    # CLI for quick agency management
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            print_agencies_summary()

        elif cmd == "import" and len(sys.argv) > 2:
            filepath = sys.argv[2]
            with open(filepath, "r") as f:
                content = f.read()
            count = import_agencies_from_markdown(content)
            print(f"Imported {count} agencies")

        elif cmd == "search" and len(sys.argv) > 2:
            name = sys.argv[2]
            agency = get_agency_by_name(name)
            if agency:
                print(f"Found: {agency['name']}")
                print(f"  Website: {agency['website']}")
                print(f"  Commission: {agency['commission']}")
                print(f"  Tier: {agency['tier']}")
            else:
                print(f"No agency found matching '{name}'")

        else:
            print("Usage:")
            print("  python agency_store.py list              - List all agencies")
            print("  python agency_store.py import <file.md>  - Import from markdown")
            print("  python agency_store.py search <name>     - Search by name")
    else:
        print_agencies_summary()
