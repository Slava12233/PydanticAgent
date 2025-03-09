"""
מודול בסיסי ל-Agent
"""
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent as PydanticAgent
import os
import logfire

from src.core.config import OPENAI_MODEL
from src.models.responses import ChatResponse

class BaseAgent:
    """מחלקה בסיסית ל-Agent"""
    
    def __init__(self, model_name: str = None, fallback_model_name: str = 'openai:gpt-3.5-turbo'):
        """אתחול ה-Agent"""
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
        
        logfire.info('agent_initialized', model=model_name)
    
    def _configure_agent(self):
        """הגדרות נוספות ל-Agent"""
        # הערה: PydanticAgent לא תומך ב-register_tool באופן ישיר
        pass
    
    async def _initialize_fallback_agent(self):
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
    
    async def _get_model_response(self, prompt: str) -> str:
        """
        קבלת תשובה מהמודל
        
        Args:
            prompt: הפרומפט לשליחה למודל
            
        Returns:
            תשובת המודל
        """
        try:
            # יצירת פרומפט מלא
            system_prompt = "אתה עוזר מועיל שעונה בעברית בלבד."
            full_prompt = f"{system_prompt}\n\nUSER: {prompt}\nASSISTANT:"
            
            response = await self.agent.run(full_prompt)
            return response.data
        except Exception as e:
            logfire.error('model_response_error', error=str(e))
            return await self._try_fallback_model(prompt)
    
    async def _try_fallback_model(self, prompt: str, error_type: str = "general") -> str:
        """
        ניסיון להשתמש במודל גיבוי
        
        Args:
            prompt: הפרומפט לשליחה למודל
            error_type: סוג השגיאה שגרמה לשימוש במודל גיבוי
            
        Returns:
            תשובת המודל או הודעת שגיאה
        """
        try:
            await self._initialize_fallback_agent()
            
            # יצירת פרומפט מלא
            system_prompt = "אתה עוזר מועיל שעונה בעברית בלבד."
            full_prompt = f"{system_prompt}\n\nUSER: {prompt}\nASSISTANT:"
            
            response = await self.fallback_agent.run(full_prompt)
            return response.data
        except Exception as e:
            logfire.error('fallback_model_error', error=str(e))
            return await self._get_simple_response(prompt, error_type)
    
    async def _get_simple_response(self, user_message: str, error_type: str = "general") -> str:
        """
        יצירת תשובה פשוטה ללא שימוש במודל חיצוני במקרה של שגיאה חמורה
        
        Args:
            user_message: הודעת המשתמש
            error_type: סוג השגיאה
            
        Returns:
            תשובה פשוטה
        """
        if error_type == "quota":
            return (
                "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                "נראה שיש בעיה עם מכסת השימוש ב-API. "
                "אנא נסה להשתמש בפקודה /switch_model gpt-3.5-turbo כדי לעבור למודל אחר, "
                "או נסה שוב מאוחר יותר."
            )
        else:
            return (
                "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                "אנא נסה שוב מאוחר יותר."
            )

    async def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> ChatResponse:
        """
        קבלת תשובה מהסוכן
        
        Args:
            message: הודעת המשתמש
            context: הקשר השיחה (אופציונלי)
            
        Returns:
            תשובת הסוכן
        """
        try:
            # בניית פרומפט עם הקשר השיחה
            prompt = "אתה עוזר אישי חכם ומועיל. ענה על שאלות המשתמש בצורה מקיפה ומדויקת.\n\n"
            
            # הוספת זיכרונות רלוונטיים לפרומפט
            if context and "memories" in context and context["memories"]:
                memories_text = "\n".join([f"- {memory['content']} ({memory['role']})" for memory in context["memories"]])
                prompt += f"היסטוריית השיחה:\n{memories_text}\n\n"
            
            prompt += f"שאלת המשתמש: {message}"
            
            # קבלת תשובה מהמודל
            response_text = await self._get_model_response(prompt)
            
            return ChatResponse(
                message=response_text,
                confidence=0.8,
                context=context
            )
        except Exception as e:
            logfire.error("get_response_error", error=str(e))
            return ChatResponse(
                message="מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות.",
                confidence=0.1,
                context=context
            )