"""
Website scrapers for Bulgarian real estate sites.

Usage:
    from websites import get_scraper, AVAILABLE_SITES

    scraper = get_scraper("imot.bg")
    listing = await scraper.extract_listing(html, url)
"""

from typing import Optional
from .base_scraper import BaseSiteScraper, ListingData

# Registry of available sites
AVAILABLE_SITES = {
    "imot.bg": {
        "description": "Largest Bulgarian RE portal",
        "implemented": True,
        "url": "https://www.imot.bg",
    },
    "bazar.bg": {
        "description": "Bulgarian classifieds - real estate section",
        "implemented": True,
        "url": "https://bazar.bg",
    },
    "homes.bg": {
        "description": "Modern RE portal (JSON in page)",
        "implemented": False,
        "url": "https://www.homes.bg",
    },
    "alo.bg": {
        "description": "Classifieds portal",
        "implemented": False,
        "url": "https://www.alo.bg",
    },
    "imoti.net": {
        "description": "Established RE portal",
        "implemented": False,
        "url": "https://www.imoti.net",
    },
}


def get_scraper(site: str) -> Optional[BaseSiteScraper]:
    """
    Get the scraper instance for a given site.

    Args:
        site: Site name (e.g., "imot.bg")

    Returns:
        Scraper instance or None if site not supported/implemented
    """
    if site not in AVAILABLE_SITES:
        return None

    if not AVAILABLE_SITES[site].get("implemented"):
        print(f"[WARNING] Scraper for {site} not yet implemented")
        return None

    # Import and instantiate the appropriate scraper
    if site == "imot.bg":
        from .imot_bg.imot_scraper import ImotBgScraper
        return ImotBgScraper()
    elif site == "bazar.bg":
        from .bazar_bg.bazar_scraper import BazarBgScraper
        return BazarBgScraper()
    elif site == "homes.bg":
        from .homes_bg.scraper import HomesBgScraper
        return HomesBgScraper()

    return None


__all__ = ["get_scraper", "AVAILABLE_SITES", "BaseSiteScraper", "ListingData"]
