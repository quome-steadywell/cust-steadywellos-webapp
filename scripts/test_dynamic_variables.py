#!/usr/bin/env python3
"""
Test the dynamic variables approach
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append('/Users/pkjar/dev.local/companies/quome/cust-steadwell/worktree-cust-steadywellos-webapp/retellai-protocol-injection')

from src.app import create_app
from src.services.protocol_injection import ProtocolInjectionService
from src.core.call_service import make_retell_call
from src.utils.logger import get_logger

def test_dynamic_variables():
    """Test that dynamic variables are being prepared correctly"""
    
    print("🧪 Testing Dynamic Variables Preparation")
    print("=" * 50)
    
    # Test protocol injection service
    service = ProtocolInjectionService()
    
    # Test with a patient ID (assuming patient 1 exists)
    patient_id = 1
    
    print(f"📋 Testing patient ID: {patient_id}")
    
    try:
        # Test prepare_agent_for_call
        success, dynamic_variables = service.prepare_agent_for_call(patient_id)
        
        if success:
            print("✅ Dynamic variables prepared successfully!")
            print(f"📊 Variables prepared:")
            for key, value in dynamic_variables.items():
                print(f"   {key}: {value}")
        else:
            print("❌ Failed to prepare dynamic variables")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dynamic variables: {e}")
        return False
    
    print()
    print("=" * 50)
    
    # Test call service integration
    print("🔧 Testing Call Service Integration")
    
    try:
        # Create a test patient dict
        test_patient = {
            "id": patient_id,
            "first_name": "John",
            "last_name": "Doe", 
            "phone_number": "+12066968474",
            "email_address": "john.doe@example.com"
        }
        
        print(f"📞 Testing call preparation for: {test_patient['first_name']} {test_patient['last_name']}")
        
        # Test make_retell_call (in simulation mode)
        call_id = make_retell_call(test_patient)
        
        if call_id:
            print(f"✅ Call prepared successfully! Call ID: {call_id}")
            return True
        else:
            print("❌ Failed to prepare call")
            return False
            
    except Exception as e:
        print(f"❌ Error testing call service: {e}")
        return False

def main():
    # Create Flask app and context
    app = create_app()
    
    with app.app_context():
        logger = get_logger()
        
        print("🚀 Testing Dynamic Variables Implementation")
        print("=" * 60)
        
        # Check environment
        make_real_call = os.getenv("MAKE_REAL_CALL", "false").lower() == "true"
        local_agent_id = os.getenv("RETELLAI_LOCAL_AGENT_ID")
        
        print(f"📍 Environment: {'REAL CALLS' if make_real_call else 'SIMULATION'}")
        print(f"🤖 Local Agent: {local_agent_id}")
        print()
        
        # Run tests
        success = test_dynamic_variables()
        
        print()
        print("=" * 60)
        
        if success:
            print("🎉 Dynamic Variables Implementation: WORKING!")
            print("✅ Ready to test DOB verification with different patients")
            print()
            print("📋 Next steps:")
            print("1. Test with actual patient data")
            print("2. Verify DOB verification works with dynamic variables")
            print("3. Test with different protocol types")
        else:
            print("❌ Dynamic Variables Implementation: FAILED")
            print("🔧 Check logs for details")

if __name__ == "__main__":
    main()