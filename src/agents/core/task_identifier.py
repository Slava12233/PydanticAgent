"""
מודול לזיהוי סוג המשימה וכוונת המשתמש
"""

import logfire
from typing import Tuple
from src.agents.models.responses import TaskIdentification
from src.agents.promts import identify_task_type
from src.tools.intent import identify_specific_intent
from src.agents.prompts.prompt_manager import prompt_manager

async def identify_task(user_message: str) -> TaskIdentification:
    """
    זיהוי סוג המשימה לפי תוכן ההודעה
    
    Args:
        user_message: הודעת המשתמש
        
    Returns:
        TaskIdentification עם פרטי המשימה שזוהתה
    """
    # שימוש בפונקציה מקובץ promts.py
    task_type = identify_task_type(user_message)
        
    # שימוש במנגנון זיהוי כוונות ספציפיות
    task_type_from_intent, specific_intent, score = identify_specific_intent(user_message)
    
    # אם זוהתה כוונה ספציפית עם ציון גבוה, נשתמש בסוג המשימה שזוהה
    if score > 15.0:
        logfire.info(f"זוהתה כוונה ספציפית: {task_type_from_intent}/{specific_intent} (ציון: {score})")
        return TaskIdentification(
            task_type=task_type_from_intent,
            specific_intent=specific_intent,
            confidence_score=score
        )
    
    logfire.info(f"זוהה סוג משימה: {task_type}")
    return TaskIdentification(
        task_type=task_type,
        specific_intent="general",
        confidence_score=0.5
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