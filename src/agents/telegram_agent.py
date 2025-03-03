from typing import List, Tuple, Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
import os
import sys
import asyncio
from datetime import datetime, timezone
from pydantic_ai.exceptions import ModelHTTPError
import json
import traceback

# ייבוא מודולים מקומיים
from src.agents.constants import GREETINGS
from src.agents.promts import identify_task_type, build_prompt

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
from src.services.rag_service import search_documents
from src.services.woocommerce.orders import get_orders, get_order, update_order_status, cancel_order, refund_order
from src.services.woocommerce.products import get_products, get_product, update_product, delete_product, create_product
from src.services.woocommerce.customers import get_customers, get_customer, create_customer, update_customer, delete_customer
from src.core.config import OPENAI_MODEL

from src.tools.managers import (
    ConversationContext,
    understand_context,
    resolve_pronouns,
    extract_context_from_history,
    learning_manager
)

# ייבוא מודול query_parser החדש
from src.tools.managers.query_parser import (
    parse_complex_query,
    is_comparative_query,
    is_hypothetical_query
)

class ChatResponse(BaseModel):
    """מודל לתגובת הצ'אט המובנית"""
    text: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None

class TelegramAgent:
    """מחלקה המרכזת את כל הלוגיקה של ה-Agent"""
    
    def __init__(self, model_name: str = None, fallback_model_name: str = 'openai:gpt-3.5-turbo'):
        """אתחול ה-Agent"""
        # אם לא סופק מודל, נשתמש במודל מקובץ ההגדרות
        if model_name is None:
            model_name = OPENAI_MODEL or 'gpt-3.5-turbo'
            
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
        
        # יצירת מנהל הקשר
        self.context_manager = ConversationContext()
        
        logfire.info('agent_initialized', model=model_name)
    
    def _configure_agent(self):
        """הגדרות נוספות ל-Agent"""
        # הערה: PydanticAgent לא תומך ב-register_tool באופן ישיר
        # הכלי RAG מופעל ישירות בפונקציות get_response ו-stream_response
        pass
    
    async def retrieve_context(self, query: str) -> str:
        """
        חיפוש מידע רלוונטי במאגר הידע לפי שאילתה
        
        Args:
            query: שאילתת החיפוש
            
        Returns:
            מחרוזת עם המידע הרלוונטי או הודעה שלא נמצא מידע
        """
        try:
            # בדיקה אם השאילתה קצרה מדי
            if len(query.strip()) <= 3:
                logfire.info('query_too_short', query=query)
                return "לא נמצא מידע רלוונטי. השאילתה קצרה מדי."
            
            logfire.info('searching_knowledge_base', query=query[:100])
            
            # שימוש בפונקציה search_documents מתוך rag_service
            from src.services.rag_service import search_documents
            
            # חיפוש מסמכים רלוונטיים
            try:
                chunks = await search_documents(query, limit=5, min_similarity=0.1)
                
                if not chunks:
                    logfire.info('no_relevant_chunks_found', query=query[:100])
                    return "לא נמצא מידע רלוונטי במאגר הידע."
                
                # בניית הקשר מהקטעים שנמצאו
                context_parts = []
                for chunk in chunks:
                    title = chunk.get('title', 'ללא כותרת')
                    source = chunk.get('source', 'לא ידוע')
                    similarity = chunk.get('similarity_percentage', 0)
                    content = chunk.get('content', '')
                    
                    chunk_text = f"### {title}\n"
                    chunk_text += f"מקור: {source}\n"
                    chunk_text += f"רלוונטיות: {similarity:.2f}%\n\n"
                    chunk_text += f"{content}"
                    
                    context_parts.append(chunk_text)
                
                context = "\n\n".join(context_parts)
                
                logfire.info('rag_context_found', chunks_count=len(chunks))
                return f"מידע רלוונטי שנמצא:\n\n{context}"
            except Exception as inner_e:
                logfire.error('search_documents_error', error=str(inner_e))
                return "לא ניתן לחפש במאגר הידע כרגע. אנא נסה שוב מאוחר יותר."
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logfire.error('retrieve_context_error', error=str(e), traceback=error_trace)
            return "לא ניתן לחפש במאגר הידע כרגע. אנא נסה שוב מאוחר יותר."
    
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
    
    async def _identify_task_type(self, user_message: str) -> Tuple[str, str, float]:
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
        from src.tools.intent import identify_specific_intent
        task_type_from_intent, specific_intent, score = identify_specific_intent(user_message)
        
        # אם זוהתה כוונה ספציפית עם ציון גבוה, נשתמש בסוג המשימה שזוהה
        if score > 15.0:
            logfire.info(f"זוהתה כוונה ספציפית: {task_type_from_intent}/{specific_intent} (ציון: {score})")
            return task_type_from_intent, specific_intent, score
        
        logfire.info(f"זוהה סוג משימה: {task_type}")
        return task_type, "general", 0.5
    
    def _get_task_specific_prompt(self, task_type: str, user_message: str, history_text: str = "") -> str:
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
    
    async def _get_simple_response(self, user_message: str, error_type: str = "general") -> str:
        """יצירת תשובה פשוטה ללא שימוש במודל חיצוני במקרה של שגיאה חמורה"""
        # תשובות מותאמות לסוגי שגיאות שונים
        if error_type == "quota":
            return (
                f"מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                f"נראה שיש בעיה עם מכסת השימוש ב-API. "
                f"אנא נסה להשתמש בפקודה /switch_model gpt-3.5-turbo כדי לעבור למודל אחר, "
                f"או פנה למנהל המערכת. "
                f"\n\nהשאלה שלך בנוגע לחנות WooCommerce הייתה: {user_message}"
            )
        elif error_type == "timeout":
            return (
                f"מצטער, הבקשה שלך בנוגע לחנות WooCommerce נמשכה זמן רב מדי ונקטעה. "
                f"אנא נסה לשאול שאלה קצרה יותר או לחלק את השאלה למספר שאלות נפרדות. "
                f"אתה יכול גם להשתמש בפקודות הספציפיות כמו /products, /orders, /customers וכו'. "
                f"\n\nהשאלה שלך הייתה: {user_message}"
            )
        elif error_type == "content_filter":
            return (
                f"מצטער, לא אוכל לענות על השאלה הזו כיוון שהיא עלולה להפר את מדיניות התוכן. "
                f"אנא נסח את השאלה מחדש או שאל שאלה אחרת בנוגע לחנות WooCommerce שלך. "
                f"אני כאן כדי לעזור לך בניהול החנות, ניתוח מכירות, ניהול מוצרים והזמנות."
            )
        else:
            return (
                f"מצטער, אירעה שגיאה בעת עיבוד השאלה שלך. "
                f"אנא נסה שוב מאוחר יותר או נסח את השאלה בצורה אחרת. "
                f"אם אתה מחפש מידע ספציפי, נסה להשתמש בפקודות כמו /products, /orders, /customers וכו'."
            )
    
    async def _try_fallback_model(self, prompt: str, error_type: str = "general") -> str:
        """
        ניסיון להשתמש במודל גיבוי במקרה של שגיאה במודל העיקרי
        
        Args:
            prompt: הפרומפט למודל
            error_type: סוג השגיאה
            
        Returns:
            תשובת המודל
        """
        try:
            # אתחול מודל הגיבוי אם צריך
            if not self.fallback_agent:
                await self._initialize_fallback_agent()
            
            # שימוש במודל הגיבוי
            result = await self.fallback_agent.run(prompt)
            response = result.data
            
            # אם התשובה היא אובייקט, ננסה לחלץ את הטקסט
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict) and ('text' in response or 'content' in response):
                return response.get('text', response.get('content', ''))
            elif isinstance(response, str):
                return response
            else:
                # אם לא הצלחנו לחלץ טקסט, נמיר את התשובה למחרוזת
                return str(response)
                
        except Exception as e:
            logfire.error("fallback_model_error", error=str(e))
            # אם גם מודל הגיבוי נכשל, נחזיר תשובה פשוטה
            return await self._get_simple_response(prompt, error_type)
    
    async def _get_model_response(self, prompt: str) -> str:
        """
        קבלת תשובה מהמודל
        
        Args:
            prompt: הפרומפט למודל
            
        Returns:
            תשובת המודל
        """
        try:
            # שימוש ב-agent.run לקבלת תשובה
            result = await self.agent.run(prompt)
            response = result.data
            
            # אם התשובה היא אובייקט, ננסה לחלץ את הטקסט
            text_response = ""
            if hasattr(response, 'text'):
                text_response = response.text
            elif hasattr(response, 'content'):
                text_response = response.content
            elif isinstance(response, dict) and ('text' in response or 'content' in response):
                text_response = response.get('text', response.get('content', ''))
            elif isinstance(response, str):
                text_response = response
            else:
                # אם לא הצלחנו לחלץ טקסט, נמיר את התשובה למחרוזת
                text_response = str(response)
            
            # ניקוי התשובה מתגיות Markdown/HTML לא תקינות
            # הסרת תגיות שעלולות לגרום לבעיות בטלגרם
            import re
            # הסרת תגיות HTML
            text_response = re.sub(r'<[^>]+>', '', text_response)
            # החלפת תווים מיוחדים של Markdown
            markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in markdown_chars:
                if char in text_response and char * 2 in text_response:  # אם יש כפילות של התו
                    text_response = text_response.replace(char * 2, char)  # להחליף כפילות בתו בודד
            
            return text_response
                
        except ModelHTTPError as e:
            logfire.error("model_http_error", error=str(e), status_code=e.status_code if hasattr(e, 'status_code') else 'unknown')
            
            # טיפול בסוגי שגיאות שונים
            if hasattr(e, 'status_code'):
                if e.status_code == 429:  # Rate limit או quota
                    return await self._try_fallback_model(prompt, "quota")
                elif e.status_code == 408:  # Timeout
                    return await self._try_fallback_model(prompt, "timeout")
                elif e.status_code == 400:  # Bad request, אולי בעיית תוכן
                    return await self._try_fallback_model(prompt, "content_filter")
            
            return await self._try_fallback_model(prompt, "general")
        except Exception as e:
            logfire.error("model_error", error=str(e))
            return await self._get_simple_response(prompt, "general")

    async def _log_interaction(self, user_message: str, response: str, task_type: str, intent_type: str) -> None:
        """
        תיעוד אינטראקציה עם המשתמש למטרות למידה ושיפור
        
        Args:
            user_message: הודעת המשתמש
            response: תשובת המערכת
            task_type: סוג המשימה שזוהה
            intent_type: סוג הכוונה הספציפית שזוהתה
        """
        try:
            # תיעוד בלוגים
            logfire.info(
                "interaction_logged",
                user_message=user_message[:100] + "..." if len(user_message) > 100 else user_message,
                response_length=len(response),
                task_type=task_type,
                intent_type=intent_type
            )
            
            # אם יש מנהל למידה, נשתמש בו לתיעוד
            if hasattr(self, 'learning_manager'):
                await self.learning_manager.log_interaction(user_message, response, task_type, intent_type)
        except Exception as e:
            logfire.error("log_interaction_error", error=str(e))

    async def get_response(self, user_id: int, message: str, chat_history: List[Dict[str, Any]] = None) -> ChatResponse:
        """
        קבלת תשובה מה-Agent
        
        Args:
            user_id: מזהה המשתמש
            message: הודעת המשתמש
            chat_history: היסטוריית הצ'אט (אופציונלי)
            
        Returns:
            תשובת הצ'אט
        """
        try:
            # אם אין היסטוריה, ננסה לקבל אותה ממסד הנתונים
            if not chat_history:
                try:
                    chat_history = await db.get_chat_history(user_id)
                except Exception as db_error:
                    logfire.error('error_getting_history', error=str(db_error))
            
            # זיהוי סוג המשימה
            task_type, intent_type, confidence = await self._identify_task_type(message)
            
            # בניית הפרומפט
            prompt = self._get_task_specific_prompt(task_type, message, chat_history)
            
            # קבלת תשובה מהמודל
            response = await self._get_model_response(prompt)
            
            # תיעוד האינטראקציה
            try:
                await self._log_interaction(message, response, task_type, intent_type)
            except Exception as log_error:
                logfire.error("log_interaction_error", error=str(log_error))
            
            return ChatResponse(
                text=response,
                confidence=confidence
            )
        except Exception as e:
            error_msg = f"שגיאה בקבלת תשובה: {str(e)}"
            logfire.error("agent_error", error=str(e))
            
            return ChatResponse(
                text=f"אירעה שגיאה בעת עיבוד הבקשה שלך: {str(e)}",
                confidence=0.0
            )

    async def process_message(self, message: str, user_id: int, context=None):
        """
        עיבוד הודעת משתמש וקבלת תשובה
        
        Args:
            message: הודעת המשתמש
            user_id: מזהה המשתמש
            context: הקשר נוסף (אופציונלי)
            
        Returns:
            תשובת המודל
        """
        try:
            # זיהוי סוג המשימה
            task_type, specific_intent, confidence = await self._identify_task_type(message)
            logfire.info("זוהה סוג משימה", task_type=task_type, specific_intent=specific_intent, confidence=confidence)
            
            # שליפת היסטוריית השיחה מהקונטקסט אם יש
            chat_history = None
            if context and isinstance(context, dict) and "history" in context:
                chat_history = context["history"]
                logfire.info("נמצאה היסטוריית שיחה", history_length=len(chat_history) if chat_history else 0)
            
            # טיפול בבקשות מיוחדות
            # אם זו בקשה להצגת רשימת מסמכים
            if task_type == "document_management" and specific_intent == "list_documents":
                try:
                    # שליפת רשימת המסמכים מהמאגר
                    from src.services.rag_service import list_documents
                    documents = await list_documents()
                    
                    if documents:
                        # בניית תשובה עם רשימת המסמכים
                        response = "הנה רשימת המסמכים שנמצאים במאגר:\n\n"
                        for i, doc in enumerate(documents, 1):
                            title = doc.get('title', 'ללא כותרת')
                            source = doc.get('source', 'לא ידוע')
                            date_added = doc.get('date_added', 'לא ידוע')
                            if isinstance(date_added, str):
                                date_str = date_added
                            else:
                                # אם זה אובייקט תאריך, נמיר אותו למחרוזת
                                date_str = date_added.strftime("%d/%m/%Y %H:%M") if date_added else 'לא ידוע'
                            
                            response += f"{i}. **{title}**\n"
                            response += f"   מקור: {source}\n"
                            response += f"   נוסף בתאריך: {date_str}\n\n"
                        
                        # תיעוד האינטראקציה
                        try:
                            await self._log_interaction(message, response, task_type, specific_intent)
                        except Exception as log_error:
                            logfire.error("log_interaction_error", error=str(log_error))
                        
                        return response
                    else:
                        response = "אין כרגע מסמכים במאגר הנתונים. ניתן להוסיף מסמכים באמצעות הפקודה /add_document."
                        
                        # תיעוד האינטראקציה
                        try:
                            await self._log_interaction(message, response, task_type, specific_intent)
                        except Exception as log_error:
                            logfire.error("log_interaction_error", error=str(log_error))
                        
                        return response
                except Exception as e:
                    logfire.error("list_documents_error", error=str(e))
                    # אם יש שגיאה, נמשיך לתהליך הרגיל
            
            # בדיקה אם זו שיחה חופשית או ברכה
            is_casual_conversation = task_type == "general" or specific_intent == "greeting"
            
            # בניית הפרומפט
            prompt = self._get_task_specific_prompt(task_type, message, chat_history)
            
            # שליפת מסמכים רלוונטיים (RAG) בכל פנייה שקשורה למסמכים או בשאלות כלליות
            if not is_casual_conversation:
                try:
                    # בדיקה אם השאלה קשורה למסמכים או שזו שאלה כללית שעשויה להיות קשורה למסמכים
                    # הוספת מילות מפתח נוספות לזיהוי
                    keywords = [
                        "נובה", "מסמך", "מצגת", "פרויקט", "מידע", "תוכן", 
                        "nexthemes", "next", "themes", "נקסט", "תימס", "נקסטתימס",
                        "מה אתה יודע על", "ספר לי על", "מה יש ב", "תסביר לי על"
                    ]
                    
                    should_search_docs = (
                        task_type == "document_management" or 
                        any(keyword in message.lower() for keyword in keywords)
                    )
                    
                    if should_search_docs:
                        logfire.info("searching_documents", message=message[:100])
                        # הוספת מסמכים רלוונטיים לפרומפט
                        documents = await self._get_relevant_documents(message)
                        if documents and documents != "לא נמצאו מסמכים רלוונטיים לשאילתה זו.":
                            logfire.info("found_relevant_documents", query=message[:100])
                            prompt += f"\n\nמסמכים רלוונטיים שעשויים לעזור בתשובה:\n{documents}"
                            prompt += "\nהשתמש במידע מהמסמכים הרלוונטיים כדי לענות על השאלה בצורה מדויקת. אם המשתמש שואל על מידע שנמצא במסמכים, השתמש במידע זה בתשובתך."
                except Exception as e:
                    logfire.error("search_documents_error", error=str(e))
                    prompt += f"\n\nמידע רלוונטי מהמסמכים: לא ניתן לחפש במאגר הידע כרגע. אנא נסה שוב מאוחר יותר."
            
            # קבלת תשובה מהמודל
            response = await self._get_model_response(prompt)
            
            # תיעוד האינטראקציה במנהל הלמידה (אם קיים)
            try:
                await self._log_interaction(message, response, task_type, specific_intent)
            except Exception as log_error:
                logfire.error("log_interaction_error", error=str(log_error))
            
            return response
        except Exception as e:
            logfire.error("process_message_error", error=str(e))
            return await self._get_simple_response(message, "general")

    async def handle_feedback(self, user_id: int, message_id: int, feedback: str, original_message: str) -> None:
        """
        טיפול במשוב מהמשתמש
        
        Args:
            user_id: מזהה המשתמש
            message_id: מזהה ההודעה
            feedback: המשוב שהתקבל
            original_message: ההודעה המקורית
        """
        try:
            # שמירת המשוב במסד הנתונים
            await db.save_feedback(user_id, message_id, feedback)
            
            # עדכון המשוב במנהל הלמידה
            # מציאת האינטראקציה האחרונה של המשתמש
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, intent_type, confidence, response FROM messages 
            WHERE user_id = ? AND id = ?
            ''', (user_id, message_id))
            
            result = cursor.fetchone()
            
            if result:
                interaction_id, intent_type, confidence, response = result
                
                # עדכון המשוב במנהל הלמידה
                learning_manager.log_interaction(
                    user_id=user_id,
                    message=original_message,
                    intent_type=intent_type or "unknown",
                    confidence=confidence or 0.0,
                    response=response,
                    success=feedback.lower() in ["טוב", "מצוין", "נהדר", "תודה", "👍", "good", "great", "thanks"],
                    feedback=feedback
                )
            
            conn.close()
            
            logfire.info("feedback_received", user_id=user_id, message_id=message_id, feedback=feedback)
        except Exception as e:
            logfire.error("feedback_error", error=str(e), traceback=traceback.format_exc())

    async def generate_report(self, report_type: str = "weekly") -> str:
        """
        יצירת דוח תקופתי על ביצועי הסוכן
        
        Args:
            report_type: סוג הדוח (daily, weekly, monthly)
            
        Returns:
            דוח ביצועים מפורמט
        """
        try:
            # יצירת הדוח באמצעות מנהל הלמידה
            from src.tools.managers.learning_manager import learning_manager
            report = learning_manager.generate_periodic_report(report_type)
            
            # פורמוט הדוח לתצוגה
            if report_type == "daily":
                title = "📊 דוח יומי"
            elif report_type == "weekly":
                title = "📊 דוח שבועי"
            elif report_type == "monthly":
                title = "📊 דוח חודשי"
            else:
                title = "📊 דוח"
            
            formatted_report = f"{title}: {report['title']}\n\n"
            
            # סטטיסטיקות
            formatted_report += "📈 *סטטיסטיקות*\n"
            stats = report["statistics"]
            formatted_report += f"• סך הכל אינטראקציות: {stats['total_interactions']}\n"
            formatted_report += f"• אינטראקציות מוצלחות: {stats['successful_interactions']}\n"
            formatted_report += f"• אינטראקציות בעייתיות: {stats['problematic_interactions']}\n"
            formatted_report += f"• אחוז הצלחה: {stats['success_rate'] * 100:.2f}%\n"
            formatted_report += f"• ממוצע רמת ביטחון: {stats['avg_confidence'] * 100:.2f}%\n\n"
            
            # התפלגות לפי סוגי כוונות
            formatted_report += "🔍 *התפלגות לפי סוגי כוונות*\n"
            for item in report["intent_distribution"][:5]:  # הצגת 5 הכוונות הנפוצות ביותר
                formatted_report += f"• {item['intent_type']}: {item['count']}\n"
            formatted_report += "\n"
            
            # הצעות מילות מפתח
            if report["keyword_suggestions"]:
                formatted_report += "🔑 *הצעות מילות מפתח חדשות*\n"
                for item in report["keyword_suggestions"][:5]:  # הצגת 5 ההצעות המובילות
                    formatted_report += f"• {item['intent_type']}: \"{item['keyword']}\" (ציון: {item['score']:.2f})\n"
            
            return formatted_report
        except Exception as e:
            import traceback
            logfire.error("report_generation_error", error=str(e), traceback=traceback.format_exc())
            return f"אירעה שגיאה בעת יצירת הדוח: {str(e)}"

    async def update_keywords(self, min_score: float = 0.5) -> str:
        """
        עדכון אוטומטי של מילות מפתח
        
        Args:
            min_score: ציון מינימלי נדרש להוספת מילת מפתח
            
        Returns:
            סיכום העדכון
        """
        try:
            # קבלת הצעות מילות מפתח חדשות
            from src.tools.managers.learning_manager import learning_manager
            new_keywords = learning_manager.update_keywords_automatically(min_score)
            
            if not new_keywords:
                return "לא נמצאו מילות מפתח חדשות להוספה."
            
            # פורמוט התוצאה
            result = "✅ מילות מפתח חדשות שהתווספו:\n\n"
            
            for intent_type, keywords in new_keywords.items():
                result += f"*{intent_type}*:\n"
                for keyword in keywords[:10]:  # הגבלה ל-10 מילות מפתח לכל סוג כוונה
                    result += f"• \"{keyword}\"\n"
                result += "\n"
            
            return result
        except Exception as e:
            import traceback
            logfire.error("keyword_update_error", error=str(e), traceback=traceback.format_exc())
            return f"אירעה שגיאה בעת עדכון מילות המפתח: {str(e)}"

    async def _get_relevant_documents(self, query: str) -> str:
        """
        שליפת מסמכים רלוונטיים מהמאגר
        
        Args:
            query: שאילתת החיפוש
            
        Returns:
            מחרוזת המכילה את המסמכים הרלוונטיים
        """
        try:
            from src.services.rag_service import search_documents
            
            # חיפוש מסמכים רלוונטיים
            results = await search_documents(query)
            
            if not results:
                return "לא נמצאו מסמכים רלוונטיים לשאילתה זו."
            
            # בניית תשובה עם המסמכים הרלוונטיים
            response = ""
            for i, result in enumerate(results, 1):
                content = result.get('content', 'אין תוכן זמין')
                title = result.get('title', 'ללא כותרת')
                source = result.get('source', 'לא ידוע')
                
                # קיצור התוכן אם הוא ארוך מדי
                if len(content) > 500:
                    content = content[:500] + "..."
                
                response += f"מסמך {i}: {title} (מקור: {source})\n"
                response += f"תוכן: {content}\n\n"
            
            return response
        except Exception as e:
            logfire.error("get_relevant_documents_error", error=str(e))
            return "אירעה שגיאה בעת חיפוש מסמכים רלוונטיים."
