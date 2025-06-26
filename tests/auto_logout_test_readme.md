# Auto-Logout Test

This document explains the auto-logout test implementation for the SteadwellOS Palliative Care Platform.

## Purpose

The auto-logout test (`test_autologout.py`) verifies that the system properly implements security measures to automatically log out inactive users, clear browser data, and prevent unauthorized access through browser history.

## What It Tests

1. **Auto-Logout Mechanism**: Confirms that the auto-logout JavaScript functionality is properly implemented, including inactivity detection and redirect to login page.

2. **Local Storage Clearing**: Verifies that user data stored in the browser's local storage is cleared during auto-logout to prevent security risks.

3. **Back Button Security**: Ensures that users cannot use the browser's back button to access protected pages after being logged out.

4. **Role-Specific Auto-Logout**: Verifies that auto-logout works for all user roles (admin, nurse, and physician) with appropriate timeout settings.

## How It Works

Since this is an HTTP-based test rather than a full browser test with Selenium, it uses a static analysis approach:

1. It examines the HTML/JavaScript to verify that the auto-logout mechanisms are properly implemented.
2. It checks for presence of specific code patterns that:
   - Track user inactivity
   - Redirect to login page after timeout
   - Clear local storage data
   - Prevent access via browser history
3. It tests each user role (admin, nurse, physician) to ensure all have the auto-logout functionality.

## Running the Test

```bash
# Run only the auto-logout test
just test-autologout

# Run as part of all tests
just test-all
```

## Test Configuration

The auto-logout test uses the system's configured timeout values from the API endpoint:
- `/api/v1/auth/session-settings`

These values are defined in `config/config.py`:
- `AUTO_LOGOUT_TIME`: Minutes until auto-logout (default: 30)
- `WARNING_TIME`: Minutes before auto-logout to show warning (default: 5)

## User Roles Tested

The test verifies auto-logout functionality for all standard user roles:

- **Admin**: System administrators with full access
- **Nurse**: Healthcare professionals providing patient care
- **Physician**: Doctors who oversee patient treatment plans

For each role, the test:
1. Logs in with role-specific credentials
2. Verifies access to the dashboard
3. Checks that auto-logout mechanisms are present and properly implemented
4. Verifies the timeout settings are correctly applied

## Notes for Developers

1. This test verifies the implementation of auto-logout rather than the actual runtime behavior. A true end-to-end test would require Selenium or similar browser automation.

2. If you modify the auto-logout functionality, ensure you update this test accordingly.

3. If you add new user roles, update the `roles` dictionary in the `test_role_specific_autologout` function to include them.

4. When implementing client-side security features like auto-logout, remember they are convenience features rather than true security boundaries. Always enforce session expiration on the server side as well.
