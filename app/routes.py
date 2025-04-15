"""
Web routes for the SteadywellOS application
These routes handle the frontend web pages and template rendering
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, current_app
import os

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Redirect to login page or dashboard if authenticated"""
    return redirect(url_for('web.dashboard'))

@web_bp.route('/login')
def login():
    """Render login page"""
    return render_template('login.html')

@web_bp.route('/dashboard')
def dashboard():
    """Render dashboard page"""
    return render_template('dashboard.html')

@web_bp.route('/patients')
def patients():
    """Render patients list page"""
    return render_template('patients.html')

@web_bp.route('/patients/new')
def new_patient():
    """Render new patient form"""
    return render_template('patients/new.html')

@web_bp.route('/patients/<int:patient_id>')
def patient_details(patient_id):
    """Render patient details page"""
    return render_template('patients/details.html', patient_id=patient_id)

@web_bp.route('/patients/<int:patient_id>/edit')
def edit_patient(patient_id):
    """Render patient edit form"""
    return render_template('patients/edit.html', patient_id=patient_id)

@web_bp.route('/calls')
def calls():
    """Render calls list page"""
    return render_template('calls.html')

@web_bp.route('/calls/schedule')
def schedule_call():
    """Render schedule call form"""
    return render_template('call_schedule.html')

@web_bp.route('/calls/<int:call_id>')
def call_details(call_id):
    """Render call details page"""
    return render_template('calls/details.html', call_id=call_id)

@web_bp.route('/calls/<int:call_id>/initiate')
def initiate_call(call_id):
    """Render call initiation page"""
    return render_template('calls/initiate.html', call_id=call_id)

@web_bp.route('/assessments')
def assessments():
    """Render assessments list page"""
    return render_template('assessments.html')

@web_bp.route('/assessments/new')
def new_assessment():
    """Render new assessment form"""
    patient_id = request.args.get('patient_id', '')
    # Log for debugging purposes
    print(f"Creating new assessment with patient_id: '{patient_id}'")
    return render_template('assessments/new.html', patient_id=patient_id)

@web_bp.route('/assessments/<int:assessment_id>')
def assessment_details(assessment_id):
    """Render assessment details page"""
    return render_template('assessment_detail.html', assessment_id=assessment_id)

@web_bp.route('/assessments/followups')
def followups():
    """Render followups list page"""
    return render_template('assessments/followups.html')

@web_bp.route('/protocols')
def protocols():
    """Render protocols list page"""
    return render_template('protocols/index.html')

@web_bp.route('/protocols/new')
def new_protocol():
    """Render new protocol form"""
    return render_template('protocols/new.html')

@web_bp.route('/protocols/<int:protocol_id>')
def protocol_details(protocol_id):
    """Render protocol details page"""
    return render_template('protocols/details.html', protocol_id=protocol_id)

@web_bp.route('/protocols/<int:protocol_id>/edit')
def edit_protocol(protocol_id):
    """Render protocol edit form"""
    return render_template('protocols/edit.html', protocol_id=protocol_id)

@web_bp.route('/profile')
def profile():
    """Render user profile page"""
    return render_template('profile.html')

@web_bp.route('/settings')
def settings():
    """Render settings page"""
    return render_template('settings.html')

@web_bp.route('/forgot-password')
def forgot_password():
    """Render forgot password page"""
    return render_template('forgot_password.html')

# Error handlers
@web_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@web_bp.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500

# Startup logs route
@web_bp.route('/startup-logs')
def startup_logs():
    """Display container startup logs"""
    return render_template('startup_logs.html')

