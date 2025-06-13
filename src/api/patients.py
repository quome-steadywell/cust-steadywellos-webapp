from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import or_

from src import db
from src.models.user import User, UserRole
from src.models.patient import Patient, Gender, ProtocolType
from src.schemas.patient import PatientSchema, PatientListSchema, PatientUpdateSchema
from src.utils.decorators import roles_required, audit_action
from src.models.audit_log import AuditLog

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_patients():
    """Get all patients with optional filtering"""
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Get query parameters
    protocol_type = request.args.get('protocol_type')
    search = request.args.get('search')
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    
    # Start with base query
    query = Patient.query.filter(Patient.is_active == is_active)
    
    # Apply role-based access control:
    # - Admins see all patients
    # - Nurses see only their assigned patients
    # - Physicians see all patients for now (could be refined later)
    if current_user and current_user.role == UserRole.NURSE:
        query = query.filter(Patient.primary_nurse_id == current_user.id)
    
    # Apply protocol type filter if provided
    if protocol_type:
        try:
            protocol_enum = ProtocolType(protocol_type)
            query = query.filter(Patient.protocol_type == protocol_enum)
        except ValueError:
            return jsonify({"error": f"Invalid protocol type: {protocol_type}"}), 400
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.mrn.ilike(search_term),
                Patient.primary_diagnosis.ilike(search_term)
            )
        )
    
    # Execute query
    patients = query.all()
    
    # For demo purposes, don't log access
    
    return jsonify(PatientListSchema(many=True).dump(patients)), 200

@patients_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_patient(id):
    """Get a patient by ID"""
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Regular nurses can only view their assigned patients
    if current_user and current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user.id:
        return jsonify({"error": "Unauthorized to view this patient"}), 403
    
    # For demo purposes, don't log access
    
    return jsonify(PatientSchema().dump(patient)), 200

@patients_bp.route('/', methods=['POST'])
@jwt_required()
def create_patient():
    """Create a new patient"""
    data = request.get_json()
    
    try:
        # Validate input
        patient_data = PatientSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Create new patient
    patient = Patient(
        mrn=patient_data['mrn'],
        first_name=patient_data['first_name'],
        last_name=patient_data['last_name'],
        date_of_birth=patient_data['date_of_birth'],
        gender=Gender(patient_data['gender']),
        phone_number=patient_data['phone_number'],
        email=patient_data.get('email'),
        address=patient_data.get('address'),
        primary_diagnosis=patient_data['primary_diagnosis'],
        secondary_diagnoses=patient_data.get('secondary_diagnoses'),
        protocol_type=ProtocolType(patient_data['protocol_type']),
        primary_nurse_id=patient_data['primary_nurse_id'],
        emergency_contact_name=patient_data.get('emergency_contact_name'),
        emergency_contact_phone=patient_data.get('emergency_contact_phone'),
        emergency_contact_relationship=patient_data.get('emergency_contact_relationship'),
        advance_directive=patient_data.get('advance_directive', False),
        dnr_status=patient_data.get('dnr_status', False),
        allergies=patient_data.get('allergies'),
        notes=patient_data.get('notes'),
        is_active=True
    )
    
    db.session.add(patient)
    db.session.commit()
    
    return jsonify(PatientSchema().dump(patient)), 201

@patients_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_patient(id):
    """Update a patient"""
    data = request.get_json()
    
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Regular nurses can only update their assigned patients
    if current_user and current_user.role == UserRole.NURSE and patient.primary_nurse_id != current_user.id:
        return jsonify({"error": "Unauthorized to update this patient"}), 403
    
    try:
        # Validate input
        patient_data = PatientUpdateSchema(context={'is_update': True}).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Update patient fields
    if 'mrn' in patient_data:
        patient.mrn = patient_data['mrn']
    if 'first_name' in patient_data:
        patient.first_name = patient_data['first_name']
    if 'last_name' in patient_data:
        patient.last_name = patient_data['last_name']
    if 'date_of_birth' in patient_data:
        patient.date_of_birth = patient_data['date_of_birth']
    if 'gender' in patient_data:
        patient.gender = Gender(patient_data['gender'])
    if 'phone_number' in patient_data:
        patient.phone_number = patient_data['phone_number']
    if 'email' in patient_data:
        patient.email = patient_data.get('email')
    if 'address' in patient_data:
        patient.address = patient_data.get('address')
    if 'primary_diagnosis' in patient_data:
        patient.primary_diagnosis = patient_data['primary_diagnosis']
    if 'secondary_diagnoses' in patient_data:
        patient.secondary_diagnoses = patient_data.get('secondary_diagnoses')
    if 'protocol_type' in patient_data:
        patient.protocol_type = ProtocolType(patient_data['protocol_type'])
    if 'primary_nurse_id' in patient_data:
        patient.primary_nurse_id = patient_data['primary_nurse_id']
    if 'emergency_contact_name' in patient_data:
        patient.emergency_contact_name = patient_data.get('emergency_contact_name')
    if 'emergency_contact_phone' in patient_data:
        patient.emergency_contact_phone = patient_data.get('emergency_contact_phone')
    if 'emergency_contact_relationship' in patient_data:
        patient.emergency_contact_relationship = patient_data.get('emergency_contact_relationship')
    if 'advance_directive' in patient_data:
        patient.advance_directive = patient_data.get('advance_directive', False)
    if 'dnr_status' in patient_data:
        patient.dnr_status = patient_data.get('dnr_status', False)
    if 'allergies' in patient_data:
        patient.allergies = patient_data.get('allergies')
    if 'notes' in patient_data:
        patient.notes = patient_data.get('notes')
    if 'is_active' in patient_data:
        patient.is_active = patient_data.get('is_active', True)
    
    db.session.commit()
    
    return jsonify(PatientSchema().dump(patient)), 200

@patients_bp.route('/<int:id>/activate', methods=['PUT'])
@jwt_required()
def activate_patient(id):
    """Activate a patient"""
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    patient.is_active = True
    db.session.commit()
    
    return jsonify({"message": f"Patient {patient.full_name} activated"}), 200

@patients_bp.route('/<int:id>/deactivate', methods=['PUT'])
@jwt_required()
def deactivate_patient(id):
    """Deactivate a patient"""
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    patient.is_active = False
    db.session.commit()
    
    return jsonify({"message": f"Patient {patient.full_name} deactivated"}), 200

@patients_bp.route('/search', methods=['GET'])
@jwt_required()
def search_patients():
    """Search patients by name, MRN, or diagnosis"""
    # Get the current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    search_term = request.args.get('q', '')
    if not search_term or len(search_term) < 2:  # Reduced to 2 characters for better usability
        return jsonify({"error": "Search term must be at least 2 characters"}), 400
    
    search_pattern = f"%{search_term}%"
    query = Patient.query.filter(
        or_(
            Patient.first_name.ilike(search_pattern),
            Patient.last_name.ilike(search_pattern),
            Patient.mrn.ilike(search_pattern),
            Patient.primary_diagnosis.ilike(search_pattern)
        )
    )
    
    # Regular nurses can only see their assigned patients
    if current_user and current_user.role == UserRole.NURSE:
        query = query.filter(Patient.primary_nurse_id == current_user.id)
    
    patients = query.all()
    
    # For demo purposes, don't log access
    
    return jsonify(PatientListSchema(many=True).dump(patients)), 200