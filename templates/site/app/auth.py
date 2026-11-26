"""One administrator. Password (scrypt) and optional Google sign-in. Sessions live in SQLite, only as hashes.

Sessions slide: each use pushes the expiry forward (at most once an hour) up to a hard limit from sign-in.
Every state-changing request must carry the session's CSRF token in the X-CSRF-Token header.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
import time
from collections import deque
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Request, Response

from . import config
from .db import get_db

COOKIE = '@@SLUG@@_session'
IDLE_SECONDS = 7 * 86400     # Signed out after this long without use.
MAX_SECONDS = 30 * 86400     # Hard limit from sign-in, however active.
RENEW_AFTER = 3600           # Extend at most once an hour so reads do not write on every request.
_TOKEN = re.compile(r'^[A-Za-z0-9_-]{40,100}$')
_SAFE_NEXT = re.compile(r'^/(?!/)[A-Za-z0-9/_?=&.%:-]*$')

_failures: deque[float] = deque()
_failures_lock = threading.Lock()


# --------------------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 1024:
        raise ValueError('Password must be 12-1024 characters')
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=32)
    return f'scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}'


def verify_password(password: str, stored: str) -> bool:
    try:
        kind, salt, expected = stored.split('$')
        if kind != 'scrypt':
            return False
        salt_b, expected_b = base64.urlsafe_b64decode(salt), base64.urlsafe_b64decode(expected)
        actual = hashlib.scrypt(password.encode(), salt=salt_b, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=len(expected_b))
        return hmac.compare_digest(actual, expected_b)
    except (ValueError, TypeError, UnicodeError):
        return False


# --------------------------------------------------------------------------- sessions
def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def throttled() -> bool:
    now = time.monotonic()
    with _failures_lock:
        while _failures and _failures[0] < now - 900:
            _failures.popleft()
        return len(_failures) >= 10


def record_failure() -> None:
    with _failures_lock:
        _failures.append(time.monotonic())


def check_password_login(email: str, password: str) -> bool:
    """Always runs the hash, so timing does not reveal whether the email matched."""
    stored = config.ADMIN_PASSWORD_HASH or 'scrypt$AAAAAAAAAAAAAAAAAAAAAA==$' + base64.urlsafe_b64encode(bytes(32)).decode()
    password_ok = verify_password(password, stored) and bool(config.ADMIN_PASSWORD_HASH)
    email_ok = bool(config.ADMIN_EMAIL) and hmac.compare_digest(email.strip().lower().encode(), config.ADMIN_EMAIL.encode())
    return password_ok and email_ok


def start_session(db: sqlite3.Connection, request: Request, response: Response, email: str) -> None:
    old = request.cookies.get(COOKIE)
    now = int(time.time())
    token = secrets.token_urlsafe(32)
    with db:
        if old and _TOKEN.fullmatch(old):
            db.execute('DELETE FROM sessions WHERE token_hash=?', (_digest(old),))
        db.execute('DELETE FROM sessions WHERE expires_at<=?', (now,))
        db.execute('INSERT INTO sessions(token_hash,csrf_token,email,expires_at,created_at) VALUES (?,?,?,?,?)',
                   (_digest(token), secrets.token_urlsafe(32), email, now + IDLE_SECONDS, now))
    response.set_cookie(COOKIE, token, max_age=MAX_SECONDS, httponly=True, samesite='lax', secure=config.SECURE_COOKIES, path='/')


def end_session(db: sqlite3.Connection, request: Request, response: Response) -> None:
    token = request.cookies.get(COOKIE)
    if token and _TOKEN.fullmatch(token):
        with db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (_digest(token),))
    response.delete_cookie(COOKIE, path='/')


def current_session(request: Request, db: sqlite3.Connection = Depends(get_db)) -> dict | None:
    token = request.cookies.get(COOKIE)
    if not token or not _TOKEN.fullmatch(token):
        return None
    row = db.execute('SELECT * FROM sessions WHERE token_hash=?', (_digest(token),)).fetchone()
    now = int(time.time())
    if not row or row['expires_at'] <= now or now >= row['created_at'] + MAX_SECONDS:
        return None
    wanted = min(now + IDLE_SECONDS, row['created_at'] + MAX_SECONDS)
    if wanted - row['expires_at'] >= RENEW_AFTER:
        with db:
            db.execute('UPDATE sessions SET expires_at=? WHERE token_hash=?', (wanted, _digest(token)))
    return {'email': row['email'], 'csrf_token': row['csrf_token']}


def require_user(session: dict | None = Depends(current_session)) -> dict:
    """For JSON endpoints: 401 when signed out (the browser script sends the person to /login)."""
    if not session:
        raise HTTPException(401, 'Sign in required')
    return session


def require_csrf(request: Request, session: dict = Depends(require_user)) -> dict:
    """For POST/PATCH/DELETE endpoints: signed in AND the right CSRF header."""
    sent = request.headers.get('x-csrf-token', '')
    if not hmac.compare_digest(sent.encode(), session['csrf_token'].encode()):
        raise HTTPException(403, 'Invalid CSRF token. Reload the page and try again.')
    return session


def safe_next(value: str | None, default: str = '/dashboard') -> str:
    return value if value and _SAFE_NEXT.fullmatch(value) else default


# --------------------------------------------------------------------------- Google sign-in (optional)
GOOGLE_STATE_COOKIE = '@@SLUG@@_gstate'


def google_url(state: str) -> str:
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id': config.GOOGLE_CLIENT_ID, 'redirect_uri': config.ORIGIN + '/auth/google/callback',
        'response_type': 'code', 'scope': 'openid email', 'state': state, 'prompt': 'select_account'})
