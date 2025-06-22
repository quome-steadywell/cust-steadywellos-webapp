import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import os
import logging
from flask import jsonify, g

def init_sentry(app):
    """Initialize Sentry error tracking."""
    
    # Only initialize Sentry if DSN is provided
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if not sentry_dsn:
        app.logger.warning("SENTRY_DSN not configured - error tracking disabled")
        return
    
    # Sentry logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(
                transaction_style='endpoint'  # Track by endpoint name
            ),
            SqlalchemyIntegration(),
            sentry_logging,
        ],
        environment=os.environ.get('ENVIRONMENT', 'development'),
        release=os.environ.get('APP_VERSION', '1.0.0'),
        
        # Performance Monitoring
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        
        # Error Sampling
        sample_rate=1.0,  # Send 100% of errors
        
        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
        
        # Custom tag extraction
        before_send=before_send_filter,
    )
    
    app.logger.info(f"Sentry initialized for environment: {os.environ.get('ENVIRONMENT', 'development')}")

def before_send_filter(event, hint):
    """Filter and enrich events before sending to Sentry."""
    
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['component'] = 'palliative-care-webapp'
    
    # Don't send certain error types in development
    if os.environ.get('ENVIRONMENT') == 'development':
        # Skip validation errors in dev
        if 'marshmallow.exceptions.ValidationError' in str(event.get('exception', {})):
            return None
    
    # Add user context if available
    try:
        if hasattr(g, 'user_id'):
            event.setdefault('user', {})['id'] = g.user_id
    except:
        pass
    
    return event

def register_sentry_error_handlers(app):
    """Enhanced error handlers that work with Sentry."""
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Sentry will automatically capture this
        app.logger.exception(f"Unhandled exception: {str(error)}")
        
        # Add custom context to Sentry
        sentry_sdk.set_context("error_context", {
            "error_type": type(error).__name__,
            "error_message": str(error)
        })
        
        # Add custom tags
        sentry_sdk.set_tag("error_handler", "global_exception")
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
