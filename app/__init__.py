import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from app.utils.logger import setup_logger

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_object="config.config.DevelopmentConfig"):
    """Application factory pattern."""
    app = Flask(__name__, static_folder='static', template_folder='templates')

    # Load the configuration
    if isinstance(config_object, str):
        app.config.from_object(config_object)
    else:
        app.config.from_mapping(config_object)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGIN_WHITELIST')}})

    # Import models to ensure they are registered with SQLAlchemy
    from app.models import user, patient, protocol, assessment, medication, call, audit_log

    # API routes
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.patients import patients_bp
    from app.api.protocols import protocols_bp
    from app.api.assessments import assessments_bp
    from app.api.calls import calls_bp
    from app.api.dashboard import dashboard_bp

    # Register API blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(patients_bp, url_prefix='/api/v1/patients')
    app.register_blueprint(protocols_bp, url_prefix='/api/v1/protocols')
    app.register_blueprint(assessments_bp, url_prefix='/api/v1/assessments')
    app.register_blueprint(calls_bp, url_prefix='/api/v1/calls')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')

    # Web routes
    from app.routes import web_bp
    app.register_blueprint(web_bp)

    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Setup application logging (stdout/stderr only)
    setup_logger(app)

    # Shell context
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    return app
