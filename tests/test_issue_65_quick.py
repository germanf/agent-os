#!/usr/bin/env python3
"""
Quick Test Plan for GitHub Issue #65: Rate Limiting
Tests without long waits for faster execution.
"""

import json
import sys
from pathlib import Path

# Add dashboard to path
sys.path.insert(0, str(Path(__file__).parent / "dashboard"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
results = []

def log_test(name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"    {details}")
    results.append((name, passed, details))

# TEST 1: Normal requests within limit
print("\n" + "=" * 80)
print("ISSUE #65 QUICK TEST PLAN - Rate Limiting")
print("=" * 80)

print("\nTEST 1: Normal requests (within limit)")
print("-" * 60)
successes = 0
for i in range(5):
    response = client.get("/api/health")
    if response.status_code == 200:
        successes += 1

passed = successes == 5
log_test("Test 1: Normal requests within limit", passed,
         "All 5 requests succeeded" if passed else f"Only {successes}/5 succeeded")

# TEST 2: Rate limit exceeded (100 rapid requests)
print("\nTEST 2: Rate limit exceeded (100 rapid requests)")
print("-" * 60)
responses = {200: 0, 429: 0, 'other': 0}
for i in range(100):
    response = client.get("/api/health")
    if response.status_code == 200:
        responses[200] += 1
    elif response.status_code == 429:
        responses[429] += 1
    else:
        responses['other'] += 1

passed = responses[200] >= 60 and responses[429] > 0
log_test("Test 2: Rate limit exceeded", passed,
         f"Succeeded: {responses[200]}, Rate limited: {responses[429]}")

# TEST 3: Response headers when rate limited
print("\nTEST 3: Response headers verification")
print("-" * 60)
headers_found = {"Retry-After": False, "X-RateLimit-Limit": False, "X-RateLimit-Remaining": False}
rate_limited_response = None

for i in range(65):
    response = client.get("/api/health")
    if response.status_code == 429:
        rate_limited_response = response
        break

if rate_limited_response:
    for header in headers_found.keys():
        if header in rate_limited_response.headers:
            headers_found[header] = True

    has_429 = rate_limited_response.status_code == 429
    try:
        body = rate_limited_response.json()
        has_detail = "detail" in body
    except:
        has_detail = False

    all_headers = all(headers_found.values())
    passed = has_429 and all_headers and has_detail
    log_test("Test 3: Response headers verification", passed,
             f"429 status: {has_429}, All headers: {all_headers}, Has detail: {has_detail}")
else:
    log_test("Test 3: Response headers verification", False, "Could not trigger rate limit")

# TEST 4: Different endpoints
print("\nTEST 4: Different endpoint rate limits")
print("-" * 60)
endpoint_results = {}
test_endpoints = [
    ("/api/health", 60),
    ("/api/diagnostics", 30),
]

for endpoint, expected_limit in test_endpoints:
    success_count = 0
    rate_limited_at = None

    for i in range(expected_limit + 5):
        response = client.get(endpoint)
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429 and rate_limited_at is None:
            rate_limited_at = i + 1

    endpoint_results[endpoint] = {
        "success_count": success_count,
        "rate_limited_at": rate_limited_at,
        "expected_limit": expected_limit,
    }

passed = all(v["rate_limited_at"] is not None for v in endpoint_results.values())
log_test("Test 4: Different endpoint rate limits", passed,
         json.dumps(endpoint_results, indent=2))

# Summary
print("\n" + "=" * 80)
print("FINAL TEST SUMMARY")
print("=" * 80)

passed_count = sum(1 for _, result, _ in results if result)
total_count = len(results)

print(f"\nTests Passed: {passed_count}/{total_count}\n")

for name, result, details in results:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status} - {name}")

print("\n" + "=" * 80)

if passed_count == total_count:
    print("RESULT: ✓ ALL TESTS PASSED")
    print("        Rate limiting is properly implemented.")
    print("        Issue #65 can be CLOSED.")
    print("=" * 80 + "\n")
    sys.exit(0)
else:
    print(f"RESULT: ✗ SOME TESTS FAILED ({total_count - passed_count}/{total_count})")
    print("=" * 80 + "\n")
    sys.exit(1)
