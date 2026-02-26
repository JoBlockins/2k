"""Initialize the database with all tables."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.database import init_db


def main():
    print("Initializing database...")
    init_db()
    print("Database initialized successfully at data/training.db")


if __name__ == "__main__":
    main()
