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

import json
import urllib.request

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "AgriSense")
CONFIRM_BASE_URL = os.getenv("CONFIRM_BASE_URL", "http://127.0.0.1:5000/confirm")

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", SMTP_USER)


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_confirmation_token() -> str:
    return secrets.token_urlsafe(32)


def send_via_brevo_api(to_email: str, first_name: str, token: str) -> bool:
    """Sends verification email using Brevo Transactional Email REST API."""
    link = f"{CONFIRM_BASE_URL}?token={token}"
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {
            "name": SMTP_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL or "noreply@agrisense.lk"
        },
        "to": [
            {
                "email": to_email,
                "name": first_name
            }
        ],
        "subject": "Confirm your AgriSense account",
        "htmlContent": f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f6f8; padding: 20px;">
            <div style="max-width: 550px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
              <h2 style="color: #2e7d32; margin-top: 0;">🌱 Welcome to AgriSense!</h2>
              <p>Hi <strong>{first_name}</strong>,</p>
              <p>Thank you for signing up. Please click the button below to confirm your account and complete your registration:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{link}" style="background-color: #2e7d32; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Confirm Account</a>
              </div>
              <p style="font-size: 13px; color: #666;">Or copy and paste this link in your browser:<br/><a href="{link}" style="color: #2e7d32;">{link}</a></p>
              <p style="font-size: 12px; color: #888; margin-top: 25px;">This link will expire in 24 hours. If you didn't create this account, please ignore this email.</p>
              <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
              <p style="font-size: 12px; color: #999; text-align: center;">— AgriSense / VectaMind Team</p>
            </div>
          </body>
        </html>
        """
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201, 202):
                print(f"[Brevo API] Verification email successfully sent to {to_email}")
                return True
            else:
                print(f"[Brevo API] Non-OK status code: {resp.status}")
                return False
    except Exception as e:
        print(f"[Brevo API] Failed to send email: {e}")
        return False


def send_confirmation_email(to_email: str, first_name: str, token: str) -> bool:
    """
    Sends the confirmation link. Priority:
    1. Brevo REST API (if BREVO_API_KEY starts with 'xkeysib-')
    2. Brevo SMTP Relay (if BREVO_API_KEY starts with 'xsmtpsib-')
    3. Standard SMTP Server (if SMTP_USER and SMTP_PASSWORD set)
    4. Console Log fallback (Dev mode)
    """
    link = f"{CONFIRM_BASE_URL}?token={token}"

    # Priority 1: Brevo REST API (using xkeysib- API Key)
    if BREVO_API_KEY and BREVO_API_KEY.startswith("xkeysib-"):
        return send_via_brevo_api(to_email, first_name, token)

    # Priority 2: Brevo SMTP Relay (using xsmtpsib- SMTP Key)
    if BREVO_API_KEY and BREVO_API_KEY.startswith("xsmtpsib-"):
        smtp_user = BREVO_SENDER_EMAIL or SMTP_USER
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
        msg["From"] = f"{SMTP_SENDER_NAME} <{smtp_user}>"
        msg["To"] = to_email

        try:
            with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
                server.starttls()
                server.login(smtp_user, BREVO_API_KEY)
                server.sendmail(smtp_user, [to_email], msg.as_string())
            print(f"[Brevo SMTP] Verification email sent to {to_email}")
            return True
        except Exception as e:
            print(f"[Brevo SMTP] Failed to send email: {e}")
            print(f"[Email][FALLBACK] Confirmation link for {to_email}: {link}")
            return False

    # Priority 3: Standard SMTP Server
    if SMTP_USER and SMTP_PASSWORD:
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

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, [to_email], msg.as_string())
            print(f"[SMTP Email] Verification email sent to {to_email}")
            return True
        except Exception as e:
            print(f"[SMTP Email] Failed to send confirmation email: {e}")
            print(f"[Email][FALLBACK] Confirmation link for {to_email}: {link}")
            return False

    # Priority 4: Dev Mode
    print("[Email] No Brevo API Key or SMTP credentials configured — skipping email send.")
    print(f"[Email][DEV] Confirmation link for {to_email}: {link}")
    return False


def token_is_expired(token_created_at: datetime, hours: int = 24) -> bool:
    if token_created_at is None:
        return True
    return (datetime.utcnow() - token_created_at).total_seconds() > hours * 3600

