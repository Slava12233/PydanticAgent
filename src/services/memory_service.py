"""
שירות לניהול זיכרון שיחה מתקדם
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from sqlalchemy import text
from openai import AsyncOpenAI

from src.database.database import db
from src.database.models import (
    Message, Conversation, ConversationMemory,
    MemoryType, MemoryPriority
)

logger = logging.getLogger(__name__)

class MemoryService:
    """שירות לניהול זיכרון שיחה"""
    
    def __init__(self):
        """אתחול השירות"""
        self.openai_client = AsyncOpenAI()
        
        # הגדרות זיכרון
        self.short_term_ttl = timedelta(hours=24)  # זמן חיים לזיכרון קצר טווח
        self.relevance_decay = 0.1  # קצב דעיכת רלוונטיות ליום
        self.memory_threshold = 0.3  # סף מינימלי לשמירת זיכרון
    
    async def process_message(self, message: Message) -> None:
        """
        עיבוד הודעה ויצירת זיכרונות
        
        Args:
            message: הודעה לעיבוד
        """
        try:
            # בדיקה אם ההודעה כבר עובדה
            if message.is_memory_processed:
                return
            
            # ניתוח ההודעה
            analysis = await self._analyze_message(message.content)
            
            # יצירת זיכרונות לפי הניתוח
            if analysis["importance"] >= self.memory_threshold:
                memory_type = (
                    MemoryType.LONG_TERM if analysis["importance"] > 0.7
                    else MemoryType.SHORT_TERM
                )
                
                priority = (
                    MemoryPriority.URGENT if analysis["importance"] > 0.9
                    else MemoryPriority.HIGH if analysis["importance"] > 0.7
                    else MemoryPriority.MEDIUM if analysis["importance"] > 0.4
                    else MemoryPriority.LOW
                )
                
                # יצירת זיכרון
                memory = ConversationMemory(
                    conversation_id=message.conversation_id,
                    memory_type=memory_type,
                    priority=priority,
                    content=analysis["summary"],
                    context=analysis["context"],
                    source_message_ids=[message.id],
                    metadata={
                        "sentiment": analysis["sentiment"],
                        "topics": analysis["topics"],
                        "entities": analysis["entities"]
                    }
                )
                
                # שמירת הזיכרון
                session = await db.get_session()
                try:
                    session.add(memory)
                    message.is_memory_processed = True
                    await session.commit()
                finally:
                    await session.close()
            
        except Exception as e:
            logger.error(f"שגיאה בעיבוד הודעה לזיכרון: {str(e)}")
    
    async def get_relevant_memories(
        self,
        conversation_id: int,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        אחזור זיכרונות רלוונטיים לשאילתה
        
        Args:
            conversation_id: מזהה השיחה
            query: שאילתת החיפוש
            limit: מספר תוצאות מקסימלי
            memory_types: סוגי זיכרון לחיפוש
            min_relevance: סף מינימלי לרלוונטיות
            
        Returns:
            רשימת זיכרונות רלוונטיים
        """
        try:
            # יצירת embedding לשאילתה
            query_embedding = await self._get_embedding(query)
            
            # בניית שאילתת חיפוש
            session = await db.get_session()
            try:
                sql = """
                WITH similarity_results AS (
                    SELECT 
                        cm.*,
                        1 - (cm.embedding <=> :query_embedding) as similarity
                    FROM 
                        conversation_memories cm
                    WHERE 
                        cm.conversation_id = :conversation_id
                        AND cm.is_active = true
                        AND cm.relevance_score >= :min_relevance
                        {memory_type_filter}
                    ORDER BY 
                        cm.priority DESC,
                        similarity DESC,
                        cm.relevance_score DESC
                    LIMIT :limit
                )
                SELECT 
                    *,
                    similarity * 100 as similarity_percentage
                FROM 
                    similarity_results
                """
                
                # הוספת פילטר לסוגי זיכרון
                memory_type_filter = ""
                if memory_types:
                    memory_type_list = [mt.value for mt in memory_types]
                    memory_type_filter = "AND cm.memory_type = ANY(:memory_types)"
                
                sql = sql.format(memory_type_filter=memory_type_filter)
                
                # ביצוע החיפוש
                result = await session.execute(
                    text(sql),
                    {
                        "conversation_id": conversation_id,
                        "query_embedding": query_embedding,
                        "min_relevance": min_relevance,
                        "memory_types": memory_types if memory_types else None,
                        "limit": limit
                    }
                )
                
                # עיבוד התוצאות
                memories = []
                for row in result:
                    try:
                        metadata = (
                            row.metadata if isinstance(row.metadata, dict)
                            else json.loads(row.metadata) if row.metadata
                            else {}
                        )
                    except:
                        metadata = {}
                    
                    memories.append({
                        "id": row.id,
                        "type": row.memory_type.value,
                        "priority": row.priority.value,
                        "content": row.content,
                        "context": row.context,
                        "similarity": row.similarity,
                        "similarity_percentage": round(row.similarity_percentage, 2),
                        "relevance_score": row.relevance_score,
                        "created_at": row.created_at.isoformat(),
                        "metadata": metadata
                    })
                
                return memories
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה באחזור זיכרונות: {str(e)}")
            return []
    
    async def update_memory_relevance(self) -> None:
        """עדכון ציוני רלוונטיות לזיכרונות"""
        try:
            session = await db.get_session()
            try:
                # עדכון ציוני רלוונטיות
                sql = """
                UPDATE conversation_memories
                SET relevance_score = GREATEST(
                    0.0,
                    relevance_score - :decay_rate * 
                    EXTRACT(EPOCH FROM (NOW() - last_accessed)) / 86400.0
                )
                WHERE is_active = true
                """
                
                await session.execute(
                    text(sql),
                    {"decay_rate": self.relevance_decay}
                )
                
                # מחיקת זיכרונות קצרי טווח ישנים
                sql = """
                UPDATE conversation_memories
                SET is_active = false
                WHERE 
                    memory_type = 'short_term'
                    AND NOW() - created_at > :ttl
                    AND is_active = true
                """
                
                await session.execute(
                    text(sql),
                    {"ttl": self.short_term_ttl}
                )
                
                await session.commit()
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בעדכון רלוונטיות זיכרונות: {str(e)}")
    
    async def _analyze_message(self, content: str) -> Dict[str, Any]:
        """
        ניתוח תוכן ההודעה
        
        Args:
            content: תוכן ההודעה
            
        Returns:
            תוצאות הניתוח
        """
        try:
            # שימוש ב-OpenAI לניתוח ההודעה
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        נתח את ההודעה וספק את המידע הבא:
                        1. חשיבות (0-1)
                        2. תקציר תמציתי
                        3. הקשר
                        4. רגש
                        5. נושאים
                        6. ישויות חשובות
                        
                        החזר את התוצאה כ-JSON.
                        """
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # פענוח התשובה
            analysis = json.loads(response.choices[0].message.content)
            
            return {
                "importance": float(analysis.get("importance", 0.5)),
                "summary": analysis.get("summary", ""),
                "context": analysis.get("context", ""),
                "sentiment": analysis.get("sentiment", "neutral"),
                "topics": analysis.get("topics", []),
                "entities": analysis.get("entities", [])
            }
            
        except Exception as e:
            logger.error(f"שגיאה בניתוח הודעה: {str(e)}")
            return {
                "importance": 0.0,
                "summary": "",
                "context": "",
                "sentiment": "neutral",
                "topics": [],
                "entities": []
            }
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        קבלת וקטור embedding עבור טקסט
        
        Args:
            text: הטקסט לקבלת embedding
            
        Returns:
            וקטור embedding
        """
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת embedding: {str(e)}")
            return [0.0] * 1536

# יצירת מופע יחיד של השירות
memory_service = MemoryService() 