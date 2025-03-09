"""
מודול לזיהוי משימות
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel

from src.agents.prompts.task_prompts import get_task_prompt
from src.core.task_identification.intents.customer_intent import identify_specific_intent

class TaskIdentification(BaseModel):
    """מודל לתוצאות זיהוי משימה"""
    task_type: str
    confidence: float
    params: Dict[str, Any] = {}

async def identify_task(message: str) -> TaskIdentification:
    """
    זיהוי סוג המשימה מתוך הודעת המשתמש
    
    Args:
        message: הודעת המשתמש
        
    Returns:
        תוצאות הזיהוי
    """
    # זיהוי כוונה ספציפית
    intent = await identify_specific_intent(message)
    
    if intent:
        return TaskIdentification(
            task_type=intent.intent_type,
            confidence=intent.confidence,
            params=intent.params
        )
    
    # TODO: להוסיף זיהוי כללי יותר
    return TaskIdentification(
        task_type="general",
        confidence=0.5
    )

def get_task_specific_prompt(task: TaskIdentification) -> str:
    """
    קבלת פרומפט ספציפי למשימה
    
    Args:
        task: תוצאות זיהוי המשימה
        
    Returns:
        פרומפט מותאם למשימה
    """
    return get_task_prompt(task.task_type, task.params) 