#!/usr/bin/env python3
"""
Protocol Ingest Script for SteadywellOS
This script processes protocol PDF files and creates protocol entries in the database.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# Add the parent directory to sys.path to import src modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Import our custom Anthropic client wrapper
from src.services.anthropic_client import get_anthropic_client

# Import src modules
from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import ProtocolType

# Import functions from rag_service instead of non-existent RAGService class
from src.services.rag_service import get_anthropic_client

# Protocol definitions for key conditions
PROTOCOL_DEFINITIONS = {
    "cancer": {
        "name": "Cancer Palliative Care Protocol",
        "description": "Assessment and management protocol for patients with advanced cancer, focusing on pain, nausea, fatigue, and emotional symptoms.",
        "protocol_type": ProtocolType.CANCER,
        "version": "1.0.0",
    },
    "heart_failure": {
        "name": "Heart Failure Protocol",
        "description": "Protocol for managing patients with advanced heart failure, addressing dyspnea, edema, activity tolerance, and medication adherence.",
        "protocol_type": ProtocolType.HEART_FAILURE,
        "version": "1.0.0",
    },
    "copd": {
        "name": "COPD Protocol",
        "description": "Protocol for patients with advanced COPD, focusing on respiratory symptoms, oxygen use, breathlessness, and breathing techniques.",
        "protocol_type": ProtocolType.COPD,
        "version": "1.0.0",
    },
}


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from {pdf_path}...")

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    text_content = ""
    for page in pages:
        text_content += page.page_content + "\n\n"

    return text_content


def chunk_text(text):
    """Split text into manageable chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,
        chunk_overlap=200,
        length_function=len,
    )
    return text_splitter.split_text(text)


