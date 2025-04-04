#!/usr/bin/env python
"""
Fix protocol type handling for assessments
"""

import sys
import os
sys.path.append('.')

from app import create_app, db
from app.models.protocol import Protocol
from app.models.patient import ProtocolType, Patient

def fix_protocol_handling():
    print("Checking protocol types in the database...")
    print("-----------------------------------------")

    app = create_app()
    with app.app_context():
        # Print available enum values from the protocol type
        print(f"Available Protocol Types (Enum values):")
        for pt in ProtocolType:
            print(f"  - {pt.name} ({pt.value})")
        print()
    
        # Check registered protocols
        protocols = Protocol.query.all()
        print(f"Found {len(protocols)} protocols in database:")
        for protocol in protocols:
            print(f"  - ID: {protocol.id}, Name: {protocol.name}")
            print(f"    Type: {protocol.protocol_type} (enum value: {protocol.protocol_type.value})")
            print(f"    Questions: {len(protocol.questions)}")
            print(f"    Active: {protocol.is_active}")
        print()
        
        # Check patients protocol types
        patients = Patient.query.all()
        print(f"Found {len(patients)} patients in database with these protocol types:")
        protocol_type_counts = {}
        for patient in patients:
            pt = patient.protocol_type
            if pt.name not in protocol_type_counts:
                protocol_type_counts[pt.name] = 0
            protocol_type_counts[pt.name] += 1
        
        for pt_name, count in protocol_type_counts.items():
            print(f"  - {pt_name}: {count} patients")
        print()
        
        # Test fetching a protocol by type
        for pt in ProtocolType:
            protocol = Protocol.query.filter_by(protocol_type=pt, is_active=True).first()
            if protocol:
                print(f"Found protocol for {pt.name}: {protocol.name} (ID: {protocol.id})")
            else:
                print(f"NO PROTOCOL FOUND for {pt.name} - this is an issue!")
        print()

        print("Protocol check complete!")

if __name__ == "__main__":
    fix_protocol_handling()