#!/usr/bin/env python3
"""
Create new unpublished agents with template-based prompts for testing
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

sys.path.append('/Users/pkjar/dev.local/companies/quome/cust-steadwell/worktree-cust-steadywellos-webapp/retellai-protocol-injection')

from src.services.protocol_injection import ProtocolInjectionService

def create_dynamic_agent(base_agent_id, agent_name_suffix):
    """Create a new agent with template-based prompt"""
    
    api_key = os.getenv("RETELLAI_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return None
    
    try:
        # Initialize protocol service
        service = ProtocolInjectionService()
        
        # Get template prompt
        template_prompt = service.generate_template_prompt()
        
        # Get base agent configuration
        agent_url = f"https://api.retellai.com/get-agent/{base_agent_id}"
        response = requests.get(agent_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        response.raise_for_status()
        
        base_agent_data = response.json()
        
        print(f"📋 Base agent info:")
        print(f"   Agent ID: {base_agent_id}")
        print(f"   Name: {base_agent_data.get('agent_name', 'Unknown')}")
        print(f"   Voice: {base_agent_data.get('voice_id', 'Unknown')}")
        
        # Create new LLM with template prompt
        print(f"🔧 Creating new LLM with template prompt...")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        create_llm_url = f"https://api.retellai.com/create-retell-llm"
        new_llm_data = {
            "general_prompt": template_prompt,
            "model": "gpt-4o",
            "model_temperature": 0.7,
            "begin_message": "",
            "general_tools": [
                {
                    "type": "end_call",
                    "name": "end_call", 
                    "description": "End the call with user."
                }
            ]
        }
        
        llm_response = requests.post(create_llm_url, json=new_llm_data, headers=headers, timeout=10)
        llm_response.raise_for_status()
        new_llm_id = llm_response.json().get("llm_id")
        
        if not new_llm_id:
            print("❌ Failed to create new LLM")
            return None
        
        print(f"✅ Created new LLM: {new_llm_id}")
        
        # Create new agent with template LLM
        print(f"🔧 Creating new agent...")
        
        create_agent_url = f"https://api.retellai.com/create-agent"
        agent_data = {
            "agent_name": f"{base_agent_data.get('agent_name', 'DOB-Agent')}-{agent_name_suffix}",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": new_llm_id
            },
            "voice_id": base_agent_data.get("voice_id", "11labs-Adrian"),
            "voice_model": base_agent_data.get("voice_model", "eleven_turbo_v2"),
            "voice_temperature": base_agent_data.get("voice_temperature", 1),
            "voice_speed": base_agent_data.get("voice_speed", 1),
            "volume": base_agent_data.get("volume", 1),
            "responsiveness": base_agent_data.get("responsiveness", 1),
            "interruption_sensitivity": base_agent_data.get("interruption_sensitivity", 1),
            "enable_backchannel": base_agent_data.get("enable_backchannel", True),
            "language": base_agent_data.get("language", "en-US"),
            "webhook_url": base_agent_data.get("webhook_url"),
            "enable_transcription_formatting": base_agent_data.get("enable_transcription_formatting", True),
            "end_call_after_silence_ms": base_agent_data.get("end_call_after_silence_ms", 600000),
            "max_call_duration_ms": base_agent_data.get("max_call_duration_ms", 3600000)
        }
        
        agent_response = requests.post(create_agent_url, json=agent_data, headers=headers, timeout=10)
        agent_response.raise_for_status()
        
        new_agent_id = agent_response.json().get("agent_id")
        
        if new_agent_id:
            print(f"✅ Created new agent: {new_agent_id}")
            print(f"   Name: {agent_data['agent_name']}")
            print(f"   LLM: {new_llm_id}")
            print(f"   Status: DRAFT (unpublished)")
            return new_agent_id
        else:
            print("❌ Failed to create new agent")
            return None
        
    except Exception as e:
        print(f"❌ Error creating dynamic agent: {e}")
        return None

def main():
    print("🔧 Creating new agents with template-based prompts...")
    print("=" * 60)
    
    # Get base agent IDs
    local_agent_id = os.getenv("RETELLAI_LOCAL_AGENT_ID")
    remote_agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
    
    new_agents = {}
    
    # Create new LOCAL agent
    if local_agent_id:
        print(f"📱 Creating new LOCAL agent based on: {local_agent_id}")
        new_local_id = create_dynamic_agent(local_agent_id, "Dynamic-Local")
        if new_local_id:
            new_agents["LOCAL"] = new_local_id
        print()
    
    # Create new REMOTE agent
    if remote_agent_id:
        print(f"☁️  Creating new REMOTE agent based on: {remote_agent_id}")
        new_remote_id = create_dynamic_agent(remote_agent_id, "Dynamic-Remote")
        if new_remote_id:
            new_agents["REMOTE"] = new_remote_id
        print()
    
    # Summary
    print("=" * 60)
    print("🎯 New agents created!")
    print()
    
    if new_agents:
        print("📋 Update your .env file with these new agent IDs:")
        print()
        for env_type, agent_id in new_agents.items():
            print(f"# New {env_type} agent with dynamic variables support")
            print(f"RETELLAI_{env_type}_AGENT_ID={agent_id}")
        print()
        print("🔧 These agents have template-based prompts with {{placeholders}}")
        print("✅ Ready to test DOB verification with dynamic variables!")
    else:
        print("❌ No new agents were created")

if __name__ == "__main__":
    main()