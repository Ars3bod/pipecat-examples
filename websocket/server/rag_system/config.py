#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
RAG System Configuration
"""

import os
from typing import Dict, List, Any

# RAG System Configuration
RAG_CONFIG = {
    "vector_db": {
        "type": "chromadb",
        "host": os.getenv("CHROMA_HOST", "localhost"),
        "port": int(os.getenv("CHROMA_PORT", "8000")),
        "collection_name": os.getenv("CHROMA_COLLECTION", "organizational_knowledge"),
        "persist_directory": os.getenv("CHROMA_PERSIST_DIR", "./knowledge_base/chroma_db")
    },
    "embedding": {
        "model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "dimensions": int(os.getenv("EMBEDDING_DIMENSIONS", "384")),
        "batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
        "device": os.getenv("EMBEDDING_DEVICE", "cpu")  # cpu or cuda
    },
    "chunking": {
        "chunk_size": int(os.getenv("CHUNK_SIZE", "500")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
        "min_chunk_size": int(os.getenv("MIN_CHUNK_SIZE", "100")),
        "separators": ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    },
    "retrieval": {
        "top_k": int(os.getenv("RETRIEVAL_TOP_K", "5")),
        "similarity_threshold": float(os.getenv("SIMILARITY_THRESHOLD", "0.7")),
        "max_context_length": int(os.getenv("MAX_CONTEXT_LENGTH", "2000")),
        "rerank": os.getenv("RERANK_ENABLED", "true").lower() == "true"
    },
    "documents": {
        "supported_formats": [".pdf", ".docx", ".xlsx", ".txt", ".md"],
        "max_file_size": int(os.getenv("MAX_FILE_SIZE", "10485760")),  # 10MB
        "upload_directory": os.getenv("UPLOAD_DIR", "./knowledge_base/documents"),
        "processed_directory": os.getenv("PROCESSED_DIR", "./knowledge_base/processed"),
        "metadata_directory": os.getenv("METADATA_DIR", "./knowledge_base/metadata")
    },
    "access_control": {
        "allowed_departments": ["HR", "IT", "Admin", "Finance", "Operations"],
        "document_classifications": ["public", "internal", "confidential"],
        "default_classification": "internal",
        "require_approval": os.getenv("REQUIRE_APPROVAL", "false").lower() == "true"
    },
    "languages": {
        "supported": ["ar", "en"],
        "default": "ar",
        "detection_model": "langdetect"
    },
    "llm": {
        "provider": os.getenv("LLM_PROVIDER", "google"),  # google, openai, azure, anthropic
        "model": os.getenv("LLM_MODEL", "gemini-1.5-flash"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1000")),
        "api_key": os.getenv("GOOGLE_API_KEY", ""),
        "api_base": os.getenv("GOOGLE_API_BASE", "https://generativelanguage.googleapis.com/v1beta/"),
        "api_version": os.getenv("GOOGLE_API_VERSION", "v1beta")
    },
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "file": os.getenv("LOG_FILE", "./logs/rag_system.log"),
        "max_size": int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB
        "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
    },
    "monitoring": {
        "enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    }
}

# Document Processing Configuration
DOCUMENT_CONFIG = {
    "pdf": {
        "extract_images": False,
        "extract_tables": True,
        "password_protected": False
    },
    "docx": {
        "extract_images": False,
        "extract_tables": True,
        "preserve_formatting": False
    },
    "xlsx": {
        "sheet_names": None,  # None means all sheets
        "header_row": 0,
        "skip_empty_rows": True
    },
    "txt": {
        "encoding": "utf-8",
        "line_endings": "auto"
    }
}

# Metadata Schema
METADATA_SCHEMA = {
    "required_fields": [
        "document_id",
        "title",
        "department",
        "category",
        "language",
        "created_date",
        "last_updated",
        "version"
    ],
    "optional_fields": [
        "author",
        "tags",
        "classification",
        "expiry_date",
        "approval_status",
        "approver",
        "source_url",
        "file_size",
        "file_hash"
    ],
    "categories": [
        "policies",
        "procedures",
        "guidelines",
        "forms",
        "manuals",
        "announcements",
        "training_materials",
        "faq",
        "contact_info",
        "other"
    ]
}

# RAG Prompt Templates
RAG_PROMPTS = {
    "ar": {
        "system": """أنت مساعده ذكية للموظفين في {organization_name} باسم "{assistant_name}".

