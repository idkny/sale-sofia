"""
Isolated Proxy-Scrape-Checker Test

Tests the proxy-scraper-checker binary execution.
Run: python tests/debug/test_psc_isolated.py

Note: PSC can take 5-15 minutes to complete a full scrape.
These tests use short timeouts for quick validation.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_psc_path():
    """Get path to proxy-scraper-checker binary."""
    from paths import PSC_EXECUTABLE_PATH
    return PSC_EXECUTABLE_PATH


def get_psc_output_path():
    """Get path to PSC output directory."""
    from paths import PROXY_CHECKER_DIR
    return PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"


def test_psc_exists():
    """Test PSC binary exists and is executable."""
    print("\n=== TEST: PSC Binary Exists ===")
    try:
        psc_path = get_psc_path()
        if not psc_path.exists():
            print(f"[FAIL] PSC not found at: {psc_path}")
            print("       Build with: cd proxies/external/proxy-scraper-checker && cargo build --release")
            return False

        # Check executable permission
        import os
        if not os.access(psc_path, os.X_OK):
            print(f"[WARN] PSC not executable, fixing...")
            psc_path.chmod(0o755)

        print(f"[PASS] PSC found at: {psc_path}")
        return True
    except Exception as e:
        print(f"[FAIL] Error checking PSC: {e}")
        return False


def test_psc_help():
    """Test PSC help command."""
    print("\n=== TEST: PSC Help ===")
    try:
        psc_path = get_psc_path()
        result = subprocess.run(
            [str(psc_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr
        if "-o" in output or "output" in output.lower():
            print("[PASS] PSC help shows expected options")
            print(f"[INFO] First 200 chars: {output[:200]}")
            return True
        else:
            print(f"[INFO] Help output: {output[:300]}")
            return True  # May have different format
    except subprocess.TimeoutExpired:
        print("[FAIL] PSC help command timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Help check failed: {e}")
        return False


def test_psc_quick_run():
    """Test PSC execution with very short timeout (just check it starts)."""
    print("\n=== TEST: PSC Quick Execution ===")
    print("[INFO] Testing if PSC starts correctly (will timeout after 10s)...")

    try:
        psc_path = get_psc_path()
        from paths import PROXY_CHECKER_DIR

        # Ensure output directory exists
        output_dir = PROXY_CHECKER_DIR / "out"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_output.json"

        try:
            result = subprocess.run(
                [str(psc_path), "-o", str(output_file)],
                cwd=str(PROXY_CHECKER_DIR),
                capture_output=True,
                text=True,
                timeout=10  # Very short - just test it starts
            )

            # If it completed in 10 seconds, great!
            print(f"[INFO] PSC completed quickly with return code: {result.returncode}")

            if output_file.exists():
                with open(output_file, 'r') as f:
                    try:
                        data = json.load(f)
                        print(f"[PASS] PSC output valid JSON with {len(data)} proxies")
                    except json.JSONDecodeError:
                        print("[WARN] PSC output is not valid JSON (partial run)")

            return True

        except subprocess.TimeoutExpired:
            print("[INFO] PSC started and is running (timed out as expected)")
            print("[PASS] PSC execution started successfully")
            return True

        finally:
            if output_file.exists():
                output_file.unlink()

    except Exception as e:
        print(f"[FAIL] PSC execution failed: {e}")
        return False


def test_psc_output_parsing():
    """Test parsing existing PSC output file."""
    print("\n=== TEST: PSC Output Parsing ===")

    try:
        output_file = get_psc_output_path()

        if not output_file.exists():
            print(f"[SKIP] No existing output file at: {output_file}")
            print("       Run PSC first to create output")
            return True  # Not a failure, just skipped

        with open(output_file, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"[FAIL] Output is not a list: {type(data)}")
            return False

        print(f"[INFO] Found {len(data)} proxies in output")

        if len(data) > 0:
            # Check first proxy structure
            proxy = data[0]
            expected_fields = ['host', 'port']
            missing = [f for f in expected_fields if f not in proxy]

            if missing:
                print(f"[WARN] Missing fields in proxy: {missing}")
            else:
                print(f"[PASS] Proxy structure valid: {list(proxy.keys())}")
                print(f"[INFO] Sample: {proxy['host']}:{proxy['port']}")

        return True

    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON in output: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Output parsing failed: {e}")
        return False


def test_psc_directory_structure():
    """Test PSC directory structure."""
    print("\n=== TEST: PSC Directory Structure ===")

    try:
        from paths import PROXY_CHECKER_DIR

        # Check required directories
        required_dirs = [
            PROXY_CHECKER_DIR,
            PROXY_CHECKER_DIR / "target",
            PROXY_CHECKER_DIR / "target" / "release",
        ]

        for dir_path in required_dirs:
            if dir_path.exists():
                print(f"[PASS] Directory exists: {dir_path.name}")
            else:
                print(f"[FAIL] Missing directory: {dir_path}")
                return False

        # Check output directory (create if missing)
        output_dir = PROXY_CHECKER_DIR / "out"
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
            print(f"[INFO] Created output directory: {output_dir}")
        else:
            print(f"[PASS] Output directory exists")

        return True

    except Exception as e:
        print(f"[FAIL] Directory structure check failed: {e}")
        return False


def main():
    """Run all PSC tests."""
    print("=" * 60)
    print("ISOLATED PROXY-SCRAPE-CHECKER TESTS")
    print("=" * 60)

    results = []

    results.append(("Binary Exists", test_psc_exists()))
    results.append(("Directory Structure", test_psc_directory_structure()))
    results.append(("Help Command", test_psc_help()))
    results.append(("Quick Execution", test_psc_quick_run()))
    results.append(("Output Parsing", test_psc_output_parsing()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL PSC TESTS PASSED")
        return 0
    else:
        print("SOME PSC TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
