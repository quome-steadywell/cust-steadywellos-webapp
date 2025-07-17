"""Database seeding utility for development and testing"""

from datetime import datetime, timedelta, date
from src import db
from src.models.user import User, UserRole
from src.models.patient import Patient, Gender, ProtocolType, AdvanceDirectiveStatus
from src.models.protocol import Protocol
from src.models.call import Call, CallStatus
from src.models.assessment import Assessment, FollowUpPriority
from src.models.medication import Medication, MedicationRoute, MedicationFrequency
from src.models.audit_log import AuditLog
from src.utils.logger import get_logger

# Set up logging
logger = get_logger()


def seed_database(test_scenario=None):
    """
    Seed the database with initial data

    Args:
        test_scenario (str, optional): Specific test scenario to generate data for
            Valid values: None, 'date_check'
    """
    logger.info("🌱 Starting database seeding process...")
    logger.info(f"Test scenario: {test_scenario if test_scenario else 'None'}")

    # Clear existing data in the correct order to handle foreign key constraints
    logger.info("🧹 Clearing existing data to reseed database...")

    # Count existing records before deletion for logging
    assessments_count = db.session.query(Assessment).count()
    calls_count = db.session.query(Call).count()
    medications_count = db.session.query(Medication).count()
    patients_count = db.session.query(Patient).count()
    audit_logs_count = db.session.query(AuditLog).count()
    users_count = db.session.query(User).count()

    logger.info(
        f"Found existing records - Users: {users_count}, Patients: {patients_count}, Calls: {calls_count}, Assessments: {assessments_count}, Medications: {medications_count}, Audit Logs: {audit_logs_count}"
    )

    # Delete records
    db.session.query(Assessment).delete()
    logger.info(f"Deleted {assessments_count} assessments")

    db.session.query(Call).delete()
    logger.info(f"Deleted {calls_count} calls")

    db.session.query(Medication).delete()
    logger.info(f"Deleted {medications_count} medications")

    db.session.query(Patient).delete()
    logger.info(f"Deleted {patients_count} patients")

    # Delete protocols to ensure clean seeding with comprehensive data
    protocols_count = db.session.query(Protocol).count()
    db.session.query(Protocol).delete()
    logger.info(f"Deleted {protocols_count} protocols")

    # Delete audit logs before users to avoid foreign key constraint issues
    db.session.query(AuditLog).delete()
    logger.info(f"Deleted {audit_logs_count} audit logs")

    db.session.query(User).delete()
    logger.info(f"Deleted {users_count} users")

    db.session.commit()
    logger.info("✅ Successfully cleared existing data")

    # Create users
    logger.info("👥 Creating seed users...")
    admin = User(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        phone_number="555-123-4567",
        is_active=True,
    )
    admin.password = "password123"

    nurse1 = User(
        username="nurse1",
        email="nurse1@example.com",
        first_name="Jane",
        last_name="Smith",
        role=UserRole.NURSE,
        phone_number="555-234-5678",
        license_number="RN12345",
        is_active=True,
    )
    nurse1.password = "password123"

    nurse2 = User(
        username="nurse2",
        email="nurse2@example.com",
        first_name="Robert",
        last_name="Johnson",
        role=UserRole.NURSE,
        phone_number="555-345-6789",
        license_number="RN67890",
        is_active=True,
    )
    nurse2.password = "password123"

    physician = User(
        username="physician",
        email="physician@example.com",
        first_name="Sarah",
        last_name="Williams",
        role=UserRole.PHYSICIAN,
        phone_number="555-456-7890",
        license_number="MD12345",
        is_active=True,
    )
    physician.password = "password123"

    db.session.add_all([admin, nurse1, nurse2, physician])
    db.session.commit()
    logger.info("✅ Created 4 seed users (admin, nurse1, nurse2, physician)")

    # Get or create protocols
    logger.info("📋 Checking for existing protocols...")
    cancer_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.CANCER).first()
    heart_failure_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.HEART_FAILURE).first()
    copd_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.COPD).first()
    fit_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.FIT).first()

    logger.info(
        f"Found protocols - Cancer: {'✅' if cancer_protocol else '❌'}, Heart Failure: {'✅' if heart_failure_protocol else '❌'}, COPD: {'✅' if copd_protocol else '❌'}, FIT: {'✅' if fit_protocol else '❌'}"
    )

    # Forces creation of default protocols since we're skipping the protocol_ingest step
    logger.info("📝 Creating default protocols in the database...")
    # Create protocols
    if not cancer_protocol:
        cancer_protocol = Protocol(
            name="Cancer Palliative Care Protocol",
            description="Protocol for managing symptoms in patients with advanced cancer",
            protocol_type=ProtocolType.CANCER,
            version="1.0",
            questions=[
                {"id": 1, "text": "Rate your current pain level from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Pain Assessment", "symptom_type": "pain"},
                {"id": 2, "text": "Where is your pain located?", "type": "choice", "choices": ["Head/Neck", "Chest", "Abdomen", "Back", "Arms/Legs", "Multiple locations"], "category": "Pain Assessment", "symptom_type": "pain"},
                {"id": 3, "text": "Are you experiencing nausea or vomiting?", "type": "boolean", "category": "Symptom Assessment", "symptom_type": "nausea"},
                {"id": 4, "text": "Rate your fatigue level from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Symptom Assessment", "symptom_type": "fatigue"},
                {"id": 5, "text": "Are you having difficulty breathing?", "type": "boolean", "category": "Respiratory Assessment", "symptom_type": "dyspnea"},
                {"id": 6, "text": "Have you had a fever in the last 24 hours?", "type": "boolean", "category": "Infection Assessment", "symptom_type": "fever"},
                {"id": 7, "text": "Are you able to eat and drink normally?", "type": "choice", "choices": ["Yes, normal intake", "Reduced but adequate", "Minimal intake", "Unable to eat/drink"], "category": "Nutritional Assessment", "symptom_type": "nutrition"},
                {"id": 8, "text": "How would you describe your appetite?", "type": "choice", "choices": ["Normal", "Reduced", "Poor", "No appetite"], "category": "Nutritional Assessment", "symptom_type": "appetite"},
                {"id": 9, "text": "Are you having any bowel movement changes?", "type": "choice", "choices": ["Normal", "Constipation", "Diarrhea", "No bowel movement >3 days"], "category": "Symptom Assessment", "symptom_type": "bowel"},
                {"id": 10, "text": "Rate your anxiety level from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Psychological Assessment", "symptom_type": "anxiety"},
                {"id": 11, "text": "Are you experiencing any new symptoms since last contact?", "type": "boolean", "category": "General Assessment", "symptom_type": "new_symptoms"},
                {"id": 12, "text": "Have you taken your medications as prescribed?", "type": "choice", "choices": ["Yes, all medications", "Missed some doses", "Stopped some medications", "Unable to take medications"], "category": "Medication Assessment", "symptom_type": "medication_compliance"},
                {"id": 13, "text": "Are you experiencing any confusion or mental changes?", "type": "boolean", "category": "Neurological Assessment", "symptom_type": "confusion"},
                {"id": 14, "text": "Do you have adequate support at home?", "type": "choice", "choices": ["Yes, full support", "Some support", "Limited support", "No support"], "category": "Social Assessment", "symptom_type": "support"},
                {"id": 15, "text": "On a scale of 0-10, how concerned are you about your current condition?", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Overall Assessment", "symptom_type": "concern_level"}
            ],
            decision_tree=[
                {"id": 1, "symptom_type": "pain", "condition": "greater_than", "value": 7, "next_node_id": 2, "intervention_ids": [1, 2]},
                {"id": 2, "symptom_type": "nausea", "condition": "equals", "value": True, "next_node_id": 3, "intervention_ids": [3]},
                {"id": 3, "symptom_type": "dyspnea", "condition": "equals", "value": True, "next_node_id": 4, "intervention_ids": [1, 4]},
                {"id": 4, "symptom_type": "fever", "condition": "equals", "value": True, "next_node_id": 5, "intervention_ids": [4]},
                {"id": 5, "symptom_type": "confusion", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
                {"id": 6, "symptom_type": "concern_level", "condition": "greater_than", "value": 7, "next_node_id": None, "intervention_ids": [4]},
                {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [5, 6]}
            ],
            interventions=[
                {"id": 1, "title": "Emergency Response", "description": "Call 911 or seek immediate emergency care", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe symptoms requiring immediate medical attention"},
                {"id": 2, "title": "Pain Management", "description": "Adjust pain medications per protocol", "priority": "high", "symptom_type": "pain", "instructions": "Follow WHO analgesic ladder"},
                {"id": 3, "title": "Nausea Management", "description": "Anti-emetic protocol", "priority": "high", "symptom_type": "nausea", "instructions": "Administer prescribed anti-emetics"},
                {"id": 4, "title": "Physician Contact", "description": "Contact oncologist within 2-4 hours", "priority": "high", "symptom_type": "urgent_symptoms", "instructions": "Report concerning symptoms to physician"},
                {"id": 5, "title": "Home Care Instructions", "description": "Continue current care plan with monitoring", "priority": "medium", "symptom_type": "stable", "instructions": "Follow home care guidelines"},
                {"id": 6, "title": "Comfort Measures", "description": "Provide comfort and supportive care", "priority": "medium", "symptom_type": "comfort", "instructions": "Non-pharmacological comfort measures"}
            ],
            is_active=True,
        )

        if not heart_failure_protocol:
            heart_failure_protocol = Protocol(
                name="Heart Failure Palliative Care Protocol",
                description="Protocol for managing symptoms in patients with advanced heart failure",
                protocol_type=ProtocolType.HEART_FAILURE,
                version="1.0",
                questions=[
                    {"id": 1, "text": "Rate your shortness of breath from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Respiratory Assessment", "symptom_type": "dyspnea"},
                    {"id": 2, "text": "Are you short of breath at rest?", "type": "boolean", "category": "Respiratory Assessment", "symptom_type": "dyspnea_rest"},
                    {"id": 3, "text": "How many pillows do you need to sleep comfortably?", "type": "choice", "choices": ["0-1 pillow", "2 pillows", "3 pillows", "Unable to lie flat"], "category": "Respiratory Assessment", "symptom_type": "orthopnea"},
                    {"id": 4, "text": "Do you have swelling in your legs, ankles, or feet?", "type": "boolean", "category": "Fluid Assessment", "symptom_type": "edema"},
                    {"id": 5, "text": "What is your weight today compared to yesterday?", "type": "choice", "choices": ["Same or less", "1-2 lbs more", "3-5 lbs more", "More than 5 lbs"], "category": "Fluid Assessment", "symptom_type": "weight_gain"},
                    {"id": 6, "text": "How is your energy level today?", "type": "choice", "choices": ["Normal", "Slightly tired", "Very tired", "Exhausted"], "category": "Activity Assessment", "symptom_type": "fatigue"},
                    {"id": 7, "text": "Are you experiencing chest pain or discomfort?", "type": "boolean", "category": "Cardiac Assessment", "symptom_type": "chest_pain"},
                    {"id": 8, "text": "Have you been dizzy or lightheaded?", "type": "boolean", "category": "Cardiac Assessment", "symptom_type": "dizziness"},
                    {"id": 9, "text": "Are you taking your medications as prescribed?", "type": "choice", "choices": ["Yes, all medications", "Missed some doses", "Stopped some medications", "Unable to take"], "category": "Medication Assessment", "symptom_type": "medication_compliance"},
                    {"id": 10, "text": "How much fluid have you had today?", "type": "choice", "choices": ["Less than 6 cups", "6-8 cups", "8-10 cups", "More than 10 cups"], "category": "Fluid Assessment", "symptom_type": "fluid_intake"},
                    {"id": 11, "text": "Have you been following your low-sodium diet?", "type": "choice", "choices": ["Strictly", "Mostly", "Sometimes", "Not at all"], "category": "Dietary Assessment", "symptom_type": "diet_compliance"},
                    {"id": 12, "text": "Are you urinating less than usual?", "type": "boolean", "category": "Fluid Assessment", "symptom_type": "urine_output"},
                    {"id": 13, "text": "Have you had any episodes of rapid heartbeat?", "type": "boolean", "category": "Cardiac Assessment", "symptom_type": "palpitations"},
                    {"id": 14, "text": "How far can you walk without getting short of breath?", "type": "choice", "choices": ["Normal distance", "1-2 blocks", "Less than 1 block", "Few steps only"], "category": "Activity Assessment", "symptom_type": "exercise_tolerance"},
                    {"id": 15, "text": "On a scale of 0-10, how concerned are you about your symptoms?", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Overall Assessment", "symptom_type": "concern_level"}
                ],
                decision_tree=[
                    {"id": 1, "symptom_type": "dyspnea_rest", "condition": "equals", "value": True, "next_node_id": 2, "intervention_ids": [1]},
                    {"id": 2, "symptom_type": "weight_gain", "condition": "in", "value": ["3-5 lbs more", "More than 5 lbs"], "next_node_id": 3, "intervention_ids": [2]},
                    {"id": 3, "symptom_type": "chest_pain", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
                    {"id": 4, "symptom_type": "edema", "condition": "equals", "value": True, "next_node_id": 5, "intervention_ids": [2, 5]},
                    {"id": 5, "symptom_type": "medication_compliance", "condition": "not_equals", "value": "Yes, all medications", "next_node_id": None, "intervention_ids": [6]},
                    {"id": 6, "symptom_type": "exercise_tolerance", "condition": "in", "value": ["Less than 1 block", "Few steps only"], "next_node_id": None, "intervention_ids": [3]},
                    {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [4, 5]}
                ],
                interventions=[
                    {"id": 1, "title": "Emergency Response", "description": "Call 911 for severe breathing difficulty", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe dyspnea, chest pain, or acute symptoms"},
                    {"id": 2, "title": "Diuretic Adjustment", "description": "Contact physician for medication adjustment", "priority": "high", "symptom_type": "fluid_overload", "instructions": "Signs of fluid retention requiring medical evaluation"},
                    {"id": 3, "title": "Activity Modification", "description": "Reduce activity and rest", "priority": "medium", "symptom_type": "activity_intolerance", "instructions": "Balance activity with rest periods"},
                    {"id": 4, "title": "Dietary Counseling", "description": "Review low-sodium diet adherence", "priority": "medium", "symptom_type": "diet", "instructions": "Reinforce dietary restrictions"},
                    {"id": 5, "title": "Weight Monitoring", "description": "Daily weight monitoring with reporting thresholds", "priority": "medium", "symptom_type": "weight_management", "instructions": "Report weight gain >2-3 lbs in 24 hours"},
                    {"id": 6, "title": "Medication Review", "description": "Review and adjust medication regimen", "priority": "high", "symptom_type": "medication", "instructions": "Ensure proper medication compliance"}
                ],
                is_active=True,
            )

        if not copd_protocol:
            copd_protocol = Protocol(
                name="COPD Palliative Care Protocol",
                description="Protocol for managing symptoms in patients with advanced COPD",
                protocol_type=ProtocolType.COPD,
                version="1.0",
                questions=[
                    {"id": 1, "text": "Rate your breathing difficulty from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Respiratory Assessment", "symptom_type": "dyspnea"},
                    {"id": 2, "text": "What color is your sputum today?", "type": "choice", "choices": ["Clear/White", "Yellow", "Green", "Brown", "Blood-tinged"], "category": "Respiratory Assessment", "symptom_type": "sputum"},
                    {"id": 3, "text": "How much sputum are you producing?", "type": "choice", "choices": ["Normal amount", "More than usual", "Much more than usual", "Unable to clear"], "category": "Respiratory Assessment", "symptom_type": "sputum_volume"},
                    {"id": 4, "text": "How is your cough compared to usual?", "type": "choice", "choices": ["Same as usual", "Worse than usual", "Much worse", "New persistent cough"], "category": "Respiratory Assessment", "symptom_type": "cough"},
                    {"id": 5, "text": "Have you had a fever or chills?", "type": "boolean", "category": "Infection Assessment", "symptom_type": "fever"},
                    {"id": 6, "text": "Are you using your rescue inhaler more than usual?", "type": "choice", "choices": ["No", "Slightly more", "Much more", "Constantly"], "category": "Medication Assessment", "symptom_type": "rescue_inhaler"},
                    {"id": 7, "text": "How many steps can you take before getting short of breath?", "type": "choice", "choices": ["Normal activity", "100+ steps", "50-100 steps", "Less than 50 steps"], "category": "Activity Assessment", "symptom_type": "exercise_tolerance"},
                    {"id": 8, "text": "Are you sleeping through the night?", "type": "choice", "choices": ["Yes, normal sleep", "Some interruption", "Frequent awakening", "Unable to sleep"], "category": "Sleep Assessment", "symptom_type": "sleep"},
                    {"id": 9, "text": "Have you been exposed to any respiratory irritants?", "type": "boolean", "category": "Environmental Assessment", "symptom_type": "irritants"},
                    {"id": 10, "text": "Are you taking your COPD medications as prescribed?", "type": "choice", "choices": ["Yes, all medications", "Missed some doses", "Stopped some medications", "Unable to use inhalers"], "category": "Medication Assessment", "symptom_type": "medication_compliance"},
                    {"id": 11, "text": "How is your appetite?", "type": "choice", "choices": ["Normal", "Reduced", "Poor", "No appetite"], "category": "Nutritional Assessment", "symptom_type": "appetite"},
                    {"id": 12, "text": "Are you experiencing chest tightness?", "type": "boolean", "category": "Respiratory Assessment", "symptom_type": "chest_tightness"},
                    {"id": 13, "text": "Have you had any ankle or leg swelling?", "type": "boolean", "category": "Cardiac Assessment", "symptom_type": "edema"},
                    {"id": 14, "text": "How is your energy level compared to usual?", "type": "choice", "choices": ["Normal", "Slightly tired", "Very tired", "Exhausted"], "category": "Activity Assessment", "symptom_type": "fatigue"},
                    {"id": 15, "text": "On a scale of 0-10, how worried are you about your breathing?", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Overall Assessment", "symptom_type": "concern_level"}
                ],
                decision_tree=[
                    {"id": 1, "symptom_type": "dyspnea", "condition": "greater_than", "value": 7, "next_node_id": 2, "intervention_ids": [1]},
                    {"id": 2, "symptom_type": "sputum", "condition": "in", "value": ["Green", "Blood-tinged"], "next_node_id": 3, "intervention_ids": [2]},
                    {"id": 3, "symptom_type": "fever", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [2]},
                    {"id": 4, "symptom_type": "rescue_inhaler", "condition": "in", "value": ["Much more", "Constantly"], "next_node_id": 5, "intervention_ids": [3]},
                    {"id": 5, "symptom_type": "exercise_tolerance", "condition": "equals", "value": "Less than 50 steps", "next_node_id": None, "intervention_ids": [4]},
                    {"id": 6, "symptom_type": "edema", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
                    {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [5, 6]}
                ],
                interventions=[
                    {"id": 1, "title": "Emergency Response", "description": "Call 911 for severe respiratory distress", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe dyspnea, confusion, or respiratory failure"},
                    {"id": 2, "title": "Infection Protocol", "description": "Antibiotic therapy and physician contact", "priority": "high", "symptom_type": "infection", "instructions": "Signs of respiratory infection requiring treatment"},
                    {"id": 3, "title": "Bronchodilator Optimization", "description": "Increase rescue medication use", "priority": "high", "symptom_type": "bronchospasm", "instructions": "Optimize bronchodilator therapy"},
                    {"id": 4, "title": "Activity Modification", "description": "Energy conservation techniques", "priority": "medium", "symptom_type": "activity_limitation", "instructions": "Pace activities and use breathing techniques"},
                    {"id": 5, "title": "Respiratory Therapy", "description": "Breathing exercises and positioning", "priority": "medium", "symptom_type": "breathing_support", "instructions": "Pursed lip breathing and optimal positioning"},
                    {"id": 6, "title": "Environmental Control", "description": "Avoid triggers and irritants", "priority": "medium", "symptom_type": "environmental", "instructions": "Minimize exposure to respiratory irritants"}
                ],
                is_active=True,
            )

        if not fit_protocol:
            fit_protocol = Protocol(
                name="FIT Protocol - Wellness Monitoring",
                description="Protocol for monitoring very fit individuals with wellness and fitness assessments",
                protocol_type=ProtocolType.FIT,
                version="1.0",
                questions=[
                    {"id": 1, "text": "What is the main reason for your call today?", "type": "choice", "choices": ["Routine check-in", "New symptoms", "Medication question", "Emergency concern"], "category": "Triage Assessment", "symptom_type": "call_reason"},
                    {"id": 2, "text": "How urgent do you feel your concern is?", "type": "choice", "choices": ["Not urgent", "Somewhat urgent", "Very urgent", "Emergency"], "category": "Triage Assessment", "symptom_type": "urgency"},
                    {"id": 3, "text": "Are you experiencing any pain?", "type": "boolean", "category": "Symptom Assessment", "symptom_type": "pain"},
                    {"id": 4, "text": "If yes, rate your pain from 0-10", "type": "numeric", "min_value": 0, "max_value": 10, "category": "Pain Assessment", "symptom_type": "pain_level"},
                    {"id": 5, "text": "Are you having any breathing difficulties?", "type": "boolean", "category": "Respiratory Assessment", "symptom_type": "dyspnea"},
                    {"id": 6, "text": "Have you had any chest pain or pressure?", "type": "boolean", "category": "Cardiac Assessment", "symptom_type": "chest_pain"},
                    {"id": 7, "text": "Are you experiencing nausea or vomiting?", "type": "boolean", "category": "GI Assessment", "symptom_type": "nausea"},
                    {"id": 8, "text": "Have you had a fever in the last 24 hours?", "type": "boolean", "category": "Infection Assessment", "symptom_type": "fever"},
                    {"id": 9, "text": "Are you having any neurological symptoms?", "type": "choice", "choices": ["None", "Headache", "Dizziness", "Confusion", "Weakness"], "category": "Neurological Assessment", "symptom_type": "neuro_symptoms"},
                    {"id": 10, "text": "How long have you had these symptoms?", "type": "choice", "choices": ["Less than 1 hour", "1-6 hours", "6-24 hours", "More than 24 hours"], "category": "Timeline Assessment", "symptom_type": "symptom_duration"},
                    {"id": 11, "text": "Have you taken any medications for these symptoms?", "type": "boolean", "category": "Medication Assessment", "symptom_type": "self_medication"},
                    {"id": 12, "text": "Do you have any known allergies to medications?", "type": "boolean", "category": "Safety Assessment", "symptom_type": "allergies"},
                    {"id": 13, "text": "Are you able to speak in full sentences?", "type": "boolean", "category": "Respiratory Assessment", "symptom_type": "speech_difficulty"},
                    {"id": 14, "text": "Do you have a reliable way to get to medical care if needed?", "type": "boolean", "category": "Access Assessment", "symptom_type": "transportation"},
                    {"id": 15, "text": "Is there anyone with you who can help if needed?", "type": "boolean", "category": "Support Assessment", "symptom_type": "support_available"}
                ],
                decision_tree=[
                    {"id": 1, "symptom_type": "urgency", "condition": "equals", "value": "Emergency", "next_node_id": None, "intervention_ids": [1]},
                    {"id": 2, "symptom_type": "chest_pain", "condition": "equals", "value": True, "next_node_id": 3, "intervention_ids": [1]},
                    {"id": 3, "symptom_type": "dyspnea", "condition": "equals", "value": True, "next_node_id": 4, "intervention_ids": [2]},
                    {"id": 4, "symptom_type": "speech_difficulty", "condition": "equals", "value": False, "next_node_id": None, "intervention_ids": [1]},
                    {"id": 5, "symptom_type": "pain_level", "condition": "greater_than", "value": 7, "next_node_id": None, "intervention_ids": [2]},
                    {"id": 6, "symptom_type": "symptom_duration", "condition": "equals", "value": "Less than 1 hour", "next_node_id": 7, "intervention_ids": [3]},
                    {"id": 7, "symptom_type": "urgency", "condition": "equals", "value": "Very urgent", "next_node_id": None, "intervention_ids": [3]},
                    {"id": 8, "symptom_type": "call_reason", "condition": "equals", "value": "Routine check-in", "next_node_id": None, "intervention_ids": [5, 6]}
                ],
                interventions=[
                    {"id": 1, "title": "Emergency Dispatch", "description": "Call 911 immediately", "priority": "urgent", "symptom_type": "emergency", "instructions": "Life-threatening symptoms requiring immediate emergency response"},
                    {"id": 2, "title": "Urgent Medical Care", "description": "Seek medical care within 1 hour", "priority": "urgent", "symptom_type": "urgent", "instructions": "Serious symptoms requiring prompt medical evaluation"},
                    {"id": 3, "title": "Same Day Medical Care", "description": "See healthcare provider today", "priority": "high", "symptom_type": "same_day", "instructions": "Symptoms requiring medical evaluation within hours"},
                    {"id": 4, "title": "Next Day Appointment", "description": "Schedule appointment within 24 hours", "priority": "medium", "symptom_type": "next_day", "instructions": "Symptoms requiring medical follow-up soon"},
                    {"id": 5, "title": "Home Care Instructions", "description": "Self-care with monitoring", "priority": "low", "symptom_type": "home_care", "instructions": "Symptoms manageable at home with guidelines"},
                    {"id": 6, "title": "Follow-up Call", "description": "Schedule follow-up call", "priority": "low", "symptom_type": "follow_up", "instructions": "Monitor symptoms and provide support"}
                ],
                is_active=True,
            )

    # Add any newly created protocols
    protocols_to_add = []
    if cancer_protocol and not cancer_protocol.id:
        protocols_to_add.append(cancer_protocol)
    if heart_failure_protocol and not heart_failure_protocol.id:
        protocols_to_add.append(heart_failure_protocol)
    if copd_protocol and not copd_protocol.id:
        protocols_to_add.append(copd_protocol)
    if fit_protocol and not fit_protocol.id:
        protocols_to_add.append(fit_protocol)

    if protocols_to_add:
        db.session.add_all(protocols_to_add)
        db.session.commit()
        logger.info(f"✅ Added {len(protocols_to_add)} new protocols to the database.")
    else:
        logger.info("✅ All required protocols already exist")

    # Create patients
    logger.info("🏥 Creating seed patients...")
    patient1 = Patient(
        mrn="MRN12345",
        first_name="Josh",
        last_name="Kerm",
        date_of_birth=date(1950, 5, 15),
        gender=Gender.MALE,
        phone_number="17205560774",
        email="josh.kerm@steadywell.com",
        address="123 Main St, Anytown, USA",
        primary_diagnosis="Stage IV Lung Cancer",
        secondary_diagnoses="COPD, Hypertension",
        protocol_type=ProtocolType.CANCER,
        primary_nurse_id=nurse1.id,
        emergency_contact_name="Jane Smith",
        emergency_contact_phone="555-222-3333",
        emergency_contact_relationship="Spouse",
        emergency_contact_can_share_medical_info=True,
        advance_directive=True,
        advance_directive_status=AdvanceDirectiveStatus.COMPLETE,
        dnr_status=True,
        allergies="None",
        notes="Patient prefers morning calls",
        is_active=True,
    )

    patient2 = Patient(
        mrn="MRN67890",
        first_name="Tim",
        last_name="Raderstorf",
        date_of_birth=date(1945, 9, 20),
        gender=Gender.MALE,
        phone_number="16142103049",
        email="tim.raderstorf@steadywell.com",
        address="456 Oak Ave, Somewhere, USA",
        primary_diagnosis="Heart Failure NYHA Class IV",
        secondary_diagnoses="Diabetes, Chronic Kidney Disease",
        protocol_type=ProtocolType.HEART_FAILURE,
        primary_nurse_id=nurse2.id,
        emergency_contact_name="Robert Johnson",
        emergency_contact_phone="555-444-5555",
        emergency_contact_relationship="Son",
        emergency_contact_can_share_medical_info=True,
        advance_directive=True,
        advance_directive_status=AdvanceDirectiveStatus.IN_PROGRESS,
        dnr_status=True,
        allergies="None",
        notes="Hard of hearing, speak clearly and loudly",
        is_active=True,
    )

    patient3 = Patient(
        mrn="MRN24680",
        first_name="Frederic",
        last_name="Sauve-Hoover",
        date_of_birth=date(1953, 3, 10),
        gender=Gender.MALE,
        phone_number="17809568114",
        email="sauvehoover@gmail.com",
        address="789 Pine St, Elsewhere, USA",
        primary_diagnosis="End-stage COPD, GOLD Stage IV",
        secondary_diagnoses="Cor Pulmonale, Osteoporosis",
        protocol_type=ProtocolType.COPD,
        primary_nurse_id=nurse1.id,
        emergency_contact_name="Jane Smith",
        emergency_contact_phone="555-666-7777",
        emergency_contact_relationship="Daughter",
        emergency_contact_can_share_medical_info=False,
        advance_directive=True,
        advance_directive_status=AdvanceDirectiveStatus.COMPLETE,
        dnr_status=True,
        allergies="None known",
        notes="Uses oxygen 24/7, 2L via nasal cannula",
        is_active=True,
    )

    # Add Pete Jarvis as new patient with FIT Protocol
    patient4 = Patient(
        mrn="MRN13579",
        first_name="Pete",
        last_name="Jarvis",
        date_of_birth=date(1975, 8, 12),
        gender=Gender.MALE,
        phone_number="12066968474",
        email="pkjarvis01@gmail.com",
        address="321 Fitness Ave, Athletic City, USA",
        primary_diagnosis="Very Fit Individual - Wellness Monitoring",
        secondary_diagnoses="None",
        protocol_type=ProtocolType.FIT,
        primary_nurse_id=nurse1.id,
        emergency_contact_name="Sarah Jarvis",
        emergency_contact_phone="555-777-8888",
        emergency_contact_relationship="Spouse",
        emergency_contact_can_share_medical_info=True,
        advance_directive=False,
        advance_directive_status=AdvanceDirectiveStatus.NOT_STARTED,
        dnr_status=False,
        allergies="None known",
        notes="Very active individual, monitors wellness and fitness metrics",
        is_active=True,
    )

    db.session.add_all([patient1, patient2, patient3, patient4])
    db.session.commit()
    logger.info("✅ Created 4 seed patients (Josh Kerm, Tim Raderstorf, Frederic Sauve-Hoover, Pete Jarvis)")

    # Create medications
    logger.info("💊 Creating seed medications...")
    med1 = Medication(
        patient_id=patient1.id,
        name="Morphine Sulfate",
        dosage="15",
        dosage_unit="mg",
        route=MedicationRoute.ORAL,
        frequency=MedicationFrequency.EVERY_MORNING,
        indication="Pain management",
        prescriber="Dr. Williams",
        start_date=date.today() - timedelta(days=30),
        instructions="Take with food",
        is_active=True,
    )

    med2 = Medication(
        patient_id=patient1.id,
        name="Ondansetron",
        dosage="4",
        dosage_unit="mg",
        route=MedicationRoute.ORAL,
        frequency=MedicationFrequency.AS_NEEDED,
        indication="Nausea",
        prescriber="Dr. Williams",
        start_date=date.today() - timedelta(days=30),
        instructions="Take as needed for nausea, up to 3 times daily",
        is_active=True,
    )

    med3 = Medication(
        patient_id=patient2.id,
        name="Furosemide",
        dosage="40",
        dosage_unit="mg",
        route=MedicationRoute.ORAL,
        frequency=MedicationFrequency.TWICE_DAILY,
        indication="Edema management",
        prescriber="Dr. Smith",
        start_date=date.today() - timedelta(days=60),
        instructions="Take first dose in morning, second dose no later than 4pm",
        is_active=True,
    )

    med4 = Medication(
        patient_id=patient3.id,
        name="Tiotropium",
        dosage="18",
        dosage_unit="mcg",
        route=MedicationRoute.INHALATION,
        frequency=MedicationFrequency.ONCE_DAILY,
        indication="COPD management",
        prescriber="Dr. Johnson",
        start_date=date.today() - timedelta(days=90),
        instructions="Use once daily with HandiHaler device",
        is_active=True,
    )

    db.session.add_all([med1, med2, med3, med4])
    db.session.commit()
    logger.info("✅ Created 4 seed medications")

    # Create calls
    logger.info("📞 Creating seed calls...")
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    call1 = Call(
        patient_id=patient1.id,
        conducted_by_id=nurse1.id,
        scheduled_time=yesterday.replace(hour=10, minute=0, second=0, microsecond=0),
        start_time=yesterday.replace(hour=10, minute=5, second=0, microsecond=0),
        end_time=yesterday.replace(hour=10, minute=20, second=0, microsecond=0),
        duration=15 * 60,  # 15 minutes in seconds
        status=CallStatus.COMPLETED,
        call_type="assessment",
        notes="Patient reported increased pain levels",
        twilio_call_sid="CA123456789",
        recording_url="https://example.com/recordings/call1.mp3",
        transcript="Nurse: How are you feeling today? Patient: My pain has been worse, about a 7 out of 10.",
    )

    call2 = Call(
        patient_id=patient2.id,
        conducted_by_id=nurse2.id,
        scheduled_time=yesterday.replace(hour=14, minute=0, second=0, microsecond=0),
        start_time=yesterday.replace(hour=14, minute=2, second=0, microsecond=0),
        end_time=yesterday.replace(hour=14, minute=18, second=0, microsecond=0),
        duration=16 * 60,  # 16 minutes in seconds
        status=CallStatus.COMPLETED,
        call_type="assessment",
        notes="Patient reports increased edema in ankles",
        twilio_call_sid="CA987654321",
        recording_url="https://example.com/recordings/call2.mp3",
        transcript="Nurse: How is your breathing today? Patient: A bit harder than usual, and my ankles are more swollen.",
    )

    call3 = Call(
        patient_id=patient3.id,
        conducted_by_id=nurse1.id,
        scheduled_time=today.replace(hour=11, minute=0, second=0, microsecond=0),
        status=CallStatus.SCHEDULED,
        call_type="assessment",
    )

    call4 = Call(
        patient_id=patient1.id,
        conducted_by_id=nurse1.id,
        scheduled_time=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        status=CallStatus.SCHEDULED,
        call_type="follow_up",
    )

    db.session.add_all([call1, call2, call3, call4])
    db.session.commit()
    logger.info("✅ Created 4 seed calls")

    # Create assessments
    logger.info("📊 Creating seed assessments...")
    assessment1 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        call_id=call1.id,
        assessment_date=yesterday.replace(hour=10, minute=20, second=0, microsecond=0),
        responses={
            "pain_level": {"value": 7},
            "pain_location": {"value": "Lower back and hips"},
            "nausea": {"value": 3},
            "fatigue": {"value": 6},
            "appetite": {"value": 4},
        },
        symptoms={"pain": 7, "nausea": 3, "fatigue": 6, "appetite": 4},
        interventions=[
            {
                "id": "severe_pain",
                "title": "Severe Pain Management",
                "description": "Urgent review of pain medication. Consider opioid rotation or adjustment.",
            }
        ],
        notes="Patient reports pain medication not lasting full duration between doses",
        follow_up_needed=True,
        follow_up_date=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Recommend increasing morphine dosage or frequency. Consider adding breakthrough pain medication.",
    )

    assessment2 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        call_id=call2.id,
        assessment_date=yesterday.replace(hour=14, minute=18, second=0, microsecond=0),
        responses={
            "dyspnea": {"value": 5},
            "edema": {"value": 7},
            "orthopnea": {"value": 3},
            "fatigue": {"value": 6},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 5,
            "edema": 7,
            "orthopnea": 3,
            "fatigue": 6,
            "chest_pain": 0,
        },
        interventions=[
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.",
            }
        ],
        notes="Patient has been compliant with fluid restriction but still has increased edema",
        follow_up_needed=True,
        follow_up_date=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
        follow_up_priority=FollowUpPriority.MEDIUM,
        ai_guidance="Consider temporary increase in furosemide dose. Monitor weight daily and fluid intake.",
    )

    db.session.add_all([assessment1, assessment2])
    db.session.commit()
    logger.info("✅ Created 2 initial assessments")

    # Add date-specific test data if requested
    if test_scenario == "date_check":
        logger.info("📅 Adding date-specific test data...")
        seed_date_check_data()

    # Add recent assessment history for patient details view
    logger.info("📈 Adding patient assessment history...")
    seed_patient_history(
        patient1,
        patient2,
        patient3,
        patient4,
        cancer_protocol,
        heart_failure_protocol,
        copd_protocol,
        fit_protocol,
        nurse1,
        nurse2,
    )

    logger.info("✅ Database seeded successfully! 🎉")


def seed_date_check_data():
    """Add test data specifically for date handling test cases"""
    logger.info("📅 Starting date check data seeding...")
    # Get reference to main entities
    patient = Patient.query.filter_by(first_name="Mary").first()
    nurse = User.query.filter_by(first_name="Robert").first()
    # Ensure we get the heart_failure_protocol from the database
    protocol = Protocol.query.filter_by(protocol_type=ProtocolType.HEART_FAILURE).first()

    if not protocol:
        logger.error("❌ Error: Heart Failure protocol not found in database. Date test data will not be added.")
        return

    # Get date references
    today = datetime.now()

    # Create assessments spanning multiple weeks
    # These dates are carefully selected to test various week boundaries

    # 1. Last week (Sunday)
    current_weekday = today.weekday()  # Monday=0, Sunday=6
    days_since_sunday = (current_weekday + 1) % 7  # Convert to Sunday=0 basis
    this_sunday = today - timedelta(days=days_since_sunday)
    last_week_sunday = this_sunday - timedelta(days=7)  # Go back to previous week's Sunday
    assessment1 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=last_week_sunday.replace(hour=9, minute=30),
        responses={"edema": {"value": 6}},
        symptoms={"edema": 6},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )

    # 2. Last week (Wednesday)
    last_week_wednesday = last_week_sunday + timedelta(days=3)  # Sunday + 3 days = Wednesday
    assessment2 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=last_week_wednesday.replace(hour=14, minute=15),
        responses={"dyspnea": {"value": 5}},
        symptoms={"dyspnea": 5},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.LOW,
    )

    # 3. This week (Sunday)
    # We already computed this_sunday above, reuse it
    this_week_sunday = this_sunday
    if this_week_sunday.date() > today.date():  # Ensure we're not in the future
        this_week_sunday = today - timedelta(days=7)
    assessment3 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=this_week_sunday.replace(hour=10, minute=0),
        responses={"edema": {"value": 7}},
        symptoms={"edema": 7},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )

    # 4. This week (Monday)
    this_week_monday = this_sunday + timedelta(days=1)  # Sunday + 1 day = Monday
    if this_week_monday.date() > today.date():  # Ensure we're not in the future
        this_week_monday = this_week_monday - timedelta(days=7)
    assessment4 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=this_week_monday.replace(hour=11, minute=30),
        responses={"fatigue": {"value": 6}},
        symptoms={"fatigue": 6},
        follow_up_needed=False,
    )

    # 5. This week (Current day)
    assessment5 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=today.replace(hour=9, minute=0),
        responses={"orthopnea": {"value": 4}},
        symptoms={"orthopnea": 4},
        follow_up_needed=False,
    )

    # 6. Next week (Monday)
    next_week_monday = today + timedelta(days=7 - today.weekday())
    assessment6 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=next_week_monday.replace(hour=10, minute=15),
        responses={"chest_pain": {"value": True}},
        symptoms={"chest_pain": 1},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH,
        follow_up_date=next_week_monday + timedelta(days=1),
    )

    # Add all assessments
    db.session.add_all([assessment1, assessment2, assessment3, assessment4, assessment5, assessment6])
    db.session.commit()

    logger.info("✅ Date check test data added successfully")


