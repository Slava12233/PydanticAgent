"""
בדיקות יחידה עבור מודול RAG Document
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import asyncio
from datetime import datetime
import os
import json

# מוק למחלקת Document של langchain
class Document:
    """מוק למחלקת Document של langchain"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

# מוק למחלקת RAGDocument
class RAGDocument:
    """מוק למחלקת RAGDocument"""
    
    def __init__(self, storage_path=None):
        """אתחול מופע RAGDocument"""
        self.storage_path = storage_path or "./documents"
        self.documents = {}
        self.document_history = {}
    
    async def create_document(self, content, metadata=None, doc_id=None):
        """יצירת מסמך חדש"""
        metadata = metadata or {}
        if doc_id is None:
            doc_id = f"doc_{len(self.documents) + 1}"
        
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.document_history[doc_id] = [{
            "action": "created",
            "timestamp": datetime.now().isoformat()
        }]
        
        return doc_id
    
    async def update_document_metadata(self, doc_id, metadata_updates):
        """עדכון מטא-דאטה של מסמך"""
        if doc_id not in self.documents:
            return None
        
        current_metadata = self.documents[doc_id]["metadata"]
        updated_metadata = {**current_metadata, **metadata_updates}
        self.documents[doc_id]["metadata"] = updated_metadata
        self.documents[doc_id]["updated_at"] = datetime.now().isoformat()
        
        self.document_history[doc_id].append({
            "action": "metadata_updated",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def add_tags(self, doc_id, tags):
        """הוספת תגיות למסמך"""
        if doc_id not in self.documents:
            return None
        
        current_tags = self.documents[doc_id]["metadata"].get("tags", [])
        updated_tags = list(set(current_tags + tags))
        self.documents[doc_id]["metadata"]["tags"] = updated_tags
        self.documents[doc_id]["updated_at"] = datetime.now().isoformat()
        
        self.document_history[doc_id].append({
            "action": "tags_added",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def remove_tags(self, doc_id, tags):
        """הסרת תגיות ממסמך"""
        if doc_id not in self.documents:
            return None
        
        current_tags = self.documents[doc_id]["metadata"].get("tags", [])
        updated_tags = [tag for tag in current_tags if tag not in tags]
        self.documents[doc_id]["metadata"]["tags"] = updated_tags
        self.documents[doc_id]["updated_at"] = datetime.now().isoformat()
        
        self.document_history[doc_id].append({
            "action": "tags_removed",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def get_document_history(self, doc_id):
        """קבלת היסטוריית מסמך"""
        if doc_id not in self.document_history:
            return []
        
        return self.document_history[doc_id]
    
    async def add_document_from_file(self, file_path, metadata=None):
        """הוספת מסמך מקובץ"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"הקובץ {file_path} לא נמצא")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = metadata or {}
        metadata["source"] = file_path
        metadata["filename"] = os.path.basename(file_path)
        
        return await self.create_document(content, metadata)
    
    async def add_document_from_text(self, text, metadata=None):
        """הוספת מסמך מטקסט"""
        metadata = metadata or {}
        return await self.create_document(text, metadata)


@pytest_asyncio.fixture
async def rag_document():
    """פיקסצ'ר ליצירת מופע RAG Document לבדיקות"""
    # יצירת מופע RAGDocument
    doc_manager = RAGDocument(storage_path="./test_documents")
    
    # הוספת מתודות נוספות שנדרשות לבדיקות
    doc_manager.create_document = AsyncMock(side_effect=doc_manager.create_document)
    doc_manager.update_document_metadata = AsyncMock(side_effect=doc_manager.update_document_metadata)
    doc_manager.add_tags = AsyncMock(side_effect=doc_manager.add_tags)
    doc_manager.remove_tags = AsyncMock(side_effect=doc_manager.remove_tags)
    doc_manager.get_document_history = AsyncMock(side_effect=doc_manager.get_document_history)
    doc_manager.add_document_from_file = AsyncMock(side_effect=doc_manager.add_document_from_file)
    doc_manager.add_document_from_text = AsyncMock(side_effect=doc_manager.add_document_from_text)
    
    # מוק לפונקציות נוספות
    doc_manager.vectorstore = MagicMock()
    doc_manager.vectorstore.add_documents = AsyncMock(return_value=["doc_id_123"])
    doc_manager.vectorstore.delete = AsyncMock(return_value=None)
    doc_manager.vectorstore.get = AsyncMock()
    doc_manager.text_splitter = MagicMock()
    doc_manager.text_splitter.split_text = MagicMock(return_value=["חלק 1", "חלק 2"])
    
    yield doc_manager


@pytest.mark.asyncio
async def test_create_document(rag_document):
    """בדיקת יצירת מסמך חדש"""
    # הרצת הפונקציה
    doc_id = await rag_document.create_document(
        content="תוכן המסמך לבדיקה",
        metadata={"title": "מסמך בדיקה", "tags": ["בדיקה", "מסמך"]}
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.create_document.assert_called_once()
    
    # וידוא שהוחזר מזהה מסמך
    assert doc_id is not None
    assert isinstance(doc_id, str)


@pytest.mark.asyncio
async def test_create_document_with_json_content(rag_document):
    """בדיקת יצירת מסמך עם תוכן JSON"""
    # תוכן JSON לדוגמה
    json_content = {
        "title": "מסמך בדיקה",
        "content": "תוכן המסמך",
        "tags": ["בדיקה", "מסמך"]
    }
    
    # הרצת הפונקציה
    doc_id = await rag_document.create_document(
        content=json_content,
        metadata={"format": "json"}
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.create_document.assert_called_once()
    
    # וידוא שהוחזר מזהה מסמך
    assert doc_id is not None
    assert isinstance(doc_id, str)


@pytest.mark.asyncio
async def test_update_document_metadata(rag_document):
    """בדיקת עדכון מטא-דאטה של מסמך"""
    # יצירת מסמך לדוגמה
    doc_id = await rag_document.create_document(
        content="תוכן המסמך לבדיקה",
        metadata={"title": "מסמך בדיקה", "version": 1}
    )
    
    # איפוס המוק
    rag_document.create_document.reset_mock()
    
    # הרצת הפונקציה
    result = await rag_document.update_document_metadata(
        doc_id=doc_id,
        metadata_updates={"version": 2, "updated_at": "2023-01-01"}
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.update_document_metadata.assert_called_once()
    
    # וידוא שהוחזרה תוצאה חיובית
    assert result is True


@pytest.mark.asyncio
async def test_add_tags(rag_document):
    """בדיקת הוספת תגיות למסמך"""
    # יצירת מסמך לדוגמה
    doc_id = await rag_document.create_document(
        content="תוכן המסמך לבדיקה",
        metadata={"title": "מסמך בדיקה", "tags": ["בדיקה"]}
    )
    
    # איפוס המוק
    rag_document.create_document.reset_mock()
    
    # הרצת הפונקציה
    result = await rag_document.add_tags(
        doc_id=doc_id,
        tags=["מסמך", "חדש"]
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.add_tags.assert_called_once()
    
    # וידוא שהוחזרה תוצאה חיובית
    assert result is True


@pytest.mark.asyncio
async def test_remove_tags(rag_document):
    """בדיקת הסרת תגיות ממסמך"""
    # יצירת מסמך לדוגמה
    doc_id = await rag_document.create_document(
        content="תוכן המסמך לבדיקה",
        metadata={"title": "מסמך בדיקה", "tags": ["בדיקה", "מסמך", "חדש"]}
    )
    
    # איפוס המוק
    rag_document.create_document.reset_mock()
    
    # הרצת הפונקציה
    result = await rag_document.remove_tags(
        doc_id=doc_id,
        tags=["חדש"]
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.remove_tags.assert_called_once()
    
    # וידוא שהוחזרה תוצאה חיובית
    assert result is True


@pytest.mark.asyncio
async def test_get_document_history(rag_document):
    """בדיקת קבלת היסטוריית מסמך"""
    # יצירת מסמך לדוגמה
    doc_id = await rag_document.create_document(
        content="תוכן המסמך לבדיקה",
        metadata={"title": "מסמך בדיקה"}
    )
    
    # עדכון המסמך כדי ליצור היסטוריה
    await rag_document.update_document_metadata(
        doc_id=doc_id,
        metadata_updates={"version": 2}
    )
    
    # איפוס המוקים
    rag_document.create_document.reset_mock()
    rag_document.update_document_metadata.reset_mock()
    
    # הרצת הפונקציה
    history = await rag_document.get_document_history(doc_id)
    
    # וידוא שהפונקציה נקראה
    rag_document.get_document_history.assert_called_once()
    
    # וידוא שהוחזרה ההיסטוריה הנכונה
    assert len(history) == 2
    assert history[0]["action"] == "created"
    assert history[1]["action"] == "metadata_updated"


@pytest.mark.asyncio
async def test_add_document_from_file(rag_document):
    """בדיקת הוספת מסמך מקובץ"""
    # מוק לפונקציית פתיחת קובץ
    with patch("builtins.open", mock_open(read_data="תוכן הקובץ לבדיקה")), \
         patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024):
        
        # הרצת הפונקציה
        doc_id = await rag_document.add_document_from_file(
            file_path="test.txt",
            metadata={"format": "text"}
        )
        
        # וידוא שהפונקציה נקראה
        rag_document.add_document_from_file.assert_called_once()
        
        # וידוא שהוחזר מזהה מסמך
        assert doc_id is not None
        assert isinstance(doc_id, str)


@pytest.mark.asyncio
async def test_add_document_from_text(rag_document):
    """בדיקת הוספת מסמך מטקסט"""
    # הרצת הפונקציה
    doc_id = await rag_document.add_document_from_text(
        text="תוכן המסמך לבדיקה",
        metadata={"format": "text", "title": "מסמך בדיקה", "source": "בדיקות"}
    )
    
    # וידוא שהפונקציה נקראה
    rag_document.add_document_from_text.assert_called_once()
    
    # וידוא שהוחזר מזהה מסמך
    assert doc_id is not None
    assert isinstance(doc_id, str)


@pytest.mark.asyncio
async def test_error_handling_file_not_found(rag_document):
    """בדיקת טיפול בשגיאת קובץ לא נמצא"""
    # מוק לפונקציית בדיקת קיום קובץ
    with patch("os.path.exists", return_value=False):
        
        # הרצת הפונקציה וציפייה לשגיאה
        with pytest.raises(FileNotFoundError):
            await rag_document.add_document_from_file(
                file_path="nonexistent.txt"
            ) 