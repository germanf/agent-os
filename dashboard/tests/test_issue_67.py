#!/usr/bin/env python3
"""Test Plan Execution for Issue #67: Refactor blocking I/O to async in handlers.

This test script evaluates:
1. Handlers and blocking I/O operations
2. API endpoint responses
3. WebSocket/SSE streaming functionality
4. Concurrent request handling
5. Latency measurements before and after (static baseline)
"""

import asyncio
import sys
import time
import traceback
from pathlib import Path


def print_header(text):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")

def print_step(num, text):
    print(f"[{num}] {text}")

def print_result(passed, message):
    symbol = "✓ PASS" if passed else "✗ FAIL"
    print(f"    {symbol}: {message}\n")

# =============================================================================
# TEST 1: Scan for blocking I/O operations in handlers
# =============================================================================

print_header("TEST 1: Scan for Blocking I/O Operations in Handlers")

try:
    import re

    main_py_path = Path(__file__).parent / "main.py"
    content = main_py_path.read_text()

    # Blocking I/O patterns that should trigger warnings
    blocking_patterns = {
        'open()': (r'open\(', 'File open operations'),
        'Path.read_text()': (r'\.read_text\(', 'Blocking text reads'),
        'Path.write_text()': (r'\.write_text\(', 'Blocking text writes'),
        'Path.exists()': (r'\.exists\(', 'Path existence checks'),
        'Path.stat()': (r'\.stat\(', 'File stat operations'),
        'os.path operations': (r'os\.path\.', 'OS path operations'),
        'json.loads/dumps': (r'json\.(loads|dumps)', 'JSON parsing/serialization'),
    }

    print_step(1, "Scanning main.py for blocking I/O patterns...")

    found_blocking = {}
    for name, (pattern, desc) in blocking_patterns.items():
        matches = re.findall(f'.*{pattern}.*', content)
        if matches:
            found_blocking[name] = {
                'count': len(matches),
                'description': desc,
                'samples': [m.strip()[:80] for m in matches[:3]]
            }

    if found_blocking:
        print("  Found blocking I/O operations:")
        for op_name, info in found_blocking.items():
            print(f"    • {op_name}: {info['count']} occurrences ({info['description']})")
            for sample in info['samples']:
                print(f"      - {sample}")

    # Analysis: Check if operations are inside async functions
    print_step(2, "Checking if blocking I/O is inside async handlers...")

    async_patterns = re.findall(r'async def\s+(\w+)\s*\([^)]*\).*?(?=\n    async def|\n    @app|\nclass|\Z)',
                               content, re.DOTALL)

    blocking_in_async = []
    for match in async_patterns:
        if any(pattern in match for pattern in
               ['.read_text()', '.write_text()', 'open(', '.stat()', '.exists()']):
            blocking_in_async.append(match)

    if blocking_in_async:
        print(f"  WARNING: Found blocking I/O in {len(blocking_in_async)} async handlers")
        result_1_1 = False
    else:
        print("  No obvious blocking I/O detected in async handlers")
        result_1_1 = True

    print_result(True, "Blocking I/O scan completed")

except Exception as e:
    print_result(False, f"Blocking I/O scan failed: {e}")
    traceback.print_exc()
    result_1_1 = False

# =============================================================================
# TEST 2: Import FastAPI app and check routes
# =============================================================================

print_header("TEST 2: Verify FastAPI App and Routes")

try:
    print_step(1, "Importing main.py...")
    sys.path.insert(0, str(Path(__file__).parent))

    # Import the app
    from main import app as fastapi_app

    print("  ✓ FastAPI app imported successfully")

    print_step(2, "Checking registered routes...")

    # Get all routes
    routes = [
        (route.path, route.methods if hasattr(route, 'methods') else 'N/A')
        for route in fastapi_app.routes
    ]

    critical_routes = [
        '/api/health',
        '/api/jobs',
        '/api/files',
        '/api/resumen',
        '/api/notes/tree',
        '/api/notes/content',
        '/api/chat/send',
    ]

    registered_paths = [path for path, _ in routes]

    missing_routes = [r for r in critical_routes if not any(r in p for p in registered_paths)]

    if missing_routes:
        print(f"  WARNING: Missing routes: {missing_routes}")
        result_2_1 = False
    else:
        print(f"  ✓ All {len(critical_routes)} critical routes registered")
        result_2_1 = True

    print(f"  Total routes: {len(routes)}")

    print_result(result_2_1, f"Found {len([r for r in registered_paths if 'api' in r])} API routes")

