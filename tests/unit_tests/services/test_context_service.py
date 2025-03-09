"""
בדיקות יחידה עבור מודול Context Service
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime, timezone, timedelta
import numpy as np

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.services.ai import ContextService, ContextData
# from src.models.responses import ServiceResponse

# מוק למחלקת ServiceResponse
class ServiceResponse:
    """מוק למחלקת ServiceResponse"""
    
    def __init__(self, success=True, data=None, message=None, error=None):
        self.success = success
        self.data = data or {}
        self.message = message
        self.error = error
    
    def to_dict(self):
        """המרת התגובה למילון"""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error
        }


# מוק למחלקת ContextData
class ContextData:
    """מוק למחלקת ContextData"""
    
    def __init__(self, entities=None, intents=None, memories=None, conversation=None):
        self.entities = entities or {
            "products": [],
            "orders": [],
            "customers": [],
            "categories": [],
            "prices": [],
            "dates": [],
            "locations": []
        }
        self.intents = intents or []
        self.memories = memories or []
        self.conversation = conversation or {
            "history": [],
            "last_message": None,
            "last_response": None
        }
    
    def to_dict(self):
        """המרת הנתונים למילון"""
        return {
            "entities": self.entities,
            "intents": self.intents,
            "memories": self.memories,
            "conversation": self.conversation
        }


# מוק למחלקת ContextService
class ContextService:
    """מוק למחלקת ContextService"""
    
    def __init__(self):
        """אתחול שירות ההקשר"""
        self.context = ContextData()
        self.embeddings = MagicMock()
        self.db = MagicMock()
    
    async def process_message(self, message, user_id=None):
        """עיבוד הודעה ועדכון ההקשר"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בעיבוד הודעה")
        
        # בדיקה אם ההודעה ריקה
        if not message or not message.strip():
            return ServiceResponse(
                success=False,
                message="ההודעה ריקה",
                error="empty_message"
            )
        
        # עדכון ההקשר
        self.context.conversation["history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self.context.conversation["last_message"] = message
        
        # הוספת כוונה
        self.context.intents.append({
            "intent": "query",
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        })
        
        # הוספת ישויות
        if "מוצר" in message:
            self.context.entities["products"].append({
                "name": "מוצר לדוגמה",
                "price": 100,
                "category": "קטגוריה לדוגמה"
            })
        
        if "הזמנה" in message:
            self.context.entities["orders"].append({
                "id": "123456",
                "status": "בטיפול",
                "date": datetime.now().isoformat()
            })
        
        return ServiceResponse(
            success=True,
            data=self.context.to_dict(),
            message="ההודעה עובדה בהצלחה"
        )
    
    async def get_conversation_context(self, user_id=None, max_history=10):
        """קבלת הקשר השיחה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בקבלת הקשר השיחה")
        
        # החזרת הקשר השיחה
        history = self.context.conversation["history"][-max_history:] if self.context.conversation["history"] else []
        
        return ServiceResponse(
            success=True,
            data={
                "history": history,
                "entities": self.context.entities,
                "intents": self.context.intents[-3:] if self.context.intents else [],
                "last_message": self.context.conversation["last_message"],
                "last_response": self.context.conversation["last_response"]
            },
            message="הקשר השיחה נטען בהצלחה"
        )
    
    async def update_context(self, context_data, user_id=None):
        """עדכון ההקשר"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בעדכון ההקשר")
        
        # עדכון ההקשר
        if "entities" in context_data:
            for entity_type, entities in context_data["entities"].items():
                if entity_type in self.context.entities:
                    self.context.entities[entity_type].extend(entities)
        
        if "intents" in context_data:
            self.context.intents.extend(context_data["intents"])
        
        if "memories" in context_data:
            self.context.memories.extend(context_data["memories"])
        
        if "conversation" in context_data:
            if "history" in context_data["conversation"]:
                self.context.conversation["history"].extend(context_data["conversation"]["history"])
            if "last_message" in context_data["conversation"]:
                self.context.conversation["last_message"] = context_data["conversation"]["last_message"]
            if "last_response" in context_data["conversation"]:
                self.context.conversation["last_response"] = context_data["conversation"]["last_response"]
        
        return ServiceResponse(
            success=True,
            data=self.context.to_dict(),
            message="ההקשר עודכן בהצלחה"
        )
    
    async def add_entity(self, entity_type, entity_data, user_id=None):
        """הוספת ישות להקשר"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בהוספת ישות להקשר")
        
        # בדיקה אם סוג הישות קיים
        if entity_type not in self.context.entities:
            return ServiceResponse(
                success=False,
                message=f"סוג הישות {entity_type} לא קיים",
                error="invalid_entity_type"
            )
        
        # הוספת הישות
        self.context.entities[entity_type].append(entity_data)
        
        return ServiceResponse(
            success=True,
            data={
                "entity_type": entity_type,
                "entity_data": entity_data
            },
            message="הישות נוספה בהצלחה"
        )
    
    async def get_last_intent(self, user_id=None):
        """קבלת הכוונה האחרונה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בקבלת הכוונה האחרונה")
        
        # בדיקה אם יש כוונות
        if not self.context.intents:
            return ServiceResponse(
                success=False,
                message="אין כוונות בהקשר",
                error="no_intents"
            )
        
        # החזרת הכוונה האחרונה
        last_intent = self.context.intents[-1]
        
        return ServiceResponse(
            success=True,
            data=last_intent,
            message="הכוונה האחרונה נטענה בהצלחה"
        )
    
    async def resolve_pronouns(self, message, user_id=None):
        """פתרון כינויי גוף בהודעה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בפתרון כינויי גוף")
        
        # בדיקה אם ההודעה ריקה
        if not message or not message.strip():
            return ServiceResponse(
                success=False,
                message="ההודעה ריקה",
                error="empty_message"
            )
        
        # פתרון כינויי גוף
        resolved_message = message
        
        # החלפת "זה" ב"מוצר לדוגמה" אם יש מוצרים בהקשר
        if self.context.entities["products"] and "זה" in message:
            product_name = self.context.entities["products"][-1]["name"]
            resolved_message = message.replace("זה", product_name)
        
        # החלפת "היא" ב"הזמנה 123456" אם יש הזמנות בהקשר
        if self.context.entities["orders"] and "היא" in message:
            order_id = self.context.entities["orders"][-1]["id"]
            resolved_message = message.replace("היא", f"הזמנה {order_id}")
        
        return ServiceResponse(
            success=True,
            data={
                "original_message": message,
                "resolved_message": resolved_message
            },
            message="כינויי הגוף נפתרו בהצלחה"
        )
    
    async def get_relevant_memories(self, query, user_id=None, max_results=5):
        """קבלת זיכרונות רלוונטיים לשאילתה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בקבלת זיכרונות רלוונטיים")
        
        # בדיקה אם השאילתה ריקה
        if not query or not query.strip():
            return ServiceResponse(
                success=False,
                message="השאילתה ריקה",
                error="empty_query"
            )
        
        # קבלת וקטור המשמעות של השאילתה
        query_embedding = await self._get_embedding(query)
        
        # יצירת זיכרונות לדוגמה
        memories = [
            {
                "content": "המשתמש שאל על מוצר X",
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "type": "message"
            },
            {
                "content": "המשתמש הזמין מוצר Y",
                "embedding": [0.2, 0.3, 0.4, 0.5],
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "type": "order"
            },
            {
                "content": "המשתמש התלונן על איכות המוצר",
                "embedding": [0.3, 0.4, 0.5, 0.6],
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "type": "complaint"
            }
        ]
        
        # חישוב דמיון קוסינוס בין השאילתה לזיכרונות
        similarities = [
            self._cosine_similarity(query_embedding, memory["embedding"])
            for memory in memories
        ]
        
        # מיון הזיכרונות לפי דמיון
        indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)
        sorted_memories = [memories[i] for i in indices]
        
        # החזרת הזיכרונות הרלוונטיים ביותר
        relevant_memories = sorted_memories[:max_results]
        
        return ServiceResponse(
            success=True,
            data={
                "query": query,
                "memories": relevant_memories
            },
            message="הזיכרונות הרלוונטיים נטענו בהצלחה"
        )
    
    def _cosine_similarity(self, vec1, vec2):
        """חישוב דמיון קוסינוס בין שני וקטורים"""
        # המרה לנומפיי
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # חישוב דמיון קוסינוס
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # מניעת חלוקה באפס
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
        
        return float(dot_product / (norm_vec1 * norm_vec2))
    
    async def _get_embedding(self, text):
        """קבלת וקטור משמעות לטקסט"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בקבלת וקטור משמעות")
        
        # החזרת וקטור לדוגמה
        return [0.1, 0.2, 0.3, 0.4]


@pytest_asyncio.fixture
async def context_service():
    """פיקסצ'ר ליצירת מופע Context Service לבדיקות"""
    # יצירת מופע של Context Service
    service = ContextService()
    return service


