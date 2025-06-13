from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta

from src import db
from src.models.user import User, UserRole
from src.models.patient import Patient
from src.models.protocol import Protocol
from src.models.assessment import Assessment, FollowUpPriority
from src.models.call import Call
from src.schemas.assessment import AssessmentSchema, AssessmentListSchema, AssessmentUpdateSchema
from src.utils.decorators import roles_required, audit_action
from src.utils import get_date_bounds
from src.models.audit_log import AuditLog
from src.core.rag_service import process_assessment

assessments_bp = Blueprint('assessments', __name__)

@assessments_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_assessments():
    """Get all assessments with optional filtering"""
    # Get the current user from JWT token if available
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id) if current_user_id else None
    
    # Get query parameters
    patient_id = request.args.get('patient_id', type=int)
    protocol_type = request.args.get('protocol_type')
    follow_up_needed = request.args.get('follow_up_needed')
    follow_up_priority = request.args.get('follow_up_priority')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    limit = request.args.get('limit', type=int)
    
    
    # Start with base query with eager loading of relationships to avoid N+1 queries
    query = Assessment.query.options(
        db.joinedload(Assessment.patient),
        db.joinedload(Assessment.protocol),
        db.joinedload(Assessment.conducted_by)
    )
    
    
    # Filter by patient if specified
    if patient_id:
        query = query.filter(Assessment.patient_id == patient_id)
        
        # Verify permissions (nurses can only see their assigned patients)
        if current_user and current_user.role == UserRole.NURSE:
            patient = Patient.query.get(patient_id)
            if not patient or patient.primary_nurse_id != current_user.id:
                return jsonify({"error": "Unauthorized to view this patient's assessments"}), 403
    # If no patient is specified and user is a nurse, only show their patients
    elif current_user and current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user.id)
    
    # Apply protocol type filter if provided
    if protocol_type:
        query = query.join(Protocol).filter(Protocol.protocol_type == protocol_type)
    
    # Filter by follow-up status
    if follow_up_needed is not None:
        follow_up_needed_bool = follow_up_needed.lower() == 'true'
        query = query.filter(Assessment.follow_up_needed == follow_up_needed_bool)
    
    # Filter by follow-up priority
    if follow_up_priority:
        try:
            priority_enum = FollowUpPriority(follow_up_priority)
            query = query.filter(Assessment.follow_up_priority == priority_enum)
        except ValueError:
            return jsonify({"error": f"Invalid follow-up priority: {follow_up_priority}"}), 400
    
    # Filter by date range
    if from_date:
        try:
            from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            query = query.filter(Assessment.assessment_date >= from_datetime)
        except ValueError:
            return jsonify({"error": f"Invalid from_date format: {from_date}"}), 400
    
    if to_date:
        try:
            to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            query = query.filter(Assessment.assessment_date <= to_datetime)
        except ValueError:
            return jsonify({"error": f"Invalid to_date format: {to_date}"}), 400
    
    # Order by date, most recent first
    query = query.order_by(Assessment.assessment_date.desc())
    
    # Apply limit if specified
    if limit:
        query = query.limit(limit)
    
    # Execute query
    assessments = query.all()
    
    # Serialize with error catching
    try:
        serialized = AssessmentListSchema(many=True).dump(assessments)
        return jsonify(serialized), 200
    except Exception as e:
        current_app.logger.error(f"Serialization error: {str(e)}")
        return jsonify({"error": f"Serialization error: {str(e)}"}), 500