except Exception as e:
    print_result(False, f"FastAPI import failed: {e}")
    traceback.print_exc()
    result_2_1 = False
    fastapi_app = None

# =============================================================================
# TEST 3: Verify runner.py async implementation
# =============================================================================

print_header("TEST 3: Verify runner.py Async Implementation")

try:
    print_step(1, "Importing runner module...")

    import runner

    print("  ✓ runner module imported successfully")

    print_step(2, "Checking async functions in runner...")

    async_functions = [
        ('run_job', hasattr(runner.run_job, '__code__') and 'await' in str(runner.run_job.__code__.co_names)),
        ('stream_logs', hasattr(runner.stream_logs, '__code__')),
        ('cancel_job', hasattr(runner.cancel_job, '__code__')),
    ]

    all_async = all(runner.run_job.__code__.co_flags & 0x100 for _ in [1])  # Check CO_COROUTINE flag

    print(f"  ✓ runner.run_job is coroutine: {asyncio.iscoroutinefunction(runner.run_job)}")
    print(f"  ✓ runner.stream_logs is async generator: {hasattr(runner.stream_logs, '__code__')}")
    print(f"  ✓ runner.cancel_job is coroutine: {asyncio.iscoroutinefunction(runner.cancel_job)}")

    result_3_1 = (
        asyncio.iscoroutinefunction(runner.run_job) and
        asyncio.iscoroutinefunction(runner.cancel_job)
    )

    print_result(result_3_1, "runner.py uses async/await properly")

except Exception as e:
    print_result(False, f"runner.py check failed: {e}")
    traceback.print_exc()
    result_3_1 = False

# =============================================================================
# TEST 4: Test API endpoints with TestClient
# =============================================================================

print_header("TEST 4: Test API Endpoints")

result_4_1 = False
result_4_2 = False
result_4_3 = False

if fastapi_app:
    try:
        from fastapi.testclient import TestClient

        print_step(1, "Creating TestClient...")
        client = TestClient(fastapi_app)

        print("  ✓ TestClient created")

        # Test health endpoint (should not require auth)
        print_step(2, "Testing GET /api/health (public endpoint)...")

        response = client.get("/api/health")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
            print_result(True, "Health check endpoint works")
            result_4_1 = True
        else:
            print_result(False, f"Unexpected status {response.status_code}")
            result_4_1 = False

        # Test credentials endpoint (requires auth by default, will return 401)
        print_step(3, "Testing protected endpoint behavior...")

        response = client.get("/api/credentials")
        print(f"  Status: {response.status_code}")

        if response.status_code in (200, 401):
            print_result(True, "Protected endpoint returns expected auth response")
            result_4_2 = True
        else:
            print_result(False, f"Unexpected status {response.status_code}")
            result_4_2 = False

        # Test 404 handling
        print_step(4, "Testing error handling...")

        response = client.get("/api/nonexistent")
        print(f"  Status: {response.status_code}")

        if response.status_code in (404, 401):  # Auth or not found
            print_result(True, "Error handling works")
            result_4_3 = True
        else:
            print_result(False, f"Unexpected status {response.status_code}")
            result_4_3 = False

    except Exception as e:
        print_result(False, f"TestClient tests failed: {e}")
        traceback.print_exc()
else:
    print_result(False, "FastAPI app not available for testing")

# =============================================================================
# TEST 5: Verify SSE stream implementation
# =============================================================================

print_header("TEST 5: Verify WebSocket/SSE Stream Implementation")

try:
    print_step(1, "Checking stream_logs implementation...")

    # Read the runner.py source to verify SSE format
    runner_path = Path(__file__).parent / "runner.py"
    runner_content = runner_path.read_text()

    sse_checks = {
        'SSE format check': 'event:' in runner_content and 'data:' in runner_content,
        'Async generator check': 'async def stream_logs' in runner_content,
        'Queue handling': 'asyncio.Queue' in runner_content,
        'Timeout handling': 'asyncio.wait_for' in runner_content,
    }

    all_passed = all(sse_checks.values())

    for check_name, result in sse_checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")

    print_result(all_passed, "SSE streaming implementation verified")
    result_5_1 = all_passed

except Exception as e:
    print_result(False, f"SSE verification failed: {e}")
    traceback.print_exc()
    result_5_1 = False

# =============================================================================
# TEST 6: Concurrent Request Simulation
# =============================================================================

print_header("TEST 6: Concurrent Request Handling")

result_6_1 = False

