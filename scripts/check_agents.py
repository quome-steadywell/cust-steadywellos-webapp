#!/usr/bin/env python3
"""
Check what prompts the current agents have
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

def check_agent_prompt(agent_id, agent_name):
    """Check what prompt an agent currently has"""
    api_key = os.getenv("RETELLAI_API_KEY")
    
    if not api_key:
        print(f"❌ No API key found")
        return
    
    try:
        # Get agent info
        agent_url = f"https://api.retellai.com/get-agent/{agent_id}"
        response = requests.get(agent_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        response.raise_for_status()
        
        agent_data = response.json()
        llm_id = agent_data.get("response_engine", {}).get("llm_id")
        is_published = agent_data.get("is_published", False)
        
        print(f"📋 {agent_name} Agent Info:")
        print(f"   Agent ID: {agent_id}")
        print(f"   LLM ID: {llm_id}")
        print(f"   Published: {is_published}")
        
        if llm_id:
            # Get LLM info
            llm_url = f"https://api.retellai.com/get-retell-llm/{llm_id}"
            llm_response = requests.get(llm_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            llm_response.raise_for_status()
            
            llm_data = llm_response.json()
            prompt = llm_data.get("general_prompt", "")
            
            print(f"   Current Prompt (first 200 chars):")
            print(f"   {prompt[:200]}...")
            
            # Check if prompt contains placeholders
            placeholders = ["{{patient_name}}", "{{expected_dob}}", "{{protocol_type}}", "{{primary_diagnosis}}"]
            has_placeholders = any(placeholder in prompt for placeholder in placeholders)
            
            print(f"   Has Dynamic Variable Placeholders: {has_placeholders}")
            
            if has_placeholders:
                found_placeholders = [p for p in placeholders if p in prompt]
                print(f"   Found Placeholders: {found_placeholders}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error checking {agent_name} agent: {e}")
        print()

def main():
    print("🔍 Checking current agent prompts...")
    print("=" * 60)
    
    # Check both agents
    local_agent_id = os.getenv("RETELLAI_LOCAL_AGENT_ID")
    remote_agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
    
    if local_agent_id:
        check_agent_prompt(local_agent_id, "LOCAL")
    else:
        print("⚠️  LOCAL agent ID not found")
    
    if remote_agent_id:
        check_agent_prompt(remote_agent_id, "REMOTE")
    else:
        print("⚠️  REMOTE agent ID not found")
    
    print("=" * 60)
    print("🎯 Agent check complete!")

if __name__ == "__main__":
    main()