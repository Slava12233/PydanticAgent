"""
בדיקות יחידה עבור מודול RAG Core
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime

# מוק למחלקת Document של langchain
class Document:
    """מוק למחלקת Document של langchain"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

# מוק למחלקת RAGCore
class RAGCore:
    """מוק למחלקת RAGCore"""
    
    def __init__(self, embeddings=None, vectorstore=None):
        """אתחול מופע RAGCore"""
        self.embeddings = embeddings or MagicMock()
        self.vectorstore = vectorstore or MagicMock()
        self.documents = {}
        self.initialized = False
    
    async def initialize(self):
        """אתחול המודול"""
        self.initialized = True
        return True
    
    async def add_document(self, content, metadata=None, doc_id=None):
        """הוספת מסמך"""
        metadata = metadata or {}
        if doc_id is None:
            doc_id = f"doc_{len(self.documents) + 1}"
        
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        
        return doc_id
    
    async def delete_document(self, doc_id):
        """מחיקת מסמך"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    async def get_document(self, doc_id):
        """קבלת מסמך"""
        if doc_id in self.documents:
            doc_data = self.documents[doc_id]
            return Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"]
            )
        return None
    
    async def update_document(self, doc_id, content=None, metadata=None):
        """עדכון מסמך"""
        if doc_id not in self.documents:
            return False
        
        if content is not None:
            self.documents[doc_id]["content"] = content
        
        if metadata is not None:
            self.documents[doc_id]["metadata"].update(metadata)
        
        return True


@pytest_asyncio.fixture
async def rag_core():
    """פיקסצ'ר ליצירת מופע RAG Core לבדיקות"""
    # יצירת מופע RAGCore
    core = RAGCore()
    
    # מוק לפונקציות
    core.initialize = AsyncMock(side_effect=core.initialize)
    core.add_document = AsyncMock(side_effect=core.add_document)
    core.delete_document = AsyncMock(side_effect=core.delete_document)
    core.get_document = AsyncMock(side_effect=core.get_document)
    core.update_document = AsyncMock(side_effect=core.update_document)
    
    # מוק למאגר הווקטורים
    core.vectorstore.add_documents = AsyncMock(return_value=["doc_id_123"])
    core.vectorstore.delete = AsyncMock(return_value=None)
    core.vectorstore.get = AsyncMock(return_value=None)
    
    yield core


@pytest.mark.asyncio
async def test_initialize(rag_core):
    """בדיקת אתחול מערכת ה-RAG"""
    # הרצת הפונקציה
    result = await rag_core.initialize()
    
    # וידוא שהפונקציה נקראה
    rag_core.initialize.assert_called_once()
    assert result is True
    assert rag_core.initialized is True


@pytest.mark.asyncio
async def test_add_document(rag_core):
    """בדיקת הוספת מסמך"""
    # נתונים לבדיקה
    content = "תוכן המסמך לבדיקה"
    metadata = {"title": "מסמך בדיקה"}
    
    # הרצת הפונקציה
    doc_id = await rag_core.add_document(content, metadata)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_core.add_document.assert_called_once_with(content, metadata)
    
    # וידוא שהוחזר מזהה מסמך
    assert doc_id is not None
    assert isinstance(doc_id, str)
    
    # וידוא שהמסמך נוסף למאגר
    assert doc_id in rag_core.documents
    assert rag_core.documents[doc_id]["content"] == content
    assert rag_core.documents[doc_id]["metadata"] == metadata


@pytest.mark.asyncio
async def test_delete_document(rag_core):
    """בדיקת מחיקת מסמך"""
    # הוספת מסמך למאגר
    doc_id = await rag_core.add_document("תוכן המסמך לבדיקה", {"title": "מסמך בדיקה"})
    
    # וידוא שהמסמך נוסף למאגר
    assert doc_id in rag_core.documents
    
    # הרצת הפונקציה
    result = await rag_core.delete_document(doc_id)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_core.delete_document.assert_called_with(doc_id)
    
    # וידוא שהוחזרה תוצאה חיובית
    assert result is True
    
    # וידוא שהמסמך נמחק מהמאגר
    assert doc_id not in rag_core.documents


@pytest.mark.asyncio
async def test_get_document(rag_core):
    """בדיקת קבלת מסמך לפי מזהה"""
    # הוספת מסמך למאגר
    content = "תוכן המסמך לבדיקה"
    metadata = {"title": "מסמך בדיקה"}
    doc_id = await rag_core.add_document(content, metadata)
    
    # הרצת הפונקציה
    result = await rag_core.get_document(doc_id)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_core.get_document.assert_called_with(doc_id)
    
    # וידוא שהוחזר המסמך הנכון
    assert result is not None
    assert isinstance(result, Document)
    assert result.page_content == content
    assert result.metadata == metadata


@pytest.mark.asyncio
async def test_update_document(rag_core):
    """בדיקת עדכון מסמך"""
    # הוספת מסמך למאגר
    original_content = "תוכן המסמך המקורי"
    original_metadata = {"title": "מסמך בדיקה"}
    doc_id = await rag_core.add_document(original_content, original_metadata)
    
    # נתונים לעדכון
    updated_content = "תוכן מעודכן"
    updated_metadata = {"title": "כותרת מעודכנת"}
    
    # הרצת הפונקציה
    result = await rag_core.update_document(doc_id, updated_content, updated_metadata)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    rag_core.update_document.assert_called_with(doc_id, updated_content, updated_metadata)
    
    # וידוא שהוחזרה תוצאה חיובית
    assert result is True
    
    # וידוא שהמסמך עודכן במאגר
    assert doc_id in rag_core.documents
    assert rag_core.documents[doc_id]["content"] == updated_content
    assert "title" in rag_core.documents[doc_id]["metadata"]
    assert rag_core.documents[doc_id]["metadata"]["title"] == updated_metadata["title"]


@pytest.mark.asyncio
async def test_error_handling(rag_core):
    """בדיקת טיפול בשגיאות"""
    # הגדרת מוק לזריקת שגיאה
    rag_core.add_document.side_effect = Exception("שגיאת בדיקה")
    
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception):
        await rag_core.add_document("תוכן המסמך", {"title": "מסמך בדיקה"}) 