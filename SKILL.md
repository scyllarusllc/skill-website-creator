---
name: website-creator
description: Create or extend a website in the house stack learned from the Inbox Tend project - FastAPI + Jinja2 pages, Tailwind CSS v4 (precompiled), self-hosted Font Awesome Free and Stimulus, vanilla-JS helpers, SQLite, strict CSP, single-admin auth with password and optional Google sign-in, systemd + Caddy deploy. Use whenever the user asks to start a new website/web app/landing page/admin tool, to add a page, login, settings page or API endpoint to one built this way, or to deploy one behind Caddy (including Cloudflare).
---

# website-creator

Builds sites the way Inbox Tend (`~/github/inboxtend`) is built, minus its historical baggage. The scaffold in
`templates/site/` is a working site (home, privacy, login, dashboard, settings, 404) that was run end to end:
password login, CSRF, whitelist-validated settings, strict CSP, sliding sessions.

## The stack, in one table

| Layer | Choice | Why |
|---|---|---|
| Server | FastAPI, sync endpoints, uvicorn bound to `127.0.0.1` | Simple, typed, threadpool for blocking SQLite |
| Pages | Jinja2 templates; `base.html` + `_header.html` + `_footer.html` shared by every page | One header/footer, per-page content blocks |
| Styling | Tailwind CSS v4 **compiled ahead of time** to `app/static/css/app.css` (committed) | Strict CSP: no inline styles, no CDN, no in-browser build |
| Icons | Font Awesome Free, **self-hosted** copy in `app/static/vendor/` (committed) | Same reason; no third-party request |
| Behaviour | Vanilla JS (`el()`, `request()`, `notify()`, `icon()`) + Stimulus controllers | No bundler, no framework |
| Data | SQLite, WAL, one connection per request, additive migrations | One file to back up |
| Auth | One admin: scrypt password and/or Google; sessions hashed in SQLite, sliding 7d idle / 30d max; CSRF header | Small attack surface |
| Deploy | systemd unit + Caddy `reverse_proxy` (Cloudflare in front is fine) | Automatic HTTPS |

Details: `references/stack.md` (versions, layout, commands), `references/design-system.md`, `references/backend-patterns.md`,
`references/frontend-patterns.md`, `references/deploy.md`, `references/gotchas.md`.

## Workflow

1. **Clarify only what you cannot default**: display name, domain (or "local only"), pages needed, whether anyone besides one
   admin signs in (the scaffold is single-admin; see backend-patterns.md before adding users), whether Google sign-in is wanted.
   Pick the port yourself: look at `ss -ltn` and the Caddyfile and choose an unused one in 8100-8199.
2. **Scaffold**
   ```sh
   python3 ~/github/skill-website-creator/scripts/scaffold.py ~/github/<slug> --name "<Display Name>" --port <port> --install --git
   ```
   It refuses a non-empty target. `--install` makes `.venv`, runs `npm install`, copies vendor assets and builds the CSS.
3. **Configure**: `cp .env.example .env && chmod 600 .env`, `make hash-password`, put the printed line in `.env`, set
   `<ENV>_ADMIN_EMAIL` and `<ENV>_ORIGIN` (https URL in production: it switches on Secure cookies).
4. **Build the product** inside the conventions below. Add a page = route in `app/pages.py` + template extending `base.html` +
   (if signed-in) an entry in `NAV`. Add an endpoint = router function in `app/api.py` with `Depends(require_csrf)` for writes.
5. **Rebuild CSS after every template or script change that adds classes**: `make css` (or leave `make css-watch` running).
   Commit `app/static/css/app.css`.
6. **Run and verify with curl before saying it works**: pages 200, protected pages 303 to `/login`, login, a write with and
   without the CSRF header (403 without), the CSP header, a 404. Check `server.log`/journal for tracebacks.
7. **Deploy** (only when asked, it is outward-facing): `references/deploy.md`. Back up the Caddyfile first, `caddy validate`
   before `reload`, then curl the public URL.

## Non-negotiable conventions

- **No inline `<script>`, `style="..."`, or `on*=` attributes, and no CDN.** The CSP is `default-src 'self'` and will silently
  drop them. Put scripts in `app/static/js/`, styles in `web/src/app.css`.
- **Build DOM from data with `textContent`** (`el(tag, text, cls)`); never `innerHTML` with anything that came from a user, a
  database row or an email. Untrusted HTML goes through a server-side sanitizer and into a sandboxed iframe.
- **Every state-changing endpoint** depends on `require_csrf`; JSON endpoints return `{"error": "..."}`; the browser helper
  `request()` sends the CSRF header and sends the person to `/login` on 401.
- **Whitelist validation** for anything a client can set (see `SETTINGS` in `app/api.py`): unknown keys are 400, values are
  range/enum checked, everything is validated before anything is written.
- **One look**: every button/input/select/textarea is styled in the Tailwind *base layer*; variants only recolour
  (`.action` main action, `.danger` destructive); one card `.panel`, one badge `.badge`. Do not sprinkle ad-hoc colours.
- **Icons** are Font Awesome classes in templates, or `icon('name')` from the `ICONS` map in `common.js`.
- **Secrets** live in `.env` (mode 600, git-ignored), read by name only. Never print a secret into the conversation; when
  told to use a credentials file, read it by script and write it straight into `.env`.
- **Do not add test files** unless the user asks for them.

## Extending beyond the scaffold

- More users or roles, per-user data: `references/backend-patterns.md` ("From one admin to many users").
- Background work (sync loops, jobs): start it in `lifespan`, keep state in SQLite, log with `logging.getLogger('<slug>.<area>')`.
- Calling slow third-party APIs from a request: set a total time budget and fail fast with a clear message instead of sleeping
  through retries; let background jobs be patient. Cache access tokens until shortly before they expire.
- A next.js shell, extension, or other client is optional and separate; the FastAPI JSON API stays the contract.

When in doubt about how something was done originally, read the source it came from (paths in `references/stack.md`).
