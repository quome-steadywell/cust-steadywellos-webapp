"""Database seeding utility for development and testing"""

from datetime import datetime, timedelta, date
from app import db
from app.models.user import User, UserRole
from app.models.patient import Patient, Gender, ProtocolType
from app.models.protocol import Protocol
from app.models.call import Call, CallStatus
from app.models.assessment import Assessment, FollowUpPriority
from app.models.medication import Medication, MedicationRoute, MedicationFrequency
from app.models.audit_log import AuditLog

def seed_database(test_scenario=None):
    """
    Seed the database with initial data
    
    Args:
        test_scenario (str, optional): Specific test scenario to generate data for
            Valid values: None, 'date_check'
    """
    # Clear existing data in the correct order to handle foreign key constraints
    db.session.query(Assessment).delete()
    db.session.query(Call).delete()
    db.session.query(Medication).delete()
    db.session.query(Patient).delete()
    
    # We don't delete protocols anymore - they should be created before this runs
    # db.session.query(Protocol).delete()
    
    # Delete audit logs before users to avoid foreign key constraint issues
    db.session.query(AuditLog).delete()
    db.session.query(User).delete()
    db.session.commit()
    
    # Create users
    admin = User(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        phone_number="555-123-4567",
        is_active=True
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
        is_active=True
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
        is_active=True
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
        is_active=True
    )
    physician.password = "password123"
    
    db.session.add_all([admin, nurse1, nurse2, physician])
    db.session.commit()
    
    # Get or create protocols
    cancer_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.CANCER).first()
    heart_failure_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.HEART_FAILURE).first()
    copd_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.COPD).first()
    
    # Forces creation of default protocols since we're skipping the protocol_ingest step
    print("Creating default protocols in the database...")
    # Create protocols
    if not cancer_protocol:
        cancer_protocol = Protocol(
                name="Cancer Palliative Care Protocol",
                description="Protocol for managing symptoms in patients with advanced cancer",
                protocol_type=ProtocolType.CANCER,
                version="1.0",
            questions=[
                {
                    "id": "pain_level",
                    "text": "On a scale of 0 to 10, how would you rate your pain?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "pain",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "pain_location",
                    "text": "Where is your pain located?",
                    "type": "text",
                    "required": True,
                    "symptom_type": "pain"
                },
                {
                    "id": "nausea",
                    "text": "On a scale of 0 to 10, how would you rate your nausea?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "nausea",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "fatigue",
                    "text": "On a scale of 0 to 10, how would you rate your fatigue?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "fatigue",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "appetite",
                    "text": "On a scale of 0 to 10, how would you rate your appetite?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "appetite",
                    "min_value": 0,
                    "max_value": 10
                }
            ],
            decision_tree=[
                {
                    "id": "pain_assessment",
                    "symptom_type": "pain",
                    "condition": ">=7",
                    "intervention_ids": ["severe_pain"]
                },
                {
                    "id": "pain_moderate",
                    "symptom_type": "pain",
                    "condition": ">=4",
                    "intervention_ids": ["moderate_pain"]
                },
                {
                    "id": "pain_mild",
                    "symptom_type": "pain",
                    "condition": "<4",
                    "intervention_ids": ["mild_pain"]
                },
                {
                    "id": "nausea_severe",
                    "symptom_type": "nausea",
                    "condition": ">=7",
                    "intervention_ids": ["severe_nausea"]
                },
                {
                    "id": "fatigue_severe",
                    "symptom_type": "fatigue",
                    "condition": ">=7",
                    "intervention_ids": ["severe_fatigue"]
                }
            ],
            interventions=[
                {
                    "id": "severe_pain",
                    "title": "Severe Pain Management",
                    "description": "Urgent review of pain medication. Consider opioid rotation or adjustment.",
                    "symptom_type": "pain",
                    "severity_threshold": 7
                },
                {
                    "id": "moderate_pain",
                    "title": "Moderate Pain Management",
                    "description": "Review current analgesics. Consider scheduled dosing instead of as-needed.",
                    "symptom_type": "pain",
                    "severity_threshold": 4
                },
                {
                    "id": "mild_pain",
                    "title": "Mild Pain Management",
                    "description": "Continue current pain management. Monitor for changes.",
                    "symptom_type": "pain",
                    "severity_threshold": 0
                },
                {
                    "id": "severe_nausea",
                    "title": "Severe Nausea Management",
                    "description": "Review antiemetic regimen. Consider adding a different class of antiemetic.",
                    "symptom_type": "nausea",
                    "severity_threshold": 7
                },
                {
                    "id": "severe_fatigue",
                    "title": "Severe Fatigue Management",
                    "description": "Assess for reversible causes. Consider energy conservation strategies.",
                    "symptom_type": "fatigue",
                    "severity_threshold": 7
                }
            ],
            is_active=True
        )
        
        if not heart_failure_protocol:
            heart_failure_protocol = Protocol(
                name="Heart Failure Palliative Care Protocol",
                description="Protocol for managing symptoms in patients with advanced heart failure",
                protocol_type=ProtocolType.HEART_FAILURE,
                version="1.0",
            questions=[
                {
                    "id": "dyspnea",
                    "text": "On a scale of 0 to 10, how would you rate your shortness of breath?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "dyspnea",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "edema",
                    "text": "On a scale of 0 to 10, how would you rate the swelling in your legs or ankles?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "edema",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "orthopnea",
                    "text": "How many pillows do you need to sleep comfortably without shortness of breath?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "orthopnea",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "fatigue",
                    "text": "On a scale of 0 to 10, how would you rate your fatigue?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "fatigue",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "chest_pain",
                    "text": "Have you experienced any chest pain?",
                    "type": "boolean",
                    "required": True,
                    "symptom_type": "chest_pain"
                }
            ],
            decision_tree=[
                {
                    "id": "dyspnea_severe",
                    "symptom_type": "dyspnea",
                    "condition": ">=7",
                    "intervention_ids": ["severe_dyspnea"]
                },
                {
                    "id": "edema_severe",
                    "symptom_type": "edema",
                    "condition": ">=7",
                    "intervention_ids": ["severe_edema"]
                },
                {
                    "id": "chest_pain_present",
                    "symptom_type": "chest_pain",
                    "condition": "==true",
                    "intervention_ids": ["chest_pain_management"]
                }
            ],
            interventions=[
                {
                    "id": "severe_dyspnea",
                    "title": "Severe Dyspnea Management",
                    "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen.",
                    "symptom_type": "dyspnea",
                    "severity_threshold": 7
                },
                {
                    "id": "severe_edema",
                    "title": "Severe Edema Management",
                    "description": "Review diuretic regimen. Consider temporary increase in diuretic dose.",
                    "symptom_type": "edema",
                    "severity_threshold": 7
                },
                {
                    "id": "chest_pain_management",
                    "title": "Chest Pain Management",
                    "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed.",
                    "symptom_type": "chest_pain"
                }
            ],
            is_active=True
        )
        
        if not copd_protocol:
            copd_protocol = Protocol(
                name="COPD Palliative Care Protocol",
                description="Protocol for managing symptoms in patients with advanced COPD",
                protocol_type=ProtocolType.COPD,
                version="1.0",
            questions=[
                {
                    "id": "dyspnea",
                    "text": "On a scale of 0 to 10, how would you rate your shortness of breath?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "dyspnea",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "cough",
                    "text": "On a scale of 0 to 10, how would you rate your cough?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "cough",
                    "min_value": 0,
                    "max_value": 10
                },
                {
                    "id": "sputum_color",
                    "text": "What color is your sputum/phlegm?",
                    "type": "choice",
                    "required": True,
                    "symptom_type": "sputum",
                    "choices": ["Clear", "White", "Yellow", "Green"]
                },
                {
                    "id": "oxygen_use",
                    "text": "How many hours per day are you using oxygen?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "oxygen_use",
                    "min_value": 0,
                    "max_value": 24
                },
                {
                    "id": "anxiety",
                    "text": "On a scale of 0 to 10, how would you rate your anxiety related to breathing?",
                    "type": "numeric",
                    "required": True,
                    "symptom_type": "anxiety",
                    "min_value": 0,
                    "max_value": 10
                }
            ],
            decision_tree=[
                {
                    "id": "dyspnea_severe",
                    "symptom_type": "dyspnea",
                    "condition": ">=7",
                    "intervention_ids": ["severe_dyspnea_copd"]
                },
                {
                    "id": "sputum_green",
                    "symptom_type": "sputum",
                    "condition": "==Green",
                    "intervention_ids": ["infection_evaluation"]
                },
                {
                    "id": "anxiety_severe",
                    "symptom_type": "anxiety",
                    "condition": ">=7",
                    "intervention_ids": ["severe_anxiety"]
                }
            ],
            interventions=[
                {
                    "id": "severe_dyspnea_copd",
                    "title": "Severe Dyspnea Management for COPD",
                    "description": "Review bronchodilator use. Consider rescue pack if available.",
                    "symptom_type": "dyspnea",
                    "severity_threshold": 7
                },
                {
                    "id": "infection_evaluation",
                    "title": "Respiratory Infection Evaluation",
                    "description": "Evaluate for respiratory infection. Consider antibiotics per protocol.",
                    "symptom_type": "sputum"
                },
                {
                    "id": "severe_anxiety",
                    "title": "Respiratory Anxiety Management",
                    "description": "Review breathing techniques. Consider anxiolytic if severe.",
                    "symptom_type": "anxiety",
                    "severity_threshold": 7
                }
            ],
            is_active=True
        )
        
    # Add any newly created protocols
    protocols_to_add = []
    if cancer_protocol and not cancer_protocol.id:
        protocols_to_add.append(cancer_protocol)
    if heart_failure_protocol and not heart_failure_protocol.id:
        protocols_to_add.append(heart_failure_protocol)
    if copd_protocol and not copd_protocol.id:
        protocols_to_add.append(copd_protocol)
        
    if protocols_to_add:
        db.session.add_all(protocols_to_add)
        db.session.commit()
        print(f"Added {len(protocols_to_add)} new protocols to the database.")
    
    # Create patients
    patient1 = Patient(
        mrn="MRN12345",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1950, 5, 15),
        gender=Gender.MALE,
        phone_number="555-111-2222",
        email="john.doe@example.com",
        address="123 Main St, Anytown, USA",
        primary_diagnosis="Stage IV Lung Cancer",
        secondary_diagnoses="COPD, Hypertension",
        protocol_type=ProtocolType.CANCER,
        primary_nurse_id=nurse1.id,
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="555-222-3333",
        emergency_contact_relationship="Spouse",
        advance_directive=True,
        dnr_status=True,
        allergies="Penicillin",
        notes="Patient prefers morning calls",
        is_active=True
    )
    
    patient2 = Patient(
        mrn="MRN67890",
        first_name="Mary",
        last_name="Johnson",
        date_of_birth=date(1945, 9, 20),
        gender=Gender.FEMALE,
        phone_number="555-333-4444",
        email="mary.johnson@example.com",
        address="456 Oak Ave, Somewhere, USA",
        primary_diagnosis="Heart Failure NYHA Class IV",
        secondary_diagnoses="Diabetes, Chronic Kidney Disease",
        protocol_type=ProtocolType.HEART_FAILURE,
        primary_nurse_id=nurse2.id,
        emergency_contact_name="Robert Johnson",
        emergency_contact_phone="555-444-5555",
        emergency_contact_relationship="Son",
        advance_directive=True,
        dnr_status=True,
        allergies="Sulfa drugs",
        notes="Hard of hearing, speak clearly and loudly",
        is_active=True
    )
    
    patient3 = Patient(
        mrn="MRN24680",
        first_name="James",
        last_name="Wilson",
        date_of_birth=date(1953, 3, 10),
        gender=Gender.MALE,
        phone_number="555-555-6666",
        email="james.wilson@example.com",
        address="789 Pine St, Elsewhere, USA",
        primary_diagnosis="End-stage COPD, GOLD Stage IV",
        secondary_diagnoses="Cor Pulmonale, Osteoporosis",
        protocol_type=ProtocolType.COPD,
        primary_nurse_id=nurse1.id,
        emergency_contact_name="Sarah Wilson",
        emergency_contact_phone="555-666-7777",
        emergency_contact_relationship="Daughter",
        advance_directive=True,
        dnr_status=True,
        allergies="None known",
        notes="Uses oxygen 24/7, 2L via nasal cannula",
        is_active=True
    )
    
    db.session.add_all([patient1, patient2, patient3])
    db.session.commit()
    
    # Create medications
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
        is_active=True
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
        is_active=True
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
        is_active=True
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
        is_active=True
    )
    
    db.session.add_all([med1, med2, med3, med4])
    db.session.commit()
    
    # Create calls
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    call1 = Call(
        patient_id=patient1.id,
        conducted_by_id=nurse1.id,
        scheduled_time=yesterday.replace(hour=10, minute=0, second=0, microsecond=0),
        start_time=yesterday.replace(hour=10, minute=5, second=0, microsecond=0),
        end_time=yesterday.replace(hour=10, minute=20, second=0, microsecond=0),
        duration=15*60,  # 15 minutes in seconds
        status=CallStatus.COMPLETED,
        call_type="assessment",
        notes="Patient reported increased pain levels",
        twilio_call_sid="CA123456789",
        recording_url="https://example.com/recordings/call1.mp3",
        transcript="Nurse: How are you feeling today? Patient: My pain has been worse, about a 7 out of 10."
    )
    
    call2 = Call(
        patient_id=patient2.id,
        conducted_by_id=nurse2.id,
        scheduled_time=yesterday.replace(hour=14, minute=0, second=0, microsecond=0),
        start_time=yesterday.replace(hour=14, minute=2, second=0, microsecond=0),
        end_time=yesterday.replace(hour=14, minute=18, second=0, microsecond=0),
        duration=16*60,  # 16 minutes in seconds
        status=CallStatus.COMPLETED,
        call_type="assessment",
        notes="Patient reports increased edema in ankles",
        twilio_call_sid="CA987654321",
        recording_url="https://example.com/recordings/call2.mp3",
        transcript="Nurse: How is your breathing today? Patient: A bit harder than usual, and my ankles are more swollen."
    )
    
    call3 = Call(
        patient_id=patient3.id,
        conducted_by_id=nurse1.id,
        scheduled_time=today.replace(hour=11, minute=0, second=0, microsecond=0),
        status=CallStatus.SCHEDULED,
        call_type="assessment"
    )
    
    call4 = Call(
        patient_id=patient1.id,
        conducted_by_id=nurse1.id,
        scheduled_time=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        status=CallStatus.SCHEDULED,
        call_type="follow_up"
    )
    
    db.session.add_all([call1, call2, call3, call4])
    db.session.commit()
    
    # Create assessments
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
            "appetite": {"value": 4}
        },
        symptoms={
            "pain": 7,
            "nausea": 3,
            "fatigue": 6,
            "appetite": 4
        },
        interventions=[
            {
                "id": "severe_pain",
                "title": "Severe Pain Management",
                "description": "Urgent review of pain medication. Consider opioid rotation or adjustment."
            }
        ],
        notes="Patient reports pain medication not lasting full duration between doses",
        follow_up_needed=True,
        follow_up_date=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Recommend increasing morphine dosage or frequency. Consider adding breakthrough pain medication."
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 5,
            "edema": 7,
            "orthopnea": 3,
            "fatigue": 6,
            "chest_pain": 0
        },
        interventions=[
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."
            }
        ],
        notes="Patient has been compliant with fluid restriction but still has increased edema",
        follow_up_needed=True,
        follow_up_date=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
        follow_up_priority=FollowUpPriority.MEDIUM,
        ai_guidance="Consider temporary increase in furosemide dose. Monitor weight daily and fluid intake."
    )
    
    db.session.add_all([assessment1, assessment2])
    db.session.commit()
    
    # Add date-specific test data if requested
    if test_scenario == 'date_check':
        seed_date_check_data()
    
    # Add recent assessment history for patient details view
    seed_patient_history(patient1, patient2, patient3, cancer_protocol, heart_failure_protocol, copd_protocol, nurse1, nurse2)
        
    print("Database seeded successfully!")
    
