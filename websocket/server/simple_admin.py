#!/usr/bin/env python3
"""
Simplified RAG Admin Interface
"""

import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from dotenv import load_dotenv
load_dotenv(override=True)

# Initialize FastAPI app
app = FastAPI(title="Simple RAG Admin", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/admin", response_class=HTMLResponse)
async def admin_interface(request: Request):
    """Serve the simplified admin interface."""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/documents")
async def get_documents():
    """Get documents - simplified version."""
    return {
        "success": True,
        "documents": [],
        "total": 0,
        "message": "نظام مستقر و جاهز للاستخدام"
    }

@app.post("/admin/upload-document")
async def upload_document(data: dict):
    """Upload document - simplified version."""
    return {
        "success": True,
        "document_id": "demo_123",
        "message": "تم تحميل الوثيقة بنجاح!"
    }

@app.post("/admin/test-query")
async def test_query(data: dict):
    """Test query - simplified version."""
    return {
        "success": True,
        "query": data.get("query", ""),
        "language": data.get("language", "ar"),
        "answer": "بناءً على المعلومات المتوفرة في قاعدة المعرفة، هذا رد تجريبي من النظام.",
        "sources": [],
        "confidence": 0.95,
        "rag_enhanced": True
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Simple RAG Admin Interface", "admin_url": "/admin"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple RAG Admin Interface...")
    print(f"📊 Admin Panel: http://localhost:8000/admin")
    uvicorn.run(app, host="0.0.0.0", port=8000)
