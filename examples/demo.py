#!/usr/bin/env python3
"""mnemos demo: remember 3 memories, recall them, print results.

Usage:
    export MNEMOS_DB=/tmp/mnemos_demo.db
    python examples/demo.py

Requires mnemos installed (pip install -e .) or PYTHONPATH set to the repo root.
"""

import os
import sys
import tempfile

# Point to a temp DB so we don't clobber anything real
os.environ.setdefault("MNEMOS_DB", os.path.join(tempfile.gettempdir(), "mnemos_demo.db"))

# Ensure the package is importable when run from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aura_mnemos.store import init_db, connect


def main():
    # --- setup ---
    db_path = os.environ["MNEMOS_DB"]
    print(f"mnemos demo — store at {db_path}")
    init_db(db_path)

    conn = connect(db_path)
    cur = conn.cursor()

    # --- remember 3 memories ---
    memories = [
        ("The AURA mesh runs on trust and honest health endpoints.", "philosophy", "6E"),
        ("A pattern library is only as good as its last cross-model review.", "workflow", "Fable"),
        ("mnemos remembers what agents forget between sessions.", "design", "Illia"),
    ]

    for content, tags, source in memories:
        cur.execute(
            "INSERT INTO memories (content, tags, source, created_at) VALUES (?, ?, ?, ?)",
            (content, tags, source, "2026-07-19T12:00:00+00:00"),
        )
        print(f"  ✓ remembered: {content[:50]}...")

    conn.commit()

    # --- recall ---
    cur.execute(
        "SELECT id, content, tags, source, created_at FROM memories WHERE content LIKE ? ORDER BY created_at DESC",
        ("%mesh%",),
    )
    results = cur.fetchall()

    print(f"\n--- recall(query='mesh') → {len(results)} result(s) ---")
    for row in results:
        print(f"  [{row['id']}] {row['content']}")
        print(f"       tags={row['tags']}  source={row['source']}  at={row['created_at']}")

    # --- list_recent ---
    cur.execute(
        "SELECT id, content, tags, source, created_at FROM memories ORDER BY created_at DESC LIMIT 5"
    )
    all_rows = cur.fetchall()

    print(f"\n--- list_recent(limit=5) → {len(all_rows)} result(s) ---")
    for row in all_rows:
        print(f"  [{row['id']}] {row['content'][:60]}...")

    conn.close()
    print("\n✓ demo complete. Clean up with: rm " + db_path)


if __name__ == "__main__":
    main()
