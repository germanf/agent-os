#!/usr/bin/env python3
"""
Test Plan for GitHub Issue #65: Add rate limiting to API endpoints

This script tests whether rate limiting is properly implemented on the API endpoints.
It follows the test plan specified in the issue.
"""

import json
import sys
import time
from pathlib import Path

# Add dashboard to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent / "dashboard"))

from fastapi.testclient import TestClient
from main import app

# Test client for making requests
client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────────
# TEST RESULTS TRACKING
# ─────────────────────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.details = ""

    def set_pass(self, message: str = "", details: str = ""):
        self.passed = True
        self.message = message
        self.details = details

    def set_fail(self, message: str = "", details: str = ""):
        self.passed = False
        self.message = message
        self.details = details

    def report(self):
        status = "PASS" if self.passed else "FAIL"
        print(f"\n{'='*80}")
        print(f"[{status}] {self.name}")
        print(f"{'='*80}")
        if self.message:
            print(f"Message: {self.message}")
        if self.details:
            print(f"Details:\n{self.details}")


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 1: EXAMINE BACKEND CODE FOR RATE LIMITING MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────────────────

def test_step1_examine_code():
    """Check if rate limiting middleware exists in the codebase."""
    result = TestResult("Step 1: Examine backend code for rate limiting middleware")

    main_py = Path(__file__).parent / "dashboard" / "main.py"
    main_content = main_py.read_text()

    # Check for rate limiting related imports
    rate_limit_indicators = [
        "slowapi",
        "RateLimiter",
        "limiter",
        "rate_limit",
        "429",
        "Too Many Requests",
        "limiter = Limiter",
    ]

    found_indicators = []
    for indicator in rate_limit_indicators:
        if indicator.lower() in main_content.lower():
            found_indicators.append(indicator)

    if found_indicators:
        result.set_pass(
            f"Found {len(found_indicators)} rate limiting indicator(s)",
            f"Indicators found: {', '.join(found_indicators)}"
        )
    else:
        result.set_fail(
            "No rate limiting middleware or indicators found in main.py",
            "Expected to find slowapi, RateLimiter, limiter, rate_limit, or 429 references"
        )

    result.report()
    return result.passed


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 2: CHECK IF RATE LIMITER IS IMPLEMENTED (REDIS, IN-MEMORY, ETC)
# ─────────────────────────────────────────────────────────────────────────────────

def test_step2_check_implementation():
    """Check what type of rate limiter is implemented, if any."""
    result = TestResult("Step 2: Check if rate limiter is implemented (Redis, in-memory, etc)")

    main_py = Path(__file__).parent / "dashboard" / "main.py"
    main_content = main_py.read_text()

    # Check for different rate limiter implementations
    implementations = {
        "slowapi": "slowapi" in main_content.lower(),
        "redis": "redis" in main_content.lower(),
        "in-memory": "in_memory" in main_content.lower() or "dict()" in main_content,
        "custom": "rate_limit" in main_content.lower() or "limiter" in main_content.lower(),
    }

    found_impls = [k for k, v in implementations.items() if v]

    if found_impls:
        result.set_pass(
            f"Found {len(found_impls)} potential implementation(s)",
            f"Types found: {', '.join(found_impls)}"
        )
    else:
        result.set_fail(
            "No rate limiter implementation found",
            "Expected to find slowapi, Redis, or custom in-memory implementation"
        )

    result.report()
    return result.passed


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 3: TEST RATE LIMIT BY SENDING MULTIPLE RAPID REQUESTS
# ─────────────────────────────────────────────────────────────────────────────────

