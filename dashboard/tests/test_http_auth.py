#!/usr/bin/env python3
"""Test HTTP Basic Auth implementation for dashboard."""

import base64
import os
import sys

# Set up environment with test credentials
os.environ["DASH_USER"] = "testuser"
os.environ["DASH_PASS"] = "testpass123"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check_no_auth():
    """Health check should work without authentication."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_without_auth():
    """API routes should return 401 without authentication."""
    response = client.get("/api/credentials")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
    assert "Basic realm" in response.headers.get("WWW-Authenticate", "")


def test_api_with_correct_auth():
    """API routes should work with correct credentials."""
    credentials = base64.b64encode(b"testuser:testpass123").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/credentials", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_api_with_wrong_username():
    """API routes should return 401 with wrong username."""
    credentials = base64.b64encode(b"wronguser:testpass123").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/credentials", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_api_with_wrong_password():
    """API routes should return 401 with wrong password."""
    credentials = base64.b64encode(b"testuser:wrongpass").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/credentials", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_api_with_malformed_auth():
    """API routes should return 401 with malformed auth header."""
    headers = {"Authorization": "Bearer sometoken"}
    response = client.get("/api/credentials", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_api_with_invalid_base64():
    """API routes should return 401 with invalid base64."""
    headers = {"Authorization": "Basic not-valid-base64!!!"}
    response = client.get("/api/credentials", headers=headers)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_oauth_callback_no_auth():
    """OAuth callback should work without authentication (X.com redirect)."""
    # Just verify it doesn't trigger auth error
    # (Will return 400 because _oauth_handler is None, but that's expected)
    response = client.get("/auth/callback?code=test&state=test")
    assert response.status_code == 400  # Expected: OAuth handler not set up
    assert "401" not in response.text  # Should not be an auth error


def test_diagnostics_with_auth():
    """Diagnostics endpoint should require authentication."""
    # Without auth
    response = client.get("/api/diagnostics")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    # With auth
    credentials = base64.b64encode(b"testuser:testpass123").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/diagnostics", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


def test_jobs_endpoint_with_auth():
    """Jobs endpoint should require authentication."""
    credentials = base64.b64encode(b"testuser:testpass123").decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = client.get("/api/jobs", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


if __name__ == "__main__":
    print("Running HTTP Auth tests...")
    print()

    tests = [
        ("Health check (no auth required)", test_health_check_no_auth),
        ("API without auth", test_api_without_auth),
        ("API with correct auth", test_api_with_correct_auth),
        ("API with wrong username", test_api_with_wrong_username),
        ("API with wrong password", test_api_with_wrong_password),
        ("API with malformed auth", test_api_with_malformed_auth),
        ("API with invalid base64", test_api_with_invalid_base64),
        ("OAuth callback (no auth required)", test_oauth_callback_no_auth),
        ("Diagnostics with auth", test_diagnostics_with_auth),
        ("Jobs endpoint with auth", test_jobs_endpoint_with_auth),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}")
            print(f"  Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
