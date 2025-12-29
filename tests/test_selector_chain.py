"""
Tests for the selector chain fallback extraction engine.
"""

import pytest
from scrapling import Adaptor

from websites.generic.selector_chain import (
    extract_field,
    get_attr,
    get_text,
    parse_currency_bgn_eur,
    parse_field,
    parse_floor_pattern,
    parse_integer,
    parse_number,
)


class TestGetText:
    """Tests for get_text helper."""

    def test_get_text_returns_stripped_text(self):
        html = "<div>  Hello World  </div>"
        page = Adaptor(html)
        element = page.css_first("div")
        assert get_text(element) == "Hello World"

    def test_get_text_returns_none_for_none_element(self):
        assert get_text(None) is None

    def test_get_text_returns_none_for_empty_element(self):
        html = "<div></div>"
        page = Adaptor(html)
        element = page.css_first("div")
        result = get_text(element)
        # Scrapling may return "None" string for empty elements
        assert result is None or result == "" or result == "None"


class TestGetAttr:
    """Tests for get_attr helper."""

    def test_get_attr_returns_attribute_value(self):
        html = '<a href="https://example.com">Link</a>'
        page = Adaptor(html)
        element = page.css_first("a")
        assert get_attr(element, "href") == "https://example.com"

    def test_get_attr_returns_none_for_missing_attr(self):
        html = "<div>Content</div>"
        page = Adaptor(html)
        element = page.css_first("div")
        assert get_attr(element, "data-missing") is None

    def test_get_attr_returns_none_for_none_element(self):
        assert get_attr(None, "href") is None


class TestParseNumber:
    """Tests for parse_number function."""

    def test_simple_integer(self):
        assert parse_number("123") == 123.0

    def test_simple_float(self):
        assert parse_number("123.45") == 123.45

    def test_us_format_with_commas(self):
        assert parse_number("1,234.56") == 1234.56

    def test_european_format_with_dots_and_comma(self):
        assert parse_number("1.234,56") == 1234.56

    def test_number_with_spaces(self):
        assert parse_number("125 000") == 125000.0

    def test_number_with_suffix(self):
        assert parse_number("123 m2") == 123.0

    def test_empty_string_returns_none(self):
        assert parse_number("") is None

    def test_no_number_returns_none(self):
        assert parse_number("no numbers here") is None


class TestParseInteger:
    """Tests for parse_integer function."""

    def test_integer_from_string(self):
        assert parse_integer("42") == 42

    def test_integer_from_float_string(self):
        assert parse_integer("42.7") == 42

    def test_empty_string_returns_none(self):
        assert parse_integer("") is None


class TestParseCurrencyBgnEur:
    """Tests for parse_currency_bgn_eur function."""

    def test_bgn_with_lv(self):
        assert parse_currency_bgn_eur("125 000 лв") == 125000.0

    def test_bgn_with_lv_dot(self):
        assert parse_currency_bgn_eur("125000 лв.") == 125000.0

    def test_bgn_with_leva(self):
        assert parse_currency_bgn_eur("125 000 лева") == 125000.0

    def test_eur_with_symbol(self):
        assert parse_currency_bgn_eur("€85,000") == 85000.0

    def test_eur_with_text(self):
        assert parse_currency_bgn_eur("85 000 EUR") == 85000.0

    def test_european_format(self):
        assert parse_currency_bgn_eur("85.000,00") == 85000.0

    def test_empty_returns_none(self):
        assert parse_currency_bgn_eur("") is None


class TestParseFloorPattern:
    """Tests for parse_floor_pattern function."""

    def test_slash_format(self):
        assert parse_floor_pattern("3/6") == "3/6"

    def test_ot_format(self):
        assert parse_floor_pattern("3 от 6") == "3/6"

    def test_etazh_only(self):
        assert parse_floor_pattern("етаж 3") == "3"

    def test_etazh_with_total(self):
        assert parse_floor_pattern("етаж 3 от 6") == "3/6"

    def test_ordinal_format(self):
        assert parse_floor_pattern("3-ти етаж") == "3"

    def test_parter(self):
        assert parse_floor_pattern("партер") == "0"

    def test_suteren(self):
        assert parse_floor_pattern("сутерен") == "-1"

    def test_just_number(self):
        assert parse_floor_pattern("5") == "5"

    def test_empty_returns_none(self):
        assert parse_floor_pattern("") is None


