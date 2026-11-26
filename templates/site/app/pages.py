"""HTML pages. A page is a Jinja2 template that extends base.html; add one route and one template per page."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import config
from .auth import current_session, safe_next
from .main_paths import TEMPLATES

templates = Jinja2Templates(directory=TEMPLATES)
router = APIRouter()

# (href, label, Font Awesome icon, needs sign-in). The header lists these; the active one is highlighted.
NAV = [
    ('/', 'Home', 'fa-house', False),
    ('/dashboard', 'Dashboard', 'fa-gauge', True),
    ('/settings', 'Settings', 'fa-gear', True),
    ('/privacy', 'Privacy', 'fa-shield-halved', False),
]


def render(request: Request, name: str, title: str, session: dict | None, status: int = 200, **context):
    path = request.url.path.rstrip('/') or '/'
    nav = [item for item in NAV if session or not item[3]]
    return templates.TemplateResponse(request, name, {
        'title': f'{title} · @@NAME@@' if title else '@@NAME@@', 'path': path, 'nav': nav, 'signed_in': bool(session),
        'google_enabled': config.GOOGLE_ENABLED, 'password_enabled': bool(config.ADMIN_PASSWORD_HASH), **context}, status_code=status)


def not_found(request: Request) -> HTMLResponse:
    return render(request, 'not_found.html', 'Not found', None, 404)


@router.get('/', response_class=HTMLResponse)
def home(request: Request, session: dict | None = Depends(current_session)):
    return render(request, 'home.html', '', session)


@router.get('/privacy', response_class=HTMLResponse)
def privacy(request: Request, session: dict | None = Depends(current_session)):
    return render(request, 'privacy.html', 'Privacy', session)


@router.get('/login', response_class=HTMLResponse)
def login(request: Request, session: dict | None = Depends(current_session), next: str | None = None):
    if session:
        return RedirectResponse(safe_next(next), status_code=303)
    return render(request, 'login.html', 'Sign in', None)


@router.get('/dashboard', response_class=HTMLResponse)
def dashboard(request: Request, session: dict | None = Depends(current_session)):
    if not session:
        return RedirectResponse('/login?next=/dashboard', status_code=303)
    return render(request, 'dashboard.html', 'Dashboard', session, email=session['email'])


@router.get('/settings', response_class=HTMLResponse)
def settings(request: Request, session: dict | None = Depends(current_session)):
    if not session:
        return RedirectResponse('/login?next=/settings', status_code=303)
    return render(request, 'settings.html', 'Settings', session)
