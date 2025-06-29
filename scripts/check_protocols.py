#!/usr/bin/env python3
"""
Check if protocols exist in the database and print information about them
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import src modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Import src modules
from src import create_app, db
from src.models.protocol import Protocol


def main():
    """Check the protocols in the database"""
    app = create_app()
    with app.app_context():
        # Count protocols
        count = db.session.query(Protocol).count()
        print(f"Found {count} protocol entries")

        if count > 0:
            protocols = db.session.query(Protocol).all()
            for protocol in protocols:
                print(f"Protocol: {protocol.name} (ID: {protocol.id})")
                print(f"  Type: {protocol.protocol_type}")
                print(f"  Version: {protocol.version}")
                print(f"  Active: {protocol.is_active}")
                print(f"  Questions: {len(protocol.questions)}")
                print(f"  Interventions: {len(protocol.interventions)}")
                print(f"  Decision Tree Nodes: {len(protocol.decision_tree)}")
                print()
        else:
            print("No protocols found in the database.")
            print("You can use standard database seeding with 'just db-seed' to create sample protocols.")


if __name__ == "__main__":
    main()
