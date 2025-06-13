#!/usr/bin/env python3
"""
Script to check assessment API
"""

import os
import sys
import json
from pathlib import Path
import requests
from flask import jsonify

# Add the parent directory to the path so we can import src
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.assessment import Assessment
from src.schemas.assessment import AssessmentSchema
from src.models.patient import Patient
from src.models.protocol import Protocol

def check_assessment_api(assessment_id):
    """Check assessment API for a specific ID"""
    app = create_app()
    with app.app_context():
        # Get assessment directly from database
        assessment = Assessment.query.get(assessment_id)
        if not assessment:
            print(f"Assessment ID {assessment_id} not found in database!")
            return
        
        # Try to serialize the assessment
        try:
            assessment_schema = AssessmentSchema()
            serialized_assessment = assessment_schema.dump(assessment)
            print("Assessment serialized successfully:")
            print(json.dumps(serialized_assessment, indent=2))
            
            # Check specific fields that might cause issues
            print("\nVerification of key fields:")
            print(f"protocol_id: {assessment.protocol_id}")
            print(f"patient_id: {assessment.patient_id}")
            
            # Check if protocol field is properly populated in serialized output
            if 'protocol' not in serialized_assessment or not serialized_assessment['protocol']:
                print("WARNING: 'protocol' field is missing or empty in serialized output!")
            else:
                print(f"protocol field populated correctly: {serialized_assessment['protocol']['name']}")
                
            # Check if patient field is properly populated in serialized output
            if 'patient' not in serialized_assessment or not serialized_assessment['patient']:
                print("WARNING: 'patient' field is missing or empty in serialized output!")
            else:
                print(f"patient field populated correctly: {serialized_assessment['patient']['full_name']}")
            
            # Check conducted_by field
            if 'conducted_by' not in serialized_assessment or not serialized_assessment['conducted_by']:
                print("WARNING: 'conducted_by' field is missing or empty in serialized output!")
            else:
                print(f"conducted_by field populated correctly: {serialized_assessment['conducted_by']['full_name']}")
                
            # Check permissions for nurse1
            from src.models.user import User, UserRole
            nurse1 = User.query.filter_by(username="nurse1").first()
            if nurse1:
                # Get patient
                patient = Patient.query.get(assessment.patient_id)
                if patient:
                    has_permission = patient.primary_nurse_id == nurse1.id
                    print(f"Nurse1 has permission to view this assessment: {has_permission}")
                    
                    # Now try to directly call the API endpoint function
                    from src.api.assessments import get_assessment
                    from flask import jsonify, Response
                    import types
                    
                    # Create a simulated request with nurse1 as current user
                    class MockAuth:
                        @staticmethod
                        def jwt_required(*args, **kwargs):
                            def decorator(f):
                                def wrapped(*args, **kwargs):
                                    # Skip authentication
                                    return f(*args, **kwargs)
                                return wrapped
                            return decorator
                            
                        @staticmethod
                        def get_jwt_identity():
                            return nurse1.id
                    
                    # Temporarily replace jwt functions
                    original_jwt_required = app.extensions.get('flask_jwt_extended').jwt_required
                    original_get_jwt_identity = app.extensions.get('flask_jwt_extended').get_jwt_identity
                    
                    try:
                        app.extensions.get('flask_jwt_extended').jwt_required = MockAuth.jwt_required
                        app.extensions.get('flask_jwt_extended').get_jwt_identity = MockAuth.get_jwt_identity
                        
                        # Create a mock request context
                        with app.test_request_context(f'/api/v1/assessments/{assessment_id}'):
                            response = get_assessment(assessment_id)
                            
                            # If response is a tuple, it likely has an error status
                            if isinstance(response, tuple):
                                print(f"API endpoint returned an error: {response}")
                            elif isinstance(response, Response):
                                print(f"API endpoint returned successfully with status {response.status_code}")
                            else:
                                print(f"API endpoint returned: {response}")
                    
                    finally:
                        # Restore original functions
                        app.extensions.get('flask_jwt_extended').jwt_required = original_jwt_required
                        app.extensions.get('flask_jwt_extended').get_jwt_identity = original_get_jwt_identity
                
        except Exception as e:
            print(f"Error serializing assessment: {str(e)}")
            import traceback
            traceback.print_exc()

def check_multiple_assessments():
    """Check specific assessment IDs with problems"""
    print("\n\n====== CHECKING MULTIPLE ASSESSMENT RECORDS ======")
    app = create_app()
    with app.app_context():
        # Check working vs non-working assessments
        assessment_ids = [106, 107, 108]  # Check the assessments failing in the app
        
        for aid in assessment_ids:
            # Get assessment directly from database
            assessment = Assessment.query.get(aid)
            if not assessment:
                print(f"\n\nAssessment ID {aid} not found in database!")
                continue
            
            print(f"\n\n==== ASSESSMENT {aid} ====")
            print(f"Patient ID: {assessment.patient_id}")
            print(f"Protocol ID: {assessment.protocol_id}")
            print(f"Conducted By ID: {assessment.conducted_by_id}")
            print(f"Call ID: {assessment.call_id}")
            
            # Check protocol relationship
            from src.models.protocol import Protocol
            from src.models.patient import Patient
            
            protocol = None
            if assessment.protocol_id:
                protocol = Protocol.query.get(assessment.protocol_id)
            
            print(f"\nProtocol Link Status: {'VALID' if protocol else 'MISSING'}")
            if protocol:
                print(f"Protocol Name: {protocol.name}")
                print(f"Protocol Type: {protocol.protocol_type}")
            else:
                print("WARNING: Protocol object is None or missing")
                # Check if protocol ID exists in Protocol table
                if assessment.protocol_id:
                    found = Protocol.query.filter(Protocol.id == assessment.protocol_id).first()
                    print(f"Protocol ID {assessment.protocol_id} exists in Protocol table: {'Yes' if found else 'No'}")
            
            # Check patient
            patient = Patient.query.get(assessment.patient_id)
            if patient:
                print(f"\nPatient: {patient.full_name} (MRN: {patient.mrn})")
            else:
                print("\nWARNING: Patient record missing")
            
            # Try serialization with schema
            try:
                schema = AssessmentSchema()
                result = schema.dump(assessment)
                print("\nSerialization result:")
                print(f"Protocol included in serialized data: {'Yes' if result.get('protocol') else 'No'}")
                if result.get('protocol'):
                    print(f"Protocol data: {result['protocol']}")
                else:
                    print("Protocol data is missing in serialized output!")
            except Exception as e:
                print(f"Serialization error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        assessment_id = int(sys.argv[1])
        check_assessment_api(assessment_id)
    else:
        # Run our comparative analysis
        check_multiple_assessments()