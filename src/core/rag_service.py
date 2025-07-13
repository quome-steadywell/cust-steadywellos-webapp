"""RAG (Retrieval-Augmented Generation) service for protocol guidance with knowledge base integration"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import current_app

from src.models.patient import Patient
from src.models.protocol import Protocol
from src.core.anthropic_client import get_anthropic_client
from src.core.knowledge_service import get_knowledge_service


def process_assessment(
    patient: Patient,
    protocol: Protocol,
    symptoms: Dict[str, float],
    responses: Dict[str, Any],
) -> str:
    """Generate AI guidance for a patient assessment using RAG with knowledge base integration"""
    try:
        # Build patient context for knowledge search
        patient_context = {
            "primary_diagnosis": patient.primary_diagnosis,
            "protocol_type": patient.protocol_type.value,
            "age": patient.age,
            "symptoms": symptoms
        }
        
        # Generate search query from symptoms and diagnosis
        symptom_list = [f"{symptom}: {score}" for symptom, score in symptoms.items() if score > 5]
        search_query = f"{patient.primary_diagnosis} {patient.protocol_type.value} " + " ".join(symptom_list)
        
        # Get enhanced guidance using knowledge base
        knowledge_service = get_knowledge_service()
        if knowledge_service and knowledge_service.embeddings:
            current_app.logger.info(f"Using knowledge-enhanced guidance for query: {search_query}")
            guidance = knowledge_service.get_enhanced_guidance(search_query, patient_context)
            
            # If knowledge-enhanced guidance is successful, return it
            if guidance and not guidance.startswith("Error"):
                return guidance
            else:
                current_app.logger.warning("Knowledge-enhanced guidance failed, falling back to standard approach")
        
        # Fallback to original approach if knowledge service unavailable
        return _process_assessment_standard(patient, protocol, symptoms, responses)

    except Exception as e:
        current_app.logger.error(f"Error in RAG service: {str(e)}")
        return f"Error generating guidance: {str(e)}"


def _process_assessment_standard(
    patient: Patient,
    protocol: Protocol,
    symptoms: Dict[str, float],
    responses: Dict[str, Any],
) -> str:
    """Standard assessment processing without knowledge base (fallback)"""
    try:
        # Get protocol details as reference
        protocol_json = {
            "questions": protocol.questions,
            "decision_tree": protocol.decision_tree,
            "interventions": protocol.interventions,
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
        client = get_anthropic_client(current_app.config.get("ANTHROPIC_API_KEY"))
        return client.call_model(
            model="claude-3-sonnet-20240229",  # More widely available model
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

    except Exception as e:
        current_app.logger.error(f"Error in standard RAG processing: {str(e)}")
        return f"Error generating guidance: {str(e)}"


def generate_call_script(patient: Patient, protocol: Protocol, call_type: str) -> str:
    """Generate a call script for a scheduled call based on patient and protocol with knowledge enhancement"""
    try:
        # Build patient context for knowledge search
        patient_context = {
            "primary_diagnosis": patient.primary_diagnosis,
            "protocol_type": patient.protocol_type.value,
            "age": patient.age,
        }
        
        # Generate search query for call script guidance
        search_query = f"{patient.primary_diagnosis} {call_type} telephone assessment communication techniques"
        
        # Try knowledge-enhanced approach first
        knowledge_service = get_knowledge_service()
        if knowledge_service and knowledge_service.embeddings:
            current_app.logger.info(f"Using knowledge-enhanced call script generation")
            
            # Get relevant knowledge for communication techniques
            relevant_docs = knowledge_service.search(search_query, k=2)
            
            if relevant_docs:
                # Build enhanced prompt with knowledge
                knowledge_context = ""
                for doc in relevant_docs:
                    knowledge_context += f"\nReference: {doc['content']}\n"
                
                # Enhanced call script generation
                return _generate_enhanced_call_script(patient, protocol, call_type, knowledge_context)
        
        # Fallback to standard approach
        return _generate_call_script_standard(patient, protocol, call_type)

    except Exception as e:
        current_app.logger.error(f"Error generating call script: {str(e)}")
        return f"Error generating call script: {str(e)}"


def _generate_enhanced_call_script(patient: Patient, protocol: Protocol, call_type: str, knowledge_context: str) -> str:
    """Generate enhanced call script with knowledge base context"""
    try:
        prompt = f"""
        You are a palliative care nurse specialist creating a telephone assessment script. Use the provided reference materials to enhance your approach.

        PATIENT INFORMATION:
        - Name: {patient.full_name}
        - Age: {patient.age}
        - Primary Diagnosis: {patient.primary_diagnosis}
        - Protocol Type: {patient.protocol_type.value}

        CALL TYPE: {call_type}

        RELEVANT KNOWLEDGE REFERENCES:
        {knowledge_context}

        PROTOCOL QUESTIONS:
        {json.dumps(protocol.questions, indent=2)}

        Create a conversational script incorporating evidence-based communication techniques from the references. Include:

        1. Empathetic introduction and consent
        2. Assessment questions using patient-friendly language
        3. Clear symptom rating instructions
        4. Smooth transitions between topics
        5. Supportive closing with clear next steps

        Base your communication approach on the reference materials provided.
        """

        client = get_anthropic_client(current_app.config.get("ANTHROPIC_API_KEY"))
        return client.call_model(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

    except Exception as e:
        current_app.logger.error(f"Error generating enhanced call script: {str(e)}")
        return _generate_call_script_standard(patient, protocol, call_type)


def _generate_call_script_standard(patient: Patient, protocol: Protocol, call_type: str) -> str:
    """Generate standard call script without knowledge enhancement"""
    try:
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

        client = get_anthropic_client(current_app.config.get("ANTHROPIC_API_KEY"))
        return client.call_model(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

    except Exception as e:
        current_app.logger.error(f"Error generating standard call script: {str(e)}")
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
        client = get_anthropic_client(current_app.config.get("ANTHROPIC_API_KEY"))
        content = client.call_model(
            model="claude-3-sonnet-20240229",  # More widely available model
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
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