@assessments_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_assessment(id):
    """Get an assessment by ID"""
    # Get the current user from JWT token if available
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id) if current_user_id else None
    
    assessment = Assessment.query.get(id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    
    # Check permission - nurses can only view their patients' assessments
    patient = Patient.query.get(assessment.patient_id)
    if current_user and current_user.role == UserRole.NURSE:
        if not patient or patient.primary_nurse_id != current_user.id:
            return jsonify({"error": "Unauthorized to view this assessment"}), 403
    
    # Ensure protocol relationship is properly loaded
    if assessment.protocol_id:
        protocol = Protocol.query.get(assessment.protocol_id)
        if not protocol:
            print(f"Warning: Protocol with ID {assessment.protocol_id} not found, referenced by assessment {id}")
        else:
            print(f"Protocol found: {protocol.name} ({protocol.protocol_type})")
    else:
        print(f"Warning: Assessment {id} has no protocol_id")
    
    # For demo purposes, don't log access
    
    return jsonify(AssessmentSchema().dump(assessment)), 200

@assessments_bp.route('/', methods=['POST'])
@jwt_required()
def create_assessment():
    """Create a new assessment"""
    data = request.get_json()
    
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Set the current user as the conductor if not specified
    if 'conducted_by_id' not in data and current_user:
        data['conducted_by_id'] = current_user.id
    
    try:
        # Validate input
        assessment_data = AssessmentSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Check if the patient exists and user has permission
    patient = Patient.query.get(assessment_data['patient_id'])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Nurses can only create assessments for their assigned patients
    if current_user and current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user.id:
        return jsonify({"error": "Unauthorized to create assessment for this patient"}), 403
    
    # Create new assessment
    assessment = Assessment(
        patient_id=assessment_data['patient_id'],
        protocol_id=assessment_data.get('protocol_id'),
        conducted_by_id=assessment_data['conducted_by_id'],
        call_id=assessment_data.get('call_id'),
        assessment_date=assessment_data.get('assessment_date', datetime.utcnow()),
        responses=assessment_data.get('responses', {}),
        symptoms=assessment_data.get('symptoms', {}),
        interventions=assessment_data.get('interventions', []),
        notes=assessment_data.get('notes'),
        follow_up_needed=assessment_data.get('follow_up_needed', False),
        follow_up_date=assessment_data.get('follow_up_date'),
        follow_up_priority=assessment_data.get('follow_up_priority'),
        ai_guidance=assessment_data.get('ai_guidance')
    )
    
    # If AI guidance isn't provided, generate it
    if not assessment.ai_guidance and assessment.responses and assessment.protocol_id:
        try:
            ai_guidance = process_assessment(assessment)
            assessment.ai_guidance = ai_guidance
        except Exception as e:
            current_app.logger.error(f"Error generating AI guidance: {e}")
    
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify(AssessmentSchema().dump(assessment)), 201

@assessments_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_assessment(id):
    """Update an assessment"""
    data = request.get_json()
    
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    assessment = Assessment.query.get(id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    
    # Verify permissions - only the creator or admins can update
    if current_user and current_user.role != UserRole.ADMIN and assessment.conducted_by_id != current_user.id:
        return jsonify({"error": "Unauthorized to update this assessment"}), 403
    
    # Check if changing patient and verify permissions
    if 'patient_id' in data and data['patient_id'] != assessment.patient_id:
        patient = Patient.query.get(data['patient_id'])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        # Nurses can only assign to their patients
        if current_user and current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user.id:
            return jsonify({"error": "Unauthorized to assign assessment to this patient"}), 403
    
    try:
        # Validate input
        assessment_data = AssessmentUpdateSchema(context={'is_update': True}).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Update assessment fields
    if 'patient_id' in assessment_data:
        assessment.patient_id = assessment_data['patient_id']
    if 'protocol_id' in assessment_data:
        assessment.protocol_id = assessment_data['protocol_id']
    if 'conducted_by_id' in assessment_data:
        assessment.conducted_by_id = assessment_data['conducted_by_id']
    if 'call_id' in assessment_data:
        assessment.call_id = assessment_data['call_id']
    if 'assessment_date' in assessment_data:
        assessment.assessment_date = assessment_data['assessment_date']
    if 'responses' in assessment_data:
        assessment.responses = assessment_data['responses']
    if 'symptoms' in assessment_data:
        assessment.symptoms = assessment_data['symptoms']
    if 'interventions' in assessment_data:
        assessment.interventions = assessment_data['interventions']
    if 'notes' in assessment_data:
        assessment.notes = assessment_data['notes']
    if 'follow_up_needed' in assessment_data:
        assessment.follow_up_needed = assessment_data['follow_up_needed']
    if 'follow_up_date' in assessment_data:
        assessment.follow_up_date = assessment_data['follow_up_date']
    if 'follow_up_priority' in assessment_data:
        assessment.follow_up_priority = assessment_data['follow_up_priority']
    if 'ai_guidance' in assessment_data:
        assessment.ai_guidance = assessment_data['ai_guidance']
    
    # Update the AI guidance if responses or protocol changed
    if (('responses' in assessment_data or 'protocol_id' in assessment_data) and
        assessment.protocol_id and not assessment.ai_guidance):
        try:
            ai_guidance = process_assessment(assessment)
            assessment.ai_guidance = ai_guidance
        except Exception as e:
            current_app.logger.error(f"Error generating AI guidance: {e}")
    
    db.session.commit()
    
    return jsonify(AssessmentSchema().dump(assessment)), 200

@assessments_bp.route('/<int:id>/complete-followup', methods=['PUT'])
@jwt_required()
def complete_followup(id):
    """Mark a follow-up as completed"""
    # Get the current user from JWT token if available
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id) if current_user_id else None
    
    assessment = Assessment.query.get(id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    
    # Verify the assessment has follow-up needed
    if not assessment.follow_up_needed:
        return jsonify({"error": "This assessment doesn't have a follow-up scheduled"}), 400
    
    # Verify permissions
    patient = Patient.query.get(assessment.patient_id)
    if current_user and current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user.id:
        return jsonify({"error": "Unauthorized to update this assessment"}), 403
    
    # Mark follow-up as completed
    assessment.follow_up_needed = False
    db.session.commit()
    
    return jsonify({"message": "Follow-up marked as completed"}), 200

@assessments_bp.route('/followups', methods=['GET'])
@jwt_required()
def get_followups():
    """Get all assessments with pending follow-ups"""
    # Get the current user from JWT token if available
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id) if current_user_id else None
    
    # Optional date filter
    date_filter = request.args.get('date')
    if date_filter:
        try:
            filter_date = datetime.fromisoformat(date_filter.replace('Z', '+00:00')).date()
        except ValueError:
            return jsonify({"error": f"Invalid date format: {date_filter}"}), 400
    else:
        filter_date = None
    
    # Start with base query for pending follow-ups
    query = Assessment.query.filter(
        Assessment.follow_up_needed == True
    )
    
    # Apply date filter if provided
    if filter_date:
        # Create datetime bounds for the specific date
        start_date = datetime.combine(filter_date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        query = query.filter(
            Assessment.follow_up_date >= start_date,
            Assessment.follow_up_date < end_date
        )
    
    # Filter by nurse's patients if applicable
    if current_user and current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user.id)
    
    # Order by priority (high to low) and date (soonest first)
    query = query.order_by(
        Assessment.follow_up_priority.desc(),
        Assessment.follow_up_date.asc()
    )
    
    # Execute query
    followups = query.all()
    
    # For demo purposes, don't log access
    
    return jsonify(AssessmentListSchema(many=True).dump(followups)), 200