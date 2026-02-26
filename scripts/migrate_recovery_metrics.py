"""One-time migration: drop and recreate recovery_metrics table.

The model was fixed (source: Integer -> String(50)) but SQLite doesn't support
ALTER COLUMN. Table has 0 rows so it's safe to drop/recreate.

Usage:
    python -m scripts.migrate_recovery_metrics
    python -m scripts.migrate_recovery_metrics --force   # skip row-count check
"""

import argparse
import sys

from sqlalchemy import inspect, text

from src.models.database import Base, engine


def main():
    parser = argparse.ArgumentParser(description="Migrate recovery_metrics schema")
    parser.add_argument("--force", action="store_true", help="Drop even if table has rows")
    args = parser.parse_args()

    table_name = "recovery_metrics"
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        print(f"Table '{table_name}' does not exist. Creating it fresh...")
        # Import models so Base knows about the table
        from src.models import wellness  # noqa: F401
        Base.metadata.tables[table_name].create(bind=engine)
        print("Done.")
        return

    # Check row count
    with engine.connect() as conn:
        row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    if row_count > 0 and not args.force:
        print(f"ERROR: Table '{table_name}' has {row_count} rows.")
        print("Use --force to drop anyway (data will be lost).")
        sys.exit(1)

    if row_count > 0:
        print(f"WARNING: Dropping table with {row_count} rows (--force)")

    # Drop and recreate
    print(f"Dropping '{table_name}'...")
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE {table_name}"))
        conn.commit()

    print(f"Recreating '{table_name}'...")
    from src.models import wellness  # noqa: F401
    Base.metadata.tables[table_name].create(bind=engine)

    # Verify
    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    source_type = str(columns.get("source", {}).get("type", ""))
    print(f"Verified: source column type = {source_type}")
    print("Migration complete.")


if __name__ == "__main__":
    main()
