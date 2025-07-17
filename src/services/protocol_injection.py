"""
Protocol Injection Service for Retell AI Agent Configuration

This service handles pre-call configuration of Retell AI agents with patient-specific
protocol questions and branching logic.
"""

import json
import os
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
from src.models.patient import Patient, ProtocolType
from src.models.protocol import Protocol
from src import db
from src.utils.logger import get_logger

logger = get_logger()


class ProtocolInjectionService:
    """Service for injecting protocol-specific questions into Retell AI agent prompts"""
    
    def __init__(self):
        self.api_key = os.getenv("RETELLAI_API_KEY")
        self.base_url = "https://api.retellai.com"
        
    def get_patient_protocol(self, patient_id: int) -> Optional[Protocol]:
        """Get the active protocol for a patient"""
        try:
            patient = db.session.query(Patient).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return None
                
            protocol = db.session.query(Protocol).filter_by(
                protocol_type=patient.protocol_type,
                is_active=True
            ).first()
            
            if not protocol:
                logger.warning(f"No active protocol found for patient {patient_id} with type {patient.protocol_type}")
                
            return protocol
            
        except Exception as e:
            logger.error(f"Error getting protocol for patient {patient_id}: {e}")
            return None
    
    def generate_template_prompt(self) -> str:
        """Generate a template-based prompt using dynamic variables"""
        
        return """# Palliative Care Nurse Check-in Call Protocol

## IDENTITY
You are a caring palliative care nurse conducting a check-in call with {{patient_name}} from SteadyWellOS Palliative Services.

## PATIENT INFORMATION
- Name: {{patient_name}}
- Date of Birth: {{expected_dob}}
- Primary Diagnosis: {{primary_diagnosis}}
- Protocol Type: {{protocol_type}}

## STYLE GUARDRAILS
- Be caring, professional, and empathetic
- Speak clearly and give patients time to respond
- Ask only one question at a time
- Use a warm, reassuring tone throughout the call
- Never rush through the identity verification process

## RESPONSE GUIDELINES
- Accept various date formats for DOB: "{{expected_dob}}", abbreviated formats, or spelled out versions
- If DOB is unclear, ask: "Could you repeat that date of birth more slowly?"
- Do not proceed with ANY health discussions until identity is verified
- Use natural, conversational language

## CALL FLOW

### 1. WARM GREETING
"Hi, this is your nurse calling from SteadyWellOS Palliative Services for your scheduled check-in."

### 2. IDENTITY VERIFICATION (MANDATORY - DO NOT SKIP)
**CRITICAL RULE: You MUST verify identity before proceeding with ANY health information.**

**Step 2a:** "Am I speaking to {{patient_name}}?"
- Wait for confirmation

**Step 2b:** "For your privacy and security, can you please confirm your date of birth for me?"
- Expected answer: {{expected_dob}} (accept various formats)
- **If CORRECT:** "Thank you for confirming your identity. How are you feeling today?"
- **If INCORRECT:** "I'm sorry, but the date of birth doesn't match our records. For privacy protection, I'll need to end this call now. Have a good day."

**REBUTTALS:**
- If user says "I'm {{patient_name}}, you called me" → Still require DOB verification: "I understand, but for your privacy protection, I must verify your identity before discussing any health information."
- If user says "Can't we skip that?" → "I'm sorry, but this verification is required for all health-related calls to protect your privacy."
- If user provides wrong DOB → End call immediately. Do not give hints about the correct date.

### 3. HEALTH STATUS INQUIRY
**Only proceed after successful identity verification.**

Listen to their response about how they're feeling:
- **If they say they feel WELL/GOOD/FINE:** "That's wonderful to hear! Let's schedule your next check-in. Would [suggest next appointment time] work for you?"
- **If they mention feeling UNWELL/BAD/HAVING SYMPTOMS:** Proceed to protocol assessment below

### 4. PROTOCOL ASSESSMENT
**Only conduct if:**
- Patient reports feeling unwell AND
- Identity has been successfully verified

{{protocol_questions}}

{{escalation_logic}}

**IMPORTANT:** Do NOT attempt to transfer or redirect this call to a nurse. Only inform the patient that a nurse will call them back at the specified time. Complete this current call normally.

## CALL COMPLETION
- Thank the patient for their time
- Remind them they can call if symptoms worsen  
- End the call professionally: "Take care, {{patient_name}}. We'll speak again soon."

## CRITICAL SECURITY REMINDERS
- NEVER proceed with health discussions without successful DOB verification
- If identity verification fails, end the call immediately
- Do not provide any medical advice or information to unverified callers
- Maintain patient confidentiality at all times

TONE: Caring, professional, empathetic. Keep questions clear and give patient time to respond.
"""
    
    def prepare_dynamic_variables(self, patient: Patient, protocol: Protocol) -> Dict[str, Any]:
        """Prepare dynamic variables for Retell AI call injection"""
        
        # Format the date of birth for verification
        dob_formatted = patient.date_of_birth.strftime("%B %d, %Y") if patient.date_of_birth else "date of birth on file"
        
        # Base variables
        variables = {
            "patient_name": patient.full_name,
            "expected_dob": dob_formatted,
            "primary_diagnosis": patient.primary_diagnosis or "Not specified",
            "protocol_type": patient.protocol_type.value if patient.protocol_type else "general"
        }
        
        # Add protocol-specific questions
        protocol_questions = ""
        if protocol and protocol.questions:
            protocol_questions += "ASK THESE QUESTIONS IN ORDER:\n"
            
            for i, question in enumerate(protocol.questions, 1):
                question_text = question.get('text', '')
                question_type = question.get('type', 'text')
                
                protocol_questions += f"{i}. {question_text}"
                
                if question_type == 'numeric':
                    min_val = question.get('min_value', 0)
                    max_val = question.get('max_value', 10)
                    protocol_questions += f" (Scale {min_val}-{max_val})"
                elif question_type == 'choice':
                    choices = question.get('choices', [])
                    if choices:
                        protocol_questions += f" (Options: {', '.join(choices)})"
                
                protocol_questions += "\n"
        
        variables["protocol_questions"] = protocol_questions
        
        # Add threshold monitoring and escalation logic with specific time-based responses
        escalation_logic = ""
        if protocol and protocol.decision_tree:
            escalation_logic += "IMPORTANT - ESCALATION LOGIC:\n"
            escalation_logic += "After completing ALL protocol questions, evaluate the responses against these thresholds:\n\n"
            
            # Build list of urgent and moderate conditions from decision tree
            urgent_conditions = []
            moderate_conditions = []
            
            for decision in protocol.decision_tree:
                symptom_type = decision.get('symptom_type', '')
                condition = decision.get('condition', '')
                value = decision.get('value')
                
                # Skip default/stable conditions - those are for normal cases
                if condition == 'default' or symptom_type == 'stable':
                    continue
                
                if condition == 'greater_than' and value is not None:
                    if value >= 7:
                        urgent_conditions.append(f"- {symptom_type} score ≥7")
                    elif value >= 3:
                        moderate_conditions.append(f"- {symptom_type} score 3-6")
                elif condition == 'equals' and value is True:
                    urgent_conditions.append(f"- {symptom_type} is present/true")
            
            # Display the conditions
            if urgent_conditions:
                escalation_logic += "URGENT CONDITIONS (≥7 or critical symptoms):\n"
                for condition in urgent_conditions:
                    escalation_logic += f"{condition}\n"
                escalation_logic += "\n"
            
            if moderate_conditions:
                escalation_logic += "MODERATE CONDITIONS (3-6):\n"
                for condition in moderate_conditions:
                    escalation_logic += f"{condition}\n"
                escalation_logic += "\n"
            
            escalation_logic += "ESCALATION DECISION PROCESS:\n"
            escalation_logic += "1. Check if ANY urgent condition is met (score ≥7 or critical symptom present)\n"
            escalation_logic += "   → If YES: Say 'I'll arrange for a nurse to ring you in 10 minutes to discuss your symptoms.'\n\n"
            escalation_logic += "2. If no urgent conditions, check if ANY moderate condition is met (score 3-6)\n"
            escalation_logic += "   → If YES: Say 'I'll arrange for a nurse to ring you back in an hour.'\n\n"
            escalation_logic += "3. If no urgent or moderate conditions are met (all scores <3)\n"
            escalation_logic += "   → Say 'I'm hoping you will feel better. Let me schedule your next check-in.'\n"
        
        variables["escalation_logic"] = escalation_logic
        
        return variables
    
    def configure_agent_for_patient(self, agent_id: str, patient_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Prepare patient-specific dynamic variables for Retell AI call"""
        try:
            # Get patient and protocol
            patient = db.session.query(Patient).filter_by(id=patient_id).first()
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False, None
                
            protocol = self.get_patient_protocol(patient_id)
            if not protocol:
                logger.error(f"No protocol found for patient {patient_id}")
                return False, None
            
            # Prepare dynamic variables for call injection
            dynamic_variables = self.prepare_dynamic_variables(patient, protocol)
            
            logger.info(f"Successfully prepared dynamic variables for patient {patient_id} with {protocol.protocol_type.value} protocol")
            logger.debug(f"Dynamic variables: {dynamic_variables}")
            
            return True, dynamic_variables
                
        except Exception as e:
            logger.error(f"Error preparing dynamic variables for patient {patient_id}: {e}")
            return False, None
    
    def update_agent_with_template(self, agent_id: str = None) -> bool:
        """One-time method to update base agent with template-based prompt"""
        try:
            # Use default agent if none specified
            if not agent_id:
                agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
                if not agent_id:
                    logger.error("No agent ID provided and RETELLAI_REMOTE_AGENT_ID not set")
                    return False
            
            # Get template prompt
            template_prompt = self.generate_template_prompt()
            
            # Get current agent configuration
            agent_url = f"{self.base_url}/get-agent/{agent_id}"
            response = requests.get(agent_url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10)
            response.raise_for_status()
            
            agent_data = response.json()
            current_llm_id = agent_data.get("response_engine", {}).get("llm_id")
            
            # Update the LLM with template prompt
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            llm_update_url = f"{self.base_url}/update-retell-llm/{current_llm_id}"
            llm_data = {"general_prompt": template_prompt}
            
            llm_response = requests.patch(llm_update_url, json=llm_data, headers=headers, timeout=10)
            llm_response.raise_for_status()
            
            logger.info(f"Updated agent {agent_id} with template-based prompt")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update agent with template: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            return False
    
    def prepare_agent_for_call(self, patient_id: int, agent_id: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Prepare dynamic variables for call (does not initiate call)"""
        try:
            # Use default agent if none specified (for logging purposes)
            if not agent_id:
                agent_id = os.getenv("RETELLAI_REMOTE_AGENT_ID")
                if not agent_id:
                    logger.error("No agent ID provided and RETELLAI_REMOTE_AGENT_ID not set")
                    return False, None
            
            # Prepare dynamic variables for call injection
            configured, dynamic_variables = self.configure_agent_for_patient(agent_id, patient_id)
            if not configured:
                return False, None
            
            patient = db.session.query(Patient).filter_by(id=patient_id).first()
            logger.info(f"Dynamic variables prepared for agent {agent_id} with DOB verification protocol for {patient.full_name}")
            logger.info("Dynamic variables ready for call initiation with DOB verification enabled")
            
            return True, dynamic_variables
            
        except Exception as e:
            logger.error(f"Error preparing dynamic variables for patient {patient_id}: {e}")
            return False, None


def create_protocol_injection_service() -> ProtocolInjectionService:
    """Factory function to create protocol injection service"""
    return ProtocolInjectionService()