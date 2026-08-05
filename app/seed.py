"""Seed 50 realistic sample leads (name / email / phone / company).
Runs automatically on startup only when the table is empty. Deterministic."""
from __future__ import annotations

from faker import Faker

from . import db

COUNT = 50


def build_rows() -> list[tuple[str, str, str, str | None]]:
    fake = Faker()
    Faker.seed(2026)
    rows: list[tuple[str, str, str, str | None]] = []
    seen: set[str] = set()
    while len(rows) < COUNT:
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first}.{last}@{fake.free_email_domain()}".lower()
        if email in seen:
            continue
        seen.add(email)
        rows.append(
            (f"{first} {last}", email, fake.phone_number(), fake.company())
        )
    return rows


def seed_if_empty() -> int:
    if db.count() > 0:
        return 0
    rows = build_rows()
    db.insert_many(rows)
    return len(rows)


if __name__ == "__main__":
    db.start()
    try:
        n = seed_if_empty()
        print(f"seeded {n} rows (table total: {db.count()})")
    finally:
        db.stop()