def seed_date_check_data():
    """Add test data specifically for date handling test cases"""
    # Get reference to main entities
    patient = Patient.query.filter_by(first_name="Mary").first()
    nurse = User.query.filter_by(first_name="Robert").first()
    # Ensure we get the heart_failure_protocol from the database
    protocol = Protocol.query.filter_by(protocol_type=ProtocolType.HEART_FAILURE).first()
    
    if not protocol:
        print("Error: Heart Failure protocol not found in database. Date test data will not be added.")
        return
    
    # Get date references
    today = datetime.now()
    
    # Create assessments spanning multiple weeks
    # These dates are carefully selected to test various week boundaries
    
    # 1. Last week (Sunday)
    last_week_sunday = today - timedelta(days=today.weekday() + 8)  # Go back to previous week's Sunday
    assessment1 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=last_week_sunday.replace(hour=9, minute=30),
        responses={"edema": {"value": 6}},
        symptoms={"edema": 6},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM
    )
    
    # 2. Last week (Wednesday)
    last_week_wednesday = today - timedelta(days=today.weekday() + 4) 
    assessment2 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=last_week_wednesday.replace(hour=14, minute=15),
        responses={"dyspnea": {"value": 5}},
        symptoms={"dyspnea": 5},
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.LOW
    )
    
    # 3. This week (Sunday)
    this_week_sunday = today - timedelta(days=today.weekday() + 1)
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
        follow_up_priority=FollowUpPriority.MEDIUM
    )
    
    # 4. This week (Monday)
    this_week_monday = today - timedelta(days=today.weekday())
    if this_week_monday.date() > today.date():  # Ensure we're not in the future
        this_week_monday = this_week_monday - timedelta(days=7)
    assessment4 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=this_week_monday.replace(hour=11, minute=30),
        responses={"fatigue": {"value": 6}},
        symptoms={"fatigue": 6},
        follow_up_needed=False
    )
    
    # 5. This week (Current day)
    assessment5 = Assessment(
        patient_id=patient.id,
        protocol_id=protocol.id,
        conducted_by_id=nurse.id,
        assessment_date=today.replace(hour=9, minute=0),
        responses={"orthopnea": {"value": 4}},
        symptoms={"orthopnea": 4},
        follow_up_needed=False
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
        follow_up_date=next_week_monday + timedelta(days=1)
    )
    
    # Add all assessments
    db.session.add_all([assessment1, assessment2, assessment3, assessment4, assessment5, assessment6])
    db.session.commit()
    
    print("Date check test data added successfully")

