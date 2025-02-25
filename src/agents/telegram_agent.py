from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
import logfire
import os
import sys
import asyncio
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ייבוא מסד הנתונים
from src.database.database import db
from src.database.rag_utils import search_documents

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
        # וידוא שמסד הנתונים מאותחל
        if db.engine is None:
            db.init_db()
        self._configure_agent()
    
    def _configure_agent(self):
        """הגדרות נוספות ל-Agent"""
        # הערה: PydanticAgent לא תומך ב-register_tool באופן ישיר
        # הכלי RAG מופעל ישירות בפונקציות get_response ו-stream_response
        pass
    
    async def retrieve_context(self, query: str) -> str:
        """כלי לחיפוש במערכת ה-RAG"""
        with logfire.span('retrieve_context', query=query):
            chunks = await search_documents(query, limit=5, min_similarity=0.0)
            if not chunks:
                return "לא נמצא מידע רלוונטי."
            
            # בניית הפורמט עבור הסוכן - שיפור הפורמט להצגה ברורה יותר
            context = "\n\n".join([
                f"### {chunk['title']}\n" +
                f"מקור: {chunk['source']}\n" +
                f"רלוונטיות: {chunk['similarity']:.2f}\n\n" +
                f"{chunk['content']}"
                for chunk in chunks
            ])
            
            logfire.info('rag_context_found', chunks_count=len(chunks))
            return f"מידע רלוונטי שנמצא:\n\n{context}"
    
    async def get_response(self, 
                           user_id: int,
                           user_message: str, 
                           history: List[Dict[str, Any]] = None,
                           use_rag: bool = True) -> str:
        """קבלת תשובה מה-Agent עם היסטוריה ו-RAG"""
        with logfire.span('agent_get_response', message_length=len(user_message)):
            # בניית הפרומפט עם היסטוריה
            history_text = ""
            if history:
                history_text = "היסטוריית שיחה:\n" + "\n".join([
                    f"User: {msg['message']}\nAssistant: {msg['response']}" 
                    for msg in history
                ]) + "\n\n"
            
            # בניית הפרומפט הבסיסי - שיפור הפרומפט
            prompt = (
                "אתה עוזר אישי ידידותי שעונה בעברית. "
                "אתה מתמחה במתן מידע אישי ומותאם למשתמש. "
                "ענה בצורה מפורטת ומדויקת. "
                "אם יש לך מידע אישי על המשתמש או משפחתו, השתמש בו כדי לענות בצורה אישית. "
                "השתמש במידע נוסף שמסופק לך רק אם הוא רלוונטי לשאלה.\n\n"
                f"{history_text}"
                f"User: {user_message}\n"
                "Assistant: "
            )
            
            # בדיקה אם יש צורך לחפש מידע נוסף ב-RAG
            if use_rag:
                # הפעלת RAG כדי למצוא מידע רלוונטי
                context = await self.retrieve_context(user_message)
                if "לא נמצא מידע רלוונטי" not in context:
                    prompt = (
                        "אתה עוזר אישי ידידותי שעונה בעברית. "
                        "אתה מתמחה במתן מידע אישי ומותאם למשתמש. "
                        "ענה בצורה מפורטת ומדויקת. "
                        "המידע הנוסף שמסופק לך הוא מידע אישי על המשתמש או משפחתו. "
                        "התייחס למידע זה כאל עובדות מדויקות והשתמש בו כדי לענות על השאלה. "
                        "אם נשאלת שאלה ישירה על מידע שנמצא במסמכים, ענה עליה באופן ישיר ומדויק.\n\n"
                        f"מידע אישי על המשתמש:\n{context}\n\n"
                        f"{history_text}"
                        f"User: {user_message}\n"
                        "Assistant: "
                    )
            
            logfire.info('sending_prompt_to_model', prompt_length=len(prompt))
            result = await self.agent.run(prompt)
            response = result.data
            logfire.info('received_model_response', response_length=len(response))
            
            # שמירת ההודעה והתשובה במסד הנתונים
            db.save_message(user_id, user_message, response)
            
            return response
    
    async def stream_response(self, 
                             user_id: int,
                             user_message: str, 
                             history: List[Dict[str, Any]] = None,
                             use_rag: bool = True):
        """הזרמת תשובה מה-Agent עם תמיכה ב-RAG"""
        with logfire.span('agent_stream_response', message_length=len(user_message)):
            # בניית הפרומפט עם היסטוריה
            history_text = ""
            if history:
                history_text = "היסטוריית שיחה:\n" + "\n".join([
                    f"User: {msg['message']}\nAssistant: {msg['response']}" 
                    for msg in history
                ]) + "\n\n"
            
            # בניית הפרומפט הבסיסי - שיפור הפרומפט
            prompt = (
                "אתה עוזר אישי ידידותי שעונה בעברית. "
                "אתה מתמחה במתן מידע אישי ומותאם למשתמש. "
                "ענה בצורה מפורטת ומדויקת. "
                "אם יש לך מידע אישי על המשתמש או משפחתו, השתמש בו כדי לענות בצורה אישית. "
                "השתמש במידע נוסף שמסופק לך רק אם הוא רלוונטי לשאלה.\n\n"
                f"{history_text}"
                f"User: {user_message}\n"
                "Assistant: "
            )
            
            # בדיקה אם יש צורך לחפש מידע נוסף ב-RAG
            if use_rag:
                # הפעלת RAG כדי למצוא מידע רלוונטי
                context = await self.retrieve_context(user_message)
                if "לא נמצא מידע רלוונטי" not in context:
                    prompt = (
                        "אתה עוזר אישי ידידותי שעונה בעברית. "
                        "אתה מתמחה במתן מידע אישי ומותאם למשתמש. "
                        "ענה בצורה מפורטת ומדויקת. "
                        "המידע הנוסף שמסופק לך הוא מידע אישי על המשתמש או משפחתו. "
                        "התייחס למידע זה כאל עובדות מדויקות והשתמש בו כדי לענות על השאלה. "
                        "אם נשאלת שאלה ישירה על מידע שנמצא במסמכים, ענה עליה באופן ישיר ומדויק.\n\n"
                        f"מידע אישי על המשתמש:\n{context}\n\n"
                        f"{history_text}"
                        f"User: {user_message}\n"
                        "Assistant: "
                    )
            
            logfire.info('streaming_prompt_to_model', prompt_length=len(prompt))
            
            # שמירת התשובה המלאה לצורך שמירה במסד הנתונים
            full_response = ""
            
            async with self.agent.run_stream(prompt) as stream_result:
                async for chunk in stream_result.stream_text():
                    full_response += chunk
                    yield chunk
            
            # שמירת ההודעה והתשובה המלאה במסד הנתונים
            db.save_message(user_id, user_message, full_response) 