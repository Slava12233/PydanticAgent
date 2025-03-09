"""
מודול לניהול המודל והאינטראקציה איתו
"""

import logfire
from typing import Optional, Dict, Any
from pydantic_ai import Agent as PydanticAgent
from .config import OPENAI_MODEL
from src.core.prompts.prompt_manager import PromptManager

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
        prompt_manager = PromptManager()
        return prompt_manager.get_error_message(error_type) 
        
    async def get_response(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        קבלת תשובה מהמודל
        
        Args:
            message: הודעת המשתמש
            context: הקשר נוסף לשיחה
            
        Returns:
            תשובת המודל
        """
        if context is None:
            context = {}
            
        prompt_manager = PromptManager()
        
        try:
            with logfire.span("model_response"):
                # בניית הפרומפט עם ההקשר
                system_prompt = prompt_manager.get_system_prompt()
                
                # וידוא שהפרומפט מדגיש את הצורך לענות בעברית
                if "בעברית" not in system_prompt:
                    system_prompt += "\nחשוב מאוד: אתה חייב לענות בעברית בלבד!"
                
                # בניית היסטוריית השיחה בפורמט מובנה
                conversation_history = ""
                
                # הוספת זיכרונות רלוונטיים לשיחה
                if "memories" in context and context["memories"]:
                    # מיון הזיכרונות לפי זמן
                    sorted_memories = sorted(
                        context["memories"], 
                        key=lambda x: x["timestamp"]
                    )
                    
                    # הוספת הזיכרונות להיסטוריה בפורמט ברור
                    for memory in sorted_memories:
                        role = memory["role"].upper()
                        content = memory["content"]
                        conversation_history += f"\n{role}: {content}"
                
                # יצירת פרומפט מלא עם היסטוריית השיחה והשאלה הנוכחית
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"היסטוריית השיחה:{conversation_history}\n\n"
                    f"USER: {message}\n"
                    f"ASSISTANT:"
                )
                
                logfire.info("sending_prompt_to_model", prompt_length=len(full_prompt))
                
                # יצירת אובייקט Agent חדש עם הפרומפט המערכתי הנכון
                agent_with_prompt = PydanticAgent(
                    self.primary_model_name,
                    system_prompt=system_prompt
                )
                
                # שליחת הבקשה למודל
                response = await agent_with_prompt.run(full_prompt)
                
                logfire.info("model_response_received", model=self.primary_model_name)
                return response.data
                
        except Exception as e:
            logfire.error("model_response_error", error=str(e))
            # במקרה של שגיאה, ננסה להשתמש במודל גיבוי
            try:
                await self.initialize_fallback_agent()
                if self.fallback_agent:
                    # יצירת אובייקט Agent חדש עם הפרומפט המערכתי הנכון
                    fallback_agent_with_prompt = PydanticAgent(
                        self.fallback_model_name,
                        system_prompt=system_prompt
                    )
                    
                    # שליחת הבקשה למודל גיבוי
                    response = await fallback_agent_with_prompt.run(full_prompt)
                    logfire.info("fallback_model_response_received", model=self.fallback_model_name)
                    return response.data
            except Exception as fallback_error:
                logfire.error("fallback_model_error", error=str(fallback_error))
            
            # אם גם מודל הגיבוי נכשל, החזרת הודעת שגיאה
            error_message = prompt_manager.get_error_message()
            return error_message