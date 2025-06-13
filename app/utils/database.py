"""Database initialization and utility functions."""

import os
import logging
from datetime import datetime, timezone
from flask import Flask
from sqlalchemy import text

logger = logging.getLogger(__name__)

def configure_database(app: Flask):
    """Configure database URL following postgress-demo pattern."""
    # Determine environment and use appropriate variables
    dev_state = os.getenv('DEV_STATE', 'TEST')

    if dev_state == 'TEST':
        # Local development - use LOCAL variables or DATABASE_LOCAL_URL
        database_url = os.getenv('DATABASE_LOCAL_URL')
        if not database_url:
            db_user = os.getenv('POSTGRES_LOCAL_USER')
            db_password = os.getenv('POSTGRES_LOCAL_PASSWORD')
            db_host = os.getenv('POSTGRES_LOCAL_HOST')
            db_port = os.getenv('POSTGRES_LOCAL_PORT', '5432')
            db_name = os.getenv('POSTGRES_LOCAL_DB')
            var_prefix = 'LOCAL'
        else:
            var_prefix = 'LOCAL'
            logger.info("✅ Using provided DATABASE_LOCAL_URL")
    else:
        # Production/Quome Cloud - use REMOTE variables
        database_url = None  # Force building from components for remote
        db_user = os.getenv('POSTGRES_REMOTE_USER')
        db_password = os.getenv('POSTGRES_REMOTE_PASSWORD')
        db_host = os.getenv('POSTGRES_REMOTE_HOST')
        db_port = os.getenv('POSTGRES_REMOTE_PORT', '5432')
        db_name = os.getenv('POSTGRES_REMOTE_DB')
        var_prefix = 'REMOTE'

    # If no DATABASE_URL, build it from individual components
    if not database_url:
        # Check if we have all required components
        missing_vars = []
        if not db_user:
            missing_vars.append(f'POSTGRES_{var_prefix}_USER')
        if not db_password:
            missing_vars.append(f'POSTGRES_{var_prefix}_PASSWORD')
        if not db_host:
            missing_vars.append(f'POSTGRES_{var_prefix}_HOST')
        if not db_name:
            missing_vars.append(f'POSTGRES_{var_prefix}_DB')

        if missing_vars:
            error_msg = (
                f"❌ CRITICAL ERROR: Missing required database environment variables: {', '.join(missing_vars)}\n"
                f"For {dev_state} environment, provide all {var_prefix} database components:\n"
                f"- POSTGRES_{var_prefix}_USER (database username)\n"
                f"- POSTGRES_{var_prefix}_PASSWORD (database password)\n"
                f"- POSTGRES_{var_prefix}_HOST (database hostname)\n"
                f"- POSTGRES_{var_prefix}_DB (database name)\n"
                f"- POSTGRES_{var_prefix}_PORT (optional, defaults to 5432)\n"
                f"Or provide DATABASE_{var_prefix}_URL directly"
            )
            logger.error(error_msg)
            raise ValueError(f"Missing required database environment variables: {', '.join(missing_vars)}")

        # Add SSL mode for remote/production environments
        ssl_suffix = "?sslmode=require" if var_prefix == 'REMOTE' else ""
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}{ssl_suffix}"
        logger.info(f"✅ Built DATABASE_URL from {var_prefix} components" + (" (with SSL required)" if ssl_suffix else ""))

    # Debug database configuration
    logger.info("=== Database Configuration Debug ===")
    logger.info(f"DEV_STATE: {dev_state}")
    logger.info(f"Using {var_prefix} database configuration")
    
    # Safely log database URL with masking
    if database_url:
        try:
            import re
            # Extract components for safe logging (first 5 chars + asterisks for password)
            def safe_truncate(match):
                username = match.group(1)
                password = match.group(2)
                # Show first 4 characters + asterisks for username, first 5 chars + asterisks for password
                safe_username = username[:4] + "****" if len(username) > 4 else username + "****"
                safe_password = password[:5] + "*" * max(0, len(password) - 5) if len(password) > 5 else password + "*****"
                return f"://{safe_username}:{safe_password}@"

            safe_url = re.sub(r'://([^:]+):([^@]+)@', safe_truncate, database_url)
            logger.info(f"Database URL (safe): {safe_url}")

            # Extract host for additional debugging
            host_match = re.search(r'@([^:/]+)', database_url)
            if host_match:
                host = host_match.group(1)
                logger.info(f"Database host: {host}")

        except Exception as e:
            logger.warning(f"Could not parse database URL for logging: {e}")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10
        }
    }

    logger.info("====================================")

