# Gotchas (each one cost time once)

- **Class not styled?** Tailwind only compiles classes it finds in `@source` paths. Add the path or use the class in a scanned
  file, then `make css`. The compiled `app.css` is committed, so remember to commit it.
- **Script or style silently ignored?** The CSP blocks inline code and other origins. Move it to a file or add the one origin
  to the one directive.
- **Typer with one command**: `python cli.py serve` fails ("unexpected extra argument") because Typer folds a lone command into
  the program. The scaffold adds an empty `@cli.callback()` for that reason.
- **Google "Testing" consent screen**: refresh tokens die after 7 days. Show time-left and offer a re-authorise button, or publish.
- **429/5xx retry loops block people**: a page request must not sleep through a 3+6+12 s back-off. Use a request time budget.
- **Fetching a token per request** wastes a round trip and a rate-limit slot; cache it until near expiry.
- **Cloudflare 525** = no Caddy site block / certificate for the host (see deploy.md).
- **SQLite `database is locked`** under a background writer: keep transactions short, `busy_timeout=5000`, WAL on.
- **Session length**: a fixed 12 h cookie annoys users; use sliding idle expiry with a hard cap (auth.py), cookie Max-Age = the cap.
- **Gitignore generated assets by mistake**: `app/static/css/app.css` and `app/static/vendor/` are committed on purpose.
- **Editing system config** (Caddyfile, systemd): back up first, validate, then reload; verify with curl.
- **Two header/footer copies drift apart**: keep one `_header.html` and one `_footer.html`, included from `base.html`.
- **Browser caches old scripts** after a deploy; hard-refresh when checking.
- **Docs paste vs. publish**: a privacy page must match reality; when you add a tracker, a third-party API or a cookie, update it.