# API endpoint to get startup logs
@web_bp.route('/api/startup-logs')
def api_startup_logs():
    """API endpoint to get startup logs"""
    # Import necessary modules
    import time
    import glob
    import socket
    import platform
    
    # Log for debugging
    print(f"API endpoint /api/startup-logs called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get environment information for the logs
    hostname = socket.gethostname()
    python_version = platform.python_version()
    system_info = f"Hostname: {hostname}, Python: {python_version}, OS: {platform.system()} {platform.release()}"
    
    # Check for startup logs in various locations
    startup_logs = ""
    log_files = [
        "/app/startup_log.txt",  # Primary log location
        "/tmp/startup_log.txt",   # Alternative location
        "/proc/1/fd/1"           # Docker stdout if running as PID 1
    ]
    
    # Find the first available log file
    log_file_found = None
    for log_file in log_files:
        print(f"Checking for log file at {log_file}")
        if os.path.exists(log_file):
            log_file_found = log_file
            print(f"Log file exists at {log_file}, attempting to read")
            try:
                with open(log_file, 'r') as f:
                    startup_logs = f.read()
                print(f"Startup logs read: {len(startup_logs)} characters")
                break
            except Exception as e:
                error_msg = f"Error reading log file {log_file}: {str(e)}"
                print(error_msg)
                startup_logs = error_msg
    
    # If no log file found, look for any log files in common directories
    if not log_file_found:
        print("No primary log files found, searching for any logs...")
        for log_pattern in ["/app/*.log", "/app/*.txt", "/tmp/*.log", "/tmp/startup*"]:
            log_matches = glob.glob(log_pattern)
            if log_matches:
                print(f"Found potential logs matching {log_pattern}: {log_matches}")
                try:
                    with open(log_matches[0], 'r') as f:
                        startup_logs = f"Found alternative log: {log_matches[0]}\n\n" + f.read()
                    print(f"Read alternative log file: {log_matches[0]}")
                    break
                except Exception as e:
                    print(f"Error reading alternative log: {str(e)}")
    
    # Try to get process information as a fallback
    process_info = ""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        process_info = f"""
Process Information:
- PID: {process.pid}
- Name: {process.name()}
- Status: {process.status()}
- Create Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(process.create_time()))}
- CPU Usage: {process.cpu_percent(interval=0.1)}%
- Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB
"""
    except Exception as e:
        process_info = f"Could not get process information: {str(e)}"
    
    # Check environment variables that would help diagnose startup issues
    env_info = ""
    important_vars = ["DEV_STATE", "FLASK_APP", "FLASK_ENV", "POSTGRES_DB", "POSTGRES_HOST"]
    for var in important_vars:
        env_info += f"{var}: {os.environ.get(var, 'Not set')}\n"
    
    # Determine if DEV_STATE=TEST, which is critical for DB initialization
    dev_state = os.environ.get("DEV_STATE", "Not set")
    db_init_expected = dev_state == "TEST"
    
    # Combine all information for a complete picture
    logs = f"""=== SYSTEM INFORMATION ===

{system_info}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
Path Checked: {', '.join(log_files)}
Log File Found: {log_file_found if log_file_found else 'None'}
DEV_STATE: {dev_state} (Database initialization {'expected' if db_init_expected else 'not expected'})

=== PROCESS INFORMATION ===
{process_info}

=== ENVIRONMENT VARIABLES ===
{env_info}
"""
    
    # Add startup logs if found
    if startup_logs:
        logs += "\n\n=== STARTUP LOG FILE ===\n\n"
        logs += startup_logs
    
    # Default message if no real logs found
    if not startup_logs and not process_info:
        logs += "\n\nNo detailed startup logs found. This could indicate the application started without errors or logs are being written to a different location."
        
        if dev_state != "TEST":
            logs += "\n\nNOTE: DEV_STATE is not set to TEST, so database initialization was likely skipped."
            logs += "\nThis is expected in production but could cause login failures if the database was not previously initialized."
    
    # Print final response size for debugging
    print(f"Sending response with {len(logs)} characters of log data")
    
    # Return response with logs
    return jsonify({
        "logs": logs, 
        "exists": True,
        "startup_logs_length": len(startup_logs),
        "system_info": system_info,
        "dev_state": dev_state,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })