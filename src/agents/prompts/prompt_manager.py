"""
מודול לניהול פרומפטים
"""

import os
import yaml
import logfire
from typing import Optional, Dict, Any

class PromptManager:
    """מנהל הפרומפטים של המערכת"""
    
    def __init__(self):
        """אתחול מנהל הפרומפטים"""
        self.prompts = {}
        self._load_prompts()
        
    def _load_prompts(self):
        """טעינת כל קבצי הפרומפטים"""
        try:
            # קריאת קובץ הפרומפטים הבסיסי
            base_path = os.path.join(os.path.dirname(__file__), 'base_prompts.yaml')
            with open(base_path, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
                
            logfire.info('prompts_loaded', count=len(self.prompts))
        except Exception as e:
            logfire.error('prompt_loading_error', error=str(e))
            raise RuntimeError(f"שגיאה בטעינת הפרומפטים: {e}")
    
    def get_base_prompt(self) -> str:
        """
        קבלת הפרומפט הבסיסי
        
        Returns:
            הפרומפט הבסיסי
        """
        return self.prompts.get('base', {}).get('default', '')
    
    def get_task_prompt(self, task_type: str) -> str:
        """
        קבלת פרומפט ספציפי למשימה
        
        Args:
            task_type: סוג המשימה
            
        Returns:
            הפרומפט המתאים למשימה
        """
        return self.prompts.get('task_specific', {}).get(task_type, '')
    
    def get_error_message(self, error_type: str) -> str:
        """
        קבלת הודעת שגיאה
        
        Args:
            error_type: סוג השגיאה
            
        Returns:
            הודעת השגיאה המתאימה
        """
        return self.prompts.get('errors', {}).get(error_type, self.prompts.get('errors', {}).get('general', ''))
    
    def format_conversation_history(self, history: str, message: str) -> str:
        """
        פורמוט היסטוריית שיחה
        
        Args:
            history: היסטוריית השיחה
            message: ההודעה הנוכחית
            
        Returns:
            טקסט מפורמט
        """
        template = self.prompts.get('templates', {}).get('conversation_history', '')
        return template.format(history=history, message=message)
    
    def format_context_info(self, context: str) -> str:
        """
        פורמוט מידע הקשר
        
        Args:
            context: מידע ההקשר
            
        Returns:
            טקסט מפורמט
        """
        template = self.prompts.get('templates', {}).get('context_info', '')
        return template.format(context=context)
    
    def build_prompt(self, task_type: str, message: str, history: Optional[str] = None, context: Optional[str] = None) -> str:
        """
        בניית פרומפט מלא
        
        Args:
            task_type: סוג המשימה
            message: הודעת המשתמש
            history: היסטוריית השיחה (אופציונלי)
            context: מידע הקשר (אופציונלי)
            
        Returns:
            הפרומפט המלא
        """
        # התחלה עם הפרומפט הבסיסי
        prompt_parts = [self.get_base_prompt()]
        
        # הוספת פרומפט ספציפי למשימה אם קיים
        task_prompt = self.get_task_prompt(task_type)
        if task_prompt:
            prompt_parts.append(task_prompt)
        
        # הוספת היסטוריית שיחה אם קיימת
        if history:
            prompt_parts.append(self.format_conversation_history(history, message))
        else:
            prompt_parts.append(f"הודעת המשתמש: {message}")
        
        # הוספת מידע הקשר אם קיים
        if context:
            prompt_parts.append(self.format_context_info(context))
        
        return "\n\n".join(prompt_parts)

# יצירת מופע גלובלי של מנהל הפרומפטים
prompt_manager = PromptManager() 