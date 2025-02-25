from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
import logfire
import os
import sys
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class ChatResponse(BaseModel):
    """מודל לתגובת הצ'אט המובנית"""
    text: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None

class TelegramAgent:
    """מחלקה המרכזת את כל הלוגיקה של ה-Agent"""
    
    def __init__(self, model_name: str = 'openai:gpt-4'):
        """אתחול ה-Agent"""
        self.agent = PydanticAgent(model_name)
        self._configure_agent()
    
    def _configure_agent(self):
        """הגדרות נוספות ל-Agent"""
        # כאן אפשר להוסיף כלים, הגדרות סיסטם וכדומה
        pass
    
    async def get_response(self, 
                           user_message: str, 
                           history: List[Dict[str, Any]] = None) -> str:
        """קבלת תשובה מה-Agent"""
        with logfire.span('agent_get_response', message_length=len(user_message)):
            # בניית הפרומפט עם היסטוריה
            history_text = ""
            if history:
                history_text = "היסטוריית שיחה:\n" + "\n".join([
                    f"User: {msg['message']}\nAssistant: {msg['response']}" 
                    for msg in history
                ]) + "\n\n"
            
            prompt = (
                "אתה עוזר ידידותי שעונה בעברית. "
                "ענה בקצרה ובצורה ממוקדת. "
                "אל תחזור על המילים של השאלה בתשובה.\n\n"
                f"{history_text}"
                f"User: {user_message}\n"
                "Assistant: "
            )
            
            logfire.info('sending_prompt_to_model', prompt_length=len(prompt))
            result = await self.agent.run(prompt)
            logfire.info('received_model_response', response_length=len(result.data))
            
            return result.data
    
    async def stream_response(self, 
                             user_message: str, 
                             history: List[Dict[str, Any]] = None):
        """הזרמת תשובה מה-Agent - שימושי לתגובות בזמן אמת"""
        with logfire.span('agent_stream_response', message_length=len(user_message)):
            # בניית הפרומפט (כמו ב-get_response)
            history_text = ""
            if history:
                history_text = "היסטוריית שיחה:\n" + "\n".join([
                    f"User: {msg['message']}\nAssistant: {msg['response']}" 
                    for msg in history
                ]) + "\n\n"
            
            prompt = (
                "אתה עוזר ידידותי שעונה בעברית. "
                "ענה בקצרה ובצורה ממוקדת. "
                "אל תחזור על המילים של השאלה בתשובה.\n\n"
                f"{history_text}"
                f"User: {user_message}\n"
                "Assistant: "
            )
            
            logfire.info('streaming_prompt_to_model', prompt_length=len(prompt))
            
            async with self.agent.run_stream(prompt) as stream_result:
                async for chunk in stream_result.stream_text():
                    yield chunk 