"""Tiny DB admin CLI for the Aegis waitlist table.

Usage (from the project folder):
    db.bat count                         show number of leads
    db.bat list                          print all leads
    db.bat add "Ada Lovelace" a@b.com "+1 555 123 4567" "ACME"
    db.bat delete a@b.com                delete a lead by email
    db.bat url                           print the live Postgres connection URI
    db.bat psql                          open an interactive psql shell

Or with the venv Python directly:
    .venv\\Scripts\\python.exe -m app.dbcli <command> ...
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from . import db


def _rows():
    with db._pool_or_raise().connection() as conn:
        return conn.execute(
            "SELECT id, name, email, phone, company, created_at "
            "FROM waitlist ORDER BY id"
        ).fetchall()


def cmd_count() -> None:
    print(db.count())


def cmd_list() -> None:
    rows = _rows()
    if not rows:
        print("(empty)")
        return
    print(f"{'ID':>3}  {'NAME':<22} {'EMAIL':<32} {'PHONE':<20} COMPANY")
    print("-" * 110)
    for r in rows:
        cid, name, email, phone, company, _ = r
        print(f"{cid:>3}  {name:<22.22} {email:<32.32} {phone:<20.20} {company or ''}")
    print(f"\n{len(rows)} row(s)")


def cmd_add(argv: list[str]) -> None:
    if len(argv) < 3:
        sys.exit('add needs: "Name" email phone [company]')
    name, email, phone = argv[0], argv[1], argv[2]
    company = argv[3] if len(argv) > 3 else None
    db.upsert_lead(name.strip(), email.strip().lower(), phone.strip(), company)
    print(f"upserted {email.lower()}  (total: {db.count()})")


def cmd_delete(argv: list[str]) -> None:
    if not argv:
        sys.exit("delete needs: email")
    email = argv[0].strip().lower()
    with db._pool_or_raise().connection() as conn:
        cur = conn.execute("DELETE FROM waitlist WHERE email = %s", (email,))
        n = cur.rowcount
    print(f"deleted {n} row(s) for {email}  (total: {db.count()})")


def cmd_psql(srv) -> None:
    bin_dir = pathlib.Path(srv.runtime_path) / "bin"
    psql = bin_dir / ("psql.exe" if sys.platform == "win32" else "psql")
    if not psql.exists():
        sys.exit(f"psql not found at {psql}")
    # pass as a list so paths with spaces are safe (no shell parsing)
    subprocess.run([str(psql), srv.get_uri()])


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd, rest = args[0], args[1:]

    srv = db.start()  # returns URI; also sets up pool + schema
    from . import db as _db  # access the live server object

    try:
        if cmd == "count":
            cmd_count()
        elif cmd == "list":
            cmd_list()
        elif cmd == "add":
            cmd_add(rest)
        elif cmd == "delete":
            cmd_delete(rest)
        elif cmd == "url":
            print(srv)
        elif cmd == "psql":
            cmd_psql(_db._server)
        else:
            print(f"unknown command: {cmd}\n")
            print(__doc__)
    finally:
        db.stop()


if __name__ == "__main__":
    main()