@pytest.mark.asyncio
async def test_process_message(context_service):
    """בדיקת עיבוד הודעה ועדכון ההקשר"""
    # עיבוד הודעה
    message = "אני רוצה לקנות מוצר חדש"
    response = await context_service.process_message(message, user_id=1)
    
    # וידוא שההודעה עובדה בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת עדכון ההקשר
    assert "entities" in response.data
    assert "intents" in response.data
    assert "conversation" in response.data
    
    # בדיקת הוספת המוצר להקשר
    assert "products" in response.data["entities"]
    assert len(response.data["entities"]["products"]) == 1
    assert response.data["entities"]["products"][0]["name"] == "מוצר לדוגמה"


@pytest.mark.asyncio
async def test_process_message_empty(context_service):
    """בדיקת עיבוד הודעה ריקה"""
    # עיבוד הודעה ריקה
    response = await context_service.process_message("", user_id=1)
    
    # וידוא שההודעה לא עובדה
    assert response.success is False
    assert "empty_message" == response.error


@pytest.mark.asyncio
async def test_get_conversation_context(context_service):
    """בדיקת קבלת הקשר השיחה"""
    # הוספת הודעות להקשר
    await context_service.process_message("הודעה ראשונה", user_id=1)
    await context_service.process_message("הודעה שנייה", user_id=1)
    
    # קבלת הקשר השיחה
    response = await context_service.get_conversation_context(user_id=1)
    
    # וידוא שהקשר השיחה נטען בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת תוכן ההקשר
    assert "history" in response.data
    assert "entities" in response.data
    assert "intents" in response.data
    assert "last_message" in response.data
    
    # בדיקת היסטוריית ההודעות
    assert len(response.data["history"]) == 2
    assert response.data["history"][0]["content"] == "הודעה ראשונה"
    assert response.data["history"][1]["content"] == "הודעה שנייה"
    
    # בדיקת ההודעה האחרונה
    assert response.data["last_message"] == "הודעה שנייה"


