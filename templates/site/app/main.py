"""@@NAME@@: FastAPI + Jinja2 pages, Tailwind CSS, Font Awesome. Run with:  python cli.py serve"""
from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import api, pages
from .db import connect

HERE = Path(__file__).parent

# No inline scripts, no inline styles, no CDN: every asset is served from this origin.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; "
       "form-action 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")


class Assets(StaticFiles):
    """Vendored files never change under the same name: cache them for a day. Our own CSS/JS are revalidated."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers['Cache-Control'] = 'public, max-age=86400' if path.startswith('vendor/') else 'no-cache'
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    connect().close()   # Create the tables on start.
    yield


app = FastAPI(title='@@NAME@@', docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.mount('/static', Assets(directory=HERE / 'static'), name='static')
app.include_router(pages.router)
app.include_router(api.router)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault('Content-Security-Policy', CSP)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if request.url.path.startswith(('/api/', '/dashboard', '/settings', '/login')):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if request.url.path.startswith('/api/'):
        return JSONResponse({'error': exc.detail}, status_code=exc.status_code)
    if exc.status_code == 404:
        return pages.not_found(request)
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(sqlite3.Error)
async def database_error(_request: Request, _exc: sqlite3.Error):
    return JSONResponse({'error': 'Database unavailable'}, status_code=503)


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return RedirectResponse('/static/icons/favicon.svg', status_code=307)


@app.get('/healthz', response_class=PlainTextResponse, include_in_schema=False)
def healthz():
    return 'ok'
