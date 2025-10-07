#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Vector Store Implementation using ChromaDB for RAG Knowledge Management System
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
import numpy as np

# Configuration
from .config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """
    ChromaDB-based vector store for storing and retrieving document embeddings.
    """
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persist directory if it doesn't exist
            persist_directory = self.config["vector_db"]["persist_directory"]
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            collection_name = self.config["vector_db"]["collection_name"]
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Organizational knowledge base"}
            )
            
            logger.info(f"Initialized ChromaDB collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document chunks
            embeddings: List of embeddings for each chunk
            metadata: List of metadata for each chunk
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare data for ChromaDB
            ids = []
            contents = []
            metadatas = []
            
            for i, (doc, embedding, meta) in enumerate(zip(documents, embeddings, metadata)):
                # Generate unique ID
                chunk_id = f"{meta['document_id']}_{doc['chunk_index']}"
                ids.append(chunk_id)
                
                # Extract content
                contents.append(doc['content'])
                
                # Prepare metadata (ChromaDB has specific requirements)
                chroma_metadata = {
                    "document_id": meta["document_id"],
                    "chunk_index": doc["chunk_index"],
                    "title": meta.get("title", ""),
                    "department": meta.get("department", ""),
                    "category": meta.get("category", ""),
                    "language": meta.get("language", "ar"),
                    "created_date": meta.get("created_date", ""),
                    "version": meta.get("version", "1.0"),
                    "classification": meta.get("classification", "internal")
                }
                metadatas.append(chroma_metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of similar documents with scores
        """
        try:
            if top_k is None:
                top_k = self.config["retrieval"]["top_k"]
            
            # Prepare where clause for filtering
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    if isinstance(value, list):
                        where_clause[key] = {"$in": value}
                    else:
                        where_clause[key] = value
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                result = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                }
                formatted_results.append(result)
            
            # Filter by similarity threshold
            threshold = self.config["retrieval"]["similarity_threshold"]
            filtered_results = [r for r in formatted_results if r["similarity"] >= threshold]
            
            logger.info(f"Found {len(filtered_results)} similar documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def get_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of document chunks
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            chunks = []
            for i in range(len(results["ids"])):
                chunk = {
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                chunks.append(chunk)
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x["metadata"]["chunk_index"])
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunk IDs for the document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["ids"]
            )
            
            if results["ids"]:
                # Delete chunks
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def update_document(self, document_id: str, documents: List[Dict[str, Any]], embeddings: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        Update a document by deleting old chunks and adding new ones.
        
        Args:
            document_id: Document ID
            documents: List of new document chunks
            embeddings: List of embeddings for new chunks
            metadata: List of metadata for new chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing chunks
            self.delete_document(document_id)
            
            # Add new chunks
            return self.add_documents(documents, embeddings, metadata)
            
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample = self.collection.get(limit=100, include=["metadatas"])
            
            # Analyze metadata
            departments = {}
            categories = {}
            languages = {}
            
            for meta in sample["metadatas"]:
                dept = meta.get("department", "unknown")
                cat = meta.get("category", "unknown")
                lang = meta.get("language", "unknown")
                
                departments[dept] = departments.get(dept, 0) + 1
                categories[cat] = categories.get(cat, 0) + 1
                languages[lang] = languages.get(lang, 0) + 1
            
            stats = {
                "total_documents": count,
                "departments": departments,
                "categories": categories,
                "languages": languages,
                "sample_size": len(sample["metadatas"])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    def reset_collection(self) -> bool:
        """
        Reset the collection (delete all documents).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(self.config["vector_db"]["collection_name"])
            self._initialize_client()
            logger.info("Collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False
    
    def backup_collection(self, backup_path: str) -> bool:
        """
        Backup the collection to a file.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all documents
            all_docs = self.collection.get(include=["documents", "metadatas", "embeddings"])
            
            # Save to file (simplified backup)
            import json
            backup_data = {
                "ids": all_docs["ids"],
                "documents": all_docs["documents"],
                "metadatas": all_docs["metadatas"],
                "embeddings": all_docs["embeddings"]
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Collection backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up collection: {str(e)}")
            return False

# Example usage
if __name__ == "__main__":
    # Initialize vector store
    vector_store = VectorStore()
    
    # Get collection stats
    stats = vector_store.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    # Example search (would need actual embedding)
    # results = vector_store.search(query_embedding=[0.1] * 384, top_k=5)
    # print(f"Search results: {len(results)} documents found")
