"""LLM extraction performance test.

Tests extraction performance with multiple descriptions.
Measures: speed, success rate, cache effectiveness.

Usage:
    python tests/llm/test_performance.py [count]

    count: Number of extractions (default: 100)
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm import extract_description, get_metrics, reset_metrics, ensure_ollama_ready

# Sample descriptions for testing (varied complexity)
SAMPLE_DESCRIPTIONS = [
    # Full featured
    """Напълно обзаведен тристаен апартамент в комплекс с охрана.
    Южно изложение с гледка към Витоша. Площ 85 кв.м., 2 спални, 1 баня.
    Паркомясто в подземен гараж. Асансьор. Централно отопление ТЕЦ.""",

    # Minimal
    "Двустаен апартамент, необзаведен, източно изложение.",

    # Medium
    """Четиристаен апартамент с тераса и мазе.
    Частично обзаведен. Газово отопление. Гараж в двора.""",

    # Needs renovation
    """Петстаен апартамент за ремонт. 3 спални, 2 бани.
    Без обзавеждане. Северно изложение. Климатик.""",

    # Modern
    """Ново строителство 2024. Луксозен апартамент.
    Открит паркинг. Ток. Западно изложение с гледка град.""",

    # Simple
    "Едностаен апартамент, обзаведен, асансьор.",

    # With parking
    """Тристаен апартамент в центъра. 2 тераси.
    Подземен гараж. Изложение юг-изток. ТЕЦ.""",

    # Renovated
    """Ремонтиран двустаен апартамент. Газово парно.
    Мазе. Панел, обзаведен. Източно изложение.""",

    # High floor
    """Четиристаен на последен етаж с гледка към парк.
    Необзаведен, за ремонт. Без асансьор. Тухла.""",

    # New building
    """Акт 16. Тристаен в нова кооперация.
    Климатик, частично обзаведен. 2 бани. Гараж.""",
]


def run_performance_test(target_count: int = 100):
    """Run performance test with specified number of extractions."""

    print(f"\n{'='*60}")
    print(f"LLM Extraction Performance Test")
    print(f"{'='*60}")
    print(f"Target extractions: {target_count}")
    print(f"Sample descriptions: {len(SAMPLE_DESCRIPTIONS)}")

    # Ensure Ollama is ready
    print("\nStarting Ollama...")
    if not ensure_ollama_ready():
        print("ERROR: Ollama not available")
        return False

    # Reset metrics
    reset_metrics()

    # Run extractions
    print(f"\nRunning {target_count} extractions...")
    start_time = time.time()

    success_count = 0
    for i in range(target_count):
        # Cycle through samples
        description = SAMPLE_DESCRIPTIONS[i % len(SAMPLE_DESCRIPTIONS)]

        result = extract_description(description)

        if result.confidence > 0:
            success_count += 1

        # Progress every 10
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  [{i + 1}/{target_count}] {rate:.1f} extractions/sec")

    total_time = time.time() - start_time

    # Get final metrics
    metrics = get_metrics()

    # Report results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"\nTiming:")
    print(f"  Total time:      {total_time:.1f}s")
    print(f"  Avg per extract: {metrics['avg_time_ms']:.0f}ms")
    print(f"  Rate:            {target_count / total_time:.1f} extractions/sec")

    print(f"\nSuccess:")
    print(f"  Total:    {metrics['extractions_total']}")
    print(f"  Success:  {metrics['extractions_success']} ({metrics['extractions_success']/max(1,metrics['extractions_total'])*100:.1f}%)")
    print(f"  Failed:   {metrics['extractions_failed']}")

    print(f"\nCache:")
    print(f"  Hits:     {metrics['cache_hits']}")
    print(f"  Misses:   {metrics['cache_misses']}")
    print(f"  Hit rate: {metrics['cache_hit_rate']*100:.1f}%")

    print(f"\nConfidence:")
    print(f"  Average:  {metrics['avg_confidence']:.2f}")

    print(f"\n{'='*60}")

    # Pass/fail criteria
    success_rate = metrics['extractions_success'] / max(1, metrics['extractions_total'])
    passed = success_rate >= 0.9 and metrics['avg_confidence'] >= 0.7

    if passed:
        print("TEST PASSED")
    else:
        print("TEST FAILED")
        if success_rate < 0.9:
            print(f"  - Success rate {success_rate*100:.1f}% < 90%")
        if metrics['avg_confidence'] < 0.7:
            print(f"  - Avg confidence {metrics['avg_confidence']:.2f} < 0.7")

    return passed


if __name__ == "__main__":
    # Parse count from args
    count = 100
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Invalid count: {sys.argv[1]}, using default 100")

    success = run_performance_test(count)
    sys.exit(0 if success else 1)
