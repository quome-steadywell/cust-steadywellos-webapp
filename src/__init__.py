import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from src.utils.logger import setup_logger

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_object="config.config.DevelopmentConfig"):
    """Application factory pattern."""
    app = Flask(
        __name__, static_folder="web_ui/static", template_folder="web_ui/templates"
    )

    # Load the configuration
    if isinstance(config_object, str):
        app.config.from_object(config_object)
    else:
        app.config.from_mapping(config_object)

    # Set up database configuration following postgress-demo pattern
    from src.utils.database import configure_database

    configure_database(app)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Enable CORS
    CORS(
        app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGIN_WHITELIST")}}
    )

    # Import models to ensure they are registered with SQLAlchemy
    from src.models import (
        user,
        patient,
        protocol,
        assessment,
        medication,
        call,
        audit_log,
    )

    # API routes
    from src.api.auth import auth_bp
    from src.api.users import users_bp
    from src.api.patients import patients_bp
    from src.api.protocols import protocols_bp
    from src.api.assessments import assessments_bp
    from src.api.calls import calls_bp
    from src.api.dashboard import dashboard_bp
    from src.api.webhooks import webhook_bp

    # Register API blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(patients_bp, url_prefix="/api/v1/patients")
    app.register_blueprint(protocols_bp, url_prefix="/api/v1/protocols")
    app.register_blueprint(assessments_bp, url_prefix="/api/v1/assessments")
    app.register_blueprint(calls_bp, url_prefix="/api/v1/calls")
    app.register_blueprint(dashboard_bp, url_prefix="/api/v1/dashboard")
    app.register_blueprint(webhook_bp)  # Register webhook blueprint

    # Web routes
    from src.api.routes import web_bp

    app.register_blueprint(web_bp)

    # Initialize Sentry error tracking (must be done early)
    from src.utils.sentry_integration import init_sentry, register_sentry_error_handlers

    init_sentry(app)

    # Register error handlers (Sentry-enhanced)
    from src.utils.error_handlers import register_error_handlers

    register_error_handlers(app)
    register_sentry_error_handlers(app)

    # Setup application logging (stdout/stderr only)
    setup_logger(app)

    # Initialize database following postgress-demo pattern
    try:
        from src.utils.database import (
            check_database_connection,
            create_tables,
            seed_database_if_empty,
        )

        if check_database_connection(app, db):
            create_tables(app, db)
            seed_database_if_empty(app, db)
            app.logger.info("✅ Database initialization complete")
        else:
            app.logger.error("❌ Database connection failed")
    except Exception as e:
        app.logger.error(f"❌ Error initializing database: {e}")
        # Don't raise the exception to allow the app to start even if DB is unavailable
        app.logger.warning("⚠️ Application starting without database initialization")

    # Shell context
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    return app
