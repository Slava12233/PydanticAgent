"""
שירות לניהול הקשר ומידע בשיחה
"""
import logging
from typing import List, Dict, Any, Optional, Set, Union
from datetime import datetime, timezone, timedelta
import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import select, text
from pydantic import BaseModel

from ..database.core import db
from .memory_service import MemoryType, MemoryPriority
from ..database.models.conversations import Memory
from ..templates.responses import ServiceResponse

logger = logging.getLogger(__name__)

class ContextData(BaseModel):
    """מודל לנתוני הקשר"""
    entities: Dict[str, List[Any]]
    last_mentioned: Dict[str, Any]
    intent_history: List[Dict[str, Any]]
    last_update: datetime

class ContextService:
    """שירות לניהול הקשר ומידע בשיחה"""
    
    def __init__(self):
        """אתחול השירות"""
        self.openai_client = AsyncOpenAI()
        self.context = ContextData(
            entities={
                "products": [],      # מוצרים שהוזכרו
                "orders": [],        # הזמנות שהוזכרו
                "customers": [],     # לקוחות שהוזכרו
                "categories": [],    # קטגוריות שהוזכרו
                "prices": [],        # מחירים שהוזכרו
                "quantities": [],    # כמויות שהוזכרו
                "dates": [],         # תאריכים שהוזכרו
                "documents": []      # מסמכים שהוזכרו
            },
            last_mentioned={
                "product": None,
                "order": None,
                "customer": None,
                "category": None,
                "price": None,
                "quantity": None,
                "date": None,
                "document": None
            },
            intent_history=[],
            last_update=datetime.now(timezone.utc)
        )
    
    async def process_message(
        self,
        message: str,
        role: str = "user",
        intent_type: Optional[str] = None,
        extracted_entities: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> ServiceResponse:
        """
        עיבוד הודעה ושמירתה בזיכרון
        
        Args:
            message: תוכן ההודעה
            role: תפקיד השולח (user/assistant)
            intent_type: סוג הכוונה שזוהתה (אופציונלי)
            extracted_entities: ישויות שחולצו מההודעה (אופציונלי)
            conversation_id: מזהה השיחה (אופציונלי)
            
        Returns:
            תוצאת הפעולה
        """
        try:
            # בדיקה שההודעה לא ריקה
            if not message.strip():
                return ServiceResponse(
                    success=False,
                    message="ההודעה ריקה",
                    error="לא ניתן לעבד הודעה ריקה",
                    service_name="context_service",
                    operation="process_message"
                )
            
            # יצירת embedding להודעה
            embedding = await self._get_embedding(message)
            
            # שמירת ההודעה בזיכרון
            memory = Memory(
                content=message,
                role=role,
                embedding=embedding,
                memory_type=MemoryType.CONVERSATION.value,  # המרה למחרוזת
                priority=MemoryPriority.MEDIUM.value,  # המרה למחרוזת
                timestamp=datetime.now(timezone.utc),
                conversation_id=conversation_id
            )
            
            async with db.get_session() as session:
                session.add(memory)
                await session.commit()
            
            # עדכון הקשר השיחה
            if intent_type or extracted_entities:
                self._update_context(message, intent_type, extracted_entities or {})
            
            return ServiceResponse(
                success=True,
                message="ההודעה עובדה ונשמרה בהצלחה",
                service_name="context_service",
                operation="process_message"
            )
            
        except Exception as e:
            logger.error(f"שגיאה בעיבוד הודעה: {str(e)}")
            return ServiceResponse(
                success=False,
                message="שגיאה בעיבוד ההודעה",
                error=str(e),
                service_name="context_service",
                operation="process_message"
            )
    
    async def get_conversation_context(
        self,
        query: str,
        conversation_id: Optional[int] = None,
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> Dict[str, Any]:
        """
        קבלת הקשר שיחה מלא
        
        Args:
            query: שאילתת החיפוש
            conversation_id: מזהה השיחה (אופציונלי)
            limit: מספר זיכרונות מקסימלי
            min_similarity: סף מינימלי לדמיון
            
        Returns:
            מילון עם כל מידע ההקשר
        """
        # שליפת זיכרונות רלוונטיים
        memories = await self._get_relevant_memories(query, limit, min_similarity, conversation_id)
        
        # פתרון כינויי גוף בשאילתה
        resolved_query = self._resolve_pronouns(query)
        
        return {
            "query": query,
            "resolved_query": resolved_query,
            "memories": memories,
            "entities": self.context.entities,
            "last_mentioned": self.context.last_mentioned,
            "last_intent": self._get_last_intent(),
            "conversation_id": conversation_id
        }
    
    def _update_context(
        self,
        message: str,
        intent_type: Optional[str],
        extracted_entities: Dict[str, Any]
    ) -> None:
        """
        עדכון הקשר השיחה
        
        Args:
            message: הודעת המשתמש
            intent_type: סוג הכוונה
            extracted_entities: ישויות שחולצו
        """
        # עדכון זמן אחרון
        self.context.last_update = datetime.now(timezone.utc)
        
        # הוספת הכוונה להיסטוריה
        if intent_type:
            self.context.intent_history.append({
                "intent": intent_type,
                "timestamp": self.context.last_update,
                "message": message
            })
            
            # שמירת היסטוריית כוונות מוגבלת
            if len(self.context.intent_history) > 10:
                self.context.intent_history = self.context.intent_history[-10:]
        
        # עדכון הישויות שהוזכרו
        for entity_type, entity_value in extracted_entities.items():
            if entity_value:
                if entity_type == "product_name" or entity_type == "product_id":
                    self._add_entity("products", entity_value)
                    self.context.last_mentioned["product"] = entity_value
                
                elif entity_type == "order_id":
                    self._add_entity("orders", entity_value)
                    self.context.last_mentioned["order"] = entity_value
                
                elif entity_type == "customer_name" or entity_type == "customer_id":
                    self._add_entity("customers", entity_value)
                    self.context.last_mentioned["customer"] = entity_value
                
                elif entity_type == "category":
                    self._add_entity("categories", entity_value)
                    self.context.last_mentioned["category"] = entity_value
                
                elif entity_type == "price":
                    self._add_entity("prices", entity_value)
                    self.context.last_mentioned["price"] = entity_value
                
                elif entity_type == "quantity":
                    self._add_entity("quantities", entity_value)
                    self.context.last_mentioned["quantity"] = entity_value
                
                elif entity_type == "date":
                    self._add_entity("dates", entity_value)
                    self.context.last_mentioned["date"] = entity_value
                
                elif entity_type == "document":
                    self._add_entity("documents", entity_value)
                    self.context.last_mentioned["document"] = entity_value
    
    def _add_entity(self, entity_list: str, entity_value: Any) -> None:
        """הוספת ישות לרשימה"""
        self.context.entities[entity_list].insert(0, entity_value)
        if len(self.context.entities[entity_list]) > 10:
            self.context.entities[entity_list] = self.context.entities[entity_list][:10]
    
    def _get_last_intent(self) -> Optional[Dict[str, Any]]:
        """קבלת הכוונה האחרונה"""
        if self.context.intent_history:
            return self.context.intent_history[-1]
        return None
    
    def _resolve_pronouns(self, text: str) -> str:
        """פתרון כינויי גוף בטקסט"""
        pronouns = {
            "he": ["הוא", "אותו", "שלו", "לו", "ממנו", "עליו", "בו"],
            "she": ["היא", "אותה", "שלה", "לה", "ממנה", "עליה", "בה"],
            "it": ["זה", "זאת", "זו", "זהו", "זוהי"],
            "they": ["הם", "אותם", "שלהם", "להם", "מהם", "עליהם", "בהם"]
        }
        
        resolved_text = text
        
        # החלפת כינויי גוף בערכים אחרונים שהוזכרו
        for gender, pronoun_list in pronouns.items():
            if any(pronoun in text for pronoun in pronoun_list):
                if gender == "he" and self.context.last_mentioned["product"]:
                    resolved_text = resolved_text.replace(
                        pronoun, str(self.context.last_mentioned["product"])
                    )
                elif gender == "she" and self.context.last_mentioned["order"]:
                    resolved_text = resolved_text.replace(
                        pronoun, str(self.context.last_mentioned["order"])
                    )
                elif gender == "it" and self.context.last_mentioned["document"]:
                    resolved_text = resolved_text.replace(
                        pronoun, str(self.context.last_mentioned["document"])
                    )
        
        return resolved_text
    
    async def _get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3,
        conversation_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """אחזור זיכרונות רלוונטיים"""
        try:
            query_embedding = await self._get_embedding(query)
            
            async with db.get_session() as session:
                stmt = select(Memory).order_by(Memory.timestamp.desc())
                if conversation_id:
                    stmt = stmt.where(Memory.conversation_id == conversation_id)
                result = await session.execute(stmt)
                memories = result.scalars().all()
                
                results = []
                for memory in memories:
                    if memory.embedding is None:
                        continue
                    
                    similarity = self._cosine_similarity(query_embedding, memory.embedding)
                    
                    if similarity >= min_similarity:
                        results.append({
                            "id": memory.id,
                            "content": memory.content,
                            "role": memory.role,
                            "timestamp": memory.timestamp.isoformat(),
                            "similarity": float(similarity)
                        })
                
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
                
        except Exception as e:
            logger.error(f"שגיאה באחזור זיכרונות: {str(e)}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """חישוב דמיון קוסינוס"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """קבלת embedding לטקסט"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"שגיאה בקבלת embedding: {str(e)}")
            return [0.0] * 1536

# יצירת מופע יחיד של השירות
context_service = ContextService() 