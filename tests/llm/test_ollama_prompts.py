"""Integration tests for LLM extraction functions.

Tests the actual map_fields() and extract_description() functions
to ensure they return English enum values from Bulgarian input.

Usage:
    pytest tests/llm/test_ollama_prompts.py -v -s
"""

import pytest

# Skip all tests if Ollama is not available
try:
    import requests
    response = requests.get("http://localhost:11434/", timeout=2)
    OLLAMA_AVAILABLE = response.status_code == 200
except Exception:
    OLLAMA_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not OLLAMA_AVAILABLE,
    reason="Ollama server not running"
)

# Valid English enum values
VALID_CONSTRUCTION = ["brick", "panel", "epk", None]
VALID_HEATING = ["district", "gas", "electric", "air_conditioner", None]
VALID_FURNISHING = ["furnished", "partially", "unfurnished", None]
VALID_ORIENTATION = ["north", "south", "east", "west", None]
VALID_PARKING = ["underground", "outdoor", "garage", None]

# Bulgarian values that should NEVER appear
FORBIDDEN_BULGARIAN = [
    "тухла", "тухлена", "панел", "епк",
    "обзаведен", "необзаведен", "частично",
    "юг", "север", "изток", "запад",
    "гараж", "подземен", "двор",
    "тец", "газ", "ток", "климатик",
    "централно",
]


class TestMapFieldsEnumValues:
    """Test map_fields() returns valid English enum values."""

    def test_construction_is_valid_enum(self):
        """Construction must be valid English enum or None."""
        from llm import map_fields

        result = map_fields("Тристаен апартамент, тухлена конструкция, 85 кв.м., етаж 3")

        assert result.construction in VALID_CONSTRUCTION, \
            f"Invalid construction: '{result.construction}'"

    def test_heating_is_valid_enum(self):
        """Heating must be valid English enum or None."""
        from llm import map_fields

        result = map_fields("Апартамент с отопление ТЕЦ (централно), 100 кв.м.")

        assert result.heating in VALID_HEATING, \
            f"Invalid heating: '{result.heating}'"

    def test_full_extraction_returns_valid_enums(self):
        """Full extraction returns valid English enums."""
        from llm import map_fields

        text = """
        Тристаен апартамент в квартал Лозенец.
        Тухлена конструкция от 2018 г.
        Площ 85 кв.м., етаж 4 от 6.
        Отопление: ТЕЦ
        Цена: 185000 евро
        """

        result = map_fields(text)

        # All enum fields must be valid English values
        assert result.construction in VALID_CONSTRUCTION
        assert result.heating in VALID_HEATING
        assert result.confidence >= 0.0


class TestExtractDescriptionEnumValues:
    """Test extract_description() returns valid English enum values."""

    def test_furnishing_is_valid_enum(self):
        """Furnishing must be valid English enum or None."""
        from llm import extract_description

        result = extract_description(
            "Напълно обзаведен апартамент с климатик, тераса, асансьор"
        )

        assert result.furnishing in VALID_FURNISHING, \
            f"Invalid furnishing: '{result.furnishing}'"

    def test_orientation_is_valid_enum(self):
        """Orientation must be valid English enum or None."""
        from llm import extract_description

        result = extract_description(
            "Тристаен апартамент с южно изложение, гледка към Витоша планина"
        )

        assert result.orientation in VALID_ORIENTATION, \
            f"Invalid orientation: '{result.orientation}'"

    def test_parking_is_valid_enum(self):
        """Parking type must be valid English enum or None."""
        from llm import extract_description

        result = extract_description(
            "Двустаен апартамент с паркомясто в подземен гараж, охрана"
        )

        assert result.parking_type in VALID_PARKING, \
            f"Invalid parking_type: '{result.parking_type}'"


class TestNoBulgarianLeakage:
    """Ensure no Bulgarian enum values leak through."""

    def test_no_bulgarian_in_map_fields(self):
        """map_fields() must not return Bulgarian values."""
        from llm import map_fields

        result = map_fields(
            "Тухлена конструкция, централно отопление ТЕЦ, 90 кв.м."
        )

        # Check construction
        if result.construction:
            assert result.construction.lower() not in FORBIDDEN_BULGARIAN, \
                f"Bulgarian leaked in construction: {result.construction}"

        # Check heating
        if result.heating:
            assert result.heating.lower() not in FORBIDDEN_BULGARIAN, \
                f"Bulgarian leaked in heating: {result.heating}"

    def test_no_bulgarian_in_extract_description(self):
        """extract_description() must not return Bulgarian values."""
        from llm import extract_description

        result = extract_description(
            "Обзаведен апартамент, южно изложение, гараж, асансьор"
        )

        # Check all string enum fields
        for field in ["furnishing", "orientation", "parking_type", "view_type", "heating_type"]:
            value = getattr(result, field)
            if value:
                assert value.lower() not in FORBIDDEN_BULGARIAN, \
                    f"Bulgarian leaked in {field}: {value}"
