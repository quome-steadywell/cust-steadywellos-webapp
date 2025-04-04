#!/usr/bin/env python
"""
Check API response for assessments
"""

import requests
import json
import sys
from flask import Flask
from flask_jwt_extended import create_access_token
import datetime

# Create a demo token directly
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'demo-secret-key'  # This is just for demo
from flask_jwt_extended import JWTManager
jwt = JWTManager(app)

with app.app_context():
    # Create a token that expires in 1 hour
    expires = datetime.timedelta(hours=1)
    access_token = create_access_token(identity={"id": 1, "role": "ADMIN"}, expires_delta=expires)
    print(f"Generated token: {access_token}")

# Make a request to the assessments API (use web for Docker service name)
print("\nChecking API access...")
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://web:5000/api/v1/assessments/', headers=headers)
print(f"Status code: {response.status_code}")

# Try to parse JSON
try:
    data = response.json()
    print(f"Data type: {type(data)}")
    print(f"Length: {len(data) if isinstance(data, list) else 'Not a list'}")
    if isinstance(data, list) and len(data) > 0:
        print(f"Sample first item: {json.dumps(data[0], indent=2)}")
    else:
        print(f"Full response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print(f"Raw response: {response.text}")

# Check patients API to see if that's working
print("\nChecking patients API...")
response = requests.get('http://web:5000/api/v1/patients/', headers=headers)
print(f"Status code: {response.status_code}")

try:
    data = response.json()
    print(f"Patients data type: {type(data)}")
    print(f"Patients length: {len(data) if isinstance(data, list) else 'Not a list'}")
    if isinstance(data, list) and len(data) > 0:
        print(f"First patient: {data[0].get('first_name')} {data[0].get('last_name')}")
except Exception as e:
    print(f"Error parsing patients JSON: {e}")

# Check followups API
print("\nChecking followups API...")
response = requests.get('http://web:5000/api/v1/assessments/followups', headers=headers)
print(f"Status code: {response.status_code}")

try:
    data = response.json()
    print(f"Followups data type: {type(data)}")
    print(f"Followups length: {len(data) if isinstance(data, list) else 'Not a list'}")
except Exception as e:
    print(f"Error parsing followups JSON: {e}")
    print(f"Raw response: {response.text}")