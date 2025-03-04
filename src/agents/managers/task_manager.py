"""
מודול לניהול משימות
"""
from typing import Tuple, Dict, Any
import logfire

from src.agents.prompts import identify_task_type, build_prompt
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
        # שימוש בפונקציה מקובץ promts.py
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
            history_text: טקסט היסטוריית השיחה (אופציונלי)
            
        Returns:
            פרומפט מותאם
        """
        # פרומפט בסיסי
        base_prompt = (
            "אתה עוזר אישי ידידותי שעונה בעברית. "
            "אתה עוזר למשתמשים בשאלות שונות ומספק מידע מדויק ושימושי. "
            "אתה תמיד מנסה לעזור בצורה הטובה ביותר, ואם אין לך מידע מספיק, "
            "אתה מבקש פרטים נוספים או מציע דרכים אחרות לעזור. "
            "כאשר מסופקים לך מסמכים רלוונטיים, אתה חייב להשתמש במידע מהם כדי לענות על שאלות המשתמש. "
            "אם המשתמש שואל על מידע שנמצא במסמכים, השתמש במידע זה בתשובתך ואל תאמר שאין לך מידע. "
            "אם המשתמש שואל על פרויקט או מסמך ספציפי, חפש את המידע במסמכים הרלוונטיים ותן תשובה מפורטת."
        )
        
        # הוספת הנחיות לגבי מסמכים
        if task_type == "document_management":
            base_prompt += (
                "\n\nאתה יכול לעזור למשתמשים למצוא מידע במסמכים שלהם. "
                "כאשר מסופקים לך מסמכים רלוונטיים, השתמש במידע מהם כדי לענות על שאלות המשתמש. "
                "אם המשתמש שואל על מסמך ספציפי, התייחס למידע מאותו מסמך. "
                "אם המשתמש מבקש סיכום או מידע על מסמך, ספק תשובה מפורטת המבוססת על תוכן המסמך. "
                "אם אין לך מספיק מידע מהמסמכים, ציין זאת בבירור ובקש מהמשתמש לספק פרטים נוספים."
            )
        
        # הוספת היסטוריית השיחה אם קיימת
        if history_text:
            prompt = f"{base_prompt}\n\nהיסטוריית השיחה:\n{history_text}\n\nהודעת המשתמש: {user_message}"
        else:
            prompt = f"{base_prompt}\n\nהודעת המשתמש: {user_message}"
        
        return prompt 