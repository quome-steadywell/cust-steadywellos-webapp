/**
 * SteadywellOS - Palliative Care Coordination Platform
 * Main JavaScript File
 */

// Global variables
window.userToken = localStorage.getItem('auth_token') || null;
window.currentUser = JSON.parse(localStorage.getItem('current_user') || '{}');

// Check authentication on each page load
document.addEventListener('DOMContentLoaded', function() {
    // Skip auth check for login page
    if (window.location.pathname.includes('login')) {
        return;
    }

    // Redirect to login if no token
    if (!window.userToken) {
        window.location.href = '/login';
        return;
    }

    // Set user name in navbar
    if (currentUser && currentUser.full_name) {
        const userNameElement = document.getElementById('current-user-name');
        if (userNameElement) {
            userNameElement.textContent = currentUser.full_name;
        }
    }

    // Setup AJAX auth header globally
    setupAjaxHeaders();
});

/**
 * Setup AJAX headers for authentication
 */
function setupAjaxHeaders() {
    // For fetch API requests
    window.authFetch = (url, options = {}) => {
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${window.userToken}`,
                'Content-Type': 'application/json'
            }
        };

        // Merge default headers with provided headers
        const mergedOptions = {
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        return fetch(url, mergedOptions);
    };

    // For jQuery AJAX requests
    if (typeof $ !== 'undefined') {
        $.ajaxSetup({
            beforeSend: function(xhr) {
                if (window.userToken) {
                    xhr.setRequestHeader('Authorization', `Bearer ${window.userToken}`);
                }
            }
        });
    }
}

/**
 * Handle logout functionality
 */
function handleLogout() {
    // Call logout endpoint
    authFetch('/api/v1/auth/logout', {
        method: 'POST',
    }).finally(() => {
        // Clear local storage and redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        window.location.href = '/login';
    });
}

// Logout button event listener
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
});

/**
 * Format date to locale string
 * @param {string|Date} date - Date to format
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
function formatDate(date, options = {}) {
    if (!date) return '';

    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };

    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleDateString(undefined, { ...defaultOptions, ...options });
}

/**
 * Format time to locale string
 * @param {string|Date} date - Date to extract time from
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted time string
 */
function formatTime(date, options = {}) {
    if (!date) return '';

    const defaultOptions = {
        hour: '2-digit',
        minute: '2-digit'
    };

    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleTimeString(undefined, { ...defaultOptions, ...options });
}

/**
 * Format protocol type for display
 * @param {string} type - Protocol type
 * @returns {string} Formatted protocol type
 */
function formatProtocolType(type) {
    if (!type) return '';

    switch(type) {
        case 'cancer': return 'Cancer';
        case 'heart_failure': return 'Heart Failure';
        case 'copd': return 'COPD';
        case 'general': return 'General';
        default: return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
    }
}

/**
 * Get CSS class for protocol type
 * @param {string} type - Protocol type
 * @returns {string} CSS class name
 */
function getProtocolClass(type) {
    if (!type) return '';

    switch(type) {
        case 'cancer': return 'protocol-cancer';
        case 'heart_failure': return 'protocol-heart-failure';
        case 'copd': return 'protocol-copd';
        case 'general': return 'protocol-general';
        default: return '';
    }
}

/**
 * Format call type for display
 * @param {string} type - Call type
 * @returns {string} Formatted call type
 */
function formatCallType(type) {
    if (!type) return '';

    switch(type) {
        case 'assessment': return 'Assessment';
        case 'follow_up': return 'Follow-up';
        case 'medication_check': return 'Medication Check';
        default: return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
    }
}

/**
 * Get CSS class for call status
 * @param {string} status - Call status
 * @returns {string} CSS class name
 */
function getCallStatusClass(status) {
    if (!status) return '';

    switch(status) {
        case 'scheduled': return 'call-scheduled';
        case 'in_progress': return 'call-in-progress';
        case 'completed': return 'call-completed';
        case 'missed': return 'call-missed';
        case 'cancelled': return 'call-cancelled';
        default: return '';
    }
}

/**
 * Show alert message
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} containerId - ID of the container to append alert to
 * @param {number} duration - Duration in ms before auto-hiding (0 for no auto-hide)
 */
function showAlert(message, type = 'info', containerId = 'alert-container', duration = 5000) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Alert container #${containerId} not found`);
        return;
    }

    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show`;
    alertEl.role = 'alert';
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Append to container
    container.appendChild(alertEl);

    // Auto-hide if duration > 0
    if (duration > 0) {
        setTimeout(() => {
            alertEl.classList.remove('show');
            setTimeout(() => alertEl.remove(), 150);
        }, duration);
    }

    return alertEl;
}

/**
 * Format number for display
 * @param {number} num - Number to format
 * @param {object} options - Intl.NumberFormat options
 * @returns {string} Formatted number string
 */
function formatNumber(num, options = {}) {
    if (num === null || num === undefined) return '';

    return new Intl.NumberFormat(undefined, options).format(num);
}

/**
 * Calculate age from date of birth
 * @param {string|Date} dob - Date of birth
 * @returns {number} Age in years
 */
function calculateAge(dob) {
    if (!dob) return null;

    const dobDate = typeof dob === 'string' ? new Date(dob) : dob;
    const today = new Date();

    let age = today.getFullYear() - dobDate.getFullYear();
    const monthDiff = today.getMonth() - dobDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dobDate.getDate())) {
        age--;
    }

    return age;
}

/**
 * Generic form submission handler
 * @param {HTMLFormElement} form - Form element
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {function} successCallback - Function to call on success
 * @param {function} errorCallback - Function to call on error
 */
function handleFormSubmit(form, endpoint, method = 'POST', successCallback, errorCallback) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Collect form data
        const formData = new FormData(form);
        const jsonData = {};

        formData.forEach((value, key) => {
            // Handle nested objects with array notation: example[key]
            if (key.includes('[') && key.includes(']')) {
                const mainKey = key.substring(0, key.indexOf('['));
                const subKey = key.substring(key.indexOf('[') + 1, key.indexOf(']'));

                if (!jsonData[mainKey]) {
                    jsonData[mainKey] = {};
                }

                jsonData[mainKey][subKey] = value;
            } else {
                jsonData[key] = value;
            }
        });

        try {
            // Send request
            const response = await authFetch(endpoint, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An error occurred');
            }

            const data = await response.json();

            // Call success callback
            if (typeof successCallback === 'function') {
                successCallback(data);
            }

        } catch (error) {
            console.error('Form submission error:', error);

            // Call error callback
            if (typeof errorCallback === 'function') {
                errorCallback(error);
            } else {
                // Default error handling
                showAlert(error.message || 'An error occurred', 'danger');
            }
        }
    });
}
