"""Daily startup: init DB, sync Whoop, launch Streamlit dashboard.

Usage:
    python -m scripts.start
"""

import subprocess
import sys
from datetime import datetime

from src.models.database import SessionLocal, init_db
from src.data.whoop_sync import sync_whoop
from src.data.wyze_sync import sync_wyze


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def main():
    # Step 1: Ensure tables exist
    _log("Initializing database...")
    init_db()
    _log("  Done.")

    # Step 2: Sync Whoop (non-blocking — failures don't prevent dashboard)
    _log("Syncing Whoop data (last 7 days)...")
    try:
        db = SessionLocal()
        stats = sync_whoop(db, days=7)
        db.close()
        _log(f"  Synced: {stats['synced']} new, {stats['updated']} updated, "
             f"{stats['skipped']} skipped, {stats['errors']} errors")
    except Exception as e:
        _log(f"  Whoop sync skipped: {e}")
        _log("  (Dashboard will still launch — run 'python -m scripts.whoop_auth' to fix)")

    # Step 3: Sync Wyze scale (non-blocking — failures don't prevent dashboard)
    _log("Syncing Wyze scale data (last 7 days)...")
    try:
        db = SessionLocal()
        stats = sync_wyze(db, days=7)
        db.close()
        _log(f"  Synced: {stats['synced']} new, {stats['updated']} updated, "
             f"{stats['skipped']} skipped, {stats['errors']} errors")
    except Exception as e:
        _log(f"  Wyze sync skipped: {e}")
        _log("  (Set WYZE_EMAIL/WYZE_PASSWORD in .env to enable)")

    # Step 4: Launch Streamlit
    print("\nLaunching dashboard...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/dashboard/app.py",
        "--server.headless", "true",
    ])


if __name__ == "__main__":
    main()
