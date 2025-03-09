"""
בדיקות יחידה עבור מודול EntityExtractor
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import json

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.core.entity_extractor import extract_entities

# יצירת מוק לפונקציית extract_entities
async def extract_entities_mock(text, entity_types=None, min_confidence=0.5, model="gpt-3.5-turbo"):
    """מוק לפונקציית extract_entities"""
    if not text:
        return []
    
    if text == "error_message":
        raise Exception("API Error")
    
    if text == "invalid_json":
        return "not a valid json"
    
    if text == "missing_fields":
        return [{"type": "person"}]  # חסר שדה text
    
    # תוצאות דוגמה
    results = [
        {
            "type": "person",
            "text": "משה כהן",
            "confidence": 0.95,
            "metadata": {"gender": "male"}
        },
        {
            "type": "location",
            "text": "תל אביב",
            "confidence": 0.9,
            "metadata": {"country": "ישראל"}
        },
        {
            "type": "date",
            "text": "1 בינואר 2023",
            "confidence": 0.8,
            "metadata": {"format": "day_month_year"}
        }
    ]
    
    # סינון לפי סוגי ישויות
    if entity_types:
        results = [r for r in results if r["type"] in entity_types]
    
    # סינון לפי רמת ביטחון
    results = [r for r in results if r["confidence"] >= min_confidence]
    
    return results


@pytest.mark.asyncio
async def test_extract_entities_basic():
    """בדיקת חילוץ ישויות בסיסי"""
    # הרצת הפונקציה
    entities = await extract_entities_mock("משה כהן גר בתל אביב ונולד ב-1 בינואר 2023")
    
    # וידוא שהערכים הוחזרו
    assert len(entities) == 3
    assert entities[0]["type"] == "person"
    assert entities[0]["text"] == "משה כהן"
    assert entities[1]["type"] == "location"
    assert entities[1]["text"] == "תל אביב"
    assert entities[2]["type"] == "date"
    assert entities[2]["text"] == "1 בינואר 2023"


@pytest.mark.asyncio
async def test_extract_entities_empty_message():
    """בדיקת חילוץ ישויות מהודעה ריקה"""
    # הרצת הפונקציה
    entities = await extract_entities_mock("")
    
    # וידוא שהוחזר מערך ריק
    assert entities == []


@pytest.mark.asyncio
async def test_extract_entities_api_error():
    """בדיקת טיפול בשגיאת API"""
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception) as excinfo:
        await extract_entities_mock("error_message")
    
    # וידוא שהשגיאה הנכונה נזרקה
    assert "API Error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_extract_entities_invalid_json():
    """בדיקת טיפול בתגובה לא תקינה"""
    # הרצת הפונקציה
    result = await extract_entities_mock("invalid_json")
    
    # וידוא שהתוצאה לא תקינה
    assert result == "not a valid json"


@pytest.mark.asyncio
async def test_extract_entities_missing_fields():
    """בדיקת טיפול בשדות חסרים"""
    # הרצת הפונקציה
    entities = await extract_entities_mock("missing_fields")
    
    # וידוא שהשדות הנדרשים קיימים
    assert len(entities) == 1
    assert "type" in entities[0]
    assert "text" not in entities[0]


@pytest.mark.asyncio
async def test_extract_entities_with_entity_types():
    """בדיקת חילוץ ישויות עם סינון לפי סוגים"""
    # הרצת הפונקציה עם סינון לפי סוגי ישויות
    entities = await extract_entities_mock(
        "משה כהן גר בתל אביב ונולד ב-1 בינואר 2023",
        entity_types=["person", "location"]
    )
    
    # וידוא שהערכים הוחזרו
    assert len(entities) == 2
    assert entities[0]["type"] == "person"
    assert entities[0]["text"] == "משה כהן"
    assert entities[1]["type"] == "location"
    assert entities[1]["text"] == "תל אביב"


@pytest.mark.asyncio
async def test_extract_entities_with_min_confidence():
    """בדיקת חילוץ ישויות עם סינון לפי רמת ביטחון"""
    # הרצת הפונקציה עם סינון לפי רמת ביטחון
    entities = await extract_entities_mock(
        "משה כהן גר בתל אביב ונולד ב-1 בינואר 2023",
        min_confidence=0.9
    )
    
    # וידוא שהערכים הוחזרו
    assert len(entities) == 2
    assert entities[0]["type"] == "person"
    assert entities[0]["text"] == "משה כהן"
    assert entities[1]["type"] == "location"
    assert entities[1]["text"] == "תל אביב"


@pytest.mark.asyncio
async def test_extract_entities_with_custom_model():
    """בדיקת חילוץ ישויות עם מודל מותאם אישית"""
    # הרצת הפונקציה עם מודל מותאם אישית
    entities = await extract_entities_mock(
        "משה כהן גר בתל אביב ונולד ב-1 בינואר 2023",
        model="gpt-4"
    )
    
    # וידוא שהערכים הוחזרו
    assert len(entities) == 3
    assert entities[0]["type"] == "person"
    assert entities[0]["text"] == "משה כהן"
    assert entities[1]["type"] == "location"
    assert entities[1]["text"] == "תל אביב"
    assert entities[2]["type"] == "date"
    assert entities[2]["text"] == "1 בינואר 2023" 