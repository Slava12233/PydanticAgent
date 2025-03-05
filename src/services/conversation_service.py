"""
שירות לניהול שיחות עם תמיכה בזיכרון ותקצירים
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json

from openai import AsyncOpenAI
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

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
        async with db.get_session() as session:
            conversation = Conversation(
                user_id=user_id,
                title=title,
                context={
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "topics": [],
                    "entities": [],
                    "user_preferences": {}
                }
            )
            session.add(conversation)
            await session.commit()
            return conversation
    
    async def add_message(self, conversation_id: int, role: str, content: str) -> None:
        """
        הוספת הודעה לשיחה
        
        Args:
            conversation_id: מזהה השיחה
            role: תפקיד השולח (user/assistant)
            content: תוכן ההודעה
        """
        try:
            async with db.get_session() as session:
                # בדיקה שהשיחה קיימת
                conversation = await session.get(Conversation, conversation_id)
                if not conversation:
                    logger.error(f"Conversation {conversation_id} not found")
                    return
                
                # יצירת הודעה חדשה
                message = Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    timestamp=datetime.now(timezone.utc)
                )
                session.add(message)
                
                # עדכון זמן העדכון האחרון של השיחה
                conversation.updated_at = datetime.now(timezone.utc)
                
                # שמירת השינויים
                await session.commit()
                
                # עיבוד ההודעה לזיכרון
                await memory_service.process_message(content, role)
                
                # בדיקה אם צריך לעדכן את תקציר השיחה
                messages_count = await session.scalar(
                    select(func.count(Message.id))
                    .where(Message.conversation_id == conversation_id)
                )
                
                if messages_count % 5 == 0:  # עדכון כל 5 הודעות
                    await self._update_conversation_summary(conversation_id, session)
                
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise
    
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
            הקשר השיחה כולל זיכרונות רלוונטיים והיסטוריה אחרונה
        """
        async with db.get_session() as session:
            # קבלת השיחה
            conversation = await session.get(Conversation, conversation_id)
            if not conversation:
                return {}
            
            # קבלת ההודעות האחרונות (5 הודעות אחרונות)
            recent_messages_query = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.desc()).limit(5)
            
            result = await session.execute(recent_messages_query)
            recent_messages = result.scalars().all()
            
            # קבלת זיכרונות רלוונטיים
            memories = await memory_service.get_relevant_memories(
                query=query,
                limit=limit
            )
            
            return {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "context": conversation.context,
                "recent_messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in recent_messages
                ],
                "relevant_memories": memories
            }
    
    async def _update_conversation_summary(self, conversation_id: int, session: AsyncSession) -> None:
        """
        עדכון תקציר השיחה
        
        Args:
            conversation_id: מזהה השיחה
            session: סשן הדאטהבייס
        """
        try:
            # קבלת ההודעות האחרונות
            messages_query = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.desc()).limit(5)
            
            result = await session.execute(messages_query)
            messages = result.scalars().all()
            
            if not messages:
                return
            
            # יצירת תקציר באמצעות GPT
            messages_text = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "אתה עוזר שמסכם שיחות. אנא צור תקציר קצר של השיחה האחרונה."},
                    {"role": "user", "content": f"הנה השיחה האחרונה:\n{messages_text}"}
                ]
            )
            
            summary = response.choices[0].message.content
            
            # עדכון התקציר בדאטהבייס
            conversation = await session.get(Conversation, conversation_id)
            if conversation:
                conversation.summary = summary
                await session.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversation summary: {str(e)}")
            raise

# יצירת מופע יחיד של השירות
conversation_service = ConversationService() 