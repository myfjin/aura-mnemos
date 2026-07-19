# aura-mnemos

**A persistent-memory MCP server for AI agents, with an honest health endpoint that survives its store dying.**

> Install name is `aura-mnemos` (`import aura_mnemos`); the plain name `mnemos` was already taken on PyPI by an unrelated project.

---

## Why

Every agent session starts blank. The conversation history is there, but the *knowing* — the things you learned last week, the patterns you noticed, the decisions you made — evaporates when the context window closes. mnemos is the shelf you put those things on. A small, durable, honest shelf.

And honest means honest. When the shelf breaks — the database file is missing, the disk is full, the permissions are wrong — mnemos tells you. It does not crash silently. It does not return empty results that look like "nothing found." It says "I am broken" in a way your agent can hear and act on. This is the disaster test: the server must survive its store dying, and the health endpoint must tell the truth about it.

---

## Install

```bash
pip install aura-mnemos             # MCP server only — stdlib, zero dependencies
pip install "aura-mnemos[health]"   # + FastAPI health sidecar
```

Requires Python ≥ 3.10.

---

## Use as an MCP server

Configure your MCP client to launch `aura-mnemos`:

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

The store lives at `~/.mnemos/mnemos.db` by default. Override with the `MNEMOS_DB` environment variable.

### Tools

**`remember`** — store a memory with optional tags and source.

```json
{
  "content": "The AURA mesh runs on trust and honest health endpoints.",
  "tags": "philosophy",
  "source": "6E"
}
```

Returns `{"id": 1, "created_at": "2026-07-19T12:00:00+00:00"}`.

**`recall`** — search memories by content substring.

```json
{
  "query": "mesh",
  "limit": 10
}
```

Returns `{"count": 1, "results": [{"id": 1, "content": "...", "tags": "...", "source": "...", "created_at": "..."}]}`.

**`list_recent`** — list the most recent memories.

```json
{
  "limit": 5
}
```

Same result shape as `recall`.

Every tool returns `{"error": "..."}` when the store is unreachable — the server never crashes, never lies.

---

## Honest health

Start the health sidecar:

```bash
aura-mnemos-health
# listens on 127.0.0.1:8080 by default; set PORT to change it
```

When the store is alive:

```bash
curl http://127.0.0.1:8080/health
```

```json
{
  "status": "ok",
  "timestamp": "2026-07-19T16:16:22.486547+00:00",
  "version": "0.1.0",
  "checks": [
    { "name": "sqlite", "status": "ok", "latency_ms": 0.27, "detail": "/home/you/.mnemos/mnemos.db" },
    { "name": "memories_table", "status": "ok", "latency_ms": 0.17, "detail": "/home/you/.mnemos/mnemos.db" }
  ]
}
```

When the store is missing:

```bash
MNEMOS_DB=/nonexistent/db.sqlite aura-mnemos-health &
curl http://127.0.0.1:8080/health
```

```json
{
  "status": "down",
  "timestamp": "2026-07-19T16:16:22.868237+00:00",
  "version": "0.1.0",
  "checks": [
    { "name": "sqlite", "status": "down", "latency_ms": null, "detail": "database not found: /nonexistent/db.sqlite" },
    { "name": "memories_table", "status": "down", "latency_ms": null, "detail": "database not found: /nonexistent/db.sqlite" }
  ]
}
```

The overall `status` is the worst of the individual checks (`ok` < `degraded` < `down`).

The disaster must actually happen. mnemos does not lie about its store. The test suite proves it: `test_health_down_when_db_missing` sets `MNEMOS_DB` to a path that does not exist and asserts the status is not `"ok"`. If that test ever passes when the store is alive, the test is lying — and the test is designed to fail when it lies.

---

## Roadmap (not shipped here)

These are directions the project may grow, but none of them exist yet:

- **Graph layer** — link memories by topic, entity, or relationship (beyond substring search)
- **Native apps** — desktop/mobile clients that read and write the same store
- **Framework adapters** — LangChain, CrewAI, Microsoft Semantic Kernel integrations
- **Mesh bridge** — sync stores across the AURA mesh (Ubuntu ↔ macOS)

If you want one of these, the store schema is stable and documented. The SQLite file is yours.

---

## Attribution / provenance

> Part of the AURA Pattern Library — © Reality Optimizer. Built by a human-led mesh of small models and Claude. Apache-2.0.

---

*The shelf is small. What you put on it is yours.*
