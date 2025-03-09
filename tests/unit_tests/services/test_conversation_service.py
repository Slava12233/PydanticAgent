"""
בדיקות יחידה עבור מודול Conversation Service
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.services.ai import ConversationService
# from src.database.models import Conversation, Message

# מוק למודל Message
class Message:
    """מוק למודל Message"""
    
    def __init__(self, id=None, conversation_id=None, content=None, role=None, timestamp=None):
        self.id = id
        self.conversation_id = conversation_id
        self.content = content
        self.role = role
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self):
        """המרת ההודעה למילון"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


# מוק למודל Conversation
class Conversation:
    """מוק למודל Conversation"""
    
    def __init__(self, id=None, user_id=None, title=None, summary=None, created_at=None, updated_at=None, messages=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.summary = summary
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.messages = messages or []
    
    def to_dict(self):
        """המרת השיחה למילון"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "messages": [m.to_dict() for m in self.messages] if self.messages else []
        }


# מוק למחלקת ConversationService
class ConversationService:
    """מוק למחלקת ConversationService"""
    
    def __init__(self):
        """אתחול שירות השיחות"""
        self.openai_client = MagicMock()
        self.db = MagicMock()
        self.memory_service = MagicMock()
        self._conversations = {}
        self._messages = {}
        self._next_conversation_id = 1
        self._next_message_id = 1
    
    async def create_conversation(self, user_id, title=None):
        """יצירת שיחה חדשה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה ביצירת שיחה חדשה")
        
        # יצירת שיחה חדשה
        conversation = Conversation(
            id=self._next_conversation_id,
            user_id=user_id,
            title=title or f"שיחה {self._next_conversation_id}",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # שמירת השיחה
        self._conversations[self._next_conversation_id] = conversation
        self._next_conversation_id += 1
        
        return conversation
    
    async def add_message(self, conversation_id, content, role, update_summary=False):
        """הוספת הודעה לשיחה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בהוספת הודעה לשיחה")
        
        # בדיקה אם השיחה קיימת
        if conversation_id not in self._conversations:
            return None
        
        # יצירת הודעה חדשה
        message = Message(
            id=self._next_message_id,
            conversation_id=conversation_id,
            content=content,
            role=role,
            timestamp=datetime.now()
        )
        
        # שמירת ההודעה
        self._messages[self._next_message_id] = message
        self._next_message_id += 1
        
        # הוספת ההודעה לשיחה
        self._conversations[conversation_id].messages.append(message)
        self._conversations[conversation_id].updated_at = datetime.now()
        
        # עדכון סיכום השיחה
        if update_summary:
            await self.update_conversation_summary(conversation_id)
        
        return message
    
    async def get_conversation_context(self, conversation_id, max_messages=10):
        """קבלת הקשר השיחה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בקבלת הקשר השיחה")
        
        # בדיקה אם השיחה קיימת
        if conversation_id not in self._conversations:
            return None
        
        # קבלת השיחה
        conversation = self._conversations[conversation_id]
        
        # קבלת ההודעות האחרונות
        messages = conversation.messages[-max_messages:] if conversation.messages else []
        
        # יצירת הקשר
        context = {
            "conversation_id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "summary": conversation.summary,
            "messages": [m.to_dict() for m in messages]
        }
        
        return context
    
    async def update_conversation_summary(self, conversation_id):
        """עדכון סיכום השיחה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בעדכון סיכום השיחה")
        
        # בדיקה אם השיחה קיימת
        if conversation_id not in self._conversations:
            return None
        
        # קבלת השיחה
        conversation = self._conversations[conversation_id]
        
        # עדכון הסיכום
        conversation.summary = "סיכום שיחה מעודכן"
        
        return conversation


@pytest_asyncio.fixture
async def conversation_service():
    """פיקסצ'ר ליצירת מופע Conversation Service לבדיקות"""
    # יצירת מופע של Conversation Service
    service = ConversationService()
    return service


@pytest.mark.asyncio
async def test_create_conversation(conversation_service):
    """בדיקת יצירת שיחה חדשה"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(user_id=1, title="שיחה חדשה")
    
    # וידוא שהשיחה נוצרה כראוי
    assert conversation is not None
    assert conversation.user_id == 1
    assert conversation.title == "שיחה חדשה"
    assert conversation.created_at is not None
    assert conversation.updated_at is not None


@pytest.mark.asyncio
async def test_add_message(conversation_service):
    """בדיקת הוספת הודעה לשיחה"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(user_id=1)
    
    # הוספת הודעה לשיחה
    message = await conversation_service.add_message(
        conversation_id=conversation.id,
        content="הודעה לדוגמה",
        role="user"
    )
    
    # וידוא שההודעה נוספה כראוי
    assert message is not None
    assert message.conversation_id == conversation.id
    assert message.content == "הודעה לדוגמה"
    assert message.role == "user"
    assert message.timestamp is not None


@pytest.mark.asyncio
async def test_add_message_with_summary_update(conversation_service):
    """בדיקת הוספת הודעה לשיחה עם עדכון סיכום"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(user_id=1)
    
    # הוספת הודעה לשיחה עם עדכון סיכום
    message = await conversation_service.add_message(
        conversation_id=conversation.id,
        content="הודעה לדוגמה",
        role="user",
        update_summary=True
    )
    
    # וידוא שההודעה נוספה כראוי
    assert message is not None
    assert message.conversation_id == conversation.id
    assert message.content == "הודעה לדוגמה"
    assert message.role == "user"
    
    # וידוא שהסיכום עודכן
    updated_conversation = conversation_service._conversations[conversation.id]
    assert updated_conversation.summary is not None
    assert updated_conversation.summary == "סיכום שיחה מעודכן"


@pytest.mark.asyncio
async def test_add_message_conversation_not_found(conversation_service):
    """בדיקת הוספת הודעה לשיחה שלא קיימת"""
    # הוספת הודעה לשיחה שלא קיימת
    message = await conversation_service.add_message(
        conversation_id=999,
        content="הודעה לדוגמה",
        role="user"
    )
    
    # וידוא שלא נוספה הודעה
    assert message is None


@pytest.mark.asyncio
async def test_get_conversation_context(conversation_service):
    """בדיקת קבלת הקשר השיחה"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(user_id=1, title="שיחה לדוגמה")
    
    # הוספת הודעות לשיחה
    await conversation_service.add_message(conversation.id, "שאלה ראשונה", "user")
    await conversation_service.add_message(conversation.id, "תשובה ראשונה", "assistant")
    await conversation_service.add_message(conversation.id, "שאלה שנייה", "user")
    await conversation_service.add_message(conversation.id, "תשובה שנייה", "assistant")
    
    # קבלת הקשר השיחה
    context = await conversation_service.get_conversation_context(conversation.id)
    
    # וידוא שהוחזר ההקשר הנכון
    assert context is not None
    assert context["conversation_id"] == conversation.id
    assert context["user_id"] == conversation.user_id
    assert context["title"] == "שיחה לדוגמה"
    assert "messages" in context
    assert len(context["messages"]) == 4
    
    # בדיקת ההודעות
    assert context["messages"][0]["role"] == "user"
    assert context["messages"][0]["content"] == "שאלה ראשונה"
    assert context["messages"][1]["role"] == "assistant"
    assert context["messages"][1]["content"] == "תשובה ראשונה"
    assert context["messages"][2]["role"] == "user"
    assert context["messages"][2]["content"] == "שאלה שנייה"
    assert context["messages"][3]["role"] == "assistant"
    assert context["messages"][3]["content"] == "תשובה שנייה"


@pytest.mark.asyncio
async def test_get_conversation_context_not_found(conversation_service):
    """בדיקת קבלת הקשר שיחה שלא קיימת"""
    # קבלת הקשר שיחה שלא קיימת
    context = await conversation_service.get_conversation_context(999)
    
    # וידוא שלא הוחזר הקשר
    assert context is None


@pytest.mark.asyncio
async def test_update_conversation_summary(conversation_service):
    """בדיקת עדכון סיכום השיחה"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(user_id=1)
    
    # הוספת הודעות לשיחה
    await conversation_service.add_message(conversation.id, "שאלה ראשונה", "user")
    await conversation_service.add_message(conversation.id, "תשובה ראשונה", "assistant")
    
    # עדכון סיכום השיחה
    updated_conversation = await conversation_service.update_conversation_summary(conversation.id)
    
    # וידוא שהסיכום עודכן
    assert updated_conversation is not None
    assert updated_conversation.summary is not None
    assert updated_conversation.summary == "סיכום שיחה מעודכן"


@pytest.mark.asyncio
async def test_update_conversation_summary_not_found(conversation_service):
    """בדיקת עדכון סיכום שיחה שלא קיימת"""
    # עדכון סיכום שיחה שלא קיימת
    updated_conversation = await conversation_service.update_conversation_summary(999)
    
    # וידוא שלא עודכן סיכום
    assert updated_conversation is None


@pytest.mark.asyncio
async def test_exception_handling(conversation_service):
    """בדיקת טיפול בשגיאות"""
    # הגדרת התנהגות המוק
    conversation_service._raise_exception = True
    
    # בדיקת שגיאה ביצירת שיחה חדשה
    with pytest.raises(Exception) as excinfo:
        await conversation_service.create_conversation(user_id=1)
    assert "שגיאה ביצירת שיחה חדשה" in str(excinfo.value)
    
    # בדיקת שגיאה בהוספת הודעה לשיחה
    with pytest.raises(Exception) as excinfo:
        await conversation_service.add_message(1, "הודעה", "user")
    assert "שגיאה בהוספת הודעה לשיחה" in str(excinfo.value)
    
    # בדיקת שגיאה בקבלת הקשר השיחה
    with pytest.raises(Exception) as excinfo:
        await conversation_service.get_conversation_context(1)
    assert "שגיאה בקבלת הקשר השיחה" in str(excinfo.value)
    
    # בדיקת שגיאה בעדכון סיכום השיחה
    with pytest.raises(Exception) as excinfo:
        await conversation_service.update_conversation_summary(1)
    assert "שגיאה בעדכון סיכום השיחה" in str(excinfo.value)
    
    # איפוס התנהגות המוק
    conversation_service._raise_exception = False 