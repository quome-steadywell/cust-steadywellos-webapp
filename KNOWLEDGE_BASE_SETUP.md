# Knowledge Base Integration Setup

This document describes the knowledge base feature that has been integrated into the SteadwellOS palliative care platform.

## Overview

The knowledge base integration enhances the existing RAG (Retrieval-Augmented Generation) service with:

1. **Vector-based knowledge storage** using FAISS
2. **Enhanced AI responses** with retrieved medical knowledge
3. **Retell AI integration** for knowledge-enhanced phone calls
4. **REST API endpoints** for knowledge management

## Features Implemented

### 1. Knowledge Base Service (`src/core/knowledge_service.py`)
- **Vector storage** using FAISS for similarity search
- **OpenAI embeddings** for document encoding
- **Default medical knowledge** for palliative care
- **Document chunking** for large content
- **Relevance scoring** for search results

### 2. Enhanced RAG Service (`src/core/rag_service.py`)
- **Knowledge-enhanced assessment processing**
- **Intelligent call script generation**
- **Fallback to standard processing** when knowledge unavailable

### 3. Retell AI Integration (`src/core/retell_integration.py`)
- **Knowledge-enhanced agent prompts**
- **Dynamic variable enhancement**
- **Call transcript analysis** with knowledge context
- **Agent configuration optimization**

### 4. API Endpoints (`src/api/knowledge.py`)
- `POST /api/v1/knowledge/search` - Search knowledge base
- `POST /api/v1/knowledge/guidance` - Get enhanced AI guidance
- `POST /api/v1/knowledge/documents` - Add new documents (admin only)
- `GET /api/v1/knowledge/stats` - Get knowledge base statistics
- `POST /api/v1/knowledge/test` - Test knowledge retrieval

### 5. Enhanced Call Service (`src/core/call_service.py`)
- **Knowledge-enhanced Retell AI calls**
- **Enhanced metadata and dynamic variables**
- **Fallback to standard calls** on error

## Configuration

### Required Environment Variables

```bash
# Existing variables (already configured)
ANTHROPIC_API_KEY=your_anthropic_api_key
RETELLAI_API_KEY=your_retell_api_key
RETELLAI_LOCAL_AGENT_ID=your_local_agent_id
RETELLAI_REMOTE_AGENT_ID=your_remote_agent_id

# New variables for knowledge base
OPENAI_API_KEY=your_openai_api_key  # For embeddings
KNOWLEDGE_BASE_DIR=data/knowledge   # Optional: defaults to data/knowledge
```

### Directory Structure

The knowledge base creates the following directory structure:

```
data/
└── knowledge/
    ├── faiss_index.bin      # FAISS vector index
    └── metadata.pkl         # Document metadata
```

## Default Knowledge

The system initializes with default palliative care knowledge including:

1. **Pain Management in Cancer Patients** - WHO analgesic ladder, red flags
2. **Heart Failure Symptom Management** - dyspnea, edema, fatigue management
3. **COPD Exacerbation Management** - warning signs, sputum assessment
4. **Nausea and Vomiting** - causes, treatments, escalation criteria

## API Usage Examples

### Search Knowledge Base
```bash
curl -X POST http://localhost:5000/api/v1/knowledge/search \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "severe cancer pain management",
    "k": 3,
    "category": "pain_management"
  }'
```

### Get Enhanced Guidance
```bash
curl -X POST http://localhost:5000/api/v1/knowledge/guidance \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "patient reports pain level 8/10",
    "patient_context": {
      "primary_diagnosis": "Stage IV Lung Cancer",
      "protocol_type": "cancer",
      "age": 65
    }
  }'
```

### Test Knowledge Retrieval
```bash
curl -X POST http://localhost:5000/api/v1/knowledge/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "pain_management"
  }'
```

## Integration Points

### 1. Assessment Processing
When processing patient assessments, the system:
1. Builds a search query from symptoms and diagnosis
2. Retrieves relevant medical knowledge
3. Enhances AI response with evidence-based guidance
4. Falls back to standard processing if knowledge unavailable

### 2. Call Script Generation
For telephone assessments, the system:
1. Searches for communication best practices
2. Enhances scripts with evidence-based approaches
3. Maintains empathetic, patient-friendly language

### 3. Retell AI Integration
For automated calls, the system:
1. Generates knowledge-enhanced agent prompts
2. Adds medical context to dynamic variables
3. Provides evidence-based response guidance
4. Enables post-call knowledge insights

## Development Notes

### Vector Embeddings
- Uses OpenAI's `text-embedding-ada-002` model
- 1536-dimensional vectors
- Cosine similarity for relevance scoring

### Knowledge Categories
- `pain_management` - Pain assessment and treatment
- `heart_failure` - Heart failure symptom management
- `copd` - COPD exacerbation and care
- `symptom_management` - General symptom control
- `general` - Uncategorized knowledge

### Performance Considerations
- FAISS index loaded at startup
- In-memory storage for fast retrieval
- Automatic index persistence
- Graceful fallback on errors

## Testing

### Manual Testing
1. Start the application with proper environment variables
2. Use the `/api/v1/knowledge/test` endpoint with scenarios:
   - `pain_management`
   - `heart_failure`
   - `copd_exacerbation`

### Integration Testing
The knowledge base integrates seamlessly with existing features:
- Assessment processing via `/api/v1/assessments`
- Call creation via `/api/v1/calls`
- Webhook processing for Retell AI calls

## Troubleshooting

### Common Issues

1. **"Knowledge base service not available"**
   - Check OPENAI_API_KEY is configured
   - Verify network connectivity
   - Check application logs for initialization errors

2. **"No relevant knowledge found"**
   - Normal behavior for queries outside medical domain
   - System falls back to standard AI processing
   - Consider adding more domain-specific knowledge

3. **"Embeddings not initialized"**
   - Ensure OPENAI_API_KEY is valid
   - Check OpenAI API quota and billing
   - Restart application to retry initialization

### Logs to Monitor
```bash
# Knowledge base initialization
"✅ Knowledge base service initialized"

# Knowledge-enhanced processing
"Using knowledge-enhanced guidance for query"
"Generated knowledge-enhanced prompt"

# Fallback scenarios
"Knowledge service not available, using basic prompt"
"No relevant knowledge found, using basic prompt"
```

## Security Notes

- Knowledge base APIs require JWT authentication
- Document upload restricted to admin users
- No sensitive patient data stored in knowledge base
- Vector embeddings are anonymized medical knowledge

## Future Enhancements

Potential improvements for the knowledge base:

1. **PDF Processing** - Add support for uploading PDF guidelines
2. **Knowledge Curation** - Admin interface for managing knowledge
3. **Usage Analytics** - Track which knowledge is most useful
4. **Automatic Updates** - Sync with latest medical guidelines
5. **Multi-language Support** - Support for non-English content

## Files Modified/Created

### New Files
- `src/core/knowledge_service.py` - Core knowledge base service
- `src/core/retell_integration.py` - Retell AI integration
- `src/api/knowledge.py` - REST API endpoints

### Modified Files
- `src/__init__.py` - Added knowledge service initialization
- `src/core/rag_service.py` - Enhanced with knowledge retrieval
- `src/core/call_service.py` - Added knowledge-enhanced calls

This implementation provides a solid foundation for evidence-based clinical decision support while maintaining compatibility with the existing palliative care platform.