// Copies the third-party front-end files the site serves into app/static/vendor. The copies are committed, so running
// the site needs no Node. Re-run after changing a version in package.json:   npm run vendor
import {cpSync, mkdirSync, readFileSync, rmSync} from 'node:fs';
const version = name => JSON.parse(readFileSync(`node_modules/${name}/package.json`, 'utf8')).version;

{   // Stimulus: native ES module, no runtime build
  const from = 'node_modules/@hotwired/stimulus', to = 'app/static/vendor/stimulus';
  rmSync(to, {recursive: true, force: true});
  mkdirSync(to, {recursive: true});
  cpSync(`${from}/dist/stimulus.js`, `${to}/stimulus.js`);
  cpSync(`${from}/LICENSE.md`, `${to}/LICENSE.md`);
  console.log(`Stimulus ${version('@hotwired/stimulus')} -> ${to}`);
}

{   // Font Awesome Free: only the styles and fonts that are used
  const from = 'node_modules/@fortawesome/fontawesome-free', to = 'app/static/vendor/fontawesome';
  rmSync(to, {recursive: true, force: true});
  mkdirSync(`${to}/css`, {recursive: true});
  mkdirSync(`${to}/webfonts`, {recursive: true});
  for (const f of ['fontawesome', 'solid', 'regular', 'brands']) cpSync(`${from}/css/${f}.min.css`, `${to}/css/${f}.min.css`);
  for (const f of ['fa-solid-900', 'fa-regular-400', 'fa-brands-400']) cpSync(`${from}/webfonts/${f}.woff2`, `${to}/webfonts/${f}.woff2`);
  cpSync(`${from}/LICENSE.txt`, `${to}/LICENSE.txt`);
  console.log(`Font Awesome Free ${version('@fortawesome/fontawesome-free')} -> ${to}`);
}
