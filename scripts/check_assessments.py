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

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentSchema

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
            from app.models.user import User, UserRole
            nurse1 = User.query.filter_by(username="nurse1").first()
            if nurse1:
                # Get patient
                patient = Patient.query.get(assessment.patient_id)
                if patient:
                    has_permission = patient.primary_nurse_id == nurse1.id
                    print(f"Nurse1 has permission to view this assessment: {has_permission}")
                    
                    # Now try to directly call the API endpoint function
                    from app.api.assessments import get_assessment
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_assessments.py <assessment_id>")
        sys.exit(1)
        
    assessment_id = int(sys.argv[1])
    check_assessment_api(assessment_id)