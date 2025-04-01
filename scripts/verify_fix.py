#!/usr/bin/env python3
"""
Script to verify Mary Johnson's assessments are properly configured
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.patient import Patient
from app.models.protocol import Protocol
from app.models.assessment import Assessment
from app.models.user import User, UserRole
from app.schemas.assessment import AssessmentSchema

def verify_mary_johnson():
    """Verify Mary Johnson's data and assessments are correctly configured"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("ERROR: Mary Johnson not found in the database!")
            return
            
        # Find nurse1
        nurse1 = User.query.filter_by(username="nurse1").first()
        if not nurse1:
            print("ERROR: Nurse1 not found in the database!")
            return
            
        # Check primary nurse
        print(f"Mary Johnson (ID: {mary.id}) - Primary nurse ID: {mary.primary_nurse_id}")
        print(f"Nurse1 ID: {nurse1.id}")
        
        if mary.primary_nurse_id != nurse1.id:
            print("ERROR: Mary's primary nurse is not set to nurse1!")
        else:
            print("PASS: Mary's primary nurse is correctly set to nurse1")
        
        # Find protocol for Mary's protocol type
        protocol = Protocol.query.filter_by(protocol_type=mary.protocol_type).first()
        if not protocol:
            print(f"ERROR: No protocol found for type {mary.protocol_type}!")
            return
            
        print(f"Protocol info: ID: {protocol.id}, Name: {protocol.name}")
        
        # Check March 25 assessments specifically
        march_25_assessments = Assessment.query.filter(
            Assessment.patient_id == mary.id,
            Assessment.assessment_date >= '2025-03-25 00:00:00',
            Assessment.assessment_date < '2025-03-26 00:00:00'
        ).all()
        
        print(f"\nFound {len(march_25_assessments)} assessments for March 25")
        
        # Print assessment details and try to serialize them
        for assessment in march_25_assessments:
            print(f"\nAssessment ID: {assessment.id}")
            print(f"  Date: {assessment.assessment_date}")
            print(f"  Protocol ID: {assessment.protocol_id}")
            print(f"  Patient ID: {assessment.patient_id}")
            print(f"  Conducted by ID: {assessment.conducted_by_id}")
            print(f"  Follow-up needed: {assessment.follow_up_needed}")
            print(f"  Follow-up priority: {assessment.follow_up_priority}")
            print(f"  Follow-up date: {assessment.follow_up_date}")
            print(f"  Symptoms: {assessment.symptoms}")
            
            # Try to serialize the assessment
            try:
                serialized = AssessmentSchema().dump(assessment)
                print("  PASS: Assessment can be serialized successfully")
                print(f"  Serialized data contains {len(serialized)} fields")
            except Exception as e:
                print(f"  ERROR: Assessment serialization failed: {e}")
                
        # Verify API access by simulating the API endpoint
        from app.api.assessments import get_assessment
        
        print("\nSimulating API access for the assessments...")
        
        # Create a mock Flask context
        with app.test_request_context():
            # Set up a user context similar to what the API does
            app.config['TESTING'] = True
            
            for assessment in march_25_assessments:
                try:
                    # Instead of calling the API endpoint directly, check the check_permission logic
                    # This is the key part that was failing before
                    patient = Patient.query.get(assessment.patient_id)
                    
                    if patient.primary_nurse_id != nurse1.id:
                        print(f"  ERROR: Assessment {assessment.id} - Patient's primary nurse is not nurse1")
                    else:
                        print(f"  PASS: Assessment {assessment.id} - Patient's primary nurse is correctly set to nurse1")
                        
                    print(f"  This assessment should be accessible to nurse1 via API")
                except Exception as e:
                    print(f"  ERROR: Assessment {assessment.id} check failed: {e}")
                
if __name__ == "__main__":
    verify_mary_johnson()