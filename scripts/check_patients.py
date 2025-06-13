#!/usr/bin/env python3
"""
Script to check patients and their assessments
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import src
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import Patient, ProtocolType 
from src.models.assessment import Assessment
from src.models.user import User, UserRole

def check_patients():
    """Check patient list and their active status"""
    app = create_app()
    with app.app_context():
        patients = Patient.query.all()
        print(f'Total patients: {len(patients)}')
        for p in patients:
            print(f'ID: {p.id}, Name: {p.first_name} {p.last_name}, Active: {p.is_active}, Protocol: {p.protocol_type}')

        # Update Mary Johnson to active if needed
        mary = Patient.query.filter_by(first_name="Mary").first()
        if mary and not mary.is_active:
            print(f"Updating Mary Johnson (ID: {mary.id}) to active status")
            mary.is_active = True
            db.session.commit()
            print("Mary Johnson updated to active status")

def update_db_for_march25():
    """Ensure March 25 assessments have correct properties"""
    app = create_app()
    with app.app_context():
        # Find assessments for March 25, 2025
        march25_assessments = Assessment.query.filter(
            Assessment.assessment_date >= '2025-03-25 00:00:00',
            Assessment.assessment_date < '2025-03-26 00:00:00'
        ).all()
        
        print(f"Found {len(march25_assessments)} assessments for March 25, 2025")
        
        # Get nurse1 as a default conducted_by
        nurse1 = User.query.filter_by(username="nurse1").first()
        if not nurse1:
            print("ERROR: Could not find nurse1 user!")
            return
            
        # Update assessments
        for assessment in march25_assessments:
            print(f"\nAssessment ID {assessment.id}:")
            print(f"  Patient ID: {assessment.patient_id}")
            
            # Get patient
            patient = Patient.query.get(assessment.patient_id)
            if patient:
                print(f"  Patient: {patient.first_name} {patient.last_name}")
            else:
                print("  ERROR: Patient not found!")
                continue
                
            print(f"  Protocol ID: {assessment.protocol_id}")
            print(f"  Date: {assessment.assessment_date}")
            
            # Make sure conducted_by_id is set properly
            if not assessment.conducted_by_id:
                assessment.conducted_by_id = nurse1.id
                print(f"  FIXING: Setting conducted_by_id to {nurse1.id} (nurse1)")
                
            # Make sure protocol_id is set correctly based on patient's protocol type
            protocol = Protocol.query.filter_by(protocol_type=patient.protocol_type).first()
            if protocol and assessment.protocol_id != protocol.id:
                print(f"  FIXING: Changing protocol_id from {assessment.protocol_id} to {protocol.id}")
                assessment.protocol_id = protocol.id
                    
            # Ensure high priority assessments are set properly
            if assessment.follow_up_needed and assessment.follow_up_priority == 'HIGH':
                if not assessment.follow_up_date:
                    # Set follow-up date to April 2, 2025
                    follow_up_date = datetime(2025, 4, 2, 10, 0, 0)
                    assessment.follow_up_date = follow_up_date
                    print(f"  FIXING: Setting follow_up_date to {follow_up_date}")
                    
        # Commit changes
        db.session.commit()
        print("\nChanges committed to database")

def check_permissions():
    """Check if nurses have permission to view patient assessments"""
    app = create_app()
    with app.app_context():
        # Get nurse1
        nurse1 = User.query.filter_by(username="nurse1").first()
        if not nurse1:
            print("ERROR: Could not find nurse1 user!")
            return
        
        print(f"Nurse1: {nurse1.first_name} {nurse1.last_name} (ID: {nurse1.id})")
        
        # Get all patients 
        patients = Patient.query.all()
        print(f"Found {len(patients)} patients")
        
        # Check which patients nurse1 has access to
        accessible_patients = []
        for patient in patients:
            has_access = (patient.primary_nurse_id == nurse1.id)
            print(f"Patient {patient.id}: {patient.first_name} {patient.last_name} - Accessible to nurse1: {has_access}")
            if has_access:
                accessible_patients.append(patient)
                
        # Check assessments for each accessible patient
        print(f"\nChecking assessments for {len(accessible_patients)} accessible patients:")
        for patient in accessible_patients:
            assessments = Assessment.query.filter_by(patient_id=patient.id).all()
            print(f"  Patient {patient.id}: {patient.first_name} {patient.last_name} - {len(assessments)} assessments")
            
            for assessment in assessments:
                print(f"    Assessment {assessment.id}: {assessment.assessment_date} - Protocol ID: {assessment.protocol_id}")
                
        # Check Mary Johnson specifically
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if mary:
            print(f"\nMary Johnson (ID: {mary.id}) - Primary nurse ID: {mary.primary_nurse_id}")
            
            # Ensure Mary's primary nurse is set correctly
            if mary.primary_nurse_id != nurse1.id:
                print(f"FIXING: Setting Mary's primary nurse to nurse1 (ID: {nurse1.id})")
                mary.primary_nurse_id = nurse1.id
                db.session.commit()
                print("Changes committed to database")

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    if command == "update":
        update_db_for_march25()
    elif command == "permissions":
        check_permissions()
    else:
        check_patients()