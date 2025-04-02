#!/usr/bin/env python3
"""
Script to check assessments for each patient
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.patient import Patient
from app.models.assessment import Assessment

def check_assessments_by_patient():
    """Check all assessments for each patient"""
    app = create_app()
    with app.app_context():
        patients = Patient.query.all()
        
        for patient in patients:
            print(f"\n{'=' * 40}")
            print(f"Patient: {patient.first_name} {patient.last_name} (ID: {patient.id})")
            print(f"MRN: {patient.mrn}")
            print(f"Protocol Type: {patient.protocol_type}")
            
            # Get assessments for this patient
            assessments = Assessment.query.filter_by(patient_id=patient.id).all()
            print(f"\nFound {len(assessments)} assessments for {patient.first_name} {patient.last_name}")
            
            for assessment in assessments:
                print(f"\nAssessment ID: {assessment.id}")
                print(f"  Date: {assessment.assessment_date}")
                print(f"  Protocol ID: {assessment.protocol_id}")
                print(f"  Follow-up needed: {assessment.follow_up_needed}")
                if assessment.follow_up_needed:
                    print(f"  Follow-up date: {assessment.follow_up_date}")
                    print(f"  Follow-up priority: {assessment.follow_up_priority}")

if __name__ == "__main__":
    check_assessments_by_patient()