"""
בדיקות יחידה למזהה המשימות
"""

import pytest
from src.agents.core.task_identifier import identify_task, get_task_specific_prompt
from src.agents.models.responses import TaskIdentification

@pytest.mark.asyncio
async def test_identify_task_product():
    """בדיקת זיהוי משימת ניהול מוצרים"""
    # בדיקת שאלה על מוצר
    task = await identify_task("כמה עולה המוצר הזה?")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "product_management"
    assert task.specific_intent in ["price_query", "general"]
    assert task.confidence_score > 0

    # בדיקת הוספת מוצר
    task = await identify_task("אני רוצה להוסיף מוצר חדש")
    assert task.task_type == "product_management"
    assert task.specific_intent in ["add_product", "general"]
    assert task.confidence_score > 0

@pytest.mark.asyncio
async def test_identify_task_order():
    """בדיקת זיהוי משימת ניהול הזמנות"""
    # בדיקת מצב הזמנה
    task = await identify_task("מה קורה עם ההזמנה שלי מספר 123?")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "order_management"
    assert task.specific_intent in ["order_status", "general"]
    assert task.confidence_score > 0

    # בדיקת ביטול הזמנה
    task = await identify_task("אני רוצה לבטל את ההזמנה")
    assert task.task_type == "order_management"
    assert task.specific_intent in ["cancel_order", "general"]
    assert task.confidence_score > 0

@pytest.mark.asyncio
async def test_identify_task_customer():
    """בדיקת זיהוי משימת ניהול לקוחות"""
    # בדיקת פרטי לקוח
    task = await identify_task("תראה לי את הפרטים של הלקוח")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "customer_management"
    assert task.specific_intent in ["customer_details", "general"]
    assert task.confidence_score > 0

    # בדיקת עדכון פרטי לקוח
    task = await identify_task("אני רוצה לעדכן את הכתובת של הלקוח")
    assert task.task_type == "customer_management"
    assert task.specific_intent in ["update_customer", "general"]
    assert task.confidence_score > 0

@pytest.mark.asyncio
async def test_identify_task_inventory():
    """בדיקת זיהוי משימת ניהול מלאי"""
    # בדיקת מצב מלאי
    task = await identify_task("כמה יחידות נשארו במלאי?")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "inventory_management"
    assert task.specific_intent in ["stock_query", "general"]
    assert task.confidence_score > 0

    # בדיקת עדכון מלאי
    task = await identify_task("צריך לעדכן את המלאי של המוצר")
    assert task.task_type == "inventory_management"
    assert task.specific_intent in ["update_stock", "general"]
    assert task.confidence_score > 0

@pytest.mark.asyncio
async def test_identify_task_analytics():
    """בדיקת זיהוי משימת ניתוח נתונים"""
    # בדיקת דוח מכירות
    task = await identify_task("תראה לי את דוח המכירות")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "analytics"
    assert task.specific_intent in ["sales_report", "general"]
    assert task.confidence_score > 0

    # בדיקת ניתוח מגמות
    task = await identify_task("מה המגמות במכירות החודש האחרון?")
    assert task.task_type == "analytics"
    assert task.specific_intent in ["trend_analysis", "general"]
    assert task.confidence_score > 0

@pytest.mark.asyncio
async def test_identify_task_general():
    """בדיקת זיהוי משימות כלליות"""
    # בדיקת ברכה
    task = await identify_task("שלום, מה שלומך?")
    assert isinstance(task, TaskIdentification)
    assert task.task_type == "general"
    assert task.specific_intent == "general"
    assert task.confidence_score > 0

    # בדיקת שאלה כללית
    task = await identify_task("איך אני יכול לעזור ללקוחות שלי?")
    assert task.task_type == "general"
    assert task.specific_intent == "general"
    assert task.confidence_score > 0

def test_get_task_specific_prompt():
    """בדיקת בניית פרומפט מותאם למשימה"""
    # בדיקת פרומפט למשימת ניהול מוצרים
    prompt = get_task_specific_prompt(
        task_type="product_management",
        user_message="כמה עולה המוצר?",
        history_text="משתמש: שלום\nבוט: שלום!"
    )
    assert prompt != ""
    assert "WooCommerce" in prompt
    assert "מוצרים" in prompt
    assert "כמה עולה המוצר?" in prompt
    assert "שלום" in prompt

    # בדיקת פרומפט למשימת ניהול מסמכים
    prompt = get_task_specific_prompt(
        task_type="document_management",
        user_message="תמצא לי את המסמך",
        history_text=""
    )
    assert prompt != ""
    assert "מסמכים" in prompt
    assert "תמצא לי את המסמך" in prompt

    # בדיקת פרומפט למשימה לא מוכרת
    prompt = get_task_specific_prompt(
        task_type="unknown_task",
        user_message="מה זה?",
        history_text=""
    )
    assert prompt != ""
    assert "מה זה?" in prompt 