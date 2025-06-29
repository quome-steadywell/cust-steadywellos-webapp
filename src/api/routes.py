"""
Web routes for the SteadywellOS application
These routes handle the frontend web pages and template rendering
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
)
import os
import json

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """Redirect to login page or dashboard if authenticated"""
    return redirect(url_for("web.dashboard"))


@web_bp.route("/login")
def login():
    """Render login page"""
    return render_template("login.html")


@web_bp.route("/dashboard")
def dashboard():
    """Render dashboard page"""
    return render_template("dashboard.html")


@web_bp.route("/patients")
def patients():
    """Render patients list page"""
    return render_template("patients.html")


@web_bp.route("/patients/new")
def new_patient():
    """Render new patient form"""
    return render_template("patients/new.html")


@web_bp.route("/patients/<int:patient_id>")
def patient_details(patient_id):
    """Render patient details page"""
    return render_template("patients/details.html", patient_id=patient_id)


@web_bp.route("/patients/<int:patient_id>/edit")
def edit_patient(patient_id):
    """Render patient edit form"""
    return render_template("patients/edit.html", patient_id=patient_id)


@web_bp.route("/calls")
def calls():
    """Render calls list page"""
    return render_template("calls.html")


@web_bp.route("/calls/schedule")
def schedule_call():
    """Render schedule call form"""
    return render_template("call_schedule.html")


@web_bp.route("/backup")
def backup():
    """Render database backup page (admin only)"""
    return render_template("backup.html")


@web_bp.route("/calls/<int:call_id>")
def call_details(call_id):
    """Render call details page"""
    return render_template("calls/details.html", call_id=call_id)


@web_bp.route("/calls/<int:call_id>/initiate")
def initiate_call(call_id):
    """Render call initiation page"""
    return render_template("calls/initiate.html", call_id=call_id)


@web_bp.route("/assessments")
def assessments():
    """Render assessments list page"""
    return render_template("assessments.html")


@web_bp.route("/assessments/new")
def new_assessment():
    """Render new assessment form"""
    patient_id = request.args.get("patient_id", "")
    # Log for debugging purposes
    print(f"Creating new assessment with patient_id: '{patient_id}'")
    return render_template("assessments/new.html", patient_id=patient_id)


@web_bp.route("/assessments/<int:assessment_id>")
def assessment_details(assessment_id):
    """Render assessment details page"""
    return render_template("assessment_detail.html", assessment_id=assessment_id)


@web_bp.route("/assessments/followups")
def followups():
    """Render followups list page"""
    return render_template("assessments/followups.html")


@web_bp.route("/protocols")
def protocols():
    """Render protocols list page"""
    return render_template("protocols/index.html")


@web_bp.route("/protocols/new")
def new_protocol():
    """Render new protocol form"""
    return render_template("protocols/new.html")


@web_bp.route("/protocols/<int:protocol_id>")
def protocol_details(protocol_id):
    """Render protocol details page"""
    return render_template("protocols/details.html", protocol_id=protocol_id)


@web_bp.route("/protocols/<int:protocol_id>/edit")
def edit_protocol(protocol_id):
    """Render protocol edit form"""
    return render_template("protocols/edit.html", protocol_id=protocol_id)


@web_bp.route("/profile")
def profile():
    """Render user profile page"""
    return render_template("profile.html")


@web_bp.route("/settings")
def settings():
    """Render settings page"""
    return render_template("settings.html")


@web_bp.route("/forgot-password")
def forgot_password():
    """Render forgot password page"""
    return render_template("forgot_password.html")


# Error handlers
@web_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template("errors/404.html"), 404


@web_bp.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template("errors/500.html"), 500
