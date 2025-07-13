"""Retell AI integration service with knowledge base enhancement."""

import json
from typing import Dict, Any, Optional
from flask import current_app

from src.core.knowledge_service import get_knowledge_service
from src.core.anthropic_client import get_anthropic_client
from src.models.patient import Patient
from src.models.protocol import Protocol
from src.utils.logger import get_logger

logger = get_logger()


class RetellKnowledgeIntegration:
    """Service for integrating knowledge base with Retell AI calls."""
    
    @staticmethod
    def generate_knowledge_enhanced_prompt(
        patient: Patient,
        protocol: Protocol,
        call_context: Dict[str, Any] = None
    ) -> str:
        """Generate a knowledge-enhanced prompt for Retell AI agents."""
        try:
            # Build search query from patient context
            search_query = f"{patient.primary_diagnosis} {patient.protocol_type.value} telephone assessment"
            
            # Get relevant knowledge
            knowledge_service = get_knowledge_service()
            if not knowledge_service or not knowledge_service.embeddings:
                logger.warning("Knowledge service not available, using basic prompt")
                return RetellKnowledgeIntegration._generate_basic_prompt(patient, protocol)
            
            # Search for relevant knowledge
            relevant_docs = knowledge_service.search(search_query, k=2, 
                                                   category_filter=patient.protocol_type.value.lower())
            
            if not relevant_docs:
                logger.info("No relevant knowledge found, using basic prompt")
                return RetellKnowledgeIntegration._generate_basic_prompt(patient, protocol)
            
            # Build knowledge-enhanced prompt
            knowledge_context = ""
            for doc in relevant_docs:
                metadata = doc["metadata"]
                content = doc["content"]
                knowledge_context += f"""
Reference ({metadata.get('title', 'Clinical Knowledge')}):
{content[:500]}...

"""
            
            # Create comprehensive prompt with knowledge integration
            enhanced_prompt = f"""
You are a compassionate palliative care specialist conducting a telephone assessment. You have access to evidence-based clinical knowledge to guide your conversation.

PATIENT INFORMATION:
- Name: {patient.full_name}
- Primary Diagnosis: {patient.primary_diagnosis}
- Protocol Type: {patient.protocol_type.value}
- Age: {patient.age}

CLINICAL KNOWLEDGE REFERENCES:
{knowledge_context}

ASSESSMENT APPROACH:
1. Begin with a warm, empathetic greeting
2. Ask about current symptoms using the protocol questions
3. Listen actively and respond with clinical knowledge when appropriate
4. Provide reassurance and practical guidance based on the references
5. Determine if urgent medical attention is needed
6. Schedule appropriate follow-up

KEY PROTOCOL QUESTIONS:
{json.dumps([q.get('text', '') for q in protocol.questions[:5]], indent=2)}

CONVERSATION GUIDELINES:
- Use patient-friendly language, avoid medical jargon
- Acknowledge concerns with empathy
- Base recommendations on the clinical references provided
- Suggest when to contact their healthcare team
- Keep responses concise but thorough
- Always prioritize patient safety

Remember: You are conducting a supportive clinical assessment. Use the knowledge references to provide evidence-based guidance while maintaining a caring, professional tone.
"""
            
            logger.info(f"Generated knowledge-enhanced prompt for {patient.full_name}")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error generating knowledge-enhanced prompt: {e}")
            return RetellKnowledgeIntegration._generate_basic_prompt(patient, protocol)
    
    @staticmethod
    def _generate_basic_prompt(patient: Patient, protocol: Protocol) -> str:
        """Generate basic prompt without knowledge enhancement."""
        return f"""
You are a palliative care specialist conducting a telephone assessment.

PATIENT: {patient.full_name}
DIAGNOSIS: {patient.primary_diagnosis}
PROTOCOL: {patient.protocol_type.value}

Conduct a compassionate assessment focusing on:
1. Current symptoms and their severity
2. Pain management effectiveness
3. Emotional wellbeing
4. Support needs

Key questions to cover:
{json.dumps([q.get('text', '') for q in protocol.questions[:3]], indent=2)}

Be empathetic, use clear language, and provide appropriate guidance.
"""
    
    @staticmethod
    def process_call_transcript_with_knowledge(
        transcript: str, 
        patient: Patient, 
        protocol: Protocol
    ) -> Dict[str, Any]:
        """Process call transcript with knowledge base enhancement."""
        try:
            # Extract key information from transcript
            key_symptoms = RetellKnowledgeIntegration._extract_symptoms_from_transcript(transcript)
            
            if not key_symptoms:
                logger.info("No symptoms extracted from transcript")
                return {"error": "Unable to extract symptom information from transcript"}
            
            # Search for relevant knowledge based on symptoms
            search_query = f"{patient.primary_diagnosis} " + " ".join(key_symptoms)
            
            knowledge_service = get_knowledge_service()
            if knowledge_service and knowledge_service.embeddings:
                # Get knowledge-enhanced analysis
                patient_context = {
                    "primary_diagnosis": patient.primary_diagnosis,
                    "protocol_type": patient.protocol_type.value,
                    "age": patient.age,
                    "symptoms": key_symptoms
                }
                
                analysis = knowledge_service.get_enhanced_guidance(
                    f"Analyze this patient call: {transcript[:500]}", 
                    patient_context
                )
                
                return {
                    "transcript_analysis": analysis,
                    "key_symptoms": key_symptoms,
                    "knowledge_enhanced": True,
                    "search_query": search_query
                }
            else:
                # Fallback to basic analysis
                return RetellKnowledgeIntegration._basic_transcript_analysis(transcript, patient)
                
        except Exception as e:
            logger.error(f"Error processing transcript with knowledge: {e}")
            return {"error": f"Error analyzing transcript: {str(e)}"}
    
    @staticmethod
    def _extract_symptoms_from_transcript(transcript: str) -> list:
        """Extract symptom keywords from transcript."""
        # Simple keyword extraction for common symptoms
        symptom_keywords = [
            "pain", "hurt", "ache", "sore",
            "nausea", "sick", "vomit", "queasy",
            "tired", "fatigue", "exhausted", "weak",
            "breath", "breathing", "short of breath", "dyspnea",
            "swelling", "edema", "bloated",
            "cough", "coughing", "sputum",
            "anxiety", "worried", "scared", "nervous",
            "sleep", "insomnia", "can't sleep"
        ]
        
        transcript_lower = transcript.lower()
        found_symptoms = []
        
        for symptom in symptom_keywords:
            if symptom in transcript_lower:
                found_symptoms.append(symptom)
        
        return list(set(found_symptoms))  # Remove duplicates
    
    @staticmethod
    def _basic_transcript_analysis(transcript: str, patient: Patient) -> Dict[str, Any]:
        """Basic transcript analysis without knowledge enhancement."""
        try:
            # Use Anthropic for basic analysis
            anthropic_api_key = current_app.config.get("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                return {"error": "AI analysis not available"}
            
            client = get_anthropic_client(anthropic_api_key)
            
            prompt = f"""
Analyze this palliative care phone call transcript for patient with {patient.primary_diagnosis}:

TRANSCRIPT:
{transcript}

Extract:
1. Key symptoms mentioned and their severity
2. Patient concerns
3. Medication issues
4. Follow-up needs
5. Urgency level (low/medium/high)

Provide concise, actionable analysis.
"""
            
            analysis = client.call_model(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            
            return {
                "transcript_analysis": analysis,
                "knowledge_enhanced": False,
                "method": "basic_ai_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error in basic transcript analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    @staticmethod
    def enhance_retell_agent_config(
        base_config: Dict[str, Any],
        patient: Patient,
        protocol: Protocol
    ) -> Dict[str, Any]:
        """Enhance Retell AI agent configuration with knowledge-based prompts."""
        try:
            # Generate knowledge-enhanced prompt
            enhanced_prompt = RetellKnowledgeIntegration.generate_knowledge_enhanced_prompt(
                patient, protocol
            )
            
            # Update agent configuration
            enhanced_config = base_config.copy()
            
            # Add enhanced prompt as system message or agent instructions
            if "response_engine" in enhanced_config:
                # For custom LLM configurations
                enhanced_config["response_engine"]["system_prompt"] = enhanced_prompt
            else:
                # Add as general instruction
                enhanced_config["instructions"] = enhanced_prompt
            
            # Add dynamic variables for patient context
            enhanced_config["retell_llm_dynamic_variables"] = {
                "patient_name": patient.full_name,
                "primary_diagnosis": patient.primary_diagnosis,
                "protocol_type": patient.protocol_type.value,
                "age": str(patient.age),
                "enhanced_knowledge": "true"
            }
            
            # Add knowledge base context tags
            enhanced_config["boosted_keywords"] = [
                patient.primary_diagnosis.lower(),
                patient.protocol_type.value.lower(),
                "palliative", "symptom", "pain", "comfort"
            ]
            
            logger.info(f"Enhanced Retell agent config for {patient.full_name}")
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Error enhancing agent config: {e}")
            return base_config  # Return original config on error
    
    @staticmethod
    def get_knowledge_insights_for_call(
        patient: Patient,
        call_summary: str
    ) -> Dict[str, Any]:
        """Get knowledge-based insights for a completed call."""
        try:
            # Search for relevant follow-up knowledge
            search_query = f"{patient.primary_diagnosis} follow-up care {call_summary[:100]}"
            
            knowledge_service = get_knowledge_service()
            if not knowledge_service or not knowledge_service.embeddings:
                return {"insights": "Knowledge service not available"}
            
            # Get relevant knowledge for follow-up
            relevant_docs = knowledge_service.search(search_query, k=2)
            
            if not relevant_docs:
                return {"insights": "No specific follow-up knowledge found"}
            
            # Generate insights based on knowledge
            insights = []
            for doc in relevant_docs:
                insight = {
                    "title": doc["metadata"].get("title", "Clinical Guidance"),
                    "relevance": doc["relevance"],
                    "content": doc["content"][:300] + "..." if len(doc["content"]) > 300 else doc["content"],
                    "source": doc["metadata"].get("source", "Knowledge Base")
                }
                insights.append(insight)
            
            return {
                "insights": insights,
                "search_query": search_query,
                "total_references": len(insights)
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge insights: {e}")
            return {"error": f"Failed to get insights: {str(e)}"}


# Convenience functions for easy integration
def enhance_retell_call_config(patient: Patient, protocol: Protocol, base_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to enhance Retell call configuration."""
    if base_config is None:
        base_config = {}
    
    return RetellKnowledgeIntegration.enhance_retell_agent_config(base_config, patient, protocol)


def process_retell_webhook_with_knowledge(webhook_data: Dict[str, Any], patient: Patient, protocol: Protocol) -> Dict[str, Any]:
    """Convenience function to process Retell webhook data with knowledge enhancement."""
    transcript = webhook_data.get("transcript", "")
    
    if not transcript:
        return {"error": "No transcript available in webhook data"}
    
    return RetellKnowledgeIntegration.process_call_transcript_with_knowledge(transcript, patient, protocol)