#!/usr/bin/env python3
"""
Script to clean the database and remove duplicate protocols
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import Patient, ProtocolType
from src.models.assessment import Assessment


def clean_database():
    """Remove duplicate protocols and keep only one of each type"""
    app = create_app()
    with app.app_context():
        print("Starting database cleanup...")

        # Get all protocols
        protocols = Protocol.query.all()
        print(f"Found {len(protocols)} protocols")

        # Group protocols by type
        protocol_by_type = {}
        for p in protocols:
            if p.protocol_type not in protocol_by_type:
                protocol_by_type[p.protocol_type] = []
            protocol_by_type[p.protocol_type].append(p)

        # For each type, keep only the first one and delete the rest
        for protocol_type, protocol_list in protocol_by_type.items():
            if len(protocol_list) > 1:
                # Keep the first protocol
                keep_protocol = protocol_list[0]
                delete_protocols = protocol_list[1:]

                print(
                    f"Type {protocol_type}: Keeping ID {keep_protocol.id}, deleting IDs {[p.id for p in delete_protocols]}"
                )

                # Update assessments to use the kept protocol
                for delete_protocol in delete_protocols:
                    assessments = Assessment.query.filter_by(
                        protocol_id=delete_protocol.id
                    ).all()
                    print(
                        f"  Updating {len(assessments)} assessments from protocol {delete_protocol.id} to {keep_protocol.id}"
                    )

                    for assessment in assessments:
                        assessment.protocol_id = keep_protocol.id

                    # Delete the duplicate protocol
                    db.session.delete(delete_protocol)
            else:
                print(
                    f"Type {protocol_type}: Only one protocol exists (ID {protocol_list[0].id})"
                )

        # Commit changes
        db.session.commit()
        print("Database cleanup complete!")


if __name__ == "__main__":
    clean_database()
