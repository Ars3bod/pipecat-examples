#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
RAG Engine for Knowledge Management System
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import os
from langdetect import detect, LangDetectException
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    import openai
except ImportError:
    openai = None

# Local imports
from .vector_store import VectorStore
from .embedding_generator import EmbeddingGenerator
from .config import get_config, get_rag_prompts

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval Augmented Generation engine for answering questions based on organizational knowledge.
    """
    
    def __init__(self):
        self.config = get_config()
        self.rag_prompts = get_rag_prompts()
        self.llm_provider = self.config["llm"]["provider"]
        
        # Initialize components
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize LLM client based on provider
        if self.llm_provider == "google":
            self._initialize_gemini()
        elif self.llm_provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        logger.info(f"RAG Engine initialized successfully with {self.llm_provider}")
    
    def _initialize_gemini(self):
        """Initialize Gemini client."""
        try:
            if genai is None:
                raise ImportError("google-generativeai package is not installed")
            
            api_key = self.config["llm"]["api_key"]
            model_name = self.config["llm"]["model"]
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(model_name)
            
            logger.info(f"Gemini client initialized with model: {model_name}")
             
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {str(e)}")
            raise
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            if openai is None:
                raise ImportError("openai package is not installed")
            
            api_key = self.config["llm"]["api_key"]
            api_base = self.config["llm"]["api_base"]
            api_version = self.config["llm"]["api_version"]
            
            if api_base:
                openai.api_base = api_base
            if api_version:
                openai.api_version = api_version
            
            openai.api_key = api_key
            
            logger.info("OpenAI client initialized")
             
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise
    
    def query(self, question: str, language: str = "ar", user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query using RAG.
        
        Args:
            question: User question
            language: Language code ('ar' or 'en')
            user_context: Additional user context (department, role, etc.)
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Detect language if not specified
            if not language:
                language = self._detect_language(question)
            
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(question, language)
            
            # Prepare filters based on user context
            filters = self._prepare_filters(user_context)
            
            # Retrieve relevant documents
            retrieved_docs = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=self.config["retrieval"]["top_k"],
                filters=filters
            )
            
            if not retrieved_docs:
                return self._create_no_results_response(question, language)
            
            # Assemble context
            context = self._assemble_context(retrieved_docs)
            
            # Generate response
            response = self._generate_response(question, context, language)
            
            # Validate response
            validated_response = self._validate_response(response, context, language)
            
            # Prepare result
            result = {
                "question": question,
                "answer": validated_response,
                "sources": self._extract_sources(retrieved_docs),
                "language": language,
                "confidence": self._calculate_confidence(retrieved_docs),
                "metadata": {
                    "retrieved_docs_count": len(retrieved_docs),
                    "context_length": len(context),
                    "user_context": user_context
                }
            }
            
            logger.info(f"RAG query processed successfully: {len(retrieved_docs)} docs retrieved")
            return result
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {str(e)}")
            return self._create_error_response(question, language, str(e))
    
    def _detect_language(self, text: str) -> str:
        """Detect language of the text."""
        try:
            detected_lang = detect(text)
            return "ar" if detected_lang in ["ar", "arabic"] else "en"
        except LangDetectException:
            return "ar"  # Default to Arabic
    
    def _prepare_filters(self, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare filters based on user context."""
        if not user_context:
            return None
        
        filters = {}
        
        # Department filter
        if "department" in user_context:
            filters["department"] = user_context["department"]
        
        # Classification filter
        if "role" in user_context:
            # Map role to classification access
            role = user_context["role"]
            if role in ["admin", "manager"]:
                filters["classification"] = {"$in": ["public", "internal", "confidential"]}
            elif role in ["employee", "staff"]:
                filters["classification"] = {"$in": ["public", "internal"]}
            else:
                filters["classification"] = "public"
        
        return filters if filters else None
    
    def _assemble_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Assemble context from retrieved documents."""
        context_parts = []
        max_length = self.config["retrieval"]["max_context_length"]
        current_length = 0
        
        for doc in retrieved_docs:
            # Add document content
            content = doc["content"]
            if current_length + len(content) > max_length:
                break
            
            # Add source information
            source_info = f"[المصدر: {doc['metadata']['title']} - {doc['metadata']['department']}]"
            context_parts.append(f"{source_info}\n{content}")
            current_length += len(content) + len(source_info)
        
        return "\n\n".join(context_parts)
    
    def _generate_response(self, question: str, context: str, language: str) -> str:
        """Generate response using LLM (Gemini or OpenAI)."""
        try:
            # Get prompt template
            prompt_template = self.rag_prompts[language]["system"]
            
            # Format prompt
            system_prompt = prompt_template.format(
                organization_name=os.getenv('ORGANIZATION_NAME', 'الهيئة'),
                assistant_name=os.getenv('ASSISTANT_NAME', 'مساعد الهيئة'),
                context=context,
                question=question
            )
            
            if self.llm_provider == "google":
                # Use Gemini
                full_prompt = f"{system_prompt}\n\nUser Question: {question}"
                response = self.gemini_model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config["llm"]["temperature"],
                        max_output_tokens=self.config["llm"]["max_tokens"]
                    )
                )
                return response.text.strip()
                
            elif self.llm_provider == "openai":
                # Use OpenAI
                response = openai.ChatCompletion.create(
                    model=self.config["llm"]["model"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=self.config["llm"]["temperature"],
                    max_tokens=self.config["llm"]["max_tokens"]
                )
                return response.choices[0].message.content.strip()
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _validate_response(self, response: str, context: str, language: str) -> str:
        """Validate response to ensure it stays within scope."""
        # Check if response contains organizational information
        if not self._contains_organizational_info(response):
            if language == "ar":
                return "آسف، لا أملك هذه المعلومة في قاعدة المعرفة. هل تريد التحويل لموظف بشري؟"
            else:
                return "Sorry, I don't have this information in the knowledge base. Would you like me to transfer you to a human?"
        
        # Check response length
        max_length = self.config["llm"]["max_tokens"] * 4  # Rough character estimate
        if len(response) > max_length:
            response = response[:max_length] + "..."
        
        return response
    
    def _contains_organizational_info(self, response: str) -> bool:
        """Check if response contains organizational information."""
        # Simple check for organizational keywords
        org_keywords = [
            "الهيئة", "الموظف", "العمل", "السياسات", "الإجراءات",
            "organization", "employee", "work", "policies", "procedures"
        ]
        
        response_lower = response.lower()
        return any(keyword.lower() in response_lower for keyword in org_keywords)
    
    def _extract_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved documents."""
        sources = []
        seen_docs = set()
        
        for doc in retrieved_docs:
            doc_id = doc["metadata"]["document_id"]
            if doc_id not in seen_docs:
                sources.append({
                    "document_id": doc_id,
                    "title": doc["metadata"]["title"],
                    "department": doc["metadata"]["department"],
                    "category": doc["metadata"]["category"],
                    "similarity": doc["similarity"]
                })
                seen_docs.add(doc_id)
        
        return sources
    
    def _calculate_confidence(self, retrieved_docs: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieved documents."""
        if not retrieved_docs:
            return 0.0
        
        # Calculate average similarity
        similarities = [doc["similarity"] for doc in retrieved_docs]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Adjust confidence based on number of documents
        confidence = avg_similarity * min(len(retrieved_docs) / 3, 1.0)
        
        return round(confidence, 2)
    
    def _create_no_results_response(self, question: str, language: str) -> Dict[str, Any]:
        """Create response when no relevant documents are found."""
        if language == "ar":
            answer = "آسف، لا أملك هذه المعلومة في قاعدة المعرفة. هل تريد التحويل لموظف بشري؟"
        else:
            answer = "Sorry, I don't have this information in the knowledge base. Would you like me to transfer you to a human?"
        
        return {
            "question": question,
            "answer": answer,
            "sources": [],
            "language": language,
            "confidence": 0.0,
            "metadata": {
                "retrieved_docs_count": 0,
                "context_length": 0,
                "no_results": True
            }
        }
    
    def _create_error_response(self, question: str, language: str, error: str) -> Dict[str, Any]:
        """Create response when an error occurs."""
        if language == "ar":
            answer = "عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى أو التحويل لموظف بشري."
        else:
            answer = "Sorry, an error occurred while processing your request. Please try again or transfer to a human."
        
        return {
            "question": question,
            "answer": answer,
            "sources": [],
            "language": language,
            "confidence": 0.0,
            "metadata": {
                "error": error,
                "retrieved_docs_count": 0,
                "context_length": 0
            }
        }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return self.vector_store.get_collection_stats()
    
    def test_rag_system(self, test_questions: List[str] = None) -> Dict[str, Any]:
        """Test the RAG system with sample questions."""
        if test_questions is None:
            test_questions = [
                "ما هي سياسات الإجازات؟",
                "كيف يمكنني تقديم طلب إجازة؟",
                "ما هي ساعات العمل؟",
                "كيف يمكنني التواصل مع قسم الموارد البشرية؟"
            ]
        
        results = []
        for question in test_questions:
            try:
                result = self.query(question, language="ar")
                results.append({
                    "question": question,
                    "success": True,
                    "answer_length": len(result["answer"]),
                    "sources_count": len(result["sources"]),
                    "confidence": result["confidence"]
                })
            except Exception as e:
                results.append({
                    "question": question,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "test_results": results,
            "total_questions": len(test_questions),
            "successful_queries": len([r for r in results if r["success"]]),
            "knowledge_base_stats": self.get_knowledge_base_stats()
        }

# Example usage
if __name__ == "__main__":
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Test the system
    test_results = rag_engine.test_rag_system()
    print(f"Test results: {test_results}")
    
    # Example query
    # result = rag_engine.query("ما هي سياسات الإجازات؟", language="ar")
    # print(f"Answer: {result['answer']}")
    # print(f"Sources: {len(result['sources'])} documents")
    # print(f"Confidence: {result['confidence']}")
