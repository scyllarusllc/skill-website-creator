PORT ?= @@PORT@@
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: help install dev run css css-watch vendor hash-password

help:
	@printf '%s\n' 'make install        Create .venv, install Python and Node dependencies.'
	@printf '%s\n' 'make dev            Run with auto-reload at http://127.0.0.1:$(PORT).'
	@printf '%s\n' 'make run            Run without reload.'
	@printf '%s\n' 'make css            Build app/static/css/app.css (commit the result).'
	@printf '%s\n' 'make css-watch      Rebuild the CSS while you edit.'
	@printf '%s\n' 'make vendor         Re-copy Font Awesome and Stimulus into app/static/vendor.'
	@printf '%s\n' 'make hash-password  Print @@ENV@@_ADMIN_PASSWORD_HASH for .env.'

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	npm install --no-audit --no-fund

dev:
	$(PYTHON) cli.py serve --port $(PORT) --reload

run:
	$(PYTHON) cli.py serve --port $(PORT)

css:
	npm run build:css

css-watch:
	npm run watch:css

vendor:
	npm run vendor

hash-password:
	$(PYTHON) scripts/hash_password.py
