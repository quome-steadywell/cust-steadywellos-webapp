from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models.user import User, UserRole
from app.models.protocol import Protocol
from app.models.patient import ProtocolType
from app.schemas.protocol import ProtocolSchema, ProtocolListSchema, ProtocolUpdateSchema
from app.utils.decorators import roles_required, audit_action
from app.models.audit_log import AuditLog

protocols_bp = Blueprint('protocols', __name__)

@protocols_bp.route('/', methods=['GET'])
def get_all_protocols():
    """Get all protocols with optional filtering"""
    # Get query parameters
    protocol_type = request.args.get('type') or request.args.get('protocol_type')
    is_active = request.args.get('is_active', 'true').lower() == 'true'
    latest_only = request.args.get('latest_only', 'false').lower() == 'true'
    
    # Start with base query
    query = Protocol.query.filter(Protocol.is_active == is_active)
    
    # Apply protocol type filter if provided
    if protocol_type:
        try:
            protocol_enum = ProtocolType(protocol_type)
            query = query.filter(Protocol.protocol_type == protocol_enum)
        except ValueError:
            return jsonify({"error": f"Invalid protocol type: {protocol_type}"}), 400
    
    # Get protocols
    if latest_only:
        # Get the latest version of each protocol type
        latest_protocols = []
        for p_type in ProtocolType:
            latest = query.filter(Protocol.protocol_type == p_type).order_by(Protocol.version.desc()).first()
            if latest:
                latest_protocols.append(latest)
        protocols = latest_protocols
    else:
        protocols = query.order_by(Protocol.protocol_type, Protocol.version.desc()).all()
    
    # Debug output - Log the type of protocols returned
    print(f"Found {len(protocols)} protocols matching type={protocol_type}, active={is_active}")
    for protocol in protocols:
        print(f"Protocol: id={protocol.id}, name={protocol.name}, type={protocol.protocol_type}")
    
    return jsonify(ProtocolListSchema(many=True).dump(protocols)), 200

@protocols_bp.route('/<int:id>', methods=['GET'])
def get_protocol(id):
    """Get a protocol by ID"""
    protocol = Protocol.query.get(id)
    if not protocol:
        return jsonify({"error": "Protocol not found"}), 404
    
    return jsonify(ProtocolSchema().dump(protocol)), 200

@protocols_bp.route('/type/<protocol_type>/latest', methods=['GET'])
def get_latest_protocol(protocol_type):
    """Get the latest version of a protocol type"""
    # Try to normalize the protocol type 
    normalized_type = protocol_type
    
    # Handle 'ProtocolType.COPD' format
    if normalized_type.startswith('ProtocolType.'):
        normalized_type = normalized_type.replace('ProtocolType.', '')
    
    # Convert to lowercase to match enum values
    normalized_type = normalized_type.lower()
    
    print(f"API: Getting protocol for type {protocol_type}, normalized to {normalized_type}")
    
    try:
        # Find the matching enum value from the normalized type
        matching_enum = None
        for pt in ProtocolType:
            if pt.value == normalized_type:
                matching_enum = pt
                break
        
        if not matching_enum:
            return jsonify({"error": f"Invalid protocol type: {protocol_type}"}), 400
        
        protocol = Protocol.query.filter(
            Protocol.protocol_type == matching_enum,
            Protocol.is_active == True
        ).order_by(Protocol.version.desc()).first()
        
        if not protocol:
            return jsonify({"error": f"No active protocol found for type: {protocol_type}"}), 404
        
        return jsonify(ProtocolSchema().dump(protocol)), 200
    except Exception as e:
        print(f"Error getting protocol: {str(e)}")
        return jsonify({"error": f"Error getting protocol: {str(e)}"}), 500

@protocols_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('create', 'protocol')
def create_protocol():
    """Create a new protocol (admin only)"""
    data = request.get_json()
    
    try:
        # Set context for validation
        if 'protocol_type' in data:
            context = {'protocol_type': data['protocol_type']}
        else:
            context = {}
            
        # Validate input
        protocol_data = ProtocolSchema(context=context).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Create new protocol
    protocol = Protocol(
        name=protocol_data['name'],
        description=protocol_data.get('description'),
        protocol_type=ProtocolType(protocol_data['protocol_type']),
        version=protocol_data['version'],
        questions=protocol_data['questions'],
        decision_tree=protocol_data['decision_tree'],
        interventions=protocol_data['interventions'],
        is_active=protocol_data.get('is_active', True)
    )
    
    db.session.add(protocol)
    db.session.commit()
    
    return jsonify(ProtocolSchema().dump(protocol)), 201

@protocols_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('update', 'protocol')
def update_protocol(id):
    """Update a protocol (admin only)"""
    data = request.get_json()
    
    protocol = Protocol.query.get(id)
    if not protocol:
        return jsonify({"error": "Protocol not found"}), 404
    
    try:
        # Validate input
        protocol_data = ProtocolUpdateSchema(context={'is_update': True}).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Update protocol fields
    if 'name' in protocol_data:
        protocol.name = protocol_data['name']
    if 'description' in protocol_data:
        protocol.description = protocol_data['description']
    if 'protocol_type' in protocol_data:
        protocol.protocol_type = ProtocolType(protocol_data['protocol_type'])
    if 'version' in protocol_data:
        protocol.version = protocol_data['version']
    if 'questions' in protocol_data:
        protocol.questions = protocol_data['questions']
    if 'decision_tree' in protocol_data:
        protocol.decision_tree = protocol_data['decision_tree']
    if 'interventions' in protocol_data:
        protocol.interventions = protocol_data['interventions']
    if 'is_active' in protocol_data:
        protocol.is_active = protocol_data['is_active']
    
    db.session.commit()
    
    return jsonify(ProtocolSchema().dump(protocol)), 200

@protocols_bp.route('/<int:id>/activate', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('activate', 'protocol')
def activate_protocol(id):
    """Activate a protocol (admin only)"""
    protocol = Protocol.query.get(id)
    if not protocol:
        return jsonify({"error": "Protocol not found"}), 404
    
    protocol.is_active = True
    db.session.commit()
    
    return jsonify({"message": f"Protocol {protocol.name} v{protocol.version} activated"}), 200

@protocols_bp.route('/<int:id>/deactivate', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('deactivate', 'protocol')
def deactivate_protocol(id):
    """Deactivate a protocol (admin only)"""
    protocol = Protocol.query.get(id)
    if not protocol:
        return jsonify({"error": "Protocol not found"}), 404
    
    # Check if it's the only active protocol of its type
    active_protocols_count = Protocol.query.filter(
        Protocol.protocol_type == protocol.protocol_type,
        Protocol.is_active == True
    ).count()
    
    if active_protocols_count <= 1:
        return jsonify({"error": f"Cannot deactivate the only active protocol of type {protocol.protocol_type.value}"}), 400
    
    protocol.is_active = False
    db.session.commit()
    
    return jsonify({"message": f"Protocol {protocol.name} v{protocol.version} deactivated"}), 200