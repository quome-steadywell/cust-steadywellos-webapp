#!/usr/bin/env python3
"""
Script to test API endpoints
"""

import requests
import json
import sys

def test_assessment_api(assessment_id):
    """Test assessment API endpoint"""
    response = requests.get(f"http://localhost:8080/api/v1/assessments/{assessment_id}")
    if response.status_code == 200:
        print("API request successful!")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Check critical fields
        if 'protocol' in data and data['protocol']:
            print(f"\nProtocol info found: {data['protocol']['name']}")
        else:
            print("\nWARNING: Protocol field is missing or empty!")
            
        if 'patient' in data and data['patient']:
            print(f"Patient info found: {data['patient']['full_name']}")
        else:
            print("WARNING: Patient field is missing or empty!")
            
        return data
    else:
        print(f"API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        assessment_id = sys.argv[1]
    else:
        assessment_id = 130  # default to Mary Johnson's assessment
    
    test_assessment_api(assessment_id)