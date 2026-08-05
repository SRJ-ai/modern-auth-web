"""Gmail welcome email via stdlib smtplib (SMTP over SSL, port 465).
Requires GMAIL_USER + GMAIL_APP_PASSWORD in the environment (.env.local)."""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from html import escape


class EmailNotConfigured(RuntimeError):
    pass


def send_welcome(name: str, email: str) -> None:
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not password:
        raise EmailNotConfigured("GMAIL_USER / GMAIL_APP_PASSWORD not set")

    first = name.split(" ")[0] or name

    msg = EmailMessage()
    msg["From"] = f"Aegis <{user}>"
    msg["To"] = email
    msg["Subject"] = "You're on the Aegis waitlist \U0001F510"
    msg.set_content(
        f"Hi {first}, you're on the Aegis waitlist. "
        "We'll email you the moment your invite is ready."
    )
    msg.add_alternative(_html(first), subtype="html")

    _send(msg, user, password)


def _send(msg: EmailMessage, user: str, password: str) -> None:
    """Send via Gmail, resilient to transient drops:
    try SSL:465 then STARTTLS:587, each retried once."""
    context = ssl.create_default_context()
    attempts = [("ssl", 465), ("starttls", 587), ("ssl", 465), ("starttls", 587)]
    last: Exception | None = None

    for mode, port in attempts:
        try:
            if mode == "ssl":
                with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context, timeout=25) as smtp:
                    smtp.login(user, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP("smtp.gmail.com", port, timeout=25) as smtp:
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                    smtp.login(user, password)
                    smtp.send_message(msg)
            return
        except smtplib.SMTPAuthenticationError:
            raise  # bad creds — retrying won't help
        except Exception as exc:  # noqa: BLE001 — transient network/disconnect
            last = exc

    raise RuntimeError(f"SMTP send failed after retries: {last}")


def _html(first: str) -> str:
    first = escape(first)
    return f"""<!doctype html>
<html><body style="margin:0;background:#0d0b1a;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0d0b1a;padding:32px 0;">
    <tr><td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0"
        style="max-width:480px;width:100%;background:#15122a;border:1px solid rgba(255,255,255,.08);border-radius:20px;overflow:hidden;">
        <tr><td style="height:6px;background:linear-gradient(90deg,#7c5cff,#4f7cff 50%,#e05cff);"></td></tr>
        <tr><td style="padding:40px 40px 8px;">
          <div style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-.02em;">Aegis</div>
        </td></tr>
        <tr><td style="padding:16px 40px 8px;">
          <h1 style="margin:0 0 12px;font-size:26px;line-height:1.25;color:#fff;letter-spacing:-.02em;">
            You're on the list, {first}.
          </h1>
          <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#b9b4d0;">
            Thanks for joining the Aegis waitlist. We're building auth that gets out of
            your way &mdash; passkeys, passwordless, and adaptive MFA in a few lines of code.
          </p>
          <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#b9b4d0;">
            We'll email you the moment your invite is ready. No spam, promise.
          </p>
          <a href="https://aegis.example.com"
            style="display:inline-block;background:linear-gradient(90deg,#7c5cff,#4f7cff);color:#fff;
            text-decoration:none;font-size:14px;font-weight:600;padding:12px 22px;border-radius:12px;">
            Read the docs
          </a>
        </td></tr>
        <tr><td style="padding:32px 40px 40px;">
          <hr style="border:none;border-top:1px solid rgba(255,255,255,.08);margin:0 0 16px;" />
          <p style="margin:0;font-size:12px;color:#6f6a86;">
            You received this because you signed up at aegis.example.com.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
