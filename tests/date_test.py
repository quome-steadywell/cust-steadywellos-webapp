#!/usr/bin/env python3
"""
Date Handling Tests - No Selenium required

This script tests the consistent date handling throughout the application,
particularly focusing on weekly assessments counting and display.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import time
import ssl
import re
from datetime import datetime, timedelta

# Disable SSL certificate verification for local testing
ssl._create_default_https_context = ssl._create_unverified_context

class DateTestClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.cookies = {}
        self.access_token = None
    
    def login(self, username="nurse1", password="password123"):
        """Login and get JWT token"""
        print(f"📝 Logging in as {username}")
        login_data = {
            "username": username,
            "password": password
        }
        
        success, response = self.post("/api/v1/auth/login", login_data, expected_status=200)
        if not success:
            print("❌ Login failed")
            return False
        
        try:
            data = json.loads(response)
            self.access_token = data.get('access_token')
            if not self.access_token:
                print("❌ No access token in response")
                return False
                
            print(f"✅ Login successful, token obtained")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error parsing login response: {e}")
            return False
    
    def get(self, path, expected_status=200):
        """Make a GET request to the API"""
        url = f"{self.base_url}{path}"
        print(f"GET {url}")
        
        req = urllib.request.Request(url)
        
        # Add cookies if available
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            req.add_header("Cookie", cookie_str)
        
        # Add JWT token if available
        if self.access_token and not path.startswith('/api/v1/auth/login'):
            req.add_header('Authorization', f'Bearer {self.access_token}')
        
        try:
            response = urllib.request.urlopen(req)
            status = response.getcode()
            content = response.read().decode('utf-8')
            
            # Save any cookies
            if response.info().get('Set-Cookie'):
                for cookie in response.info().get_all('Set-Cookie'):
                    name, value = cookie.split(';')[0].split('=', 1)
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
                # Try to get error details
                try:
                    error_details = e.read().decode('utf-8')
                    print(f"❌ HTTP Error: {e.code} - {error_details}")
                except:
                    print(f"❌ HTTP Error: {e.code}")
                return False, None
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None
    
    def post(self, path, data, expected_status=200):
        """Make a POST request to the API"""
        url = f"{self.base_url}{path}"
        print(f"POST {url}")
        
        # Encode data as JSON
        data_bytes = json.dumps(data).encode('utf-8')
        
        # Create request with headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add JWT token if available and not login request
        if self.access_token and not path.startswith('/api/v1/auth/login'):
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        req = urllib.request.Request(
            url, 
            data=data_bytes,
            headers=headers,
            method='POST'
        )
        
        # Add cookies if available
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            req.add_header("Cookie", cookie_str)
        
        try:
            response = urllib.request.urlopen(req)
            status = response.getcode()
            content = response.read().decode('utf-8')
            
            # Save any cookies
            if response.info().get('Set-Cookie'):
                for cookie in response.info().get_all('Set-Cookie'):
                    name, value = cookie.split(';')[0].split('=', 1)
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
                # Try to get error details
                try:
                    error_details = e.read().decode('utf-8')
                    print(f"❌ HTTP Error: {e.code} - {error_details}")
                except:
                    print(f"❌ HTTP Error: {e.code}")
                return False, None
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, None

    def fetch_page(self, path, expected_title=None, expected_content=None):
        """Fetch an HTML page and check its content"""
        url = f"{self.base_url}{path}"
        print(f"Fetching {url}...")
        
        try:
            # Create request
            req = urllib.request.Request(url)
            
            # Add authentication token if available
            if self.access_token:
                req.add_header('Authorization', f'Bearer {self.access_token}')
                
            # Add cookies if available
            if self.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                req.add_header("Cookie", cookie_str)
            
            # Send request
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                
                # Check status code
                if response.getcode() != 200:
                    print(f"❌ Unexpected status code: {response.getcode()}")
                    return False, None
                    
                # Save any cookies
                if response.info().get('Set-Cookie'):
                    for cookie in response.info().get_all('Set-Cookie'):
                        name, value = cookie.split(';')[0].split('=', 1)
                        self.cookies[name] = value
                
                # Check for expected title
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                title = title_match.group(1) if title_match else ""
                
                if expected_title and expected_title not in title:
                    print(f"❌ Title '{title}' doesn't contain expected '{expected_title}'")
                    return False, None
                
                if expected_title:
                    print(f"✅ Found expected title: {expected_title}")
                
                # Check for expected content
                if expected_content and expected_content not in html:
                    print(f"❌ Couldn't find '{expected_content}' in page content")
                    return False, None
                
                if expected_content:
                    print(f"✅ Found expected content: {expected_content}")
                
                return True, html
        
        except urllib.error.HTTPError as e:
            # Try to get error details
            try:
                error_details = e.read().decode('utf-8')
                print(f"❌ HTTP Error: {e.code} - {error_details}")
            except:
                print(f"❌ HTTP Error: {e.code}")
            return False, None
        except Exception as e:
            print(f"❌ Error fetching page: {e}")
            return False, None

def get_week_start_date():
    """Get the first day (Sunday) of current week according to app logic"""
    today = datetime.now()
    days_since_sunday = today.weekday() + 1 % 7  # Convert to Sunday=0 basis
    return today - timedelta(days=days_since_sunday)

def format_date(date_obj):
    """Format date for API requests"""
    return date_obj.strftime('%Y-%m-%dT00:00:00')

def test_dashboard_weekly_assessments(client):
    """Test weekly assessments count on dashboard"""
    print("\n🔍 Test 1: Dashboard Weekly Assessments Count")
    
    # Get dashboard summary from API
    success, content = client.get("/api/v1/dashboard/summary", expected_status=200)
    if not success:
        print("❌ Failed to get dashboard summary")
        return False
    
    try:
        summary = json.loads(content)
        weekly_count = summary["assessments"]["this_week"]
        print(f"✅ Dashboard reports {weekly_count} weekly assessments")
    except (json.JSONDecodeError, KeyError):
        print("❌ Invalid dashboard summary data")
        return False
    
    # Now calculate the expected count by querying assessments directly
    week_start = get_week_start_date()
    week_end = week_start + timedelta(days=7)
    
    # Format dates for API
    from_date = format_date(week_start)
    to_date = format_date(week_end)
    
    # Get assessments for this week
    success, content = client.get(f"/api/v1/assessments/?from_date={from_date}&to_date={to_date}", expected_status=200)
    if not success:
        print("❌ Failed to get assessments for date range")
        return False
    
    try:
        assessments = json.loads(content)
        actual_count = len(assessments)
        print(f"✅ Assessments API returns {actual_count} assessments for this week")
        
        # Compare counts
        if weekly_count == actual_count:
            print(f"✅ Dashboard count ({weekly_count}) matches assessments API count ({actual_count})")
            return True
        else:
            print(f"❌ Dashboard count ({weekly_count}) does not match assessments API count ({actual_count})")
            return False
    except json.JSONDecodeError:
        print("❌ Invalid assessments data")
        return False

def test_dashboard_ui_consistency(client):
    """Test consistency between dashboard API and assessments API"""
    print("\n🔍 Test 2: Dashboard API and Assessments API Consistency")
    
    # Get dashboard data from the API
    success, content = client.get("/api/v1/dashboard/summary", expected_status=200)
    if not success:
        print("❌ Failed to get dashboard summary")
        return False
        
    try:
        dashboard_data = json.loads(content)
        weekly_count = dashboard_data["assessments"]["this_week"]
        print(f"✅ Dashboard API reports {weekly_count} weekly assessments")
    except (json.JSONDecodeError, KeyError):
        print("❌ Invalid dashboard summary data")
        return False
    
    # Now check the assessments API with the same date range
    week_start = get_week_start_date()
    week_end = week_start + timedelta(days=7)
    
    # Format dates for API
    from_date = format_date(week_start)
    to_date = format_date(week_end)
    
    # Query assessments API
    success, content = client.get(f"/api/v1/assessments/?from_date={from_date}&to_date={to_date}", expected_status=200)
    if not success:
        print("❌ Failed to get assessments for date range")
        return False
    
    try:
        assessments = json.loads(content)
        actual_count = len(assessments)
        print(f"✅ Assessments API shows {actual_count} assessments for this week")
        
        # Verify consistency
        if weekly_count == actual_count:
            print(f"✅ Dashboard API count ({weekly_count}) matches assessments API count ({actual_count})")
            return True
        else:
            print(f"❌ Dashboard API count ({weekly_count}) does not match assessments API count ({actual_count})")
            return False
    except json.JSONDecodeError:
        print("❌ Invalid assessments data")
        return False

def test_weekly_assessment_boundary_cases(client):
    """Test boundary cases for weekly assessment counts"""
    print("\n🔍 Test 3: Weekly Assessment Boundary Cases")
    
    # Get dashboard summary
    success, content = client.get("/api/v1/dashboard/summary", expected_status=200)
    if not success:
        print("❌ Failed to get dashboard summary")
        return False
    
    try:
        summary = json.loads(content)
        weekly_count = summary["assessments"]["this_week"]
        print(f"✅ Dashboard reports {weekly_count} weekly assessments")
    except (json.JSONDecodeError, KeyError):
        print("❌ Invalid dashboard summary data")
        return False
    
    # Calculate the current week boundaries
    today = datetime.now()
    
    # Calculate last week's Sunday
    days_since_sunday = today.weekday() + 1 % 7  # Convert to Sunday=0 basis
    this_sunday = today - timedelta(days=days_since_sunday)
    last_sunday = this_sunday - timedelta(days=7)
    next_sunday = this_sunday + timedelta(days=7)
    
    # Format dates for API
    last_week_start = format_date(last_sunday)
    this_week_start = format_date(this_sunday)
    next_week_start = format_date(next_sunday)
    
    # Query for last week's assessments
    success, content = client.get(f"/api/v1/assessments/?from_date={last_week_start}&to_date={this_week_start}", expected_status=200)
    if not success:
        print("❌ Failed to get last week's assessments")
        return False
    
    last_week_assessments = json.loads(content)
    print(f"✅ Found {len(last_week_assessments)} assessments for last week")
    
    # Query for this week's assessments
    success, content = client.get(f"/api/v1/assessments/?from_date={this_week_start}&to_date={next_week_start}", expected_status=200)
    if not success:
        print("❌ Failed to get this week's assessments")
        return False
    
    this_week_assessments = json.loads(content)
    print(f"✅ Found {len(this_week_assessments)} assessments for this week")
    
    # Verify that this week's count matches the dashboard
    if len(this_week_assessments) == weekly_count:
        print(f"✅ Dashboard count ({weekly_count}) matches API count for this week ({len(this_week_assessments)})")
        return True
    else:
        print(f"❌ Dashboard count ({weekly_count}) does not match API count for this week ({len(this_week_assessments)})")
        return False

def test_sunday_inclusion(client):
    """Test that Sunday assessments are properly included in the weekly count"""
    print("\n🔍 Test 4: Sunday Assessment Inclusion")
    
    # Get dashboard summary
    success, content = client.get("/api/v1/dashboard/summary", expected_status=200)
    if not success:
        print("❌ Failed to get dashboard summary")
        return False
    
    try:
        summary = json.loads(content)
        weekly_count = summary["assessments"]["this_week"]
        print(f"✅ Dashboard reports {weekly_count} weekly assessments")
    except (json.JSONDecodeError, KeyError):
        print("❌ Invalid dashboard summary data")
        return False
    
    # Calculate the current week start (Sunday)
    today = datetime.now()
    days_since_sunday = today.weekday() + 1 % 7  # Convert to Sunday=0 basis
    this_sunday = today - timedelta(days=days_since_sunday)
    next_sunday = this_sunday + timedelta(days=7)
    monday = this_sunday + timedelta(days=1)
    
    # Format dates for API
    sunday_start = format_date(this_sunday)
    monday_start = format_date(monday)
    next_week_start = format_date(next_sunday)
    
    # Query for Sunday's assessments only
    success, content = client.get(f"/api/v1/assessments/?from_date={sunday_start}&to_date={monday_start}", expected_status=200)
    if not success:
        print("❌ Failed to get Sunday's assessments")
        return False
    
    sunday_assessments = json.loads(content)
    print(f"✅ Found {len(sunday_assessments)} assessments for Sunday")
    
    # Query for Monday through Saturday
    success, content = client.get(f"/api/v1/assessments/?from_date={monday_start}&to_date={next_week_start}", expected_status=200)
    if not success:
        print("❌ Failed to get Monday-Saturday assessments")
        return False
    
    weekday_assessments = json.loads(content)
    print(f"✅ Found {len(weekday_assessments)} assessments for Monday-Saturday")
    
    # The sum should equal the dashboard count
    total_count = len(sunday_assessments) + len(weekday_assessments)
    if total_count == weekly_count:
        print(f"✅ Dashboard count ({weekly_count}) matches combined count ({total_count})")
        return True
    else:
        print(f"❌ Dashboard count ({weekly_count}) does not match combined count ({total_count})")
        return False

def run_date_tests(base_url="http://localhost:5000"):
    """Run all date handling tests"""
    print("Running date handling tests for SteadwellOS application...")
    
    # Create client and login
    client = DateTestClient(base_url)
    if not client.login():
        print("❌ Authentication failed, cannot run tests")
        return False
    
    # Run all tests
    test_results = [
        test_dashboard_weekly_assessments(client),
        test_dashboard_ui_consistency(client),
        test_weekly_assessment_boundary_cases(client),
        test_sunday_inclusion(client)
    ]
    
    # Print summary
    print("\n=== Test Summary ===")
    test_names = [
        "Dashboard Weekly Assessments Count",
        "Dashboard API and Assessments API Consistency",
        "Weekly Assessment Boundary Cases",
        "Sunday Assessment Inclusion"
    ]
    
    for i, result in enumerate(test_results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_names[i]}")
    
    # Overall result
    if all(test_results):
        print("\n🎉 All date handling tests passed!")
        return True
    else:
        print("\n❌ Some date handling tests failed!")
        return False

if __name__ == "__main__":
    success = run_date_tests()
    if not success:
        sys.exit(1)
    else:
        print("✅ Date handling tests completed successfully!")
        sys.exit(0)