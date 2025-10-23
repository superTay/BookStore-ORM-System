"""Project runner for common tasks.

Usage examples (run from project root):
    python manage.py init-db
    python manage.py test-db
    python manage.py cli seed-libros
    python manage.py cli listar-libros
    python manage.py cli crear-venta "Cliente Demo" 1:2 2:1
    python manage.py cli actualizar-precios --ids 1,2 --precio 9.99
    python manage.py cli actualizar-pedido 1 1:3 2:1
"""

import argparse
import sys


def cmd_init_db(_: argparse.Namespace) -> None:
    from config.database import Base, engine
    # Ensure models are imported so metadata includes them
    from domain.models import libro, venta, usuario  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("Tables created (if not existing).")


def cmd_test_db(_: argparse.Namespace) -> None:
    from sqlalchemy import text
    from config.database import engine

    with engine.connect() as conn:
        val = conn.execute(text("SELECT 1")).scalar()
    print(f"Connection OK. SELECT 1 -> {val}")


def cmd_cli(args: argparse.Namespace) -> None:
    # Forward to the existing CLI implementation
    from app.cli.main import main as cli_main

    # Rebuild argv as if calling `python -m app.cli.main ...`
    sys.argv = ["app.cli.main", *args.rest]
    cli_main()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Project task runner")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create database tables").set_defaults(func=cmd_init_db)
    sub.add_parser("test-db", help="Test database connectivity").set_defaults(func=cmd_test_db)

    cli = sub.add_parser("cli", help="Run app CLI commands")
    cli.add_argument("rest", nargs=argparse.REMAINDER, help="CLI args (e.g., listar-libros)")
    cli.set_defaults(func=cmd_cli)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

