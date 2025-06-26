#!/usr/bin/env python
"""
Ensure assessment data consistency after database restore
This script verifies and ensures critical assessment records exist
after a database restore from SQL backup.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, date


def setup_basic_logging():
    """Set up basic console logging for this script without requiring file access"""
    logger = logging.getLogger("palliative_care")

    # Clear any existing handlers
    logger.handlers = []

    # Add a simple console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    return logger


# Set up basic logging before imports to avoid file logging issues
setup_basic_logging()

# Add the parent directory to path so we can import src
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.user import User, UserRole
from src.models.patient import Patient, Gender, ProtocolType
from src.models.protocol import Protocol
from src.models.assessment import Assessment, FollowUpPriority
from src.utils.db_seeder import seed_patient_history

app = create_app()


def check_assessments_data():
    """
    Check and ensure critical assessment records exist, particularly Mary Johnson's urgent assessment
    """
    with app.app_context():
        try:
            # Check if patients table exists before proceeding
            from sqlalchemy import text

            db.session.execute(
                text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='patients'"
                )
            )

            # Get required objects
            mary_johnson = Patient.query.filter_by(
                first_name="Mary", last_name="Johnson"
            ).first()
            heart_failure_protocol = Protocol.query.filter_by(
                protocol_type=ProtocolType.HEART_FAILURE
            ).first()
            nurse = User.query.filter_by(role=UserRole.NURSE).first()

            # If Mary Johnson doesn't exist, check if we can create her
            if not mary_johnson:
                print(
                    "Warning: Mary Johnson patient record not found. Attempting to create it..."
                )

                # Check if we have a nurse user
                if not nurse:
                    # Try to find any user
                    nurse = User.query.filter_by(role=UserRole.ADMIN).first()
                    if not nurse:
                        # Create a default nurse user
                        nurse = User(
                            username="nurse1",
                            email="nurse1@example.com",
                            password="$2b$12$tJ9xPNz4LX5Ql0aaP/RI/.HzP5pWkFHuHBh0gVgVXupQHKfF7zRl2",  # password123 hashed
                            first_name="Sarah",
                            last_name="Nurse",
                            role=UserRole.NURSE,
                            phone_number="555-111-2222",
                            license_number="RN123456",
                            is_active=True,
                            login_attempts=0,
                        )
                        db.session.add(nurse)
                        db.session.commit()
                        print("Created nurse user")

                # Check for heart failure protocol
                if not heart_failure_protocol:
                    print("Error: Heart failure protocol not found. Terminating setup.")
                    return False

                # Create Mary Johnson record
                mary_johnson = Patient(
                    mrn="MRN67890",
                    first_name="Mary",
                    last_name="Johnson",
                    date_of_birth=datetime(1945, 9, 20).date(),
                    gender=Gender.FEMALE,
                    phone_number="555-333-4444",
                    email="mary.johnson@example.com",
                    address="456 Oak Ave, Somewhere, USA",
                    primary_diagnosis="Heart Failure NYHA Class IV",
                    secondary_diagnoses="Diabetes, Chronic Kidney Disease",
                    protocol_type=ProtocolType.HEART_FAILURE,
                    primary_nurse_id=nurse.id,
                    emergency_contact_name="Robert Johnson",
                    emergency_contact_phone="555-444-5555",
                    emergency_contact_relationship="Son",
                    advance_directive=True,
                    dnr_status=True,
                    allergies="Sulfa drugs",
                    notes="Hard of hearing, speak clearly and loudly",
                    is_active=True,
                )
                db.session.add(mary_johnson)
                db.session.commit()
                print(f"Created Mary Johnson record with ID: {mary_johnson.id}")

            # Re-check that required objects exist
            if not heart_failure_protocol:
                print("Error: Heart failure protocol not found")
                return False

            if not nurse:
                print("Error: No nurse user found")
                return False

            # Check if the urgent assessment exists
            urgent_assessment = Assessment.query.filter(
                Assessment.patient_id == mary_johnson.id,
                Assessment.assessment_date >= datetime(2025, 3, 25, 0, 0),
                Assessment.assessment_date <= datetime(2025, 3, 25, 23, 59),
                Assessment.follow_up_priority == FollowUpPriority.HIGH,
            ).first()

            # If urgent assessment is missing, create it
            if not urgent_assessment:
                print("Creating urgent assessment for Mary Johnson...")
                urgent_assessment = Assessment(
                    patient_id=mary_johnson.id,
                    protocol_id=heart_failure_protocol.id,
                    conducted_by_id=nurse.id,
                    assessment_date=datetime(
                        2025, 3, 25, 9, 30
                    ),  # March 25, 2025 9:30 AM
                    responses={
                        "dyspnea": {"value": 8},
                        "edema": {"value": 9},
                        "orthopnea": {"value": 5},
                        "fatigue": {"value": 7},
                        "chest_pain": {"value": True},
                    },
                    symptoms={
                        "dyspnea": 8,
                        "edema": 9,
                        "orthopnea": 5,
                        "fatigue": 7,
                        "chest_pain": 1,
                    },
                    interventions=[
                        {
                            "id": "severe_dyspnea",
                            "title": "Severe Dyspnea Management",
                            "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen.",
                        },
                        {
                            "id": "severe_edema",
                            "title": "Severe Edema Management",
                            "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.",
                        },
                        {
                            "id": "chest_pain_management",
                            "title": "Chest Pain Management",
                            "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed.",
                        },
                    ],
                    notes="Patient reports severe increase in edema, dyspnea, and new onset chest pain. Needs immediate medical attention.",
                    follow_up_needed=True,
                    follow_up_date=datetime(
                        2025, 4, 2, 10, 0
                    ),  # April 2, 2025 10:00 AM
                    follow_up_priority=FollowUpPriority.HIGH,
                    ai_guidance="Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely.",
                )
                db.session.add(urgent_assessment)

                second_urgent_assessment = Assessment(
                    patient_id=mary_johnson.id,
                    protocol_id=heart_failure_protocol.id,
                    conducted_by_id=nurse.id,
                    assessment_date=datetime(
                        2025, 3, 25, 14, 30
                    ),  # March 25, 2025 2:30 PM
                    responses={
                        "dyspnea": {"value": 9},
                        "edema": {"value": 10},
                        "orthopnea": {"value": 6},
                        "fatigue": {"value": 8},
                        "chest_pain": {"value": True},
                    },
                    symptoms={
                        "dyspnea": 9,
                        "edema": 10,
                        "orthopnea": 6,
                        "fatigue": 8,
                        "chest_pain": 1,
                    },
                    interventions=[
                        {
                            "id": "severe_dyspnea",
                            "title": "Severe Dyspnea Management",
                            "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen.",
                        },
                        {
                            "id": "severe_edema",
                            "title": "Severe Edema Management",
                            "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.",
                        },
                        {
                            "id": "chest_pain_management",
                            "title": "Chest Pain Management",
                            "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed.",
                        },
                    ],
                    notes="Follow-up check shows worsening symptoms. Patient sent to emergency department for evaluation.",
                    follow_up_needed=True,
                    follow_up_date=datetime(
                        2025, 3, 28, 10, 0
                    ),  # March 28, 2025 10:00 AM
                    follow_up_priority=FollowUpPriority.HIGH,
                    ai_guidance="Urgent hospital evaluation recommended. Possible acute decompensated heart failure with cardiac ischemia.",
                )
                db.session.add(second_urgent_assessment)
                db.session.commit()
                print("Urgent assessments created.")
            else:
                print("Urgent assessment already exists.")

            # Check if we need to create other assessment history
            patient_count = Patient.query.count()
            assessment_count = Assessment.query.count()

            if assessment_count < 5 and patient_count >= 3:
                print(
                    f"Few assessments found ({assessment_count}). Adding patient history..."
                )

                # Get all patients
                patients = Patient.query.all()
                nurses = User.query.filter_by(role=UserRole.NURSE).all()
                protocols = Protocol.query.all()

                if len(patients) >= 3 and len(nurses) >= 1 and len(protocols) >= 3:
                    # Find the patients by name if possible
                    patient1 = next(
                        (
                            p
                            for p in patients
                            if p.first_name == "John" and p.last_name == "Doe"
                        ),
                        patients[0],
                    )
                    patient2 = next(
                        (
                            p
                            for p in patients
                            if p.first_name == "Mary" and p.last_name == "Johnson"
                        ),
                        patients[1],
                    )
                    patient3 = next(
                        (
                            p
                            for p in patients
                            if p.first_name == "James" and p.last_name == "Wilson"
                        ),
                        patients[2],
                    )

                    # Find protocols by type
                    cancer_protocol = next(
                        (
                            p
                            for p in protocols
                            if p.protocol_type == ProtocolType.CANCER
                        ),
                        protocols[0],
                    )
                    heart_failure_protocol = next(
                        (
                            p
                            for p in protocols
                            if p.protocol_type == ProtocolType.HEART_FAILURE
                        ),
                        protocols[1],
                    )
                    copd_protocol = next(
                        (p for p in protocols if p.protocol_type == ProtocolType.COPD),
                        protocols[2],
                    )

                    # Use available nurses
                    nurse1 = nurses[0]
                    nurse2 = nurses[0] if len(nurses) == 1 else nurses[1]

                    # Seed the history data
                    seed_patient_history(
                        patient1,
                        patient2,
                        patient3,
                        cancer_protocol,
                        heart_failure_protocol,
                        copd_protocol,
                        nurse1,
                        nurse2,
                    )
                    print("Patient assessment history added.")
                else:
                    print(
                        "Not enough patient, nurse, or protocol records to add history."
                    )
            else:
                print(
                    f"Sufficient assessments found ({assessment_count}). No additional history needed."
                )

            return True

        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                print(f"Database tables not ready yet: {str(e)}")
                print(
                    "This is normal during initial setup. The script will be run again after tables are created."
                )
                # Return True to avoid error messages during startup
                return True
            else:
                print(f"Unexpected error: {str(e)}")
                return False


if __name__ == "__main__":
    print("Checking and ensuring assessment data...")
    if check_assessments_data():
        print("Assessment data verification completed successfully!")
    else:
        print("Error during assessment data verification")
        sys.exit(1)
