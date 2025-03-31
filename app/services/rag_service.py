"""RAG (Retrieval-Augmented Generation) service for protocol guidance"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import current_app

from app.models.patient import Patient
from app.models.protocol import Protocol
from app.services.anthropic_client import get_anthropic_client

def process_assessment(patient: Patient, protocol: Protocol, symptoms: Dict[str, float], responses: Dict[str, Any]) -> str:
    """Generate AI guidance for a patient assessment using RAG"""
    try:
        # Build prompt context
        context = {
            "patient": {
                "id": patient.id,
                "name": patient.full_name,
                "age": patient.age,
                "gender": patient.gender.value,
                "primary_diagnosis": patient.primary_diagnosis,
                "secondary_diagnoses": patient.secondary_diagnoses,
                "protocol_type": patient.protocol_type.value
            },
            "protocol": {
                "name": protocol.name,
                "type": protocol.protocol_type.value,
                "version": protocol.version
            },
            "symptoms": symptoms,
            "responses": responses
        }
        
        # Get protocol details as reference
        protocol_json = {
            "questions": protocol.questions,
            "decision_tree": protocol.decision_tree,
            "interventions": protocol.interventions
        }
        
        # Build the prompt
        prompt = f"""
        You are a palliative care specialist assistant. You are helping analyze a patient assessment for a patient with {patient.primary_diagnosis}.
        
        PATIENT INFORMATION:
        - Name: {patient.full_name}
        - Age: {patient.age}
        - Gender: {patient.gender.value}
        - Primary Diagnosis: {patient.primary_diagnosis}
        - Secondary Diagnoses: {patient.secondary_diagnoses or 'None documented'}
        - Protocol Type: {patient.protocol_type.value}
        
        ASSESSMENT FINDINGS:
        {json.dumps(symptoms, indent=2)}
        
        RAW RESPONSES:
        {json.dumps(responses, indent=2)}
        
        PROTOCOL REFERENCE:
        {json.dumps(protocol_json, indent=2)}
        
        Based on the {protocol.protocol_type.value} palliative care protocol and the assessment findings, please provide:
        
        1. A clinical interpretation of the patient's symptoms
        2. Specific recommendations for symptom management
        3. Any follow-up actions that should be considered
        4. Educational points for the patient or caregiver
        
        Please be concise and focus on practical, evidence-based guidance. Your response should be in a clinical note format suitable for documentation.
        """
        
        # Call Anthropic API using our custom wrapper
        client = get_anthropic_client(current_app.config.get('ANTHROPIC_API_KEY'))
        return client.call_model(
            model="claude-3-sonnet-20240229",  # More widely available model
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in RAG service: {str(e)}")
        return f"Error generating guidance: {str(e)}"

def generate_call_script(patient: Patient, protocol: Protocol, call_type: str) -> str:
    """Generate a call script for a scheduled call based on patient and protocol"""
    try:
        # Build prompt context
        context = {
            "patient": {
                "name": patient.full_name,
                "age": patient.age,
                "gender": patient.gender.value,
                "primary_diagnosis": patient.primary_diagnosis,
                "protocol_type": patient.protocol_type.value
            },
            "protocol": {
                "name": protocol.name,
                "type": protocol.protocol_type.value,
                "questions": protocol.questions
            },
            "call_type": call_type
        }
        
        # Build the prompt
        prompt = f"""
        You are a palliative care nurse specialist. You're preparing a script for a telephone assessment call with a patient.
        
        PATIENT INFORMATION:
        - Name: {patient.full_name}
        - Age: {patient.age}
        - Gender: {patient.gender.value}
        - Primary Diagnosis: {patient.primary_diagnosis}
        - Protocol Type: {patient.protocol_type.value}
        
        CALL TYPE: {call_type}
        
        PROTOCOL QUESTIONS:
        {json.dumps(protocol.questions, indent=2)}
        
        Please create a conversational script for this call that covers:
        
        1. An appropriate introduction and consent to proceed
        2. Assessment questions based on the protocol, phrased in a patient-friendly way
        3. Clear instructions for symptom rating scales when needed
        4. Appropriate transitions between topic areas
        5. A supportive closing with next steps
        
        The script should be empathetic, clear, and follow best practices for palliative care telephone assessment.
        """
        
        # Call Anthropic API using our custom wrapper
        client = get_anthropic_client(current_app.config.get('ANTHROPIC_API_KEY'))
        return client.call_model(
            model="claude-3-sonnet-20240229",  # More widely available model
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating call script: {str(e)}")
        return f"Error generating call script: {str(e)}"

def analyze_call_transcript(transcript: str, patient: Patient, protocol: Protocol) -> Dict[str, Any]:
    """Analyze a call transcript to extract symptoms, concerns, and suggested actions"""
    try:
        # Build the prompt
        prompt = f"""
        You are a palliative care specialist assistant. You are analyzing a transcript from a telephone assessment with a patient.
        
        PATIENT INFORMATION:
        - Primary Diagnosis: {patient.primary_diagnosis}
        - Protocol Type: {patient.protocol_type.value}
        
        CALL TRANSCRIPT:
        {transcript}
        
        Please analyze this transcript and extract the following information:
        
        1. Symptoms mentioned with severity (on a 0-10 scale if available)
        2. Key concerns expressed by the patient
        3. Any medication issues mentioned
        4. Psychosocial factors discussed
        5. Recommended follow-up actions
        
        Format your response as a structured JSON object with these categories.
        """
        
        # Call Anthropic API using our custom wrapper
        client = get_anthropic_client(current_app.config.get('ANTHROPIC_API_KEY'))
        content = client.call_model(
            model="claude-3-sonnet-20240229",  # More widely available model
            max_tokens=1200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Try to parse response as JSON
        try:
            # Extract JSON from response if it's wrapped in markdown code block
            if "```json" in content and "```" in content.split("```json", 1)[1]:
                json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in content and "```" in content.split("```", 1)[1]:
                json_str = content.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                json_str = content
                
            result = json.loads(json_str)
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            result = {"analysis": content}
        
        return result
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing transcript: {str(e)}")
        return {"error": f"Error analyzing transcript: {str(e)}"}
