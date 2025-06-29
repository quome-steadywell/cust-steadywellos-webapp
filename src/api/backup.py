"""Database backup/restore API endpoints for admin users."""

import os
import subprocess
import tempfile
from datetime import datetime
from flask import Blueprint, send_file, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import text
from werkzeug.utils import secure_filename

from src import db
from src.models.user import UserRole
from src.models.audit_log import AuditLog
from src.utils.decorators import roles_required, audit_action
from src.utils.logger import get_logger

logger = get_logger()

backup_bp = Blueprint("backup", __name__)


def get_database_config():
    """Get database configuration from environment variables."""
    dev_state = os.getenv("DEV_STATE", "TEST")

    if dev_state == "TEST":
        # Local development
        db_host = os.getenv("POSTGRES_LOCAL_HOST", "localhost")
        db_port = os.getenv("POSTGRES_LOCAL_PORT", "5432")
        db_name = os.getenv("POSTGRES_LOCAL_DB")
        db_user = os.getenv("POSTGRES_LOCAL_USER")
        db_password = os.getenv("POSTGRES_LOCAL_PASSWORD")
    else:
        # Production/Quome Cloud
        db_host = os.getenv("POSTGRES_REMOTE_HOST")
        db_port = os.getenv("POSTGRES_REMOTE_PORT", "5432")
        db_name = os.getenv("POSTGRES_REMOTE_DB")
        db_user = os.getenv("POSTGRES_REMOTE_USER")
        db_password = os.getenv("POSTGRES_REMOTE_PASSWORD")

    return {"host": db_host, "port": db_port, "dbname": db_name, "user": db_user, "password": db_password}


@backup_bp.route("/export", methods=["GET"])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action("export", "database_backup")
def export_database():
    """Export the database as a SQL dump file."""
    try:
        logger.info("Starting database export...")

        # Get database configuration
        db_config = get_database_config()

        # Create temporary file for the dump with PC/Mac compatible filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"steadywellos_{timestamp}.sql"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as tmp_file:
            tmp_path = tmp_file.name

            # Build pg_dump command (data-only backup for safety)
            cmd = [
                "pg_dump",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['dbname']}",
                "--no-password",
                "--data-only",
                "--column-inserts",
                f"--file={tmp_path}",
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["password"]

            # Execute pg_dump
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return jsonify({"error": "Database export failed", "details": result.stderr}), 500

            logger.info(f"Database exported successfully to {tmp_path}")

            # Log the export action manually (audit_action decorator will handle this)
            # The decorator will log this automatically

            # Send the file
            return send_file(tmp_path, as_attachment=True, download_name=filename, mimetype="application/sql")

    except Exception as e:
        logger.error(f"Database export error: {str(e)}")
        return jsonify({"error": "Database export failed", "details": str(e)}), 500


@backup_bp.route("/import", methods=["POST"])
@jwt_required()
@roles_required(UserRole.ADMIN)
@audit_action("import", "database_backup")
def import_database():
    """Import a database from an uploaded SQL dump file."""
    try:
        logger.info("Starting database import...")

        # Check if file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Validate file extension
        if not file.filename.endswith(".sql"):
            return jsonify({"error": "Invalid file type. Only .sql files are allowed"}), 400

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".sql", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            file.save(tmp_path)

            logger.info(f"Saved uploaded file to {tmp_path}")

            # Get database configuration
            db_config = get_database_config()

            # Build psql command
            cmd = [
                "psql",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['dbname']}",
                "--no-password",
                f"--file={tmp_path}",
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config["password"]

            # Execute psql with timeout to prevent hanging
            try:
                result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)  # 2 minute timeout
            except subprocess.TimeoutExpired:
                logger.error("Database import timed out after 2 minutes")
                return (
                    jsonify(
                        {
                            "error": "Database import timed out. This may happen if the database is busy or the backup file is very large."
                        }
                    ),
                    500,
                )

            # Clean up temporary file
            os.unlink(tmp_path)

            if result.returncode != 0:
                logger.error(f"psql import failed: {result.stderr}")
                return jsonify({"error": "Database import failed", "details": result.stderr}), 500

            logger.info("Database imported successfully")

            # Log the import action manually (audit_action decorator will handle this)
            # The decorator will log this automatically

            return jsonify({"message": "Database imported successfully"}), 200

    except Exception as e:
        logger.error(f"Database import error: {str(e)}")
        return jsonify({"error": "Database import failed", "details": str(e)}), 500


@backup_bp.route("/status", methods=["GET"])
@jwt_required()
@roles_required(UserRole.ADMIN)
def backup_status():
    """Get database backup/restore status and capabilities."""
    try:
        # Check if pg_dump and psql are available
        pg_dump_available = subprocess.run(["which", "pg_dump"], capture_output=True).returncode == 0
        psql_available = subprocess.run(["which", "psql"], capture_output=True).returncode == 0

        # Get database size
        result = db.session.execute(text("SELECT pg_database_size(current_database()) as size"))
        db_size = result.fetchone()[0]

        # Get table count
        result = db.session.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        )
        table_count = result.fetchone()[0]

        return (
            jsonify(
                {
                    "status": "available",
                    "capabilities": {"export": pg_dump_available, "import": psql_available},
                    "database_info": {
                        "size_bytes": db_size,
                        "size_mb": round(db_size / (1024 * 1024), 2),
                        "table_count": table_count,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Backup status error: {str(e)}")
        return jsonify({"error": "Failed to get backup status", "details": str(e)}), 500
