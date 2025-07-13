"""API endpoints for knowledge base management."""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, Any, List
import json

from src.core.knowledge_service import get_knowledge_service
from src.models.user import User
from src.utils.logger import get_logger

# Create blueprint
knowledge_bp = Blueprint("knowledge", __name__)
logger = get_logger()


@knowledge_bp.route("/search", methods=["POST"])
@jwt_required()
def search_knowledge():
    """Search the knowledge base for relevant information."""
    try:
        data = request.get_json()
        
        if not data or "query" not in data:
            return jsonify({"error": "Query is required"}), 400
        
        query = data["query"]
        k = data.get("k", 5)  # Number of results to return
        category_filter = data.get("category")
        
        # Validate parameters
        if not isinstance(query, str) or len(query.strip()) == 0:
            return jsonify({"error": "Query must be a non-empty string"}), 400
        
        if not isinstance(k, int) or k < 1 or k > 20:
            return jsonify({"error": "k must be an integer between 1 and 20"}), 400
        
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Perform search
        results = knowledge_service.search(query, k=k, category_filter=category_filter)
        
        # Format results for API response
        formatted_results = []
        for result in results:
            formatted_result = {
                "content": result["content"],
                "score": result["score"],
                "relevance": result["relevance"],
                "metadata": {
                    "title": result["metadata"].get("title", ""),
                    "category": result["metadata"].get("category", ""),
                    "tags": result["metadata"].get("tags", []),
                    "source": result["metadata"].get("source", ""),
                    "added_at": result["metadata"].get("added_at", "")
                }
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error in knowledge search: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/guidance", methods=["POST"])
@jwt_required()
def get_enhanced_guidance():
    """Get AI-enhanced guidance using knowledge base retrieval."""
    try:
        data = request.get_json()
        
        if not data or "query" not in data:
            return jsonify({"error": "Query is required"}), 400
        
        query = data["query"]
        patient_context = data.get("patient_context", {})
        
        # Validate parameters
        if not isinstance(query, str) or len(query.strip()) == 0:
            return jsonify({"error": "Query must be a non-empty string"}), 400
        
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Get enhanced guidance
        guidance = knowledge_service.get_enhanced_guidance(query, patient_context)
        
        if guidance.startswith("Error"):
            return jsonify({"error": guidance}), 500
        
        return jsonify({
            "query": query,
            "guidance": guidance,
            "patient_context": patient_context
        })
        
    except Exception as e:
        logger.error(f"Error getting enhanced guidance: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/documents", methods=["POST"])
@jwt_required()
def add_document():
    """Add a new document to the knowledge base."""
    try:
        # Check if user has admin privileges
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["content", "title"]
        for field in required_fields:
            if not data or field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        content = data["content"]
        title = data["title"]
        category = data.get("category", "general")
        tags = data.get("tags", [])
        source = data.get("source", "Manual Entry")
        
        # Validate parameters
        if not isinstance(content, str) or len(content.strip()) == 0:
            return jsonify({"error": "Content must be a non-empty string"}), 400
        
        if not isinstance(title, str) or len(title.strip()) == 0:
            return jsonify({"error": "Title must be a non-empty string"}), 400
        
        if not isinstance(tags, list):
            return jsonify({"error": "Tags must be a list"}), 400
        
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Add document
        success = knowledge_service.add_document(
            content=content,
            title=title,
            category=category,
            tags=tags,
            source=source
        )
        
        if success:
            logger.info(f"Document '{title}' added by user {user.username}")
            return jsonify({
                "message": "Document added successfully",
                "title": title,
                "category": category
            }), 201
        else:
            return jsonify({"error": "Failed to add document"}), 500
        
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_knowledge_stats():
    """Get knowledge base statistics."""
    try:
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Get statistics
        stats = knowledge_service.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/categories", methods=["GET"])
@jwt_required()
def get_categories():
    """Get list of available knowledge categories."""
    try:
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Extract categories from metadata
        categories = set()
        for metadata in knowledge_service.metadata:
            category = metadata.get("category", "uncategorized")
            categories.add(category)
        
        return jsonify({
            "categories": sorted(list(categories))
        })
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_document():
    """Upload and process a document file (PDF or text)."""
    try:
        # Check if user has admin privileges
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get additional metadata from form
        title = request.form.get('title', file.filename)
        category = request.form.get('category', 'general')
        tags_str = request.form.get('tags', '')
        source = request.form.get('source', f'Upload: {file.filename}')
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Validate file type
        allowed_extensions = {'.txt', '.pdf'}
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({"error": "Only .txt and .pdf files are supported"}), 400
        
        try:
            # Read file content
            if file_ext == '.txt':
                content = file.read().decode('utf-8')
            elif file_ext == '.pdf':
                # For now, return error for PDF as we'd need to implement PDF processing
                return jsonify({"error": "PDF processing not yet implemented"}), 400
            
            if not content.strip():
                return jsonify({"error": "File appears to be empty"}), 400
            
            # Get knowledge service
            knowledge_service = get_knowledge_service()
            if not knowledge_service:
                return jsonify({"error": "Knowledge base service not available"}), 503
            
            # Add document
            success = knowledge_service.add_document(
                content=content,
                title=title,
                category=category,
                tags=tags,
                source=source
            )
            
            if success:
                logger.info(f"File '{file.filename}' uploaded and processed by user {user.username}")
                return jsonify({
                    "message": "File uploaded and processed successfully",
                    "filename": file.filename,
                    "title": title,
                    "category": category,
                    "content_length": len(content)
                }), 201
            else:
                return jsonify({"error": "Failed to process uploaded file"}), 500
                
        except UnicodeDecodeError:
            return jsonify({"error": "File encoding not supported. Please use UTF-8 text files."}), 400
        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            return jsonify({"error": "Error processing file"}), 500
        
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@knowledge_bp.route("/test", methods=["POST"])
@jwt_required()
def test_knowledge_retrieval():
    """Test endpoint for knowledge retrieval functionality."""
    try:
        data = request.get_json()
        
        if not data or "scenario" not in data:
            return jsonify({"error": "Test scenario is required"}), 400
        
        scenario = data["scenario"]
        
        # Get knowledge service
        knowledge_service = get_knowledge_service()
        if not knowledge_service:
            return jsonify({"error": "Knowledge base service not available"}), 503
        
        # Define test scenarios
        test_queries = {
            "pain_management": {
                "query": "severe cancer pain management opioid rotation",
                "patient_context": {
                    "primary_diagnosis": "Stage IV Lung Cancer",
                    "protocol_type": "cancer",
                    "age": 65,
                    "symptoms": {"pain": 8, "nausea": 3}
                }
            },
            "heart_failure": {
                "query": "heart failure edema shortness of breath",
                "patient_context": {
                    "primary_diagnosis": "Heart Failure NYHA Class IV",
                    "protocol_type": "heart_failure",
                    "age": 72,
                    "symptoms": {"dyspnea": 7, "edema": 8}
                }
            },
            "copd_exacerbation": {
                "query": "COPD exacerbation green sputum infection",
                "patient_context": {
                    "primary_diagnosis": "End-stage COPD",
                    "protocol_type": "copd",
                    "age": 68,
                    "symptoms": {"dyspnea": 8, "cough": 7}
                }
            }
        }
        
        if scenario not in test_queries:
            available_scenarios = list(test_queries.keys())
            return jsonify({
                "error": f"Unknown test scenario. Available: {available_scenarios}"
            }), 400
        
        test_data = test_queries[scenario]
        
        # Perform search
        search_results = knowledge_service.search(test_data["query"], k=3)
        
        # Get enhanced guidance
        guidance = knowledge_service.get_enhanced_guidance(
            test_data["query"], 
            test_data["patient_context"]
        )
        
        return jsonify({
            "scenario": scenario,
            "test_query": test_data["query"],
            "patient_context": test_data["patient_context"],
            "search_results": [
                {
                    "title": r["metadata"].get("title", ""),
                    "relevance": r["relevance"],
                    "score": r["score"],
                    "content_preview": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
                }
                for r in search_results
            ],
            "enhanced_guidance": guidance,
            "knowledge_stats": knowledge_service.get_stats()
        })
        
    except Exception as e:
        logger.error(f"Error in knowledge test: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500