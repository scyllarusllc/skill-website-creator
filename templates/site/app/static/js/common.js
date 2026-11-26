'use strict';
// Shared helpers for signed-in pages. No inline script anywhere: the CSP only allows scripts from this origin.
let csrfToken = '';

function el(tag, text, cls) {   // Always build DOM with textContent, never innerHTML with data.
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}

async function request(path, method = 'GET', body) {
  const options = {method, headers: {}, credentials: 'same-origin'};
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  if (method !== 'GET') options.headers['X-CSRF-Token'] = csrfToken;
  const response = await fetch(path, options);
  let data;
  try { data = await response.json(); }
  catch (_) { throw Error('The server returned an unexpected response (HTTP ' + response.status + '). Please try again.'); }
  if (response.status === 401) { location.assign('/login'); throw Error('Session expired'); }
  if (!response.ok) throw Error(data.error || 'Request failed (' + response.status + ')');
  return data;
}

function notify(message, error = false) {   // Shown by the toast controller in stimulus-app.js
  document.getElementById('notice')?.dispatchEvent(new CustomEvent('site:notice', {detail: {message, error}}));
}

// Icons: a name maps to a Font Awesome class, so scripts never repeat class strings.
const ICONS = {check: 'fa-solid fa-check', plus: 'fa-solid fa-plus', trash: 'fa-regular fa-trash-can', copy: 'fa-regular fa-copy', xmark: 'fa-solid fa-xmark'};
function icon(name) {
  const node = document.createElement('i');
  node.className = (ICONS[name] || 'fa-solid fa-circle') + ' fa-fw';
  node.setAttribute('aria-hidden', 'true');
  return node;
}

const sessionReady = request('/api/session').then(session => { csrfToken = session.csrf_token; });

document.getElementById('logout')?.addEventListener('click', async () => {
  try { await sessionReady; await request('/api/auth/logout', 'POST', {}); location.assign('/login'); }
  catch (error) { notify(error.message, true); }
});
