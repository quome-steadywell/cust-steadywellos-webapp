#!/usr/bin/env python3
"""
Check the post-call analysis configuration of the original agent
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

def check_agent_details(agent_id):
    """Check all details of an agent"""
    api_key = os.getenv("RETELLAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found")
        return
    
    try:
        # Get agent info
        agent_url = f"https://api.retellai.com/get-agent/{agent_id}"
        response = requests.get(agent_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        response.raise_for_status()
        
        agent_data = response.json()
        
        print(f"📋 Agent {agent_id} Details:")
        print(f"   Name: {agent_data.get('agent_name', 'Unknown')}")
        print(f"   Published: {agent_data.get('is_published', False)}")
        print(f"   Voice: {agent_data.get('voice_id', 'Unknown')}")
        print()
        
        # Check post-call analysis schema
        post_call_analysis_schema = agent_data.get("post_call_analysis_schema", [])
        print(f"📊 Post-call analysis schema fields: {len(post_call_analysis_schema)}")
        
        if post_call_analysis_schema:
            for field in post_call_analysis_schema:
                print(f"   - {field.get('name', 'Unknown')}: {field.get('description', 'No description')}")
                print(f"     Type: {field.get('type', 'Unknown')}")
                if 'enum' in field:
                    print(f"     Options: {field.get('enum', [])}")
        else:
            print("   No post-call analysis schema fields found")
        
        # Check post-call analysis data 
        post_call_analysis_data = agent_data.get("post_call_analysis_data", [])
        print(f"📊 Post-call analysis data fields: {len(post_call_analysis_data)}")
        
        if post_call_analysis_data:
            for field in post_call_analysis_data:
                print(f"   - {field.get('name', 'Unknown')}: {field.get('description', 'No description')}")
                print(f"     Type: {field.get('type', 'Unknown')}")
                if 'enum' in field:
                    print(f"     Options: {field.get('enum', [])}")
                print(f"     Full field: {json.dumps(field, indent=4)}")
        else:
            print("   No post-call analysis data fields found")
        
        print()
        
        # Check all keys in the agent data
        print("🔍 All agent configuration keys:")
        for key in sorted(agent_data.keys()):
            if key != "post_call_analysis_schema":  # Already shown above
                value = agent_data[key]
                if isinstance(value, (dict, list)) and len(str(value)) > 100:
                    print(f"   {key}: {type(value).__name__} (length: {len(value) if isinstance(value, list) else 'N/A'})")
                else:
                    print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error checking agent {agent_id}: {e}")

def main():
    print("🔍 Checking post-call analysis configuration...")
    print("=" * 60)
    
    # Check original agent
    old_agent_id = "agent_88609f029da1444efad68581eb"  # Original REMOTE agent
    
    check_agent_details(old_agent_id)

if __name__ == "__main__":
    main()