"""JSON API (/api/...) and the Google sign-in redirects (/auth/google/...).

Pattern for a new endpoint:
    @router.patch('/things/{id}')
    def update(id: int, body: ThingIn, session=Depends(require_csrf), db=Depends(get_db)): ...
Validate with a whitelist (see SETTINGS below), never trust the client's field names or ranges.
"""
from __future__ import annotations

import json
import secrets
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request as HttpRequest, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from . import auth, config
from .auth import current_session, require_csrf, require_user
from .db import get_db

router = APIRouter()


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=1024)


@router.get('/api/session')
def session_info(session: dict = Depends(require_user)):
    return {'csrf_token': session['csrf_token'], 'user': {'email': session['email']}}


@router.get('/api/auth/providers')
def providers():
    return {'password': bool(config.ADMIN_PASSWORD_HASH), 'google': config.GOOGLE_ENABLED}


@router.post('/api/auth/login')
def login(body: LoginIn, request: Request, response: Response, db=Depends(get_db)):
    if auth.throttled():
        raise HTTPException(429, 'Too many failed attempts. Wait 15 minutes and try again.')
    if not auth.check_password_login(body.email, body.password):
        auth.record_failure()
        raise HTTPException(401, 'Wrong email or password.')
    auth.start_session(db, request, response, config.ADMIN_EMAIL)
    return {'ok': True}


@router.post('/api/auth/logout')
def logout(request: Request, response: Response, db=Depends(get_db), _session: dict = Depends(require_csrf)):
    auth.end_session(db, request, response)
    return {'ok': True}


# --------------------------------------------------------------------------- settings (whitelist pattern)
# key -> (default, validator that returns the cleaned value or raises ValueError)
def _short_text(value):
    if not isinstance(value, str) or len(value.strip()) > 60:
        raise ValueError('Must be text of at most 60 characters')
    return value.strip()


SETTINGS = {'display_name': ('', _short_text)}


def stored_settings(db) -> dict:
    values = {key: default for key, (default, _check) in SETTINGS.items()}
    for row in db.execute('SELECT key,value FROM settings'):
        if row['key'] in SETTINGS:
            try:
                values[row['key']] = SETTINGS[row['key']][1](json.loads(row['value']))
            except (ValueError, TypeError):
                pass   # An invalid leftover falls back to the default.
    return values


@router.get('/api/settings')
def get_settings(_session: dict = Depends(require_user), db=Depends(get_db)):
    return {'settings': stored_settings(db)}


@router.patch('/api/settings')
def patch_settings(changes: dict, _session: dict = Depends(require_csrf), db=Depends(get_db)):
    if not changes:
        raise HTTPException(400, 'No settings to save')
    cleaned = {}
    for key, value in changes.items():   # Validate everything before writing anything.
        if key not in SETTINGS:
            raise HTTPException(400, f'Unknown setting: {key}')
        try:
            cleaned[key] = SETTINGS[key][1](value)
        except ValueError as exc:
            raise HTTPException(400, f'{key}: {exc}') from None
    now = int(time.time())
    with db:
        for key, value in cleaned.items():
            db.execute('INSERT INTO settings(key,value,updated_at) VALUES (?,?,?) '
                       'ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (key, json.dumps(value), now))
    return {'settings': stored_settings(db)}


# --------------------------------------------------------------------------- Google sign-in
def _login_error(response: RedirectResponse, code: str = 'google') -> RedirectResponse:
    response.headers['location'] = f'/login?error={code}'
    response.delete_cookie(auth.GOOGLE_STATE_COOKIE, path='/')
    return response


@router.get('/auth/google/start')
def google_start(next: str | None = None):
    if not config.GOOGLE_ENABLED:
        return RedirectResponse('/login?error=google', status_code=303)
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(auth.google_url(state), status_code=303)
    # The state and the page to return to travel in one short-lived cookie.
    response.set_cookie(auth.GOOGLE_STATE_COOKIE, f'{state}|{auth.safe_next(next)}', max_age=600, httponly=True,
                        samesite='lax', secure=config.SECURE_COOKIES, path='/')
    return response


@router.get('/auth/google/callback')
def google_callback(request: Request, code: str = '', state: str = '', db=Depends(get_db)):
    response = RedirectResponse('/dashboard', status_code=303)
    saved, _, destination = request.cookies.get(auth.GOOGLE_STATE_COOKIE, '').partition('|')
    if not config.GOOGLE_ENABLED or not saved or not code or not secrets.compare_digest(saved, state):
        return _login_error(response)
    try:
        token_request = HttpRequest('https://oauth2.googleapis.com/token', method='POST', data=urlencode({
            'code': code, 'client_id': config.GOOGLE_CLIENT_ID, 'client_secret': config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': config.ORIGIN + '/auth/google/callback', 'grant_type': 'authorization_code'}).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        with urlopen(token_request, timeout=10) as reply:
            access = json.load(reply).get('access_token')
        profile_request = HttpRequest('https://openidconnect.googleapis.com/v1/userinfo', headers={'Authorization': f'Bearer {access}'})
        with urlopen(profile_request, timeout=10) as reply:
            profile = json.load(reply)
    except (URLError, OSError, ValueError, TypeError):
        return _login_error(response)
    # Only the administrator's verified Google address may sign in.
    if profile.get('email_verified') is not True or str(profile.get('email', '')).lower() != config.ADMIN_EMAIL:
        return _login_error(response, 'google-denied')
    auth.start_session(db, request, response, config.ADMIN_EMAIL)
    response.headers['location'] = auth.safe_next(destination)
    response.delete_cookie(auth.GOOGLE_STATE_COOKIE, path='/')
    return response
