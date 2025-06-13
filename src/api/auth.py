from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta
from marshmallow import ValidationError

from src import db
from src.models.user import User
from src.schemas.user import UserSchema, LoginSchema, TokenSchema, PasswordResetRequestSchema, PasswordResetSchema
from src.utils.security import verify_password_reset_token, generate_password_reset_token
from src.models.audit_log import AuditLog

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    try:
        # Validate input
        login_data = LoginSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Check if username exists
    user = User.query.filter_by(username=login_data['username']).first()
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403
    
    if user.is_account_locked():
        return jsonify({"error": "Account is locked due to too many failed login attempts"}), 403
    
    # Check password
    if not user.check_password(login_data['password']):
        user.increment_login_attempts()
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Reset login attempts on successful login
    user.reset_login_attempts()
    
    # Generate tokens
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(minutes=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 30))
    )
    
    refresh_token = create_refresh_token(identity=user.id)
    
    # Log the login
    AuditLog.log(
        user_id=user.id,
        action='login',
        resource_type='user',
        resource_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    # Return tokens and user data
    token_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 30) * 60,
        'refresh_token': refresh_token,
        'user': user
    }
    
    return jsonify(TokenSchema().dump(token_data)), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({"error": "Invalid token"}), 401
    
    # Generate new access token
    access_token = create_access_token(
        identity=current_user_id,
        expires_delta=timedelta(minutes=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 30))
    )
    
    # Log the token refresh
    AuditLog.log(
        user_id=user.id,
        action='token_refresh',
        resource_type='user',
        resource_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', 30) * 60
    }), 200

@auth_bp.route('/password-reset-request', methods=['POST'])
def password_reset_request():
    """Request password reset via email"""
    data = request.get_json()
    
    try:
        # Validate input
        schema_data = PasswordResetRequestSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Find user by email
    user = User.query.filter_by(email=schema_data['email']).first()
    
    # Always return success even if email not found (security best practice)
    if not user:
        return jsonify({"message": "If the email exists, a password reset link will be sent"}), 200
    
    # Generate password reset token
    reset_token = generate_password_reset_token(user.id)
    
    # In a real app, send email with the token
    # Here we just log it
    current_app.logger.info(f"Password reset token for {user.email}: {reset_token}")
    
    # Log the password reset request
    AuditLog.log(
        user_id=user.id,
        action='password_reset_request',
        resource_type='user',
        resource_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify({"message": "If the email exists, a password reset link will be sent"}), 200

@auth_bp.route('/password-reset', methods=['POST'])
def password_reset():
    """Reset password using token"""
    data = request.get_json()
    
    try:
        # Validate input
        schema_data = PasswordResetSchema(context={'password': data.get('password')}).load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400
    
    # Verify token
    user_id = verify_password_reset_token(schema_data['token'])
    
    if not user_id:
        return jsonify({"error": "Invalid or expired token"}), 400
    
    # Find user
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update password
    user.password = schema_data['password']
    user.login_attempts = 0  # Reset login attempts
    db.session.commit()
    
    # Log the password reset
    AuditLog.log(
        user_id=user.id,
        action='password_reset',
        resource_type='user',
        resource_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    return jsonify({"message": "Password reset successful"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(UserSchema().dump(user)), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Log user out (client-side, just for audit)"""
    current_user_id = get_jwt_identity()
    
    # Log the logout
    AuditLog.log(
        user_id=current_user_id,
        action='logout',
        resource_type='user',
        resource_id=current_user_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    
    # In a real implementation, you would blacklist the token
    # For now, just return success (client will delete the token)
    return jsonify({"message": "Successfully logged out"}), 200

@auth_bp.route('/session-settings', methods=['GET'])
def get_session_settings():
    """Get session timeout settings for the frontend"""
    # Get the timeout settings from config
    time_unit = current_app.config.get('TIME_UNIT', 'MINUTES')
    auto_logout_time = int(current_app.config.get('AUTO_LOGOUT_TIME', 30))
    warning_time = int(current_app.config.get('WARNING_TIME', 5))
    
    # Convert to milliseconds for the frontend based on the time unit
    if time_unit == 'SECONDS':
        auto_logout_ms = auto_logout_time * 1000
        warning_ms = warning_time * 1000
        auto_logout_mins = auto_logout_time / 60
        warning_mins = warning_time / 60
        current_app.logger.info(f"Returning session settings: auto_logout={auto_logout_time}sec ({auto_logout_mins:.2f}min), warning={warning_time}sec ({warning_mins:.2f}min)")
    else:  # Default to MINUTES
        auto_logout_ms = auto_logout_time * 60 * 1000
        warning_ms = warning_time * 60 * 1000
        auto_logout_mins = auto_logout_time
        warning_mins = warning_time
        current_app.logger.info(f"Returning session settings: auto_logout={auto_logout_time}min, warning={warning_time}min")
    
    return jsonify({
        "auto_logout_time": auto_logout_ms,
        "warning_time": warning_ms,
        "auto_logout_minutes": auto_logout_mins,
        "warning_minutes": warning_mins,
        "time_unit": time_unit,
        "debug_mode": current_app.config.get('AUTO_LOGOUT_DEBUG', False)
    }), 200