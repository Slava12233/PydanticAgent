"""
שירות לניהול זיכרון שיחה מתקדם
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from openai import AsyncOpenAI

from src.database.database import db
from src.database.models import Memory

logger = logging.getLogger(__name__)

class MemoryService:
    """שירות לניהול זיכרון שיחה"""
    
    def __init__(self):
        """אתחול השירות"""
        self.openai_client = AsyncOpenAI()
    
    async def process_message(self, message: str, role: str = "user") -> None:
        """
        עיבוד הודעה ושמירתה בזיכרון
        
        Args:
            message: תוכן ההודעה
            role: תפקיד השולח (user/assistant)
        """
        try:
            # בדיקה שההודעה לא ריקה
            if not message.strip():
                logger.warning("ניסיון לשמור הודעה ריקה")
                return
            
            # יצירת embedding להודעה
            embedding = await self._get_embedding(message)
            
            # יצירת רשומת זיכרון חדשה
            memory = Memory(
                content=message,
                role=role,
                embedding=embedding,
                timestamp=datetime.now(timezone.utc)
            )
            
            async with db.get_session() as session:
                session.add(memory)
                await session.commit()
                
            logger.info(f"Processed and saved message to memory: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"שגיאה בעיבוד הודעה לזיכרון: {str(e)}")
    
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        אחזור זיכרונות רלוונטיים לשאילתה
        
        Args:
            query: שאילתת החיפוש
            limit: מספר תוצאות מקסימלי
            min_similarity: סף מינימלי לדמיון
            
        Returns:
            רשימת זיכרונות רלוונטיים
        """
        try:
            # יצירת embedding לשאילתה
            query_embedding = await self._get_embedding(query)
            
            async with db.get_session() as session:
                # שליפת כל הזיכרונות
                stmt = select(Memory).order_by(Memory.timestamp.desc())
                result = await session.execute(stmt)
                memories = result.scalars().all()
                
                # חישוב דמיון וסינון תוצאות
                results = []
                for memory in memories:
                    if memory.embedding is None:
                        continue
                    
                    # חישוב דמיון קוסינוס
                    similarity = self._cosine_similarity(query_embedding, memory.embedding)
                    
                    if similarity >= min_similarity:
                        results.append({
                            "id": memory.id,
                            "content": memory.content,
                            "role": memory.role,
                            "timestamp": memory.timestamp.isoformat(),
                            "similarity": float(similarity)
                        })
                
                # מיון לפי דמיון
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
                
        except Exception as e:
            logger.error(f"שגיאה באחזור זיכרונות: {str(e)}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """חישוב דמיון קוסינוס בין שני וקטורים"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        קבלת embedding עבור טקסט
        
        Args:
            text: הטקסט לעיבוד
            
        Returns:
            רשימת מספרים המייצגת את ה-embedding
        """
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"שגיאה בקבלת embedding: {str(e)}")
            return [0.0] * 1536  # ערך ברירת מחדל

# יצירת מופע יחיד של השירות
memory_service = MemoryService() 