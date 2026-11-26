"""@@NAME@@ command line:  python cli.py serve --port @@PORT@@ [--reload]"""
from pathlib import Path

import typer

cli = typer.Typer(help='Run @@NAME@@.')


@cli.callback()
def main():
    """Keeps `serve` a named subcommand (Typer folds a lone command into the program itself)."""


@cli.command()
def serve(port: int = typer.Option(@@PORT@@, min=1, max=65535), host: str = '127.0.0.1',
          reload: bool = typer.Option(False, help='Reload Python code and templates during development.')):
    """Run the FastAPI application with Uvicorn (bind to 127.0.0.1 and put Caddy in front of it)."""
    import uvicorn
    root = Path(__file__).resolve().parent
    options = {'reload_dirs': [str(root / 'app')], 'reload_includes': ['*.py', '*.html']} if reload else {}
    uvicorn.run('app.main:app', host=host, port=port, reload=reload, proxy_headers=True, forwarded_allow_ips='127.0.0.1', **options)


if __name__ == '__main__':
    cli()
