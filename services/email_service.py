from __future__ import annotations

import smtplib

from config import config


def send_email(subject: str, body: str, to_email: str):
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        return False
    try:
        with smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(config.SMTP_USER, to_email, message)
        return True
    except Exception:
        return False
