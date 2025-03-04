"""
שירות לניהול שיחות עם תמיכה בזיכרון ותקצירים
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from openai import AsyncOpenAI

from src.database.database import db
from src.database.models import Message, Conversation, ConversationMemory, MemoryType
from src.services.memory_service import memory_service

logger = logging.getLogger(__name__)

class ConversationService:
    """שירות לניהול שיחות"""
    
    def __init__(self):
        """אתחול השירות"""
        self.openai_client = AsyncOpenAI()
        self.summary_interval = 5  # מספר ההודעות בין עדכוני תקציר
    
    async def create_conversation(self, user_id: int, title: Optional[str] = None) -> Conversation:
        """
        יצירת שיחה חדשה
        
        Args:
            user_id: מזהה המשתמש
            title: כותרת השיחה (אופציונלי)
            
        Returns:
            שיחה חדשה
        """
        session = await db.get_session()
        try:
            conversation = Conversation(
                user_id=user_id,
                title=title,
                context={
                    "start_time": datetime.utcnow().isoformat(),
                    "topics": [],
                    "entities": [],
                    "user_preferences": {}
                }
            )
            session.add(conversation)
            await session.commit()
            return conversation
        finally:
            await session.close()
    
    async def add_message(self, conversation_id: int, role: str, content: str) -> Message:
        """
        הוספת הודעה לשיחה
        
        Args:
            conversation_id: מזהה השיחה
            role: תפקיד השולח ('user' או 'assistant')
            content: תוכן ההודעה
            
        Returns:
            ההודעה שנוספה
        """
        session = await db.get_session()
        try:
            # יצירת הודעה חדשה
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            session.add(message)
            
            # קבלת מספר ההודעות בשיחה
            messages_count = await session.scalar(
                text("SELECT COUNT(*) FROM messages WHERE conversation_id = :conv_id"),
                {"conv_id": conversation_id}
            )
            
            # עדכון תקציר אם צריך
            if messages_count % self.summary_interval == 0:
                await self._update_conversation_summary(conversation_id, session)
            
            await session.commit()
            
            # עיבוד ההודעה למערכת הזיכרון (בנפרד מהטרנזקציה)
            await memory_service.process_message(message)
            
            return message
        finally:
            await session.close()
    
    async def get_conversation_context(
        self,
        conversation_id: int,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        קבלת הקשר רלוונטי לשיחה
        
        Args:
            conversation_id: מזהה השיחה
            query: שאילתת החיפוש
            limit: מספר זיכרונות מקסימלי
            
        Returns:
            הקשר השיחה כולל זיכרונות רלוונטיים
        """
        session = await db.get_session()
        try:
            # קבלת השיחה
            conversation = await session.get(Conversation, conversation_id)
            if not conversation:
                return {}
            
            # קבלת זיכרונות רלוונטיים
            memories = await memory_service.get_relevant_memories(
                conversation_id=conversation_id,
                query=query,
                limit=limit
            )
            
            # בניית הקשר
            context = {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "summary": conversation.summary,
                "context": conversation.context,
                "relevant_memories": memories,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return context
        finally:
            await session.close()
    
    async def _update_conversation_summary(self, conversation_id: int, session) -> None:
        """
        עדכון תקציר השיחה
        
        Args:
            conversation_id: מזהה השיחה
            session: סשן מסד הנתונים
        """
        try:
            # קבלת ההודעות האחרונות
            result = await session.execute(
                text("""
                SELECT content, role 
                FROM messages 
                WHERE conversation_id = :conv_id 
                ORDER BY timestamp DESC 
                LIMIT 10
                """),
                {"conv_id": conversation_id}
            )
            messages = result.fetchall()
            
            if not messages:
                return
            
            # בניית הקלט ל-GPT
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in reversed(messages)
            ])
            
            # יצירת תקציר באמצעות GPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        צור תקציר קצר וממוקד של השיחה.
                        כלול:
                        1. נושאים עיקריים
                        2. החלטות או תובנות חשובות
                        3. פעולות שבוצעו
                        4. נקודות למעקב
                        
                        החזר את התוצאה כ-JSON עם השדות הבאים:
                        - summary: תקציר טקסטואלי
                        - topics: רשימת נושאים
                        - insights: רשימת תובנות
                        - actions: רשימת פעולות
                        - follow_up: נקודות למעקב
                        """
                    },
                    {
                        "role": "user",
                        "content": conversation_text
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # פענוח התשובה
            summary_data = json.loads(response.choices[0].message.content)
            
            # עדכון השיחה
            await session.execute(
                text("""
                UPDATE conversations 
                SET 
                    summary = :summary,
                    context = context || :context_update::jsonb
                WHERE id = :conv_id
                """),
                {
                    "conv_id": conversation_id,
                    "summary": summary_data["summary"],
                    "context_update": json.dumps({
                        "topics": summary_data["topics"],
                        "insights": summary_data["insights"],
                        "actions": summary_data["actions"],
                        "follow_up": summary_data["follow_up"],
                        "last_summary_update": datetime.utcnow().isoformat()
                    })
                }
            )
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון תקציר שיחה: {str(e)}")

# יצירת מופע יחיד של השירות
conversation_service = ConversationService() 