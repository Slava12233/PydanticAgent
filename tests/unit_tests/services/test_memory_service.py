"""
בדיקות יחידה עבור מודול Memory Service
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime, timedelta

from src.services.ai import MemoryService, ContextData
from src.models.memory import MemoryType, ServiceResponse


@pytest_asyncio.fixture
async def memory_service():
    """פיקסצ'ר ליצירת מופע Memory Service לבדיקות"""
    # יצירת מופע מדומה של Memory Service
    with patch('src.services.ai.memory_service.OpenAIEmbeddings'), \
         patch('src.services.ai.memory_service.db'):
        service = MemoryService()
        # מוק לפונקציות
        service._get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        service._context = ContextData(
            entities={
                "products": [],
                "orders": [],
                "customers": []
            },
            last_mentioned={},
            intent_history=[],
            last_update=datetime.now()
        )
        yield service


@pytest.mark.asyncio
async def test_process_message(memory_service):
    """בדיקת עיבוד הודעה"""
    # מוק לפונקציות מסד הנתונים
    with patch('src.services.ai.memory_service.db') as mock_db:
        mock_db.execute = AsyncMock(return_value=None)
        
        # הרצת הפונקציה
        result = await memory_service.process_message(
            message="אני רוצה לקנות מוצר חדש",
            role="user",
            intent_type="product_search",
            extracted_entities={"products": ["מוצר חדש"]}
        )
        
        # וידוא שהפונקציה נקראה
        mock_db.execute.assert_called_once()
        
        # וידוא שהוחזרה תוצאה חיובית
        assert result.success is True
        assert result.message == "Memory saved successfully"


@pytest.mark.asyncio
async def test_get_relevant_memories(memory_service):
    """בדיקת קבלת זיכרונות רלוונטיים"""
    # יצירת זיכרונות לדוגמה
    sample_memories = [
        {
            "id": 1,
            "content": "אני רוצה לקנות מוצר חדש",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "memory_type": "message",
            "created_at": datetime.now() - timedelta(minutes=5),
            "metadata": {"role": "user"}
        },
        {
            "id": 2,
            "content": "הנה המוצרים שלנו",
            "embedding": [0.2, 0.3, 0.4, 0.5],
            "memory_type": "message",
            "created_at": datetime.now() - timedelta(minutes=4),
            "metadata": {"role": "assistant"}
        }
    ]
    
    # מוק לפונקציות מסד הנתונים
    with patch('src.services.ai.memory_service.db') as mock_db:
        mock_db.fetch_all = AsyncMock(return_value=sample_memories)
        
        # הרצת הפונקציה
        results = await memory_service.get_relevant_memories(
            query="מוצר",
            limit=5,
            min_similarity=0.3,
            memory_types=[MemoryType.MESSAGE]
        )
        
        # וידוא שהפונקציה נקראה
        mock_db.fetch_all.assert_called_once()
        
        # וידוא שהוחזרו התוצאות הנכונות
        assert len(results) == 2
        assert results[0]["content"] == "אני רוצה לקנות מוצר חדש"
        assert results[1]["content"] == "הנה המוצרים שלנו"


@pytest.mark.asyncio
async def test_get_conversation_context(memory_service):
    """בדיקת קבלת הקשר שיחה"""
    # יצירת זיכרונות לדוגמה
    sample_memories = [
        {
            "id": 1,
            "content": "אני רוצה לקנות מוצר חדש",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "memory_type": "message",
            "created_at": datetime.now() - timedelta(minutes=5),
            "metadata": {"role": "user"}
        },
        {
            "id": 2,
            "content": "הנה המוצרים שלנו",
            "embedding": [0.2, 0.3, 0.4, 0.5],
            "memory_type": "message",
            "created_at": datetime.now() - timedelta(minutes=4),
            "metadata": {"role": "assistant"}
        }
    ]
    
    # מוק לפונקציות מסד הנתונים
    with patch('src.services.ai.memory_service.db') as mock_db:
        mock_db.fetch_all = AsyncMock(return_value=sample_memories)
        
        # הרצת הפונקציה
        context = await memory_service.get_conversation_context(
            query="מוצר",
            limit=5,
            min_similarity=0.3
        )
        
        # וידוא שהפונקציה נקראה
        mock_db.fetch_all.assert_called_once()
        
        # וידוא שהוחזר ההקשר הנכון
        assert "messages" in context
        assert len(context["messages"]) == 2
        assert context["messages"][0]["content"] == "אני רוצה לקנות מוצר חדש"
        assert context["messages"][0]["role"] == "user"
        assert context["messages"][1]["content"] == "הנה המוצרים שלנו"
        assert context["messages"][1]["role"] == "assistant"
        
        # וידוא שהוחזר גם הקשר ישויות
        assert "entities" in context
        assert "products" in context["entities"]
        assert "orders" in context["entities"]
        assert "customers" in context["entities"]


