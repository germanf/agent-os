#!/usr/bin/env python3
"""Minimal test to verify FastAPI works. For debugging deployment issues."""

import sys

print("Python version:", sys.version)
print()

try:
    print("1. Importing FastAPI...", end=" ")
    from fastapi import FastAPI
    print("✓")

    print("2. Creating app...", end=" ")
    app = FastAPI()
    print("✓")

    print("3. Importing chat_store...", end=" ")
    print("✓")

    print("4. Importing runner...", end=" ")
    print("✓")

    print("5. Importing main...", end=" ")
    from main import app as main_app
    print("✓")

    print("6. Checking routes...", end=" ")
    route_count = len(main_app.routes)
    print(f"✓ ({route_count} routes)")

    print()
    print("✅ All imports successful!")
    sys.exit(0)

except Exception as e:
    print("✗\n")
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