القواعد الأساسية:
1. ابدأي دائماً بالترحيب باللغة العربية بقول السلام عليكم (اللهجة السعودية)
2. استمري بالعربية ما لم يطلب الموظف التحدث بالإنجليزية صراحة
3. أجيبي فقط عن الأسئلة المتعلقة بالهيئة والعمل بناءً على المعلومات المتوفرة
4. إذا لم تجدي الإجابة في المعلومات المتوفرة، قولي "آسف، لا أملك هذه المعلومة في قاعدة المعرفة. هل تريد التحويل لموظف بشري؟"
5. لا تجيبي عن أسئلة خارج نطاق الهيئة أبداً
6. كوني مهذبة ومفيدة ومختصرة (جملة أو جملتين كحد أقصى)
7. لا تستخدمي رموز خاصة في الإجابات لأنها ستُحول لصوت
8. عند ذكر الأرقام، استخدمي الأرقام العربية (٠١٢٣٤٥٦٧٨٩) أو النص العربي للأرقام الصغيرة (واحد، اثنان، ثلاثة، إلخ)
9. عند الحديث عن نفسك، استخدمي الضمائر المؤنثة (أنا، أنا مساعده، أنا هنا لمساعدتك)
10. عند تقديم نفسك، قولي دائماً "أنا المُساعِد الرقمي" بدلاً من "المساعدة الذكية"
11. استخدمي المعلومات المتوفرة في السياق للإجابة على الأسئلة بدقة

المعلومات المتوفرة:
{context}

السؤال: {question}""",
        
        "user": "{question}"
    },
    "en": {
        "system": """You are an AI assistant for {organization_name} employees named "{assistant_name}".

Basic Rules:
1. Always start with Arabic greeting (Saudi accent)
2. Continue in Arabic unless employee explicitly requests English
3. Only answer organization-related questions based on available information
4. If you don't find the answer in available information, say "Sorry, I don't have this information in the knowledge base. Would you like me to transfer you to a human?"
5. Never answer non-organizational questions
6. Be polite, helpful, and concise (one or two sentences maximum)
7. Don't use special characters in responses as they'll be converted to speech
8. When mentioning numbers, use Arabic numerals (٠١٢٣٤٥٦٧٨٩) or Arabic text for small numbers (واحد، اثنان، ثلاثة، etc.)
9. When talking about yourself, use feminine pronouns (I am, I'm here to help you)
10. When introducing yourself, always say "I am the Digital Assistant" instead of "the Smart Assistant"
11. Use the available information in the context to answer questions accurately

Available Information:
{context}

Question: {question}""",
        
        "user": "{question}"
    }
}

# Validation Rules
VALIDATION_RULES = {
    "file_size": {
        "max": RAG_CONFIG["documents"]["max_file_size"],
        "min": 1024  # 1KB minimum
    },
    "file_types": RAG_CONFIG["documents"]["supported_formats"],
    "departments": RAG_CONFIG["access_control"]["allowed_departments"],
    "classifications": RAG_CONFIG["access_control"]["document_classifications"],
    "languages": RAG_CONFIG["languages"]["supported"],
    "categories": METADATA_SCHEMA["categories"]
}

def get_config() -> Dict[str, Any]:
    """Get the complete RAG configuration."""
    return RAG_CONFIG

def get_document_config() -> Dict[str, Any]:
    """Get document processing configuration."""
    return DOCUMENT_CONFIG

def get_metadata_schema() -> Dict[str, Any]:
    """Get metadata schema configuration."""
    return METADATA_SCHEMA

def get_rag_prompts() -> Dict[str, Any]:
    """Get RAG prompt templates."""
    return RAG_PROMPTS

def get_validation_rules() -> Dict[str, Any]:
    """Get validation rules."""
    return VALIDATION_RULES

def validate_config() -> List[str]:
    """Validate configuration and return any errors."""
    errors = []
    
    # Check required environment variables based on provider
    provider = os.getenv("LLM_PROVIDER", "google")
    if provider == "google":
        required_vars = ["GOOGLE_API_KEY"]
    elif provider == "openai":
        required_vars = ["OPENAI_API_KEY"]
    else:
        required_vars = ["GOOGLE_API_KEY"]  # Default to Google
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate numeric values
    if RAG_CONFIG["chunking"]["chunk_size"] <= 0:
        errors.append("chunk_size must be positive")
    
    if RAG_CONFIG["chunking"]["chunk_overlap"] < 0:
        errors.append("chunk_overlap must be non-negative")
    
    if RAG_CONFIG["retrieval"]["similarity_threshold"] < 0 or RAG_CONFIG["retrieval"]["similarity_threshold"] > 1:
        errors.append("similarity_threshold must be between 0 and 1")
    
    return errors

if __name__ == "__main__":
    # Test configuration
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Configuration is valid!")
        print(f"Vector DB: {RAG_CONFIG['vector_db']['type']}")
        print(f"Embedding Model: {RAG_CONFIG['embedding']['model']}")
        print(f"Chunk Size: {RAG_CONFIG['chunking']['chunk_size']}")
        print(f"Top K: {RAG_CONFIG['retrieval']['top_k']}")
