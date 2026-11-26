# Backend patterns

All of these exist, working, in `templates/site/app/`.

## Request handling

- Endpoints are plain `def` (not `async def`): FastAPI runs them in a threadpool, which is right for blocking SQLite.
- `Depends(get_db)` gives a short-lived connection per request, closed afterwards.
- Pages return `TemplateResponse` via `pages.render()` so title, nav and signed-in state are decided in one place.
- JSON errors are always `{"error": "message"}` (the `HTTPException` handler in `main.py` does this for `/api/*`).
- Responses for signed-in areas carry `Cache-Control: no-store`.

## Security headers

`main.py` middleware adds a strict CSP (`default-src 'self'`, no inline script/style, `frame-ancestors 'none'`),
`X-Content-Type-Options: nosniff` and `Referrer-Policy`. If a page genuinely needs another origin (an analytics script, an API
called from the browser), add exactly that origin to exactly that directive (`script-src`, `connect-src`, `img-src`), never `*`
and never `'unsafe-inline'`. Third-party scripts and trackers also belong in the privacy page.

## Authentication (single administrator)

- Password: scrypt (`n=2**15, r=8, p=1`) stored as `scrypt$salt$hash` in `.env`. Login always runs the hash, so timing does not
  reveal whether the email matched. 10 failures per 15 minutes -> 429.
- Sessions: random 256-bit token in an HttpOnly, SameSite=Lax cookie (`Secure` when the origin is https). Only the SHA-256 of the
  token is stored. **Sliding expiry**: each use pushes `expires_at` to now+7 days (at most once an hour), capped at 30 days from
  sign-in. Sign-in rotates the token (the old session row is deleted).
- CSRF: the session row holds a CSRF token, returned by `GET /api/session`; every POST/PATCH/DELETE must send it in
  `X-CSRF-Token` (`require_csrf`). Cookies alone never authorise a write.
- Redirect targets (`?next=`) are matched against `^/(?!/)[A-Za-z0-9/_?=&.%:-]*$` (same-site paths only), on both server and client.
- Google sign-in (optional): `/auth/google/start` sets a short-lived state cookie, `/auth/google/callback` checks the state,
  exchanges the code, reads `userinfo`, and accepts only `email_verified == true` **and** an email equal to the admin email.

### Google OAuth gotchas

- A Google Cloud OAuth consent screen in **Testing** status makes refresh tokens expire **7 days** after they were issued
  (refreshing does not extend it). Apps that keep a Google refresh token must either publish the consent screen or show the
  person when re-authorisation is due. Sensitive scopes (e.g. Gmail) can require Google's verification before publishing.
- The redirect URI registered in Google Cloud must equal `<ORIGIN>/auth/google/callback` exactly.
- To know whether a stored refresh token still works, ask Google (refresh it); compute "time left" as issued + 7 days only as an
  estimate.

## From one admin to many users

The scaffold has one implicit user (the admin email). To add users: create `users(id, email, password_hash, role)`, put
`user_id` in `sessions`, return it from `current_session`, and add `user_id` to every table that holds per-user data and to
**every** query's WHERE clause. Inboxtend does exactly this (`auth.py`, `tasks.py`); copy the shape, including "changing a
password signs out the user's other sessions".

## SQLite

- `connect()` creates the folder (0700) and file (0600), sets WAL and `busy_timeout=5000`, runs `SCHEMA` (idempotent
  `CREATE TABLE IF NOT EXISTS`) and `ADDITIONS` (add columns on old databases). Never edit `SCHEMA` for a new column on a
  table that exists in production; add it to `ADDITIONS`.
- Use `with db:` for a transaction; parameterised queries only (`?`), never string-built SQL with data in it.
- A background writer (sync loop) plus web requests can collide: keep write transactions short.
- Back up with SQLite's backup API (inboxtend `scripts/backup.py`), not by copying a live WAL database.

## Settings pattern

`SETTINGS = {key: (default, validator)}` in `api.py`. GET returns defaults overlaid with stored values (invalid leftovers fall
back to the default); PATCH rejects unknown keys, validates all changes, then writes them in one transaction.

## Third-party calls

- Set a timeout on every outbound request.
- For a request a person is waiting on, give the whole call a time budget (inboxtend uses a `contextvars` budget of 8 s in
  `connectors/gmail_readonly.py`) and fail fast with a clear message on rate limits; background jobs may keep a patient retry
  schedule (3, 6, 12, 24, 48 s).
- Cache short-lived access tokens until shortly before they expire; drop the cache on 401 and retry once.
- Log retries and slow calls at WARNING with the *kind* of call, never ids, tokens or message content.

## Untrusted HTML (e.g. email)

Sanitize server-side with an allow-list (bleach: tags, attributes, CSS properties, protocols `https`/`data` only), keep only
`https` links, add `target="_blank" rel="noopener noreferrer nofollow ugc"` yourself, serve it from its own endpoint with its own
CSP, and show it in an `<iframe sandbox="allow-popups allow-popups-to-escape-sandbox">` (no scripts, no same-origin).
Reference: inboxtend `mail_design.py` and the `/design` route in `asgi.py`.
