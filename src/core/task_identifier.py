"""
מזהה סוגי משימות
"""

from typing import Optional
import logging
from pydantic import BaseModel

class TaskIdentification(BaseModel):
    """מודל לזיהוי משימה"""
    task_type: str
    specific_intent: str
    confidence_score: float

async def identify_task(message: str, context: Optional[str] = None) -> TaskIdentification:
    """
    זיהוי סוג המשימה מתוך הודעה
    
    Args:
        message: הודעת המשתמש
        context: הקשר השיחה (אופציונלי)
        
    Returns:
        זיהוי המשימה
    """
    # מילות מפתח למשימות שונות
    task_keywords = {
        "weather": [
            "מזג", "אוויר", "גשם", "טמפרטורה", "חם", "קר",
            "תחזית", "מעונן", "שמש", "רוח"
        ],
        "add_product": [
            "הוסף", "תוסיף", "להוסיף", "מוצר חדש", "הוספת מוצר",
            "רשום מוצר", "הכנס מוצר"
        ],
        "update_product": [
            "עדכן", "תעדכן", "לעדכן", "שנה", "תשנה", "לשנות",
            "מחיר", "כמות", "תיאור"
        ],
        "view_orders": [
            "הזמנות", "הזמנה", "הצג הזמנות", "תראה הזמנות",
            "מצב הזמנה", "סטטוס הזמנה"
        ],
        "help": [
            "עזרה", "תעזור", "לעזור", "הסבר", "הדרכה",
            "איך", "כיצד"
        ]
    }
    
    # ספירת מילות מפתח לכל סוג משימה
    task_scores = {task_type: 0 for task_type in task_keywords}
    
    # בדיקת מילות מפתח בהודעה
    message_lower = message.lower()
    for task_type, keywords in task_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                task_scores[task_type] += 1
    
    # בדיקת הקשר אם קיים
    if context:
        context_lower = context.lower()
        for task_type, keywords in task_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    task_scores[task_type] += 0.5
    
    # מציאת המשימה עם הציון הגבוה ביותר
    max_score = max(task_scores.values())
    if max_score > 0:
        for task_type, score in task_scores.items():
            if score == max_score:
                logging.info(f"זוהה סוג משימה: {task_type}")
                return TaskIdentification(
                    task_type=task_type,
                    specific_intent=_get_specific_intent(message, task_type),
                    confidence_score=min(score / len(task_keywords[task_type]), 1.0)
                )
    
    # אם לא זוהתה משימה ספציפית
    if not message.strip():
        logging.info("זוהה סוג משימה: general")
        return TaskIdentification(
            task_type="general",
            specific_intent="empty",
            confidence_score=0.1
        )
    
    logging.info("זוהה סוג משימה: general")
    return TaskIdentification(
        task_type="general",
        specific_intent="general",
        confidence_score=0.5
    )

def _get_specific_intent(message: str, task_type: str) -> str:
    """
    זיהוי כוונה ספציפית בתוך סוג המשימה
    
    Args:
        message: הודעת המשתמש
        task_type: סוג המשימה
        
    Returns:
        הכוונה הספציפית
    """
    message_lower = message.lower()
    
    if task_type == "weather":
        if "גשם" in message_lower:
            return "rain"
        elif "טמפרטורה" in message_lower:
            return "temperature"
        return "general_weather"
        
    elif task_type == "add_product":
        return "add_product"
        
    elif task_type == "update_product":
        if "מחיר" in message_lower:
            return "update_price"
        elif "כמות" in message_lower:
            return "update_quantity"
        elif "תיאור" in message_lower:
            return "update_description"
        return "general_update"
        
    elif task_type == "view_orders":
        if "סטטוס" in message_lower or "מצב" in message_lower:
            return "order_status"
        return "view_all_orders"
        
    elif task_type == "help":
        return "general_help"
        
    return "general"

def get_task_specific_prompt(task_type: str, message: str) -> str:
    """
    קבלת פרומפט מותאם למשימה
    
    Args:
        task_type: סוג המשימה
        message: הודעת המשתמש
        
    Returns:
        פרומפט מותאם
    """
    prompts = {
        "weather": """
        אתה עוזר שמספק מידע על מזג אוויר.
        אתה מבין היטב תחזיות ונתוני מזג אוויר.
        אתה תמיד מציין את המקור לנתונים שאתה מספק.
        """,
        
        "add_product": """
        אתה עוזר שמסייע בניהול מוצרים בחנות.
        אתה מבין היטב את המערכת של WooCommerce.
        אתה תמיד מוודא שכל הפרטים הנדרשים קיימים.
        """,
        
        "update_product": """
        אתה עוזר שמסייע בעדכון מוצרים בחנות.
        אתה מבין היטב את המערכת של WooCommerce.
        אתה תמיד מוודא שהעדכונים נשמרים כראוי.
        """,
        
        "view_orders": """
        אתה עוזר שמציג מידע על הזמנות.
        אתה מבין היטב את מערכת ההזמנות.
        אתה תמיד מארגן את המידע בצורה ברורה ומסודרת.
        """,
        
        "help": """
        אתה עוזר שמספק הדרכה ועזרה.
        אתה מסביר דברים בצורה ברורה ופשוטה.
        אתה תמיד מוודא שהמשתמש הבין את ההסבר.
        """,
        
        "general": """
        אתה עוזר ידידותי שמנהל שיחה.
        אתה עונה בצורה טבעית ונעימה.
        אתה תמיד מנסה להבין את כוונת המשתמש.
        """
    }
    
    base_prompt = prompts.get(task_type, prompts["general"])
    return f"{base_prompt}\n\nהודעת המשתמש: {message}" 