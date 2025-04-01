#!/usr/bin/env python3
"""
Script to fix assessment protocol IDs and other data issues
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.protocol import Protocol
from app.models.patient import Patient, ProtocolType
from app.models.assessment import Assessment, FollowUpPriority
from app.models.user import User, UserRole

def fix_assessment_protocols():
    """Fix assessment protocol IDs by reassigning to the correct protocol IDs"""
    app = create_app()
    with app.app_context():
        # Get the correct protocol IDs
        cancer_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.CANCER).first()
        heart_failure_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.HEART_FAILURE).first()
        copd_protocol = Protocol.query.filter_by(protocol_type=ProtocolType.COPD).first()
        
        if not cancer_protocol or not heart_failure_protocol or not copd_protocol:
            print("ERROR: One or more protocols are missing in the database")
            return
            
        print(f"Found protocols: Cancer (ID: {cancer_protocol.id}), Heart Failure (ID: {heart_failure_protocol.id}), COPD (ID: {copd_protocol.id})")
        
        # Get all patients and their protocol types
        patients = Patient.query.all()
        for patient in patients:
            # Determine correct protocol ID based on patient's protocol type
            correct_protocol_id = None
            if patient.protocol_type == ProtocolType.CANCER:
                correct_protocol_id = cancer_protocol.id
            elif patient.protocol_type == ProtocolType.HEART_FAILURE:
                correct_protocol_id = heart_failure_protocol.id
            elif patient.protocol_type == ProtocolType.COPD:
                correct_protocol_id = copd_protocol.id
            else:
                print(f"WARNING: Patient {patient.id} has unknown protocol type: {patient.protocol_type}")
                continue
                
            # Get all assessments for this patient
            assessments = Assessment.query.filter_by(patient_id=patient.id).all()
            assessment_count = len(assessments)
            
            if assessment_count == 0:
                print(f"Patient {patient.id} ({patient.first_name} {patient.last_name}) has no assessments")
                continue
                
            print(f"Updating {assessment_count} assessments for Patient {patient.id} ({patient.first_name} {patient.last_name}) to protocol ID {correct_protocol_id}")
            
            # Update all assessments for this patient
            for assessment in assessments:
                if assessment.protocol_id != correct_protocol_id:
                    old_id = assessment.protocol_id
                    assessment.protocol_id = correct_protocol_id
                    print(f"  Assessment {assessment.id}: Changed protocol ID from {old_id} to {correct_protocol_id}")
                else:
                    print(f"  Assessment {assessment.id}: Already has correct protocol ID {correct_protocol_id}")
            
        # Commit all changes
        db.session.commit()
        print("Database updated successfully!")

def fix_mary_johnson_assessments():
    """Fix specific issues with Mary Johnson's assessments"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in the database!")
            return
            
        # Find assessments from March 25, 2025
        march25_assessments = Assessment.query.filter(
            Assessment.patient_id == mary.id,
            Assessment.assessment_date >= '2025-03-25 00:00:00',
            Assessment.assessment_date < '2025-03-26 00:00:00'
        ).all()
        
        if not march25_assessments:
            print("No March 25 assessments found for Mary Johnson!")
            return
            
        print(f"Found {len(march25_assessments)} assessments on March 25 for Mary Johnson")
        
        # Make sure all of these are properly linked and consistent
        for assessment in march25_assessments:
            # Set all to HIGH priority with consistent follow-up dates
            if assessment.follow_up_priority != 'HIGH':
                assessment.follow_up_priority = FollowUpPriority.HIGH
                print(f"Set assessment {assessment.id} to HIGH priority")
                
            # Set follow-up dates consistently
            assessment.follow_up_date = datetime(2025, 4, 2, 10, 0, 0)
            print(f"Set assessment {assessment.id} follow-up date to April 2, 2025")
            
            # Make sure each has proper AI guidance
            if not assessment.ai_guidance:
                assessment.ai_guidance = "Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely."
                print(f"Set AI guidance for assessment {assessment.id}")
                
            # Make sure each has proper notes
            if not assessment.notes:
                assessment.notes = "Patient reports severe increase in edema, dyspnea, and new onset chest pain. Needs immediate medical attention."
                print(f"Set notes for assessment {assessment.id}")
                
            # Make sure conducted_by is set
            if not assessment.conducted_by_id:
                # Find a nurse to assign
                nurse = User.query.filter_by(role=UserRole.NURSE).first()
                if nurse:
                    assessment.conducted_by_id = nurse.id
                    print(f"Set conducted_by for assessment {assessment.id} to {nurse.first_name} {nurse.last_name}")
        
        # Commit changes
        db.session.commit()
        print("Mary Johnson's assessments fixed and updated in the database")

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if command == "protocols":
        fix_assessment_protocols()
    elif command == "mary":
        fix_mary_johnson_assessments()
    elif command == "all":
        fix_assessment_protocols()
        fix_mary_johnson_assessments()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python fix_data.py [all|protocols|mary]")
        print("  all - Run all fixes")
        print("  protocols - Fix all assessment protocol IDs")
        print("  mary - Fix Mary Johnson's assessments")