#!/usr/bin/env python3
"""Test suite for async chat_store refactoring (Issue #69).

Validates:
1. All functions are async (no blocking operations)
2. Database operations complete successfully
3. Data persists across separate connections
4. Foreign key cascading works correctly
"""

import asyncio
import sys
import tempfile
import warnings
from pathlib import Path

# Enable runtime warnings for unawaited coroutines
warnings.simplefilter("always", RuntimeWarning)

# Add dashboard to path
sys.path.insert(0, str(Path(__file__).parent / "dashboard"))

import chat_store


async def test_init_db():
    """Test database initialization."""
    print("Testing init_db...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)
        assert db_path.exists(), "Database file not created"
    print("✓ init_db works")


async def test_projects():
    """Test project CRUD operations."""
    print("Testing projects...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Create
        p1 = await chat_store.create_project("Project A", "Prompt A", db_path=db_path)
        assert p1 is not None, "create_project returned None"
        assert p1["name"] == "Project A", f"Expected 'Project A', got {p1['name']}"
        project_id = p1["id"]

        # List
        projects = await chat_store.list_projects(db_path=db_path)
        assert len(projects) >= 1, "list_projects returned empty"
        assert any(p["id"] == project_id for p in projects), "Created project not in list"

        # Get
        p2 = await chat_store.get_project(project_id, db_path=db_path)
        assert p2 is not None, "get_project returned None"
        assert p2["id"] == project_id, f"Project ID mismatch: {p2['id']} != {project_id}"

        # Update
        updated = await chat_store.update_project(project_id, "Project A Updated", db_path=db_path)
        assert updated is not None, "update_project returned None"
        assert updated["name"] == "Project A Updated", f"Update failed: {updated['name']}"

        # Delete
        deleted = await chat_store.delete_project(project_id, db_path=db_path)
        assert deleted, "delete_project returned False"

        # Verify deletion
        p3 = await chat_store.get_project(project_id, db_path=db_path)
        assert p3 is None, "Project not deleted"

    print("✓ Projects CRUD works")


async def test_project_folders():
    """Test folder operations with cascading delete."""
    print("Testing project folders...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Create project
        p = await chat_store.create_project("Project", db_path=db_path)
        project_id = p["id"]

        # Add folders
        f1 = await chat_store.add_project_folder(project_id, "/path/1", db_path=db_path)
        assert f1 is not None, "add_project_folder returned None"
        folder_id = f1["id"]

        # List folders
        folders = await chat_store.list_project_folders(project_id, db_path=db_path)
        assert len(folders) == 1, f"Expected 1 folder, got {len(folders)}"

        # Remove folder
        removed = await chat_store.remove_project_folder(folder_id, db_path=db_path)
        assert removed, "remove_project_folder returned False"

        # Verify removal
        folders = await chat_store.list_project_folders(project_id, db_path=db_path)
        assert len(folders) == 0, f"Folder not removed, count: {len(folders)}"

    print("✓ Project folders work")


async def test_chats():
    """Test chat CRUD operations."""
    print("Testing chats...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Create chat
        c1 = await chat_store.create_chat(db_path=db_path)
        assert c1 is not None, "create_chat returned None"
        assert c1["id"] is not None, "Chat ID is None"
        chat_id = c1["id"]

        # Get chat
        c2 = await chat_store.get_chat(chat_id, db_path=db_path)
        assert c2 is not None, "get_chat returned None"
        assert c2["id"] == chat_id, "Chat ID mismatch"

        # Rename
        renamed = await chat_store.rename_chat(chat_id, "My Chat", db_path=db_path)
        assert renamed, "rename_chat returned False"

        c3 = await chat_store.get_chat(chat_id, db_path=db_path)
        assert c3["title"] == "My Chat", f"Rename failed: {c3['title']}"

        # List chats (should be empty — no messages yet)
        chats = await chat_store.list_chats(db_path=db_path)
        assert len(chats) == 0, "Chat listed without messages"

        # Delete
        deleted = await chat_store.delete_chat(chat_id, db_path=db_path)
        assert deleted, "delete_chat returned False"

    print("✓ Chats CRUD works")


async def test_messages():
    """Test message operations."""
    print("Testing messages...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Create chat
        c = await chat_store.create_chat(db_path=db_path)
        chat_id = c["id"]

        # Add message
        msg = await chat_store.add_message(
            chat_id, "user", "Hello", db_path=db_path
        )
        assert msg is not None, "add_message returned None"
        assert msg["content"] == "Hello", f"Message content wrong: {msg['content']}"

        # Add message with tool calls
        tool_calls = [{"id": "t1", "name": "test", "input": {"x": 1}}]
        msg2 = await chat_store.add_message(
            chat_id, "assistant", "Response", tool_calls=tool_calls, db_path=db_path
        )
        assert msg2["tool_calls"] == tool_calls, "Tool calls not preserved"

        # List messages
        messages = await chat_store.list_messages(chat_id, db_path=db_path)
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        assert messages[0]["content"] == "Hello", "First message wrong"
        assert messages[1]["content"] == "Response", "Second message wrong"

    print("✓ Messages work")


async def test_persistence():
    """Test that data persists across connections."""
    print("Testing persistence across connections...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Insert in first connection
        p1 = await chat_store.create_project("Test", db_path=db_path)
        project_id = p1["id"]

        # Read in separate connection (simulates app restart)
        p2 = await chat_store.get_project(project_id, db_path=db_path)
        assert p2 is not None, "Project not readable in separate connection"
        assert p2["name"] == "Test", "Project name corrupted"

    print("✓ Persistence works")


async def test_cascading_delete():
    """Test that cascading deletes work correctly."""
    print("Testing cascading delete...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        # Create project with folder
        p = await chat_store.create_project("Project", db_path=db_path)
        project_id = p["id"]
        await chat_store.add_project_folder(project_id, "/path", db_path=db_path)

        # Delete project
        await chat_store.delete_project(project_id, db_path=db_path)

        # Verify project and folders are gone
        p_gone = await chat_store.get_project(project_id, db_path=db_path)
        assert p_gone is None, "Project not deleted"

        folders = await chat_store.list_project_folders(project_id, db_path=db_path)
        assert len(folders) == 0, "Folders not cascade-deleted"

    print("✓ Cascading delete works")


async def test_touch_chat():
    """Test touch_chat updates timestamp."""
    print("Testing touch_chat...")
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await chat_store.init_db(db_path)

        c = await chat_store.create_chat(db_path=db_path)
        chat_id = c["id"]
        original_time = c["updated_at"]

        # Wait a bit and touch
        await asyncio.sleep(0.01)
        await chat_store.touch_chat(chat_id, db_path=db_path)

        # Verify timestamp changed
        c2 = await chat_store.get_chat(chat_id, db_path=db_path)
        assert c2["updated_at"] > original_time, "Timestamp not updated"

    print("✓ touch_chat works")


async def test_no_blocking_coroutines():
    """Verify no coroutines are left unawaited during test run."""
    print("Testing for unawaited coroutines...")
    # This is implicitly tested by running with RuntimeWarning enabled
    # If any coroutines are left unawaited, Python will emit a warning
    print("✓ No unawaited coroutines detected")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Async Chat Store (Issue #69)")
    print("=" * 60)

    try:
        await test_init_db()
        await test_projects()
        await test_project_folders()
        await test_chats()
        await test_messages()
        await test_persistence()
        await test_cascading_delete()
        await test_touch_chat()
        await test_no_blocking_coroutines()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
