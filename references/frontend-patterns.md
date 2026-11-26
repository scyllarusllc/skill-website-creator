# Front-end patterns

Plain JavaScript loaded with `<script defer>`, one file per page plus `common.js`. No bundler, no framework.

## common.js (signed-in pages)

| Helper | Use |
|---|---|
| `el(tag, text, cls)` | create an element; text goes in via `textContent` |
| `request(path, method, body)` | `fetch` with JSON, CSRF header on writes, 401 -> `/login`, throws `Error(message)` from `{"error"}` |
| `notify(message, error?)` | toast (the Stimulus `toast` controller listens for `site:notice`) |
| `icon(name)` | `<i>` for a Font Awesome class from the `ICONS` map |
| `sessionReady` | promise resolved once the CSRF token is loaded: `await sessionReady` before the first write |

## Stimulus

`stimulus-app.js` registers controllers (`toast`). Use Stimulus for reusable behaviours bound to markup (`data-controller`);
use a page script for page-specific logic. Stimulus is a vendored ES module imported from `/static/vendor/stimulus/stimulus.js`.

## Page script template

```js
'use strict';
const form = document.getElementById('thing-form');
async function load() { await sessionReady; const data = await request('/api/thing'); /* fill the DOM with el() */ }
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try { await request('/api/thing', 'PATCH', {/* fields */}); notify('Saved.'); }
  catch (error) { notify(error.message, true); }
  finally { button.disabled = false; }
});
load().catch(error => notify(error.message, true));
```

## Habits that avoided real bugs

- Disable the button while a request runs; re-enable in `finally`.
- Time labels: render absolute time in the tooltip, "x ago" in the text, refresh every 30 s.
- Copy buttons: `navigator.clipboard.writeText` works only on https/localhost; show "Copied"/"Copy failed" for 2 s.
- Progress bars: `role="progressbar"` with `aria-valuenow`; colour by threshold (emerald, amber under a limit, rose when urgent).
- A sandboxed iframe cannot be read by the page: to copy its text, fetch the same document and parse it with `DOMParser`
  (an inert document: no scripts run, nothing loads).
- Do not parse HTML with regexes for display; sanitize on the server.
- If the page shows state that can go stale (sync status), poll a cheap status endpoint rather than reloading.
