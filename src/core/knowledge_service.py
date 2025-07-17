"""Knowledge Base Service for storing and retrieving medical knowledge using vector search."""

import os
import json
import pickle
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import numpy as np
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.utils.logger import get_logger
from src.core.anthropic_client import get_anthropic_client

logger = get_logger()


class KnowledgeBaseService:
    """Service for managing medical knowledge base with vector search capabilities."""
    
    def __init__(self, app=None):
        """Initialize the knowledge base service."""
        self.app = app
        self.embeddings = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.knowledge_dir = None
        self.index_path = None
        self.metadata_path = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the service with Flask app context."""
        self.app = app
        
        # Set up paths
        self.knowledge_dir = Path(app.config.get('KNOWLEDGE_BASE_DIR', 'data/knowledge'))
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.knowledge_dir / 'faiss_index.bin'
        self.metadata_path = self.knowledge_dir / 'metadata.pkl'
        
        # Initialize embeddings
        openai_api_key = app.config.get('OPENAI_API_KEY')
        if openai_api_key:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=openai_api_key,
                model="text-embedding-ada-002"
            )
        else:
            logger.warning("OPENAI_API_KEY not configured - knowledge base will be limited")
        
        # Load existing index if available
        self._load_existing_index()
        
        # Initialize with default medical knowledge and load documents if empty
        if self._is_empty():
            self._initialize_default_knowledge()
        
        # Always try to load documents from directory (controlled by env vars)
        self._load_documents_from_directory()
    
    def _load_existing_index(self):
        """Load existing FAISS index and metadata."""
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                logger.info("Loading existing knowledge base index...")
                
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_path))
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.metadata = data.get('metadata', [])
                    self.documents = data.get('documents', [])
                
                logger.info(f"Loaded knowledge base with {len(self.documents)} documents")
            else:
                logger.info("No existing knowledge base found - will create new one")
                self._initialize_empty_index()
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self._initialize_empty_index()
    
    def _initialize_empty_index(self):
        """Initialize empty FAISS index."""
        # Create empty index with 1536 dimensions (OpenAI ada-002 embedding size)
        dimension = 1536
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []
        self.metadata = []
    
    def _is_empty(self) -> bool:
        """Check if knowledge base is empty."""
        return len(self.documents) == 0
    
    def _initialize_default_knowledge(self):
        """Initialize with default palliative care knowledge."""
        logger.info("Initializing default medical knowledge...")
        
        default_knowledge = [
            {
                "title": "Pain Management in Cancer Patients",
                "content": """
                Pain management in cancer patients follows the WHO analgesic ladder:
                
                Step 1: Non-opioid analgesics (acetaminophen, NSAIDs)
                - For mild pain (1-3/10)
                - First-line treatment for mild cancer pain
                
                Step 2: Weak opioids + non-opioids
                - For moderate pain (4-6/10)
                - Codeine, tramadol, low-dose morphine
                
                Step 3: Strong opioids + non-opioids
                - For severe pain (7-10/10)
                - Morphine, oxycodone, fentanyl, hydromorphone
                
                Key principles:
                - Regular dosing schedule, not as-needed only
                - Breakthrough medication for incident pain
                - Address constipation proactively
                - Monitor for respiratory depression
                - Consider opioid rotation for side effects
                
                Red flags requiring immediate attention:
                - Sudden onset severe pain
                - Pain with neurological deficits
                - Signs of opioid withdrawal
                """,
                "category": "pain_management",
                "tags": ["cancer", "pain", "opioids", "WHO", "breakthrough"],
                "source": "WHO Guidelines for Cancer Pain Management"
            },
            {
                "title": "Heart Failure Symptom Management",
                "content": """
                Key symptoms in heart failure and management approaches:
                
                Dyspnea (Shortness of Breath):
                - Optimize diuretic therapy
                - Consider oxygen if hypoxic
                - Positioning: head of bed elevated
                - Fan therapy for cooling
                - Breathing techniques
                
                Edema Management:
                - Daily weights (report 2-3 lb gain in 24 hrs)
                - Leg elevation when sitting/lying
                - Compression stockings if appropriate
                - Fluid restriction if prescribed
                - Monitor diuretic effectiveness
                
                Fatigue:
                - Energy conservation techniques
                - Paced activities
                - Rest periods between activities
                - Optimize hemoglobin levels
                
                Signs requiring urgent medical attention:
                - Severe dyspnea at rest
                - Chest pain
                - Rapid weight gain (>2-3 lbs in 24 hrs)
                - Syncope or near-syncope
                - Reduced urine output despite diuretics
                """,
                "category": "heart_failure",
                "tags": ["heart failure", "dyspnea", "edema", "fatigue", "emergency"],
                "source": "Heart Failure Society Guidelines"
            },
            {
                "title": "COPD Exacerbation Management",
                "content": """
                COPD exacerbation signs and management:
                
                Early Warning Signs:
                - Increased dyspnea
                - Change in sputum color/volume
                - Increased cough frequency
                - Fatigue or decreased exercise tolerance
                - Chest tightness
                
                Management Strategies:
                - Bronchodilator optimization
                - Breathing techniques (pursed-lip breathing)
                - Positioning for comfort
                - Energy conservation
                - Oxygen therapy if prescribed
                
                Sputum Assessment:
                - Clear/white: Normal
                - Yellow: Possible infection
                - Green: Likely bacterial infection
                - Blood-tinged: Requires evaluation
                
                When to seek emergency care:
                - Severe dyspnea at rest
                - Confusion or altered mental status
                - Cyanosis (blue lips/fingernails)
                - High fever with productive cough
                - Unable to speak in full sentences
                
                Infection Prevention:
                - Hand hygiene
                - Avoid crowds during respiratory illness seasons
                - Stay up to date with vaccinations
                """,
                "category": "copd",
                "tags": ["COPD", "exacerbation", "infection", "dyspnea", "emergency"],
                "source": "GOLD COPD Guidelines"
            },
            {
                "title": "Nausea and Vomiting in Palliative Care",
                "content": """
                Common causes and management of nausea/vomiting:
                
                Medication-Related:
                - Opioids: Consider anti-emetics, dose adjustment
                - Chemotherapy: Prophylactic anti-emetics
                - Antibiotics: Take with food if appropriate
                
                Disease-Related:
                - Gastric stasis: Metoclopramide, domperidone
                - Bowel obstruction: Octreotide, hyoscine
                - Increased intracranial pressure: Dexamethasone
                
                Anti-emetic Options:
                - Ondansetron: For chemotherapy-induced nausea
                - Metoclopramide: For gastric stasis
                - Haloperidol: For opioid-induced nausea
                - Promethazine: For motion-related nausea
                
                Non-pharmacological approaches:
                - Small, frequent meals
                - Avoid strong odors
                - Ginger tea or supplements
                - Acupressure (P6 point)
                - Cool, fresh air
                
                When to escalate:
                - Persistent vomiting >24 hours
                - Signs of dehydration
                - Unable to keep medications down
                - Blood in vomit
                """,
                "category": "symptom_management",
                "tags": ["nausea", "vomiting", "anti-emetics", "palliative", "side effects"],
                "source": "Palliative Care Guidelines"
            }
        ]
        
        # Add default knowledge to the index
        for item in default_knowledge:
            self.add_document(
                content=item["content"],
                title=item["title"],
                category=item["category"],
                tags=item["tags"],
                source=item["source"]
            )
        
        logger.info(f"Added {len(default_knowledge)} default knowledge items")
    
    def _load_documents_from_directory(self):
        """Load documents from the data directory following seeding pattern."""
        try:
            import os
            
            # Check environment variables for document loading configuration
            load_documents_env = os.getenv("LOAD_DOCUMENTS", "true") 
            force_reload_env = os.getenv("FORCE_RELOAD_DOCUMENTS", "false")
            documents_dir_env = os.getenv("DOCUMENTS_DIR", "data")
            
            logger.info(f"Document loading - LOAD_DOCUMENTS: '{load_documents_env}', FORCE_RELOAD_DOCUMENTS: '{force_reload_env}', DOCUMENTS_DIR: '{documents_dir_env}'")
            
            should_load = load_documents_env.lower() == "true"
            force_reload = force_reload_env.lower() == "true"
            
            if not should_load and not force_reload:
                logger.info("❌ LOAD_DOCUMENTS=false and FORCE_RELOAD_DOCUMENTS=false, skipping document loading")
                return
                
            # Check if documents have already been loaded (unless force reload)
            if not force_reload:
                # Check if any documents from files are already in the knowledge base
                existing_doc_sources = [meta.get('source', '') for meta in self.metadata if meta.get('source', '').startswith('Document:')]
                if existing_doc_sources:
                    logger.info(f"✅ Found {len(existing_doc_sources)} existing documents from previous ingestion, skipping document loading (use FORCE_RELOAD_DOCUMENTS=true to reload)")
                    return
                
            # Get documents directory
            documents_dir = Path(documents_dir_env)
            
            if not documents_dir.exists():
                logger.info(f"📁 Documents directory {documents_dir} does not exist, skipping document loading")
                return
                
            # Find PDF and TXT files in the documents directory
            pdf_files = list(documents_dir.glob("*.pdf"))
            txt_files = list(documents_dir.glob("*.txt"))
            docx_files = list(documents_dir.glob("*.docx"))
            
            all_files = pdf_files + txt_files + docx_files
            
            if not all_files:
                logger.info(f"📄 No documents found in {documents_dir}")
                return
                
            logger.info(f"📚 Found {len(all_files)} documents to load: {len(pdf_files)} PDFs, {len(txt_files)} TXT files, {len(docx_files)} DOCX files")
            logger.info("🔄 INGESTING DATA - Application will be available after document processing completes")
            logger.info(f"⏱️  Estimated time: {len(all_files) * 8} minutes for large protocol documents")
            
            # Load each document
            successful_loads = 0
            failed_loads = 0
            
            for i, file_path in enumerate(all_files, 1):
                try:
                    logger.info(f"📖 INGESTING ({i}/{len(all_files)}): {file_path.name}")
                    logger.info(f"🔄 Progress: {((i-1)/len(all_files)*100):.0f}% complete")
                    
                    # Determine document loader based on file type
                    if file_path.suffix.lower() == '.pdf':
                        from langchain_community.document_loaders import PyPDFLoader
                        loader = PyPDFLoader(str(file_path))
                    elif file_path.suffix.lower() == '.txt':
                        from langchain_community.document_loaders import TextLoader
                        loader = TextLoader(str(file_path))
                    elif file_path.suffix.lower() == '.docx':
                        # For DOCX files, we'll need to add python-docx to requirements
                        try:
                            from langchain_community.document_loaders import UnstructuredWordDocumentLoader
                            loader = UnstructuredWordDocumentLoader(str(file_path))
                        except ImportError:
                            logger.warning(f"⚠️ DOCX support not available, skipping {file_path.name}")
                            continue
                    else:
                        logger.warning(f"⚠️ Unsupported file type: {file_path.suffix}")
                        continue
                        
                    # Load and process the document
                    documents = loader.load()
                    
                    # Combine all pages/sections into one content string
                    content = "\n\n".join([doc.page_content for doc in documents])
                    
                    # Extract metadata from filename and content
                    title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
                    
                    # Categorize based on filename patterns
                    filename_lower = file_path.name.lower()
                    if 'protocol' in filename_lower or 'telephone' in filename_lower:
                        category = "protocols"
                        tags = ["protocols", "telephone", "triage"]
                    elif 'caregiver' in filename_lower or 'handbook' in filename_lower:
                        category = "caregiving"
                        tags = ["caregiving", "handbook", "support"]
                    elif 'palliative' in filename_lower:
                        category = "palliative_care"
                        tags = ["palliative", "care", "management"]
                    else:
                        category = "medical_reference"
                        tags = ["medical", "reference"]
                    
                    # Add document to knowledge base
                    success = self.add_document(
                        content=content,
                        title=title,
                        category=category,
                        tags=tags,
                        source=f"Document: {file_path.name}"
                    )
                    
                    if success:
                        successful_loads += 1
                        logger.info(f"✅ COMPLETED ({i}/{len(all_files)}): {file_path.name}")
                        logger.info(f"📊 Progress: {(i/len(all_files)*100):.0f}% complete")
                    else:
                        failed_loads += 1
                        logger.error(f"❌ FAILED ({i}/{len(all_files)}): {file_path.name}")
                        
                except Exception as e:
                    failed_loads += 1
                    logger.error(f"❌ Error loading {file_path.name}: {e}")
                    
            logger.info(f"🎉 INGESTION COMPLETE: {successful_loads} successful, {failed_loads} failed")
            
            # Save the updated index after all documents are loaded
            if successful_loads > 0:
                logger.info("💾 Saving updated knowledge base index to disk...")
                self._save_index()
                logger.info("✅ Knowledge base index saved successfully")
                logger.info("🚀 APPLICATION READY - All services now available")
            
        except Exception as e:
            logger.error(f"❌ Error in document directory loading: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def add_document(self, content: str, title: str = "", category: str = "", 
                    tags: List[str] = None, source: str = "") -> bool:
        """Add a document to the knowledge base."""
        try:
            if not self.embeddings:
                logger.error("Embeddings not initialized - cannot add document")
                return False
            
            # Split long content into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            chunks = text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embeddings.embed_query(chunk)
                embedding_array = np.array([embedding], dtype=np.float32)
                
                # Add to FAISS index
                self.index.add(embedding_array)
                
                # Store document and metadata
                doc_id = len(self.documents)
                self.documents.append(chunk)
                
                metadata = {
                    "id": doc_id,
                    "title": title,
                    "category": category,
                    "tags": tags or [],
                    "source": source,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "added_at": datetime.utcnow().isoformat(),
                    "content_hash": hashlib.md5(chunk.encode()).hexdigest()
                }
                self.metadata.append(metadata)
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added document '{title}' with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def search(self, query: str, k: int = 5, category_filter: str = None) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant documents."""
        try:
            if not self.embeddings or not self.index or len(self.documents) == 0:
                logger.warning("Knowledge base not properly initialized")
                return []
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Search FAISS index
            scores, indices = self.index.search(query_array, min(k * 2, len(self.documents)))
            
            results = []
            seen_hashes = set()
            
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No more results
                    break
                
                metadata = self.metadata[idx]
                content = self.documents[idx]
                
                # Apply category filter if specified
                if category_filter and metadata.get("category") != category_filter:
                    continue
                
                # Avoid duplicate content
                content_hash = metadata.get("content_hash", "")
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)
                
                result = {
                    "content": content,
                    "score": float(score),
                    "metadata": metadata,
                    "relevance": self._calculate_relevance_score(score)
                }
                results.append(result)
                
                if len(results) >= k:
                    break
            
            logger.info(f"Knowledge search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def _calculate_relevance_score(self, distance_score: float) -> str:
        """Convert FAISS distance score to relevance category."""
        if distance_score < 0.3:
            return "very_high"
        elif distance_score < 0.5:
            return "high"
        elif distance_score < 0.8:
            return "medium"
        else:
            return "low"
    
    def get_enhanced_guidance(self, query: str, patient_context: Dict[str, Any] = None) -> str:
        """Get AI-enhanced guidance combining knowledge retrieval with Claude AI."""
        try:
            # Search knowledge base
            relevant_docs = self.search(query, k=3)
            
            if not relevant_docs:
                logger.info("No relevant knowledge found, using basic AI response")
                return self._get_basic_ai_response(query, patient_context)
            
            # Prepare context with retrieved knowledge
            knowledge_context = self._prepare_knowledge_context(relevant_docs)
            
            # Get enhanced response from Claude
            return self._get_enhanced_ai_response(query, knowledge_context, patient_context)
            
        except Exception as e:
            logger.error(f"Error getting enhanced guidance: {e}")
            return f"Error retrieving guidance: {str(e)}"
    
    def _prepare_knowledge_context(self, docs: List[Dict[str, Any]]) -> str:
        """Prepare knowledge context for AI prompt."""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            metadata = doc["metadata"]
            content = doc["content"]
            
            context_part = f"""
Reference {i} (Relevance: {doc['relevance']}):
Title: {metadata.get('title', 'Unknown')}
Source: {metadata.get('source', 'Internal Knowledge Base')}
Category: {metadata.get('category', 'general')}

Content:
{content}
"""
            context_parts.append(context_part)
        
        return "\\n".join(context_parts)
    
    def _get_enhanced_ai_response(self, query: str, knowledge_context: str, 
                                patient_context: Dict[str, Any] = None) -> str:
        """Get enhanced AI response using retrieved knowledge."""
        try:
            # Get Anthropic client
            anthropic_api_key = self.app.config.get("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                return "Anthropic API key not configured"
            
            client = get_anthropic_client(anthropic_api_key)
            
            # Build context-aware prompt
            system_prompt = """
You are a specialized palliative care assistant with access to evidence-based medical knowledge. 
Your role is to provide clinical guidance based on current best practices and the specific 
knowledge references provided.

Guidelines:
1. Base your recommendations on the provided reference materials
2. Cite specific sources when making recommendations
3. Acknowledge limitations if the query goes beyond available knowledge
4. Focus on practical, actionable guidance
5. Consider patient safety as the top priority
6. Suggest when to escalate to physician care
"""
            
            patient_info = ""
            if patient_context:
                patient_info = f"""
PATIENT CONTEXT:
- Primary Diagnosis: {patient_context.get('primary_diagnosis', 'Not specified')}
- Protocol Type: {patient_context.get('protocol_type', 'Not specified')}
- Age: {patient_context.get('age', 'Not specified')}
- Current Symptoms: {patient_context.get('symptoms', 'Not assessed')}
"""
            
            user_prompt = f"""
CLINICAL QUERY: {query}

{patient_info}

AVAILABLE KNOWLEDGE REFERENCES:
{knowledge_context}

Based on the above reference materials and patient context (if provided), please provide 
evidence-based clinical guidance. Include:

1. Direct recommendations based on the reference materials
2. Any relevant considerations for this specific patient context
3. When to seek additional medical evaluation
4. Source citations for your recommendations

Keep the response practical and focused on actionable guidance.
"""
            
            response = client.call_model(
                model="claude-3-sonnet-20240229",
                system=system_prompt,
                max_tokens=1500,
                messages=[{"role": "user", "content": user_prompt}],
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting enhanced AI response: {e}")
            return f"Error generating enhanced guidance: {str(e)}"
    
    def _get_basic_ai_response(self, query: str, patient_context: Dict[str, Any] = None) -> str:
        """Get basic AI response without knowledge retrieval."""
        try:
            # This is a fallback when no relevant knowledge is found
            anthropic_api_key = self.app.config.get("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                return "Clinical guidance system not available"
            
            client = get_anthropic_client(anthropic_api_key)
            
            patient_info = ""
            if patient_context:
                patient_info = f"Patient context: {patient_context.get('primary_diagnosis', 'General palliative care')}"
            
            prompt = f"""
You are a palliative care assistant. Provide brief, evidence-based guidance for: {query}

{patient_info}

Focus on:
1. Immediate symptom management
2. When to seek physician evaluation
3. Safety considerations

Keep response concise and practical.
"""
            
            response = client.call_model(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting basic AI response: {e}")
            return "Unable to provide guidance at this time"
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'documents': self.documents,
                    'updated_at': datetime.utcnow().isoformat()
                }, f)
            
            logger.debug("Knowledge base index saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base index: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        categories = {}
        for meta in self.metadata:
            category = meta.get("category", "uncategorized")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.documents),
            "categories": categories,
            "index_size": self.index.ntotal if self.index else 0,
            "last_updated": max([meta.get("added_at", "") for meta in self.metadata], default="Never")
        }


# Global service instance
knowledge_service = KnowledgeBaseService()


def init_knowledge_service(app):
    """Initialize knowledge service with app."""
    knowledge_service.init_app(app)
    return knowledge_service


def get_knowledge_service():
    """Get the global knowledge service instance."""
    return knowledge_service