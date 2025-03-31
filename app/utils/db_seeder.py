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

def seed_database():
    """Seed the database with initial data"""
    # Clear existing data in the correct order to handle foreign key constraints
    db.session.query(Assessment).delete()
    db.session.query(Call).delete()
    db.session.query(Medication).delete()
    db.session.query(Patient).delete()
    db.session.query(Protocol).delete()
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
    
    # Create protocols
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
    
    db.session.add_all([cancer_protocol, heart_failure_protocol, copd_protocol])
    db.session.commit()
    
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
    
    print("Database seeded successfully!")
