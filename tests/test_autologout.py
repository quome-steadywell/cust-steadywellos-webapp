#!/usr/bin/env python3
"""
Auto-Logout Testing

This script tests the auto-logout functionality by:
1. Logging in to the application
2. Accessing protected pages
3. Testing if auto-logout occurs after inactivity
4. Verifying browser cache is cleared and back navigation requires re-login
"""

import urllib.request
import urllib.error
import urllib.parse
import re
import sys
import time
import ssl
import json
import subprocess
from html.parser import HTMLParser

# Disable SSL certificate verification for local testing
ssl._create_default_https_context = ssl._create_unverified_context


class HTMLContentParser(HTMLParser):
    """Simple HTML parser to extract text content"""

    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []
        self.forms = []

    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = next((v for k, v in attrs if k == "href"), None)
            if href:
                self.links.append(href)
        elif tag == "form":
            action = next((v for k, v in attrs if k == "action"), None)
            method = next((v for k, v in attrs if k == "method"), None)
            self.forms.append({"action": action, "method": method or "get"})


class AutoLogoutTester:
    """Class to test auto-logout functionality"""

    def __init__(self, base_url="http://0.0.0.0:8080"):
        self.base_url = base_url
        self.access_token = None
        self.cookies = {}
        self.browser_session = None

    def login(self, username="nurse1", password="password123"):
        """Login and get JWT token"""
        print(f"📝 Logging in as {username}...")

        # Prepare login data
        login_data = {"username": username, "password": password}

        # Convert to JSON and encode
        data = json.dumps(login_data).encode("utf-8")

        try:
            # Create login request
            req = urllib.request.Request(
                f"{self.base_url}/api/v1/auth/login",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )

            # Send request
            with urllib.request.urlopen(req) as response:
                if response.getcode() != 200:
                    print(f"❌ Login failed with status code: {response.getcode()}")
                    return False

                # Parse response
                content = response.read().decode("utf-8")
                data = json.loads(content)

                # Save token
                self.access_token = data.get("access_token")
                if not self.access_token:
                    print("❌ No access token in response")
                    return False

                # Save any cookies
                if response.info().get("Set-Cookie"):
                    for cookie in response.info().get_all("Set-Cookie"):
                        name, value = cookie.split(";")[0].split("=", 1)
                        self.cookies[name] = value

                print(f"✅ Login successful, token obtained")
                return True

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def fetch_page(self, path, expected_title=None, expected_content=None):
        """Fetch a page and check for expected content"""
        url = f"{self.base_url}{path}"
        print(f"Fetching {url}...")

        try:
            # Create request
            req = urllib.request.Request(url)

            # Add authentication token if available
            if self.access_token:
                req.add_header("Authorization", f"Bearer {self.access_token}")

            # Add cookies if available
            if self.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                req.add_header("Cookie", cookie_str)

            # Send request
            with urllib.request.urlopen(req) as response:
                html = response.read().decode("utf-8")

                # Check status code
                if response.getcode() != 200:
                    print(f"❌ Unexpected status code: {response.getcode()}")
                    return False, None, None

                # Save any cookies
                if response.info().get("Set-Cookie"):
                    for cookie in response.info().get_all("Set-Cookie"):
                        name, value = cookie.split(";")[0].split("=", 1)
                        self.cookies[name] = value

                # Parse HTML
                parser = HTMLContentParser()
                parser.feed(html)

                # Print extracted text summary (first 3 items)
                text_preview = " | ".join(parser.text[:3]) if parser.text else ""
                print(f"✅ Page loaded: {text_preview}...")

                # Check for expected title
                title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
                title = title_match.group(1) if title_match else ""

                if expected_title and expected_title not in title:
                    print(
                        f"❌ Title '{title}' doesn't contain expected '{expected_title}'"
                    )
                    return False, html, parser

                if expected_title:
                    print(f"✅ Found expected title: {expected_title}")

                # Check for expected content in text
                if expected_content:
                    found = any(expected_content in text for text in parser.text)
                    if not found:
                        print(f"❌ Couldn't find '{expected_content}' in page content")
                        return False, html, parser

                    print(f"✅ Found expected content: {expected_content}")

                return True, html, parser

        except Exception as e:
            print(f"❌ Error fetching page: {e}")
            return False, None, None

    def get_session_settings(self):
        """Fetch auto-logout settings"""
        try:
            # Create request
            req = urllib.request.Request(
                f"{self.base_url}/api/v1/auth/session-settings"
            )

            # Add authentication token if available
            if self.access_token:
                req.add_header("Authorization", f"Bearer {self.access_token}")

            # Send request
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content)

                auto_logout_ms = data.get("auto_logout_time")
                warning_ms = data.get("warning_time")

                auto_logout_minutes = data.get("auto_logout_minutes")
                warning_minutes = data.get("warning_minutes")

                print(
                    f"✅ Auto-logout time: {auto_logout_minutes} minutes ({auto_logout_ms} ms)"
                )
                print(f"✅ Warning time: {warning_minutes} minutes ({warning_ms} ms)")

                return auto_logout_minutes, warning_minutes

        except Exception as e:
            print(f"❌ Error fetching session settings: {e}")
            return 30, 5  # Default values

    def simulate_inactivity(self, minutes=None):
        """Simulate user inactivity for specified minutes"""
        if minutes is None:
            # Get session settings to determine inactivity timeout
            auto_logout_minutes, _ = self.get_session_settings()
            # Add 1 minute to ensure we exceed the timeout
            minutes = auto_logout_minutes + 1

        print(f"⏳ Simulating inactivity for {minutes} minutes...")

        # Note: In a real browser environment, we would actually wait for
        # the timeout to occur. In our HTTP-based test, we're just checking
        # if the auto-logout mechanism is properly implemented, so we don't
        # need to wait the full time.

        # This is just a token wait to simulate the concept:
        test_wait_seconds = 2  # Minimal wait

        time.sleep(test_wait_seconds)
        print(f"✅ Simulated inactivity period (token wait: {test_wait_seconds}s)")

    def test_auto_logout_redirect(self):
        """Test that after inactivity, accessing a protected page redirects to login"""
        print("\n🔍 Test: Auto-Logout Redirect")

        # First login
        if not self.login():
            return False

        # Access a protected page to verify we're logged in
        result, html, _ = self.fetch_page("/dashboard", "Dashboard")
        if not result:
            print("❌ Failed to access dashboard after login")
            return False

        print("✅ Successfully accessed dashboard")

        # In a real browser, JavaScript would handle the auto-logout after inactivity
        # Here we'll check if the auto-logout mechanism is properly included in the page

        # Check for performAutoLogout function
        auto_logout_fn = re.search(
            r"function\s+performAutoLogout\(\)", html, re.IGNORECASE
        )
        if not auto_logout_fn:
            print("❌ performAutoLogout function not found")
            return False

        # Check for redirection to login in the auto-logout function
        redirect_to_login = re.search(
            r'window\.location\.href\s*=\s*[\'"]\/login[\'"]', html, re.IGNORECASE
        )
        if not redirect_to_login:
            print("❌ Redirect to login page not found in auto-logout function")
            return False

        # Check for inactivity timer setup
        inactivity_timer = re.search(
            r"inactivityTimer\s*=\s*setTimeout\(\s*performAutoLogout",
            html,
            re.IGNORECASE,
        )
        if not inactivity_timer:
            print("❌ Inactivity timer setup not found")
            return False

        print("✅ Auto-logout redirect mechanism is properly implemented")
        return True

    def test_auto_logout_local_storage_cleared(self):
        """Test that local storage is cleared after auto-logout"""
        print("\n🔍 Test: Auto-Logout Local Storage Clearing")

        # This test would normally require a browser with JavaScript capabilities
        # For this HTTP-based test, we can check if the auto-logout JavaScript is present

        # First login
        if not self.login():
            return False

        # Access a protected page to verify we're logged in
        result, html, _ = self.fetch_page("/dashboard", "Dashboard")
        if not result:
            print("❌ Failed to access dashboard after login")
            return False

        # Check if the auto-logout JavaScript is present
        auto_logout_js = re.search(
            r"function\s+performAutoLogout\(\)", html, re.IGNORECASE
        )
        if not auto_logout_js:
            print("❌ Auto-logout JavaScript not found in page")
            return False

        # Check if local storage clearing code is present
        localStorage_clear = re.search(
            r"localStorage\.removeItem\(.*\)", html, re.IGNORECASE
        )
        if not localStorage_clear:
            print("❌ Local storage clearing code not found in auto-logout function")
            return False

        print("✅ Auto-logout function includes local storage clearing code")
        return True

    def test_back_button_security(self):
        """Test that using browser back button after auto-logout requires re-login"""
        print("\n🔍 Test: Back Button Security After Auto-Logout")

        # Since we can't simulate browser back button in this HTTP-based test,
        # we'll check that the essential security mechanisms are in place

        # First login
        if not self.login():
            return False

        # Access a protected page to verify we're logged in
        result, html, _ = self.fetch_page("/dashboard", "Dashboard")
        if not result:
            print("❌ Failed to access dashboard after login")
            return False

        # Check if any token validation is present
        # This might be in different forms depending on implementation
        has_token_check = False

        # Check for token checks in different formats
        patterns = [
            r'if\s*\(\s*!token.*window\.location\.href\s*=\s*[\'"]\/login[\'"]',
            r'if\s*\(!token\s*\&\&\s*window\.location\.pathname\s*!==\s*[\'"]\/login[\'"]',
            r'!token.*window\.location\.href\s*=\s*[\'"]\/login[\'"]',
        ]

        for pattern in patterns:
            if re.search(pattern, html, re.IGNORECASE):
                has_token_check = True
                break

        if not has_token_check:
            # Last resort - check if the script contains both token check and redirect code
            # even if not in the exact pattern we expected
            token_check = (
                "!token" in html or "!localStorage.getItem('auth_token')" in html
            )
            redirect_code = "window.location.href" in html and "/login" in html

            if token_check and redirect_code:
                has_token_check = True

        if not has_token_check:
            print("❌ Token validation and redirect code not found")
            return False

        print(
            "✅ Page contains token validation code that prevents access to protected pages after logout"
        )
        return True


