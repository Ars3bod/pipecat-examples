#!/usr/bin/env python3
"""
Simple startup script for RAG Admin Interface
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

def check_system():
    """Check if the system is ready."""
    print("🔍 Checking RAG system readiness...")
    
    # Check if GOOGLE_API_KEY is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("   Please add GOOGLE_API_KEY to your .env file")
        return False
    
    # Check if directories exist
    required_dirs = ['knowledge_base/chroma_db', 'knowledge_base/documents', 
                    'knowledge_base/processed', 'knowledge_base/metadata', 'logs']
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ System is ready!")
    return True

def main():
    """Main startup function."""
    print("🚀 RAG Knowledge Management System")
    print("=" * 50)
    
    if not check_system():
        print("\n❌ System not ready. Please fix the issues above.")
        sys.exit(1)
    
    print("\n📋 What you can do:")
    print("1. 📖 Open Admin Interface: http://localhost:8000/admin")
    print("2. 📊 View API Documentation: http://localhost:8000/docs")
    print("3. 🧪 Test RAG Queries directly")
    print("4. 📚 Upload organizational documents")
    
    print("\n🎯 Quick Start:")
    print("1. Start the admin interface: uvicorn admin_api:app --host 0.0.0.0 --port 8000")
    print("2. Open http://localhost:8000/admin in your browser")
    print("3. Upload some sample documents")
    print("4. Test your knowledge base!")
    
    # Start admin interface
    print("\n🌐 Starting Admin Interface...\n")
    
    import uvicorn
    try:
        uvicorn.run("admin_api:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Admin Interface stopped.")

if __name__ == "__main__":
    main()
