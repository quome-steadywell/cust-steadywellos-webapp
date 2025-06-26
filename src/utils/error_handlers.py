from flask import jsonify
from werkzeug.exceptions import (
    HTTPException,
    NotFound,
    Unauthorized,
    Forbidden,
    BadRequest,
)
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jwt.exceptions import PyJWTError
from src.utils.logger import get_logger

# Get the application logger
logger = get_logger()


def register_error_handlers(app):
    """Register error handlers for the app."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.info(f"Validation error: {error.messages}")
        return jsonify({"error": "Validation Error", "messages": error.messages}), 400

    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        logger.info(f"Bad request: {str(error)}")
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(Unauthorized)
    def handle_unauthorized(error):
        logger.warning("Unauthorized access attempt")
        return (
            jsonify({"error": "Unauthorized", "message": "Authentication required"}),
            401,
        )

    @app.errorhandler(Forbidden)
    def handle_forbidden(error):
        logger.warning("Forbidden access attempt")
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to access this resource",
                }
            ),
            403,
        )

    @app.errorhandler(NotFound)
    def handle_not_found(error):
        logger.info(f"Resource not found: {error}")
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": "The requested resource was not found",
                }
            ),
            404,
        )

    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        logger.warning(f"JWT authentication error: {str(error)}")
        return jsonify({"error": "Authentication Error", "message": str(error)}), 401

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        logger.error(f"Database integrity error: {str(error.orig)}")
        return (
            jsonify({"error": "Database Integrity Error", "message": str(error.orig)}),
            400,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        logger.error(f"Database error: {str(error)}")
        return jsonify({"error": "Database Error", "message": str(error)}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # Log based on error code severity
        if error.code >= 500:
            logger.error(f"Server error: {error.name} - {error.description}")
        elif error.code >= 400:
            logger.warning(f"Client error: {error.name} - {error.description}")
        else:
            logger.info(f"HTTP exception: {error.name} - {error.description}")

        return jsonify({"error": error.name, "message": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        # Log the error with full traceback
        logger.exception(f"Unhandled exception: {str(error)}")
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )
