#!/usr/bin/env python3
"""
Check and clear audit logs in the database
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import app modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Import app modules
from app import create_app, db
from app.models.audit_log import AuditLog

def main():
    """Check and optionally clear audit logs"""
    app = create_app()
    with app.app_context():
        # Count audit logs
        count = db.session.query(AuditLog).count()
        print(f"Found {count} audit log entries")
        
        if count > 0:
            confirm = input("Do you want to clear these entries? (y/N): ")
            if confirm.lower() == 'y':
                db.session.query(AuditLog).delete()
                db.session.commit()
                print(f"Deleted {count} audit log entries")
            else:
                print("No entries were deleted")

if __name__ == "__main__":
    main()