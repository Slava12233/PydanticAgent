"""
בדיקות יחידה למזהה המשימות
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.core.task_identifier import identify_task, get_task_specific_prompt
from src.agents.models.responses import TaskIdentification
from src.tools.intent.intent_recognizer import calculate_intent_score
from src.tools.intent.recognizers.base_recognizer import BaseIntentRecognizer

@pytest.mark.asyncio
async def test_identify_task():
    """בדיקת זיהוי סוגי משימות"""
    test_cases = [
        # משימות מזג אוויר
        ("מה מזג האוויר היום?", "weather", "general_weather"),
        ("האם ירד גשם מחר?", "weather", "rain"),
        ("מה הטמפרטורה בחוץ?", "weather", "temperature"),
        
        # משימות חנות
        ("תוסיף מוצר חדש לחנות", "product_management", "create_product"),
        ("אני רוצה לעדכן מחיר למוצר", "product_management", "update_product"),
        ("תראה לי את כל ההזמנות", "order_management", "get_orders"),
        
        # משימות כלליות
        ("שלום, מה שלומך?", "general", "greeting"),
        ("תודה רבה!", "general", "gratitude"),
        ("אני צריך עזרה", "help", "general_help"),
        
        # משימות מורכבות
        ("אני רוצה להוסיף מוצר חדש לחנות ולעדכן את המחיר של מוצר קיים", "product_management", "create_product"),
        ("תבדוק את מזג האוויר ותקבע לי פגישה למחר", "weather", "general_weather")
    ]
    
    for message, expected_task_type, expected_intent in test_cases:
        task = await identify_task(message)
        assert task.task_type == expected_task_type
        assert task.specific_intent == expected_intent
        assert task.confidence_score > 0.5

@pytest.mark.asyncio
async def test_identify_task_with_context():
    """בדיקת זיהוי משימות עם הקשר"""
    # בדיקת זיהוי משימה בהקשר של שיחה על מזג אוויר
    history_text = """
    משתמש: מה מזג האוויר היום?
    מערכת: היום יהיה חם ושמשי
    משתמש: ומחר?
    """
    
    task = await identify_task("כן, ומה לגבי סוף השבוע?", context=history_text)
    assert task.task_type == "weather"
    assert task.specific_intent == "general_weather"
    assert task.confidence_score > 0.6

    # בדיקת זיהוי משימה בהקשר של שיחה על מוצרים
    history_text = """
    משתמש: אני רוצה להוסיף מוצר חדש
    מערכת: בשמחה, איזה סוג מוצר?
    משתמש: ספר
    """

    task = await identify_task("כמה עותקים יש במלאי?", context=history_text)
    assert task.task_type == "product_management"
    assert task.specific_intent == "check_inventory"
    assert task.confidence_score > 0.6

@pytest.mark.asyncio
async def test_identify_task_with_multiple_intents():
    """בדיקת זיהוי משימות עם כוונות מרובות"""
    # בדיקת משימה עם שתי כוונות
    message = "תוסיף מוצר חדש לחנות ותבדוק את המלאי"
    task = await identify_task(message)
    assert task.task_type == "product_management"
    assert task.specific_intent in ["create_product", "check_inventory"]
    assert task.confidence_score > 0.7

    # בדיקת משימה עם שלוש כוונות
    message = "תוסיף מוצר, תעדכן מחיר ותבדוק את ההזמנות"
    task = await identify_task(message)
    assert task.task_type in ["product_management", "order_management"]
    assert task.confidence_score > 0.6

def test_calculate_intent_score():
    """בדיקת חישוב ציון התאמה"""
    # בדיקת התאמה מלאה
    text = "אני רוצה להוסיף מוצר חדש"
    keywords = ["הוסף", "מוצר", "חדש"]
    score = calculate_intent_score(text, keywords)
    assert score > 0.8

    # בדיקת התאמה חלקית
    text = "אני רוצה לראות מוצר"
    keywords = ["הוסף", "מוצר", "חדש"]
    score = calculate_intent_score(text, keywords)
    assert 0.3 < score < 0.7

    # בדיקת אי התאמה
    text = "מה השעה?"
    keywords = ["הוסף", "מוצר", "חדש"]
    score = calculate_intent_score(text, keywords)
    assert score < 0.3

def test_base_recognizer():
    """בדיקת המזהה הבסיסי"""
    recognizer = BaseIntentRecognizer()

    # בדיקת זיהוי לפי תבניות
    text = "אני רוצה להוסיף מוצר חדש"
    intent_type, action, score = recognizer.identify_intent(text)
    assert intent_type == "product_management"
    assert action == "create_product"
    assert score > 0.8

    # בדיקת זיהוי לפי מילות מפתח
    text = "תעדכן בבקשה את המחיר"
    intent_type, action, score = recognizer.identify_intent(text)
    assert intent_type == "product_management"
    assert action == "update_product"
    assert score > 0.7

    # בדיקת למידה מפידבק
    text = "אני מעוניין להכניס פריט חדש למערכת"
    recognizer.learn_from_feedback(text, "product_management", "create_product")
    # בדיקה שהמילים החדשות נוספו
    assert "מעוניין" in recognizer.keywords["product_management"]["create_product"]
    assert "להכניס" in recognizer.keywords["product_management"]["create_product"]
    assert "פריט" in recognizer.keywords["product_management"]["create_product"]

@pytest.mark.asyncio
async def test_get_task_specific_prompt():
    """בדיקת קבלת פרומפט מותאם למשימה"""
    test_cases = [
        # משימת מזג אוויר
        (
            "weather",
            "מה מזג האוויר היום?",
            "אתה עוזר שמספק מידע על מזג אוויר"
        ),
        
        # משימת הוספת מוצר
        (
            "product_management",
            "תוסיף מוצר חדש",
            "אתה עוזר שמסייע בניהול מוצרים בחנות"
        ),
        
        # משימת הזמנות
        (
            "order_management",
            "תראה לי את ההזמנות",
            "אתה עוזר שמציג מידע על הזמנות"
        ),
        
        # משימה כללית
        (
            "general",
            "שלום, מה שלומך?",
            "אתה עוזר ידידותי שמנהל שיחה"
        )
    ]
    
    for task_type, message, expected_content in test_cases:
        prompt = get_task_specific_prompt(task_type, message)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert expected_content in prompt

@pytest.mark.asyncio
async def test_identify_task_error_handling():
    """בדיקת טיפול בשגיאות בזיהוי משימות"""
    # הודעה ריקה
    task = await identify_task("")
    assert task.task_type == "general"
    assert task.specific_intent == "empty"
    assert task.confidence_score < 0.2
    
    # הודעה לא ברורה
    task = await identify_task("123456789")
    assert task.task_type == "general"
    assert task.specific_intent == "unknown"
    assert task.confidence_score < 0.3
    
    # הודעה ארוכה מדי
    long_message = "א" * 1000
    task = await identify_task(long_message)
    assert task.task_type == "general"
    assert task.confidence_score < 0.4 