import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import text
from app.models.base import db

from app.core.config import settings

@click.command("manage-tables")
@click.option("--list", "list_only", is_flag=True, help="List all database tables with their row counts.")
@click.option("--empty", "empty_tables", help="Comma-separated list of table names to empty (DELETE ALL ROWS). Use 'all' to empty all tables.")
@click.option("--drop", "drop_tables", help="Comma-separated list of table names to drop. Use 'all' to drop all tables.")
@click.option("--force", is_flag=True, help="Execute actions without interactive confirmation.")
@with_appcontext
def manage_tables_command(list_only: bool, empty_tables: str | None, drop_tables: str | None, force: bool) -> None:
    """Manage database tables: list, empty, or delete (drop) tables."""
    # Safety Check: Limit destructive actions to development or testing
    env = settings.FLASK_ENV
    if (empty_tables or drop_tables) and env not in ("development", "testing"):
        click.echo(f"CRITICAL: Destructive operations are not allowed in env={env}. Operation cancelled.")
        return

    # Gather registered tables from SQLAlchemy metadata
    tables = list(db.metadata.tables.keys())

    # 1. Handle Listing
    if list_only or (not empty_tables and not drop_tables):
        click.echo(f"{'Table Name':<30} | Row Count")
        click.echo("-" * 45)
        for tbl in sorted(tables):
            try:
                row_count = db.session.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                click.echo(f"{tbl:<30} | {row_count}")
            except Exception as e:
                click.echo(f"{tbl:<30} | Error: {e}")
        return

    # Check database engine dialect
    is_sqlite = db.engine.url.drivername == "sqlite" or "sqlite" in current_app.config.get("SQLALCHEMY_DATABASE_URI", "")

    # 2. Handle Empty (Delete Rows)
    if empty_tables:
        target_tables = tables if empty_tables.strip().lower() == "all" else [t.strip() for t in empty_tables.split(",") if t.strip() in tables]
        if not target_tables:
            click.echo("No valid tables selected to empty.")
            return

        if not force:
            click.confirm(f"Are you sure you want to empty these tables: {', '.join(target_tables)}?", abort=True)

        try:
            if is_sqlite:
                db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            for tbl in target_tables:
                db.session.execute(text(f"DELETE FROM {tbl}"))
                click.echo(f"Emptied table: {tbl}")

            if is_sqlite:
                db.session.execute(text("PRAGMA foreign_keys = ON"))

            db.session.commit()
            click.echo("Selected tables emptied successfully.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error emptying tables: {e}")

    # 3. Handle Drop (Drop Tables)
    if drop_tables:
        target_tables = tables if drop_tables.strip().lower() == "all" else [t.strip() for t in drop_tables.split(",") if t.strip() in tables]
        if not target_tables:
            click.echo("No valid tables selected to drop.")
            return

        if not force:
            click.confirm(f"Are you sure you want to DROP these tables: {', '.join(target_tables)}?", abort=True)

        try:
            if is_sqlite:
                db.session.execute(text("PRAGMA foreign_keys = OFF"))

            for tbl in target_tables:
                db.session.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
                click.echo(f"Dropped table: {tbl}")

            if is_sqlite:
                db.session.execute(text("PRAGMA foreign_keys = ON"))

            db.session.commit()
            click.echo("Selected tables dropped successfully.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error dropping tables: {e}")
