"""Local Postgres via pgserver (bundled binaries, no Docker/install)
plus a psycopg3 connection pool. The FastAPI app owns the DB lifecycle."""
from __future__ import annotations

import pathlib
from typing import Optional

import pgserver
from psycopg_pool import ConnectionPool

PGDATA = pathlib.Path(__file__).resolve().parent.parent / "pgdata"

_server: Optional["pgserver.PostgresServer"] = None
_pool: Optional[ConnectionPool] = None

DDL = """
CREATE TABLE IF NOT EXISTS waitlist (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT NOT NULL,
    company     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def start() -> str:
    """Boot the local Postgres cluster + pool, ensure schema. Returns the URI."""
    global _server, _pool
    PGDATA.mkdir(parents=True, exist_ok=True)
    _server = pgserver.get_server(PGDATA)
    uri = _server.get_uri()
    _pool = ConnectionPool(uri, min_size=1, max_size=10, kwargs={"autocommit": True})
    with _pool.connection() as conn:
        conn.execute(DDL)
    return uri


def stop() -> None:
    global _server, _pool
    if _pool is not None:
        _pool.close()
        _pool = None
    if _server is not None:
        _server.cleanup()
        _server = None


def _pool_or_raise() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool not started")
    return _pool


def upsert_lead(name: str, email: str, phone: str, company: str | None) -> None:
    with _pool_or_raise().connection() as conn:
        conn.execute(
            """
            INSERT INTO waitlist (name, email, phone, company)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE
              SET name = EXCLUDED.name,
                  phone = EXCLUDED.phone,
                  company = EXCLUDED.company
            """,
            (name, email, phone, company),
        )


def count() -> int:
    with _pool_or_raise().connection() as conn:
        row = conn.execute("SELECT count(*) FROM waitlist").fetchone()
        return int(row[0]) if row else 0


def insert_many(rows: list[tuple[str, str, str, str | None]]) -> int:
    with _pool_or_raise().connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO waitlist (name, email, phone, company)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                rows,
            )
    return len(rows)
