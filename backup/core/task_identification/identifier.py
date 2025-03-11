"""
מודול מרכזי לזיהוי משימות
"""
from typing import Optional, List, Dict, Any
from .models import TaskIdentification, IntentRecognitionResult, TaskContext
from .intents.product_intent import identify_product_intent
from .intents.order_intent import identify_order_intent
from .intents.customer_intent import identify_customer_intent

async def identify_task(
    message: str,
    context: Optional[TaskContext] = None
) -> TaskIdentification:
    """
    זיהוי סוג המשימה מתוך הודעת המשתמש
    
    Args:
        message: הודעת המשתמש
        context: הקשר המשימה (אופציונלי)
        
    Returns:
        תוצאות הזיהוי
    """
    # רשימת כל מזהי הכוונות
    intent_recognizers = [
        identify_product_intent,
        identify_order_intent,
        identify_customer_intent
    ]
    
    # הרצת כל המזהים וקבלת התוצאות
    results: List[IntentRecognitionResult] = []
    for recognizer in intent_recognizers:
        result = await recognizer(message, context)
        if result and result.confidence > 0.5:
            results.append(result)
    
    # בחירת התוצאה עם הביטחון הגבוה ביותר
    if results:
        best_result = max(results, key=lambda x: x.confidence)
        return TaskIdentification(
            task_type=best_result.intent_type,
            confidence=best_result.confidence,
            params=best_result.params,
            context=context.dict() if context else None
        )
    
    # אם לא זוהתה כוונה ספציפית, החזרת משימה כללית
    return TaskIdentification(
        task_type="general",
        confidence=0.5,
        context=context.dict() if context else None
    )

def get_task_specific_prompt(task: TaskIdentification) -> str:
    """
    קבלת פרומפט ספציפי למשימה
    
    Args:
        task: תוצאות זיהוי המשימה
        
    Returns:
        פרומפט מותאם למשימה
    """
    # TODO: להעביר את הלוגיקה של הפרומפטים לקובץ prompts.py
    from .prompts import get_task_prompt
    return get_task_prompt(task.task_type, task.params) 