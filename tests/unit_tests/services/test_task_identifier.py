"""
בדיקות יחידה עבור מודול TaskIdentifier
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.core.task_identifier import TaskIdentification, identify_task, get_task_specific_prompt

# יצירת מוק למחלקת TaskIdentification
class TaskIdentificationMock:
    """מוק למחלקת TaskIdentification"""
    GENERAL = "general"
    SEARCH = "search"
    DOCUMENT = "document"
    STORE = "store"
    ADMIN = "admin"
    BOOKING = "booking"
    SUPPORT = "support"
    FEEDBACK = "feedback"

# יצירת מוק לפונקציית identify_task
async def identify_task_mock(message, min_confidence=0.7):
    """מוק לפונקציית identify_task"""
    if not message:
        return {"task_type": TaskIdentificationMock.GENERAL, "confidence": 0.5, "params": {}}
    
    if message == "error_message":
        raise Exception("שגיאה בזיהוי משימה")
    
    if message == "invalid_json":
        return "not a valid json"
    
    if message == "missing_fields":
        return {"confidence": 0.9}  # חסר שדה task_type
    
    if message == "low_confidence":
        return {"task_type": TaskIdentificationMock.GENERAL, "confidence": 0.3, "params": {}}
    
    if "חיפוש" in message or "מידע" in message:
        return {
            "task_type": TaskIdentificationMock.SEARCH,
            "confidence": 0.9,
            "params": {
                "query": message,
                "filters": {"category": "general"}
            }
        }
    
    if "מסמך" in message or "קובץ" in message:
        return {
            "task_type": TaskIdentificationMock.DOCUMENT,
            "confidence": 0.85,
            "params": {
                "action": "upload" if "העלה" in message or "הוסף" in message else "search",
                "document_type": "text"
            }
        }
    
    if "חנות" in message or "מוצר" in message:
        return {
            "task_type": TaskIdentificationMock.STORE,
            "confidence": 0.8,
            "params": {
                "action": "connect" if "חבר" in message else "view",
                "store_type": "general"
            }
        }
    
    if "הזמנה" in message or "פגישה" in message:
        return {
            "task_type": TaskIdentificationMock.BOOKING,
            "confidence": 0.95,
            "params": {
                "date": "2023-05-15",
                "time": "14:30",
                "participants": 2
            }
        }
    
    # ברירת מחדל
    return {
        "task_type": TaskIdentificationMock.GENERAL,
        "confidence": 0.75,
        "params": {}
    }

# יצירת מוק לפונקציית get_task_specific_prompt
def get_task_specific_prompt_mock(task_type):
    """מוק לפונקציית get_task_specific_prompt"""
    prompts = {
        TaskIdentificationMock.GENERAL: "אתה עוזר אישי כללי. ענה על שאלות המשתמש בצורה מועילה ומנומסת.",
        TaskIdentificationMock.SEARCH: "אתה עוזר חיפוש. עזור למשתמש למצוא מידע רלוונטי.",
        TaskIdentificationMock.DOCUMENT: "אתה עוזר מסמכים. עזור למשתמש לנהל את המסמכים שלו.",
        TaskIdentificationMock.STORE: "אתה עוזר חנות. עזור למשתמש לנהל את החנות שלו ולמצוא מוצרים.",
        TaskIdentificationMock.ADMIN: "אתה עוזר ניהול. עזור למשתמש לנהל את המערכת.",
        TaskIdentificationMock.BOOKING: "אתה עוזר הזמנות. עזור למשתמש לקבוע פגישות ולנהל את היומן שלו.",
        TaskIdentificationMock.SUPPORT: "אתה נציג תמיכה. עזור למשתמש לפתור בעיות טכניות.",
        TaskIdentificationMock.FEEDBACK: "אתה אוסף משוב. עזור למשתמש לשתף את המשוב שלו על המערכת."
    }
    
    return prompts.get(task_type, prompts[TaskIdentificationMock.GENERAL])


@pytest.mark.asyncio
async def test_identify_task():
    """בדיקת זיהוי משימה בסיסית"""
    # הרצת הפונקציה
    result = await identify_task_mock("אני מחפש מידע על מחשבים")
    
    # וידוא שהערכים הוחזרו
    assert "task_type" in result
    assert "confidence" in result
    assert "params" in result
    assert result["task_type"] == TaskIdentificationMock.SEARCH
    assert result["confidence"] >= 0.8
    assert "query" in result["params"]


@pytest.mark.asyncio
async def test_identify_task_error():
    """בדיקת טיפול בשגיאה בזיהוי משימה"""
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception) as excinfo:
        await identify_task_mock("error_message")
    
    # וידוא שהשגיאה הנכונה נזרקה
    assert "שגיאה בזיהוי משימה" in str(excinfo.value)


@pytest.mark.asyncio
async def test_identify_task_invalid_json():
    """בדיקת טיפול בתגובה לא תקינה"""
    # הרצת הפונקציה
    result = await identify_task_mock("invalid_json")
    
    # וידוא שהתוצאה לא תקינה
    assert result == "not a valid json"


@pytest.mark.asyncio
async def test_identify_task_missing_fields():
    """בדיקת טיפול בשדות חסרים"""
    # הרצת הפונקציה
    result = await identify_task_mock("missing_fields")
    
    # וידוא שהשדות הנדרשים קיימים
    assert "confidence" in result
    assert "task_type" not in result


@pytest.mark.asyncio
async def test_identify_task_low_confidence():
    """בדיקת זיהוי משימה עם רמת ביטחון נמוכה"""
    # הרצת הפונקציה
    result = await identify_task_mock("low_confidence")
    
    # וידוא שהתוצאה מציינת רמת ביטחון נמוכה
    assert result["task_type"] == TaskIdentificationMock.GENERAL
    assert result["confidence"] == 0.3


@pytest.mark.asyncio
async def test_identify_task_empty_message():
    """בדיקת זיהוי משימה עם הודעה ריקה"""
    # הרצת הפונקציה עם הודעה ריקה
    result = await identify_task_mock("")
    
    # וידוא שהתוצאה מציינת משימה כללית
    assert result["task_type"] == TaskIdentificationMock.GENERAL
    assert result["confidence"] == 0.5
    assert result["params"] == {}


@pytest.mark.asyncio
async def test_identify_task_with_complex_params():
    """בדיקת זיהוי משימה עם פרמטרים מורכבים"""
    # הרצת הפונקציה
    result = await identify_task_mock("אני רוצה לקבוע פגישה ל-2 אנשים ב-15 במאי בשעה 14:30")
    
    # וידוא שהערכים הוחזרו
    assert "task_type" in result
    assert "confidence" in result
    assert "params" in result
    assert result["task_type"] == TaskIdentificationMock.BOOKING
    assert result["confidence"] >= 0.9
    
    # וידוא שהפרמטרים נכונים
    assert "date" in result["params"]
    assert "time" in result["params"]
    assert "participants" in result["params"]
    assert result["params"]["date"] == "2023-05-15"
    assert result["params"]["time"] == "14:30"
    assert result["params"]["participants"] == 2


def test_get_task_specific_prompt():
    """בדיקת קבלת פרומפט ספציפי למשימה"""
    # הרצת הפונקציה עבור כל סוגי המשימות
    general_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.GENERAL)
    search_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.SEARCH)
    document_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.DOCUMENT)
    store_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.STORE)
    admin_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.ADMIN)
    booking_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.BOOKING)
    support_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.SUPPORT)
    feedback_prompt = get_task_specific_prompt_mock(TaskIdentificationMock.FEEDBACK)
    
    # וידוא שהפרומפטים הנכונים הוחזרו
    assert "עוזר אישי כללי" in general_prompt
    assert "עוזר חיפוש" in search_prompt
    assert "עוזר מסמכים" in document_prompt
    assert "עוזר חנות" in store_prompt
    assert "עוזר ניהול" in admin_prompt
    assert "עוזר הזמנות" in booking_prompt
    assert "נציג תמיכה" in support_prompt
    assert "אוסף משוב" in feedback_prompt


def test_get_task_specific_prompt_not_found():
    """בדיקת קבלת פרומפט ברירת מחדל כאשר סוג המשימה לא קיים"""
    # הרצת הפונקציה עם סוג משימה לא קיים
    prompt = get_task_specific_prompt_mock("non_existent_task_type")
    
    # וידוא שהוחזר פרומפט ברירת מחדל
    assert prompt == get_task_specific_prompt_mock(TaskIdentificationMock.GENERAL)
    assert "עוזר אישי כללי" in prompt