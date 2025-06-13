#!/usr/bin/env python3
"""
Script to check database records for Mary Johnson
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from one directory above this script
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add the parent directory to the path so we can import src
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.patient import Patient
from src.models.protocol import Protocol
from src.models.assessment import Assessment
from src.models.user import User

def check_mary_johnson():
    """Check Mary Johnson record in database"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in the database!")
            return
            
        # Display Mary's info
        print(f"Mary Johnson (ID: {mary.id})")
        print(f"MRN: {mary.mrn}")
        print(f"Protocol Type: {mary.protocol_type}")
        print(f"Primary Nurse ID: {mary.primary_nurse_id}")
        
        # Find nurse1
        nurse1 = User.query.filter_by(username="nurse1").first()
        if nurse1:
            print(f"Nurse1 (ID: {nurse1.id}, Name: {nurse1.first_name} {nurse1.last_name})")
            print(f"Mary's primary nurse matches nurse1: {mary.primary_nurse_id == nurse1.id}")
        else:
            print("Nurse1 not found in the database!")
        
        # Find protocol for Mary's protocol type
        protocol = Protocol.query.filter_by(protocol_type=mary.protocol_type).first()
        if protocol:
            print(f"\nProtocol (ID: {protocol.id}, Name: {protocol.name})")
        else:
            print(f"No protocol found for type {mary.protocol_type}!")
            
        # Get Mary's assessments
        assessments = Assessment.query.filter_by(patient_id=mary.id).all()
        print(f"\nFound {len(assessments)} assessments for Mary Johnson")
        
        for assessment in assessments:
            print(f"\nAssessment {assessment.id}:")
            print(f"  Date: {assessment.assessment_date}")
            print(f"  Protocol ID: {assessment.protocol_id}")
            print(f"  Follow-up needed: {assessment.follow_up_needed}")
            if assessment.follow_up_needed:
                print(f"  Follow-up date: {assessment.follow_up_date}")
                print(f"  Follow-up priority: {assessment.follow_up_priority}")

if __name__ == "__main__":
    check_mary_johnson()