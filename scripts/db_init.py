#!/usr/bin/env python3
"""
Database initialization script for SteadywellOS
This script creates the necessary database tables and can seed the database with initial data
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import src modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.user import User, UserRole
from src.models.patient import Patient, Gender, ProtocolType
from src.models.protocol import Protocol
from src.utils.db_seeder import seed_database


def init_db(config=None, seed=False, reset=False):
    """Initialize the database"""
    print("Initializing database...")

    # Create app with specified config
    app = create_app(config)

    with app.app_context():
        if reset:
            print("Dropping all tables...")
            db.drop_all()

        print("Creating database tables...")
        db.create_all()

        # Check if admin user exists
        if User.query.filter_by(username="admin").first() is None:
            print("Creating admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                is_active=True,
            )
            admin.password = "password123"
            db.session.add(admin)
            db.session.commit()
            print("Admin user created.")

        if seed:
            print("Seeding database with initial data...")
            seed_database()
            print("Database seeded.")

    print("Database initialization complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the SteadywellOS database")
    parser.add_argument(
        "--seed", action="store_true", help="Seed the database with initial data"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset the database (drop all tables)"
    )
    parser.add_argument("--config", help="Specify the configuration to use")

    args = parser.parse_args()

    init_db(config=args.config, seed=args.seed, reset=args.reset)
