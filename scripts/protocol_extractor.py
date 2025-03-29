#!/usr/bin/env python3
"""
Protocol Extractor for SteadywellOS
This script extracts protocol data from PDF documentation and converts it into the JSON format
required by the SteadywellOS platform.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF is not installed. Install it with: pip install pymupdf")
    sys.exit(1)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_protocol_from_text(text, protocol_type):
    """Parse protocol data from extracted text"""
    # This is a placeholder implementation
    # In a real implementation, you would use NLP or more sophisticated parsing
    # to extract structured data from the text
    
    # Basic structure for protocol data
    protocol_data = {
        "name": f"{protocol_type.title()} Palliative Care Protocol",
        "description": f"Protocol for managing symptoms in patients with advanced {protocol_type}",
        "protocol_type": protocol_type.lower(),
        "version": "1.0",
        "questions": [],
        "decision_tree": [],
        "interventions": []
    }
    
    # Simple pattern matching for questions
    question_pattern = r"([0-9]+\.\s*)([\w\s,]+\?)"
    questions = re.findall(question_pattern, text)
    
    # Create basic questions
    for i, (_, question_text) in enumerate(questions[:10]):  # Limit to first 10 questions for demo
        question_id = f"q_{i+1}"
        symptom_type = "general"
        
        # Try to determine symptom type from question text
        if "pain" in question_text.lower():
            symptom_type = "pain"
        elif "breath" in question_text.lower() or "dyspnea" in question_text.lower():
            symptom_type = "dyspnea"
        elif "nausea" in question_text.lower():
            symptom_type = "nausea"
        elif "fatigue" in question_text.lower() or "tired" in question_text.lower():
            symptom_type = "fatigue"
        
        # Determine question type
        question_type = "text"
        if "scale" in question_text.lower() or "rate" in question_text.lower():
            question_type = "numeric"
        elif "yes" in question_text.lower() or "no" in question_text.lower():
            question_type = "boolean"
        
        question = {
            "id": question_id,
            "text": question_text.strip(),
            "type": question_type,
            "required": True,
            "symptom_type": symptom_type
        }
        
        if question_type == "numeric":
            question["min_value"] = 0
            question["max_value"] = 10
            
        protocol_data["questions"].append(question)
        
        # Create a basic decision node for numeric questions
        if question_type == "numeric":
            # Severe threshold (>=7)
            severe_node = {
                "id": f"{symptom_type}_severe",
                "symptom_type": symptom_type,
                "condition": ">=7",
                "intervention_ids": [f"{symptom_type}_severe_mgmt"]
            }
            
            # Moderate threshold (>=4)
            moderate_node = {
                "id": f"{symptom_type}_moderate",
                "symptom_type": symptom_type,
                "condition": ">=4",
                "intervention_ids": [f"{symptom_type}_moderate_mgmt"]
            }
            
            protocol_data["decision_tree"].append(severe_node)
            protocol_data["decision_tree"].append(moderate_node)
            
            # Create interventions
            severe_intervention = {
                "id": f"{symptom_type}_severe_mgmt",
                "title": f"Severe {symptom_type.title()} Management",
                "description": f"Urgent management of severe {symptom_type}",
                "symptom_type": symptom_type,
                "severity_threshold": 7
            }
            
            moderate_intervention = {
                "id": f"{symptom_type}_moderate_mgmt",
                "title": f"Moderate {symptom_type.title()} Management",
                "description": f"Management of moderate {symptom_type}",
                "symptom_type": symptom_type,
                "severity_threshold": 4
            }
            
            protocol_data["interventions"].append(severe_intervention)
            protocol_data["interventions"].append(moderate_intervention)
    
    return protocol_data

def save_protocol_json(protocol_data, output_path):
    """Save protocol data as JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(protocol_data, f, indent=2)
    print(f"Protocol saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract protocol data from PDF documentation")
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--type', required=True, choices=['cancer', 'heart_failure', 'copd'], 
                        help='Protocol type to extract')
    parser.add_argument('--output', help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'protocols')
        os.makedirs(output_dir, exist_ok=True)
        args.output = os.path.join(output_dir, f"{args.type}_protocol.json")
    
    # Extract text from PDF
    print(f"Extracting text from {args.pdf_path}...")
    text = extract_text_from_pdf(args.pdf_path)
    
    # Parse protocol data
    print(f"Parsing {args.type} protocol data...")
    protocol_data = parse_protocol_from_text(text, args.type)
    
    # Save as JSON
    save_protocol_json(protocol_data, args.output)
    print("Protocol extraction complete.")

if __name__ == "__main__":
    main()