from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta

from app import db
from app.models.user import User, UserRole
from app.models.patient import Patient, ProtocolType
from app.models.call import Call, CallStatus
from app.models.assessment import Assessment, FollowUpPriority

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get date ranges
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    
    # Base patient query
    patient_query = Patient.query
    
    # Base call query
    call_query = Call.query
    
    # Base assessment query
    assessment_query = Assessment.query
    
    # Limit queries for nurses to their assigned patients
    if current_user.role == UserRole.NURSE:
        patient_query = patient_query.filter(Patient.primary_nurse_id == current_user_id)
        call_query = call_query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
        assessment_query = assessment_query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    # Get patient counts
    total_patients = patient_query.count()
    active_patients = patient_query.filter(Patient.is_active == True).count()
    
    # Count patients by protocol type
    protocol_counts = db.session.query(
        Patient.protocol_type, func.count(Patient.id)
    ).filter(
        Patient.is_active == True
    ).group_by(Patient.protocol_type).all()
    
    protocol_distribution = {
        protocol_type.value: 0 for protocol_type in ProtocolType
    }
    for protocol_type, count in protocol_counts:
        protocol_distribution[protocol_type.value] = count
    
    # Get call statistics
    today_calls = call_query.filter(
        Call.scheduled_time >= today,
        Call.scheduled_time < tomorrow
    ).count()
    
    completed_calls_today = call_query.filter(
        Call.status == CallStatus.COMPLETED,
        Call.end_time >= today,
        Call.end_time < tomorrow
    ).count()
    
    pending_calls = call_query.filter(
        Call.status == CallStatus.SCHEDULED
    ).count()
    
    # Get assessment statistics
    assessments_this_week = assessment_query.filter(
        Assessment.assessment_date >= week_start,
        Assessment.assessment_date < week_end
    ).count()
    
    urgent_followups = assessment_query.filter(
        Assessment.follow_up_needed == True,
        Assessment.follow_up_priority == FollowUpPriority.HIGH
    ).count()
    
    # Compile the summary
    summary = {
        "patients": {
            "total": total_patients,
            "active": active_patients,
            "by_protocol": protocol_distribution
        },
        "calls": {
            "today": today_calls,
            "completed_today": completed_calls_today,
            "pending": pending_calls
        },
        "assessments": {
            "this_week": assessments_this_week,
            "urgent_followups": urgent_followups
        }
    }
    
    return jsonify(summary), 200

@dashboard_bp.route('/upcoming-calls', methods=['GET'])
@jwt_required()
def get_upcoming_calls():
    """Get upcoming calls for the dashboard"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get upcoming scheduled calls
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    query = Call.query.filter(
        Call.status == CallStatus.SCHEDULED,
        Call.scheduled_time >= datetime.utcnow(),
        Call.scheduled_time < tomorrow
    )
    
    # Limit to nurse's patients if applicable
    if current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    # Get the calls
    calls = query.order_by(Call.scheduled_time).limit(10).all()
    
    # Format the response
    result = []
    for call in calls:
        result.append({
            "id": call.id,
            "patient_name": f"{call.patient.first_name} {call.patient.last_name}",
            "patient_id": call.patient.id,
            "scheduled_time": call.scheduled_time.isoformat(),
            "call_type": call.call_type,
            "protocol_type": call.patient.protocol_type.value
        })
    
    return jsonify(result), 200

@dashboard_bp.route('/urgent-followups', methods=['GET'])
@jwt_required()
def get_urgent_followups():
    """Get urgent follow-ups for the dashboard"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get assessments with urgent follow-ups
    query = Assessment.query.filter(
        Assessment.follow_up_needed == True,
        Assessment.follow_up_priority == FollowUpPriority.HIGH
    )
    
    # Limit to nurse's patients if applicable
    if current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    # Get the assessments
    assessments = query.order_by(Assessment.follow_up_date).limit(10).all()
    
    # Format the response
    result = []
    for assessment in assessments:
        result.append({
            "id": assessment.id,
            "patient_name": f"{assessment.patient.first_name} {assessment.patient.last_name}",
            "patient_id": assessment.patient.id,
            "assessment_date": assessment.assessment_date.isoformat(),
            "follow_up_date": assessment.follow_up_date.isoformat() if assessment.follow_up_date else None,
            "protocol_type": assessment.patient.protocol_type.value
        })
    
    return jsonify(result), 200

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent activity for the dashboard"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get recent completed calls
    call_query = Call.query.filter(
        Call.status == CallStatus.COMPLETED
    )
    
    # Get recent assessments
    assessment_query = Assessment.query
    
    # Limit to nurse's patients if applicable
    if current_user.role == UserRole.NURSE:
        call_query = call_query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
        assessment_query = assessment_query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    # Get the activities
    recent_calls = call_query.order_by(Call.end_time.desc()).limit(5).all()
    recent_assessments = assessment_query.order_by(Assessment.assessment_date.desc()).limit(5).all()
    
    # Format the response
    result = {
        "calls": [],
        "assessments": []
    }
    
    for call in recent_calls:
        result["calls"].append({
            "id": call.id,
            "patient_name": f"{call.patient.first_name} {call.patient.last_name}",
            "patient_id": call.patient.id,
            "timestamp": call.end_time.isoformat() if call.end_time else None,
            "call_type": call.call_type,
            "duration": call.duration
        })
    
    for assessment in recent_assessments:
        result["assessments"].append({
            "id": assessment.id,
            "patient_name": f"{assessment.patient.first_name} {assessment.patient.last_name}",
            "patient_id": assessment.patient.id,
            "timestamp": assessment.assessment_date.isoformat(),
            "protocol_type": assessment.patient.protocol_type.value,
            "follow_up_needed": assessment.follow_up_needed
        })
    
    return jsonify(result), 200