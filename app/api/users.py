from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models.user import User, UserRole
from app.schemas.user import UserSchema, UserUpdateSchema
from app.utils.decorators import roles_required, audit_action
from app.models.audit_log import AuditLog

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
@roles_required(UserRole.ADMIN)
def get_all_users():
    """Get all users (admin only)"""
    users = User.query.all()
    return jsonify(UserSchema(many=True).dump(users)), 200

@users_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    """Get a user by ID"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Allow admins to view any user, others can only view themselves
    if current_user.role != UserRole.ADMIN and current_user_id != id:
        return jsonify({"error": "Unauthorized to view this user"}), 403
    
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Log the access
    AuditLog.log(
        user_id=current_user_id,
        action='view',
        resource_type='user',
        resource_id=id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify(UserSchema().dump(user)), 200

@users_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('create', 'user')
def create_user():
    """Create a new user (admin only)"""
    data = request.get_json()
    
    try:
        # Validate input
        user_data = UserSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Create new user
    user = User(
        username=user_data['username'],
        email=user_data['email'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        role=UserRole(user_data['role']) if 'role' in user_data else UserRole.NURSE,
        phone_number=user_data.get('phone_number'),
        license_number=user_data.get('license_number'),
        is_active=True
    )
    
    # Set password
    user.password = user_data['password']
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(UserSchema().dump(user)), 201

@users_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_action('update', 'user')
def update_user(id):
    """Update a user"""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Allow admins to update any user, others can only update themselves
    if current_user.role != UserRole.ADMIN and current_user_id != id:
        return jsonify({"error": "Unauthorized to update this user"}), 403
    
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Validate input
        user_data = UserUpdateSchema(context={'is_update': True}).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Update user fields
    if 'username' in user_data:
        user.username = user_data['username']
    if 'email' in user_data:
        user.email = user_data['email']
    if 'first_name' in user_data:
        user.first_name = user_data['first_name']
    if 'last_name' in user_data:
        user.last_name = user_data['last_name']
    if 'phone_number' in user_data:
        user.phone_number = user_data['phone_number']
    if 'license_number' in user_data:
        user.license_number = user_data['license_number']
    
    # Only admins can change roles
    if 'role' in user_data and current_user.role == UserRole.ADMIN:
        user.role = UserRole(user_data['role'])
    
    # Update password if provided
    if 'password' in user_data:
        user.password = user_data['password']
    
    db.session.commit()
    
    return jsonify(UserSchema().dump(user)), 200

@users_bp.route('/<int:id>/activate', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('activate', 'user')
def activate_user(id):
    """Activate a user (admin only)"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.is_active = True
    db.session.commit()
    
    return jsonify({"message": f"User {user.username} activated"}), 200

@users_bp.route('/<int:id>/deactivate', methods=['PUT'])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action('deactivate', 'user')
def deactivate_user(id):
    """Deactivate a user (admin only)"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Prevent deactivating the last admin
    if user.role == UserRole.ADMIN:
        admin_count = User.query.filter_by(role=UserRole.ADMIN, is_active=True).count()
        if admin_count <= 1:
            return jsonify({"error": "Cannot deactivate the last active admin"}), 400
    
    user.is_active = False
    db.session.commit()
    
    return jsonify({"message": f"User {user.username} deactivated"}), 200

@users_bp.route('/nurses', methods=['GET'])
@jwt_required()
def get_nurses():
    """Get all active nurses (for assigning to patients)"""
    nurses = User.query.filter(
        User.role.in_([UserRole.NURSE, UserRole.PHYSICIAN]),
        User.is_active == True
    ).all()
    
    return jsonify(UserSchema(many=True, only=['id', 'username', 'full_name', 'role']).dump(nurses)), 200