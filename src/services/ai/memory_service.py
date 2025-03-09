"""
שירות לניהול זיכרון והקשר בשיחה
"""
import logging
from typing import List, Dict, Any, Optional, Set, Union
from datetime import datetime, timezone, timedelta
import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import select, text
from pydantic import BaseModel
import enum

from src.database.database import db
from src.models.database import Memory as DBMemory
from src.models.responses import ServiceResponse

logger = logging.getLogger(__name__)

# הגדרת סוגי זיכרונות ועדיפויות כאן במקום לייבא אותם
class MemoryType(enum.Enum):
    """סוגי זיכרונות במערכת"""
    CONVERSATION = "conversation"
    ENTITY = "entity"
    FACT = "fact"
    PREFERENCE = "preference"
    TASK = "task"
    SYSTEM = "system"

class MemoryPriority(enum.Enum):
    """רמות עדיפות לזיכרונות"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Memory(BaseModel):
    id: int
    content: str
    role: str
    embedding: List[float]
    memory_type: MemoryType
    priority: MemoryPriority
    timestamp: datetime
    conversation_id: Optional[int] = None

class ContextData(BaseModel):
    """מודל לנתוני הקשר"""
    entities: Dict[str, List[Any]]
    last_mentioned: Dict[str, Any]
    intent_history: List[Dict[str, Any]]
    last_update: datetime

class MemoryService:
    """שירות לניהול זיכרון והקשר בשיחה"""
    
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
            intent_type: סוג הכוונה (אופציונלי)
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
                    error_details="לא ניתן לעבד הודעה ריקה"
                )
            
            # יצירת embedding להודעה
            embedding = await self._get_embedding(message)
            
            # קביעת סוג הזיכרון ועדיפות
            memory_type = MemoryType.CONVERSATION
            priority = MemoryPriority.MEDIUM
            
            async with db.get_session() as session:
                memory = DBMemory(
                    content=message,
                    role=role,
                    embedding=embedding,
                    memory_type=memory_type.value,
                    priority=priority.value,
                    timestamp=datetime.now(timezone.utc),
                    conversation_id=conversation_id
                )
                
                session.add(memory)
                await session.commit()
            
            # עדכון הקשר השיחה
            if intent_type or extracted_entities:
                self._update_context(message, intent_type, extracted_entities or {})
            
            return ServiceResponse(
                success=True,
                message="ההודעה עובדה ונשמרה בהצלחה"
            )
            
        except Exception as e:
            logger.error(f"שגיאה בעיבוד הודעה: {str(e)}")
            return ServiceResponse(
                success=False,
                message="שגיאה בעיבוד ההודעה",
                error_details=str(e)
            )
    
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3,
        memory_types: Optional[List[MemoryType]] = None,
        conversation_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        אחזור זיכרונות רלוונטיים לשאילתה
        
        Args:
            query: שאילתת החיפוש
            limit: מספר התוצאות המקסימלי
            min_similarity: סף מינימלי לדמיון
            memory_types: סוגי זיכרונות לחיפוש
            conversation_id: מזהה השיחה (אופציונלי)
            
        Returns:
            רשימת זיכרונות רלוונטיים
        """
        try:
            # יצירת embedding לשאילתה
            query_embedding = await self._get_embedding(query)
            
            async with db.get_session() as session:
                # בניית השאילתה
                stmt = select(DBMemory).order_by(DBMemory.timestamp.desc())
                
                # סינון לפי סוגי זיכרונות
                if memory_types:
                    stmt = stmt.where(DBMemory.memory_type.in_([mt.value for mt in memory_types]))
                
                # סינון לפי מזהה שיחה
                if conversation_id is not None:
                    stmt = stmt.where(DBMemory.conversation_id == conversation_id)
                
                # ביצוע השאילתה
                result = await session.execute(stmt)
                memories = result.scalars().all()
                
                # חישוב דמיון וסינון לפי סף
                results = []
                for memory in memories:
                    if memory.embedding:
                        similarity = self._cosine_similarity(query_embedding, memory.embedding)
                        
                        if similarity >= min_similarity:
                            results.append({
                                "id": memory.id,
                                "content": memory.content,
                                "role": memory.role,
                                "similarity": similarity,
                                "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
                                "conversation_id": memory.conversation_id
                            })
                
                # מיון לפי דמיון
                results.sort(key=lambda x: x["similarity"], reverse=True)
                
                return results[:limit]
                
        except Exception as e:
            logger.error(f"שגיאה באחזור זיכרונות: {str(e)}")
            return []
    
    async def get_conversation_context(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        קבלת הקשר שיחה מלא
        
        Args:
            query: שאילתת החיפוש
            limit: מספר התוצאות המקסימלי
            min_similarity: סף מינימלי לדמיון
            conversation_id: מזהה השיחה (אופציונלי)
            
        Returns:
            מילון עם הקשר השיחה
        """
        try:
            # אחזור זיכרונות רלוונטיים
            memories = await self.get_relevant_memories(
                query, 
                limit=limit, 
                min_similarity=min_similarity,
                memory_types=[MemoryType.CONVERSATION],
                conversation_id=conversation_id
            )
            
            # בניית הקשר
            context = {
                "entities": self.context.entities,
                "last_mentioned": self.context.last_mentioned,
                "intent_history": self.context.intent_history,
                "relevant_memories": memories
            }
            
            return context
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הקשר שיחה: {str(e)}")
            return {
                "entities": {},
                "last_mentioned": {},
                "intent_history": [],
                "relevant_memories": []
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
            message: תוכן ההודעה
            intent_type: סוג הכוונה
            extracted_entities: ישויות שחולצו מההודעה
        """
        # עדכון היסטוריית כוונות
        if intent_type:
            self.context.intent_history.append({
                "intent_type": intent_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "entities": extracted_entities
            })
            
            # שמירה על גודל סביר
            if len(self.context.intent_history) > 10:
                self.context.intent_history = self.context.intent_history[-10:]
        
        # עדכון ישויות
        for entity_type, entity_value in extracted_entities.items():
            if not entity_value:
                continue
                
            if entity_type == "product":
                self._add_entity("products", entity_value)
                self.context.last_mentioned["product"] = entity_value
                
            elif entity_type == "order":
                self._add_entity("orders", entity_value)
                self.context.last_mentioned["order"] = entity_value
                
            elif entity_type == "customer":
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
        
        # עדכון זמן עדכון אחרון
        self.context.last_update = datetime.now(timezone.utc)
    
    def _add_entity(self, entity_list: str, entity_value: Any) -> None:
        """הוספת ישות לרשימת ישויות"""
        if entity_value not in self.context.entities[entity_list]:
            self.context.entities[entity_list].append(entity_value)
            
            # שמירה על גודל סביר
            if len(self.context.entities[entity_list]) > 10:
                self.context.entities[entity_list] = self.context.entities[entity_list][-10:]
    
    def _get_last_intent(self) -> Optional[Dict[str, Any]]:
        """קבלת הכוונה האחרונה"""
        if not self.context.intent_history:
            return None
        return self.context.intent_history[-1]
    
    def _resolve_pronouns(self, text: str) -> str:
        """
        פתרון כינויי גוף בטקסט
        
        Args:
            text: הטקסט לפתרון
            
        Returns:
            הטקסט לאחר פתרון כינויי גוף
        """
        # החלפת כינויי גוף בשמות ישויות
        resolved_text = text
        
        # החלפת "הוא", "אותו" וכו' במוצר האחרון שהוזכר
        if self.context.last_mentioned["product"]:
            product_name = self.context.last_mentioned["product"]
            resolved_text = resolved_text.replace("הוא", product_name)
            resolved_text = resolved_text.replace("אותו", product_name)
            resolved_text = resolved_text.replace("זה", product_name)
        
        # החלפת "היא", "אותה" וכו' בהזמנה האחרונה שהוזכרה
        if self.context.last_mentioned["order"]:
            order_id = self.context.last_mentioned["order"]
            resolved_text = resolved_text.replace("היא", f"הזמנה {order_id}")
            resolved_text = resolved_text.replace("אותה", f"הזמנה {order_id}")
            resolved_text = resolved_text.replace("זו", f"הזמנה {order_id}")
        
        return resolved_text
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        חישוב דמיון קוסינוס בין שני וקטורים
        
        Args:
            a: וקטור ראשון
            b: וקטור שני
            
        Returns:
            דמיון קוסינוס (0-1)
        """
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        קבלת embedding לטקסט
        
        Args:
            text: הטקסט לחישוב embedding
            
        Returns:
            וקטור embedding
        """
        try:
            response = await self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"שגיאה בקבלת embedding: {str(e)}")
            # החזרת וקטור אפסים במקרה של שגיאה
            return [0.0] * 1536  # גודל וקטור של text-embedding-3-small

# יצירת מופע גלובלי של השירות
memory_service = MemoryService() 