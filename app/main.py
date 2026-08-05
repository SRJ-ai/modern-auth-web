from __future__ import annotations

import logging
import pathlib
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, field_validator

# load secrets before anything reads the environment
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env.local")

from . import db, emailer, seed  # noqa: E402

log = logging.getLogger("aegis")
STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    uri = db.start()
    log.info("Postgres up: %s", uri)
    n = seed.seed_if_empty()
    if n:
        log.info("seeded %d sample leads", n)
    yield
    db.stop()


app = FastAPI(title="Aegis", lifespan=lifespan)


class Lead(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str | None = ""

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not (2 <= len(v) <= 80):
            raise ValueError("Name must be 2-80 characters")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = v.strip()
        digits = sum(c.isdigit() for c in v)
        if not (7 <= len(v) <= 20) or digits < 7:
            raise ValueError("Enter a valid phone number")
        if not all(c.isdigit() or c in " +-()." for c in v):
            raise ValueError("Phone has invalid characters")
        return v

    @field_validator("company")
    @classmethod
    def _company(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


@app.post("/api/subscribe")
def subscribe(lead: Lead):
    # 1) persist (idempotent on email)
    try:
        db.upsert_lead(lead.name, str(lead.email), lead.phone, lead.company)
    except Exception:  # noqa: BLE001
        log.exception("db insert failed")
        return JSONResponse(
            {"error": "Could not save your details. Try again later."},
            status_code=500,
        )

    # 2) welcome email (row already saved either way)
    try:
        emailer.send_welcome(lead.name, str(lead.email))
    except emailer.EmailNotConfigured:
        return {"ok": True, "warning": "Saved you, but email is not configured yet."}
    except Exception:  # noqa: BLE001
        log.exception("email send failed")
        return {"ok": True, "warning": "Saved you, but the welcome email failed."}

    return {"ok": True}


@app.get("/api/health")
def health():
    return {"ok": True, "leads": db.count()}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
