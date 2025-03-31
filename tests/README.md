# SteadwellOS Test Framework

This directory contains tests for the SteadwellOS palliative care platform.

## Test Structure

- `simple_test.py`: Basic application availability check (no dependencies)
- `http_test.py`: HTTP-based API tests (no browser dependencies)
- `ui_test.py`: UI tests through HTTP requests (no browser dependencies)
- `ui/`: Selenium-based UI tests (not recommended, requires ChromeDriver)

## Running Tests

### Basic Application Check

To check if the application is running correctly:

```bash
just check-app
```

This runs a simple script that verifies the application is up and accessible.

### HTTP API Tests

To run tests against the application's HTTP API endpoints:

```bash
just test-http
```

These tests verify that the application's API endpoints are working as expected.

The HTTP API tests cover:

- Protocols API (list and details)
- Patients API (list and details)
- Assessments API (list and details)
- Assessments Followups API
- Calls API
- Users API

### UI Tests (No Browser Required)

To run UI tests without requiring a browser:

```bash
just test-ui
```

These tests verify that the web interface is working correctly by checking HTML content.

### Run All Tests

To run all tests in sequence:

```bash
just test-all
```

This will run the application check, HTTP API tests, and UI tests in sequence.

The UI tests cover:

- Login page
- Protocols page
- Patients page
- Assessment creation page
- Assessment details page
- Protocol details page
- Calls page
- Dashboard page
- Follow-ups page

## Test Approach

Our testing approach is designed to be reliable and dependency-free:

1. **Basic Application Check**: Verifies that the application is running and endpoints are accessible
2. **HTTP API Tests**: Validates API endpoints and their responses with JWT authentication
3. **UI Tests**: Checks HTML content for expected elements and functionality with authenticated requests

All tests run without requiring browsers, Selenium, or ChromeDriver, making them much more reliable
and easier to run in any environment.

### Authentication

The tests use JWT authentication to validate protected endpoints:

1. Tests first check that the login endpoint works correctly
2. Then they authenticate using test credentials (typically nurse1/password123)
3. All subsequent requests include the JWT token in the Authorization header
4. This ensures that our tests work against the production API with authentication enabled

## Requirements

- Python 3.6+
- No additional dependencies required!

## Adding New Tests

1. For API tests, modify `http_test.py`
   - Use the `TestClient` class to make authenticated requests
   - The client will automatically add authentication headers

2. For UI tests, modify `ui_test.py`
   - Use `UITestClient` for authenticated page requests
   - Use the existing testing functions for page content validation
   
3. Make sure to add docstrings and comments