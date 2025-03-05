"""
מודול לניהול משימות
"""
from typing import Tuple, Dict, Any
import logfire

from src.agents.prompts.task_prompts import identify_task_type, get_task_prompt
from src.agents.prompts.base_prompts import build_prompt
from src.tools.intent import identify_specific_intent

class TaskManager:
    """מחלקה לניהול משימות"""
    
    @staticmethod
    async def identify_task_type(user_message: str) -> Tuple[str, str, float]:
        """
        זיהוי סוג המשימה לפי תוכן ההודעה
        
        Args:
            user_message: הודעת המשתמש
            
        Returns:
            סוג המשימה: 'product_management', 'order_management', 'customer_management',
                        'inventory_management', 'sales_analysis', 'seo_optimization',
                        'pricing_strategy', 'marketing', 'document_management', 'general'
            סוג הכוונה הספציפית
            ציון הביטחון בזיהוי
        """
        # שימוש בפונקציה מקובץ task_prompts.py
        task_type = identify_task_type(user_message)
            
        # שימוש במנגנון זיהוי כוונות ספציפיות
        task_type_from_intent, specific_intent, score = identify_specific_intent(user_message)
        
        # אם זוהתה כוונה ספציפית עם ציון גבוה, נשתמש בסוג המשימה שזוהה
        if score > 15.0:
            logfire.info(f"זוהתה כוונה ספציפית: {task_type_from_intent}/{specific_intent} (ציון: {score})")
            return task_type_from_intent, specific_intent, score
        
        logfire.info(f"זוהה סוג משימה: {task_type}")
        return task_type, "general", 0.5
    
    @staticmethod
    def get_task_specific_prompt(task_type: str, user_message: str, history_text: str = "") -> str:
        """
        בניית פרומפט מותאם לסוג המשימה
        
        Args:
            task_type: סוג המשימה
            user_message: הודעת המשתמש
            history_text: טקסט היסטוריית השיחה
            
        Returns:
            פרומפט מותאם למשימה
        """
        return get_task_prompt(task_type, user_message, history_text) 