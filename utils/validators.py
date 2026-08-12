"""
Validation helpers for registration: email format, email-already-used
check, and password strength scoring.
"""
import re

from database.db_connection import get_session
from database.models import User

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Password rule: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
PW_MIN_LEN = 8
PW_UPPER = re.compile(r"[A-Z]")
PW_LOWER = re.compile(r"[a-z]")
PW_DIGIT = re.compile(r"\d")
PW_SPECIAL = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:,.<>/?]")


def is_valid_email_format(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def email_already_registered(email: str) -> bool:
    db = get_session()
    try:
        return db.query(User).filter_by(email=email.strip().lower()).first() is not None
    except Exception as e:
        print(f"[Validators] email_already_registered check failed: {e}")
        return False  # fail open here — final safety net is the DB unique constraint on save
    finally:
        db.close()


def check_password_strength(password: str):
    """
    Returns (score 0-5, label, hex_color, list_of_missing_rules).
    Used both to block weak passwords and to drive a live strength bar in the UI.
    """
    rules = {
        f"At least {PW_MIN_LEN} characters": len(password) >= PW_MIN_LEN,
        "An uppercase letter (A-Z)": bool(PW_UPPER.search(password)),
        "A lowercase letter (a-z)": bool(PW_LOWER.search(password)),
        "A number (0-9)": bool(PW_DIGIT.search(password)),
        "A special character (!@#$...)": bool(PW_SPECIAL.search(password)),
    }
    score = sum(1 for ok in rules.values() if ok)
    missing = [rule for rule, ok in rules.items() if not ok]

    if not password:
        return 0, "", "#E0E0E0", missing
    if score <= 2:
        return score, "Weak", "#E53935", missing
    if score in (3, 4):
        return score, "Medium", "#FB8C00", missing
    return score, "Strong", "#43A047", missing


def is_password_acceptable(password: str) -> bool:
    score, _, _, _ = check_password_strength(password)
    return score >= 4   # require at least 4 of the 5 rules
