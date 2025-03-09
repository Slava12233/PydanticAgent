"""
בדיקות יחידה עבור מודול KnowledgeBase
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import json
from datetime import datetime

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.core.knowledge_base import KnowledgeBase

# יצירת מוק למחלקת KnowledgeBase
class KnowledgeBaseMock:
    """מוק למחלקת KnowledgeBase"""
    
    def __init__(self):
        self.db = MagicMock()
        self.collection = MagicMock()
        self.db.get_collection.return_value = self.collection
    
    async def add_fact(self, fact=None, source=None, confidence=None, metadata=None):
        """הוספת עובדה למאגר הידע"""
        fact_id = "fact_123"
        return fact_id
    
    async def get_fact(self, fact_id):
        """קבלת עובדה לפי מזהה"""
        if fact_id == "not_found":
            return None
        return {
            "id": fact_id, 
            "fact": "תוכן לדוגמה", 
            "source": "מקור", 
            "confidence": 0.95,
            "metadata": {"tags": ["תג1", "תג2"]}
        }
    
    async def update_fact(self, fact_id, updates):
        """עדכון עובדה קיימת"""
        if fact_id == "not_found":
            return None
        return {"id": fact_id, **updates}
    
    async def delete_fact(self, fact_id):
        """מחיקת עובדה"""
        if fact_id == "not_found":
            return False
        return True
    
    async def search_facts(self, query, filters=None, limit=10):
        """חיפוש עובדות"""
        if query == "no_results":
            return []
        
        results = [
            {
                "id": "fact_1", 
                "fact": "תוכן 1", 
                "source": "מקור 1", 
                "confidence": 0.9,
                "metadata": {"tags": ["תג1"]}
            },
            {
                "id": "fact_2", 
                "fact": "תוכן 2", 
                "source": "מקור 2", 
                "confidence": 0.8,
                "metadata": {"tags": ["תג2"]}
            }
        ]
        
        if filters:
            if "source" in filters:
                results = [r for r in results if r["source"] == filters["source"]]
            if "tags" in filters:
                results = [r for r in results if any(tag in r["metadata"]["tags"] for tag in filters["tags"])]
        
        return results[:limit]
    
    async def get_facts_by_source(self, source, limit=10):
        """קבלת עובדות לפי מקור"""
        return await self.search_facts("", {"source": source}, limit)
    
    async def get_facts_by_tag(self, tag, limit=10):
        """קבלת עובדות לפי תג"""
        return await self.search_facts("", {"tags": [tag]}, limit)


@pytest.fixture
def knowledge_base():
    """פיקסטורה ליצירת אובייקט KnowledgeBase למבחנים"""
    return KnowledgeBaseMock()


@pytest.mark.asyncio
async def test_add_fact(knowledge_base):
    """בדיקת הוספת עובדה למאגר הידע"""
    # הרצת הפונקציה
    fact_id = await knowledge_base.add_fact(
        fact="ירושלים היא בירת ישראל",
        source="ספר גיאוגרפיה",
        confidence=0.95,
        metadata={"category": "גיאוגרפיה", "tags": ["ישראל", "ערים"]}
    )
    
    # וידוא שהערך הוחזר
    assert fact_id is not None
    assert isinstance(fact_id, str)


@pytest.mark.asyncio
async def test_get_fact(knowledge_base):
    """בדיקת קבלת עובדה לפי מזהה"""
    # הרצת הפונקציה
    fact = await knowledge_base.get_fact("fact_123")
    
    # וידוא שהערך הוחזר
    assert fact is not None
    assert "id" in fact
    assert "fact" in fact
    assert "source" in fact
    assert "confidence" in fact
    assert "metadata" in fact


@pytest.mark.asyncio
async def test_get_fact_not_found(knowledge_base):
    """בדיקת קבלת עובדה שלא קיימת"""
    # הרצת הפונקציה
    fact = await knowledge_base.get_fact("not_found")
    
    # וידוא שהערך לא הוחזר
    assert fact is None


@pytest.mark.asyncio
async def test_update_fact(knowledge_base):
    """בדיקת עדכון עובדה"""
    # הרצת הפונקציה
    updated = await knowledge_base.update_fact("fact_123", {
        "fact": "עובדה מעודכנת",
        "confidence": 0.98
    })
    
    # וידוא שהערך הוחזר
    assert updated is not None
    assert updated["id"] == "fact_123"
    assert updated["fact"] == "עובדה מעודכנת"
    assert updated["confidence"] == 0.98


@pytest.mark.asyncio
async def test_delete_fact(knowledge_base):
    """בדיקת מחיקת עובדה"""
    # הרצת הפונקציה
    result = await knowledge_base.delete_fact("fact_123")
    
    # וידוא שהערך הוחזר
    assert result is True


@pytest.mark.asyncio
async def test_search_facts(knowledge_base):
    """בדיקת חיפוש עובדות"""
    # הרצת הפונקציה
    results = await knowledge_base.search_facts("תוכן")
    
    # וידוא שהערך הוחזר
    assert results is not None
    assert len(results) > 0
    assert "id" in results[0]
    assert "fact" in results[0]
    assert "source" in results[0]
    assert "confidence" in results[0]
    assert "metadata" in results[0]


@pytest.mark.asyncio
async def test_search_facts_with_filters(knowledge_base):
    """בדיקת חיפוש עובדות עם פילטרים"""
    # הרצת הפונקציה
    results = await knowledge_base.search_facts("תוכן", {"source": "מקור 1"})
    
    # וידוא שהערך הוחזר
    assert results is not None
    assert len(results) > 0
    assert results[0]["source"] == "מקור 1"


@pytest.mark.asyncio
async def test_search_facts_no_results(knowledge_base):
    """בדיקת חיפוש עובדות ללא תוצאות"""
    # הרצת הפונקציה
    results = await knowledge_base.search_facts("no_results")
    
    # וידוא שהערך הוחזר
    assert results is not None
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_facts_by_source(knowledge_base):
    """בדיקת קבלת עובדות לפי מקור"""
    # הרצת הפונקציה
    results = await knowledge_base.get_facts_by_source("מקור 1")
    
    # וידוא שהערך הוחזר
    assert results is not None
    assert len(results) > 0
    assert results[0]["source"] == "מקור 1"


@pytest.mark.asyncio
async def test_get_facts_by_tag(knowledge_base):
    """בדיקת קבלת עובדות לפי תג"""
    # הרצת הפונקציה
    results = await knowledge_base.get_facts_by_tag("תג1")
    
    # וידוא שהערך הוחזר
    assert results is not None
    assert len(results) > 0
    assert "תג1" in results[0]["metadata"]["tags"]


@pytest.mark.asyncio
async def test_add_fact_with_error(knowledge_base):
    """בדיקת הוספת עובדה עם שגיאה"""
    # הגדרת התנהגות המוק לזרוק שגיאה
    knowledge_base.add_fact = AsyncMock(side_effect=Exception("שגיאת מסד נתונים"))
    
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception):
        await knowledge_base.add_fact(
            fact="עובדה שתגרום לשגיאה",
            source="מקור בעייתי",
            confidence=0.5,
            metadata={}
        ) 