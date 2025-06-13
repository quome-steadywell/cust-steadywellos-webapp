from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from src.models.user import User, UserRole
from src.models.audit_log import AuditLog
from app import db

def roles_required(*roles):
    """Decorator to restrict access based on user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 401
                
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403
                
            if user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def audit_action(action, resource_type):
    """Decorator to audit user actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            try:
                # Extract user_id from JWT
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Determine resource_id from kwargs or response
                resource_id = kwargs.get('id') or kwargs.get(f'{resource_type}_id')
                
                # Get additional request information
                ip_address = request.remote_addr
                user_agent = request.user_agent.string
                
                # Log the action
                AuditLog.log(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                # Log the error but don't disrupt the flow
                current_app.logger.error(f"Audit logging error: {str(e)}")
                
            return result
        return decorated_function
    return decorator

def rate_limit(limit=100, per=60):
    """Simple rate limiting decorator using in-memory storage"""
    def decorator(f):
        # Basic in-memory rate limiting for single-instance deployments
        _rate_limits = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            key = f"{ip}:{f.__name__}"
            now = datetime.now().timestamp()
            
            # Initialize or clean up old requests
            if key not in _rate_limits:
                _rate_limits[key] = []
            
            _rate_limits[key] = [t for t in _rate_limits[key] if now - t < per]
            
            # Check if limit is reached
            if len(_rate_limits[key]) >= limit:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request timestamp
            _rate_limits[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
