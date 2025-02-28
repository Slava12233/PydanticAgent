from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
import os
import sys
import asyncio
from datetime import datetime
from pydantic_ai.exceptions import ModelHTTPError

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'

import logfire
# נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
try:
    logfire.configure(
        token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7',
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
except (AttributeError, ImportError):
    # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
    logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')

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
    
    def __init__(self, model_name: str = 'openai:gpt-4', fallback_model_name: str = 'openai:gpt-3.5-turbo'):
        """אתחול ה-Agent"""
        self.primary_model_name = model_name
        self.fallback_model_name = fallback_model_name
        
        # בדיקה אם המודל הוא של Anthropic
        if 'claude' in model_name.lower() and not model_name.startswith('openai:'):
            model_name = f"anthropic:{model_name}"
        elif not ':' in model_name:
            # אם לא צוין ספק המודל, נניח שזה OpenAI
            model_name = f"openai:{model_name}"
            
        self.agent = PydanticAgent(model_name)
        self.fallback_agent = None  # יאותחל רק בעת הצורך
        # וידוא שמסד הנתונים מאותחל
        if db.engine is None:
            db.init_db()
        self._configure_agent()
        
        logfire.info('agent_initialized', model=model_name)
    
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
    
    async def _get_simple_response(self, user_message: str, error_type: str = "general") -> str:
        """יצירת תשובה פשוטה ללא שימוש במודל חיצוני במקרה של שגיאה חמורה"""
        # תשובות מותאמות לסוגי שגיאות שונים
        if error_type == "quota":
            return (
                f"מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                f"נראה שיש בעיה עם מכסת השימוש ב-API. "
                f"אנא נסה להשתמש בפקודה /switch_model gpt-3.5-turbo כדי לעבור למודל אחר, "
                f"או פנה למנהל המערכת. "
                f"\n\nהשאלה שלך הייתה: {user_message}"
            )
        elif error_type == "timeout":
            return (
                f"מצטער, הבקשה שלך נמשכה זמן רב מדי ונקטעה. "
                f"אנא נסה לשאול שאלה קצרה יותר או לחלק את השאלה למספר שאלות נפרדות. "
                f"\n\nהשאלה שלך הייתה: {user_message}"
            )
        elif error_type == "content_filter":
            return (
                f"מצטער, לא אוכל לענות על השאלה הזו בגלל מדיניות התוכן שלנו. "
                f"אנא נסה לנסח את השאלה בצורה אחרת. "
                f"\n\nהשאלה שלך הייתה: {user_message}"
            )
        else:  # שגיאה כללית
            return (
                f"מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                f"אנא נסה שוב מאוחר יותר או פנה למנהל המערכת. "
                f"\n\nהשאלה שלך הייתה: {user_message}"
            )
    
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
                try:
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
                except Exception as e:
                    logfire.error('rag_error', error=str(e))
                    # אם יש שגיאה ב-RAG, נמשיך בלעדיו
            
            logfire.info('sending_prompt_to_model', prompt_length=len(prompt))
            
            try:
                # ניסיון להשתמש במודל העיקרי
                result = await self.agent.run(prompt)
                response = result.data
                logfire.info('received_model_response', response_length=len(response))
            except ModelHTTPError as e:
                # בדיקה אם השגיאה היא בעיית מכסה (quota)
                error_message = str(e).lower()
                is_quota_error = "quota" in error_message or "exceeded" in error_message or "429" in error_message
                is_timeout_error = "timeout" in error_message or "timed out" in error_message
                is_content_filter = "content filter" in error_message or "content_filter" in error_message or "moderation" in error_message
                
                if is_quota_error:
                    logfire.warning('quota_exceeded_using_fallback', error=str(e))
                    
                    try:
                        # אתחול סוכן הגיבוי אם צריך
                        await self._initialize_fallback_agent()
                        
                        # ניסיון להשתמש במודל הגיבוי
                        result = await self.fallback_agent.run(prompt)
                        response = result.data
                        logfire.info('received_fallback_model_response', response_length=len(response))
                    except Exception as fallback_error:
                        # אם גם מודל הגיבוי נכשל, נחזיר תשובה פשוטה
                        logfire.error('fallback_model_error', error=str(fallback_error))
                        response = await self._get_simple_response(user_message, "quota")
                elif is_timeout_error:
                    # שגיאת timeout
                    logfire.error('timeout_error', error=str(e))
                    response = await self._get_simple_response(user_message, "timeout")
                elif is_content_filter:
                    # שגיאת סינון תוכן
                    logfire.error('content_filter_error', error=str(e))
                    response = await self._get_simple_response(user_message, "content_filter")
                else:
                    # שגיאה אחרת שאינה קשורה למכסה
                    logfire.error('model_error', error=str(e))
                    response = await self._get_simple_response(user_message, "general")
            except Exception as e:
                # שגיאה כללית
                logfire.error('general_error', error=str(e))
                response = await self._get_simple_response(user_message, "general")
            
            # שמירת ההודעה והתשובה במסד הנתונים
            try:
                db.save_message(user_id, user_message, response)
            except Exception as db_error:
                logfire.error('database_save_error', error=str(db_error))
            
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
                try:
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
                except Exception as e:
                    logfire.error('rag_error_in_stream', error=str(e))
                    # אם יש שגיאה ב-RAG, נמשיך בלעדיו
            
            logfire.info('streaming_prompt_to_model', prompt_length=len(prompt))
            
            # שמירת התשובה המלאה לצורך שמירה במסד הנתונים
            full_response = ""
            
            try:
                # ניסיון להשתמש במודל העיקרי
                async with self.agent.run_stream(prompt) as stream_result:
                    async for chunk in stream_result.stream_text():
                        full_response += chunk
                        yield chunk
            except ModelHTTPError as e:
                # בדיקה אם השגיאה היא בעיית מכסה (quota)
                error_message = str(e).lower()
                is_quota_error = "quota" in error_message or "exceeded" in error_message or "429" in error_message
                is_timeout_error = "timeout" in error_message or "timed out" in error_message
                is_content_filter = "content filter" in error_message or "content_filter" in error_message or "moderation" in error_message
                
                if is_quota_error:
                    logfire.warning('quota_exceeded_using_fallback_in_stream', error=str(e))
                    
                    try:
                        # אתחול סוכן הגיבוי אם צריך
                        await self._initialize_fallback_agent()
                        
                        # ניסיון להשתמש במודל הגיבוי
                        async with self.fallback_agent.run_stream(prompt) as fallback_stream:
                            async for chunk in fallback_stream.stream_text():
                                full_response += chunk
                                yield chunk
                    except Exception as fallback_error:
                        # אם גם מודל הגיבוי נכשל, נחזיר תשובה פשוטה
                        logfire.error('fallback_model_error_in_stream', error=str(fallback_error))
                        simple_response = await self._get_simple_response(user_message, "quota")
                        full_response = simple_response
                        yield simple_response
                elif is_timeout_error:
                    # שגיאת timeout
                    logfire.error('timeout_error_in_stream', error=str(e))
                    simple_response = await self._get_simple_response(user_message, "timeout")
                    full_response = simple_response
                    yield simple_response
                elif is_content_filter:
                    # שגיאת סינון תוכן
                    logfire.error('content_filter_error_in_stream', error=str(e))
                    simple_response = await self._get_simple_response(user_message, "content_filter")
                    full_response = simple_response
                    yield simple_response
                else:
                    # שגיאה אחרת שאינה קשורה למכסה
                    logfire.error('model_error_in_stream', error=str(e))
                    simple_response = await self._get_simple_response(user_message, "general")
                    full_response = simple_response
                    yield simple_response
            except Exception as e:
                # שגיאה כללית
                logfire.error('general_error_in_stream', error=str(e))
                simple_response = await self._get_simple_response(user_message, "general")
                full_response = simple_response
                yield simple_response
            
            # שמירת ההודעה והתשובה המלאה במסד הנתונים
            try:
                db.save_message(user_id, user_message, full_response)
            except Exception as db_error:
                logfire.error('database_save_error_in_stream', error=str(db_error)) 