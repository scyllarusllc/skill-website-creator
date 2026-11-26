# Deploy: systemd + Caddy (+ Cloudflare)

Assumes a Linux host where Caddy already terminates TLS for other sites (the Inbox Tend host does).

## 1. Run the app as a service

Copy `deploy/<slug>.service` to `/etc/systemd/system/`, fix `WorkingDirectory` and `ExecStart`, then:

```sh
sudo systemctl daemon-reload && sudo systemctl enable --now <slug>
systemctl status <slug>; journalctl -u <slug> -f
curl -s http://127.0.0.1:<port>/healthz        # ok
```

The app listens on `127.0.0.1` only; Caddy is the public edge. Restart the service after changing Python code or templates
(`make dev` reloads, the service does not).

## 2. Caddy

1. Pick the port the app uses (`ss -ltn`, grep the Caddyfile) so nothing collides.
2. Back up: `cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-<slug>-$(date +%Y%m%d)`.
3. Append the block from `deploy/Caddyfile.snippet` (apex site, `www` redirect, `http://` redirect).
4. `caddy validate --config /etc/caddy/Caddyfile` and only then `systemctl reload caddy`.
5. Wait ~10 s for the certificate, then `curl -sI https://<domain>/`.

## 3. DNS / Cloudflare

- Point the domain at the server (proxied through Cloudflare is fine).
- **Cloudflare error 525** = Cloudflare could not complete TLS to the origin: Caddy has no site block (or no certificate yet)
  for that hostname. Add the block and reload.
- Behind Cloudflare the client IP is in `CF-Connecting-IP`; uvicorn's `proxy_headers` only trusts `127.0.0.1` (Caddy).
- Set `<ENV>_ORIGIN=https://<domain>` in `.env` so cookies are `Secure` and Google redirects back correctly.

## 4. Backups and secrets

- `.env` mode 600, owned by the service user. Never commit it. Credentials handed over as a file (for example a Google
  `client_secret*.json`) are read by a script and written into `.env`; do not paste them into chat or logs.
- Back up `data/<slug>.sqlite3` with the SQLite backup API on a timer (see inboxtend `deploy/systemd/inboxtend-backup.*`).

## 5. After changing code on a live site

`make css` if classes changed -> `systemctl restart <slug>` -> curl the changed pages -> check `journalctl -u <slug>` for errors.
Browsers cache scripts: tell the user to hard-refresh, or version the script URL.
