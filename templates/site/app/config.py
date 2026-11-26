"""Settings come from the environment, then from .env. Only the named keys are read; .env is never run as shell code."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ('@@ENV@@_ORIGIN', '@@ENV@@_ADMIN_EMAIL', '@@ENV@@_ADMIN_PASSWORD_HASH',
        '@@ENV@@_GOOGLE_CLIENT_ID', '@@ENV@@_GOOGLE_CLIENT_SECRET', '@@ENV@@_DB')


def read_config(path: Path = ROOT / '.env') -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text().splitlines():
            key, sep, value = line.partition('=')
            if sep and key in KEYS:
                values[key] = value.strip()
    for key in KEYS:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


CONFIG = read_config()
ORIGIN = CONFIG.get('@@ENV@@_ORIGIN', 'http://127.0.0.1:@@PORT@@').rstrip('/')
SECURE_COOKIES = ORIGIN.startswith('https://')
DB_PATH = Path(CONFIG.get('@@ENV@@_DB') or ROOT / 'data' / '@@SLUG@@.sqlite3')
ADMIN_EMAIL = CONFIG.get('@@ENV@@_ADMIN_EMAIL', '').strip().lower()
ADMIN_PASSWORD_HASH = CONFIG.get('@@ENV@@_ADMIN_PASSWORD_HASH', '')
GOOGLE_CLIENT_ID = CONFIG.get('@@ENV@@_GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = CONFIG.get('@@ENV@@_GOOGLE_CLIENT_SECRET', '')
GOOGLE_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and ADMIN_EMAIL)
