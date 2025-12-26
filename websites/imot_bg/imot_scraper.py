"""
imot.bg scraper implementation.

Site structure:
- Search URL: https://www.imot.bg/obiavi/prodazhbi/grad-sofiya
- Pagination: append /p-{page_num} to URL
- Listing URL: https://www.imot.bg/obiava-{id}-prodava-{type}-{location}
"""

import re
from typing import List, Optional

from loguru import logger
from scrapling import Adaptor

from ..base_scraper import BaseSiteScraper, ListingData
from ..scrapling_base import ScraplingMixin
from . import selectors as sel

# LLM integration (optional - enabled via use_llm flag)
try:
    from llm import extract_description as llm_extract, get_confidence_threshold
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def get_confidence_threshold(): return 0.7  # Fallback if LLM not available


class ImotBgScraper(ScraplingMixin, BaseSiteScraper):
    """Scraper for imot.bg - largest Bulgarian real estate portal."""

    def __init__(self):
        super().__init__()
        self.site_name = "imot.bg"
        self.base_url = "https://www.imot.bg"
        self.search_base = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya"
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
        price_eur = self._extract_price_eur(page_text)
        sqm_total = self._extract_sqm(page_text)
        price_per_sqm = (price_eur / sqm_total) if (price_eur and sqm_total) else None

        floor_number, floor_total = self._extract_floor_info(page_text)
        rooms_count = self._extract_rooms_from_url(url) or self._parse_rooms(page_text)
        bathrooms_count = self._extract_bathrooms(page_text)
        building_type = self._extract_building_type(page_text)
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

        # LLM enrichment: fill gaps in CSS extraction
        if self.use_llm and LLM_AVAILABLE and description:
            try:
                llm_result = llm_extract(description)
                if llm_result.confidence >= get_confidence_threshold():
                    # Fill gaps - only override if CSS returned None
                    if rooms_count is None and llm_result.rooms:
                        rooms_count = llm_result.rooms
                    if bathrooms_count is None and llm_result.bathrooms:
                        bathrooms_count = llm_result.bathrooms
                    if condition is None and llm_result.condition:
                        condition = llm_result.condition
                    if has_elevator is None and llm_result.has_elevator is not None:
                        has_elevator = llm_result.has_elevator
                    if has_parking is None and llm_result.has_parking is not None:
                        has_parking = llm_result.has_parking
                    if has_balcony is None and llm_result.has_balcony is not None:
                        has_balcony = llm_result.has_balcony
                    if has_storage is None and llm_result.has_storage is not None:
                        has_storage = llm_result.has_storage
                    if orientation is None and llm_result.orientation:
                        orientation = llm_result.orientation
                    if heating_type is None and llm_result.heating_type:
                        heating_type = llm_result.heating_type
                    logger.debug(f"LLM enriched listing {external_id} (confidence: {llm_result.confidence:.2f})")
            except Exception as e:
                logger.warning(f"LLM extraction failed for {external_id}: {e}")

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

        for link in self.css(
            page,
            "a[href]",
            identifier="imot_listing_links",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            href = self.get_attr(link, "href")

            # Check if link matches listing pattern
            if all(pattern in href for pattern in sel.LISTING_LINK_CONTAINS):
                # Normalize URL
                if href.startswith("//"):
                    full_url = "https:" + href
                elif href.startswith("/"):
                    full_url = self.base_url + href
                else:
                    full_url = href

                if full_url not in listing_urls:
                    listing_urls.append(full_url)

        logger.info(f"Found {len(listing_urls)} listings on search page")
        return listing_urls

    def is_last_page(self, html: str, current_page: int) -> bool:
        """
        Detect if this is the last page of search results.

        Args:
            html: Search results page HTML
            current_page: Current page number (1-indexed)

        Returns:
            True if this is the last page
        """
        page = self.parse(html)
        page_text = self.get_page_text(page).lower()

        if self._has_no_results_message(page_text):
            logger.debug("Last page detected: found 'no results' message")
            return True
        if self._has_no_listings(page):
            logger.debug("Last page detected: no listings found")
            return True
        if not self._has_next_page_link(page, current_page):
            logger.debug(f"Last page detected: no link to page {current_page + 1}")
            return True
        if self._is_past_total_pages(page_text, current_page):
            logger.debug("Last page detected: current page at or past total")
            return True
        return False

    def _has_no_results_message(self, page_text: str) -> bool:
        """Check if page contains 'no results' message."""
        for pattern in sel.NO_RESULTS_PATTERNS:
            if pattern.lower() in page_text:
                return True
        return False

    def _has_no_listings(self, page: Adaptor) -> bool:
        """Check if no listing links found on page."""
        for link in self.css(page, "a[href]"):
            href = self.get_attr(link, "href")
            if all(p in href for p in sel.LISTING_LINK_CONTAINS):
                return False  # Found at least one listing
        return True  # No listings found

    def _has_next_page_link(self, page: Adaptor, current_page: int) -> bool:
        """Check if link to next page exists."""
        next_page = current_page + 1
        for link in self.css(
            page,
            "a[href]",
            identifier="imot_pagination",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            href = self.get_attr(link, "href")
            if f"/p-{next_page}" in href:
                return True
            if self.get_text(link) == str(next_page):
                return True
        return False

    def _is_past_total_pages(self, page_text: str, current_page: int) -> bool:
        """Check if current page is at or past total pages."""
        total_match = re.search(r"(?:от|/)\s*(\d+)\s*(?:стр|page)?", page_text)
        if total_match:
            try:
                total_pages = int(total_match.group(1))
                return current_page >= total_pages
            except ValueError:
                pass
        return False

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

        # Handle query parameters - page goes before them
        if "?" in base:
            parts = base.split("?", 1)
            return f"{parts[0]}/p-{next_page}?{parts[1]}"

        return f"{base}/p-{next_page}"

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
        return f"{self.search_base}/p-{page}"

    # =========================================================================
    # PRIVATE EXTRACTION METHODS
    # =========================================================================

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract listing ID from URL."""
        match = re.search(sel.LISTING_ID_PATTERN, url)
        return match.group(1) if match else None

    def _extract_price_eur(self, text: str) -> Optional[float]:
        """Extract price in EUR from page text."""
        for pattern in sel.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(" ", "").replace("\xa0", "")
                try:
                    return float(price_str)
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
            if any(kw in text_lower for kw in keywords):
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
                if re.search(pattern, text_lower):
                    return act_status

        # If building is old (no act mentioned but has year < 2000), it's act16
        year_match = re.search(r"(?:година|год\.|г\.?)\s*(\d{4})|(\d{4})\s*(?:г\.?|год)", text_lower)
        if year_match:
            year = int(year_match.group(1) or year_match.group(2))
            if year < 2000:
                return "act16"  # Old buildings are fully permitted

        return None

    def _extract_location(self, url: str, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract district and neighborhood from URL and text."""
        district = "София"  # Default for Sofia search
        neighborhood = None

        # Try to extract neighborhood from URL
        url_match = re.search(sel.NEIGHBORHOOD_URL_PATTERN, url.lower())
        if url_match:
            neighborhood = url_match.group(1).replace("-", " ").title()

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
            if any(kw in text_lower for kw in keywords):
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
            if any(kw in text_lower for kw in keywords):
                return heating_type

        return None

    def _extract_images(self, page: Adaptor) -> List[str]:
        """Extract image URLs from the page."""
        images = []

        # Look for images in img tags
        for img in self.css(
            page,
            "img",
            identifier="imot_images",
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
            identifier="imot_image_links",
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
            identifier="imot_title",
            auto_save=True,
            auto_match=self.adaptive_mode,
        )
        if title_tag:
            return self.get_text(title_tag)

        # Try h1
        h1 = self.css_first(
            page,
            "h1",
            identifier="imot_h1",
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
            identifier="imot_description",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            text = self.get_text(div)
            if len(text) > 100 and len(text) < 2000:
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

        # Look for agency subdomain links
        for link in self.css(
            page,
            "a[href]",
            identifier="imot_contact_links",
            auto_save=True,
            auto_match=self.adaptive_mode,
        ):
            href = self.get_attr(link, "href")
            if ".imot.bg" in href and "www.imot.bg" not in href:
                agency_match = re.search(sel.AGENCY_SUBDOMAIN_PATTERN, href)
                if agency_match:
                    agency = agency_match.group(1)
                    break

        return agency, agent_name, agent_phone