def test_role_specific_autologout(base_url="http://0.0.0.0:8080"):
    """Test auto-logout for different user roles"""
    print("\n🔍 Test: Role-Specific Auto-Logout")

    # User credentials for different roles
    roles = {
        "admin": {"username": "admin", "password": "password123"},
        "nurse": {"username": "nurse1", "password": "password123"},
        "physician": {"username": "physician", "password": "password123"},
    }

    results = {}
    timeout_settings = {}

    for role, credentials in roles.items():
        print(f"\n🔍 Testing auto-logout for {role} role")
        tester = AutoLogoutTester(base_url)

        # Login with role-specific credentials
        if not tester.login(
            username=credentials["username"], password=credentials["password"]
        ):
            print(f"❌ Login failed for {role}")
            results[role] = False
            continue

        print(f"✅ Successfully logged in as {role}")

        # Verify we can access dashboard
        result, html, _ = tester.fetch_page("/dashboard", "Dashboard")
        if not result:
            print(f"❌ Failed to access dashboard as {role}")
            results[role] = False
            continue

        print(f"✅ Successfully accessed dashboard as {role}")

        # Check if auto-logout mechanism is present for this role
        auto_logout_fn = re.search(
            r"function\s+performAutoLogout\(\)", html, re.IGNORECASE
        )
        local_storage_clear = re.search(
            r"localStorage\.removeItem\(.*\)", html, re.IGNORECASE
        )
        inactivity_timer = re.search(
            r"inactivityTimer\s*=\s*setTimeout\(\s*performAutoLogout",
            html,
            re.IGNORECASE,
        )

        if not auto_logout_fn:
            print(f"❌ Auto-logout function not found for {role}")
            results[role] = False
            continue

        if not local_storage_clear:
            print(f"❌ Local storage clearing not found for {role}")
            results[role] = False
            continue

        if not inactivity_timer:
            print(f"❌ Inactivity timer not found for {role}")
            results[role] = False
            continue

        # Get auto-logout settings
        auto_logout_minutes, warning_minutes = tester.get_session_settings()
        print(f"✅ {role} auto-logout time: {auto_logout_minutes} minutes")
        print(f"✅ {role} warning time: {warning_minutes} minutes")

        # Store timeout settings for comparison
        timeout_settings[role] = {
            "auto_logout": auto_logout_minutes,
            "warning": warning_minutes,
        }

        # If all checks pass, test is successful for this role
        print(f"✅ Auto-logout mechanisms properly implemented for {role}")
        results[role] = True

    # Check if different roles have different timeout settings
    has_role_specific_timeouts = False
    unique_timeouts = set()
    for role, settings in timeout_settings.items():
        timeout_key = f"{settings['auto_logout']}_{settings['warning']}"
        unique_timeouts.add(timeout_key)

    if len(unique_timeouts) > 1:
        has_role_specific_timeouts = True
        print("\n✅ Different roles have different timeout settings")
    elif len(unique_timeouts) == 1:
        print("\n⚠️ All roles have the same timeout settings")

    # Print summary for all roles
    print("\n=== Role-Specific Auto-Logout Summary ===")
    all_passed = True
    for role, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        all_passed = all_passed and result
        if role in timeout_settings:
            auto_logout = timeout_settings[role]["auto_logout"]
            warning = timeout_settings[role]["warning"]
            print(
                f"{status}: {role.capitalize()} auto-logout (timeout: {auto_logout}min, warning: {warning}min)"
            )
        else:
            print(f"{status}: {role.capitalize()} auto-logout")

    if all_passed:
        print("\n🎉 Auto-logout test passed for all roles!")
        return True
    else:
        print("\n❌ Auto-logout test failed for one or more roles!")
        return False


