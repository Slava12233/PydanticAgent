import pytest
import pytest_asyncio
from datetime import datetime, timezone
import json
from src.services.rag_service import RAGService
from src.database.models import Document, DocumentChunk
from src.database.database import Database

db = Database()

@pytest_asyncio.fixture
async def rag_service():
    """פיקסצ'ר ליצירת מופע של RAG Service לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת שירות חדש
    service = RAGService()
    
    yield service
    
    # ניקוי אחרי כל בדיקה
    await service.delete_all_documents()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_add_document_with_chunks(rag_service):
    """בדיקת הוספת מסמך עם חלוקה לקטעים"""
    # הכנת תוכן ארוך שיחולק לקטעים
    content = "\n\n".join([
        "פסקה ראשונה עם תוכן מעניין.",
        "פסקה שנייה עם תוכן אחר לגמרי.",
        "פסקה שלישית שמדברת על נושא חדש.",
        "פסקה רביעית שמסכמת את הכל."
    ])
    
    doc_id = await rag_service.add_document_from_text(
        content=content,
        title="מסמך עם קטעים",
        source="test"
    )
    
    # בדיקה שהמסמך נוצר
    assert doc_id is not None
    
    # בדיקה שהקטעים נוצרו
    doc = await rag_service.get_document_by_id(doc_id)
    assert doc is not None
    assert len(doc["chunks"]) > 1  # וידוא שיש יותר מקטע אחד

@pytest.mark.asyncio
async def test_metadata_handling(rag_service):
    """בדיקת טיפול במטא-דאטה מורכב"""
    # מטא-דאטה מורכב
    metadata = {
        "tags": ["חשוב", "דחוף", "לטיפול"],
        "priority": 1,
        "due_date": "2024-12-31",
        "nested": {
            "key1": "value1",
            "key2": ["a", "b", "c"]
        }
    }
    
    # הוספת מסמך עם מטא-דאטה
    doc_id = await rag_service.add_document_from_text(
        content="תוכן לבדיקה",
        title="מסמך עם מטא-דאטה",
        source="test",
        metadata=metadata
    )
    
    # בדיקת שמירת המטא-דאטה
    doc = await rag_service.get_document_by_id(doc_id)
    assert doc is not None
    assert doc["metadata"]["tags"] == metadata["tags"]
    assert doc["metadata"]["priority"] == metadata["priority"]
    assert doc["metadata"]["nested"]["key1"] == metadata["nested"]["key1"]

@pytest.mark.asyncio
async def test_concurrent_operations(rag_service):
    """בדיקת פעולות מקביליות"""
    import asyncio
    
    # הוספת מספר מסמכים במקביל
    docs = [
        ("מסמך 1", "תוכן 1"),
        ("מסמך 2", "תוכן 2"),
        ("מסמך 3", "תוכן 3"),
        ("מסמך 4", "תוכן 4"),
        ("מסמך 5", "תוכן 5")
    ]
    
    async def add_doc(title, content):
        return await rag_service.add_document_from_text(
            content=content,
            title=title,
            source="test"
        )
    
    # הוספת כל המסמכים במקביל
    tasks = [add_doc(title, content) for title, content in docs]
    doc_ids = await asyncio.gather(*tasks)
    
    # וידוא שכל המסמכים נוספו
    assert all(doc_id is not None for doc_id in doc_ids)
    assert len(doc_ids) == len(docs)

@pytest.mark.asyncio
async def test_search_with_special_characters(rag_service):
    """בדיקת חיפוש עם תווים מיוחדים"""
    # הוספת מסמך עם תווים מיוחדים
    content = "תוכן עם תווים מיוחדים: !@#$%^&*()_+-=[]{}|;:'\",.<>/?"
    doc_id = await rag_service.add_document_from_text(
        content=content,
        title="מסמך מיוחד",
        source="test"
    )
    
    # חיפוש עם תווים מיוחדים
    results = await rag_service.search_documents("!@#$%^&*()")
    assert len(results) > 0
    assert results[0]["id"] == doc_id

@pytest.mark.asyncio
async def test_large_document_handling(rag_service):
    """בדיקת טיפול במסמך גדול"""
    # יצירת תוכן גדול
    large_content = "שורה במסמך. " * 1000  # 10000 תווים בערך
    
    # הוספת המסמך הגדול
    doc_id = await rag_service.add_document_from_text(
        content=large_content,
        title="מסמך גדול",
        source="test"
    )
    
    # בדיקה שהמסמך נשמר ונחלק לקטעים
    doc = await rag_service.get_document_by_id(doc_id)
    assert doc is not None
    assert len(doc["content"]) == len(large_content)
    assert len(doc["chunks"]) > 1

@pytest.mark.asyncio
async def test_document_versioning(rag_service):
    """בדיקת גרסאות של מסמך"""
    # יצירת מסמך ראשוני
    doc_id = await rag_service.add_document_from_text(
        content="תוכן ראשוני",
        title="כותרת ראשונית",
        source="test",
        metadata={"version": 1}
    )
    
    # עדכון המסמך מספר פעמים
    versions = [
        ("תוכן מעודכן 1", "כותרת מעודכנת 1", 2),
        ("תוכן מעודכן 2", "כותרת מעודכנת 2", 3),
        ("תוכן מעודכן 3", "כותרת מעודכנת 3", 4)
    ]
    
    for content, title, version in versions:
        success = await rag_service.update_document(
            doc_id=doc_id,
            content=content,
            title=title,
            metadata={"version": version}
        )
        assert success
    
    # בדיקת הגרסה האחרונה
    doc = await rag_service.get_document_by_id(doc_id)
    assert doc["metadata"]["version"] == 4
    assert doc["content"] == "תוכן מעודכן 3"
    assert doc["title"] == "כותרת מעודכנת 3" 