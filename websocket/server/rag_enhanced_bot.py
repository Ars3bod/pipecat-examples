#!/usr/bin/env python3
"""
RAG-Enhanced Bot Integration
This module integrates the RAG Knowledge Management System with the existing bot.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any
from loguru import logger

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from rag_system.rag_engine import RAGEngine
from rag_system.config import get_config, validate_config
from organizational_filter import OrganizationalKnowledgeFilter

class RAGEnhancedBot:
    """
    RAG-Enhanced Bot that combines organizational filtering with knowledge retrieval.
    """
    
    def __init__(self):
        """Initialize the RAG-enhanced bot."""
        self.rag_engine = None
        self.org_filter = OrganizationalKnowledgeFilter()
        self.config = get_config()
        self.is_initialized = False
        
        # Initialize RAG engine lazily
        self._rag_initialized = False
    
    async def _initialize_rag(self):
        """Initialize the RAG engine asynchronously."""
        try:
            # Validate configuration first
            errors = validate_config()
            if errors:
                logger.error(f"RAG configuration errors: {errors}")
                return
            
            # Initialize RAG engine
            self.rag_engine = RAGEngine()
            await self.rag_engine.initialize()
            self.is_initialized = True
            logger.info("RAG engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self.is_initialized = False
    
    def is_rag_available(self) -> bool:
        """Check if RAG system is available."""
        return self.is_initialized and self.rag_engine is not None
    
    async def process_query(self, user_input: str, language: str = "ar") -> Dict[str, Any]:
        """
        Process user query with RAG enhancement.
        
        Args:
            user_input: User's question or input
            language: Language of the query (ar/en)
            
        Returns:
            Dict containing response, sources, and metadata
        """
        try:
            # Initialize RAG if not already done
            if not self._rag_initialized:
                await self._initialize_rag()
            
            # First, check if query is organizational
            is_org, reason = self.org_filter.is_organizational_query(user_input)
            if not is_org:
                return {
                    "response": self._get_non_org_response(language),
                    "sources": [],
                    "is_organizational": False,
                    "rag_enhanced": False
                }
            
            # If RAG is available, use it for enhanced responses
            if self.is_rag_available():
                try:
                    rag_result = await self.rag_engine.query(user_input, language=language)
                    
                    if rag_result and rag_result.get("answer"):
                        return {
                            "response": rag_result["answer"],
                            "sources": rag_result.get("sources", []),
                            "confidence": rag_result.get("confidence", 0.0),
                            "is_organizational": True,
                            "rag_enhanced": True,
                            "context_used": rag_result.get("context", "")
                        }
                    else:
                        # RAG didn't find relevant information
                        return {
                            "response": self._get_no_info_response(language),
                            "sources": [],
                            "is_organizational": True,
                            "rag_enhanced": False
                        }
                        
                except Exception as e:
                    logger.error(f"RAG query failed: {e}")
                    # Fall back to basic organizational response
                    return {
                        "response": self._get_fallback_response(language),
                        "sources": [],
                        "is_organizational": True,
                        "rag_enhanced": False,
                        "error": str(e)
                    }
            else:
                # RAG not available, use basic organizational response
                return {
                    "response": self._get_basic_org_response(user_input, language),
                    "sources": [],
                    "is_organizational": True,
                    "rag_enhanced": False
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": self._get_error_response(language),
                "sources": [],
                "is_organizational": False,
                "rag_enhanced": False,
                "error": str(e)
            }
    
    def _get_non_org_response(self, language: str) -> str:
        """Get response for non-organizational queries."""
        if language == "ar":
            return "آسف، أنا مساعد رقمي مخصص للأسئلة المتعلقة بالهيئة فقط. هل لديك سؤال عن العمل أو سياسات الهيئة؟"
        else:
            return "Sorry, I'm a digital assistant dedicated to organization-related questions only. Do you have a question about work or organizational policies?"
    
    def _get_no_info_response(self, language: str) -> str:
        """Get response when no relevant information is found."""
        if language == "ar":
            return "آسف، لا أملك هذه المعلومة في قاعدة المعرفة الحالية. هل تريد التحويل لموظف بشري؟"
        else:
            return "Sorry, I don't have this information in the current knowledge base. Would you like me to transfer you to a human employee?"
    
    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response when RAG fails."""
        if language == "ar":
            return "أعتذر، واجهت مشكلة في الوصول لقاعدة المعرفة. سأحولك لموظف بشري للمساعدة."
        else:
            return "I apologize, I encountered an issue accessing the knowledge base. I'll transfer you to a human employee for assistance."
    
    def _get_basic_org_response(self, user_input: str, language: str) -> str:
        """Get basic organizational response when RAG is not available."""
        if language == "ar":
            return "شكراً لسؤالك عن الهيئة. نظام المعرفة غير متوفر حالياً. هل تريد التحويل لموظف بشري؟"
        else:
            return "Thank you for your question about the organization. The knowledge system is currently unavailable. Would you like me to transfer you to a human employee?"
    
    def _get_error_response(self, language: str) -> str:
        """Get error response."""
        if language == "ar":
            return "أعتذر، حدث خطأ تقني. هل تريد المحاولة مرة أخرى أو التحويل لموظف بشري؟"
        else:
            return "I apologize, a technical error occurred. Would you like to try again or be transferred to a human employee?"
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status information."""
        return {
            "rag_initialized": self.is_initialized,
            "rag_available": self.is_rag_available(),
            "config_valid": len(validate_config()) == 0,
            "organizational_filter": True
        }
    
    async def reload_knowledge_base(self):
        """Reload the knowledge base."""
        if self.rag_engine:
            await self.rag_engine.reload_knowledge_base()
            logger.info("Knowledge base reloaded")

# Global instance
rag_bot = RAGEnhancedBot()

async def get_rag_enhanced_response(user_input: str, language: str = "ar") -> str:
    """
    Get RAG-enhanced response for user input.
    This is the main function to be called from the bot files.
    
    Args:
        user_input: User's question or input
        language: Language of the query (ar/en)
        
    Returns:
        Enhanced response string
    """
    result = await rag_bot.process_query(user_input, language)
    return result["response"]

async def get_detailed_rag_response(user_input: str, language: str = "ar") -> Dict[str, Any]:
    """
    Get detailed RAG response with sources and metadata.
    
    Args:
        user_input: User's question or input
        language: Language of the query (ar/en)
        
    Returns:
        Detailed response dictionary
    """
    return await rag_bot.process_query(user_input, language)

if __name__ == "__main__":
    # Test the RAG-enhanced bot
    async def test_bot():
        print("Testing RAG-Enhanced Bot...")
        
        # Wait for initialization
        await asyncio.sleep(2)
        
        # Test queries
        test_queries = [
            ("ما هي سياسات الإجازات؟", "ar"),
            ("What are the working hours?", "en"),
            ("كيف الطقس اليوم؟", "ar"),  # Non-organizational
        ]
        
        for query, lang in test_queries:
            print(f"\nQuery: {query}")
            response = await get_detailed_rag_response(query, lang)
            print(f"Response: {response['response']}")
            print(f"RAG Enhanced: {response['rag_enhanced']}")
            print(f"Sources: {len(response['sources'])}")
    
    asyncio.run(test_bot())
