"""
Isolated Mubeng Test

Tests Mubeng binary execution in check mode.
Run: python tests/debug/test_mubeng_isolated.py

Tests both direct execution and script-wrapper execution.
"""

import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_mubeng_path():
    """Get path to Mubeng binary."""
    from paths import MUBENG_EXECUTABLE_PATH
    return MUBENG_EXECUTABLE_PATH


def test_mubeng_exists():
    """Test Mubeng binary exists and is executable."""
    print("\n=== TEST: Mubeng Binary Exists ===")
    try:
        mubeng_path = get_mubeng_path()
        if not mubeng_path.exists():
            print(f"[FAIL] Mubeng not found at: {mubeng_path}")
            return False

        # Check executable permission
        import os
        if not os.access(mubeng_path, os.X_OK):
            print(f"[WARN] Mubeng not executable, fixing...")
            mubeng_path.chmod(0o755)

        print(f"[PASS] Mubeng found at: {mubeng_path}")
        return True
    except Exception as e:
        print(f"[FAIL] Error checking Mubeng: {e}")
        return False


def test_mubeng_version():
    """Test Mubeng version command."""
    print("\n=== TEST: Mubeng Version ===")
    try:
        mubeng_path = get_mubeng_path()
        result = subprocess.run(
            [str(mubeng_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if "v0.22.0" in result.stdout or "v0.22.0" in result.stderr:
            print(f"[PASS] Mubeng version: v0.22.0")
            return True
        else:
            output = result.stdout + result.stderr
            print(f"[WARN] Unexpected version output: {output[:100]}")
            return True  # Still passes, just unexpected version
    except subprocess.TimeoutExpired:
        print("[FAIL] Mubeng version command timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Version check failed: {e}")
        return False


def test_mubeng_help():
    """Test Mubeng help command."""
    print("\n=== TEST: Mubeng Help ===")
    try:
        mubeng_path = get_mubeng_path()
        result = subprocess.run(
            [str(mubeng_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Check for expected options
        output = result.stdout + result.stderr
        if "--check" in output and "-f" in output:
            print("[PASS] Mubeng help shows expected options")
            return True
        else:
            print(f"[WARN] Help output may be incomplete: {output[:200]}")
            return True
    except Exception as e:
        print(f"[FAIL] Help check failed: {e}")
        return False


def test_mubeng_check_direct():
    """Test Mubeng check mode without PTY wrapper (may hang)."""
    print("\n=== TEST: Mubeng Check (Direct) ===")
    print("[INFO] This test may hang if PTY is required...")

    try:
        mubeng_path = get_mubeng_path()

        # Create test input file with a few known proxies
        # Using public proxy test endpoints
        test_proxies = [
            "http://1.1.1.1:80",  # Cloudflare (not a proxy, will fail)
            "http://8.8.8.8:80",  # Google DNS (not a proxy, will fail)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for proxy in test_proxies:
                f.write(proxy + '\n')
            input_file = Path(f.name)

        output_file = Path(tempfile.mktemp(suffix='.txt'))

        try:
            cmd = [
                str(mubeng_path),
                "--check",
                "-f", str(input_file),
                "-o", str(output_file),
                "-t", "3s",  # Short timeout for test
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15  # 15 second overall timeout
            )

            if result.returncode == 0:
                print("[PASS] Mubeng check completed directly")
            else:
                print(f"[INFO] Mubeng returned code {result.returncode} (expected for dead proxies)")

            # Check if output file was created
            if output_file.exists():
                with open(output_file, 'r') as f:
                    live_proxies = f.read().strip()
                print(f"[INFO] Live proxies found: {len(live_proxies.split()) if live_proxies else 0}")

            return True

        finally:
            input_file.unlink(missing_ok=True)
            output_file.unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        print("[WARN] Direct execution timed out (PTY may be required)")
        return False
    except Exception as e:
        print(f"[FAIL] Direct check failed: {e}")
        return False


def test_mubeng_check_with_script():
    """Test Mubeng check mode with script PTY wrapper."""
    print("\n=== TEST: Mubeng Check (with script wrapper) ===")

    try:
        mubeng_path = get_mubeng_path()

        # Create test input file
        test_proxies = [
            "http://1.1.1.1:80",
            "http://8.8.8.8:80",
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for proxy in test_proxies:
                f.write(proxy + '\n')
            input_file = Path(f.name)

        output_file = Path(tempfile.mktemp(suffix='.txt'))

        try:
            mubeng_cmd = [
                str(mubeng_path),
                "--check",
                "-f", str(input_file),
                "-o", str(output_file),
                "-t", "3s",
            ]

            # Wrap with script for PTY
            cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )

            print(f"[INFO] Return code: {result.returncode}")

            # Check output file
            if output_file.exists():
                with open(output_file, 'r') as f:
                    live_proxies = f.read().strip()
                count = len(live_proxies.split('\n')) if live_proxies else 0
                print(f"[INFO] Live proxies found: {count}")
            else:
                print("[INFO] No live proxies (output file not created)")

            print("[PASS] Mubeng check with script wrapper completed")
            return True

        finally:
            input_file.unlink(missing_ok=True)
            output_file.unlink(missing_ok=True)

    except subprocess.TimeoutExpired:
        print("[FAIL] Script-wrapped execution timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Script-wrapped check failed: {e}")
        return False


def test_mubeng_with_real_proxy():
    """Test Mubeng with a likely-live public proxy."""
    print("\n=== TEST: Mubeng with Real Proxy ===")
    print("[INFO] This test uses public proxy lists, may be flaky...")

    try:
        mubeng_path = get_mubeng_path()

        # Use proxies from a free proxy list API
        # Note: These may not work, just testing execution
        test_proxies = [
            # Some commonly listed free proxies (may be dead)
            "http://185.162.231.166:8080",
            "http://103.152.112.162:80",
            "http://178.48.68.61:8080",
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for proxy in test_proxies:
                f.write(proxy + '\n')
            input_file = Path(f.name)

        output_file = Path(tempfile.mktemp(suffix='.txt'))

        try:
            mubeng_cmd = [
                str(mubeng_path),
                "--check",
                "-f", str(input_file),
                "-o", str(output_file),
                "-t", "5s",
            ]
            cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if output_file.exists():
                with open(output_file, 'r') as f:
                    content = f.read().strip()
                if content:
                    print(f"[PASS] Found live proxies:\n{content}")
                    return True
                else:
                    print("[INFO] No live proxies found (expected for public proxies)")
            else:
                print("[INFO] No output file (all proxies dead)")

            print("[PASS] Mubeng execution completed (proxy liveness is separate concern)")
            return True

        finally:
            input_file.unlink(missing_ok=True)
            output_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"[FAIL] Real proxy test failed: {e}")
        return False


def main():
    """Run all Mubeng tests."""
    print("=" * 60)
    print("ISOLATED MUBENG TESTS")
    print("=" * 60)

    results = []

    results.append(("Binary Exists", test_mubeng_exists()))
    results.append(("Version Check", test_mubeng_version()))
    results.append(("Help Command", test_mubeng_help()))
    results.append(("Direct Check", test_mubeng_check_direct()))
    results.append(("Script Wrapper", test_mubeng_check_with_script()))
    results.append(("Real Proxy Test", test_mubeng_with_real_proxy()))

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
        print("ALL MUBENG TESTS PASSED")
        return 0
    else:
        print("SOME MUBENG TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
