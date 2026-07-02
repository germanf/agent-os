#!/usr/bin/env python3
"""Verify CodexBackend and KimiBackend instantiate and produce valid commands."""

import sys

from dashboard.backends.codex import CodexBackend
from dashboard.backends.kimi import KimiBackend
from dashboard.backends.protocol import Done, TextDelta


def test_backend(backend, name: str) -> list[str]:
    errors = []
    cmd = backend.build_command("hello", session_id="sess_1", first=True)
    if not isinstance(cmd, list) or not cmd:
        errors.append(f"{name}: build_command returned invalid cmd={cmd!r}")

    cmd2 = backend.build_command("follow up", session_id="sess_1", first=False)
    if not isinstance(cmd2, list) or not cmd2:
        errors.append(f"{name}: build_command (not first) returned invalid cmd={cmd2!r}")

    evt = backend.parse_line('{"type": "text", "content": "hi"}')
    if not isinstance(evt, TextDelta):
        errors.append(f"{name}: parse_line(text) did not return TextDelta: {evt!r}")

    evt = backend.parse_line('{"type": "result"}')
    if not isinstance(evt, Done):
        errors.append(f"{name}: parse_line(result) did not return Done: {evt!r}")

    evt = backend.parse_line("raw text line")
    if not isinstance(evt, TextDelta):
        errors.append(f"{name}: parse_line(raw) did not return TextDelta: {evt!r}")

    evt = backend.parse_line("")
    if evt is not None:
        errors.append(f"{name}: parse_line(empty) should return None")

    return errors


def main():
    errors = []
    errors += test_backend(CodexBackend(), "CodexBackend")
    errors += test_backend(KimiBackend(), "KimiBackend")

    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print("✅ All backend tests passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
