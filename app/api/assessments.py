from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime, timedelta

from app import db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.protocol import Protocol
from app.models.assessment import Assessment, FollowUpPriority
from app.models.call import Call
from app.schemas.assessment import AssessmentSchema, AssessmentListSchema, AssessmentUpdateSchema
from app.utils.decorators import roles_required, audit_action
from app.models.audit_log import AuditLog
from app.services.rag_service import process_assessment

assessments_bp = Blueprint('assessments', __name__)

@assessments_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_assessments():
    """Get all assessments with optional filtering"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get query parameters
    patient_id = request.args.get('patient_id', type=int)
    protocol_type = request.args.get('protocol_type')
    follow_up_needed = request.args.get('follow_up_needed')
    follow_up_priority = request.args.get('follow_up_priority')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Start with base query
    query = Assessment.query
    
    # Apply filters
    if patient_id:
        query = query.filter(Assessment.patient_id == patient_id)
        
        # Check access to patient for nurses
        if current_user.role == UserRole.NURSE:
            patient = Patient.query.get(patient_id)
            if not patient or patient.primary_nurse_id != current_user_id:
                return jsonify({"error": "Unauthorized to view this patient's assessments"}), 403
    elif current_user.role == UserRole.NURSE:
        # Nurses can only see assessments for their patients
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    if protocol_type:
        query = query.join(Protocol).filter(Protocol.protocol_type == protocol_type)
    
    if follow_up_needed is not None:
        follow_up = follow_up_needed.lower() == 'true'
        query = query.filter(Assessment.follow_up_needed == follow_up)
    
    if follow_up_priority:
        try:
            priority_enum = FollowUpPriority(follow_up_priority)
            query = query.filter(Assessment.follow_up_priority == priority_enum)
        except ValueError:
            return jsonify({"error": f"Invalid follow-up priority: {follow_up_priority}"}), 400
    
    if from_date:
        try:
            from_date_obj = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            query = query.filter(Assessment.assessment_date >= from_date_obj)
        except ValueError:
            return jsonify({"error": f"Invalid from_date format: {from_date}"}), 400
    
    if to_date:
        try:
            to_date_obj = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            query = query.filter(Assessment.assessment_date <= to_date_obj)
        except ValueError:
            return jsonify({"error": f"Invalid to_date format: {to_date}"}), 400
    
    # Order by date, most recent first
    assessments = query.order_by(Assessment.assessment_date.desc()).all()
    
    return jsonify(AssessmentListSchema(many=True).dump(assessments)), 200

@assessments_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_assessment(id):
    """Get an assessment by ID"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    assessment = Assessment.query.get(id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    
    # Regular nurses can only view assessments for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(assessment.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to view this assessment"}), 403
    
    # Log the access
    AuditLog.log(
        user_id=current_user_id,
        action='view',
        resource_type='assessment',
        resource_id=id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify(AssessmentSchema().dump(assessment)), 200

@assessments_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action('create', 'assessment')
def create_assessment():
    """Create a new assessment"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    try:
        # Add conducted_by_id if not provided
        if 'conducted_by_id' not in data:
            data['conducted_by_id'] = current_user_id
            
        # Validate input
        assessment_data = AssessmentSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Get patient and check access for nurses
    patient = Patient.query.get(assessment_data['patient_id'])
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    current_user = User.query.get(current_user_id)
    if current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user_id:
        return jsonify({"error": "Unauthorized to create assessment for this patient"}), 403
    
    # Process assessment responses to extract symptoms and interventions
    protocol = Protocol.query.get(assessment_data['protocol_id'])
    if not protocol:
        return jsonify({"error": "Protocol not found"}), 404
    
    # Extract symptoms from responses based on protocol questions
    symptoms = {}
    for question in protocol.questions:
        question_id = question.get('id')
        symptom_type = question.get('symptom_type')
        
        if question_id and symptom_type and question_id in assessment_data['responses']:
            response = assessment_data['responses'][question_id]
            
            # Handle different question types
            if question.get('type') == 'numeric':
                try:
                    value = float(response.get('value', 0))
                    symptoms[symptom_type] = value
                except (ValueError, TypeError):
                    pass
            elif question.get('type') == 'boolean':
                value = response.get('value')
                if isinstance(value, bool):
                    symptoms[symptom_type] = 1 if value else 0
                elif isinstance(value, str):
                    symptoms[symptom_type] = 1 if value.lower() == 'true' else 0
    
    # Determine interventions based on decision tree
    interventions = []
    for node in protocol.decision_tree:
        symptom_type = node.get('symptom_type')
        condition = node.get('condition')
        
        if symptom_type in symptoms and condition:
            symptom_value = symptoms[symptom_type]
            
            # Evaluate condition
            if condition.startswith('>=') and symptom_value >= float(condition[2:]):
                # Add interventions for this node
                for intervention_id in node.get('intervention_ids', []):
                    # Find intervention details from protocol
                    for intervention in protocol.interventions:
                        if intervention.get('id') == intervention_id:
                            interventions.append(intervention)
                            break
            elif condition.startswith('>') and symptom_value > float(condition[1:]):
                pass  # Similar logic for other operators
            elif condition.startswith('<=') and symptom_value <= float(condition[2:]):
                pass
            elif condition.startswith('<') and symptom_value < float(condition[1:]):
                pass
            elif condition.startswith('=='):
                # Handle boolean or string comparison
                compare_to = condition[2:]
                if compare_to.lower() in ('true', 'false'):
                    bool_value = compare_to.lower() == 'true'
                    if bool(symptom_value) == bool_value:
                        # Add interventions
                        pass
                else:
                    # String comparison
                    if str(symptom_value) == compare_to:
                        # Add interventions
                        pass
    
    # Get AI guidance if RAG service is available
    try:
        ai_guidance = process_assessment(
            patient=patient,
            protocol=protocol,
            symptoms=symptoms,
            responses=assessment_data['responses']
        )
    except Exception as e:
        current_app.logger.error(f"Error getting AI guidance: {str(e)}")
        ai_guidance = None
    
    # Create new assessment
    assessment = Assessment(
        patient_id=assessment_data['patient_id'],
        protocol_id=assessment_data['protocol_id'],
        conducted_by_id=assessment_data['conducted_by_id'],
        call_id=assessment_data.get('call_id'),
        assessment_date=assessment_data['assessment_date'],
        responses=assessment_data['responses'],
        symptoms=symptoms,
        interventions=interventions,
        notes=assessment_data.get('notes'),
        follow_up_needed=assessment_data.get('follow_up_needed', False),
        follow_up_date=assessment_data.get('follow_up_date'),
        follow_up_priority=FollowUpPriority(assessment_data['follow_up_priority']) if 'follow_up_priority' in assessment_data else None,
        ai_guidance=ai_guidance
    )
    
    db.session.add(assessment)
    
    # If linked to a call, update the call status if needed
    if assessment.call_id:
        call = Call.query.get(assessment.call_id)
        if call and call.status != 'completed':
            call.status = 'completed'
            call.end_time = datetime.utcnow()
            if call.start_time:
                call.duration = (call.end_time - call.start_time).total_seconds()
    
    db.session.commit()
    
    # Include the AI guidance in the response
    result = AssessmentSchema().dump(assessment)
    result['ai_guidance'] = ai_guidance
    
    return jsonify(result), 201

@assessments_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.NURSE, UserRole.PHYSICIAN)
@audit_action('update', 'assessment')
def update_assessment(id):
    """Update an assessment"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    assessment = Assessment.query.get(id)
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404
    
    # Regular nurses can only update assessments for their patients
    if current_user.role == UserRole.NURSE:
        patient = Patient.query.get(assessment.patient_id)
        if not patient or patient.primary_nurse_id != current_user_id:
            return jsonify({"error": "Unauthorized to update this assessment"}), 403
    
    try:
        # Validate input
        assessment_data = AssessmentUpdateSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Update assessment fields
    if 'notes' in assessment_data:
        assessment.notes = assessment_data['notes']
    if 'follow_up_needed' in assessment_data:
        assessment.follow_up_needed = assessment_data['follow_up_needed']
    if 'follow_up_date' in assessment_data:
        assessment.follow_up_date = assessment_data['follow_up_date']
    if 'follow_up_priority' in assessment_data:
        assessment.follow_up_priority = FollowUpPriority(assessment_data['follow_up_priority'])
    
    db.session.commit()
    
    return jsonify(AssessmentSchema().dump(assessment)), 200

@assessments_bp.route('/patient/<int:patient_id>/recent', methods=['GET'])
@jwt_required()
def get_recent_assessments(patient_id):
    """Get recent assessments for a patient"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Check if patient exists
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Regular nurses can only view their assigned patients
    if current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user_id:
        return jsonify({"error": "Unauthorized to view this patient's assessments"}), 403
    
    # Get query parameters
    limit = request.args.get('limit', default=5, type=int)
    
    # Get recent assessments
    assessments = Assessment.query.filter(
        Assessment.patient_id == patient_id
    ).order_by(Assessment.assessment_date.desc()).limit(limit).all()
    
    return jsonify(AssessmentListSchema(many=True).dump(assessments)), 200

@assessments_bp.route('/followups', methods=['GET'])
@jwt_required()
def get_followups():
    """Get assessments needing follow-up"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get query parameters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    priority = request.args.get('priority')
    
    # Default date range is today to next 7 days if not specified
    if not from_date:
        from_date_obj = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            from_date_obj = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": f"Invalid from_date format: {from_date}"}), 400
    
    if not to_date:
        to_date_obj = from_date_obj + timedelta(days=7)
    else:
        try:
            to_date_obj = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": f"Invalid to_date format: {to_date}"}), 400
    
    # Build query for follow-ups
    query = Assessment.query.filter(
        Assessment.follow_up_needed == True,
        Assessment.follow_up_date >= from_date_obj,
        Assessment.follow_up_date <= to_date_obj
    )
    
    # Apply priority filter
    if priority:
        try:
            priority_enum = FollowUpPriority(priority)
            query = query.filter(Assessment.follow_up_priority == priority_enum)
        except ValueError:
            return jsonify({"error": f"Invalid priority: {priority}"}), 400
    
    # Regular nurses can only see followups for their patients
    if current_user.role == UserRole.NURSE:
        query = query.join(Patient).filter(Patient.primary_nurse_id == current_user_id)
    
    # Order by priority (highest first) and then by follow-up date
    followups = query.order_by(
        Assessment.follow_up_priority.desc(),  # HIGH, MEDIUM, LOW
        Assessment.follow_up_date
    ).all()
    
    return jsonify(AssessmentListSchema(many=True).dump(followups)), 200