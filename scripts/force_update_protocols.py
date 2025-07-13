#!/usr/bin/env python3
"""
Force update protocols with comprehensive 15-question assessments.
Direct database approach to ensure JSON fields are updated.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import ProtocolType
from src.utils.logger import get_logger

logger = get_logger()


def get_comprehensive_cancer_protocol():
    """Get comprehensive cancer protocol data."""
    questions = [
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
    ]
    
    interventions = [
        {"id": 1, "title": "Emergency Response", "description": "Call 911 or seek immediate emergency care", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe symptoms requiring immediate medical attention"},
        {"id": 2, "title": "Pain Management", "description": "Adjust pain medications per protocol", "priority": "high", "symptom_type": "pain", "instructions": "Follow WHO analgesic ladder"},
        {"id": 3, "title": "Nausea Management", "description": "Anti-emetic protocol", "priority": "high", "symptom_type": "nausea", "instructions": "Administer prescribed anti-emetics"},
        {"id": 4, "title": "Physician Contact", "description": "Contact oncologist within 2-4 hours", "priority": "high", "symptom_type": "urgent_symptoms", "instructions": "Report concerning symptoms to physician"},
        {"id": 5, "title": "Home Care Instructions", "description": "Continue current care plan with monitoring", "priority": "medium", "symptom_type": "stable", "instructions": "Follow home care guidelines"},
        {"id": 6, "title": "Comfort Measures", "description": "Provide comfort and supportive care", "priority": "medium", "symptom_type": "comfort", "instructions": "Non-pharmacological comfort measures"}
    ]
    
    decision_tree = [
        {"id": 1, "symptom_type": "pain", "condition": "greater_than", "value": 7, "next_node_id": 2, "intervention_ids": [1, 2]},
        {"id": 2, "symptom_type": "nausea", "condition": "equals", "value": True, "next_node_id": 3, "intervention_ids": [3]},
        {"id": 3, "symptom_type": "dyspnea", "condition": "equals", "value": True, "next_node_id": 4, "intervention_ids": [1, 4]},
        {"id": 4, "symptom_type": "fever", "condition": "equals", "value": True, "next_node_id": 5, "intervention_ids": [4]},
        {"id": 5, "symptom_type": "confusion", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
        {"id": 6, "symptom_type": "concern_level", "condition": "greater_than", "value": 7, "next_node_id": None, "intervention_ids": [4]},
        {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [5, 6]}
    ]
    
    return questions, interventions, decision_tree


def get_comprehensive_heart_failure_protocol():
    """Get comprehensive heart failure protocol data."""
    questions = [
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
    ]
    
    interventions = [
        {"id": 1, "title": "Emergency Response", "description": "Call 911 for severe breathing difficulty", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe dyspnea, chest pain, or acute symptoms"},
        {"id": 2, "title": "Diuretic Adjustment", "description": "Contact physician for medication adjustment", "priority": "high", "symptom_type": "fluid_overload", "instructions": "Signs of fluid retention requiring medical evaluation"},
        {"id": 3, "title": "Activity Modification", "description": "Reduce activity and rest", "priority": "medium", "symptom_type": "activity_intolerance", "instructions": "Balance activity with rest periods"},
        {"id": 4, "title": "Dietary Counseling", "description": "Review low-sodium diet adherence", "priority": "medium", "symptom_type": "diet", "instructions": "Reinforce dietary restrictions"},
        {"id": 5, "title": "Weight Monitoring", "description": "Daily weight monitoring with reporting thresholds", "priority": "medium", "symptom_type": "weight_management", "instructions": "Report weight gain >2-3 lbs in 24 hours"},
        {"id": 6, "title": "Medication Review", "description": "Review and adjust medication regimen", "priority": "high", "symptom_type": "medication", "instructions": "Ensure proper medication compliance"}
    ]
    
    decision_tree = [
        {"id": 1, "symptom_type": "dyspnea_rest", "condition": "equals", "value": True, "next_node_id": 2, "intervention_ids": [1]},
        {"id": 2, "symptom_type": "weight_gain", "condition": "in", "value": ["3-5 lbs more", "More than 5 lbs"], "next_node_id": 3, "intervention_ids": [2]},
        {"id": 3, "symptom_type": "chest_pain", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
        {"id": 4, "symptom_type": "edema", "condition": "equals", "value": True, "next_node_id": 5, "intervention_ids": [2, 5]},
        {"id": 5, "symptom_type": "medication_compliance", "condition": "not_equals", "value": "Yes, all medications", "next_node_id": None, "intervention_ids": [6]},
        {"id": 6, "symptom_type": "exercise_tolerance", "condition": "in", "value": ["Less than 1 block", "Few steps only"], "next_node_id": None, "intervention_ids": [3]},
        {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [4, 5]}
    ]
    
    return questions, interventions, decision_tree


def get_comprehensive_copd_protocol():
    """Get comprehensive COPD protocol data."""
    questions = [
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
    ]
    
    interventions = [
        {"id": 1, "title": "Emergency Response", "description": "Call 911 for severe respiratory distress", "priority": "urgent", "symptom_type": "emergency", "instructions": "Severe dyspnea, confusion, or respiratory failure"},
        {"id": 2, "title": "Infection Protocol", "description": "Antibiotic therapy and physician contact", "priority": "high", "symptom_type": "infection", "instructions": "Signs of respiratory infection requiring treatment"},
        {"id": 3, "title": "Bronchodilator Optimization", "description": "Increase rescue medication use", "priority": "high", "symptom_type": "bronchospasm", "instructions": "Optimize bronchodilator therapy"},
        {"id": 4, "title": "Activity Modification", "description": "Energy conservation techniques", "priority": "medium", "symptom_type": "activity_limitation", "instructions": "Pace activities and use breathing techniques"},
        {"id": 5, "title": "Respiratory Therapy", "description": "Breathing exercises and positioning", "priority": "medium", "symptom_type": "breathing_support", "instructions": "Pursed lip breathing and optimal positioning"},
        {"id": 6, "title": "Environmental Control", "description": "Avoid triggers and irritants", "priority": "medium", "symptom_type": "environmental", "instructions": "Minimize exposure to respiratory irritants"}
    ]
    
    decision_tree = [
        {"id": 1, "symptom_type": "dyspnea", "condition": "greater_than", "value": 7, "next_node_id": 2, "intervention_ids": [1]},
        {"id": 2, "symptom_type": "sputum", "condition": "in", "value": ["Green", "Blood-tinged"], "next_node_id": 3, "intervention_ids": [2]},
        {"id": 3, "symptom_type": "fever", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [2]},
        {"id": 4, "symptom_type": "rescue_inhaler", "condition": "in", "value": ["Much more", "Constantly"], "next_node_id": 5, "intervention_ids": [3]},
        {"id": 5, "symptom_type": "exercise_tolerance", "condition": "equals", "value": "Less than 50 steps", "next_node_id": None, "intervention_ids": [4]},
        {"id": 6, "symptom_type": "edema", "condition": "equals", "value": True, "next_node_id": None, "intervention_ids": [1]},
        {"id": 7, "symptom_type": "stable", "condition": "default", "value": None, "next_node_id": None, "intervention_ids": [5, 6]}
    ]
    
    return questions, interventions, decision_tree


def get_comprehensive_fit_protocol():
    """Get comprehensive FIT protocol data."""
    questions = [
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
    ]
    
    interventions = [
        {"id": 1, "title": "Emergency Dispatch", "description": "Call 911 immediately", "priority": "urgent", "symptom_type": "emergency", "instructions": "Life-threatening symptoms requiring immediate emergency response"},
        {"id": 2, "title": "Urgent Medical Care", "description": "Seek medical care within 1 hour", "priority": "urgent", "symptom_type": "urgent", "instructions": "Serious symptoms requiring prompt medical evaluation"},
        {"id": 3, "title": "Same Day Medical Care", "description": "See healthcare provider today", "priority": "high", "symptom_type": "same_day", "instructions": "Symptoms requiring medical evaluation within hours"},
        {"id": 4, "title": "Next Day Appointment", "description": "Schedule appointment within 24 hours", "priority": "medium", "symptom_type": "next_day", "instructions": "Symptoms requiring medical follow-up soon"},
        {"id": 5, "title": "Home Care Instructions", "description": "Self-care with monitoring", "priority": "low", "symptom_type": "home_care", "instructions": "Symptoms manageable at home with guidelines"},
        {"id": 6, "title": "Follow-up Call", "description": "Schedule follow-up call", "priority": "low", "symptom_type": "follow_up", "instructions": "Monitor symptoms and provide support"}
    ]
    
    decision_tree = [
        {"id": 1, "symptom_type": "urgency", "condition": "equals", "value": "Emergency", "next_node_id": None, "intervention_ids": [1]},
        {"id": 2, "symptom_type": "chest_pain", "condition": "equals", "value": True, "next_node_id": 3, "intervention_ids": [1]},
        {"id": 3, "symptom_type": "dyspnea", "condition": "equals", "value": True, "next_node_id": 4, "intervention_ids": [2]},
        {"id": 4, "symptom_type": "speech_difficulty", "condition": "equals", "value": False, "next_node_id": None, "intervention_ids": [1]},
        {"id": 5, "symptom_type": "pain_level", "condition": "greater_than", "value": 7, "next_node_id": None, "intervention_ids": [2]},
        {"id": 6, "symptom_type": "symptom_duration", "condition": "equals", "value": "Less than 1 hour", "next_node_id": 7, "intervention_ids": [3]},
        {"id": 7, "symptom_type": "urgency", "condition": "equals", "value": "Very urgent", "next_node_id": None, "intervention_ids": [3]},
        {"id": 8, "symptom_type": "call_reason", "condition": "equals", "value": "Routine check-in", "next_node_id": None, "intervention_ids": [5, 6]}
    ]
    
    return questions, interventions, decision_tree


def force_update_protocols():
    """Force update all protocols with comprehensive 15-question assessments."""
    logger.info("🔧 Force updating protocols with comprehensive assessments...")
    
    # Import standardized protocol names
    from src.utils.protocol_names import get_standard_protocol_names
    standard_names = get_standard_protocol_names()
    
    protocols_data = {
        ProtocolType.CANCER: get_comprehensive_cancer_protocol(),
        ProtocolType.HEART_FAILURE: get_comprehensive_heart_failure_protocol(),
        ProtocolType.COPD: get_comprehensive_copd_protocol(),
        ProtocolType.FIT: get_comprehensive_fit_protocol()
    }
    
    updated_count = 0
    
    for protocol_type, (questions, interventions, decision_tree) in protocols_data.items():
        try:
            protocol = Protocol.query.filter_by(protocol_type=protocol_type).first()
            
            if not protocol:
                logger.warning(f"No protocol found for type {protocol_type}")
                continue
            
            logger.info(f"Updating {protocol_type.value} protocol...")
            
            # Direct SQL update to bypass SQLAlchemy caching issues
            # Use standardized name for this protocol type
            standard_name = standard_names[protocol_type]
            
            from sqlalchemy import text
            db.session.execute(
                text("""UPDATE protocols 
                        SET name = :name,
                            questions = :questions,
                            interventions = :interventions, 
                            decision_tree = :decision_tree,
                            version = :version,
                            updated_at = NOW()
                        WHERE id = :protocol_id"""),
                {
                    'name': standard_name,
                    'questions': json.dumps(questions),
                    'interventions': json.dumps(interventions),
                    'decision_tree': json.dumps(decision_tree),
                    'version': f"{float(protocol.version) + 0.1:.1f}",
                    'protocol_id': protocol.id
                }
            )
            
            logger.info(f"✅ Updated {protocol_type.value}: {len(questions)} questions, {len(interventions)} interventions, {len(decision_tree)} decision nodes")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error updating {protocol_type}: {e}")
    
    if updated_count > 0:
        db.session.commit()
        logger.info(f"🎉 Successfully force-updated {updated_count} protocols!")
        return True
    else:
        logger.error("❌ No protocols were updated")
        return False


def main():
    """Main function."""
    logger.info("Force Protocol Update Script Starting...")
    
    app = create_app()
    
    with app.app_context():
        success = force_update_protocols()
        
        if success:
            logger.info("🚀 All protocols now have comprehensive 15-question assessments!")
            logger.info("Visit http://localhost:8081/protocols/1 to see the updated content")
        else:
            logger.error("❌ Protocol update failed")
            sys.exit(1)


if __name__ == "__main__":
    main()