def seed_patient_history(
    patient1,
    patient2,
    patient3,
    patient4,
    cancer_protocol,
    heart_failure_protocol,
    copd_protocol,
    fit_protocol,
    nurse1,
    nurse2,
):
    """Add assessment history for patients to populate patient details pages"""

    logger.info("📈 Starting patient assessment history creation...")
    today = datetime.now()

    # Add urgent follow-up assessment for Mary Johnson (patient2) on 3/25/2025
    urgent_assessment = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=datetime(2025, 3, 25, 9, 30),  # March 25, 2025 9:30 AM
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
        follow_up_date=datetime(2025, 4, 2, 10, 0),  # April 2, 2025 10:00 AM
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely.",
    )
    db.session.add(urgent_assessment)

    # For the urgent follow-up to appear properly in the dashboard, we'll add a second assessment
    # specifically for 3/25/2025 date shown in the dashboard
    second_urgent_assessment = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=datetime(2025, 3, 25, 14, 30),  # March 25, 2025 2:30 PM
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
        follow_up_date=datetime(2025, 3, 28, 10, 0),  # March 28, 2025 10:00 AM
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Urgent hospital evaluation recommended. Possible acute decompensated heart failure with cardiac ischemia.",
    )
    db.session.add(second_urgent_assessment)
    db.session.commit()

    # Create assessment history for patient1 (cancer patient)
    # Last 4 weeks of assessments, twice per week
    patient1_assessments = []

    # 4 weeks ago
    date_4w_ago = today - timedelta(days=28)
    assessment1 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_4w_ago.replace(hour=9, minute=30),
        responses={
            "pain_level": {"value": 4},
            "pain_location": {"value": "Lower back"},
            "nausea": {"value": 2},
            "fatigue": {"value": 5},
            "appetite": {"value": 6},
        },
        symptoms={"pain": 4, "nausea": 2, "fatigue": 5, "appetite": 6},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            }
        ],
        notes="Patient reports stable pain with current medication regimen",
        follow_up_needed=False,
    )
    patient1_assessments.append(assessment1)

    # 3.5 weeks ago
    date_3w5d_ago = today - timedelta(days=25)
    assessment2 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_3w5d_ago.replace(hour=14, minute=0),
        responses={
            "pain_level": {"value": 5},
            "pain_location": {"value": "Lower back and right hip"},
            "nausea": {"value": 3},
            "fatigue": {"value": 6},
            "appetite": {"value": 5},
        },
        symptoms={"pain": 5, "nausea": 3, "fatigue": 6, "appetite": 5},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            }
        ],
        notes="Patient reports slight increase in pain, spreading to hip",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.LOW,
    )
    patient1_assessments.append(assessment2)

    # 3 weeks ago
    date_3w_ago = today - timedelta(days=21)
    assessment3 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_3w_ago.replace(hour=10, minute=15),
        responses={
            "pain_level": {"value": 6},
            "pain_location": {"value": "Lower back and right hip"},
            "nausea": {"value": 4},
            "fatigue": {"value": 6},
            "appetite": {"value": 4},
        },
        symptoms={"pain": 6, "nausea": 4, "fatigue": 6, "appetite": 4},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            }
        ],
        notes="Continued increase in pain. Referred to physician for medication adjustment",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient1_assessments.append(assessment3)

    # 2.5 weeks ago
    date_2w5d_ago = today - timedelta(days=18)
    assessment4 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_2w5d_ago.replace(hour=11, minute=0),
        responses={
            "pain_level": {"value": 4},
            "pain_location": {"value": "Lower back and right hip"},
            "nausea": {"value": 5},
            "fatigue": {"value": 5},
            "appetite": {"value": 3},
        },
        symptoms={"pain": 4, "nausea": 5, "fatigue": 5, "appetite": 3},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            }
        ],
        notes="Pain improved after medication adjustment but nausea increased - likely side effect",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient1_assessments.append(assessment4)

    # 2 weeks ago
    date_2w_ago = today - timedelta(days=14)
    assessment5 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_2w_ago.replace(hour=9, minute=30),
        responses={
            "pain_level": {"value": 3},
            "pain_location": {"value": "Lower back and right hip"},
            "nausea": {"value": 3},
            "fatigue": {"value": 4},
            "appetite": {"value": 4},
        },
        symptoms={"pain": 3, "nausea": 3, "fatigue": 4, "appetite": 4},
        interventions=[
            {
                "id": "mild_pain",
                "title": "Mild Pain Management",
                "description": "Continue current pain management. Monitor for changes.",
            }
        ],
        notes="Pain and nausea both improved. Anti-nausea medication effective",
        follow_up_needed=False,
    )
    patient1_assessments.append(assessment5)

    # 1.5 weeks ago
    date_1w5d_ago = today - timedelta(days=11)
    assessment6 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_1w5d_ago.replace(hour=14, minute=0),
        responses={
            "pain_level": {"value": 5},
            "pain_location": {"value": "Lower back, right hip, and now radiating to leg"},
            "nausea": {"value": 2},
            "fatigue": {"value": 6},
            "appetite": {"value": 4},
        },
        symptoms={"pain": 5, "nausea": 2, "fatigue": 6, "appetite": 4},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            }
        ],
        notes="New pain location reported - now radiating to leg. Discussed with physician",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient1_assessments.append(assessment6)

    # 1 week ago
    date_1w_ago = today - timedelta(days=7)
    assessment7 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_1w_ago.replace(hour=10, minute=15),
        responses={
            "pain_level": {"value": 6},
            "pain_location": {"value": "Lower back, right hip, and radiating to leg"},
            "nausea": {"value": 2},
            "fatigue": {"value": 7},
            "appetite": {"value": 3},
        },
        symptoms={"pain": 6, "nausea": 2, "fatigue": 7, "appetite": 3},
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
            },
            {
                "id": "severe_fatigue",
                "title": "Severe Fatigue Management",
                "description": "Assess for reversible causes. Consider energy conservation strategies.",
            },
        ],
        notes="Increasing pain and fatigue. Scheduled for follow-up with oncologist",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH,
    )
    patient1_assessments.append(assessment7)

    # 3 days ago
    date_3d_ago = today - timedelta(days=3)
    assessment8 = Assessment(
        patient_id=patient1.id,
        protocol_id=cancer_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_3d_ago.replace(hour=11, minute=0),
        responses={
            "pain_level": {"value": 7},
            "pain_location": {"value": "Lower back, right hip, and radiating to leg"},
            "nausea": {"value": 3},
            "fatigue": {"value": 7},
            "appetite": {"value": 2},
        },
        symptoms={"pain": 7, "nausea": 3, "fatigue": 7, "appetite": 2},
        interventions=[
            {
                "id": "severe_pain",
                "title": "Severe Pain Management",
                "description": "Urgent review of pain medication. Consider opioid rotation or adjustment.",
            },
            {
                "id": "severe_fatigue",
                "title": "Severe Fatigue Management",
                "description": "Assess for reversible causes. Consider energy conservation strategies.",
            },
        ],
        notes="Pain continues to increase despite medication adjustments. Oncologist appointment scheduled for tomorrow",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH,
    )
    patient1_assessments.append(assessment8)

    # Create assessment history for patient2 (heart failure patient)
    patient2_assessments = []

    # 4 weeks ago
    assessment1 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=date_4w_ago.replace(hour=10, minute=0),
        responses={
            "dyspnea": {"value": 3},
            "edema": {"value": 4},
            "orthopnea": {"value": 2},
            "fatigue": {"value": 4},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 3,
            "edema": 4,
            "orthopnea": 2,
            "fatigue": 4,
            "chest_pain": 0,
        },
        notes="Patient stable on current medication regimen",
        follow_up_needed=False,
    )
    patient2_assessments.append(assessment1)

    # 3 weeks ago
    assessment2 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=date_3w_ago.replace(hour=14, minute=30),
        responses={
            "dyspnea": {"value": 4},
            "edema": {"value": 5},
            "orthopnea": {"value": 2},
            "fatigue": {"value": 5},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 4,
            "edema": 5,
            "orthopnea": 2,
            "fatigue": 5,
            "chest_pain": 0,
        },
        notes="Slight increase in edema and fatigue. Recommended fluid restriction",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.LOW,
    )
    patient2_assessments.append(assessment2)

    # 2 weeks ago
    assessment3 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=date_2w_ago.replace(hour=11, minute=15),
        responses={
            "dyspnea": {"value": 4},
            "edema": {"value": 6},
            "orthopnea": {"value": 3},
            "fatigue": {"value": 5},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 4,
            "edema": 6,
            "orthopnea": 3,
            "fatigue": 5,
            "chest_pain": 0,
        },
        notes="Edema increasing despite fluid restriction. Recommended diuretic adjustment",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient2_assessments.append(assessment3)

    # 1 week ago
    assessment4 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=date_1w_ago.replace(hour=9, minute=45),
        responses={
            "dyspnea": {"value": 5},
            "edema": {"value": 7},
            "orthopnea": {"value": 4},
            "fatigue": {"value": 6},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 5,
            "edema": 7,
            "orthopnea": 4,
            "fatigue": 6,
            "chest_pain": 0,
        },
        interventions=[
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.",
            }
        ],
        notes="Significant increase in edema and now requiring more pillows to sleep. Diuretic dose increased",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH,
    )
    patient2_assessments.append(assessment4)

    # 4 days ago
    date_4d_ago = today - timedelta(days=4)
    assessment5 = Assessment(
        patient_id=patient2.id,
        protocol_id=heart_failure_protocol.id,
        conducted_by_id=nurse2.id,
        assessment_date=date_4d_ago.replace(hour=10, minute=30),
        responses={
            "dyspnea": {"value": 4},
            "edema": {"value": 5},
            "orthopnea": {"value": 3},
            "fatigue": {"value": 5},
            "chest_pain": {"value": False},
        },
        symptoms={
            "dyspnea": 4,
            "edema": 5,
            "orthopnea": 3,
            "fatigue": 5,
            "chest_pain": 0,
        },
        notes="Improvement in symptoms with increased diuretic dose",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient2_assessments.append(assessment5)

    # Create assessment history for patient3 (COPD patient)
    patient3_assessments = []

    # 3 weeks ago
    assessment1 = Assessment(
        patient_id=patient3.id,
        protocol_id=copd_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_3w_ago.replace(hour=11, minute=30),
        responses={
            "dyspnea": {"value": 5},
            "cough": {"value": 4},
            "sputum_color": {"value": "White"},
            "oxygen_use": {"value": 16},
            "anxiety": {"value": 4},
        },
        symptoms={
            "dyspnea": 5,
            "cough": 4,
            "sputum": 2,
            "oxygen_use": 16,
            "anxiety": 4,
        },
        notes="Stable respiratory status. Using oxygen as prescribed",
        follow_up_needed=False,
    )
    patient3_assessments.append(assessment1)

    # 2 weeks ago
    assessment2 = Assessment(
        patient_id=patient3.id,
        protocol_id=copd_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_2w_ago.replace(hour=14, minute=15),
        responses={
            "dyspnea": {"value": 6},
            "cough": {"value": 5},
            "sputum_color": {"value": "Yellow"},
            "oxygen_use": {"value": 18},
            "anxiety": {"value": 5},
        },
        symptoms={
            "dyspnea": 6,
            "cough": 5,
            "sputum": 3,
            "oxygen_use": 18,
            "anxiety": 5,
        },
        notes="Increasing shortness of breath and cough. Sputum now yellow",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient3_assessments.append(assessment2)

    # 1 week ago
    assessment3 = Assessment(
        patient_id=patient3.id,
        protocol_id=copd_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_1w_ago.replace(hour=10, minute=0),
        responses={
            "dyspnea": {"value": 7},
            "cough": {"value": 6},
            "sputum_color": {"value": "Green"},
            "oxygen_use": {"value": 21},
            "anxiety": {"value": 7},
        },
        symptoms={
            "dyspnea": 7,
            "cough": 6,
            "sputum": 4,
            "oxygen_use": 21,
            "anxiety": 7,
        },
        interventions=[
            {
                "id": "severe_dyspnea_copd",
                "title": "Severe Dyspnea Management for COPD",
                "description": "Review bronchodilator use. Consider rescue pack if available.",
            },
            {
                "id": "infection_evaluation",
                "title": "Respiratory Infection Evaluation",
                "description": "Evaluate for respiratory infection. Consider antibiotics per protocol.",
            },
            {
                "id": "severe_anxiety",
                "title": "Respiratory Anxiety Management",
                "description": "Review breathing techniques. Consider anxiolytic if severe.",
            },
        ],
        notes="Likely respiratory infection. Started on antibiotics and increased bronchodilator use",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH,
    )
    patient3_assessments.append(assessment3)

    # 3 days ago
    assessment4 = Assessment(
        patient_id=patient3.id,
        protocol_id=copd_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_3d_ago.replace(hour=11, minute=45),
        responses={
            "dyspnea": {"value": 5},
            "cough": {"value": 5},
            "sputum_color": {"value": "Yellow"},
            "oxygen_use": {"value": 18},
            "anxiety": {"value": 5},
        },
        symptoms={
            "dyspnea": 5,
            "cough": 5,
            "sputum": 3,
            "oxygen_use": 18,
            "anxiety": 5,
        },
        notes="Improving with antibiotics. Breathing easier and sputum changing from green to yellow",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM,
    )
    patient3_assessments.append(assessment4)

    # Create assessment history for patient4 (FIT patient - Pete Jarvis)
    patient4_assessments = []

    # 2 weeks ago - excellent performance
    date_2w_ago = today - timedelta(days=14)
    assessment1 = Assessment(
        patient_id=patient4.id,
        protocol_id=fit_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_2w_ago.replace(hour=10, minute=0),
        responses={
            "mile_time": {"value": 6.5},
            "plank_time": {"value": 7},
            "row_5k_time": {"value": 22},
            "pushups_per_minute": {"value": 75},
            "swim_mile_time": {"value": 28},
        },
        symptoms={"fitness": 6.5, "strength": 7, "endurance": 22},
        interventions=[
            {
                "id": "maintain_fitness",
                "title": "Maintain Excellent Fitness",
                "description": "Continue current fitness routine. Excellent cardiovascular health.",
            },
            {
                "id": "maintain_strength",
                "title": "Maintain Strength Training",
                "description": "Continue strength training program. Excellent muscular endurance.",
            },
            {
                "id": "maintain_endurance",
                "title": "Maintain Endurance Training",
                "description": "Continue endurance training. Excellent cardiovascular capacity.",
            },
        ],
        notes="All fitness metrics at excellent levels. Continue current training regimen",
        follow_up_needed=False,
    )
    patient4_assessments.append(assessment1)

    # 1 week ago - continued excellence
    date_1w_ago = today - timedelta(days=7)
    assessment2 = Assessment(
        patient_id=patient4.id,
        protocol_id=fit_protocol.id,
        conducted_by_id=nurse1.id,
        assessment_date=date_1w_ago.replace(hour=9, minute=30),
        responses={
            "mile_time": {"value": 6.2},
            "plank_time": {"value": 6.8},
            "row_5k_time": {"value": 21.5},
            "pushups_per_minute": {"value": 78},
            "swim_mile_time": {"value": 27},
        },
        symptoms={"fitness": 6.2, "strength": 6.8, "endurance": 21.5},
        interventions=[
            {
                "id": "maintain_fitness",
                "title": "Maintain Excellent Fitness",
                "description": "Continue current fitness routine. Excellent cardiovascular health.",
            },
            {
                "id": "maintain_strength",
                "title": "Maintain Strength Training",
                "description": "Continue strength training program. Excellent muscular endurance.",
            },
            {
                "id": "maintain_endurance",
                "title": "Maintain Endurance Training",
                "description": "Continue endurance training. Excellent cardiovascular capacity.",
            },
        ],
        notes="Slight improvement in all metrics. Fitness level remains exceptional",
        follow_up_needed=False,
    )
    patient4_assessments.append(assessment2)

    # Add all assessments to the database
    db.session.add_all(patient1_assessments)
    db.session.add_all(patient2_assessments)
    db.session.add_all(patient3_assessments)
    db.session.add_all(patient4_assessments)
    db.session.commit()

    total_assessments = (
        len(patient1_assessments) + len(patient2_assessments) + len(patient3_assessments) + len(patient4_assessments)
    )
    logger.info(f"✅ Patient assessment history added successfully ({total_assessments} total assessments created)")
