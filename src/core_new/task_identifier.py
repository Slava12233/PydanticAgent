"""
מודול לזיהוי סוג המשימה וכוונת המשתמש

מודול זה משלב את היכולות של זיהוי משימות בסיסי עם מערכת זיהוי כוונות מתקדמת.
הוא תומך הן בזיהוי לפי מילות מפתח והן בזיהוי סמנטי מתקדם.
"""

import logfire
from typing import Optional, Tuple, Dict, List
from pydantic import BaseModel

from src.agents.models.responses import TaskIdentification
from src.agents.prompts.task_prompts import identify_task_type
from src.tools.intent import identify_specific_intent
from src.agents.prompts.prompt_manager import prompt_manager

# מילות מפתח בסיסיות למשימות שונות - משמשות כגיבוי למערכת הזיהוי המתקדמת
BASIC_TASK_KEYWORDS = {
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

def _identify_task_basic(message: str) -> Tuple[str, float]:
    """
    זיהוי בסיסי של משימה לפי מילות מפתח
    
    Args:
        message: הודעת המשתמש
        
    Returns:
        tuple של סוג המשימה וציון הביטחון
    """
    message_lower = message.lower()
    task_scores = {task_type: 0 for task_type in BASIC_TASK_KEYWORDS}
    
    for task_type, keywords in BASIC_TASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                task_scores[task_type] += 1
    
    if not any(task_scores.values()):
        return "general", 0.1
        
    best_task = max(task_scores.items(), key=lambda x: x[1])
    confidence = min(best_task[1] / len(BASIC_TASK_KEYWORDS[best_task[0]]), 1.0)
    
    return best_task[0], confidence

async def identify_task(message: str, context: Optional[str] = None) -> TaskIdentification:
    """
    זיהוי סוג המשימה מתוך הודעה
    
    משלב זיהוי מתקדם עם זיהוי בסיסי לפי מילות מפתח כגיבוי
    
    Args:
        message: הודעת המשתמש
        context: הקשר השיחה (אופציונלי)
        
    Returns:
        TaskIdentification עם פרטי המשימה שזוהתה
    """
    # ניסיון זיהוי מתקדם
    try:
        # שימוש במנגנון זיהוי כוונות ספציפיות
        task_type_from_intent, specific_intent, score = identify_specific_intent(message)
        
        # אם זוהתה כוונה ספציפית עם ציון גבוה
        if score > 15.0:
            logfire.info(f"זוהתה כוונה ספציפית: {task_type_from_intent}/{specific_intent} (ציון: {score})")
            return TaskIdentification(
                task_type=task_type_from_intent,
                specific_intent=specific_intent,
                confidence_score=score
            )
            
        # שימוש בפונקציה מקובץ task_prompts.py
        task_type = identify_task_type(message)
        if task_type != "general":
            logfire.info(f"זוהה סוג משימה: {task_type}")
            return TaskIdentification(
                task_type=task_type,
                specific_intent="general",
                confidence_score=0.5
            )
    
    except Exception as e:
        logfire.error(f"שגיאה בזיהוי מתקדם: {str(e)}")
    
    # זיהוי בסיסי כגיבוי
    task_type, confidence = _identify_task_basic(message)
    logfire.info(f"זוהה סוג משימה בסיסי: {task_type} (ביטחון: {confidence})")
    
    return TaskIdentification(
        task_type=task_type,
        specific_intent="general",
        confidence_score=confidence
    )

def get_task_specific_prompt(task_type: str, user_message: str, history_text: str = "") -> str:
    """
    בניית פרומפט מותאם לסוג המשימה
    
    Args:
        task_type: סוג המשימה
        user_message: הודעת המשתמש
        history_text: טקסט היסטוריית השיחה (אופציונלי)
        
    Returns:
        פרומפט מותאם
    """
    return prompt_manager.build_prompt(
        task_type=task_type,
        message=user_message,
        history=history_text if history_text else None
    ) 