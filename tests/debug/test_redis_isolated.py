"""
Isolated Redis Test

Tests Redis connectivity and basic operations without Celery.
Run: python tests/debug/test_redis_isolated.py
"""

import sys
import time

def test_redis_ping():
    """Test basic Redis connectivity."""
    print("\n=== TEST: Redis PING ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        response = r.ping()
        if response:
            print("[PASS] Redis PING returned True")
            return True
        else:
            print("[FAIL] Redis PING returned False")
            return False
    except redis.ConnectionError as e:
        print(f"[FAIL] Redis connection error: {e}")
        print("       Is Redis running? Try: redis-server --daemonize yes")
        return False
    except ImportError:
        print("[FAIL] redis package not installed: pip install redis")
        return False


def test_redis_set_get():
    """Test Redis SET/GET operations."""
    print("\n=== TEST: Redis SET/GET ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)

        test_key = "debug_test_key"
        test_value = f"test_value_{time.time()}"

        # SET
        r.set(test_key, test_value)
        print(f"[INFO] SET {test_key} = {test_value}")

        # GET
        result = r.get(test_key).decode('utf-8')
        if result == test_value:
            print(f"[PASS] GET returned correct value: {result}")
            r.delete(test_key)  # Cleanup
            return True
        else:
            print(f"[FAIL] GET returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"[FAIL] Redis SET/GET failed: {e}")
        return False


def test_redis_list_operations():
    """Test Redis list operations (used by Celery queues)."""
    print("\n=== TEST: Redis List Operations ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)

        test_queue = "debug_test_queue"

        # Clear first
        r.delete(test_queue)

        # LPUSH
        r.lpush(test_queue, "task1", "task2", "task3")
        print("[INFO] LPUSH 3 items to queue")

        # LLEN
        length = r.llen(test_queue)
        if length == 3:
            print(f"[PASS] Queue length is 3")
        else:
            print(f"[FAIL] Queue length is {length}, expected 3")
            return False

        # RPOP
        item = r.rpop(test_queue).decode('utf-8')
        if item == "task1":
            print(f"[PASS] RPOP returned first item: {item}")
        else:
            print(f"[FAIL] RPOP returned wrong item: {item}")
            return False

        # Cleanup
        r.delete(test_queue)
        print("[PASS] All list operations work correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Redis list operations failed: {e}")
        return False


def test_redis_celery_queues():
    """Check Celery queue status in Redis."""
    print("\n=== TEST: Celery Queue Status ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)

        # Check common Celery queues
        queues = ['celery', 'sale_sofia']
        for queue in queues:
            length = r.llen(queue)
            print(f"[INFO] Queue '{queue}' has {length} pending tasks")

        print("[PASS] Queue status check complete")
        return True
    except Exception as e:
        print(f"[FAIL] Queue status check failed: {e}")
        return False


def main():
    """Run all Redis tests."""
    print("=" * 60)
    print("ISOLATED REDIS TESTS")
    print("=" * 60)

    results = []
    results.append(("Redis PING", test_redis_ping()))
    results.append(("Redis SET/GET", test_redis_set_get()))
    results.append(("Redis List Ops", test_redis_list_operations()))
    results.append(("Celery Queues", test_redis_celery_queues()))

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
        print("ALL REDIS TESTS PASSED")
        return 0
    else:
        print("SOME REDIS TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
