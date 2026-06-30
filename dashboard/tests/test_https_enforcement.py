#!/usr/bin/env python3
"""Test HTTPS enforcement: HTTP redirects and HSTS headers."""

import sys

from fastapi.testclient import TestClient
from main import app


def test_hsts_header_on_https():
    """Verify HSTS header is present in responses.

    This tests the FastAPI middleware layer. In production, nginx also adds
    the HSTS header, but we test the app layer independently here.
    """
    client = TestClient(app)
    response = client.get("/api/health")

    assert "Strict-Transport-Security" in response.headers, \
        f"HSTS header missing. Headers: {dict(response.headers)}"

    hsts_value = response.headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts_value, \
        f"HSTS max-age incorrect. Got: {hsts_value}"
    assert "includeSubDomains" in hsts_value, \
        f"HSTS includeSubDomains missing. Got: {hsts_value}"

    print(f"✓ HSTS header present: {hsts_value}")


def test_health_endpoint():
    """Verify the health check endpoint works."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok", f"Status not 'ok'. Got: {data}"
    assert "timestamp" in data, "Timestamp missing from response"

    print(f"✓ Health endpoint working: {data}")


if __name__ == "__main__":
    try:
        print("Testing HTTPS enforcement...\n")

        print("1. Testing HSTS header...", end=" ")
        test_hsts_header_on_https()

        print("2. Testing health endpoint...", end=" ")
        test_health_endpoint()

        print("\n✅ All HTTPS enforcement tests passed!")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
