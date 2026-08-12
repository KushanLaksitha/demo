"""
Auth helpers: bcrypt password hashing + email confirmation link sending.
"""
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

import bcrypt
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "AgriSense")
CONFIRM_BASE_URL = os.getenv("CONFIRM_BASE_URL", "http://127.0.0.1:5000/confirm")


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_confirmation_token() -> str:
    return secrets.token_urlsafe(32)


def send_confirmation_email(to_email: str, first_name: str, token: str) -> bool:
    """
    Sends the confirmation link. Returns True on success, False otherwise
    (the calling screen should show a friendly error but still let the
    user retry from the login screen with a 'Resend confirmation' option).
    """
    link = f"{CONFIRM_BASE_URL}?token={token}"
    body = (
        f"Hi {first_name},\n\n"
        f"Welcome to AgriSense! Please confirm your account by opening this link:\n"
        f"{link}\n\n"
        f"This link expires in 24 hours. If you didn't create this account, "
        f"you can ignore this email.\n\n"
        f"— AgriSense / VectaMind Team"
    )
    msg = MIMEText(body)
    msg["Subject"] = "Confirm your AgriSense account"
    msg["From"] = f"{SMTP_SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = to_email

    if not SMTP_USER or not SMTP_PASSWORD:
        print("[Email] SMTP credentials not configured — skipping send (dev mode).")
        print(f"[Email][DEV] Confirmation link for {to_email}: {link}")
        return False

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] Failed to send confirmation email: {e}")
        print(f"[Email][FALLBACK] Confirmation link for {to_email}: {link}")
        return False


def token_is_expired(token_created_at: datetime, hours: int = 24) -> bool:
    if token_created_at is None:
        return True
    return (datetime.utcnow() - token_created_at).total_seconds() > hours * 3600
