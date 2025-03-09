"""
מודול שירותי AI - מכיל שירותים שונים לעבודה עם מודלי AI
"""

# ייבוא שירותי RAG
from src.services.ai.rag import (
    RAGCore,
    RAGSearch,
    RAGDocument,
    generate_document_id,
    clean_text,
    extract_keywords,
    chunk_text,
    merge_metadata
)

# ייבוא שירותי זיכרון והקשר
from src.services.ai.memory_service import (
    memory_service,
    MemoryService,
    ContextData
)

# יצירת מופע RAG מוכן לשימוש
rag_core = RAGCore()
rag_search = RAGSearch()
rag_document = RAGDocument()

# פונקציות נוחות לשימוש ישיר
async def add_document_from_file(file_path: str, title: str = None, source: str = None, metadata: dict = None) -> str:
    """פונקציית נוחות להוספת מסמך מקובץ"""
    return await rag_document.add_document_from_file(file_path, title, source, metadata)

async def add_document_from_text(text: str, title: str, source: str = None, metadata: dict = None) -> str:
    """פונקציית נוחות להוספת מסמך מטקסט"""
    return await rag_document.add_document_from_text(text, title, source, metadata)

async def search_documents(query: str, limit: int = 5, min_score: float = 0.7, filters: dict = None) -> list:
    """פונקציית נוחות לחיפוש במסמכים"""
    return await rag_search.semantic_search(query, k=limit, min_relevance_score=min_score, filter_metadata=filters)

async def list_documents() -> list:
    """פונקציית נוחות לקבלת רשימת המסמכים"""
    return await rag_document.list_documents()

async def delete_document(doc_id: str) -> bool:
    """פונקציית נוחות למחיקת מסמך"""
    return await rag_document.delete_document(doc_id)

async def get_document_by_id(doc_id: str) -> dict:
    """פונקציית נוחות לקבלת מסמך לפי מזהה"""
    return await rag_document.get_document_by_id(doc_id)

__all__ = [
    # מחלקות RAG
    'RAGCore',
    'RAGSearch',
    'RAGDocument',
    
    # פונקציות עזר
    'generate_document_id',
    'clean_text',
    'extract_keywords',
    'chunk_text',
    'merge_metadata',
    
    # מופעים מוכנים לשימוש
    'rag_core',
    'rag_search',
    'rag_document',
    
    # פונקציות נוחות
    'add_document_from_file',
    'add_document_from_text',
    'search_documents',
    'list_documents',
    'delete_document',
    'get_document_by_id',
    
    # שירותי זיכרון והקשר
    'memory_service',
    'MemoryService',
    'ContextData'
] 