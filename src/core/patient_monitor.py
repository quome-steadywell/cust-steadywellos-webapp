"""Core functionality for patient monitoring and status updates."""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from src import db
from src.models.patient import Patient
from config.config import config

logger = logging.getLogger(__name__)


def load_patient_data() -> List[Dict[str, Any]]:
    """Load patient data from PostgreSQL database.

    Returns:
        List of patient dictionaries

    Raises:
        RuntimeError: If database cannot be accessed
    """
    try:
        logger.info("Loading patient data from PostgreSQL database")

        # Query all patients from the database
        patients = Patient.query.all()

        # Convert to list of dictionaries with template-compatible field names
        patient_data = []
        for patient in patients:
            patient_dict = {
                "id": patient.id,
                "First Name": patient.first_name,
                "Last Name": patient.last_name,
                "Phone Number": patient.phone_number,
                "Email Address": patient.email or "",
                "Protocol": (
                    patient.protocol_type.value if patient.protocol_type else ""
                ),
                "Status": getattr(
                    patient, "status", "Not-Called"
                ),  # Default status if not exists
                # Template compatibility fields
                "firstName": patient.first_name,
                "lastName": patient.last_name,
                "phoneNumber": patient.phone_number,
                "email": patient.email or "",
            }
            patient_data.append(patient_dict)

        logger.info(
            f"Successfully retrieved {len(patient_data)} patients from database"
        )
        return patient_data

    except Exception as e:
        logger.error(f"Failed to load data from database: {str(e)}")
        raise RuntimeError(f"Database access failed: {str(e)}")


