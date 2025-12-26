"""Compare extraction accuracy between qwen2.5:1.5b and qwen2.5:3b.

Usage:
    python tests/llm/test_model_comparison.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from llm.llm_main import _get_client
from llm.prompts import EXTRACTION_PROMPT
from llm.schemas import ExtractedDescription

# Test samples with expected values
TEST_SAMPLES = [
    {
        "name": "Feature-rich",
        "text": """Напълно обзаведен тристаен апартамент в комплекс с охрана.
Южно изложение с гледка към Витоша.
Площ 85 кв.м., 2 спални, 1 баня.
Паркомясто в подземен гараж. Асансьор.
Централно отопление ТЕЦ.""",
        "expected": {
            "rooms": 3,
            "bedrooms": 2,
            "bathrooms": 1,
            "furnishing": "furnished",
            "orientation": "south",
            "has_view": True,
            "view_type": "mountain",
            "has_parking": True,
            "parking_type": "underground",
            "has_elevator": True,
            "has_security": True,
            "heating_type": "district",
        },
    },
    {
        "name": "Minimal",
        "text": "Двустаен апартамент, необзаведен, източно изложение.",
        "expected": {
            "rooms": 2,
            "furnishing": "unfurnished",
            "orientation": "east",
        },
    },
    {
        "name": "Price-focused",
        "text": """Четиристаен апартамент с тераса и мазе.
Частично обзаведен. Газово отопление.
Гараж в двора. Ново строителство 2023.""",
        "expected": {
            "rooms": 4,
            "has_balcony": True,
            "has_storage": True,
            "furnishing": "partially",
            "heating_type": "gas",
            "has_parking": True,
            "parking_type": "outdoor",
            "condition": "new",
        },
    },
]


def test_model(model: str):
    """Test a specific model and return accuracy."""
    client = _get_client()

    total_correct = 0
    total_fields = 0

    print(f"\n{'=' * 60}")
    print(f"TESTING MODEL: {model}")
    print('=' * 60)

    for sample in TEST_SAMPLES:
        prompt = EXTRACTION_PROMPT.format(description=sample["text"])

        # Override model in config temporarily
        original_model = client.config["tasks"]["description_extraction"]["primary_model"]
        client.config["tasks"]["description_extraction"]["primary_model"] = model

        response = client._call_ollama(prompt, "description_extraction", schema_class=ExtractedDescription)
        result = client._parse_response(response, ExtractedDescription)

        # Restore original
        client.config["tasks"]["description_extraction"]["primary_model"] = original_model

        print(f"\n--- {sample['name']} (conf: {result.confidence:.2f}) ---")

        sample_correct = 0
        for field, expected in sample["expected"].items():
            actual = getattr(result, field)
            is_correct = actual == expected

            if is_correct:
                sample_correct += 1
                total_correct += 1
                status = "✓"
            else:
                status = "✗"

            total_fields += 1
            print(f"  {status} {field}: expected={expected}, got={actual}")

        accuracy = sample_correct / len(sample["expected"]) * 100
        print(f"  Sample: {accuracy:.0f}%")

    overall = total_correct / total_fields * 100 if total_fields else 0
    print(f"\n{'=' * 60}")
    print(f"MODEL {model} OVERALL: {total_correct}/{total_fields} ({overall:.0f}%)")
    print('=' * 60)

    return overall


if __name__ == "__main__":
    models = ["qwen2.5:1.5b", "qwen2.5:3b"]
    results = {}

    for model in models:
        results[model] = test_model(model)

    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    for model, acc in results.items():
        print(f"  {model}: {acc:.0f}%")

    winner = max(results, key=results.get)
    print(f"\n  WINNER: {winner} ({results[winner]:.0f}%)")
