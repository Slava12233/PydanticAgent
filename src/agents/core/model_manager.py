"""
מודול לניהול המודל והאינטראקציה איתו
"""

import logfire
from typing import Optional
from pydantic_ai import Agent as PydanticAgent
from src.core.config import OPENAI_MODEL
from src.agents.prompts.prompt_manager import prompt_manager

class ModelManager:
    """מנהל המודל והאינטראקציה איתו"""
    
    def __init__(self, model_name: Optional[str] = None, fallback_model_name: str = 'openai:gpt-3.5-turbo'):
        """
        אתחול מנהל המודל
        
        Args:
            model_name: שם המודל הראשי (אופציונלי)
            fallback_model_name: שם מודל הגיבוי
        """
        # אם לא סופק מודל, נשתמש במודל מקובץ ההגדרות
        if model_name is None:
            model_name = OPENAI_MODEL or 'gpt-3.5-turbo'
            
        self.primary_model_name = model_name
        self.fallback_model_name = fallback_model_name
        
        # בדיקה אם המודל הוא של Anthropic
        if 'claude' in model_name.lower() and not model_name.startswith('anthropic:'):
            model_name = f"anthropic:{model_name}"
        elif not ':' in model_name:
            # אם לא צוין ספק המודל, נניח שזה OpenAI
            model_name = f"openai:{model_name}"
            
        self.agent = PydanticAgent(model_name)
        self.fallback_agent = None  # יאותחל רק בעת הצורך
        
        logfire.info('model_manager_initialized', model=model_name)
    
    async def initialize_fallback_agent(self):
        """אתחול סוכן גיבוי אם עדיין לא אותחל"""
        if self.fallback_agent is None:
            fallback_model = self.fallback_model_name
            
            # בדיקה אם המודל הוא של Anthropic
            if 'claude' in fallback_model.lower() and not fallback_model.startswith('anthropic:'):
                fallback_model = f"anthropic:{fallback_model}"
            elif not ':' in fallback_model:
                # אם לא צוין ספק המודל, נניח שזה OpenAI
                fallback_model = f"openai:{fallback_model}"
                
            logfire.info('initializing_fallback_agent', model=fallback_model)
            self.fallback_agent = PydanticAgent(fallback_model)
    
    def get_simple_response(self, user_message: str, error_type: str = "general") -> str:
        """
        יצירת תשובה פשוטה ללא שימוש במודל חיצוני במקרה של שגיאה חמורה
        
        Args:
            user_message: הודעת המשתמש
            error_type: סוג השגיאה
            
        Returns:
            תשובה פשוטה
        """
        return prompt_manager.get_error_message(error_type) 