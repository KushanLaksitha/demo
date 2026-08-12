"""
Registration & login logic — wraps User table access + email confirmation flow.
"""
from datetime import datetime
from database.db_connection import get_session
from database.models import User, Region
from utils.auth_utils import (
    hash_password, verify_password, generate_confirmation_token,
    send_confirmation_email, token_is_expired
)

ROLES = ["farmer", "trader", "policymaker"]


def register_user(email, password, first_name, last_name, user_type, region_id, crop_ids=None):
    db = get_session()
    try:
        if user_type not in ROLES:
            return False, "Invalid role selected."
        existing = db.query(User).filter_by(email=email.strip().lower()).first()
        if existing:
            return False, "An account with this email already exists."

        token = generate_confirmation_token()
        user = User(
            email=email.strip().lower(),
            password=hash_password(password),
            user_type=user_type,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            region_id=region_id,
            is_active=False,
            confirmation_token=token,
            token_created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()

        if crop_ids:
            from database.models import UserPreferences
            db.add(UserPreferences(user_id=user.user_id,
                                     preferred_crops=",".join(str(c) for c in crop_ids)))
            db.commit()

        sent = send_confirmation_email(user.email, user.first_name, token)
        if sent:
            return True, "Registered! Please check your email to confirm your account."
        return True, "Registered! (Email service not configured — check the app log for your confirmation link.)"
    except Exception as e:
        db.rollback()
        return False, f"Registration failed: {e}"
    finally:
        db.close()


def resend_confirmation(email):
    db = get_session()
    try:
        user = db.query(User).filter_by(email=email.strip().lower()).first()
        if not user:
            return False, "No account found with that email."
        if user.is_active:
            return False, "This account is already confirmed — please log in."
        token = generate_confirmation_token()
        user.confirmation_token = token
        user.token_created_at = datetime.utcnow()
        db.commit()
        send_confirmation_email(user.email, user.first_name, token)
        return True, "Confirmation email resent — please check your inbox."
    except Exception as e:
        db.rollback()
        return False, "Can't reach the database right now. Please make sure MySQL is running."
    finally:
        db.close()


def login_user(email, password):
    """Returns (success, message_or_userdict)."""
    db = get_session()
    try:
        user = db.query(User).filter_by(email=email.strip().lower()).first()
        if not user or not verify_password(password, user.password):
            return False, "Incorrect email or password."
        if not user.is_active:
            return False, "Please confirm your email before logging in."
        region = db.query(Region).filter_by(region_id=user.region_id).first() if user.region_id else None
        return True, {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "region_id": user.region_id,
            "region_name": region.region_name if region else None,
            "district": region.district if region else None,
        }
    except Exception as e:
        print(f"[Auth] login_user failed: {e}")
        return False, "Can't reach the database right now. Please make sure MySQL is running and try again."
    finally:
        db.close()
