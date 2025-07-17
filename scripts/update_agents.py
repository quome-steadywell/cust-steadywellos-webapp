#!/usr/bin/env python3
"""
One-time script to update both LOCAL and REMOTE agents with template-based prompts
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append('/Users/pkjar/dev.local/companies/quome/cust-steadwell/worktree-cust-steadywellos-webapp/retellai-protocol-injection')

from src.services.protocol_injection import ProtocolInjectionService
from src.utils.logger import get_logger

def main():
    logger = get_logger()
    
    # Initialize the service
    service = ProtocolInjectionService()
    
    # Get agent IDs from environment
    local_agent_id = os.getenv("RETELLAI_LOCAL_AGENT_ID")
    remote_agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
    
    print("🔧 Updating agents with template-based prompts...")
    print("=" * 60)
    
    # Update LOCAL agent
    if local_agent_id:
        print(f"📱 Updating LOCAL agent: {local_agent_id}")
        try:
            success = service.update_agent_with_template(local_agent_id)
            if success:
                print(f"✅ LOCAL agent {local_agent_id} updated successfully")
            else:
                print(f"❌ Failed to update LOCAL agent {local_agent_id}")
        except Exception as e:
            print(f"❌ Error updating LOCAL agent: {e}")
    else:
        print("⚠️  LOCAL agent ID not found in environment")
    
    print()
    
    # Update REMOTE agent
    if remote_agent_id:
        print(f"☁️  Updating REMOTE agent: {remote_agent_id}")
        try:
            success = service.update_agent_with_template(remote_agent_id)
            if success:
                print(f"✅ REMOTE agent {remote_agent_id} updated successfully")
            else:
                print(f"❌ Failed to update REMOTE agent {remote_agent_id}")
        except Exception as e:
            print(f"❌ Error updating REMOTE agent: {e}")
    else:
        print("⚠️  REMOTE agent ID not found in environment")
    
    print()
    print("=" * 60)
    print("🎯 Agent updates complete!")
    print("📋 Next: Test the dynamic variables approach")

if __name__ == "__main__":
    main()