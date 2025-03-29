from flask import jsonify
from werkzeug.exceptions import HTTPException, NotFound, Unauthorized, Forbidden, BadRequest
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jwt.exceptions import PyJWTError

def register_error_handlers(app):
    """Register error handlers for the app."""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({
            'error': 'Validation Error',
            'messages': error.messages
        }), 400
    
    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(Unauthorized)
    def handle_unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(Forbidden)
    def handle_forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(NotFound)
    def handle_not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        return jsonify({
            'error': 'Authentication Error',
            'message': str(error)
        }), 401
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        return jsonify({
            'error': 'Database Integrity Error',
            'message': str(error.orig)
        }), 400
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        return jsonify({
            'error': 'Database Error',
            'message': str(error)
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        # Log the error here
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