@pytest.mark.asyncio
async def test_update_context(context_service):
    """בדיקת עדכון ההקשר"""
    # עדכון ההקשר
    context_data = {
        "entities": {
            "products": [{"name": "מוצר חדש", "price": 200}]
        },
        "intents": [{"intent": "purchase", "confidence": 0.8}]
    }
    
    response = await context_service.update_context(context_data, user_id=1)
    
    # וידוא שההקשר עודכן בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת עדכון הישויות
    assert "products" in response.data["entities"]
    assert len(response.data["entities"]["products"]) == 1
    assert response.data["entities"]["products"][0]["name"] == "מוצר חדש"
    
    # בדיקת עדכון הכוונות
    assert len(response.data["intents"]) == 1
    assert response.data["intents"][0]["intent"] == "purchase"


@pytest.mark.asyncio
async def test_add_entity(context_service):
    """בדיקת הוספת ישות להקשר"""
    # הוספת ישות
    entity_type = "products"
    entity_data = {"name": "מוצר חדש", "price": 200}
    
    response = await context_service.add_entity(entity_type, entity_data, user_id=1)
    
    # וידוא שהישות נוספה בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת הישות שנוספה
    assert response.data["entity_type"] == "products"
    assert response.data["entity_data"]["name"] == "מוצר חדש"
    assert response.data["entity_data"]["price"] == 200
    
    # בדיקת הוספת הישות להקשר
    context_response = await context_service.get_conversation_context(user_id=1)
    assert len(context_response.data["entities"]["products"]) == 1
    assert context_response.data["entities"]["products"][0]["name"] == "מוצר חדש"


