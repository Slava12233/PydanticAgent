"""
בדיקות יחידה לשירות השיחות
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from src.services.conversation_service import ConversationService
from src.database.database import db
from src.database.models import User

@pytest_asyncio.fixture
async def test_user():
    """פיקסצ'ר ליצירת משתמש בדיקה"""
    async with db.get_session() as session:
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        return user

@pytest_asyncio.fixture
async def conversation_service():
    """פיקסצ'ר ליצירת מופע של Conversation Service לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת שירות חדש
    service = ConversationService()
    
    yield service
    
    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute(text("DELETE FROM messages"))
        await session.execute(text("DELETE FROM conversations"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_create_conversation(conversation_service, test_user):
    """בדיקת יצירת שיחה חדשה"""
    # יצירת שיחה חדשה
    conversation = await conversation_service.create_conversation(test_user.id, "שיחת בדיקה")
    
    # בדיקה שהשיחה נוצרה
    assert conversation is not None
    assert conversation.user_id == test_user.id
    assert conversation.title == "שיחת בדיקה"
    assert conversation.is_active is True
    assert conversation.context is not None
    assert "start_time" in conversation.context

@pytest.mark.asyncio
async def test_add_message(conversation_service, test_user):
    """בדיקת הוספת הודעה לשיחה"""
    # יצירת שיחה
    conversation = await conversation_service.create_conversation(test_user.id, "שיחת בדיקה")
    
    # הוספת הודעה
    await conversation_service.add_message(
        conversation_id=conversation.id,
        role="user",
        content="הודעת בדיקה"
    )
    
    # בדיקה שההודעה נשמרה
    async with db.get_session() as session:
        result = await session.execute(
            text("SELECT * FROM messages WHERE conversation_id = :id"),
            {"id": conversation.id}
        )
        messages = result.fetchall()
        
        assert len(messages) == 1
        assert messages[0].content == "הודעת בדיקה"
        assert messages[0].role == "user"

@pytest.mark.asyncio
async def test_get_conversation_context(conversation_service, test_user):
    """בדיקת קבלת הקשר שיחה"""
    # יצירת שיחה עם כמה הודעות
    conversation = await conversation_service.create_conversation(test_user.id, "שיחת בדיקה")
    
    messages = [
        ("שלום, מה שלומך?", "user"),
        ("שלומי טוב, תודה ששאלת!", "assistant"),
        ("יופי, אשמח לשאול כמה שאלות", "user")
    ]
    
    for content, role in messages:
        await conversation_service.add_message(conversation.id, role, content)
    
    # קבלת הקשר השיחה
    context = await conversation_service.get_conversation_context(
        conversation_id=conversation.id,
        query="שלום"
    )
    
    # בדיקות
    assert context is not None
    assert context["conversation_id"] == conversation.id
    assert context["title"] == "שיחת בדיקה"
    assert len(context["recent_messages"]) > 0
    assert isinstance(context["context"], dict)

@pytest.mark.asyncio
async def test_conversation_summary(conversation_service, test_user):
    """בדיקת עדכון תקציר שיחה"""
    # יצירת שיחה עם מספיק הודעות לעדכון תקציר
    conversation = await conversation_service.create_conversation(test_user.id, "שיחת בדיקה")
    
    # הוספת 5 הודעות (מספר ההודעות שמפעיל עדכון תקציר)
    messages = [
        ("שלום, אני מחפש מידע על מזג האוויר", "user"),
        ("היום יהיה חם ושמשי", "assistant"),
        ("ומה לגבי מחר?", "user"),
        ("מחר צפוי להיות גשום", "assistant"),
        ("תודה רבה על המידע", "user")
    ]
    
    for content, role in messages:
        await conversation_service.add_message(conversation.id, role, content)
    
    # בדיקה שהתקציר התעדכן
    async with db.get_session() as session:
        result = await session.execute(
            text("SELECT summary FROM conversations WHERE id = :id"),
            {"id": conversation.id}
        )
        summary = result.scalar()
        assert summary is not None

@pytest.mark.asyncio
async def test_error_handling(conversation_service):
    """בדיקת טיפול בשגיאות"""
    # ניסיון להוסיף הודעה לשיחה לא קיימת
    await conversation_service.add_message(
        conversation_id=999,
        role="user",
        content="הודעת בדיקה"
    )
    
    # בדיקה שלא נוספה הודעה
    async with db.get_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM messages"))
        count = result.scalar()
        assert count == 0

@pytest.mark.asyncio
async def test_parallel_conversations(conversation_service, test_user):
    """בדיקת טיפול בשיחות מקבילות"""
    # יצירת שתי שיחות במקביל
    conversation1 = await conversation_service.create_conversation(test_user.id, "שיחה 1")
    conversation2 = await conversation_service.create_conversation(test_user.id, "שיחה 2")
    
    # הוספת הודעות לשתי השיחות לסירוגין
    messages1 = [
        ("שלום, זו שיחה ראשונה", "user"),
        ("אהלן, כן זו שיחה ראשונה", "assistant")
    ]
    
    messages2 = [
        ("היי, זו שיחה שנייה", "user"),
        ("נכון, זו שיחה שנייה", "assistant")
    ]
    
    for (content1, role1), (content2, role2) in zip(messages1, messages2):
        # הוספת הודעה לשיחה 1
        await conversation_service.add_message(
            conversation_id=conversation1.id,
            role=role1,
            content=content1
        )
        
        # הוספת הודעה לשיחה 2
        await conversation_service.add_message(
            conversation_id=conversation2.id,
            role=role2,
            content=content2
        )
    
    # בדיקה שההודעות נשמרו נכון בכל שיחה
    async with db.get_session() as session:
        # בדיקת שיחה 1
        result1 = await session.execute(
            text("SELECT content FROM messages WHERE conversation_id = :id ORDER BY timestamp"),
            {"id": conversation1.id}
        )
        messages_content1 = [row[0] for row in result1]
        assert len(messages_content1) == 2
        assert messages_content1[0] == "שלום, זו שיחה ראשונה"
        assert messages_content1[1] == "אהלן, כן זו שיחה ראשונה"
        
        # בדיקת שיחה 2
        result2 = await session.execute(
            text("SELECT content FROM messages WHERE conversation_id = :id ORDER BY timestamp"),
            {"id": conversation2.id}
        )
        messages_content2 = [row[0] for row in result2]
        assert len(messages_content2) == 2
        assert messages_content2[0] == "היי, זו שיחה שנייה"
        assert messages_content2[1] == "נכון, זו שיחה שנייה" 