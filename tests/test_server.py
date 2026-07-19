"""Tests for mnemos server."""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura_mnemos import store, server


def _set_temp_db(tmpdir: str) -> str:
    db_path = os.path.join(tmpdir, "mnemos.db")
    os.environ["MNEMOS_DB"] = db_path
    return db_path


def _call_tool(name: str, arguments: dict) -> dict:
    handler = server.TOOL_MAP[name]
    return handler(arguments)


def test_remember_recall_roundtrip():
    tmpdir = tempfile.mkdtemp()
    try:
        _set_temp_db(tmpdir)
        store.init_db()

        result = _call_tool("remember", {"content": "hello mnemos"})
        assert "error" not in result, f"remember failed: {result}"
        assert result.get("id") is not None
        assert result.get("created_at") is not None

        result = _call_tool("recall", {"query": "hello"})
        assert "error" not in result, f"recall failed: {result}"
        assert result["count"] >= 1
        contents = [r["content"] for r in result["results"]]
        assert "hello mnemos" in contents, f"expected content missing: {contents}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_recall_on_missing_store_returns_error_not_crash():
    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "mnemos.db")
        # Make the parent dir a FILE so sqlite cannot create the database.
        os.rmdir(tmpdir)
        with open(tmpdir, "w") as f:
            f.write("not a directory")
        os.environ["MNEMOS_DB"] = db_path

        result = _call_tool("remember", {"content": "will fail"})
        assert isinstance(result, dict), "handler must return a dict"
        assert "error" in result, f"expected error dict, got {result}"

        result2 = _call_tool("recall", {"query": "will fail"})
        assert isinstance(result2, dict), "handler must return a dict"
        assert "error" in result2, f"expected error dict, got {result2}"
    finally:
        if os.path.isfile(tmpdir):
            os.remove(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_list_recent_returns_recent():
    tmpdir = tempfile.mkdtemp()
    try:
        _set_temp_db(tmpdir)
        store.init_db()
        _call_tool("remember", {"content": "first"})
        _call_tool("remember", {"content": "second"})
        result = _call_tool("list_recent", {"limit": 2})
        assert "error" not in result, f"list_recent failed: {result}"
        assert result["count"] == 2
        contents = [r["content"] for r in result["results"]]
        assert "second" in contents
        assert "first" in contents
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    test_remember_recall_roundtrip()
    print("PASS: remember_recall_roundtrip")
    test_recall_on_missing_store_returns_error_not_crash()
    print("PASS: recall_on_missing_store_returns_error_not_crash")
    test_list_recent_returns_recent()
    print("PASS: list_recent_returns_recent")
    print("ALL PASSED")
