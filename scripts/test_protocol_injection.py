#!/usr/bin/env python3
"""
Test script for protocol injection service

This script tests the protocol injection functionality by:
1. Loading a sample patient with protocol
2. Generating protocol-enhanced prompt
3. Configuring the Retell AI agent (dry-run mode available)
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import src modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from src import create_app, db
from src.models.patient import Patient, ProtocolType
from src.models.protocol import Protocol
from src.services.protocol_injection import ProtocolInjectionService
from src.utils.logger import get_logger

logger = get_logger()


def test_protocol_injection(patient_id: int = None, dry_run: bool = True):
    """Test protocol injection for a patient"""
    
    app = create_app()
    with app.app_context():
        # Get or create test patient
        if patient_id:
            patient = db.session.query(Patient).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
        else:
            # Find first patient with a protocol
            patient = db.session.query(Patient).filter(
                Patient.protocol_type.in_([
                    ProtocolType.CANCER,
                    ProtocolType.HEART_FAILURE, 
                    ProtocolType.COPD
                ])
            ).first()
            
            if not patient:
                logger.error("No patients found with protocols")
                return False
        
        logger.info(f"Testing with patient: {patient.full_name} (ID: {patient.id})")
        logger.info(f"Protocol type: {patient.protocol_type}")
        
        # Get protocol
        protocol = db.session.query(Protocol).filter_by(
            protocol_type=patient.protocol_type,
            is_active=True
        ).first()
        
        if not protocol:
            logger.error(f"No active protocol found for {patient.protocol_type}")
            return False
            
        logger.info(f"Found protocol: {protocol.name}")
        logger.info(f"Questions: {len(protocol.questions)}")
        logger.info(f"Decision tree nodes: {len(protocol.decision_tree)}")
        
        # Create service and generate prompt
        service = ProtocolInjectionService()
        enhanced_prompt = service.generate_protocol_prompt(patient, protocol)
        
        print("\n" + "="*80)
        print("GENERATED PROTOCOL-ENHANCED PROMPT:")
        print("="*80)
        print(enhanced_prompt)
        print("="*80)
        
        if not dry_run:
            # Actually configure the agent
            agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID", "agent_ca445602b7ce60f9d67037e3d8")
            logger.info(f"Configuring agent {agent_id} with protocol...")
            
            success = service.configure_agent_for_patient(agent_id, patient.id)
            if success:
                logger.info("✅ Agent configured successfully!")
            else:
                logger.error("❌ Failed to configure agent")
                return False
        else:
            logger.info("🔍 Dry run mode - not actually updating agent")
        
        return True


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test protocol injection service")
    parser.add_argument("--patient-id", type=int, help="Specific patient ID to test")
    parser.add_argument("--live", action="store_true", help="Actually update the agent (not dry run)")
    
    args = parser.parse_args()
    
    dry_run = not args.live
    if dry_run:
        logger.info("Running in DRY RUN mode - will not update agent")
    else:
        logger.info("Running in LIVE mode - will update agent")
    
    success = test_protocol_injection(args.patient_id, dry_run)
    
    if success:
        logger.info("✅ Test completed successfully")
    else:
        logger.error("❌ Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()