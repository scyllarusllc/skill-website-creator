'use strict';
const form = document.getElementById('settings-form');

async function load() {
  await sessionReady;
  const {settings} = await request('/api/settings');
  for (const [key, value] of Object.entries(settings)) if (form.elements[key]) form.elements[key].value = value;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = document.getElementById('save-settings');
  button.disabled = true;
  try {
    await request('/api/settings', 'PATCH', {display_name: form.elements.display_name.value.trim()});
    notify('Saved.');
  } catch (error) { notify(error.message, true); }
  finally { button.disabled = false; }
});

load().catch(error => notify(error.message, true));
