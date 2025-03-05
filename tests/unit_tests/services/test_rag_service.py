import pytest
import pytest_asyncio
from datetime import datetime
from src.services.rag_service import RAGService
from src.database.models import Document
from src.database.database import Database

db = Database()

@pytest_asyncio.fixture
async def rag_service():
    """פיקסצ'ר ליצירת מופע של RAG Service לבדיקות"""
    service = RAGService()
    yield service
    # ניקוי אחרי כל בדיקה
    await service.delete_all_documents()
    # סגירת החיבור לדאטהבייס
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_add_document(rag_service):
    """בדיקת הוספת מסמך חדש"""
    # הכנת נתוני בדיקה
    doc_content = "זהו מסמך בדיקה"
    doc_title = "מסמך בדיקה"
    doc_source = "test"
    metadata = {"type": "test", "author": "tester"}
    
    # הוספת המסמך
    doc_id = await rag_service.add_document_from_text(
        content=doc_content,
        title=doc_title,
        source=doc_source,
        metadata=metadata
    )
    
    # וידוא שהמסמך נוסף בהצלחה
    assert doc_id is not None
    
    # אחזור המסמך ובדיקת הפרטים שלו
    results = await rag_service.search_documents(doc_title)
    assert len(results) > 0
    doc = results[0]
    assert doc["title"] == doc_title
    assert doc["content"] == doc_content
    assert doc["source"] == doc_source
    assert doc["document_metadata"]["type"] == metadata["type"]
    assert doc["document_metadata"]["author"] == metadata["author"]

@pytest.mark.asyncio
async def test_search_documents(rag_service):
    """בדיקת חיפוש במסמכים"""
    # הוספת מספר מסמכי בדיקה
    docs = [
        ("מסמך על חתולים", "חתולים הם חיות מחמד פופולריות"),
        ("מסמך על כלבים", "כלבים הם חיות מחמד נאמנות"),
        ("מסמך על תוכים", "תוכים הם ציפורים צבעוניות")
    ]
    
    for title, content in docs:
        await rag_service.add_document_from_text(
            content=content,
            title=title,
            source="test"
        )
    
    # חיפוש מסמכים
    results = await rag_service.search_documents("חיות מחמד")
    assert len(results) >= 2  # צריך למצוא לפחות את המסמכים על חתולים וכלבים
    
    # בדיקת דירוג התוצאות
    assert all(result["similarity"] > 0.0 for result in results)
    assert results[0]["similarity"] >= results[-1]["similarity"]  # וידוא שהתוצאות מסודרות לפי רלוונטיות

@pytest.mark.asyncio
async def test_delete_document(rag_service):
    """בדיקת מחיקת מסמך"""
    # הוספת מסמך
    doc_id = await rag_service.add_document_from_text(
        content="מסמך למחיקה",
        title="מסמך בדיקה",
        source="test"
    )
    
    # וידוא שהמסמך קיים
    results = await rag_service.search_documents("מסמך למחיקה")
    assert len(results) > 0
    
    # מחיקת המסמך
    success = await rag_service.delete_document(doc_id)
    assert success
    
    # וידוא שהמסמך נמחק
    results = await rag_service.search_documents("מסמך למחיקה")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_update_document(rag_service):
    """בדיקת עדכון מסמך קיים"""
    # הוספת מסמך
    doc_id = await rag_service.add_document_from_text(
        content="תוכן מקורי",
        title="כותרת מקורית",
        source="test"
    )
    
    # עדכון המסמך
    new_content = "תוכן מעודכן"
    new_title = "כותרת מעודכנת"
    await rag_service.update_document(
        doc_id=doc_id,
        content=new_content,
        title=new_title
    )
    
    # בדיקת העדכון
    updated_doc = await rag_service.search_documents(new_title)
    assert len(updated_doc) > 0
    doc = updated_doc[0]
    assert doc["content"] == new_content
    assert doc["title"] == new_title

@pytest.mark.asyncio
async def test_semantic_search(rag_service):
    """בדיקת חיפוש סמנטי"""
    # הוספת מסמכים עם תוכן סמנטי דומה אך מילים שונות
    docs = [
        ("מזג אוויר", "היום יהיה חם ושמשי עם טמפרטורות גבוהות"),
        ("תחזית", "הטמפרטורות יעלו היום והשמש תקפח"),
        ("מסמך אחר", "היום יתקיים משחק כדורגל חשוב")
    ]
    
    for title, content in docs:
        await rag_service.add_document_from_text(
            content=content,
            title=title,
            source="test"
        )
    
    # חיפוש סמנטי
    results = await rag_service.search_documents("מה מזג האוויר היום")
    
    # בדיקה שהתוצאות הרלוונטיות נמצאו
    assert len(results) >= 2
    found_weather_docs = False
    for result in results[:2]:  # שתי התוצאות הראשונות צריכות להיות קשורות למזג אוויר
        if "טמפרטורות" in result["content"] or "שמש" in result["content"]:
            found_weather_docs = True
    assert found_weather_docs

@pytest.mark.asyncio
async def test_error_handling(rag_service):
    """בדיקת טיפול בשגיאות"""
    # ניסיון להוסיף מסמך ריק
    doc_id = await rag_service.add_document_from_text(
        content="",
        title="",
        source=""
    )
    assert doc_id is None

    # ניסיון למחוק מסמך לא קיים
    success = await rag_service.delete_document(999999)
    assert not success 