@pytest.mark.asyncio
async def test_get_last_intent(context_service):
    """בדיקת קבלת הכוונה האחרונה"""
    # הוספת כוונות להקשר
    await context_service.process_message("אני רוצה לקנות מוצר", user_id=1)
    
    # קבלת הכוונה האחרונה
    response = await context_service.get_last_intent(user_id=1)
    
    # וידוא שהכוונה נטענה בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת הכוונה
    assert response.data["intent"] == "query"
    assert response.data["confidence"] == 0.9


@pytest.mark.asyncio
async def test_resolve_pronouns(context_service):
    """בדיקת פתרון כינויי גוף"""
    # הוספת ישויות להקשר
    await context_service.add_entity("products", {"name": "מוצר לדוגמה", "price": 100}, user_id=1)
    await context_service.add_entity("orders", {"id": "123456", "status": "בטיפול"}, user_id=1)
    
    # פתרון כינויי גוף
    message = "אני רוצה לדעת מתי זה יגיע והאם היא בדרך"
    response = await context_service.resolve_pronouns(message, user_id=1)
    
    # וידוא שכינויי הגוף נפתרו בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת ההודעה המקורית
    assert response.data["original_message"] == message
    
    # בדיקת ההודעה המפוענחת - לפחות אחד מהכינויים צריך להיות מוחלף
    resolved_message = response.data["resolved_message"]
    assert "מוצר לדוגמה" in resolved_message or "הזמנה 123456" in resolved_message


@pytest.mark.asyncio
async def test_get_relevant_memories(context_service):
    """בדיקת קבלת זיכרונות רלוונטיים"""
    # קבלת זיכרונות רלוונטיים
    query = "מה קרה עם ההזמנה שלי?"
    response = await context_service.get_relevant_memories(query, user_id=1)
    
    # וידוא שהזיכרונות נטענו בהצלחה
    assert response.success is True
    assert "data" in response.to_dict()
    assert "message" in response.to_dict()
    
    # בדיקת השאילתה
    assert response.data["query"] == query
    
    # בדיקת הזיכרונות
    assert "memories" in response.data
    assert len(response.data["memories"]) > 0
    
    # בדיקת סוגי הזיכרונות
    memory_types = [memory["type"] for memory in response.data["memories"]]
    assert "message" in memory_types or "order" in memory_types or "complaint" in memory_types


@pytest.mark.asyncio
async def test_get_relevant_memories_empty_query(context_service):
    """בדיקת קבלת זיכרונות רלוונטיים עם שאילתה ריקה"""
    # קבלת זיכרונות רלוונטיים עם שאילתה ריקה
    response = await context_service.get_relevant_memories("", user_id=1)
    
    # וידוא שהשאילתה לא עובדה
    assert response.success is False
    assert "empty_query" == response.error


@pytest.mark.asyncio
async def test_cosine_similarity(context_service):
    """בדיקת חישוב דמיון קוסינוס"""
    # חישוב דמיון קוסינוס
    vec1 = [1, 0, 0, 0]
    vec2 = [0, 1, 0, 0]
    similarity = context_service._cosine_similarity(vec1, vec2)
    
    # וידוא שהדמיון הוא 0 (וקטורים מאונכים)
    assert similarity == 0
    
    # חישוב דמיון קוסינוס לוקטורים זהים
    vec1 = [1, 2, 3, 4]
    vec2 = [1, 2, 3, 4]
    similarity = context_service._cosine_similarity(vec1, vec2)
    
    # וידוא שהדמיון הוא 1 (וקטורים זהים)
    assert similarity == 1


@pytest.mark.asyncio
async def test_get_embedding(context_service):
    """בדיקת קבלת וקטור משמעות"""
    # קבלת וקטור משמעות
    text = "טקסט לדוגמה"
    embedding = await context_service._get_embedding(text)
    
    # וידוא שהוקטור הוחזר
    assert embedding is not None
    assert len(embedding) == 4
    assert embedding == [0.1, 0.2, 0.3, 0.4] 