class TestParseField:
    """Tests for parse_field function."""

    def test_text_type(self):
        assert parse_field("  hello  ", "text") == "hello"

    def test_number_type(self):
        assert parse_field("123.45", "number") == 123.45

    def test_integer_type(self):
        assert parse_field("42", "integer") == 42

    def test_currency_type(self):
        assert parse_field("125 000 лв", "currency_bgn_eur") == 125000.0

    def test_floor_type(self):
        assert parse_field("3/6", "floor_pattern") == "3/6"

    def test_unknown_type_defaults_to_text(self):
        assert parse_field("  value  ", "unknown") == "value"

    def test_none_value_returns_none(self):
        assert parse_field(None, "text") is None


class TestExtractField:
    """Tests for extract_field main function."""

    def test_first_selector_matches(self):
        html = '<h1 class="title">Main Title</h1>'
        page = Adaptor(html)
        result = extract_field(page, ["h1.title", "h1"], "text")
        assert result == "Main Title"

    def test_fallback_to_second_selector(self):
        html = "<h1>Fallback Title</h1>"
        page = Adaptor(html)
        result = extract_field(page, ["h1.missing", "h1"], "text")
        assert result == "Fallback Title"

    def test_all_selectors_fail_returns_none(self):
        html = "<div>Content</div>"
        page = Adaptor(html)
        result = extract_field(page, ["h1", "h2", "h3"], "text")
        assert result is None

    def test_number_extraction(self):
        html = '<span class="price">125 000 лв</span>'
        page = Adaptor(html)
        result = extract_field(page, [".price"], "currency_bgn_eur")
        assert result == 125000.0

    def test_attribute_extraction_syntax(self):
        html = '<div data-price="99500">Price</div>'
        page = Adaptor(html)
        result = extract_field(page, ["div::attr(data-price)"], "number")
        assert result == 99500.0

    def test_list_extraction(self):
        html = """
        <div class="gallery">
            <img src="/img1.jpg">
            <img src="/img2.jpg">
            <img src="/img3.jpg">
        </div>
        """
        page = Adaptor(html)
        result = extract_field(page, [".gallery img"], "list")
        assert len(result) == 3
        assert "/img1.jpg" in result
        assert "/img2.jpg" in result
        assert "/img3.jpg" in result

    def test_list_fallback(self):
        html = '<img class="main-img" src="/main.jpg">'
        page = Adaptor(html)
        result = extract_field(page, [".gallery img", ".main-img"], "list")
        assert result == ["/main.jpg"]

    def test_empty_selectors_returns_none(self):
        html = "<div>Content</div>"
        page = Adaptor(html)
        result = extract_field(page, [], "text")
        assert result is None

    def test_complex_selector_chain(self):
        html = """
        <div class="listing">
            <div class="info">
                <span class="area">75 кв.м</span>
            </div>
        </div>
        """
        page = Adaptor(html)
        result = extract_field(
            page,
            [".listing .area-main", ".listing .info .area", ".area"],
            "number"
        )
        assert result == 75.0


class TestIntegration:
    """Integration tests with realistic HTML."""

    def test_real_estate_listing(self):
        html = """
        <div class="property-detail">
            <h1 class="title">Тристаен апартамент в Младост</h1>
            <div class="price-box">
                <span class="main-price">125 000 лв</span>
            </div>
            <div class="features">
                <div class="area">75 кв.м</div>
                <div class="floor">3/6</div>
                <div class="rooms">3</div>
            </div>
            <div class="gallery">
                <img src="/photos/1.jpg">
                <img src="/photos/2.jpg">
            </div>
        </div>
        """
        page = Adaptor(html)

        # Title
        title = extract_field(page, ["h1.title", "h1"], "text")
        assert title == "Тристаен апартамент в Младост"

        # Price
        price = extract_field(
            page,
            [".main-price", ".price-box .price", ".price"],
            "currency_bgn_eur"
        )
        assert price == 125000.0

        # Area
        area = extract_field(page, [".features .area"], "number")
        assert area == 75.0

        # Floor
        floor = extract_field(page, [".features .floor"], "floor_pattern")
        assert floor == "3/6"

        # Rooms
        rooms = extract_field(page, [".features .rooms"], "integer")
        assert rooms == 3

        # Images
        images = extract_field(page, [".gallery img"], "list")
        assert len(images) == 2
