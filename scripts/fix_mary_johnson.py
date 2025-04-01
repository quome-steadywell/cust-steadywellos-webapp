#!/usr/bin/env python3
"""
Script to fix Mary Johnson's assessments and primary nurse
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from app import create_app, db
from app.models.patient import Patient
from app.models.protocol import Protocol
from app.models.assessment import Assessment
from app.models.user import User, UserRole
from app.models.assessment import FollowUpPriority
from datetime import datetime

def fix_mary_johnson_data():
    """Fix Mary Johnson's data in the database"""
    app = create_app()
    with app.app_context():
        # Find Mary Johnson
        mary = Patient.query.filter_by(first_name="Mary", last_name="Johnson").first()
        if not mary:
            print("Mary Johnson not found in the database!")
            return
            
        # Find nurse1
        nurse1 = User.query.filter_by(username="nurse1").first()
        if not nurse1:
            print("Nurse1 not found in the database!")
            return
            
        # Update primary nurse
        print(f"Mary Johnson (ID: {mary.id}) - Current primary nurse ID: {mary.primary_nurse_id}")
        print(f"Nurse1 (ID: {nurse1.id})")
        
        if mary.primary_nurse_id != nurse1.id:
            print(f"Setting Mary's primary nurse to nurse1 (ID: {nurse1.id})")
            mary.primary_nurse_id = nurse1.id
            db.session.commit()
        else:
            print("Mary's primary nurse is already set to nurse1")
        
        # Find protocol for Mary's protocol type
        protocol = Protocol.query.filter_by(protocol_type=mary.protocol_type).first()
        if not protocol:
            print(f"No protocol found for type {mary.protocol_type}!")
            return
            
        print(f"Found protocol (ID: {protocol.id}, Name: {protocol.name})")
        
        # Get Mary's assessments
        assessments = Assessment.query.filter_by(patient_id=mary.id).all()
        print(f"Found {len(assessments)} assessments for Mary Johnson")
        
        # Fix protocol IDs and other issues
        for assessment in assessments:
            print(f"\nAssessment {assessment.id}:")
            print(f"  Date: {assessment.assessment_date}")
            print(f"  Protocol ID: {assessment.protocol_id}")
            
            # Fix protocol ID if needed
            if assessment.protocol_id != protocol.id:
                print(f"  FIXING: Setting protocol_id from {assessment.protocol_id} to {protocol.id}")
                assessment.protocol_id = protocol.id
                
            # Fix follow-up settings for March 25 assessments
            if assessment.assessment_date.date() == datetime(2025, 3, 25).date():
                print(f"  This is a March 25 assessment")
                
                # Ensure follow-up settings are correct
                if not assessment.follow_up_needed:
                    print(f"  FIXING: Setting follow_up_needed to True")
                    assessment.follow_up_needed = True
                    
                if assessment.follow_up_priority != FollowUpPriority.HIGH:
                    print(f"  FIXING: Setting follow_up_priority to HIGH")
                    assessment.follow_up_priority = FollowUpPriority.HIGH
                    
                # Set a consistent follow-up date
                follow_up_date = datetime(2025, 4, 2, 10, 0, 0)
                print(f"  FIXING: Setting follow_up_date to {follow_up_date}")
                assessment.follow_up_date = follow_up_date
                
                # Ensure symptoms are correctly set
                if 'dyspnea' not in assessment.symptoms or assessment.symptoms['dyspnea'] < 8:
                    print(f"  FIXING: Setting dyspnea to 8")
                    assessment.symptoms['dyspnea'] = 8
                    
                if 'edema' not in assessment.symptoms or assessment.symptoms['edema'] < 9:
                    print(f"  FIXING: Setting edema to 9")
                    assessment.symptoms['edema'] = 9
                    
                if 'chest_pain' not in assessment.symptoms or not assessment.symptoms['chest_pain']:
                    print(f"  FIXING: Setting chest_pain to 1")
                    assessment.symptoms['chest_pain'] = 1
                    
                # Ensure notes and AI guidance are set
                if not assessment.notes:
                    assessment.notes = "Patient reports severe increase in edema, dyspnea, and new onset chest pain. Needs immediate medical attention."
                    print(f"  FIXING: Set notes")
                    
                if not assessment.ai_guidance:
                    assessment.ai_guidance = "Urgent review by physician recommended. Consider hospital evaluation for decompensated heart failure with possible acute coronary syndrome. Increase diuretic dose and monitor fluid status closely."
                    print(f"  FIXING: Set AI guidance")
        
        # Commit all changes
        db.session.commit()
        print("\nAll Mary Johnson data fixed and updated in the database!")
                
if __name__ == "__main__":
    fix_mary_johnson_data()