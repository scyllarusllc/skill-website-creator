"""Paths shared by main.py and pages.py (kept apart so the two modules do not import each other)."""
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATES = HERE / 'templates'