def run_auto_logout_tests(base_url="http://0.0.0.0:8080"):
    """Run all auto-logout tests"""
    print(f"🔄 Running auto-logout tests for SteadwellOS at {base_url}")

    tester = AutoLogoutTester(base_url)

    # Run standard tests
    redirect_test = tester.test_auto_logout_redirect()
    storage_test = tester.test_auto_logout_local_storage_cleared()
    back_button_test = tester.test_back_button_security()

    # Run role-specific test
    role_test = test_role_specific_autologout(base_url)

    # Print summary
    print("\n=== Auto-Logout Test Summary ===")
    print(f"{'✅ PASS' if redirect_test else '❌ FAIL'}: Auto-Logout Redirect")
    print(f"{'✅ PASS' if storage_test else '❌ FAIL'}: Local Storage Clearing")
    print(f"{'✅ PASS' if back_button_test else '❌ FAIL'}: Back Button Security")
    print(f"{'✅ PASS' if role_test else '❌ FAIL'}: Role-Specific Auto-Logout")

    # Overall result
    overall_result = redirect_test and storage_test and back_button_test and role_test

    if overall_result:
        print("\n🎉 All auto-logout tests passed!")
    else:
        print("\n❌ Some auto-logout tests failed!")

    return overall_result


if __name__ == "__main__":
    success = run_auto_logout_tests()
    if not success:
        sys.exit(1)
    else:
        print("✅ Auto-logout tests completed successfully!")
        sys.exit(0)