def create_questions_for_protocol(protocol_type, client):
    """Create standardized questions for a protocol type."""

    system_prompt = """
    You are a specialized palliative care protocol designer. Your task is to create a structured set of assessment questions for a telephone triage protocol.
    
    The questions should:
    1. Be organized into logical categories or body systems
    2. Focus on symptom severity and impact on daily life
    3. Include both primary and follow-up questions
    4. Use numeric scales (0-10) for severity when appropriate
    5. Be clearly worded for telephone assessment
    
    Output format must be a valid JSON array with questions in this structure:
    [
      {
        "id": "string identifier (e.g., 'pain_severity')",
        "text": "The question text",
        "type": "one of: numeric, text, boolean, choice",
        "required": true/false,
        "symptom_type": "category of symptom (e.g., 'pain', 'dyspnea')",
        "min_value": minimum value for numeric questions,
        "max_value": maximum value for numeric questions,
        "choices": ["array", "of", "choices"] for choice questions,
        "category": "grouping category (e.g., 'Physical Symptoms')"
      }
    ]
    
    Include approximately 15-20 questions that cover the most important aspects of assessment.
    """

    if protocol_type == ProtocolType.CANCER:
        user_prompt = """
        Create a set of telephone triage assessment questions for palliative care patients with advanced cancer. 
        
        Focus on these key areas:
        - Pain (location, severity, quality, relief measures)
        - Nausea and vomiting
        - Constipation and bowel function
        - Fatigue and energy levels
        - Appetite and weight changes
        - Psychological symptoms (anxiety, depression)
        - Medication side effects
        - Support system and caregiver burden
        
        Each question should help assess if the patient needs immediate intervention, a change in care plan, or reassurance.
        Format the output as described in the system prompt.
        """

    elif protocol_type == ProtocolType.HEART_FAILURE:
        user_prompt = """
        Create a set of telephone triage assessment questions for palliative care patients with advanced heart failure.
        
        Focus on these key areas:
        - Breathlessness (at rest, with activity)
        - Edema (location, severity, changes)
        - Chest pain or discomfort
        - Fatigue and activity tolerance
        - Sleep quality (positioning, orthopnea)
        - Medication adherence and side effects
        - Weight fluctuations
        - Appetite and dietary adherence
        - Psychological wellbeing
        
        Each question should help assess if the patient needs immediate intervention, a change in care plan, or reassurance.
        Format the output as described in the system prompt.
        """

    elif protocol_type == ProtocolType.COPD:
        user_prompt = """
        Create a set of telephone triage assessment questions for palliative care patients with advanced COPD.
        
        Focus on these key areas:
        - Breathlessness (severity, triggers, patterns)
        - Cough (frequency, productivity, color of sputum)
        - Oxygen use and effectiveness
        - Activity tolerance and limitations
        - Sleep quality and positioning
        - Signs of respiratory infection
        - Medication use and inhaler technique
        - Anxiety and panic related to breathing
        - Support needs for activities of daily living
        
        Each question should help assess if the patient needs immediate intervention, a change in care plan, or reassurance.
        Format the output as described in the system prompt.
        """

    print(f"Generating questions for {protocol_type.value} protocol...")

    # Get response using our custom wrapper
    content = client.call_model(
        model="claude-3-sonnet-20240229",  # More widely available model
        system=system_prompt,
        max_tokens=4000,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract JSON from the response
    try:
        # Find JSON array in content - sometimes Claude adds explanatory text
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            questions = json.loads(json_content)
            return questions
        else:
            print("Could not find valid JSON array in response")
            print(content)
            return []
    except Exception as e:
        print(f"Error parsing questions JSON: {e}")
        print(content)
        return []


def create_interventions_for_protocol(protocol_type, client):
    """Create standardized interventions for a protocol type."""

    system_prompt = """
    You are a specialized palliative care protocol designer. Your task is to create a structured set of interventions for a palliative care protocol.
    
    The interventions should:
    1. Address common symptoms and concerns
    2. Include both pharmacological and non-pharmacological approaches
    3. Be specific and actionable by telephone
    4. Include guidance on when to escalate care
    5. Be evidence-based for palliative care
    
    Output format must be a valid JSON array with interventions in this structure:
    [
      {
        "id": "string identifier (e.g., 'severe_pain_intervention')",
        "title": "Short title for the intervention",
        "description": "Detailed description of the intervention",
        "symptom_type": "category of symptom (e.g., 'pain', 'dyspnea')",
        "severity_threshold": numeric value indicating when to use this intervention,
        "priority": "one of: low, medium, high, urgent",
        "instructions": "Specific instructions for the patient or caregiver"
      }
    ]
    
    Include approximately 15-20 interventions covering the most important aspects of care.
    """

    if protocol_type == ProtocolType.CANCER:
        user_prompt = """
        Create a set of interventions for palliative care patients with advanced cancer.
        
        Focus on these key areas:
        - Pain management (breakthrough, persistent, neuropathic)
        - Nausea and vomiting control
        - Constipation prevention and management
        - Fatigue management and energy conservation
        - Psychological support for anxiety and depression
        - Medication side effect management
        - Caregiver support and education
        - Emergency symptom management
        
        Include interventions with varying priorities from routine management to urgent intervention.
        Format the output as described in the system prompt.
        """

    elif protocol_type == ProtocolType.HEART_FAILURE:
        user_prompt = """
        Create a set of interventions for palliative care patients with advanced heart failure.
        
        Focus on these key areas:
        - Management of breathlessness (positioning, oxygen, medications)
        - Edema management (elevation, compression, diuretic adjustment)
        - Activity and exercise recommendations
        - Diet and fluid management
        - Sleep positioning and quality improvement
        - Psychological support for disease burden
        - Medication adherence support
        - When to seek emergency care
        
        Include interventions with varying priorities from routine management to urgent intervention.
        Format the output as described in the system prompt.
        """

    elif protocol_type == ProtocolType.COPD:
        user_prompt = """
        Create a set of interventions for palliative care patients with advanced COPD.
        
        Focus on these key areas:
        - Breathing techniques (pursed-lip, diaphragmatic)
        - Positioning to ease breathing
        - Energy conservation strategies
        - Oxygen therapy optimization
        - Anxiety management during breathlessness
        - Secretion clearance techniques
        - Inhaler technique optimization
        - Recognition and early management of exacerbations
        - Environmental modifications
        
        Include interventions with varying priorities from routine management to urgent intervention.
        Format the output as described in the system prompt.
        """

    print(f"Generating interventions for {protocol_type.value} protocol...")

    # Get response using our custom wrapper
    content = client.call_model(
        model="claude-3-sonnet-20240229",  # More widely available model
        system=system_prompt,
        max_tokens=4000,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract JSON from the response
    try:
        # Find JSON array in content
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            interventions = json.loads(json_content)
            return interventions
        else:
            print("Could not find valid JSON array in response")
            print(content)
            return []
    except Exception as e:
        print(f"Error parsing interventions JSON: {e}")
        print(content)
        return []


def create_decision_tree(protocol_type, questions, interventions, client):
    """Create a decision tree based on questions and interventions."""

    system_prompt = """
    You are a specialized palliative care protocol designer. Your task is to create a decision tree that connects assessment questions to appropriate interventions.
    
    The decision tree should:
    1. Use logical if-then structures based on symptom severity
    2. Consider combinations of symptoms where appropriate
    3. Route to the correct intervention based on assessment responses
    4. Include appropriate escalation pathways
    
    Output format must be a valid JSON array with decision nodes in this structure:
    [
      {
        "id": "string identifier (e.g., 'node_pain_severe')",
        "symptom_type": "category of symptom (e.g., 'pain', 'dyspnea')",
        "condition": "logical condition (e.g., '>=', '<=', '==')",
        "value": numeric or string value to compare against,
        "next_node_id": "ID of the next decision node if condition is met (or null)",
        "intervention_ids": ["array", "of", "intervention", "ids"] if interventions should be triggered
      }
    ]
    
    Create approximately 15-20 decision nodes that cover the most important symptom pathways.
    """

    # Prepare context with questions and interventions
    questions_json = json.dumps(questions, indent=2)
    interventions_json = json.dumps(interventions, indent=2)

    user_prompt = f"""
    Create a decision tree for the {protocol_type.value} protocol that connects these assessment questions to appropriate interventions.
    
    The decision tree should determine when to trigger specific interventions based on assessment responses, especially focusing on:
    1. Severe symptoms that need urgent intervention
    2. Moderate symptoms that need attention
    3. Mild symptoms that need monitoring
    4. Combinations of symptoms that together indicate higher risk
    
    Here are the assessment questions available:
    ```
    {questions_json}
    ```
    
    Here are the interventions available:
    ```
    {interventions_json}
    ```
    
    Create decision nodes that would appropriately link these questions to interventions based on patient responses. The decision tree should cover all major symptom pathways and ensure that urgent issues are prioritized appropriately.
    
    Format the output as described in the system prompt.
    """

    print(f"Generating decision tree for {protocol_type.value} protocol...")

    # Get response using our custom wrapper
    content = client.call_model(
        model="claude-3-sonnet-20240229",  # More widely available model
        system=system_prompt,
        max_tokens=4000,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract JSON from the response
    try:
        # Find JSON array in content
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
            decision_tree = json.loads(json_content)
            return decision_tree
        else:
            print("Could not find valid JSON array in response")
            print(content)
            return []
    except Exception as e:
        print(f"Error parsing decision tree JSON: {e}")
        print(content)
        return []


def create_protocol(protocol_type, anthropic_client):
    """Create a full protocol entry of the specified type."""

    protocol_def = next(
        (
            p
            for p in PROTOCOL_DEFINITIONS.values()
            if p["protocol_type"] == protocol_type
        ),
        None,
    )

    if not protocol_def:
        print(f"No protocol definition found for {protocol_type}")
        return None

    print(f"Creating {protocol_type.value} protocol...")

    # Create protocol components
    questions = create_questions_for_protocol(protocol_type, anthropic_client)
    if not questions:
        print(f"Failed to create questions for {protocol_type.value}")
        return None

    interventions = create_interventions_for_protocol(protocol_type, anthropic_client)
    if not interventions:
        print(f"Failed to create interventions for {protocol_type.value}")
        return None

    decision_tree = create_decision_tree(
        protocol_type, questions, interventions, anthropic_client
    )
    if not decision_tree:
        print(f"Failed to create decision tree for {protocol_type.value}")
        return None

    # Create protocol object
    protocol = Protocol(
        name=protocol_def["name"],
        description=protocol_def["description"],
        protocol_type=protocol_type,
        version=protocol_def["version"],
        questions=questions,
        decision_tree=decision_tree,
        interventions=interventions,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    return protocol


def save_protocol(protocol):
    """Save protocol to database."""
    try:
        db.session.add(protocol)
        db.session.commit()
        print(f"Protocol saved: {protocol.name} (ID: {protocol.id})")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error saving protocol: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Ingest protocol PDFs and create database entries"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="../data",
        help="Directory containing protocol PDF files",
    )
    parser.add_argument(
        "--protocol-type",
        type=str,
        choices=["cancer", "heart_failure", "copd", "all"],
        default="all",
        help="Protocol type to create",
    )
    args = parser.parse_args()

    # Initialize app context
    app = create_app()
    with app.app_context():
        # Get Anthropic API key from app config
        anthropic_api_key = app.config.get("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            print("ERROR: ANTHROPIC_API_KEY not found in app configuration")
            sys.exit(1)

        # Initialize our custom Anthropic client wrapper
        try:
            client = get_anthropic_client(anthropic_api_key)
        except Exception as e:
            print(f"ERROR: Failed to initialize Anthropic client: {e}")
            sys.exit(1)

        if args.protocol_type == "all":
            protocol_types = [
                ProtocolType.CANCER,
                ProtocolType.HEART_FAILURE,
                ProtocolType.COPD,
            ]
        else:
            protocol_types = [ProtocolType(args.protocol_type)]

        for protocol_type in protocol_types:
            # Check if protocol already exists
            existing = Protocol.query.filter_by(
                protocol_type=protocol_type,
                version=PROTOCOL_DEFINITIONS[protocol_type.value]["version"],
            ).first()

            if existing:
                print(
                    f"Protocol {protocol_type.value} v{existing.version} already exists (ID: {existing.id})"
                )
                continue

            # Create and save protocol
            protocol = create_protocol(protocol_type, client)
            if protocol:
                save_protocol(protocol)
            else:
                print(f"Failed to create {protocol_type.value} protocol")


if __name__ == "__main__":
    main()