@pytest.mark.asyncio
async def test_update_context(memory_service):
    """בדיקת עדכון הקשר"""
    # הרצת הפונקציה
    memory_service._update_context(
        message="אני רוצה לקנות מוצר חדש",
        intent_type="product_search",
        extracted_entities={"products": ["מוצר חדש"]}
    )
    
    # וידוא שההקשר עודכן
    assert len(memory_service._context.entities["products"]) == 1
    assert memory_service._context.entities["products"][0] == "מוצר חדש"
    assert len(memory_service._context.intent_history) == 1
    assert memory_service._context.intent_history[0]["type"] == "product_search"


@pytest.mark.asyncio
async def test_add_entity(memory_service):
    """בדיקת הוספת ישות"""
    # הרצת הפונקציה
    memory_service._add_entity("products", "מוצר חדש")
    
    # וידוא שהישות נוספה
    assert len(memory_service._context.entities["products"]) == 1
    assert memory_service._context.entities["products"][0] == "מוצר חדש"
    
    # הוספת ישות נוספת
    memory_service._add_entity("products", "מוצר נוסף")
    
    # וידוא שהישות נוספה
    assert len(memory_service._context.entities["products"]) == 2
    assert memory_service._context.entities["products"][1] == "מוצר נוסף"
    
    # הוספת ישות קיימת
    memory_service._add_entity("products", "מוצר חדש")
    
    # וידוא שהישות לא נוספה שוב
    assert len(memory_service._context.entities["products"]) == 2


@pytest.mark.asyncio
async def test_get_last_intent(memory_service):
    """בדיקת קבלת כוונה אחרונה"""
    # הוספת כוונות להיסטוריה
    memory_service._context.intent_history = [
        {"type": "product_search", "timestamp": datetime.now() - timedelta(minutes=5)},
        {"type": "order_status", "timestamp": datetime.now() - timedelta(minutes=2)}
    ]
    
    # הרצת הפונקציה
    last_intent = memory_service._get_last_intent()
    
    # וידוא שהוחזרה הכוונה האחרונה
    assert last_intent is not None
    assert last_intent["type"] == "order_status"


@pytest.mark.asyncio
async def test_resolve_pronouns(memory_service):
    """בדיקת פתרון כינויי גוף"""
    # הגדרת הקשר
    memory_service._context.last_mentioned = {
        "product": "מוצר חדש",
        "order": "הזמנה 123"
    }
    
    # הרצת הפונקציה
    resolved_text = memory_service._resolve_pronouns("אני רוצה לקנות אותו")
    
    # וידוא שהטקסט פוענח
    assert "מוצר חדש" in resolved_text
    assert "אני רוצה לקנות מוצר חדש" == resolved_text
    
    # בדיקה נוספת
    resolved_text = memory_service._resolve_pronouns("מה הסטטוס שלה?")
    
    # וידוא שהטקסט פוענח
    assert "הזמנה 123" in resolved_text
    assert "מה הסטטוס של הזמנה 123?" == resolved_text


@pytest.mark.asyncio
async def test_cosine_similarity(memory_service):
    """בדיקת חישוב דמיון קוסינוס"""
    # וקטורים לבדיקה
    vec1 = [1, 0, 0, 0]
    vec2 = [0, 1, 0, 0]
    vec3 = [1, 1, 0, 0]
    
    # הרצת הפונקציה
    sim1_2 = memory_service._cosine_similarity(vec1, vec2)
    sim1_3 = memory_service._cosine_similarity(vec1, vec3)
    sim1_1 = memory_service._cosine_similarity(vec1, vec1)
    
    # וידוא שהדמיון חושב נכון
    assert sim1_2 == 0  # וקטורים מאונכים
    assert 0 < sim1_3 < 1  # וקטורים בזווית חדה
    assert sim1_1 == 1  # אותו וקטור


@pytest.mark.asyncio
async def test_get_embedding(memory_service):
    """בדיקת קבלת וקטור הטבעה"""
    # הרצת הפונקציה
    embedding = await memory_service._get_embedding("טקסט לבדיקה")
    
    # וידוא שהוחזר וקטור
    assert embedding is not None
    assert len(embedding) == 4  # לפי המוק שהגדרנו
    assert embedding == [0.1, 0.2, 0.3, 0.4] 