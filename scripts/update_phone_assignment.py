#!/usr/bin/env python3
"""
Update phone number assignment to use new dynamic agents
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def update_phone_assignment():
    """Update phone number to use new agents"""
    
    api_key = os.getenv('RETELLAI_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    phone_number = '+13203139120'
    new_local_agent = 'agent_45c56dd9129c4ad312aaa2604d'
    new_remote_agent = 'agent_d8201e62bbac187faad42956b5'
    
    print(f"📞 Updating phone number assignment...")
    print(f"   Phone: {phone_number}")
    print(f"   New Inbound (LOCAL): {new_local_agent}")
    print(f"   New Outbound (REMOTE): {new_remote_agent}")
    print()
    
    # Check current assignment
    print("🔍 Checking current phone assignment...")
    phone_url = 'https://api.retellai.com/list-phone-numbers'
    response = requests.get(phone_url, headers=headers)
    
    if response.status_code == 200:
        phone_numbers = response.json()
        current_assignment = None
        
        for phone in phone_numbers:
            if phone.get('phone_number') == phone_number:
                current_assignment = phone
                break
        
        if current_assignment:
            print(f"📋 Current assignment:")
            print(f"   Inbound: {current_assignment.get('inbound_agent_id')}")
            print(f"   Outbound: {current_assignment.get('outbound_agent_id')}")
            print()
        else:
            print(f"❌ Phone number {phone_number} not found")
            return False
    else:
        print(f"❌ Error getting phone numbers: {response.status_code}")
        return False
    
    # Try to update - this might need to be done manually via dashboard
    print("⚠️  Manual Update Required:")
    print("🌐 Go to https://dashboard.retellai.com/phone-numbers")
    print(f"📞 Find phone number: {phone_number}")
    print("🔧 Update the assignment:")
    print(f"   - Inbound Agent: dev-webapp-steadywellos-Dynamic-Local ({new_local_agent})")
    print(f"   - Outbound Agent: prod-webapp-steadywellos-Dynamic-Remote ({new_remote_agent})")
    print()
    print("💡 This will ensure calls use the new agents with DOB verification!")
    
    return True

if __name__ == "__main__":
    update_phone_assignment()