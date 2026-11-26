#!/usr/bin/env python3
"""Create a new site from templates/site.

    python3 scripts/scaffold.py ~/github/my-site --name "My Site" [--slug my-site] [--port 8100] [--install] [--git]

Placeholders replaced in file contents and file names:
    @@NAME@@  display name         "My Site"
    @@SLUG@@  kebab-case id        "my-site"      (service name, cookie names, database file)
    @@ENV@@   env-var prefix       "MY_SITE"
    @@PORT@@  local port           8100
    @@YEAR@@  current year
"""
from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / 'templates' / 'site'
RENAMES = {'gitignore': '.gitignore'}   # Stored without the dot so it is not treated as this repo's own ignore file.


def slugify(text: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if not slug:
        raise SystemExit('Cannot derive a slug from that name; pass --slug.')
    return slug


def run(command: list[str], cwd: Path) -> None:
    print('+', ' '.join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', type=Path, help='Directory to create (must be empty or not exist)')
    parser.add_argument('--name', required=True, help='Display name, e.g. "My Site"')
    parser.add_argument('--slug', help='kebab-case id (default: from the name)')
    parser.add_argument('--port', type=int, default=8100, help='Local port behind Caddy (default 8100)')
    parser.add_argument('--install', action='store_true', help='Also create .venv, npm install, vendor assets and build the CSS')
    parser.add_argument('--git', action='store_true', help='git init and make the first commit')
    args = parser.parse_args()

    slug = args.slug or slugify(args.name)
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,40}', slug):
        raise SystemExit('The slug must be lowercase letters, digits and dashes, starting with a letter.')
    if not 1024 <= args.port <= 65535:
        raise SystemExit('The port must be between 1024 and 65535.')
    values = {'@@NAME@@': args.name, '@@SLUG@@': slug, '@@ENV@@': slug.upper().replace('-', '_'),
              '@@PORT@@': str(args.port), '@@YEAR@@': str(datetime.date.today().year)}

    target = args.target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f'{target} is not empty. Pick a new directory.')

    def fill(text: str) -> str:
        for token, value in values.items():
            text = text.replace(token, value)
        return text

    count = 0
    for source in sorted(TEMPLATE.rglob('*')):
        if source.is_dir() or '__pycache__' in source.parts:
            continue
        relative = Path(*[RENAMES.get(fill(part), fill(part)) for part in source.relative_to(TEMPLATE).parts])
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.write_text(fill(source.read_text()))
        except UnicodeDecodeError:
            shutil.copyfile(source, destination)
        count += 1
    print(f'Created {count} files in {target}')

    if args.install:
        run([sys.executable, '-m', 'venv', '.venv'], target)
        run(['.venv/bin/pip', 'install', '-q', '-r', 'requirements.txt'], target)
        run(['npm', 'install', '--no-audit', '--no-fund'], target)
        run(['npm', 'run', 'vendor'], target)
        run(['npm', 'run', 'build:css'], target)
    if args.git:
        run(['git', 'init', '-q', '-b', 'main'], target)
        run(['git', 'add', '-A'], target)
        run(['git', 'commit', '-q', '-m', f'Start {args.name} from skill-website-creator'], target)

    print(f'''
Next:
  cd {target}
  {"" if args.install else "make install && npm run vendor && make css\n  "}cp .env.example .env && chmod 600 .env && make hash-password   # paste the line into .env
  make dev        # http://127.0.0.1:{args.port}''')


if __name__ == '__main__':
    main()
