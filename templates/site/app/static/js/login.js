'use strict';
const form = document.getElementById('login-form');
const status = document.getElementById('login-status');
const params = new URLSearchParams(location.search);
const next = params.get('next');
const googleLink = document.getElementById('google-login');
if (googleLink && next) googleLink.href += '?next=' + encodeURIComponent(next);
const errors = {google: 'Google sign-in failed. Please try again.', 'google-denied': 'That Google account is not allowed to sign in.'};
if (params.get('error') && errors[params.get('error')]) document.getElementById('google-error').textContent = errors[params.get('error')];

form?.addEventListener('submit', async event => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  status.textContent = '';
  try {
    const response = await fetch('/api/auth/login', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(Object.fromEntries(new FormData(form).entries()))});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'Sign in failed');
    // Only same-site paths: anything else goes to the dashboard.
    location.assign(/^\/(?!\/)[A-Za-z0-9/_?=&.%:-]*$/.test(next || '') ? next : '/dashboard');
  } catch (error) { status.textContent = error.message; button.disabled = false; }
});