def test_step3_rapid_requests():
    """Send 100+ requests to /api/health endpoint in rapid succession."""
    result = TestResult("Step 3: Test rate limit by sending 100+ rapid requests")

    endpoint = "/api/health"
    num_requests = 110

    print(f"  Sending {num_requests} rapid requests to {endpoint}...")

    responses = []
    start_time = time.time()

    for i in range(num_requests):
        try:
            response = client.get(endpoint)
            responses.append({
                "status_code": response.status_code,
                "time": time.time() - start_time,
                "order": i
            })
            # Print progress every 10 requests
            if (i + 1) % 10 == 0:
                print(f"    Sent {i + 1}/{num_requests} requests...")
        except Exception as e:
            print(f"    ERROR on request {i}: {e}")

    elapsed = time.time() - start_time

    # Analyze responses
    success_count = sum(1 for r in responses if r["status_code"] == 200)
    rate_limited_count = sum(1 for r in responses if r["status_code"] == 429)
    other_errors = sum(1 for r in responses if r["status_code"] not in (200, 429))

    details = f"""
Total requests sent: {num_requests}
Time elapsed: {elapsed:.2f} seconds
Request rate: {num_requests/elapsed:.1f} req/sec

Response breakdown:
- 200 OK: {success_count}
- 429 Too Many Requests: {rate_limited_count}
- Other errors: {other_errors}
"""

    if rate_limited_count > 0:
        result.set_pass(
            f"Rate limiting detected: {rate_limited_count} requests returned 429",
            details
        )
    else:
        result.set_fail(
            f"No rate limiting detected: all {success_count} requests succeeded",
            details
        )

    result.report()
    return rate_limited_count > 0


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 4: VERIFY 429 RESPONSE WHEN LIMIT EXCEEDED
# ─────────────────────────────────────────────────────────────────────────────────

def test_step4_verify_429():
    """Verify that 429 Too Many Requests response is returned correctly."""
    result = TestResult("Step 4: Verify 429 Too Many Requests response when limit exceeded")

    endpoint = "/api/health"
    num_requests = 110

    print(f"  Sending {num_requests} requests to {endpoint}...")

    responses = []
    for i in range(num_requests):
        response = client.get(endpoint)
        responses.append(response)
        if (i + 1) % 20 == 0:
            print(f"    Sent {i + 1}/{num_requests} requests...")

    # Find 429 responses
    responses_429 = [r for r in responses if r.status_code == 429]

    if not responses_429:
        result.set_fail(
            "No 429 responses received",
            f"Out of {len(responses)} requests, none returned 429"
        )
    else:
        # Check response format
        sample_429 = responses_429[0]
        has_content = bool(sample_429.content)

        try:
            body = sample_429.json()
            has_proper_format = isinstance(body, dict)
        except:
            has_proper_format = False
            body = None

        details = f"""
Number of 429 responses: {len(responses_429)}
Has response body: {has_content}
Response format is JSON dict: {has_proper_format}
Sample 429 response: {json.dumps(body, indent=2) if body else 'N/A'}
"""

        if has_content and has_proper_format:
            result.set_pass(
                "429 responses properly formatted",
                details
            )
        else:
            result.set_fail(
                "429 responses received but format may be incorrect",
                details
            )

    result.report()
    return len(responses_429) > 0


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 5: CONFIRM LIMIT RESET AFTER TIME WINDOW
# ─────────────────────────────────────────────────────────────────────────────────

def test_step5_limit_reset():
    """Test that rate limit resets after the specified time window."""
    result = TestResult("Step 5: Confirm limit reset after time window")

    endpoint = "/api/health"

    # First, saturate the rate limit
    print("  Saturating rate limit...")
    for i in range(110):
        client.get(endpoint)

    # Check current state
    time.sleep(0.5)
    check_response = client.get(endpoint)
    rate_limited_now = check_response.status_code == 429

    print(f"  Currently rate limited: {rate_limited_now}")
    print("  WARNING: Full rate limit reset test requires waiting for time window")
    print("           (typically 1-60 seconds depending on implementation)")
    print("  This test can only verify current state, not the reset.")

    details = f"""
Current state check after burst:
- Endpoint: {endpoint}
- Response status: {check_response.status_code}
- Rate limited now: {rate_limited_now}

Full reset testing would require:
1. Saturating the rate limit
2. Waiting for the configured time window (unknown, not yet implemented)
3. Retrying and verifying requests succeed

This step cannot be fully verified until rate limiting is implemented
and its configuration (time window, request limit) is known.
"""

    if rate_limited_now:
        result.set_pass(
            "Rate limit is active (detected 429 after burst)",
            details + "\nNOTE: Full reset test requires implementation details"
        )
    else:
        result.set_fail(
            "Could not verify rate limit state",
            details
        )

    result.report()
    return rate_limited_now


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 6: TEST DIFFERENT ENDPOINTS FOR CONSISTENT RATE LIMITING
# ─────────────────────────────────────────────────────────────────────────────────

