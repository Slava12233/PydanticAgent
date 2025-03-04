"""
בדיקות יחידה למנהל הפרומפטים
"""

import pytest
from src.agents.prompts.prompt_manager import PromptManager

@pytest.fixture
def prompt_manager():
    """יצירת מופע של מנהל הפרומפטים לבדיקות"""
    return PromptManager()

def test_get_base_prompt(prompt_manager):
    """בדיקת קבלת הפרומפט הבסיסי"""
    prompt = prompt_manager.get_base_prompt()
    assert prompt != ""
    assert "אתה עוזר אישי" in prompt
    assert "עונה בעברית" in prompt

def test_get_task_prompt(prompt_manager):
    """בדיקת קבלת פרומפט למשימה ספציפית"""
    # בדיקת משימת ניהול מסמכים
    doc_prompt = prompt_manager.get_task_prompt("document_management")
    assert doc_prompt != ""
    assert "מסמכים" in doc_prompt
    
    # בדיקת משימת ניהול מוצרים
    product_prompt = prompt_manager.get_task_prompt("product_management")
    assert product_prompt != ""
    assert "WooCommerce" in product_prompt
    assert "מוצרים" in product_prompt
    
    # בדיקת משימה לא קיימת
    unknown_prompt = prompt_manager.get_task_prompt("unknown_task")
    assert unknown_prompt == ""

def test_get_error_message(prompt_manager):
    """בדיקת קבלת הודעות שגיאה"""
    # בדיקת שגיאת מכסה
    quota_error = prompt_manager.get_error_message("quota")
    assert quota_error != ""
    assert "מכסת השימוש" in quota_error
    
    # בדיקת שגיאת זמן
    timeout_error = prompt_manager.get_error_message("timeout")
    assert timeout_error != ""
    assert "זמן" in timeout_error
    
    # בדיקת שגיאה כללית
    general_error = prompt_manager.get_error_message("general")
    assert general_error != ""
    assert "בעיה טכנית" in general_error
    
    # בדיקת שגיאה לא קיימת
    unknown_error = prompt_manager.get_error_message("unknown_error")
    assert unknown_error == prompt_manager.get_error_message("general")

def test_format_conversation_history(prompt_manager):
    """בדיקת פורמוט היסטוריית שיחה"""
    history = "משתמש: מה שלומך?\nבוט: טוב, תודה!"
    message = "מה השעה?"
    
    formatted = prompt_manager.format_conversation_history(history, message)
    assert formatted != ""
    assert history in formatted
    assert message in formatted
    assert "היסטוריית השיחה" in formatted

def test_format_context_info(prompt_manager):
    """בדיקת פורמוט מידע הקשר"""
    context = "זהו מידע רלוונטי מהמסמכים"
    
    formatted = prompt_manager.format_context_info(context)
    assert formatted != ""
    assert context in formatted
    assert "מידע רלוונטי" in formatted

def test_build_prompt(prompt_manager):
    """בדיקת בניית פרומפט מלא"""
    task_type = "product_management"
    message = "כמה מוצרים יש במלאי?"
    history = "משתמש: מה שלומך?\nבוט: טוב, תודה!"
    context = "יש 100 מוצרים במלאי"
    
    # בדיקה עם כל הפרמטרים
    full_prompt = prompt_manager.build_prompt(
        task_type=task_type,
        message=message,
        history=history,
        context=context
    )
    assert full_prompt != ""
    assert "עוזר אישי" in full_prompt  # מהפרומפט הבסיסי
    assert "WooCommerce" in full_prompt  # מהפרומפט הספציפי למשימה
    assert message in full_prompt  # ההודעה הנוכחית
    assert history in full_prompt  # היסטוריית השיחה
    assert context in full_prompt  # מידע ההקשר
    
    # בדיקה ללא היסטוריה והקשר
    simple_prompt = prompt_manager.build_prompt(
        task_type=task_type,
        message=message
    )
    assert simple_prompt != ""
    assert "עוזר אישי" in simple_prompt
    assert "WooCommerce" in simple_prompt
    assert message in simple_prompt
    assert history not in simple_prompt
    assert context not in simple_prompt 