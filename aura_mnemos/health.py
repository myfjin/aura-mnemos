"""Mnemos health sidecar — honest /health that survives a dead store."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from aura_mnemos.store import resolve_db_path


VERSION = "0.1.0"


class CheckResult(BaseModel):
    name: str
    status: str  # "ok" | "degraded" | "down"
    latency_ms: Optional[float] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    checks: list[CheckResult]


def sqlite_check(db_path: Optional[Path] = None) -> CheckResult:
    start = datetime.now(timezone.utc)
    path = db_path or resolve_db_path()
    try:
        if not path.exists():
            return CheckResult(
                name="sqlite",
                status="down",
                detail=f"database not found: {path}",
            )
        conn = sqlite3.connect(str(path))
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
        return CheckResult(
            name="sqlite",
            status="ok",
            latency_ms=(datetime.now(timezone.utc) - start).total_seconds() * 1000,
            detail=str(path),
        )
    except Exception as exc:
        return CheckResult(
            name="sqlite",
            status="down",
            detail=str(exc),
        )


def table_check(db_path: Optional[Path] = None) -> CheckResult:
    start = datetime.now(timezone.utc)
    path = db_path or resolve_db_path()
    try:
        if not path.exists():
            return CheckResult(
                name="memories_table",
                status="down",
                detail=f"database not found: {path}",
            )
        conn = sqlite3.connect(str(path))
        try:
            conn.execute("SELECT count(*) FROM memories")
        finally:
            conn.close()
        return CheckResult(
            name="memories_table",
            status="ok",
            latency_ms=(datetime.now(timezone.utc) - start).total_seconds() * 1000,
            detail=str(path),
        )
    except Exception as exc:
        return CheckResult(
            name="memories_table",
            status="down",
            detail=str(exc),
        )


def build_health_router(version: str, checks: list[Callable[[], CheckResult]]):
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health():
        results = [check() for check in checks]
        worst = max(
            (["ok", "degraded", "down"].index(c.status) for c in results),
            default=0,
        )
        overall = ["ok", "degraded", "down"][worst]
        return HealthResponse(
            status=overall,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            checks=results,
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(title="aura-mnemos-health", version=VERSION)
    app.include_router(
        build_health_router(
            version=VERSION,
            checks=[
                sqlite_check,
                table_check,
            ],
        )
    )
    return app


def main():
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