def test_step6_different_endpoints():
    """Test rate limiting on different endpoints."""
    result = TestResult("Step 6: Test different endpoints for consistent rate limiting")

    # Endpoints to test (ones that don't require auth in this test environment)
    endpoints = [
        "/api/health",
        "/api/diagnostics",
    ]

    results_by_endpoint = {}

    for endpoint in endpoints:
        print(f"  Testing {endpoint}...")
        rate_limited = False

        for i in range(30):
            try:
                response = client.get(endpoint)
                if response.status_code == 429:
                    rate_limited = True
                    break
            except:
                pass

        results_by_endpoint[endpoint] = {
            "tested": True,
            "rate_limited": rate_limited,
        }
        print(f"    Rate limited: {rate_limited}")

    details = json.dumps(results_by_endpoint, indent=2)

    any_rate_limited = any(r["rate_limited"] for r in results_by_endpoint.values())

    if any_rate_limited:
        result.set_pass(
            "Rate limiting found on tested endpoints",
            details
        )
    else:
        result.set_fail(
            "No rate limiting found on any tested endpoints",
            details
        )

    result.report()
    return any_rate_limited


# ─────────────────────────────────────────────────────────────────────────────────
# STEP 7: VERIFY LEGITIMATE REQUESTS WITHIN LIMIT ARE NOT REJECTED
# ─────────────────────────────────────────────────────────────────────────────────

def test_step7_legitimate_requests():
    """Verify that normal requests within the limit are not rejected."""
    result = TestResult("Step 7: Verify legitimate requests within limit are not rejected")

    endpoint = "/api/health"
    num_requests = 5  # Very conservative, should be well within any limit

    print(f"  Sending {num_requests} normal requests to {endpoint}...")

    responses = []
    for i in range(num_requests):
        response = client.get(endpoint)
        responses.append(response.status_code)
        time.sleep(0.1)  # Space them out

    success_count = sum(1 for code in responses if code == 200)
    failed_count = len(responses) - success_count

    details = f"""
Requests sent: {num_requests}
Successful (200): {success_count}
Failed: {failed_count}
Response codes: {responses}
"""

    if success_count == num_requests:
        result.set_pass(
            f"All {num_requests} legitimate requests succeeded",
            details
        )
    else:
        result.set_fail(
            f"Some legitimate requests were rejected: {success_count}/{num_requests}",
            details
        )

    result.report()
    return success_count == num_requests


# ─────────────────────────────────────────────────────────────────────────────────
# MAIN TEST EXECUTION
# ─────────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*80)
    print("GITHUB ISSUE #65 TEST PLAN: Add rate limiting to API endpoints")
    print("="*80)

    results = []

    # Execute all tests
    print("\n[Test 1/7] Examining backend code...")
    results.append(("Step 1", test_step1_examine_code()))

    print("\n[Test 2/7] Checking implementation type...")
    results.append(("Step 2", test_step2_check_implementation()))

    print("\n[Test 3/7] Testing rapid requests...")
    results.append(("Step 3", test_step3_rapid_requests()))

    print("\n[Test 4/7] Verifying 429 response format...")
    results.append(("Step 4", test_step4_verify_429()))

    print("\n[Test 5/7] Testing limit reset...")
    results.append(("Step 5", test_step5_limit_reset()))

    print("\n[Test 6/7] Testing different endpoints...")
    results.append(("Step 6", test_step6_different_endpoints()))

    print("\n[Test 7/7] Testing legitimate requests...")
    results.append(("Step 7", test_step7_legitimate_requests()))

    # Summary report
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}\n")

    for step_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {step_name}")

    print("\n" + "="*80)

    if passed == total:
        print("RESULT: All tests PASSED - Rate limiting is properly implemented")
        print("        Issue #65 can be CLOSED")
    elif passed > 0:
        print("RESULT: Some tests PASSED - Partial rate limiting implementation")
        print("        Issue #65 requires additional work")
    else:
        print("RESULT: All tests FAILED - Rate limiting is NOT implemented")
        print("        Issue #65 requires full implementation")

    print("="*80 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
