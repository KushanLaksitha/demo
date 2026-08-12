"""
Minimal Flask endpoint that the confirmation email link points to.
When a user clicks the link in their inbox, this flips user.is_active = True.

Run separately (e.g. on a small VPS, or locally while testing):
    python database/confirm_server.py
Then set CONFIRM_BASE_URL in .env to point at wherever this is hosted,
e.g. http://your-server-ip:5000/confirm
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request
from database.db_connection import get_session
from database.models import User
from utils.auth_utils import token_is_expired

app = Flask(__name__)

PAGE_OK = """<html><body style="font-family:sans-serif;text-align:center;padding-top:80px;">
<h2 style="color:#4CAF50;">✅ Account confirmed!</h2>
<p>You can now return to the AgriSense app and log in.</p></body></html>"""

PAGE_EXPIRED = """<html><body style="font-family:sans-serif;text-align:center;padding-top:80px;">
<h2 style="color:#E53935;">Link expired</h2>
<p>Please request a new confirmation email from the app's login screen.</p></body></html>"""

PAGE_INVALID = """<html><body style="font-family:sans-serif;text-align:center;padding-top:80px;">
<h2 style="color:#E53935;">Invalid link</h2>
<p>This confirmation link is not valid.</p></body></html>"""


@app.route("/confirm")
def confirm():
    token = request.args.get("token", "")
    db = get_session()
    try:
        user = db.query(User).filter_by(confirmation_token=token).first()
        if not user:
            return PAGE_INVALID, 400
        if user.is_active:
            return PAGE_OK
        if token_is_expired(user.token_created_at):
            return PAGE_EXPIRED, 410
        user.is_active = True
        user.confirmation_token = None
        db.commit()
        return PAGE_OK
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
