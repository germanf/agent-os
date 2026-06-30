#!/usr/bin/env python3
"""Test that .env files are created with restricted permissions (0o600)."""

import os
import sys
import tempfile
from pathlib import Path

# Add dashboard to path so we can import main
sys.path.insert(0, str(Path(__file__).parent))

from main import _write_env_file


def test_env_file_permissions():
    """Test that _write_env_file creates files with 0o600 permissions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"
        content = 'API_KEY="secret123"\nAPI_SECRET="secret456"'

        # Write the .env file using the helper
        _write_env_file(env_path, content)

        # Check that the file exists
        assert env_path.exists(), "File was not created"

        # Check that the file has the correct permissions
        file_mode = os.stat(env_path).st_mode & 0o777
        assert file_mode == 0o600, f"Expected permissions 0o600, got {oct(file_mode)}"

        # Check that the content is correct
        assert env_path.read_text() == content, "File content was not written correctly"

        print(f"✓ .env file created at {env_path}")
        print(f"✓ Permissions verified: {oct(file_mode)}")
        print("✓ Content verified")
        return True


if __name__ == "__main__":
    try:
        success = test_env_file_permissions()
        if success:
            print("\n✅ All tests passed!")
            sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
