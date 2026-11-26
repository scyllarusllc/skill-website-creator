# Stack reference

Learned from `~/github/inboxtend` (Inbox Tend), the reference implementation, and refined in the ProxySpring site.

## Versions the scaffold pins

| Package | Version | Where |
|---|---|---|
| Python | 3.11+ (tested on 3.14) | system `python3`, venv in `.venv` |
| fastapi / uvicorn / jinja2 / typer / watchfiles | `>=` ranges in `requirements.txt` | pip |
| tailwindcss + @tailwindcss/cli | 4.3.5 | npm (build time only) |
| @fortawesome/fontawesome-free | 7.3.1 | npm -> copied to `app/static/vendor/fontawesome` |
| @hotwired/stimulus | 3.2.2 | npm -> copied to `app/static/vendor/stimulus` |

Inboxtend also uses sqlmodel (ORM mappings over its existing SQLite tables), Pillow, bleach (HTML sanitizing) and cryptography
(encrypting stored OAuth refresh tokens). Add them only when the product needs them.

## Layout of a generated site

```
app/
  main.py        FastAPI app, security-headers middleware (CSP), static mount, error handlers, /healthz
  pages.py       HTML routes + NAV list + render() helper (one place decides title, nav, signed-in state)
  api.py         JSON API, whitelist-validated settings, Google sign-in redirects
  auth.py        password hashing (scrypt), sessions, CSRF, throttling
  db.py          sqlite connect(), SCHEMA, ADDITIONS (additive migrations), get_db dependency
  config.py      .env + environment, named keys only
  templates/     base.html, _header.html, _footer.html, one template per page
  static/css/app.css        compiled Tailwind (committed)
  static/js/                common.js (helpers), per-page scripts, stimulus-app.js
  static/vendor/            Font Awesome + Stimulus copies (committed)
web/src/app.css  design system source (Tailwind @theme, base layer, components)
scripts/         vendor-assets.mjs, hash_password.py
deploy/          systemd unit, Caddyfile snippet
cli.py           `python cli.py serve --port N [--reload]`
Makefile         install, dev, run, css, css-watch, vendor, hash-password
```

## Commands

```sh
make install            # .venv + pip + npm
npm run vendor          # copy Font Awesome/Stimulus (after changing a version)
make css                # compile Tailwind; commit app/static/css/app.css
make dev                # uvicorn --reload on 127.0.0.1:<port>
```

## Where each idea came from in inboxtend

| Idea | Source |
|---|---|
| Design system rules, class conventions | `docs/frontend.md`, `static/src/app.css` (header comment + base layer) |
| Shared header/footer layout | `static/layout.html`, `app.py: render_page` (string markers); the skill uses Jinja2 includes instead |
| Vendored assets, committed so no Node at runtime | `scripts/vendor-assets.mjs` |
| `el()/request()/icon()` helpers, CSRF header | `static/common.js` |
| Stimulus toast controller | `static/stimulus-app.js` |
| Auth, sessions, throttling | `auth.py` |
| SQLite connect + additive migrations + WAL | `tasks.py: connection()` |
| Strict CSP and security headers | `asgi.py: RequestAdapter._send` |
| Whitelist-validated per-user settings | `settings.py` |
| Google sign-in (state cookie, verified email) | `google_login.py` |
| systemd + Caddy deploy | `deploy/systemd/*.service`, `deploy/Caddyfile.local` |

## Deliberate differences from inboxtend

- Inboxtend wraps a legacy `http.server` handler in a catch-all FastAPI route (`asgi.py: RequestAdapter`). That is a migration
  scaffold, not a pattern: new sites use native FastAPI routers and dependencies.
- Inboxtend composes pages with `{{MARKER}}` string replacement in `app.py`; the skill uses Jinja2 (`{% include %}`, blocks).
- Inboxtend's scripts are plain globals loaded per page; the skill keeps that (no bundler) but names events `site:*`.