def check_database_connection(app: Flask, db):
    """Check if database connection is working."""
    with app.app_context():
        try:
            logger.info("Testing database connection...")

            # Try to execute a simple query
            result = db.session.execute(text('SELECT 1 as test'))
            test_result = result.fetchone()

            if test_result and test_result[0] == 1:
                logger.info("✅ Database connection successful")

                # Try to get database version for additional verification
                try:
                    version_result = db.session.execute(text('SELECT version()'))
                    version = version_result.fetchone()[0]
                    logger.info(f"Database version: {version.split(',')[0]}")  # Just the first part
                except Exception as ve:
                    logger.warning(f"Could not get database version: {ve}")

                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")

            # Try to provide more specific error information
            error_msg = str(e).lower()
            if 'connection refused' in error_msg:
                logger.error("➤ Connection refused - database server may not be running")
            elif 'timeout' in error_msg:
                logger.error("➤ Connection timeout - database server may be unreachable")
            elif 'authentication' in error_msg or 'password' in error_msg:
                logger.error("➤ Authentication failed - check database credentials")
            elif 'database' in error_msg and 'does not exist' in error_msg:
                logger.error("➤ Database does not exist - check database name")
            elif 'host' in error_msg or 'name resolution' in error_msg:
                logger.error("➤ Host resolution failed - check database hostname")

            return False

def create_tables(app: Flask, db):
    """Create all database tables."""
    with app.app_context():
        try:
            # Check if we need to recreate tables due to schema changes
            needs_recreation = False

            # Try to query a table to see if it exists
            try:
                result = db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
                logger.info("✅ Database tables exist")
            except Exception as schema_error:
                if "does not exist" in str(schema_error).lower():
                    logger.info("ℹ️ Database tables don't exist yet - will create with current schema")
                    needs_recreation = True
                else:
                    # Some other error, assume we need to create tables
                    logger.info("ℹ️ Database tables need to be created")
                    needs_recreation = True

            if needs_recreation:
                logger.info("🔄 Creating database tables...")
                db.create_all()
                logger.info("✅ Database tables created successfully")
            else:
                logger.info("✅ Database tables already exist")

        except Exception as e:
            logger.error(f"❌ Error creating database tables: {e}")
            raise

def seed_database_if_empty(app: Flask, db):
    """Seed the database with initial data if it's empty."""
    with app.app_context():
        try:
            # Check if force reseed is requested
            force_reseed = os.getenv("FORCE_RESEED", "false").lower() == "true"
            
            # Check if data already exists by looking for users
            from app.models.user import User
            existing_count = User.query.count()
            
            if existing_count > 0 and not force_reseed:
                logger.info("Database already contains user data, skipping seed")
                return
            elif existing_count > 0 and force_reseed:
                logger.info(f"FORCE_RESEED=true: Clearing {existing_count} existing users and reseeding with fresh data")
                # This would need more careful handling to clear all related data
                logger.warning("⚠️ FORCE_RESEED not fully implemented - manual database reset recommended")
                return
            else:
                logger.info("Database is empty, seeding with fresh data")

            # Seed the database using the existing seeder
            from app.utils.db_seeder import seed_database
            seed_database()
            logger.info("✅ Database seeded successfully")

        except Exception as e:
            logger.error(f"❌ Error seeding database: {e}")
            # Don't raise the exception - allow the app to continue without seeding
            logger.warning("⚠️ Application starting without database seeding")