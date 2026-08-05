# Aegis — waitlist landing page + Python backend

A single-stack app: a **FastAPI** server that serves a beautiful landing page,
accepts waitlist signups, stores them in a **local PostgreSQL** database, and
sends a **welcome email** via Gmail. No Docker, no database install, no Node.

- **Frontend:** static HTML + CSS + vanilla JS (animated, dark theme)
- **Backend:** FastAPI + Uvicorn
- **Database:** PostgreSQL, fully local via `pgserver` (bundled binaries) — data in `./pgdata`
- **Email:** Gmail SMTP (stdlib `smtplib`)
- **Seed:** 50 realistic sample leads inserted automatically on first run

---

## 1. Requirements

- **Windows** with **Python 3.10+** installed
  ([download](https://www.python.org/downloads/) — during install tick
  *"Add python.exe to PATH"*).
- Internet on the **first run only** (downloads Python packages + the bundled
  Postgres binaries).

That's it. No PostgreSQL install, no Docker.

---

## 2. Run it (the clickable way)

**Double-click `start.bat`.**

On the first run it will:

1. create a virtual environment (`.venv`)
2. install dependencies (this is the slow part — a few minutes, once)
3. create `.env.local` from the template if missing
4. boot the local Postgres + seed 50 sample leads
5. start the server and open your browser at **http://127.0.0.1:8000**

Every run after that is fast. To stop the server, close the window or press
`Ctrl + C`.

### Run it manually (optional)

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

---

## 3. Sending real emails (Gmail)

The app **runs and saves signups without email configured** — it just skips the
send and shows a warning. To actually send the welcome email:

1. Turn on **2-Step Verification** on the Gmail account.
2. Create an **App Password**: https://myaccount.google.com/apppasswords
3. Put both values in **`.env.local`** (this file is git-ignored — never commit it):

   ```
   GMAIL_USER="youraddress@gmail.com"
   GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"
   ```

4. Restart the server.

The welcome email is sent **from** `GMAIL_USER` **to** whatever address the
visitor types into the form.

---

## 4. The database — access, insert, delete

Postgres runs locally on a random port; data lives in `./pgdata`. You don't
manage it directly — use the **`db.bat`** helper (or `python -m app.dbcli`).

> The server does **not** need to be running to use `db.bat` — it attaches to
> (or boots) the same local cluster.

| Command | What it does |
|---|---|
| `db.bat count` | print number of leads |
| `db.bat list` | print all leads as a table |
| `db.bat add "Ada Lovelace" ada@company.com "+1 555 123 4567" "ACME"` | insert/update a lead (by email) |
| `db.bat delete ada@company.com` | delete a lead by email |
| `db.bat url` | print the live Postgres connection URI |
| `db.bat psql` | open an interactive `psql` shell |

### Examples

```bat
db.bat list
db.bat add "Grace Hopper" grace@navy.mil "+1 202 555 0100" "US Navy"
db.bat delete grace@navy.mil
db.bat count
```

### Raw SQL in the psql shell

```bat
db.bat psql
```
```sql
SELECT id, name, email, phone FROM waitlist ORDER BY id;
INSERT INTO waitlist (name, email, phone, company)
  VALUES ('Alan Turing', 'alan@bletchley.uk', '+44 20 7946 0000', 'GC&CS');
DELETE FROM waitlist WHERE email = 'alan@bletchley.uk';
\q
```

### Connect with an external GUI (DBeaver, TablePlus, pgAdmin)

Run `db.bat url` to get the connection string, then paste it into your client.
Note the port changes each time Postgres restarts — re-run `db.bat url` after a
restart.

### Re-seed / reset

Delete the `pgdata` folder and start again — the app recreates the schema and
re-inserts the 50 sample leads.

---

## 5. Running on another system

1. Copy the project folder (or `git clone` the repo) — you do **not** need to
   copy `.venv` or `pgdata`; they're rebuilt locally.
2. Make sure Python 3.10+ is installed.
3. Double-click **`start.bat`**.
4. (Optional) edit `.env.local` with that machine's Gmail App Password to enable
   email.

Everything else — virtual env, dependencies, Postgres binaries, database,
seed data — is created automatically on that machine.

---

## 6. Project layout

```
modern-auth-web/
├─ start.bat            # one-click: setup + run + open browser
├─ db.bat               # DB admin helper (count/list/add/delete/url/psql)
├─ requirements.txt
├─ .env.example         # template (committed)
├─ .env.local           # your Gmail secrets (git-ignored)
├─ app/
│  ├─ main.py           # FastAPI app, routes, startup lifecycle
│  ├─ db.py             # pgserver boot + psycopg pool + queries
│  ├─ emailer.py        # Gmail welcome email (smtplib)
│  ├─ seed.py           # 50 sample leads (auto on first run)
│  └─ dbcli.py          # DB admin CLI (used by db.bat)
├─ static/
│  ├─ index.html        # landing page
│  ├─ styles.css
│  └─ app.js            # form submit + validation + toasts
└─ pgdata/              # local Postgres data (git-ignored, auto-created)
```

---

## 7. API

| Method | Path | Body | Result |
|---|---|---|---|
| `GET` | `/` | — | landing page |
| `GET` | `/api/health` | — | `{ "ok": true, "leads": <count> }` |
| `POST` | `/api/subscribe` | `{name, email, phone, company?}` | saves lead + sends welcome email |
