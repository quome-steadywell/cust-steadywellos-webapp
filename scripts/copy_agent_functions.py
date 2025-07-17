#!/usr/bin/env python3
"""
Copy functions from old agent to new agent via Retell AI API
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

def get_agent_config(agent_id):
    """Get functions and post-call analysis from an agent"""
    api_key = os.getenv("RETELLAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found")
        return None, None
    
    try:
        # Get agent info
        agent_url = f"https://api.retellai.com/get-agent/{agent_id}"
        response = requests.get(agent_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        response.raise_for_status()
        
        agent_data = response.json()
        
        # Extract post-call analysis from agent (using correct field name)
        post_call_analysis_data = agent_data.get("post_call_analysis_data", [])
        print(f"📊 Found {len(post_call_analysis_data)} post-call analysis fields in agent {agent_id}")
        for field in post_call_analysis_data:
            print(f"   - {field.get('name', 'Unknown')}: {field.get('description', 'No description')[:50]}...")
        
        # Extract functions from response_engine
        response_engine = agent_data.get("response_engine", {})
        if response_engine.get("type") == "retell-llm":
            # Get LLM details
            llm_id = response_engine.get("llm_id")
            llm_url = f"https://api.retellai.com/get-retell-llm/{llm_id}"
            llm_response = requests.get(llm_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
            llm_response.raise_for_status()
            
            llm_data = llm_response.json()
            general_tools = llm_data.get("general_tools", [])
            
            print(f"📋 Found {len(general_tools)} functions in agent {agent_id}")
            for tool in general_tools:
                print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            
            return general_tools, post_call_analysis_data
        else:
            print(f"⚠️  Agent {agent_id} does not use retell-llm response engine")
            return None, post_call_analysis_data
            
    except Exception as e:
        print(f"❌ Error getting config from agent {agent_id}: {e}")
        return None, None

def update_agent_config(agent_id, functions, post_call_analysis_data):
    """Update agent with new functions and post-call analysis"""
    api_key = os.getenv("RETELLAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        # Get current agent info
        agent_url = f"https://api.retellai.com/get-agent/{agent_id}"
        response = requests.get(agent_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        agent_data = response.json()
        response_engine = agent_data.get("response_engine", {})
        
        # Update post-call analysis data on agent
        if post_call_analysis_data:
            agent_update_url = f"https://api.retellai.com/update-agent/{agent_id}"
            agent_update_data = {"post_call_analysis_data": post_call_analysis_data}
            
            agent_response = requests.patch(agent_update_url, json=agent_update_data, headers=headers, timeout=10)
            agent_response.raise_for_status()
            
            print(f"✅ Updated agent {agent_id} with {len(post_call_analysis_data)} post-call analysis fields")
        
        # Update functions on LLM
        if response_engine.get("type") == "retell-llm" and functions:
            llm_id = response_engine.get("llm_id")
            
            llm_update_url = f"https://api.retellai.com/update-retell-llm/{llm_id}"
            llm_data = {"general_tools": functions}
            
            llm_response = requests.patch(llm_update_url, json=llm_data, headers=headers, timeout=10)
            llm_response.raise_for_status()
            
            print(f"✅ Updated agent {agent_id} with {len(functions)} functions")
        
        return True
            
    except Exception as e:
        print(f"❌ Error updating agent {agent_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {e.response.text}")
        return False

def main():
    print("📋 Copying functions and post-call analysis between agents...")
    print("=" * 60)
    
    # Agent IDs
    old_agent_id = "agent_88609f029da1444efad68581eb"  # Original REMOTE agent
    new_remote_id = "agent_d8201e62bbac187faad42956b5"  # New dynamic REMOTE agent
    new_local_id = "agent_45c56dd9129c4ad312aaa2604d"   # New dynamic LOCAL agent
    
    print(f"📤 Source agent: {old_agent_id}")
    print(f"📥 Target agents: {new_remote_id} (REMOTE), {new_local_id} (LOCAL)")
    print()
    
    # Get functions and post-call analysis from old agent
    print("🔍 Getting configuration from source agent...")
    functions, post_call_analysis_data = get_agent_config(old_agent_id)
    
    if not functions and not post_call_analysis_data:
        print("❌ No configuration found or error occurred")
        return
    
    print()
    
    # Copy configuration to both new agents
    print("📋 Copying configuration to REMOTE agent...")
    remote_success = update_agent_config(new_remote_id, functions, post_call_analysis_data)
    
    print()
    print("📋 Copying configuration to LOCAL agent...")
    local_success = update_agent_config(new_local_id, functions, post_call_analysis_data)
    
    print()
    print("=" * 60)
    
    if remote_success and local_success:
        print("🎉 Configuration copied successfully to both agents!")
        print(f"✅ Both agents now have the same configuration as {old_agent_id}")
        print()
        if functions:
            print("📋 Functions copied:")
            for func in functions:
                print(f"   - {func.get('name', 'Unknown')}")
        if post_call_analysis_data:
            print("📊 Post-call analysis fields copied:")
            for field in post_call_analysis_data:
                print(f"   - {field.get('name', 'Unknown')}")
    elif remote_success or local_success:
        print("⚠️  Partial success:")
        print(f"   REMOTE agent: {'✅ Success' if remote_success else '❌ Failed'}")
        print(f"   LOCAL agent: {'✅ Success' if local_success else '❌ Failed'}")
    else:
        print("❌ Failed to copy configuration to both agents")
        print("🔧 You may need to copy them manually via the dashboard")

if __name__ == "__main__":
    main()