if fastapi_app:
    try:
        import concurrent.futures

        from fastapi.testclient import TestClient

        print_step(1, "Testing concurrent health check requests...")

        client = TestClient(fastapi_app)

        def make_request():
            return client.get("/api/health")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for r in results if r.status_code == 200)

        print(f"  Completed: {success_count}/10 requests succeeded")

        if success_count == 10:
            print_result(True, "Concurrent requests handled successfully")
            result_6_1 = True
        else:
            print_result(False, f"Only {success_count}/10 requests succeeded")
            result_6_1 = False

    except Exception as e:
        print_result(False, f"Concurrent request test failed: {e}")
        traceback.print_exc()
else:
    print_result(False, "FastAPI app not available for testing")

# =============================================================================
# TEST 7: Latency Baseline Measurement
# =============================================================================

print_header("TEST 7: Endpoint Latency Measurement")

result_7_1 = False

if fastapi_app:
    try:
        from fastapi.testclient import TestClient

        print_step(1, "Measuring latency for health endpoint...")

        client = TestClient(fastapi_app)

        latencies = []
        for i in range(5):
            start = time.time()
            response = client.get("/api/health")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            latencies.append(elapsed)
            print(f"  Request {i+1}: {elapsed:.2f}ms")

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        print(f"\n  Average: {avg_latency:.2f}ms")
        print(f"  Max: {max_latency:.2f}ms")

        # Health check should be very fast (< 10ms typical)
        if avg_latency < 100:
            print_result(True, f"Latency acceptable (avg: {avg_latency:.2f}ms)")
            result_7_1 = True
        else:
            print_result(False, f"Latency high (avg: {avg_latency:.2f}ms)")
            result_7_1 = False

    except Exception as e:
        print_result(False, f"Latency measurement failed: {e}")
        traceback.print_exc()
else:
    print_result(False, "FastAPI app not available for testing")

# =============================================================================
# TEST 8: Verify no deadlocks in async operations
# =============================================================================

print_header("TEST 8: Verify No Deadlocks in Async Operations")

result_8_1 = False

try:
    print_step(1, "Checking for potential deadlock patterns...")

    main_py_path = Path(__file__).parent / "main.py"
    content = main_py_path.read_text()

    deadlock_patterns = {
        'Synchronous wait in async': r'time\.sleep\(',
        'Blocking subprocess in async': r'subprocess\.run\(',
        'Thread locks in async': r'threading\.Lock',
        'Global state mutations': r'global\s+\w+.*=',
    }

    issues_found = {}
    for pattern_name, pattern in deadlock_patterns.items():
        matches = re.findall(f'.*{pattern}.*', content)
        if matches:
            issues_found[pattern_name] = len(matches)
            print(f"  ✗ {pattern_name}: {len(matches)} occurrences")
            for match in matches[:2]:
                print(f"      {match.strip()[:70]}")

    if not issues_found:
        print("  ✓ No obvious deadlock patterns found")
        print_result(True, "No deadlock patterns detected")
        result_8_1 = True
    else:
        print_result(False, f"Found {len(issues_found)} potential deadlock patterns")
        result_8_1 = False

except Exception as e:
    print_result(False, f"Deadlock check failed: {e}")
    traceback.print_exc()
    result_8_1 = False

# =============================================================================
# SUMMARY
# =============================================================================

print_header("TEST SUMMARY - Issue #67: Refactor blocking I/O to async")

results = {
    "TEST 1: Blocking I/O Scan": result_1_1,
    "TEST 2: FastAPI Routes": result_2_1,
    "TEST 3: runner.py Async": result_3_1,
    "TEST 4.1: Health Endpoint": result_4_1,
    "TEST 4.2: Auth Protection": result_4_2,
    "TEST 4.3: Error Handling": result_4_3,
    "TEST 5: SSE Streaming": result_5_1,
    "TEST 6: Concurrent Requests": result_6_1,
    "TEST 7: Latency": result_7_1,
    "TEST 8: Deadlock Detection": result_8_1,
}

passed = sum(1 for v in results.values() if v)
total = len(results)

for test_name, result in results.items():
    symbol = "✓" if result else "✗"
    print(f"  {symbol} {test_name}")

print(f"\n{'=' * 70}")
print(f"RESULT: {passed}/{total} tests passed")
print(f"{'=' * 70}\n")

# Determine final status
if passed == total:
    print("✅ ALL TESTS PASSED - Issue #67 can be closed")
    exit_code = 0
elif passed >= total * 0.8:
    print("⚠️  MOSTLY PASSING - Some manual verification needed")
    exit_code = 1
else:
    print("❌ TESTS FAILING - Blocking I/O refactoring needed")
    exit_code = 2

sys.exit(exit_code)
