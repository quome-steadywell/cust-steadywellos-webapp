#!/usr/bin/env python3
"""
Script to check database data
"""

import os
import sys
from pathlib import Path
import json

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.protocol import Protocol
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.user import User
from app.models.call import Call

def check_data():
    """Print database data information"""
    app = create_app()
    with app.app_context():
        # Check protocols
        protocols = Protocol.query.all()
        print('PROTOCOLS:')
        for p in protocols:
            print(f'{p.id}: {p.name} - {p.protocol_type}')
        
        print('\nPATIENTS:')
        patients = Patient.query.all()
        for p in patients:
            print(f'{p.id}: {p.first_name} {p.last_name} - Protocol: {p.protocol_type}')
        
        print('\nASSESSMENTS:')
        assessments = Assessment.query.all()
        print(f'Total assessments: {len(assessments)}')
        for p in patients:
            assess_count = Assessment.query.filter_by(patient_id=p.id).count()
            print(f'Patient {p.id} ({p.first_name} {p.last_name}) has {assess_count} assessments')
            
            # Check the most recent assessment for each patient
            latest = Assessment.query.filter_by(patient_id=p.id).order_by(Assessment.assessment_date.desc()).first()
            if latest:
                print(f'  Latest assessment: {latest.assessment_date} - Protocol ID: {latest.protocol_id}')
            else:
                print(f'  No assessments found')

def check_mary_johnson():
    """Check Mary Johnson's data specifically"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in the database!")
            return
        
        print(f"Found Mary Johnson (ID: {mary.id})")
        print(f"Protocol Type: {mary.protocol_type}")
        
        # Get the protocol
        protocol = Protocol.query.filter_by(protocol_type=mary.protocol_type).first()
        if not protocol:
            print(f"No protocol found for type {mary.protocol_type}!")
            return
        
        print(f"Found protocol (ID: {protocol.id}, Name: {protocol.name})")
        
        # Get all assessments for March 25, 2025
        march25_assessments = Assessment.query.filter(
            Assessment.assessment_date >= '2025-03-25 00:00:00',
            Assessment.assessment_date < '2025-03-26 00:00:00'
        ).all()
        
        print(f"\nAll assessments for March 25, 2025 (all patients):")
        for assessment in march25_assessments:
            patient = Patient.query.get(assessment.patient_id)
            patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
            print(f"Assessment ID: {assessment.id}, Patient: {patient_name}, Protocol ID: {assessment.protocol_id}")
        
        # Get Mary's assessments
        assessments = Assessment.query.filter_by(patient_id=mary.id).all()
        print(f"\nFound {len(assessments)} assessments for Mary Johnson")
        
        for i, assessment in enumerate(assessments):
            print(f"\nAssessment {i+1} (ID: {assessment.id}):")
            print(f"  Date: {assessment.assessment_date}")
            print(f"  Protocol ID: {assessment.protocol_id}")
            print(f"  Follow-up Needed: {assessment.follow_up_needed}")
            if assessment.follow_up_needed:
                print(f"  Follow-up Date: {assessment.follow_up_date}")
                print(f"  Follow-up Priority: {assessment.follow_up_priority}")
            
            # Check if protocol exists for this assessment
            if assessment.protocol_id:
                protocol = Protocol.query.get(assessment.protocol_id)
                if protocol:
                    print(f"  Protocol Found: Yes (ID: {protocol.id}, Name: {protocol.name})")
                else:
                    print(f"  Protocol Found: No! Protocol ID {assessment.protocol_id} not found")
            else:
                print("  Protocol ID is None!")
                
            # Print responses and symptoms
            if assessment.responses:
                print("  Responses:")
                for key, value in assessment.responses.items():
                    print(f"    {key}: {value}")
                    
            if assessment.symptoms:
                print("  Symptoms:")
                for key, value in assessment.symptoms.items():
                    print(f"    {key}: {value}")
                    
            if assessment.interventions:
                print("  Interventions:")
                for intervention in assessment.interventions:
                    print(f"    {intervention.get('title', 'No title')}: {intervention.get('description', 'No description')}")

def fix_mary_johnson():
    """Fix Mary Johnson's assessment data"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in the database!")
            return
        
        # Get the protocol
        protocol = Protocol.query.filter_by(protocol_type=mary.protocol_type).first()
        if not protocol:
            print(f"No protocol found for type {mary.protocol_type}!")
            return
        
        # Get Mary's assessments
        assessments = Assessment.query.filter_by(patient_id=mary.id).all()
        
        # Fix each assessment
        for assessment in assessments:
            if assessment.protocol_id is None:
                print(f"Fixing assessment ID {assessment.id} - setting protocol_id to {protocol.id}")
                assessment.protocol_id = protocol.id
        
        # Commit changes
        db.session.commit()
        print("Fixes applied and committed to database")

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    if command == "check":
        check_data()
    elif command == "mary":
        check_mary_johnson()
    elif command == "fix":
        fix_mary_johnson()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python check_data.py [check|mary|fix]")
        print("  check - Check all database data")
        print("  mary - Check Mary Johnson's data")
        print("  fix - Fix Mary Johnson's assessment data")