def update_patient_status_by_phone(phone_number: str, new_status: str) -> bool:
    """Update a patient's status by phone number.

    Args:
        phone_number: Phone number to identify the patient
        new_status: New status value (e.g., 'Called', 'Not-Called')

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(
            f"Updating patient status for {phone_number} to '{new_status}' in database"
        )

        # Normalize phone number for comparison (remove +, spaces, etc.)
        normalized_search = (
            phone_number.replace("+", "").replace(" ", "").replace("-", "")
        )

        # Find patient by phone number
        patient = Patient.query.filter(
            Patient.phone_number.like(f"%{normalized_search}")
            | Patient.phone_number.like(f"%{phone_number}")
        ).first()

        if patient:
            # Add status field dynamically if it doesn't exist in the model
            # This is a workaround since the current Patient model might not have a status field
            if not hasattr(patient, "status"):
                # We can store this in the notes field or add a custom attribute
                # For now, let's use a custom approach
                logger.info(
                    f"Patient model doesn't have status field, updating notes instead for {patient.first_name} {patient.last_name}"
                )

                # Update the notes field to include status information
                current_notes = patient.notes or ""
                status_prefix = f"Status: {new_status} | Last updated: {datetime.now(timezone.utc).isoformat()} | "

                # Remove any existing status information
                if "Status:" in current_notes:
                    # Find and remove old status line
                    lines = current_notes.split("\n")
                    filtered_lines = [
                        line for line in lines if not line.strip().startswith("Status:")
                    ]
                    current_notes = "\n".join(filtered_lines).strip()

                # Add new status
                patient.notes = status_prefix + current_notes
            else:
                patient.status = new_status

            patient.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(
                f"Successfully updated patient {patient.first_name} {patient.last_name} ({phone_number}) status to '{new_status}'"
            )
            return True
        else:
            logger.warning(f"No patient found with phone number {phone_number}")
            return False

    except Exception as e:
        logger.error(f"Failed to update patient status: {str(e)}")
        db.session.rollback()
        return False


def update_patient_status(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update patient status based on webhook data from Retell.ai.

    Args:
        webhook_data: Dictionary containing webhook payload from Retell.ai

    Returns:
        Dictionary with update results
    """
    try:
        logger.info("Processing Retell.ai webhook to update patient status")

        # Extract relevant information from webhook
        # Handle both direct format and event-based format from Retell AI
        if "call" in webhook_data:
            # Event-based format: {"event": "call_analyzed", "call": {...}}
            call_data = webhook_data.get("call", {})
            call_status = call_data.get("call_status", "")
            to_number = call_data.get("to_number", "")
            recording_url = call_data.get("recording_url", "")
            public_log_url = call_data.get("public_log_url", "")
            call_id = call_data.get("call_id", "")
        else:
            # Direct format: {"call_id": "...", "call_status": "...", ...}
            call_status = webhook_data.get("call_status", "")
            to_number = webhook_data.get("to_number", "")
            recording_url = webhook_data.get("recording_url", "")
            public_log_url = webhook_data.get("public_log_url", "")
            call_id = webhook_data.get("call_id", "")

        if not to_number:
            logger.error("No phone number found in webhook data")
            logger.error(f"Webhook structure: {list(webhook_data.keys())}")
            if "call" in webhook_data:
                logger.error(
                    f"Call data keys: {list(webhook_data.get('call', {}).keys())}"
                )
            return {"status": "error", "message": "No phone number in webhook data"}

        # Determine new status based on call outcome
        if call_status in ["completed", "ended"]:
            new_status = "Called"
        elif call_status in ["failed", "busy", "no-answer"]:
            new_status = "Call Failed"
        else:
            new_status = "Call Attempted"

        # Update the patient status
        success = update_patient_status_by_phone(to_number, new_status)

        # Also update additional call information if provided
        if success and (recording_url or public_log_url or call_id):
            try:
                # Normalize phone number for comparison
                normalized_search = (
                    to_number.replace("+", "").replace(" ", "").replace("-", "")
                )

                # Find patient by phone number
                patient = Patient.query.filter(
                    Patient.phone_number.like(f"%{normalized_search}")
                    | Patient.phone_number.like(f"%{to_number}")
                ).first()

                if patient:
                    # Store call information in notes since we don't have dedicated fields
                    call_info = []
                    if recording_url:
                        call_info.append(f"Recording URL: {recording_url}")
                        logger.info(
                            f"Updated recording URL for patient {to_number}: {recording_url}"
                        )
                    if public_log_url:
                        call_info.append(f"Public Log URL: {public_log_url}")
                        logger.info(
                            f"Updated public log URL for patient {to_number}: {public_log_url}"
                        )
                    if call_id:
                        call_info.append(f"Call ID: {call_id}")
                        logger.info(
                            f"Updated call ID for patient {to_number}: {call_id}"
                        )

                    if call_info:
                        current_notes = patient.notes or ""
                        call_info_str = " | ".join(call_info)
                        patient.notes = f"{call_info_str} | {current_notes}"

                    db.session.commit()
                    logger.info(
                        f"Successfully updated call information for patient {to_number}"
                    )
            except Exception as e:
                logger.error(f"Failed to update call information for patient: {str(e)}")
                db.session.rollback()

        if success:
            return {
                "status": "success",
                "message": f"Updated patient {to_number} status to '{new_status}'",
                "phone_number": to_number,
                "new_status": new_status,
                "recording_url": recording_url,
                "public_log_url": public_log_url,
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to update patient {to_number} status",
                "phone_number": to_number,
            }

    except Exception as e:
        logger.error(f"Error updating patient status from webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


def monitor_and_call() -> Dict[str, Any]:
    """Monitor patient statuses and initiate calls for eligible patients.

    This is a simplified version that doesn't make actual calls since that
    functionality requires additional setup and configuration.

    Returns:
        Dictionary with monitoring results
    """
    try:
        logger.info("Starting patient monitoring process")

        # Load current patient data from database
        patient_data = load_patient_data()

        # Find patients with "Not-Called" status
        not_called_patients = [
            patient
            for patient in patient_data
            if patient.get("Status", "").lower() == "not-called"
        ]

        logger.info(
            f"Found {len(not_called_patients)} patients with 'not-called' status out of {len(patient_data)} total patients"
        )

        return {
            "status": "success",
            "message": f"Monitoring complete. Found {len(not_called_patients)} patients needing calls.",
            "total_patients": len(patient_data),
            "not_called_found": len(not_called_patients),
            "patients_needing_calls": not_called_patients,
        }

    except Exception as e:
        logger.error(f"Error in monitor_and_call: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
