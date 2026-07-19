# aura-mnemos quickstart

Remember what matters. Recall when it counts.

## Install

```bash
pip install aura-mnemos             # MCP server only (stdlib, zero deps)
pip install "aura-mnemos[health]"   # + honest /health sidecar
```

## MCP client config

Add to your MCP client's config (e.g. `claude_desktop_config.json` or the equivalent for your agent):

```json
{
  "mcpServers": {
    "mnemos": {
      "command": "aura-mnemos",
      "args": []
    }
  }
}
```

Set the store location via environment variable (defaults to `~/.mnemos/mnemos.db`):

```bash
export MNEMOS_DB=/path/to/my-memories.db
```

## Tools

### `remember`

Store a memory with optional tags and source attribution.

```json
{
  "content": "The AURA mesh runs on trust and honest health endpoints.",
  "tags": "philosophy",
  "source": "6E"
}
```

Returns:

```json
{
  "id": 1,
  "created_at": "2026-07-19T12:00:00+00:00"
}
```

### `recall`

Search stored memories by content substring.

```json
{
  "query": "mesh",
  "limit": 10
}
```

Returns:

```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "content": "The AURA mesh runs on trust and honest health endpoints.",
      "tags": "philosophy",
      "source": "6E",
      "created_at": "2026-07-19T12:00:00+00:00"
    }
  ]
}
```

### `list_recent`

List the most recent memories.

```json
{
  "limit": 5
}
```

Returns the same shape as `recall`.

## Run the demo

```bash
python examples/demo.py
```

## Honest health

Start the health sidecar:

```bash
aura-mnemos-health
# or: MNEMOS_DB=/tmp/test.db aura-mnemos-health
```

When the store is alive:

```bash
curl http://127.0.0.1:8080/health
# → {"status":"ok","version":"0.1.0","checks":[{"name":"sqlite","status":"ok",...},{"name":"memories_table","status":"ok",...}]}
```

When the store is missing:

```bash
MNEMOS_DB=/nonexistent/db.sqlite aura-mnemos-health &
curl http://127.0.0.1:8080/health
# → {"status":"down","version":"0.1.0","checks":[{"name":"sqlite","status":"down",...},{"name":"memories_table","status":"down",...}]}
```

`checks` is a list; the top-level `status` is the worst of them (`ok` < `degraded` < `down`).

The disaster must actually happen. mnemos does not lie about its store.
