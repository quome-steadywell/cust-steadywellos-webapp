#!/usr/bin/env python3
"""
Inspect protocol data structure to understand decision tree format
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path to import src modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import ProtocolType


def main():
    """Inspect protocol data structure"""
    app = create_app()
    with app.app_context():
        # Get cancer protocol
        protocol = db.session.query(Protocol).filter_by(
            protocol_type=ProtocolType.CANCER,
            is_active=True
        ).first()
        
        if not protocol:
            print("No cancer protocol found")
            return
            
        print(f"Protocol: {protocol.name}")
        print(f"Type: {protocol.protocol_type}")
        print()
        
        print("DECISION TREE:")
        print("=" * 50)
        print(json.dumps(protocol.decision_tree, indent=2))
        print()
        
        print("QUESTIONS (first 3):")
        print("=" * 50)
        for i, question in enumerate(protocol.questions[:3]):
            print(f"Question {i+1}: {json.dumps(question, indent=2)}")
            print()


if __name__ == "__main__":
    main()