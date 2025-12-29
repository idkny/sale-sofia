"""
Fallback extraction engine for config-driven scrapers.

Tries CSS selectors in order until one returns a value.
Supports various field types for parsing extracted values.

Usage:
    from websites.generic.selector_chain import extract_field

    # Simple text extraction with fallback chain
    title = extract_field(page, ["h1.title", "h1", ".listing-title"], "text")

    # Price extraction with currency parsing
    price = extract_field(page, [".price", ".cost"], "currency_bgn_eur")
"""

import re
from typing import Any, List, Optional, Union

from loguru import logger
from scrapling import Adaptor


def get_text(element) -> Optional[str]:
    """
    Safely extract text from element.

    Args:
        element: Scrapling element

    Returns:
        Stripped text or None if element is None or empty
    """
    if element is None:
        return None

    try:
        text = element.text
        if text and text.strip():
            return text.strip()

        # Fallback: try html_content if available
        if hasattr(element, "html_content"):
            html = element.html_content
            # Strip HTML tags
            clean = re.sub(r"<[^>]+>", " ", html)
            clean = re.sub(r"\s+", " ", clean).strip()
            return clean if clean else None

        return None
    except Exception:
        return None


def get_attr(element, attr: str) -> Optional[str]:
    """
    Safely get attribute from element.

    Args:
        element: Scrapling element
        attr: Attribute name (e.g., "href", "src", "data-price")

    Returns:
        Attribute value or None if not found
    """
    if element is None:
        return None

    try:
        value = element.attrib.get(attr)
        return value.strip() if value else None
    except Exception:
        return None


def parse_text(value: str) -> str:
    """Parse as plain text (strip whitespace)."""
    return value.strip()


def parse_number(value: str) -> Optional[float]:
    """
    Extract numeric value from string.

    Handles: "123.45", "1,234.56", "1 234,56", "123 m2"

    Args:
        value: String possibly containing a number

    Returns:
        Float value or None if no number found
    """
    if not value:
        return None

    # First, extract the numeric portion (number with spaces, dots, commas)
    # This handles "123 m2" -> "123", "1 234,56 лв" -> "1 234,56"
    match = re.match(r"^[\s]*([\d\s.,\-]+)", value)
    if match:
        numeric_part = match.group(1)
    else:
        numeric_part = value

    # Remove spaces, keep digits, dots, commas, minus
    cleaned = re.sub(r"[^\d.,\-]", "", numeric_part.replace(" ", ""))

    if not cleaned:
        return None

    # Handle European format: 1.234,56 -> 1234.56
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # European: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Could be European decimal: 123,45
        # Or US thousands: 1,234
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely European decimal
            cleaned = cleaned.replace(",", ".")
        else:
            # Likely US thousands
            cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_integer(value: str) -> Optional[int]:
    """
    Extract integer value from string.

    Args:
        value: String possibly containing an integer

    Returns:
        Integer value or None if no number found
    """
    num = parse_number(value)
    return int(num) if num is not None else None


def parse_currency_bgn_eur(value: str) -> Optional[float]:
    """
    Parse Bulgarian Lev (BGN) or Euro (EUR) currency amounts.

    Handles formats:
    - "125 000 лв"
    - "125000 лв."
    - "125 000 лева"
    - "85,000" (EUR)
    - "85 000 EUR"
    - "85.000,00" (European format)

    Args:
        value: Currency string

    Returns:
        Float amount or None if parsing fails
    """
    if not value:
        return None

    # Normalize: remove currency symbols and words
    cleaned = value.upper()
    cleaned = re.sub(r"(ЛВ\.?|ЛЕВА|BGN|EUR|€|\$)", "", cleaned)
    cleaned = cleaned.strip()

    return parse_number(cleaned)


