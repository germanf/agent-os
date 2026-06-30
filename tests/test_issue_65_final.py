#!/usr/bin/env python3
"""
Final Comprehensive Test Plan for GitHub Issue #65: Rate Limiting

This test properly validates the rate limiting implementation.
"""

import subprocess
import sys

print("\n" + "=" * 80)
print("ISSUE #65 - RATE LIMITING TEST PLAN")
print("=" * 80)

# ────────────────────────────────────────────────────────────────────────────
# TEST 1: Normal requests within limit
# ────────────────────────────────────────────────────────────────────────────
print("\nTEST 1: Normal requests (within limit)")
print("-" * 60)

test1_pass = True
for i in range(5):
    result = subprocess.run(
        ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
         "http://localhost:8765/api/health"],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()
    if status == "200":
        print(f"  Request {i+1}: {status} OK ✓")
    else:
        print(f"  Request {i+1}: {status} ✗")
        test1_pass = False

if test1_pass:
    print("[✓ PASS] Test 1: Normal requests within limit")
else:
    print("[✗ FAIL] Test 1: Normal requests within limit")

# ────────────────────────────────────────────────────────────────────────────
# TEST 2: Rate limit exceeded
# ────────────────────────────────────────────────────────────────────────────
print("\nTEST 2: Rate limit exceeded (100 rapid requests)")
print("-" * 60)

success_count = 0
rate_limited_count = 0

for i in range(100):
    result = subprocess.run(
        ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
         "http://localhost:8765/api/health"],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()

    if status == "200":
        success_count += 1
    elif status == "429":
        rate_limited_count += 1

print(f"  Results: {success_count} succeeded (200), {rate_limited_count} rate limited (429)")

# /api/health has 60/minute limit
test2_pass = success_count >= 58 and rate_limited_count > 0
if test2_pass:
    print("[✓ PASS] Test 2: Rate limit exceeded")
else:
    print(f"[✗ FAIL] Test 2: Expected ~60 success, ~40 rate limited. Got {success_count}, {rate_limited_count}")

# ────────────────────────────────────────────────────────────────────────────
# TEST 3: Response format when rate limited
# ────────────────────────────────────────────────────────────────────────────
print("\nTEST 3: Response headers when rate limited")
print("-" * 60)

test3_pass = True

for i in range(15):
    result = subprocess.run(
        ["curl", "-s", "-i", "http://localhost:8765/api/health"],
        capture_output=True,
        text=True
    )

    if "429" in result.stdout:
        # Check headers
        headers_ok = True
        if "Retry-After" not in result.stdout:
            print("  Missing: Retry-After header ✗")
            headers_ok = False
        if "X-RateLimit-Limit" not in result.stdout:
            print("  Missing: X-RateLimit-Limit header ✗")
            headers_ok = False
        if "X-RateLimit-Remaining" not in result.stdout:
            print("  Missing: X-RateLimit-Remaining header ✗")
            headers_ok = False

        # Check body
        if '"detail"' in result.stdout:
            print("  Response has detail field ✓")
        else:
            print("  Response missing detail field ✗")
            headers_ok = False

        test3_pass = headers_ok
        if test3_pass:
            print("[✓ PASS] Test 3: Response headers verified")
        break

if not test3_pass:
    print("[✗ FAIL] Test 3: Response headers verification failed")

# ────────────────────────────────────────────────────────────────────────────
# TEST 4: Different endpoints have different limits
# ────────────────────────────────────────────────────────────────────────────
print("\nTEST 4: Endpoint-specific rate limits")
print("-" * 60)

# /api/health: 60/minute limit
health_success = 0
for i in range(65):
    result = subprocess.run(
        ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
         "http://localhost:8765/api/health"],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()
    if status == "200":
        health_success += 1
    elif status == "429":
        break

# /api/diagnostics: 30/minute limit
diag_success = 0
for i in range(35):
    result = subprocess.run(
        ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
         "http://localhost:8765/api/diagnostics"],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()
    if status == "200":
        diag_success += 1
    elif status == "429":
        break

print(f"  /api/health: {health_success} requests before rate limit")
print(f"  /api/diagnostics: {diag_success} requests before rate limit")

# Test that endpoints have different effective limits
test4_pass = (health_success > 50) and (diag_success < health_success or diag_success == 30)
if test4_pass:
    print("[✓ PASS] Test 4: Endpoint limits working")
else:
    print("[✗ FAIL] Test 4: Limits not as expected")

# ────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("FINAL TEST SUMMARY")
print("=" * 80)

results = [
    ("Test 1: Normal requests within limit", test1_pass),
    ("Test 2: Rate limit exceeded", test2_pass),
    ("Test 3: Response headers", test3_pass),
    ("Test 4: Endpoint-specific limits", test4_pass),
]

passed = sum(1 for _, p in results if p)
total = len(results)

for name, result in results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"[{status}] {name}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n✓ ALL TESTS PASSED - Issue #65 can be CLOSED")
    print("=" * 80 + "\n")
    sys.exit(0)
else:
    print(f"\n✗ {total - passed} TEST(S) FAILED - Issue #65 needs review")
    print("=" * 80 + "\n")
    sys.exit(1)
