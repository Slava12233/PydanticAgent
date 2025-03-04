"""
סוכן טלגרם עם תמיכה בזיכרון ותקצירים
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
import logfire
from typing import Optional, Dict, Any, AsyncGenerator, List
import logging
import json

# הוספת נתיב הפרויקט ל-Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ייבוא מודולים מקומיים
from src.agents.core.model_manager import ModelManager
from src.agents.core.task_identifier import identify_task, get_task_specific_prompt
from src.agents.core.context_retriever import retrieve_context
from src.agents.models.responses import ChatResponse, TaskIdentification, AgentContext
from src.tools.managers import ConversationContext
from src.database.database import db
from src.services.conversation_service import conversation_service
from src.services.memory_service import memory_service
from src.services.rag_service import rag_service
from src.services.learning_service import learning_service

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'

logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')

logger = logging.getLogger(__name__)

class TelegramAgent:
    """מחלקה המרכזת את כל הלוגיקה של ה-Agent"""
    
    def __init__(self):
        """אתחול הסוכן"""
        self.openai_client = AsyncOpenAI()
        self.max_context_length = 4000  # אורך מקסימלי להקשר
        
        # אתחול מנהל המודל
        self.model_manager = ModelManager()
        
        # וידוא שמסד הנתונים מאותחל
        if db.engine is None:
            db.init_db()
            
        # יצירת מנהל הקשר
        self.context_manager = ConversationContext()
        
        # הגדרות למידה
        self.pattern_analysis_interval = 10  # מספר הודעות בין ניתוחי דפוסים
        self.last_pattern_analysis = {}  # מעקב אחר ניתוח אחרון לכל משתמש
        
        logfire.info('telegram_agent_initialized')
    
    async def handle_message(self, user_id: int, message_text: str, conversation_id: Optional[int] = None) -> str:
        """
        טיפול בהודעה נכנסת
        
        Args:
            user_id: מזהה המשתמש
            message_text: תוכן ההודעה
            conversation_id: מזהה השיחה (אופציונלי)
            
        Returns:
            תשובת הסוכן
        """
        try:
            # יצירת שיחה חדשה אם צריך
            if not conversation_id:
                conversation = await conversation_service.create_conversation(user_id)
                conversation_id = conversation.id
            
            # שמירת הודעת המשתמש
            await conversation_service.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message_text
            )
            
            # בדיקה אם צריך לנתח דפוסים
            await self._check_pattern_analysis(user_id)
            
            # קבלת הקשר רלוונטי
            context = await conversation_service.get_conversation_context(
                conversation_id=conversation_id,
                query=message_text
            )
            
            # חיפוש במסמכים רלוונטיים
            relevant_docs = await rag_service.search_documents(
                query=message_text,
                limit=3,
                min_similarity=0.3
            )
            
            # בניית הקשר מלא לשאילתה
            full_context = self._build_prompt_context(
                message_text,
                context,
                relevant_docs
            )
            
            # קבלת תשובה מ-GPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        אתה עוזר אישי מקצועי שמדבר עברית.
                        השתמש בהקשר ובמידע שסופק כדי לתת תשובה מדויקת ומועילה.
                        אם אין לך מספיק מידע, ציין זאת בבירור.
                        """
                    },
                    {
                        "role": "user",
                        "content": full_context
                    }
                ]
            )
            
            # קבלת התשובה המקורית
            original_response = response.choices[0].message.content
            
            # התאמת התשובה לסגנון המשתמש
            adapted_response = await learning_service.adapt_response_style(
                user_id=user_id,
                original_response=original_response
            )
            
            # שמירת התשובה
            await conversation_service.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=adapted_response
            )
            
            # עדכון משקלי זיכרונות
            await learning_service.update_memory_weights(user_id)
            
            return adapted_response
            
        except Exception as e:
            logger.error(f"שגיאה בטיפול בהודעה: {str(e)}")
            return "מצטער, אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב."
    
    async def _check_pattern_analysis(self, user_id: int) -> None:
        """
        בדיקה אם צריך לנתח דפוסי משתמש
        
        Args:
            user_id: מזהה המשתמש
        """
        try:
            # בדיקה מתי נערך הניתוח האחרון
            last_analysis = self.last_pattern_analysis.get(user_id, 0)
            messages_since_analysis = await self._count_messages_since(user_id, last_analysis)
            
            # ניתוח דפוסים אם עברו מספיק הודעות
            if messages_since_analysis >= self.pattern_analysis_interval:
                await learning_service.analyze_user_patterns(user_id)
                self.last_pattern_analysis[user_id] = datetime.utcnow().timestamp()
                
        except Exception as e:
            logger.error(f"שגיאה בבדיקת ניתוח דפוסים: {str(e)}")
    
    async def _count_messages_since(self, user_id: int, timestamp: float) -> int:
        """
        ספירת הודעות מאז נקודת זמן
        
        Args:
            user_id: מזהה המשתמש
            timestamp: חותמת זמן
            
        Returns:
            מספר ההודעות
        """
        try:
            session = await db.get_session()
            try:
                result = await session.execute(
                    text("""
                    SELECT COUNT(*)
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE 
                        c.user_id = :user_id
                        AND m.timestamp > to_timestamp(:ts)
                    """),
                    {
                        "user_id": user_id,
                        "ts": timestamp
                    }
                )
                return result.scalar() or 0
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"שגיאה בספירת הודעות: {str(e)}")
            return 0
    
    def _build_prompt_context(
        self,
        query: str,
        conversation_context: Dict[str, Any],
        relevant_docs: List[Dict[str, Any]]
    ) -> str:
        """
        בניית הקשר מלא לשאילתה
        
        Args:
            query: השאילתה המקורית
            conversation_context: הקשר השיחה
            relevant_docs: מסמכים רלוונטיים
            
        Returns:
            הקשר מלא כטקסט
        """
        context_parts = []
        
        # הוספת תקציר השיחה
        if conversation_context.get("summary"):
            context_parts.append(
                "תקציר השיחה הנוכחית:\n" + conversation_context["summary"]
            )
        
        # הוספת זיכרונות רלוונטיים
        if conversation_context.get("relevant_memories"):
            memories_text = "\n".join([
                f"- {memory['content']} (רלוונטיות: {memory['similarity_percentage']}%)"
                for memory in conversation_context["relevant_memories"]
            ])
            context_parts.append(
                "זיכרונות רלוונטיים מהשיחה:\n" + memories_text
            )
        
        # הוספת מסמכים רלוונטיים
        if relevant_docs:
            docs_text = "\n".join([
                f"- {doc['content']} (מקור: {doc['source']})"
                for doc in relevant_docs
            ])
            context_parts.append(
                "מידע רלוונטי ממסמכים:\n" + docs_text
            )
        
        # הוספת נושאים ותובנות
        if conversation_context.get("context", {}).get("topics"):
            context_parts.append(
                "נושאי השיחה:\n" + 
                "\n".join([f"- {topic}" for topic in conversation_context["context"]["topics"]])
            )
        
        # הוספת השאילתה
        context_parts.append("\nשאילתת המשתמש: " + query)
        
        # חיבור כל החלקים
        full_context = "\n\n".join(context_parts)
        
        # קיצור אם צריך
        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length - 100] + "..."
        
        return full_context

    async def get_response(self, user_message: str, user_id: str, conversation_id: str) -> ChatResponse:
        """
        קבלת תשובה להודעת משתמש
        
        Args:
            user_message: הודעת המשתמש
            user_id: מזהה המשתמש
            conversation_id: מזהה השיחה
            
        Returns:
            תשובת הצ'אט
        """
        try:
            # זיהוי סוג המשימה
            task = await identify_task(user_message)
            
            # חיפוש הקשר רלוונטי
            context = await retrieve_context(user_message)
            
            # בניית פרומפט מותאם
            history = self.context_manager.get_conversation_history(conversation_id)
            prompt = get_task_specific_prompt(task.task_type, user_message, history)
            
            # הוספת ההקשר לפרומפט אם נמצא
            if context and context != "לא נמצא מידע רלוונטי במאגר הידע.":
                prompt += f"\n\nמידע רלוונטי מהמאגר:\n{context}"
            
            # קבלת תשובה מהמודל
            try:
                response = await self.model_manager.agent.complete(prompt)
                return ChatResponse(
                    text=response,
                    confidence=task.confidence_score,
                    sources=[context] if context else None
                )
            except Exception as model_error:
                # ניסיון להשתמש במודל גיבוי
                await self.model_manager.initialize_fallback_agent()
                response = await self.model_manager.fallback_agent.complete(prompt)
                return ChatResponse(
                    text=response,
                    confidence=task.confidence_score,
                    sources=[context] if context else None
                )
                
        except Exception as e:
            logfire.error('get_response_error', error=str(e))
            error_response = self.model_manager.get_simple_response(user_message)
            return ChatResponse(text=error_response, confidence=0.0)
    
    async def stream_response(self, user_message: str, user_id: str, conversation_id: str) -> AsyncGenerator[str, None]:
        """
        קבלת תשובה להודעת משתמש בזרימה
        
        Args:
            user_message: הודעת המשתמש
            user_id: מזהה המשתמש
            conversation_id: מזהה השיחה
            
        Yields:
            חלקי התשובה בזרימה
        """
        try:
            # זיהוי סוג המשימה
            task = await identify_task(user_message)
            
            # חיפוש הקשר רלוונטי
            context = await retrieve_context(user_message)
            
            # בניית פרומפט מותאם
            history = self.context_manager.get_conversation_history(conversation_id)
            prompt = get_task_specific_prompt(task.task_type, user_message, history)
            
            # הוספת ההקשר לפרומפט אם נמצא
            if context and context != "לא נמצא מידע רלוונטי במאגר הידע.":
                prompt += f"\n\nמידע רלוונטי מהמאגר:\n{context}"
            
            # קבלת תשובה מהמודל בזרימה
            try:
                async for token in self.model_manager.agent.stream_complete(prompt):
                    yield token
            except Exception as model_error:
                # ניסיון להשתמש במודל גיבוי
                await self.model_manager.initialize_fallback_agent()
                async for token in self.model_manager.fallback_agent.stream_complete(prompt):
                    yield token
                    
        except Exception as e:
            logfire.error('stream_response_error', error=str(e))
            error_response = self.model_manager.get_simple_response(user_message)
            yield error_response
