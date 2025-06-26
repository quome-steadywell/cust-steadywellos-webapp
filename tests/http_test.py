#!/usr/bin/env python3
"""
HTTP-based tests for the SteadwellOS application.
These tests use simple HTTP requests and don't require Selenium.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import time
import ssl

# Disable SSL certificate verification for local testing
ssl._create_default_https_context = ssl._create_unverified_context


class TestClient:
    def __init__(self, base_url="http://0.0.0.0:8080"):
        self.base_url = base_url
        self.cookies = {}
        self.access_token = None

    def login(self, username="nurse1", password="password123"):
        """Login and get JWT token"""
        print(f"📝 Logging in as {username}")
        login_data = {"username": username, "password": password}

        success, response = self.post("/api/v1/auth/login", login_data, expected_status=200)
        if not success:
            print("❌ Login failed")
            return False

        try:
            data = json.loads(response)
            self.access_token = data.get("access_token")
            if not self.access_token:
                print("❌ No access token in response")
                return False

            print(f"✅ Login successful, token obtained")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error parsing login response: {e}")
            return False

    def get(self, path, expected_status=200):
        url = f"{self.base_url}{path}"
        print(f"GET {url}")

        req = urllib.request.Request(url)

        # Add cookies if available
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            req.add_header("Cookie", cookie_str)

        # Add JWT token if available
        if self.access_token and not path.startswith("/api/v1/auth/login"):
            req.add_header("Authorization", f"Bearer {self.access_token}")

        try:
            response = urllib.request.urlopen(req)
            status = response.getcode()
            content = response.read().decode("utf-8")

            # Save any cookies
            if response.info().get("Set-Cookie"):
                for cookie in response.info().get_all("Set-Cookie"):
                    name, value = cookie.split(";")[0].split("=", 1)
                    self.cookies[name] = value

            if status != expected_status:
                print(f"❌ Unexpected status: {status}, expected: {expected_status}")
                return False, None

            print(f"✅ Status: {status}")
            return True, content

        except urllib.error.HTTPError as e:
            if e.code == expected_status:
                print(f"✅ Status: {e.code} (expected)")
                return True, None
            else:
                print(f"❌ HTTP Error: {e.code}")
                return False, None
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def post(self, path, data, expected_status=200):
        url = f"{self.base_url}{path}"
        print(f"POST {url}")

        # Encode data as JSON
        data_bytes = json.dumps(data).encode("utf-8")

        # Create request with headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Add JWT token if available and not login request
        if self.access_token and not path.startswith("/api/v1/auth/login"):
            headers["Authorization"] = f"Bearer {self.access_token}"

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        # Add cookies if available
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            req.add_header("Cookie", cookie_str)

        try:
            response = urllib.request.urlopen(req)
            status = response.getcode()
            content = response.read().decode("utf-8")

            # Save any cookies
            if response.info().get("Set-Cookie"):
                for cookie in response.info().get_all("Set-Cookie"):
                    name, value = cookie.split(";")[0].split("=", 1)
                    self.cookies[name] = value

            if status != expected_status:
                print(f"❌ Unexpected status: {status}, expected: {expected_status}")
                return False, None

            print(f"✅ Status: {status}")
            return True, content

        except urllib.error.HTTPError as e:
            if e.code == expected_status:
                print(f"✅ Status: {e.code} (expected)")
                return True, None
            else:
                print(f"❌ HTTP Error: {e.code}")
                return False, None
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None


def run_basic_tests(base_url="http://0.0.0.0:8080"):
    """Run basic HTTP tests against the application"""
    client = TestClient(base_url)

    # Test 1: Check if the server is running
    print("\n🔍 Test 1: Application is up and running")
    success, _ = client.get("/", expected_status=200)
    if not success:
        print("❌ Application doesn't appear to be running")
        return False
    print("✅ Application is up and running")

    # Test 2: Login with valid credentials
    print("\n🔍 Test 2: Authentication")
    if not client.login(username="nurse1", password="password123"):
        print("❌ Authentication failed")
        return False
    print("✅ Authentication successful")

    # Test 3: Access protocols API
    print("\n🔍 Test 3: Protocols API")
    success, content = client.get("/api/v1/protocols/", expected_status=200)
    if not success:
        print("❌ Failed to access protocols API")
        return False

    try:
        protocols = json.loads(content)
        if not isinstance(protocols, list):
            print("❌ Protocols API didn't return a list")
            return False

        print(f"✅ Protocols API returned {len(protocols)} protocols")
    except json.JSONDecodeError:
        print("❌ Protocols API didn't return valid JSON")
        return False

    # Test 4: Access patients API
    print("\n🔍 Test 4: Patients API")
    success, content = client.get("/api/v1/patients/", expected_status=200)
    if not success:
        print("❌ Failed to access patients API")
        return False

    try:
        patients = json.loads(content)
        if not isinstance(patients, list):
            print("❌ Patients API didn't return a list")
            return False

        print(f"✅ Patients API returned {len(patients)} patients")
    except json.JSONDecodeError:
        print("❌ Patients API didn't return valid JSON")
        return False

    # Test 5: Get specific protocols
    if len(protocols) > 0:
        protocol_id = protocols[0]["id"]
        print(f"\n🔍 Test 5: Get protocol details for ID {protocol_id}")
        success, content = client.get(f"/api/v1/protocols/{protocol_id}", expected_status=200)
        if not success:
            print("❌ Failed to access protocol details")
            return False

        try:
            protocol = json.loads(content)
            print(f"✅ Retrieved protocol: {protocol['name']}")
        except (json.JSONDecodeError, KeyError):
            print("❌ Protocol details didn't return valid JSON or missing name field")
            return False

    # Test 6: Access assessments API
    print("\n🔍 Test 6: Assessments API")
    success, content = client.get("/api/v1/assessments/", expected_status=200)
    if not success:
        print("❌ Failed to access assessments API")
        return False

    try:
        assessments = json.loads(content)
        if not isinstance(assessments, list):
            print("❌ Assessments API didn't return a list")
            return False

        print(f"✅ Assessments API returned {len(assessments)} assessments")
    except json.JSONDecodeError:
        print("❌ Assessments API didn't return valid JSON")
        return False

    # Test 7: Access calls API
    print("\n🔍 Test 7: Calls API")
    success, content = client.get("/api/v1/calls/", expected_status=200)
    if not success:
        print("❌ Failed to access calls API")
        return False

    try:
        calls = json.loads(content)
        if not isinstance(calls, list):
            print("❌ Calls API didn't return a list")
            return False

        print(f"✅ Calls API returned {len(calls)} calls")
    except json.JSONDecodeError:
        print("❌ Calls API didn't return valid JSON")
        return False

    # Test 8: Get specific patient if available
    if len(patients) > 0:
        patient_id = patients[0]["id"]
        print(f"\n🔍 Test 8: Get patient details for ID {patient_id}")
        success, content = client.get(f"/api/v1/patients/{patient_id}", expected_status=200)
        if not success:
            print("❌ Failed to access patient details")
            return False

        try:
            patient = json.loads(content)
            print(f"✅ Retrieved patient: {patient['first_name']} {patient['last_name']}")
        except (json.JSONDecodeError, KeyError):
            print("❌ Patient details didn't return valid JSON or missing name fields")
            return False

    # Test 9: Access users API
    print("\n🔍 Test 9: Users API")
    success, content = client.get("/api/v1/users/", expected_status=200)
    if not success:
        print("❌ Failed to access users API")
        return False

    try:
        users = json.loads(content)
        if not isinstance(users, list):
            print("❌ Users API didn't return a list")
            return False

        print(f"✅ Users API returned {len(users)} users")
    except json.JSONDecodeError:
        print("❌ Users API didn't return valid JSON")
        return False

    # Test 10: Access assessments followups API
    print("\n🔍 Test 10: Assessments Followups API")
    success, content = client.get("/api/v1/assessments/followups", expected_status=200)
    if not success:
        print("❌ Failed to access assessments followups API")
        return False

    try:
        followups = json.loads(content)
        if not isinstance(followups, list):
            print("❌ Assessments followups API didn't return a list")
            return False

        print(f"✅ Assessments followups API returned {len(followups)} followups")
    except json.JSONDecodeError:
        print("❌ Assessments followups API didn't return valid JSON")
        return False

    # Test 11: Access specific assessment
    if len(patients) > 0 and assessments and len(assessments) > 0:
        assessment_id = assessments[0]["id"]
        print(f"\n🔍 Test 11: Get assessment details for ID {assessment_id}")
        success, content = client.get(f"/api/v1/assessments/{assessment_id}", expected_status=200)
        if not success:
            print("❌ Failed to access assessment details")
            return False

        try:
            assessment = json.loads(content)
            print(f"✅ Retrieved assessment for patient: {assessment['patient']['full_name']}")

            # Test that protocol data is accessible
            if "protocol_id" in assessment:
                protocol_id = assessment["protocol_id"]
                print(f"Checking protocol {protocol_id} is accessible...")
                success, protocol_content = client.get(f"/api/v1/protocols/{protocol_id}", expected_status=200)
                if success:
                    print(f"✅ Associated protocol is accessible")
                else:
                    print(f"❌ Failed to access associated protocol")

        except (json.JSONDecodeError, KeyError):
            print("❌ Assessment details didn't return valid JSON or missing fields")
            return False

    print("\n🎉 All basic HTTP tests passed!")
    return True


if __name__ == "__main__":
    print("Running HTTP tests for SteadwellOS application...")
    success = run_basic_tests()
    if not success:
        sys.exit(1)
    else:
        print("✅ HTTP tests completed successfully!")
        sys.exit(0)
