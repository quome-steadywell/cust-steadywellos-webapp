import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""

    # Application Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-for-development-only")
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "SimpleCache"  # In-memory cache for single-instance deployments
    CORS_ORIGIN_WHITELIST = [
        "http://0.0.0.0:5000",
        "http://localhost:5000",
    ]

    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("AUTH_TOKEN_EXPIRY_DAYS", 1)))
    PASSWORD_SALT = os.getenv("PASSWORD_SALT", "default-salt-for-dev-only")
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))

    # Auto-logout settings
    TIME_UNIT = os.getenv("TIME", "MINUTES").upper()  # Time unit for auto-logout settings (SECONDS or MINUTES)
    AUTO_LOGOUT_TIME = int(os.getenv("AUTO_LOGOUT_TIME", 30))  # Time until auto-logout (in TIME_UNIT)
    WARNING_TIME = int(os.getenv("WARNING_TIME", 5))  # Time before auto-logout to show warning (in TIME_UNIT)
    # Special debug mode for auto-logout
    AUTO_LOGOUT_DEBUG = os.getenv("AUTO_LOGOUT", "") == "TEST"  # Enable debug display for auto-logout timing

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/palliative_care_db",
    )

    # AWS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    S3_BUCKET = os.getenv("S3_BUCKET")

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # RAG Model
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Retell AI Configuration - aligned with postgres-demo naming
    RETELLAI_API_KEY = os.getenv("RETELLAI_API_KEY")
    RETELLAI_LOCAL_AGENT_ID = os.getenv("RETELLAI_LOCAL_AGENT_ID")
    RETELLAI_REMOTE_AGENT_ID = os.getenv("RETELLAI_REMOTE_AGENT_ID")
    RETELLAI_PHONE_NUMBER = os.getenv("RETELLAI_PHONE_NUMBER")

    # Webhook settings - derived from CLOUD_APP_NAME
    CLOUD_APP_NAME = os.getenv("CLOUD_APP_NAME", "")

    @classmethod
    def _get_webhook_url(cls, endpoint: str) -> str:
        """Get webhook URL for a specific endpoint.

        Runtime environment detection:
        - RUNTIME_ENV=local: Uses RETELLAI_LOCAL_WEBHOOK (ngrok URL for local development)
        - RUNTIME_ENV unset/other: Uses CLOUD_APP_NAME (Quome cloud URL for production)
        """
        runtime_env = os.getenv("RUNTIME_ENV", "")

        # Determine base URL based on runtime environment
        if runtime_env == "local":
            # Local development mode - use RETELLAI_LOCAL_WEBHOOK (ngrok URL)
            base_url = os.getenv("RETELLAI_LOCAL_WEBHOOK", "")
        else:
            # Production mode (Quome cloud) - use CLOUD_APP_NAME (Quome URL)
            base_url = os.getenv("CLOUD_APP_NAME", "")

        if not base_url:
            raise ValueError(
                f"No base URL configured for {runtime_env} environment. "
                f"Set RETELLAI_LOCAL_WEBHOOK (local) or CLOUD_APP_NAME (production)"
            )

        # Remove trailing slash if present to avoid double slashes
        base_url = base_url.rstrip("/")
        return f"{base_url}/{endpoint}"

    @property
    def WEBHOOK_URL(self) -> str:
        """Webhook URL for Retell.ai callbacks."""
        return self.__class__._get_webhook_url("webhook")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@example.com")


class DevelopmentConfig(Config):
    """Development configuration."""

    ENV = "development"
    DEBUG = True
    SQLALCHEMY_ECHO = True
    BCRYPT_LOG_ROUNDS = 4


class TestingConfig(Config):
    """Testing configuration."""

    ENV = "testing"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/palliative_care_test_db",
    )
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class ProductionConfig(Config):
    """Production configuration."""

    ENV = "production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    BCRYPT_LOG_ROUNDS = 13


# Dictionary with all available configurations
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
