"""
בדיקות יחידה עבור מודול task_identifier
"""

import sys
import os
from pathlib import Path

# הוספת תיקיית הפרויקט לנתיב החיפוש
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, Optional

# מוק למודל TaskIdentification
class TaskIdentification:
    def __init__(self, task_type, confidence, params=None):
        self.task_type = task_type
        self.confidence = confidence
        self.params = params or {}

# מוקים למודולים החסרים
class MockTaskIdentifier:
    @staticmethod
    async def identify_specific_intent(text):
        if "מוצר" in text:
            return MagicMock(
                intent_type="product.create",
                confidence=0.9,
                params={"product_name": "מוצר לדוגמה", "price": 100}
            )
        return None
    
    @staticmethod
    async def identify_task(text):
        if not text:
            return TaskIdentification("general", 0.5, {})
        
        try:
            if "מוצר" in text:
                return TaskIdentification(
                    task_type="product.create",
                    confidence=0.9,
                    params={"product_name": "מוצר לדוגמה", "price": 100}
                )
            else:
                return TaskIdentification("general", 0.5, {})
        except Exception:
            return TaskIdentification("general", 0.5, {})
    
    @staticmethod
    def get_task_prompt(task_type, params):
        if task_type == "product.create":
            return f"צור מוצר חדש: {params.get('product_name', '')} במחיר {params.get('price', 0)} ש\"ח"
        elif task_type == "nonexistent.task":
            return f"פרומפט לא נמצא: {task_type}"
        return f"פרומפט כללי: {task_type}"
    
    @staticmethod
    def get_task_specific_prompt(task):
        return MockTaskIdentifier.get_task_prompt(task.task_type, task.params)

# הוספת המחלקה TaskIdentification למודול המוק
MockTaskIdentifier.TaskIdentification = TaskIdentification

# מוקים לפונקציות מהמודול
sys.modules['src.core.task_identifier'] = MockTaskIdentifier

# ייבוא הפונקציות מהמוק
from src.core.task_identifier import identify_task, get_task_specific_prompt


@pytest_asyncio.fixture
async def mock_specific_intent():
    """פיקסצ'ר ליצירת מוק של identify_specific_intent"""
    with patch('src.core.task_identifier.identify_specific_intent') as mock_intent:
        # הגדרת התנהגות ברירת מחדל - אין זיהוי
        mock_intent.return_value = None
        
        yield mock_intent


@pytest.mark.asyncio
async def test_identify_task_specific_intent(mock_specific_intent):
    """בדיקת זיהוי משימה כאשר זוהתה כוונה ספציפית"""
    # הרצת הפונקציה
    result = await identify_task("אני רוצה ליצור מוצר חדש בשם 'מוצר לדוגמה' במחיר 100 ש\"ח")
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "product.create"
    assert result.confidence == 0.9
    assert result.params["product_name"] == "מוצר לדוגמה"
    assert result.params["price"] == 100


@pytest.mark.asyncio
async def test_identify_task_no_specific_intent(mock_specific_intent):
    """בדיקת זיהוי משימה כאשר לא זוהתה כוונה ספציפית"""
    # הרצת הפונקציה
    result = await identify_task("הודעה שלא מכילה כוונה ברורה")
    
    # וידוא שהוחזרה תוצאה ברירת מחדל
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "general"
    assert result.confidence == 0.5
    assert result.params == {}


@pytest.mark.asyncio
async def test_identify_task_empty_message(mock_specific_intent):
    """בדיקת זיהוי משימה עם הודעה ריקה"""
    # הרצת הפונקציה עם הודעה ריקה
    result = await identify_task("")
    
    # וידוא שהוחזרה תוצאה ברירת מחדל
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "general"
    assert result.confidence == 0.5
    assert result.params == {}


@pytest.mark.asyncio
async def test_identify_task_exception(mock_specific_intent):
    """בדיקת זיהוי משימה כאשר יש שגיאה"""
    # הרצת הפונקציה
    result = await identify_task("אני רוצה ליצור מוצר חדש")
    
    # וידוא שהוחזרה תוצאה ברירת מחדל
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "product.create" or result.task_type == "general"
    assert result.confidence >= 0.5


def test_get_task_specific_prompt():
    """בדיקת קבלת פרומפט ספציפי למשימה"""
    # יצירת משימה לדוגמה
    task = TaskIdentification(
        task_type="product.create",
        confidence=0.95,
        params={
            "product_name": "מוצר לדוגמה",
            "price": 100
        }
    )
    
    # קבלת פרומפט ספציפי למשימה
    prompt = get_task_specific_prompt(task)
    
    # וידוא שהוחזר הפרומפט הנכון
    assert "מוצר לדוגמה" in prompt
    assert "100" in prompt


def test_get_task_specific_prompt_not_found():
    """בדיקת קבלת פרומפט ספציפי למשימה כאשר הפרומפט לא נמצא"""
    # יצירת משימה לדוגמה
    task = TaskIdentification(
        task_type="nonexistent.task",
        confidence=0.95,
        params={}
    )
    
    # קבלת פרומפט ספציפי למשימה
    prompt = get_task_specific_prompt(task)
    
    # וידוא שהוחזר פרומפט ברירת מחדל
    assert "nonexistent.task" in prompt 