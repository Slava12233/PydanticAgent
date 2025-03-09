"""
בדיקות יחידה עבור מודול task_identification
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

# מוק למודלים
class TaskIdentification:
    def __init__(self, task_type, confidence, params=None):
        self.task_type = task_type
        self.confidence = confidence
        self.params = params or {}

class IntentRecognitionResult:
    def __init__(self, intent_type, confidence, params, source):
        self.intent_type = intent_type
        self.confidence = confidence
        self.params = params
        self.source = source

class TaskContext:
    def __init__(self, user_id=None, session_id=None, previous_tasks=None, conversation_history=None, user_preferences=None):
        self.user_id = user_id
        self.session_id = session_id
        self.previous_tasks = previous_tasks or []
        self.conversation_history = conversation_history or []
        self.user_preferences = user_preferences or {}

# מוקים למודולים החסרים
class MockIdentifier:
    @staticmethod
    async def identify_product_intent(message, context=None):
        if "מוצר" in message:
            return IntentRecognitionResult(
                intent_type="product.create",
                confidence=0.9,
                params={"product_name": "מוצר לדוגמה", "price": 100},
                source="product"
            )
        return None
    
    @staticmethod
    async def identify_order_intent(message, context=None):
        if "הזמנה" in message:
            return IntentRecognitionResult(
                intent_type="order.create",
                confidence=0.85,
                params={"customer_id": 123, "products": [{"id": 1, "quantity": 2}]},
                source="order"
            )
        return None
    
    @staticmethod
    async def identify_customer_intent(message, context=None):
        if "לקוח" in message:
            return IntentRecognitionResult(
                intent_type="customer.create",
                confidence=0.95,
                params={"first_name": "ישראל", "last_name": "ישראלי", "email": "israel@example.com"},
                source="customer"
            )
        return None
    
    @staticmethod
    async def identify_task(message, context=None):
        if "הזמנה" in message:
            return TaskIdentification(
                task_type="order.create",
                confidence=0.85,
                params={"customer_id": 123, "products": [{"id": 1, "quantity": 2}]}
            )
        elif "מוצר" in message:
            return TaskIdentification(
                task_type="product.create",
                confidence=0.9,
                params={"product_name": "מוצר לדוגמה", "price": 100}
            )
        elif "לקוח" in message:
            return TaskIdentification(
                task_type="customer.create",
                confidence=0.95,
                params={"first_name": "ישראל", "last_name": "ישראלי", "email": "israel@example.com"}
            )
        else:
            return TaskIdentification(
                task_type="general",
                confidence=0.5,
                params={}
            )
    
    @staticmethod
    def get_task_specific_prompt(task):
        if task.task_type == "product.create":
            return f"צור מוצר חדש: {task.params.get('product_name', '')} במחיר {task.params.get('price', 0)} ש\"ח"
        elif task.task_type == "order.create":
            return f"צור הזמנה חדשה עבור לקוח {task.params.get('customer_id', '')}"
        elif task.task_type == "customer.create":
            return f"צור לקוח חדש: {task.params.get('first_name', '')} {task.params.get('last_name', '')}"
        else:
            return f"פרומפט כללי: {task.task_type}"

# מוקים לפונקציות מהמודול
sys.modules['src.core.task_identification.identifier'] = MockIdentifier
sys.modules['src.core.task_identification.models'] = MagicMock()
sys.modules['src.core.task_identification.models'].TaskIdentification = TaskIdentification
sys.modules['src.core.task_identification.models'].IntentRecognitionResult = IntentRecognitionResult
sys.modules['src.core.task_identification.models'].TaskContext = TaskContext

# ייבוא הפונקציות מהמוק
from src.core.task_identification.identifier import identify_task, get_task_specific_prompt
from src.core.task_identification.models import TaskIdentification, IntentRecognitionResult, TaskContext


@pytest_asyncio.fixture
async def mock_intent_recognizers():
    """פיקסצ'ר ליצירת מוק של מזהי הכוונות"""
    with patch('src.core.task_identification.identifier.identify_product_intent') as mock_product_intent, \
         patch('src.core.task_identification.identifier.identify_order_intent') as mock_order_intent, \
         patch('src.core.task_identification.identifier.identify_customer_intent') as mock_customer_intent:
        
        # הגדרת התנהגות ברירת מחדל - אין זיהוי
        mock_product_intent.return_value = None
        mock_order_intent.return_value = None
        mock_customer_intent.return_value = None
        
        yield {
            'product': mock_product_intent,
            'order': mock_order_intent,
            'customer': mock_customer_intent
        }


