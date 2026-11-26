# skill-website-creator

A Claude Code skill that builds websites in the stack learned from the [Inbox Tend](../inboxtend) project:

**FastAPI + Jinja2 + Tailwind CSS v4 + Font Awesome (self-hosted) + Stimulus + SQLite**, a strict CSP, single-admin auth
(password and optional Google sign-in), and a systemd + Caddy deploy.

## Use it

Install the skill (any one of):

```sh
ln -s ~/github/skill-website-creator ~/.claude/skills/website-creator   # personal skills
# or copy the folder into <project>/.claude/skills/website-creator
```

Then ask Claude: "create a new website called Acme Notes", "add a settings page", "deploy it behind Caddy". Or scaffold by hand:

```sh
python3 scripts/scaffold.py ~/github/acme-notes --name "Acme Notes" --port 8110 --install --git
cd ~/github/acme-notes && cp .env.example .env && chmod 600 .env && make hash-password && make dev
```

## What is in here

| Path | What |
|---|---|
| `SKILL.md` | The skill: stack table, workflow, conventions |
| `references/` | stack, design system, backend patterns, front-end patterns, deploy, gotchas |
| `templates/site/` | A working site (home, privacy, login, dashboard, settings, 404) with `@@TOKENS@@` |
| `scripts/scaffold.py` | Fills the tokens and writes a new project |

The scaffold was generated, built and exercised end to end (pages, login, CSRF, validation, headers, logout) before release.
Licence: MIT.
