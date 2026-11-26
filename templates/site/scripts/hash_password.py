"""Print the password hash for .env:   .venv/bin/python scripts/hash_password.py"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.auth import hash_password  # noqa: E402

password = getpass.getpass('New admin password (12+ characters): ')
if password != getpass.getpass('Repeat: '):
    sys.exit('The two passwords differ.')
print('@@ENV@@_ADMIN_PASSWORD_HASH=' + hash_password(password))