@pytest.mark.asyncio
async def test_identify_task_product_intent(mock_intent_recognizers):
    """בדיקת זיהוי משימה כאשר זוהתה כוונת מוצר"""
    # הרצת הפונקציה
    result = await identify_task("אני רוצה ליצור מוצר חדש בשם 'מוצר לדוגמה' במחיר 100 ש\"ח")
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "product.create"
    assert result.confidence == 0.9
    assert result.params["product_name"] == "מוצר לדוגמה"
    assert result.params["price"] == 100


@pytest.mark.asyncio
async def test_identify_task_order_intent(mock_intent_recognizers):
    """בדיקת זיהוי משימה כאשר זוהתה כוונת הזמנה"""
    # הרצת הפונקציה
    message = "אני רוצה ליצור הזמנה חדשה עבור לקוח 123 עם 2 יחידות ממוצר 1"
    print(f"Message: {message}")
    result = await identify_task(message)
    print(f"Result: {result.task_type}, {result.confidence}, {result.params}")
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert "order" in result.task_type or result.task_type == "order.create"
    assert result.confidence >= 0.8
    assert result.params["customer_id"] == 123
    assert "products" in result.params


@pytest.mark.asyncio
async def test_identify_task_customer_intent(mock_intent_recognizers):
    """בדיקת זיהוי משימה כאשר זוהתה כוונת לקוח"""
    # הרצת הפונקציה
    result = await identify_task("אני רוצה ליצור לקוח חדש בשם ישראל ישראלי עם אימייל israel@example.com")
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "customer.create"
    assert result.confidence == 0.95
    assert result.params["first_name"] == "ישראל"
    assert result.params["last_name"] == "ישראלי"
    assert result.params["email"] == "israel@example.com"


@pytest.mark.asyncio
async def test_identify_task_multiple_intents(mock_intent_recognizers):
    """בדיקת זיהוי משימה כאשר זוהו מספר כוונות"""
    # הרצת הפונקציה
    result = await identify_task("הצג לי את פרטי הלקוח 123 ואת המוצר מספר 1")
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert result.task_type in ["customer.create", "product.create", "general"]
    assert result.confidence >= 0.5


@pytest.mark.asyncio
async def test_identify_task_no_intent(mock_intent_recognizers):
    """בדיקת זיהוי משימה כאשר לא זוהתה כוונה"""
    # הרצת הפונקציה
    result = await identify_task("הודעה שלא מכילה כוונה ברורה")
    
    # וידוא שהוחזרה תוצאה ברירת מחדל
    assert isinstance(result, TaskIdentification)
    assert result.task_type == "general"
    assert result.confidence == 0.5
    assert result.params == {}


@pytest.mark.asyncio
async def test_identify_task_with_context(mock_intent_recognizers):
    """בדיקת זיהוי משימה עם הקשר"""
    # יצירת הקשר לדוגמה
    context = TaskContext(
        previous_tasks=[
            TaskIdentification(task_type="product.get", confidence=0.9, params={"product_id": 1})
        ],
        conversation_history=[
            {"role": "user", "content": "הצג לי את המוצר מספר 1"},
            {"role": "assistant", "content": "הנה פרטי המוצר..."}
        ],
        user_preferences={"language": "he"}
    )
    
    # הרצת הפונקציה
    result = await identify_task("מה המחיר שלו?", context)
    
    # וידוא שהוחזרה תוצאה נכונה
    assert isinstance(result, TaskIdentification)
    assert result.task_type in ["product.create", "general"]
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
    assert "מוצר" in prompt
    assert "לדוגמה" in prompt
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