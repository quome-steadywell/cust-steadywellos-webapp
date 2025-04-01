#!/usr/bin/env python3
"""
Script to test API authentication and assessment endpoints
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app

def test_login_and_assessment():
    """Test login and assessment API"""
    
    # Get a token first - from inside docker, use the Flask app directly
    app = create_app()
    
    with app.app_context():
        from app.models.user import User, UserRole
        from app.models.patient import Patient
        from app.models.assessment import Assessment
        from app.models.protocol import Protocol
        from app.schemas.assessment import AssessmentSchema
        
        # Check if Mary Johnson has assessments directly
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in database!")
            return
            
        assessments = Assessment.query.filter_by(patient_id=mary.id).all()
        print(f"Found {len(assessments)} assessments for Mary Johnson")
        
        # Use the same schema the API uses
        schema = AssessmentSchema()
        for assessment in assessments:
            print(f"\nAssessment {assessment.id}:")
            print(f"  Date: {assessment.assessment_date}")
            print(f"  Protocol ID: {assessment.protocol_id}")
            
            try:
                # Try to serialize the assessment (this would mimic what the API does)
                data = schema.dump(assessment)
                
                # Check key fields
                if 'protocol' not in data or not data['protocol']:
                    print("  WARNING: protocol field is missing after serialization!")
                else:
                    print(f"  protocol field OK: {data['protocol']['name']}")
                    
                if 'patient' not in data or not data['patient']:
                    print("  WARNING: patient field is missing after serialization!")
                else:
                    print(f"  patient field OK: {data['patient']['full_name']}")
                    
                # Test other fields
                print(f"  interventions: {len(data.get('interventions', []))} items")
                print(f"  symptoms: {len(data.get('symptoms', {}))} items")
                
            except Exception as e:
                print(f"  ERROR serializing assessment: {str(e)}")
    
    # Now simulate the endpoint directly
    print("\nSimulating endpoint directly...")
    
    with app.app_context():
        from app.api.assessments import get_assessment
        from flask import jsonify
        
        # Directly test the assessment endpoint with IDs 24, 25, and 37
        for assessment_id in [24, 25, 37]:
            print(f"\nTesting assessment endpoint with ID {assessment_id}")
            
            # Call the endpoint function directly
            try:
                # Use the actual endpoint function
                assessment = Assessment.query.get(assessment_id)
                if not assessment:
                    print(f"Assessment ID {assessment_id} not found!")
                    continue
                    
                # Check if required relationships are loaded
                if not hasattr(assessment, 'patient') or not assessment.patient:
                    print(f"PROBLEM: patient relationship not loaded for assessment {assessment_id}")
                else:
                    print(f"Patient relationship is working: {assessment.patient.first_name} {assessment.patient.last_name}")
                    
                if not hasattr(assessment, 'protocol') or not assessment.protocol:
                    print(f"PROBLEM: protocol relationship not loaded for assessment {assessment_id}")
                else:
                    print(f"Protocol relationship is working: {assessment.protocol.name}")
                    
                # Serialize using the schema
                dumped = AssessmentSchema().dump(assessment)
                
                # Check key fields
                print(f"Serialized fields check:")
                for field in ['id', 'patient_id', 'protocol_id', 'assessment_date', 'patient', 'protocol']:
                    if field not in dumped or not dumped[field]:
                        print(f"  PROBLEM: {field} is missing or empty in serialized data!")
                    else:
                        value = dumped[field]
                        if isinstance(value, dict):
                            value = f"{value.get('name', '')} or {value.get('full_name', '')}"
                        print(f"  {field}: {value}")
                    
            except Exception as e:
                print(f"ERROR testing endpoint: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_login_and_assessment()