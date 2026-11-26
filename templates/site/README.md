# @@NAME@@

FastAPI + Jinja2 pages, Tailwind CSS v4, Font Awesome Free, Stimulus, SQLite.

## Run

```sh
make install                 # .venv + npm packages
npm run vendor && make css   # first time only: copy Font Awesome/Stimulus, build the CSS
cp .env.example .env && chmod 600 .env
make hash-password           # paste the printed line into .env
make dev                     # http://127.0.0.1:@@PORT@@
```

## Where things are

| What | Where |
|---|---|
| Routes for pages / JSON API | `app/pages.py`, `app/api.py` |
| Page templates, shared header and footer | `app/templates/` (`base.html`, `_header.html`, `_footer.html`) |
| Design system source and compiled CSS | `web/src/app.css` -> `app/static/css/app.css` (committed) |
| Browser scripts | `app/static/js/` (no inline scripts: the CSP forbids them) |
| Auth (password, optional Google), sessions, CSRF | `app/auth.py` |
| SQLite connection and migrations | `app/db.py` |
| Deploy files | `deploy/` |

Deploy: copy `deploy/@@SLUG@@.service` to systemd and `deploy/Caddyfile.snippet` into the Caddyfile.
