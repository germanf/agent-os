#!/bin/bash
# Test plan for Issue #65 - Rate Limiting

BASE_URL="http://localhost:8765"

echo "========================================================================"
echo "ISSUE #65 - Rate Limiting Test Plan"
echo "========================================================================"

# ──────────────────────────────────────────────────────────────────────────
# TEST 1: Normal requests (within limit)
# ──────────────────────────────────────────────────────────────────────────
echo ""
echo "TEST 1: Normal requests (within limit)"
echo "========================================================================"

success_count=0
for i in {1..5}; do
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/health")
    http_code=$(echo "$response" | tail -n1)
    if [ "$http_code" = "200" ]; then
        echo "  Request $i: 200 OK ✓"
        ((success_count++))
    else
        echo "  Request $i: $http_code ✗"
    fi
done

if [ "$success_count" -eq 5 ]; then
    echo "✓ TEST 1 PASSED: All 5 requests succeeded"
    test1_pass=1
else
    echo "✗ TEST 1 FAILED: Only $success_count/5 requests succeeded"
    test1_pass=0
fi

# ──────────────────────────────────────────────────────────────────────────
# TEST 2: Rate limit exceeded (100 rapid requests)
# ──────────────────────────────────────────────────────────────────────────
echo ""
echo "TEST 2: Rate limit exceeded (100 rapid requests to /api/health)"
echo "========================================================================"

success_count=0
rate_limited_count=0

# Create temp file for responses
tmpfile=$(mktemp)

for i in {1..100}; do
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/health")
    http_code=$(echo "$response" | tail -n1)
    echo "$http_code" >> "$tmpfile"

    if [ "$http_code" = "200" ]; then
        ((success_count++))
    elif [ "$http_code" = "429" ]; then
        ((rate_limited_count++))
    fi
done

echo "  Sent 100 requests"
echo "  Results: $success_count succeeded (200), $rate_limited_count rate limited (429)"

if [ "$success_count" -ge 60 ] && [ "$rate_limited_count" -gt 0 ]; then
    echo "✓ TEST 2 PASSED: Expected ~60 success, ~40 rate limited"
    test2_pass=1
else
    echo "✗ TEST 2 FAILED: Expected 60+ success and 40+ rate limited, got $success_count and $rate_limited_count"
    test2_pass=0
fi

rm -f "$tmpfile"

# ──────────────────────────────────────────────────────────────────────────
# TEST 3: Response headers when rate limited
# ──────────────────────────────────────────────────────────────────────────
echo ""
echo "TEST 3: Response headers when rate limited"
echo "========================================================================"

# Send requests until we hit rate limit
headers_file=$(mktemp)
for i in {1..70}; do
    response=$(curl -s -i "$BASE_URL/api/health" 2>/dev/null)
    http_code=$(echo "$response" | head -n1 | awk '{print $2}')

    if [ "$http_code" = "429" ]; then
        echo "$response" > "$headers_file"

        # Check for required headers
        echo "  Checking headers for 429 response..."

        retry_after=$(grep -i "Retry-After" "$headers_file" | head -1)
        if [ -n "$retry_after" ]; then
            echo "    $retry_after ✓"
        else
            echo "    Retry-After header MISSING ✗"
        fi

        rate_limit=$(grep -i "X-RateLimit-Limit" "$headers_file" | head -1)
        if [ -n "$rate_limit" ]; then
            echo "    $rate_limit ✓"
        else
            echo "    X-RateLimit-Limit header MISSING ✗"
        fi

        rate_remaining=$(grep -i "X-RateLimit-Remaining" "$headers_file" | head -1)
        if [ -n "$rate_remaining" ]; then
            echo "    $rate_remaining ✓"
        else
            echo "    X-RateLimit-Remaining header MISSING ✗"
        fi

        if [ -n "$retry_after" ] && [ -n "$rate_limit" ] && [ -n "$rate_remaining" ]; then
            echo "✓ TEST 3 PASSED: All required headers present"
            test3_pass=1
        else
            echo "✗ TEST 3 FAILED: Some headers missing"
            test3_pass=0
        fi

        break
    fi
done

rm -f "$headers_file"

# ──────────────────────────────────────────────────────────────────────────
# TEST 4: Different endpoints have different limits
# ──────────────────────────────────────────────────────────────────────────
echo ""
echo "TEST 4: Different endpoints have different limits"
echo "========================================================================"

# Test /api/health (60/min limit)
echo "  Testing /api/health (60/minute limit)..."
success_count=0
for i in {1..65}; do
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/health")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ]; then
        ((success_count++))
    elif [ "$http_code" = "429" ] && [ "$i" -ge 60 ]; then
        echo "    Rate limited at request $i ✓"
        break
    fi
done

if [ "$success_count" -ge 60 ] && [ "$success_count" -le 65 ]; then
    echo "    /api/health: $success_count requests before limit ✓"
    echo "✓ TEST 4 PASSED: Endpoint limits working"
    test4_pass=1
else
    echo "    /api/health: Expected 60-65, got $success_count"
    echo "✗ TEST 4 FAILED: Endpoint limits not working as expected"
    test4_pass=0
fi

# ──────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================================"
echo "TEST SUMMARY"
echo "========================================================================"

passed=0
failed=0

[ "$test1_pass" -eq 1 ] && ((passed++)) || ((failed++))
[ "$test2_pass" -eq 1 ] && ((passed++)) || ((failed++))
[ "$test3_pass" -eq 1 ] && ((passed++)) || ((failed++))
[ "$test4_pass" -eq 1 ] && ((passed++)) || ((failed++))

echo "[$([ "$test1_pass" -eq 1 ] && echo 'PASS' || echo 'FAIL')] TEST 1: Normal requests (within limit)"
echo "[$([ "$test2_pass" -eq 1 ] && echo 'PASS' || echo 'FAIL')] TEST 2: Rate limit exceeded"
echo "[$([ "$test3_pass" -eq 1 ] && echo 'PASS' || echo 'FAIL')] TEST 3: Response headers"
echo "[$([ "$test4_pass" -eq 1 ] && echo 'PASS' || echo 'FAIL')] TEST 4: Different endpoint limits"

echo ""
echo "Total: $passed PASS, $failed FAIL"

if [ "$failed" -eq 0 ]; then
    echo ""
    echo "✓ ALL TESTS PASSED"
    exit 0
else
    echo ""
    echo "✗ $failed TEST(S) FAILED"
    exit 1
fi
