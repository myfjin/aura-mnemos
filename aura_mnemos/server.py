"""Mnemos MCP server — stdio, stdlib-only memory tools."""

import sys
import json
import os
from datetime import datetime, timezone

from aura_mnemos.store import init_db, connect, resolve_db_path


VERSION = "0.1.0"
NAME = "mnemos"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def send_message(msg: dict) -> None:
    payload = json.dumps(msg)
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()


def recv_message():
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            log(f"Ignoring non-JSON line: {line[:200]}")
            continue


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "content": row["content"],
        "tags": row["tags"],
        "source": row["source"],
        "created_at": row["created_at"],
    }


def handle_remember(args: dict) -> dict:
    content = args.get("content")
    if not isinstance(content, str) or content == "":
        return {"error": "content is required and must be a non-empty string"}
    tags = args.get("tags")
    source = args.get("source")
    created_at = _now_iso()
    try:
        conn = connect()
        try:
            cur = conn.execute(
                "INSERT INTO memories (content, tags, source, created_at) VALUES (?, ?, ?, ?)",
                (content, tags, source, created_at),
            )
            conn.commit()
            return {"id": cur.lastrowid, "created_at": created_at}
        finally:
            conn.close()
    except Exception as exc:
        return {"error": str(exc)}


def handle_recall(args: dict) -> dict:
    query = args.get("query")
    if not isinstance(query, str):
        return {"error": "query is required and must be a string"}
    limit = args.get("limit", 10)
    try:
        limit = int(limit)
    except Exception:
        return {"error": "limit must be an integer"}
    try:
        conn = connect()
        try:
            cur = conn.execute(
                """SELECT id, content, tags, source, created_at
                   FROM memories
                   WHERE content LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (f"%{query}%", limit),
            )
            rows = [_row_to_dict(r) for r in cur.fetchall()]
            return {"count": len(rows), "results": rows}
        finally:
            conn.close()
    except Exception as exc:
        return {"error": str(exc)}


def handle_list_recent(args: dict) -> dict:
    limit = args.get("limit", 10)
    try:
        limit = int(limit)
    except Exception:
        return {"error": "limit must be an integer"}
    try:
        conn = connect()
        try:
            cur = conn.execute(
                """SELECT id, content, tags, source, created_at
                   FROM memories
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
            rows = [_row_to_dict(r) for r in cur.fetchall()]
            return {"count": len(rows), "results": rows}
        finally:
            conn.close()
    except Exception as exc:
        return {"error": str(exc)}


TOOL_MAP = {
    "remember": handle_remember,
    "recall": handle_recall,
    "list_recent": handle_list_recent,
}


def _build_tools_list() -> dict:
    return {
        "tools": [
            {
                "name": "remember",
                "description": "Persist a memory with optional tags and source.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "tags": {"type": "string"},
                        "source": {"type": "string"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "recall",
                "description": "Search memories by content substring.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "list_recent",
                "description": "List the most recent memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
        ]
    }


def _handle_call(msg: dict) -> None:
    params = msg.get("params", {})
    tool_name = params.get("name")
    args = params.get("arguments", {})
    handler = TOOL_MAP.get(tool_name)
    if handler is None:
        result = {"error": f"Unknown tool: {tool_name}"}
    else:
        try:
            result = handler(args)
        except Exception as exc:
            result = {"error": str(exc)}
    is_error = bool(result.get("error"))
    send_message({
        "jsonrpc": "2.0",
        "id": msg.get("id"),
        "result": {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            "isError": is_error,
        },
    })


def main():
    log(f"{NAME} MCP server starting (version {VERSION})")
    log(f"DB path: {resolve_db_path()}")
    try:
        init_db()
        log("Store initialized")
    except Exception as exc:
        log(f"WARNING: store init failed: {exc}")

    while True:
        msg = recv_message()
        if msg is None:
            log("Stdin closed. Exiting.")
            break

        method = msg.get("method")
        req_id = msg.get("id")

        if method == "initialize":
            send_message({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": NAME, "version": VERSION},
                },
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_message({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": _build_tools_list(),
            })
        elif method == "tools/call":
            _handle_call(msg)
        else:
            if req_id is not None:
                send_message({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                })


if __name__ == "__main__":
    main()