def parse_floor_pattern(value: str) -> Optional[str]:
    """
    Parse floor information from various formats.

    Handles:
    - "3/6" -> "3/6"
    - "3 от 6" -> "3/6"
    - "етаж 3" -> "3"
    - "3-ти етаж от 6" -> "3/6"
    - "партер" -> "0"
    - "сутерен" -> "-1"

    Args:
        value: Floor description string

    Returns:
        Normalized floor string or None
    """
    if not value:
        return None

    text = value.lower().strip()

    # Special floors
    if "партер" in text:
        return "0"
    if "сутерен" in text:
        return "-1"

    # Pattern: X/Y or X от Y
    match = re.search(r"(\d+)\s*(?:/|от)\s*(\d+)", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # Pattern: етаж X (от Y)?
    match = re.search(r"етаж\s*(\d+)(?:\s*(?:от|/)\s*(\d+))?", text, re.IGNORECASE)
    if match:
        floor = match.group(1)
        total = match.group(2)
        return f"{floor}/{total}" if total else floor

    # Pattern: X-ти етаж
    match = re.search(r"(\d+)[-\s]*(?:ти|ри|ви)?\s*етаж", text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Just a number
    match = re.search(r"(\d+)", text)
    if match:
        return match.group(1)

    return None


def parse_list(page: Adaptor, selector: str) -> List[str]:
    """
    Extract all matching elements as a list.

    Used for images, features, etc.

    Args:
        page: Scrapling Adaptor
        selector: CSS selector

    Returns:
        List of extracted values (text or href/src attributes)
    """
    results = []
    try:
        elements = page.css(selector)
        for el in elements:
            # Try common attributes first (for images/links)
            value = get_attr(el, "src") or get_attr(el, "href") or get_attr(el, "data-src")
            if not value:
                value = get_text(el)
            if value:
                results.append(value)
    except Exception as e:
        logger.debug(f"List extraction failed for {selector}: {e}")

    return results


def parse_field(value: str, field_type: str) -> Optional[Union[str, int, float]]:
    """
    Parse raw value based on field type.

    Args:
        value: Raw extracted value
        field_type: One of: text, number, integer, currency_bgn_eur, floor_pattern

    Returns:
        Parsed value or None if parsing fails
    """
    if not value:
        return None

    parsers = {
        "text": parse_text,
        "number": parse_number,
        "integer": parse_integer,
        "currency_bgn_eur": parse_currency_bgn_eur,
        "floor_pattern": parse_floor_pattern,
    }

    parser = parsers.get(field_type, parse_text)
    return parser(value)


def extract_field(
    page: Adaptor,
    selectors: List[str],
    field_type: str = "text",
) -> Optional[Any]:
    """
    Try selectors in order until one returns a value.

    Args:
        page: Scrapling Adaptor
        selectors: List of CSS selectors to try in order
        field_type: How to parse the result (text, number, integer,
                   currency_bgn_eur, floor_pattern, list)

    Returns:
        Extracted and parsed value, or None if all selectors fail

    Example:
        # Try multiple selectors for price
        price = extract_field(
            page,
            [".price-main", ".listing-price", "[data-price]"],
            "currency_bgn_eur"
        )
    """
    if not selectors:
        return None

    # Handle list type specially - needs multiple elements
    if field_type == "list":
        for selector in selectors:
            result = parse_list(page, selector)
            if result:
                logger.debug(f"List extraction succeeded: {selector} -> {len(result)} items")
                return result
        logger.debug(f"All list selectors failed: {selectors}")
        return []

    # Standard single-value extraction
    for selector in selectors:
        try:
            # Check for attribute extraction syntax: "selector::attr(name)"
            attr_match = re.match(r"(.+?)::attr\(([^)]+)\)$", selector)

            if attr_match:
                css_selector = attr_match.group(1)
                attr_name = attr_match.group(2)
                element = page.css_first(css_selector)
                raw_value = get_attr(element, attr_name)
            else:
                element = page.css_first(selector)
                raw_value = get_text(element)

            if raw_value:
                parsed = parse_field(raw_value, field_type)
                if parsed is not None:
                    logger.debug(f"Extraction succeeded: {selector} -> {parsed}")
                    return parsed

        except Exception as e:
            logger.debug(f"Selector failed: {selector} - {e}")
            continue

    logger.debug(f"All selectors failed for field_type={field_type}: {selectors}")
    return None
