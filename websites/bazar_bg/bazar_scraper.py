"""
bazar.bg scraper implementation.

Site structure:
- Search URL: https://bazar.bg/obiavi/apartamenti/sofia
- Pagination: ?page=N (page 1 has no parameter)
- Listing URL: https://bazar.bg/obiava-{id}/{slug}
"""

import re
from typing import List, Optional

from loguru import logger
from scrapling import Adaptor

from ..base_scraper import BaseSiteScraper, ListingData
from ..scrapling_base import ScraplingMixin
from . import selectors as sel


class BazarBgScraper(ScraplingMixin, BaseSiteScraper):
    """Scraper for bazar.bg - Bulgarian classifieds site."""

    def __init__(self):
        super().__init__()
        self.site_name = "bazar.bg"
        self.base_url = "https://bazar.bg"
        self.search_base = "https://bazar.bg/obiavi/apartamenti/sofia"
        self.adaptive_mode = True  # Enable adaptive matching for selector resilience

    # =========================================================================
    # PUBLIC METHODS (required by BaseSiteScraper)
    # =========================================================================

    async def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
        """
        Extract listing data from a single property page.

        Args:
            html: Page HTML content
            url: Page URL

        Returns:
            ListingData object or None if extraction failed
        """
        page = self.parse(html, url)

        # Extract ID from URL
        external_id = self._extract_id_from_url(url)
        if not external_id:
            logger.warning(f"Could not extract listing ID from URL: {url}")
            return None

        # Get page text for regex extraction
        page_text = self.get_page_text(page)

        # Extract all fields
        price_eur = self._extract_price_eur(html, page_text)
        sqm_total = self._extract_sqm(page_text)
        price_per_sqm = (price_eur / sqm_total) if (price_eur and sqm_total) else None

        floor_number, floor_total = self._extract_floor_info(page_text)
        rooms_count = self._extract_rooms_from_url(url) or self._parse_rooms(page_text)
        bathrooms_count = self._extract_bathrooms(page_text)
        building_type = self._extract_building_type(page_text)
        construction_year = self._extract_construction_year(page_text)
        act_status = self._extract_act_status(page_text)
        district, neighborhood = self._extract_location(url, page_text)
        metro_station, metro_distance = self._extract_metro_info(page_text)
        condition = self._extract_condition(page_text)

        # Extract features
        has_elevator = self._has_feature(page_text, sel.FEATURES["elevator"])
        has_balcony = self._has_feature(page_text, sel.FEATURES["balcony"])
        has_parking = self._has_feature(page_text, sel.FEATURES["parking"])
        has_storage = self._has_feature(page_text, sel.FEATURES["storage"])
        has_garden = self._has_feature(page_text, sel.FEATURES["garden"])

        orientation = self._extract_orientation(page_text)
        heating_type = self._extract_heating(page_text)
        image_urls = self._extract_images(page)
        title = self._extract_title(page, url)
        description = self._extract_description(page)
        agency, agent_name, agent_phone = self._extract_contact(page, page_text)

        listing = ListingData(
            external_id=external_id,
            url=url,
            source_site=self.site_name,
            title=title,
            description=description,
            price_eur=price_eur,
            price_per_sqm_eur=price_per_sqm,
            sqm_total=sqm_total,
            rooms_count=rooms_count,
            bathrooms_count=bathrooms_count,
            floor_number=floor_number,
            floor_total=floor_total,
            has_elevator=has_elevator,
            building_type=building_type,
            construction_year=construction_year,
            act_status=act_status,
            district=district,
            neighborhood=neighborhood,
            metro_station=metro_station,
            metro_distance_m=metro_distance,
            condition=condition,
            orientation=orientation,
            has_balcony=has_balcony,
            has_garden=has_garden,
            has_parking=has_parking,
            has_storage=has_storage,
            heating_type=heating_type,
            image_urls=image_urls,
            main_image_url=image_urls[0] if image_urls else None,
            agency=agency,
            agent_name=agent_name,
            agent_phone=agent_phone,
        )

        logger.debug(f"Extracted listing {external_id}: {price_eur} EUR, {sqm_total} sqm")
        return listing

    async def extract_search_results(self, html: str) -> List[str]:
        """
        Extract listing URLs from a search results page.

        Args:
            html: Search results page HTML

        Returns:
            List of listing URLs
        """
        page = self.parse(html)
        listing_urls = []

        # Find all listing links using the CSS selector
        for link in self.css(
            page,
            sel.LISTING_LINK,
            identifier="bazar_listing_links",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            href = self.get_attr(link, sel.LISTING_URL_ATTR)
            if not href:
                continue

            # Check if link matches listing pattern
            if self._is_listing_link(href):
                full_url = self._normalize_url(href)
                if full_url not in listing_urls:
                    listing_urls.append(full_url)

        logger.info(f"Found {len(listing_urls)} listings on search page")
        return listing_urls

    def is_last_page(self, html: str, current_page: int) -> bool:
        """
        Detect if this is the last page of search results.

        Detection methods (in order):
        1. Check for "no results" message
        2. Check if no listings found
        3. Extract maxPage from JavaScript and compare
        4. Check if next page link is missing/disabled

        Args:
            html: Search results page HTML
            current_page: Current page number (1-indexed)

        Returns:
            True if this is the last page
        """
        page = self.parse(html)
        page_text = self.get_page_text(page)

        # Method 1: Check for "no results" message
        for pattern in sel.NO_RESULTS_PATTERNS:
            if pattern.lower() in page_text.lower():
                logger.debug(f"Last page detected: found '{pattern}'")
                return True

        # Method 2: Check if no listings on page
        listing_links = self.css(
            page,
            sel.LISTING_LINK,
            identifier="bazar_pagination",
            auto_save=True,
            auto_match=self.adaptive_mode,
        )
        if len(listing_links) == 0:
            logger.debug("Last page detected: no listings found")
            return True

        # Method 3: Extract maxPage from JavaScript
        max_page_match = re.search(sel.MAX_PAGE_JS_PATTERN, html)
        if max_page_match:
            try:
                max_page = int(max_page_match.group(1))
                if current_page >= max_page:
                    logger.debug(f"Last page detected: page {current_page} >= maxPage {max_page}")
                    return True
            except ValueError:
                pass

        # Method 4: Check for next page link
        # Look for "Следваща" (Next) text in page
        for next_text in sel.NEXT_PAGE_SELECTORS:
            if next_text in page_text:
                # Next button exists, not last page
                return False

        # If we can't find next button, might be last page
        logger.debug(f"No next button found on page {current_page}, assuming last page")
        return True

    def get_next_page_url(self, current_url: str, current_page: int) -> str:
        """
        Get the URL for the next page of search results.

        Args:
            current_url: Current search URL
            current_page: Current page number (1-indexed)

        Returns:
            URL for the next page
        """
        next_page = current_page + 1

        # Remove existing page parameter if present
        base = re.sub(sel.PAGE_URL_PATTERN, "", current_url)

        # Remove trailing ? or & if they exist
        base = base.rstrip("?&")

        # Add page parameter
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}page={next_page}"

    def get_search_url(self, page: int = 1) -> str:
        """
        Get the search URL for Sofia apartments.

        Args:
            page: Page number (1-indexed)

        Returns:
            Search URL
        """
        if page == 1:
            return self.search_base

        return f"{self.search_base}?page={page}"

    # =========================================================================
    # PRIVATE EXTRACTION METHODS
    # =========================================================================

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract listing ID from URL."""
        match = re.search(sel.LISTING_ID_PATTERN, url)
        return match.group(1) if match else None

    def _extract_price_eur(self, html: str, text: str) -> Optional[float]:
        """Extract price in EUR from page HTML and text."""
        # First try JavaScript variables (most reliable)
        price_match = re.search(sel.AD_PRICE_JS, html)
        currency_match = re.search(sel.AD_CURRENCY_JS, html)

        if price_match and currency_match:
            price_str = price_match.group(1)
            currency = currency_match.group(1)

            try:
                price = float(price_str)
                # If currency is BGN (лв), convert to EUR (approximate rate: 1 EUR = 1.95583 BGN)
                if currency == "лв":
                    price = price / 1.95583
                return price
            except ValueError:
                pass

        # Fallback to text patterns
        for pattern in sel.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(" ", "").replace("\xa0", "").replace(",", "")
                try:
                    price = float(price_str)
                    # Check if this is EUR or BGN based on the pattern
                    if "€" in pattern or "EUR" in pattern:
                        return price
                    elif "лв" in pattern:
                        # Convert BGN to EUR
                        return price / 1.95583
                except ValueError:
                    continue

        return None

    def _extract_sqm(self, text: str) -> Optional[float]:
        """Extract square meters from page text."""
        for pattern in sel.SQM_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sqm_str = match.group(1).replace(",", ".").replace(" ", "")
                try:
                    return float(sqm_str)
                except ValueError:
                    continue
        return None

    def _extract_floor_info(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract floor number and total floors."""
        # Try patterns with total floors first
        for pattern in sel.FLOOR_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1)), int(match.group(2))
                except (ValueError, IndexError):
                    continue

        # Try floor number only
        floor_match = re.search(sel.FLOOR_NUMBER_ONLY_PATTERN, text, re.IGNORECASE)
        if floor_match:
            try:
                return int(floor_match.group(1)), None
            except ValueError:
                pass

        return None, None

    def _extract_rooms_from_url(self, url: str) -> Optional[int]:
        """Extract room count from URL slug."""
        url_lower = url.lower()
        for slug, count in sel.ROOM_SLUGS.items():
            if slug in url_lower:
                return count
        return None

    def _parse_rooms(self, text: str) -> Optional[int]:
        """Parse room count from Bulgarian text."""
        text_lower = text.lower()

        # Try numeric pattern first: "3-стаен"
        match = re.search(sel.ROOM_NUMERIC_PATTERN, text_lower)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        # Try Bulgarian word mappings
        for word, count in sel.ROOM_WORDS_BG.items():
            if word in text_lower:
                return count

        return None

    def _extract_construction_year(self, text: str) -> Optional[int]:
        """Extract construction year from page text."""
        match = re.search(sel.CONSTRUCTION_YEAR_PATTERN, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    def _extract_bathrooms(self, text: str) -> Optional[int]:
        """Extract bathroom count from page text."""
        text_lower = text.lower()

        # Check for explicit "2 бани" patterns first
        for keyword in sel.TWO_BATHROOM_KEYWORDS:
            if keyword in text_lower:
                return 2

        # Try regex patterns
        for pattern in sel.BATHROOM_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        # Default: if "баня" mentioned but no count, assume 1
        if any(w in text_lower for w in ["баня", "санитар", "wc", "тоалетна"]):
            return 1

        return None

    def _extract_building_type(self, text: str) -> Optional[str]:
        """Extract building construction type."""
        text_lower = text.lower()

        for building_type, keywords in sel.BUILDING_TYPES.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return building_type

        return None

    def _extract_act_status(self, text: str) -> Optional[str]:
        """
        Extract construction act status.

        Bulgarian construction stages:
        - Act 14: Rough construction complete (груб строеж)
        - Act 15: Building systems installed (въвеждане в експлоатация)
        - Act 16: Ready for occupancy (разрешение за ползване)
        """
        text_lower = text.lower()

        for act_status, patterns in sel.ACT_STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return act_status

        # If building is old (has year < 2000), it's act16
        year = self._extract_construction_year(text)
        if year and year < 2000:
            return "act16"

        return None

    def _extract_location(self, url: str, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract district and neighborhood from URL and text."""
        district = "София"  # Default for Sofia search
        neighborhood = None

        # Try to extract neighborhood from URL
        url_match = re.search(sel.NEIGHBORHOOD_URL_PATTERN, url.lower())
        if url_match:
            # Get the slug and convert to title case
            slug = url_match.group(1)
            # Remove "gr-" prefix if present
            slug = slug.replace("gr-", "")
            # Convert dashes to spaces and title case
            neighborhood = slug.replace("-", " ").title()

        # If not found in URL, try from page text
        if not neighborhood:
            location_match = re.search(sel.LOCATION_PATTERN, text)
            if location_match:
                neighborhood = location_match.group(1).strip()

        return district, neighborhood

    def _extract_metro_info(self, text: str) -> tuple[Optional[str], Optional[int]]:
        """
        Extract nearest metro station and distance.

        Returns:
            Tuple of (station_name, distance_in_meters)
        """
        text_lower = text.lower()
        station = None
        distance = None

        # Find metro station name
        for metro_station in sel.SOFIA_METRO_STATIONS:
            if metro_station in text_lower:
                station = metro_station.title()
                break

        # Find distance to metro
        for pattern in sel.METRO_DISTANCE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    distance = int(match.group(1))
                    break
                except ValueError:
                    continue

        # Generic "близо до метро" without distance
        if station is None and "метро" in text_lower:
            # Check for "до метро" or "близо до метро"
            if any(phrase in text_lower for phrase in ["до метро", "близо до метро", "метростанция"]):
                station = "nearby"  # Indicates metro access but unknown station

        return station, distance

    def _extract_condition(self, text: str) -> Optional[str]:
        """Extract apartment condition."""
        text_lower = text.lower()

        for condition, keywords in sel.CONDITION_TYPES.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return condition

        return None

    def _has_feature(self, text: str, keywords: List[str]) -> Optional[bool]:
        """Check if text contains any of the feature keywords."""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return None  # Unknown, not False

    def _extract_orientation(self, text: str) -> Optional[str]:
        """Extract orientation (compass direction)."""
        text_lower = text.lower()
        orientations = []

        for bg_word, direction in sel.ORIENTATION_MAPPING.items():
            if bg_word in text_lower:
                if direction not in orientations:
                    orientations.append(direction)

        return "/".join(orientations) if orientations else None

    def _extract_heating(self, text: str) -> Optional[str]:
        """Extract heating type."""
        text_lower = text.lower()

        for heating_type, keywords in sel.HEATING_TYPES.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return heating_type

        return None

    def _extract_images(self, page: Adaptor) -> List[str]:
        """Extract image URLs from the page."""
        images = []

        # Look for images in img tags
        for img in self.css(
            page,
            "img",
            identifier="bazar_images",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            src = self.get_attr(img, "src") or self.get_attr(img, "data-src") or ""

            if re.search(sel.IMAGE_HOST_PATTERN, src):
                if src.startswith("//"):
                    src = "https:" + src
                if src not in images:
                    images.append(src)

        # Also look in anchor tags (carousel/lightbox)
        for link in self.css(
            page,
            "a[href]",
            identifier="bazar_image_links",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            href = self.get_attr(link, "href")
            if re.search(sel.IMAGE_HOST_PATTERN, href):
                if any(ext in href.lower() for ext in sel.IMAGE_EXTENSIONS):
                    if href.startswith("//"):
                        href = "https:" + href
                    if href not in images:
                        images.append(href)

        return images

    def _extract_title(self, page: Adaptor, url: str) -> Optional[str]:
        """Extract listing title."""
        # Try meta title
        title_tag = self.css_first(
            page,
            "title",
            identifier="bazar_title",
            auto_save=True,
            auto_match=self.adaptive_mode,
        )
        if title_tag:
            return self.get_text(title_tag)

        # Try h1
        h1 = self.css_first(
            page,
            "h1",
            identifier="bazar_h1",
            auto_save=True,
            auto_match=self.adaptive_mode,
        )
        if h1:
            return self.get_text(h1)

        # Generate from URL
        return url.split("/")[-1].replace("-", " ").title()

    def _extract_description(self, page: Adaptor) -> Optional[str]:
        """Extract listing description."""
        # Find text blocks containing property keywords
        for div in self.css(
            page,
            "div",
            identifier="bazar_description",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            text = self.get_text(div)
            if len(text) > 100 and len(text) < 5000:
                if any(kw in text.lower() for kw in sel.DESCRIPTION_KEYWORDS):
                    return text

        return None

    def _extract_contact(
        self, page: Adaptor, text: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract agency, agent name, and phone."""
        agency = None
        agent_name = None
        agent_phone = None

        # Try to find phone numbers
        phone_match = re.search(sel.PHONE_PATTERN, text)
        if phone_match:
            agent_phone = phone_match.group(0).replace(" ", "")

        # bazar.bg doesn't use agency subdomains, but we can try to find agency name in text
        # Agency names are usually in specific sections, but without HTML structure analysis
        # we'll leave it as None for now

        return agency, agent_name, agent_phone

    def _normalize_url(self, href: str) -> str:
        """Normalize relative/absolute URLs."""
        if href.startswith("//"):
            return "https:" + href
        elif href.startswith("/"):
            return self.base_url + href
        else:
            return href

    def _is_listing_link(self, href: str) -> bool:
        """Check if link is a listing URL."""
        return all(pattern in href for pattern in sel.LISTING_LINK_CONTAINS)
