#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Content Management Interface for RAG Knowledge Management System
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import shutil

# Local imports
from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .embedding_generator import EmbeddingGenerator
from .config import get_config, get_metadata_schema, VALIDATION_RULES

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentManager:
    """
    Manages content in the RAG knowledge management system.
    """
    
    def __init__(self):
        self.config = get_config()
        self.metadata_schema = get_metadata_schema()
        self.validation_rules = VALIDATION_RULES
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        
        # Create directories
        self._create_directories()
        
        logger.info("Content Manager initialized successfully")
    
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            self.config["documents"]["upload_directory"],
            self.config["documents"]["processed_directory"],
            self.config["documents"]["metadata_directory"]
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def upload_document(self, file_path: str, metadata: Dict[str, Any], user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Upload and process a document.
        
        Args:
            file_path: Path to the document file
            metadata: Document metadata
            user_context: User context (department, role, etc.)
            
        Returns:
            Upload result with document ID and status
        """
        try:
            # Validate metadata
            if not self._validate_metadata(metadata):
                raise ValueError("Invalid metadata")
            
            # Validate file
            if not self._validate_file(file_path):
                raise ValueError("Invalid file")
            
            # Process document
            processed_doc = self.document_processor.process_document(file_path, metadata)
            
            # Generate embeddings
            embeddings = self.embedding_generator.generate_embeddings_batch(
                [chunk["content"] for chunk in processed_doc["chunks"]],
                language=processed_doc["language"]
            )
            
            # Prepare metadata for vector store
            vector_metadata = []
            for chunk in processed_doc["chunks"]:
                chunk_metadata = {
                    **processed_doc["metadata"],
                    "chunk_index": chunk["chunk_index"],
                    "start_char": chunk["start_char"],
                    "end_char": chunk["end_char"]
                }
                vector_metadata.append(chunk_metadata)
            
            # Add to vector store
            success = self.vector_store.add_documents(
                documents=processed_doc["chunks"],
                embeddings=embeddings,
                metadata=vector_metadata
            )
            
            if not success:
                raise RuntimeError("Failed to add documents to vector store")
            
            # Save metadata file
            self._save_metadata_file(processed_doc["document_id"], processed_doc["metadata"])
            
            # Move processed file
            processed_path = self._move_processed_file(file_path, processed_doc["document_id"])
            
            result = {
                "success": True,
                "document_id": processed_doc["document_id"],
                "file_path": processed_path,
                "chunks_count": len(processed_doc["chunks"]),
                "language": processed_doc["language"],
                "metadata": processed_doc["metadata"]
            }
            
            logger.info(f"Document uploaded successfully: {processed_doc['document_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_id": None
            }
    
    def update_document(self, document_id: str, file_path: str, metadata: Dict[str, Any], user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update an existing document.
        
        Args:
            document_id: Document ID to update
            file_path: Path to the new document file
            metadata: Updated metadata
            user_context: User context
            
        Returns:
            Update result
        """
        try:
            # Check if document exists
            existing_chunks = self.vector_store.get_document(document_id)
            if not existing_chunks:
                raise ValueError(f"Document {document_id} not found")
            
            # Upload new version
            upload_result = self.upload_document(file_path, metadata, user_context)
            
            if upload_result["success"]:
                # Delete old version
                self.vector_store.delete_document(document_id)
                
                # Update document ID in new version
                new_document_id = upload_result["document_id"]
                self._update_document_id(new_document_id, document_id)
                
                result = {
                    "success": True,
                    "old_document_id": document_id,
                    "new_document_id": new_document_id,
                    "chunks_count": upload_result["chunks_count"],
                    "language": upload_result["language"]
                }
                
                logger.info(f"Document updated successfully: {document_id} -> {new_document_id}")
                return result
            else:
                return upload_result
                
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_document(self, document_id: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delete a document.
        
        Args:
            document_id: Document ID to delete
            user_context: User context
            
        Returns:
            Delete result
        """
        try:
            # Check if document exists
            existing_chunks = self.vector_store.get_document(document_id)
            if not existing_chunks:
                raise ValueError(f"Document {document_id} not found")
            
            # Delete from vector store
            success = self.vector_store.delete_document(document_id)
            
            if success:
                # Delete metadata file
                self._delete_metadata_file(document_id)
                
                # Delete processed file
                self._delete_processed_file(document_id)
                
                result = {
                    "success": True,
                    "document_id": document_id,
                    "chunks_deleted": len(existing_chunks)
                }
                
                logger.info(f"Document deleted successfully: {document_id}")
                return result
            else:
                raise RuntimeError("Failed to delete document from vector store")
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get document information.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document information
        """
        try:
            # Get chunks from vector store
            chunks = self.vector_store.get_document(document_id)
            
            if not chunks:
                return {"error": "Document not found"}
            
            # Get metadata
            metadata = self._load_metadata_file(document_id)
            
            # Combine chunks
            content = "\n".join([chunk["content"] for chunk in chunks])
            
            result = {
                "document_id": document_id,
                "content": content,
                "chunks_count": len(chunks),
                "metadata": metadata,
                "chunks": chunks
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return {"error": str(e)}
    
    def list_documents(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        List documents with optional filters.
        
        Args:
            filters: Optional filters (department, category, etc.)
            
        Returns:
            List of document information
        """
        try:
            # Get collection stats
            stats = self.vector_store.get_collection_stats()
            
            # Get all documents (simplified approach)
            all_docs = self.vector_store.collection.get(include=["metadatas"])
            
            # Group by document ID
            documents = {}
            for i, metadata in enumerate(all_docs["metadatas"]):
                doc_id = metadata["document_id"]
                if doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "title": metadata["title"],
                        "department": metadata["department"],
                        "category": metadata["category"],
                        "language": metadata["language"],
                        "created_date": metadata["created_date"],
                        "version": metadata["version"],
                        "classification": metadata["classification"],
                        "chunks_count": 0
                    }
                documents[doc_id]["chunks_count"] += 1
            
            # Apply filters
            if filters:
                filtered_docs = []
                for doc in documents.values():
                    if self._matches_filters(doc, filters):
                        filtered_docs.append(doc)
                return filtered_docs
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def search_documents(self, query: str, language: str = "ar", filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search documents.
        
        Args:
            query: Search query
            language: Language code
            filters: Optional filters
            
        Returns:
            List of matching documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(query, language)
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=self.config["retrieval"]["top_k"],
                filters=filters
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document_id": result["metadata"]["document_id"],
                    "title": result["metadata"]["title"],
                    "department": result["metadata"]["department"],
                    "category": result["metadata"]["category"],
                    "content": result["content"],
                    "similarity": result["similarity"],
                    "chunk_index": result["metadata"]["chunk_index"]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            stats = self.vector_store.get_collection_stats()
            
            # Add additional stats
            stats["upload_directory"] = self.config["documents"]["upload_directory"]
            stats["processed_directory"] = self.config["documents"]["processed_directory"]
            stats["metadata_directory"] = self.config["documents"]["metadata_directory"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}")
            return {"error": str(e)}
    
    def backup_knowledge_base(self, backup_path: str) -> Dict[str, Any]:
        """
        Backup the knowledge base.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            Backup result
        """
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup vector store
            vector_backup_path = os.path.join(backup_path, "vector_store.json")
            success = self.vector_store.backup_collection(vector_backup_path)
            
            if success:
                # Backup metadata files
                metadata_backup_path = os.path.join(backup_path, "metadata")
                shutil.copytree(
                    self.config["documents"]["metadata_directory"],
                    metadata_backup_path,
                    dirs_exist_ok=True
                )
                
                result = {
                    "success": True,
                    "backup_path": backup_path,
                    "vector_backup": vector_backup_path,
                    "metadata_backup": metadata_backup_path
                }
                
                logger.info(f"Knowledge base backed up to: {backup_path}")
                return result
            else:
                raise RuntimeError("Failed to backup vector store")
                
        except Exception as e:
            logger.error(f"Error backing up knowledge base: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate document metadata."""
        required_fields = self.metadata_schema["required_fields"]
        
        for field in required_fields:
            if field not in metadata:
                return False
        
        # Validate department
        if metadata["department"] not in self.validation_rules["departments"]:
            return False
        
        # Validate category
        if metadata["category"] not in self.validation_rules["categories"]:
            return False
        
        return True
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file before processing."""
        if not os.path.exists(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        if file_size > self.validation_rules["file_size"]["max"]:
            return False
        
        if file_size < self.validation_rules["file_size"]["min"]:
            return False
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.validation_rules["file_types"]:
            return False
        
        return True
    
    def _save_metadata_file(self, document_id: str, metadata: Dict[str, Any]):
        """Save metadata to file."""
        metadata_path = os.path.join(
            self.config["documents"]["metadata_directory"],
            f"{document_id}.json"
        )
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _load_metadata_file(self, document_id: str) -> Dict[str, Any]:
        """Load metadata from file."""
        metadata_path = os.path.join(
            self.config["documents"]["metadata_directory"],
            f"{document_id}.json"
        )
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    
    def _delete_metadata_file(self, document_id: str):
        """Delete metadata file."""
        metadata_path = os.path.join(
            self.config["documents"]["metadata_directory"],
            f"{document_id}.json"
        )
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
    
    def _move_processed_file(self, original_path: str, document_id: str) -> str:
        """Move processed file to processed directory."""
        file_extension = os.path.splitext(original_path)[1]
        processed_path = os.path.join(
            self.config["documents"]["processed_directory"],
            f"{document_id}{file_extension}"
        )
        
        shutil.move(original_path, processed_path)
        return processed_path
    
    def _delete_processed_file(self, document_id: str):
        """Delete processed file."""
        processed_dir = self.config["documents"]["processed_directory"]
        
        # Find file with document ID
        for filename in os.listdir(processed_dir):
            if filename.startswith(document_id):
                file_path = os.path.join(processed_dir, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                break
    
    def _update_document_id(self, new_document_id: str, old_document_id: str):
        """Update document ID in vector store."""
        # This is a simplified approach - in production, you might want to update the IDs directly
        pass
    
    def _matches_filters(self, document: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches filters."""
        for key, value in filters.items():
            if key in document:
                if isinstance(value, list):
                    if document[key] not in value:
                        return False
                else:
                    if document[key] != value:
                        return False
        return True

# Example usage
if __name__ == "__main__":
    # Initialize content manager
    content_manager = ContentManager()
    
    # Get knowledge base stats
    stats = content_manager.get_knowledge_base_stats()
    print(f"Knowledge base stats: {stats}")
    
    # List documents
    documents = content_manager.list_documents()
    print(f"Total documents: {len(documents)}")
    
    # Example search
    # results = content_manager.search_documents("سياسات الإجازات", language="ar")
    # print(f"Search results: {len(results)} documents found")