def seed_patient_history(patient1, patient2, patient3, cancer_protocol, heart_failure_protocol, copd_protocol, nurse1, nurse2):
    """Add assessment history for patients to populate patient details pages"""
    
    print("Adding patient assessment history...")
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
            "chest_pain": {"value": True}
        },
        symptoms={
            "dyspnea": 8,
            "edema": 9,
            "orthopnea": 5, 
            "fatigue": 7,
            "chest_pain": 1
        },
        interventions=[
            {
                "id": "severe_dyspnea",
                "title": "Severe Dyspnea Management",
                "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen."
            },
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."
            },
            {
                "id": "chest_pain_management",
                "title": "Chest Pain Management",
                "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed."
            }
        ],
        notes="Patient reports severe increase in edema, dyspnea, and new onset chest pain. Needs immediate medical attention.",
        follow_up_needed=True,
        follow_up_date=datetime(2025, 4, 2, 10, 0),  # April 2, 2025 10:00 AM
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely."
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
            "chest_pain": {"value": True}
        },
        symptoms={
            "dyspnea": 9,
            "edema": 10,
            "orthopnea": 6, 
            "fatigue": 8,
            "chest_pain": 1
        },
        interventions=[
            {
                "id": "severe_dyspnea",
                "title": "Severe Dyspnea Management",
                "description": "Urgent evaluation needed. Review diuretic regimen and consider supplemental oxygen."
            },
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."
            },
            {
                "id": "chest_pain_management",
                "title": "Chest Pain Management",
                "description": "Evaluate for cardiac causes. Consider nitroglycerin if prescribed."
            }
        ],
        notes="Follow-up check shows worsening symptoms. Patient sent to emergency department for evaluation.",
        follow_up_needed=True,
        follow_up_date=datetime(2025, 3, 28, 10, 0),  # March 28, 2025 10:00 AM
        follow_up_priority=FollowUpPriority.HIGH,
        ai_guidance="Urgent hospital evaluation recommended. Possible acute decompensated heart failure with cardiac ischemia."
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
            "appetite": {"value": 6}
        },
        symptoms={
            "pain": 4,
            "nausea": 2,
            "fatigue": 5,
            "appetite": 6
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
            }
        ],
        notes="Patient reports stable pain with current medication regimen",
        follow_up_needed=False
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
            "appetite": {"value": 5}
        },
        symptoms={
            "pain": 5,
            "nausea": 3,
            "fatigue": 6,
            "appetite": 5
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
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
            "appetite": {"value": 4}
        },
        symptoms={
            "pain": 6,
            "nausea": 4,
            "fatigue": 6,
            "appetite": 4
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
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
            "appetite": {"value": 3}
        },
        symptoms={
            "pain": 4,
            "nausea": 5,
            "fatigue": 5,
            "appetite": 3
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
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
            "appetite": {"value": 4}
        },
        symptoms={
            "pain": 3,
            "nausea": 3,
            "fatigue": 4,
            "appetite": 4
        },
        interventions=[
            {
                "id": "mild_pain",
                "title": "Mild Pain Management",
                "description": "Continue current pain management. Monitor for changes."
            }
        ],
        notes="Pain and nausea both improved. Anti-nausea medication effective",
        follow_up_needed=False
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
            "appetite": {"value": 4}
        },
        symptoms={
            "pain": 5,
            "nausea": 2,
            "fatigue": 6,
            "appetite": 4
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
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
            "appetite": {"value": 3}
        },
        symptoms={
            "pain": 6,
            "nausea": 2,
            "fatigue": 7,
            "appetite": 3
        },
        interventions=[
            {
                "id": "moderate_pain",
                "title": "Moderate Pain Management",
                "description": "Review current analgesics. Consider scheduled dosing instead of as-needed."
            },
            {
                "id": "severe_fatigue",
                "title": "Severe Fatigue Management",
                "description": "Assess for reversible causes. Consider energy conservation strategies."
            }
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
            "appetite": {"value": 2}
        },
        symptoms={
            "pain": 7,
            "nausea": 3,
            "fatigue": 7,
            "appetite": 2
        },
        interventions=[
            {
                "id": "severe_pain",
                "title": "Severe Pain Management",
                "description": "Urgent review of pain medication. Consider opioid rotation or adjustment."
            },
            {
                "id": "severe_fatigue",
                "title": "Severe Fatigue Management",
                "description": "Assess for reversible causes. Consider energy conservation strategies."
            }
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 3,
            "edema": 4,
            "orthopnea": 2,
            "fatigue": 4,
            "chest_pain": 0
        },
        notes="Patient stable on current medication regimen",
        follow_up_needed=False
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 4,
            "edema": 5,
            "orthopnea": 2,
            "fatigue": 5,
            "chest_pain": 0
        },
        notes="Slight increase in edema and fatigue. Recommended fluid restriction",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.LOW
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 4,
            "edema": 6,
            "orthopnea": 3,
            "fatigue": 5,
            "chest_pain": 0
        },
        notes="Edema increasing despite fluid restriction. Recommended diuretic adjustment",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 5,
            "edema": 7,
            "orthopnea": 4,
            "fatigue": 6,
            "chest_pain": 0
        },
        interventions=[
            {
                "id": "severe_edema",
                "title": "Severe Edema Management",
                "description": "Review diuretic regimen. Consider temporary increase in diuretic dose."
            }
        ],
        notes="Significant increase in edema and now requiring more pillows to sleep. Diuretic dose increased",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH
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
            "chest_pain": {"value": False}
        },
        symptoms={
            "dyspnea": 4,
            "edema": 5,
            "orthopnea": 3,
            "fatigue": 5,
            "chest_pain": 0
        },
        notes="Improvement in symptoms with increased diuretic dose",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM
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
            "anxiety": {"value": 4}
        },
        symptoms={
            "dyspnea": 5,
            "cough": 4,
            "sputum": 2,
            "oxygen_use": 16,
            "anxiety": 4
        },
        notes="Stable respiratory status. Using oxygen as prescribed",
        follow_up_needed=False
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
            "anxiety": {"value": 5}
        },
        symptoms={
            "dyspnea": 6,
            "cough": 5,
            "sputum": 3,
            "oxygen_use": 18,
            "anxiety": 5
        },
        notes="Increasing shortness of breath and cough. Sputum now yellow",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM
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
            "anxiety": {"value": 7}
        },
        symptoms={
            "dyspnea": 7,
            "cough": 6,
            "sputum": 4,
            "oxygen_use": 21,
            "anxiety": 7
        },
        interventions=[
            {
                "id": "severe_dyspnea_copd",
                "title": "Severe Dyspnea Management for COPD",
                "description": "Review bronchodilator use. Consider rescue pack if available."
            },
            {
                "id": "infection_evaluation",
                "title": "Respiratory Infection Evaluation",
                "description": "Evaluate for respiratory infection. Consider antibiotics per protocol."
            },
            {
                "id": "severe_anxiety",
                "title": "Respiratory Anxiety Management",
                "description": "Review breathing techniques. Consider anxiolytic if severe."
            }
        ],
        notes="Likely respiratory infection. Started on antibiotics and increased bronchodilator use",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.HIGH
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
            "anxiety": {"value": 5}
        },
        symptoms={
            "dyspnea": 5,
            "cough": 5,
            "sputum": 3,
            "oxygen_use": 18,
            "anxiety": 5
        },
        notes="Improving with antibiotics. Breathing easier and sputum changing from green to yellow",
        follow_up_needed=True,
        follow_up_priority=FollowUpPriority.MEDIUM
    )
    patient3_assessments.append(assessment4)
    
    # Add all assessments to the database
    db.session.add_all(patient1_assessments)
    db.session.add_all(patient2_assessments)
    db.session.add_all(patient3_assessments)
    db.session.commit()
    
    print("Patient assessment history added successfully")
