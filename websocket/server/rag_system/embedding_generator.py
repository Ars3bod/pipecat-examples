#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Embedding Generator for RAG Knowledge Management System
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

# Configuration
from .config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Generates embeddings for text using sentence transformers.
    """
    
    def __init__(self):
        self.config = get_config()
        self.model = None
        self.device = self.config["embedding"]["device"]
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            model_name = self.config["embedding"]["model"]
            
            # Initialize model
            self.model = SentenceTransformer(model_name)
            
            # Move to device if available
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to(self.device)
                logger.info("Using CUDA for embeddings")
            else:
                logger.info("Using CPU for embeddings")
            
            logger.info(f"Initialized embedding model: {model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
    
    def generate_embedding(self, text: str, language: str = "ar") -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            language: Language code ('ar' or 'en')
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # Preprocess text based on language
            processed_text = self._preprocess_text(text, language)
            
            # Generate embedding
            embedding = self.model.encode(processed_text, convert_to_tensor=False)
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], language: str = "ar") -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            language: Language code ('ar' or 'en')
            
        Returns:
            List of embedding vectors
        """
        try:
            # Preprocess texts
            processed_texts = [self._preprocess_text(text, language) for text in texts]
            
            # Generate embeddings in batch
            batch_size = self.config["embedding"]["batch_size"]
            embeddings = []
            
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, convert_to_tensor=False)
                embeddings.extend(batch_embeddings.tolist())
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def generate_query_embedding(self, query: str, language: str = "ar") -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query
            language: Language code ('ar' or 'en')
            
        Returns:
            Query embedding vector
        """
        try:
            # Preprocess query
            processed_query = self._preprocess_query(query, language)
            
            # Generate embedding
            embedding = self.model.encode(processed_query, convert_to_tensor=False)
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str, language: str) -> str:
        """
        Preprocess text before embedding generation.
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            Preprocessed text
        """
        # Remove extra whitespace
        text = text.strip()
        
        # Remove special characters but keep text content
        if language == "ar":
            # Keep Arabic characters, numbers, and basic punctuation
            import re
            text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\.\,\!\?\:\;\(\)]', '', text)
        else:
            # Keep English characters, numbers, and basic punctuation
            import re
            text = re.sub(r'[^a-zA-Z0-9\s\.\,\!\?\:\;\(\)]', '', text)
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _preprocess_query(self, query: str, language: str) -> str:
        """
        Preprocess search query before embedding generation.
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            Preprocessed query
        """
        # Basic preprocessing
        processed_query = self._preprocess_text(query, language)
        
        # For queries, we might want to add some context
        if language == "ar":
            # Add context for Arabic queries
            processed_query = f"سؤال: {processed_query}"
        else:
            # Add context for English queries
            processed_query = f"Question: {processed_query}"
        
        return processed_query
    
    def get_embedding_dimensions(self) -> int:
        """Get the dimension of embeddings."""
        return self.config["embedding"]["dimensions"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.config["embedding"]["model"],
            "dimensions": self.config["embedding"]["dimensions"],
            "device": self.device,
            "batch_size": self.config["embedding"]["batch_size"]
        }
    
    def test_embedding(self, text: str = "مرحبا بك في الهيئة") -> Dict[str, Any]:
        """
        Test embedding generation with sample text.
        
        Args:
            text: Test text
            
        Returns:
            Test results
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Test results
            results = {
                "text": text,
                "embedding_length": len(embedding),
                "embedding_dimensions": self.get_embedding_dimensions(),
                "embedding_sample": embedding[:5],  # First 5 values
                "model_info": self.get_model_info()
            }
            
            logger.info(f"Embedding test successful: {len(embedding)} dimensions")
            return results
            
        except Exception as e:
            logger.error(f"Embedding test failed: {str(e)}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    # Initialize embedding generator
    generator = EmbeddingGenerator()
    
    # Test embedding generation
    test_results = generator.test_embedding("مرحبا بك في الهيئة")
    print(f"Test results: {test_results}")
    
    # Test batch embedding
    texts = [
        "مرحبا بك في الهيئة",
        "كيف يمكنني مساعدتك؟",
        "سياسات الموارد البشرية"
    ]
    
    embeddings = generator.generate_embeddings_batch(texts, language="ar")
    print(f"Generated {len(embeddings)} embeddings")
    
    # Test query embedding
    query_embedding = generator.generate_query_embedding("ما هي سياسات الإجازات؟", language="ar")
    print(f"Query embedding length: {len(query_embedding)}")
