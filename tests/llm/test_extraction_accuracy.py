"""Per-field accuracy test for extract_description().

Measures which fields fail to extract, not just enum validity.

Usage:
    python tests/llm/test_extraction_accuracy.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm import extract_description

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
    {
        "name": "Renovation needed",
        "text": """Петстаен апартамент за ремонт.
3 спални, 2 бани. Без обзавеждане.
Северно изложение. Климатик.""",
        "expected": {
            "rooms": 5,
            "bedrooms": 3,
            "bathrooms": 2,
            "furnishing": "unfurnished",
            "condition": "needs_renovation",
            "orientation": "north",
            "heating_type": "air_conditioner",
        },
    },
    {
        "name": "Renovated modern",
        "text": """Ремонтиран двустаен апартамент.
Обзаведен с нови мебели.
Западно изложение с гледка към парк.
Паркомясто в гараж. Охрана 24/7.""",
        "expected": {
            "rooms": 2,
            "furnishing": "furnished",
            "condition": "renovated",
            "orientation": "west",
            "has_view": True,
            "view_type": "park",
            "has_parking": True,
            "parking_type": "garage",
            "has_security": True,
        },
    },
]


def run_accuracy_test():
    """Run extraction on all samples and measure per-field accuracy."""
    # Track per-field results
    field_stats = {}
    sample_results = []

    print("\n" + "=" * 60)
    print("EXTRACTION ACCURACY TEST")
    print("=" * 60)

    for sample in TEST_SAMPLES:
        print(f"\n--- {sample['name']} ---")
        print(f"Text: {sample['text'][:60]}...")

        result = extract_description(sample["text"])

        print(f"Confidence: {result.confidence:.2f}")

        sample_correct = 0
        sample_total = 0

        for field, expected in sample["expected"].items():
            actual = getattr(result, field)
            is_correct = actual == expected

            if is_correct:
                sample_correct += 1
                status = "✓"
            else:
                status = "✗"

            print(f"  {status} {field}: expected={expected}, got={actual}")

            # Track per-field stats
            if field not in field_stats:
                field_stats[field] = {"correct": 0, "total": 0}
            field_stats[field]["total"] += 1
            if is_correct:
                field_stats[field]["correct"] += 1

            sample_total += 1

        sample_accuracy = sample_correct / sample_total * 100 if sample_total else 0
        print(f"  Sample accuracy: {sample_correct}/{sample_total} ({sample_accuracy:.0f}%)")
        sample_results.append((sample["name"], sample_accuracy))

    # Print summary
    print("\n" + "=" * 60)
    print("PER-FIELD ACCURACY SUMMARY")
    print("=" * 60)
    print(f"{'Field':<20} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
    print("-" * 50)

    total_correct = 0
    total_fields = 0

    for field, stats in sorted(field_stats.items()):
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] else 0
        print(f"{field:<20} {stats['correct']:<10} {stats['total']:<10} {acc:.0f}%")
        total_correct += stats["correct"]
        total_fields += stats["total"]

    overall_accuracy = total_correct / total_fields * 100 if total_fields else 0
    print("-" * 50)
    print(f"{'OVERALL':<20} {total_correct:<10} {total_fields:<10} {overall_accuracy:.0f}%")

    print("\n" + "=" * 60)
    print("SAMPLE SUMMARY")
    print("=" * 60)
    for name, acc in sample_results:
        print(f"  {name}: {acc:.0f}%")

    return overall_accuracy, field_stats


if __name__ == "__main__":
    overall, stats = run_accuracy_test()
    print(f"\n\nFINAL ACCURACY: {overall:.1f}%")
    if overall < 95:
        print("⚠️  Below 95% target - improvements needed")
    else:
        print("✓ Meets 95% target")
