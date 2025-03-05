"""
בדיקות יחידה לשירות הלמידה
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from src.services.learning_service import LearningService
from src.database.database import db
from src.database.models import User, Message, Conversation, BotSettings

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
        
        # יצירת הגדרות למשתמש
        settings = BotSettings(
            user_id=user.id,
            preferences={
                "response_style": "formal",
                "language": "he",
                "interests": ["טכנולוגיה", "מדע"]
            }
        )
        session.add(settings)
        await session.commit()
        
        return user

@pytest_asyncio.fixture
async def learning_service():
    """פיקסצ'ר ליצירת מופע של Learning Service לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת שירות חדש
    service = LearningService()
    
    yield service
    
    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute(text("DELETE FROM messages"))
        await session.execute(text("DELETE FROM conversations"))
        await session.execute(text("DELETE FROM bot_settings"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_analyze_user_patterns(learning_service, test_user):
    """בדיקת ניתוח דפוסי משתמש"""
    # יצירת שיחה עם כמה הודעות חוזרות
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
        
        # הוספת הודעות עם דפוס חוזר
        messages = [
            ("בוקר טוב, מה שלומך?", "user"),
            ("בוקר אור, שלומי טוב!", "assistant"),
            ("בוקר טוב, מה המצב?", "user"),
            ("בוקר נעים, הכל טוב!", "assistant"),
            ("בוקר טוב, מה חדש?", "user"),
            ("בוקר מקסים, הכל מצוין!", "assistant")
        ]
        
        for content, role in messages:
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(message)
        await session.commit()
    
    # ניתוח דפוסים
    patterns = await learning_service.analyze_user_patterns(test_user.id)
    
    # בדיקות
    assert patterns is not None
    assert "greeting_patterns" in patterns
    assert len(patterns["greeting_patterns"]) > 0
    assert any("בוקר טוב" in pattern for pattern in patterns["greeting_patterns"])

@pytest.mark.asyncio
async def test_adapt_response_style(learning_service, test_user):
    """בדיקת התאמת סגנון תשובות"""
    # תשובה מקורית
    original_response = "היי! אשמח לעזור לך עם השאלה שלך."
    
    # התאמת התשובה לסגנון המשתמש
    adapted_response = await learning_service.adapt_response_style(
        user_id=test_user.id,
        original_response=original_response
    )
    
    # בדיקות
    assert adapted_response is not None
    assert adapted_response != original_response
    assert len(adapted_response) > 0
    # בדיקה שהתשובה בעברית
    assert any(ord('\u0590') <= ord(c) <= ord('\u05FF') for c in adapted_response)

@pytest.mark.asyncio
async def test_update_memory_weights(learning_service, test_user):
    """בדיקת עדכון משקלי זיכרון"""
    # יצירת שיחה עם כמה הודעות
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
        
        # הוספת הודעות
        messages = [
            ("אני מתעניין בטכנולוגיה", "user"),
            ("אשמח לשמוע עוד על טכנולוגיה", "assistant"),
            ("בעיקר בתחום הבינה המלאכותית", "user"),
            ("נושא מרתק! אשמח לשתף מידע", "assistant")
        ]
        
        for content, role in messages:
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(message)
        await session.commit()
    
    # עדכון משקלי זיכרון
    await learning_service.update_memory_weights(test_user.id)
    
    # בדיקה שהמשקלים התעדכנו
    async with db.get_session() as session:
        settings = await session.get(BotSettings, test_user.id)
        assert settings is not None
        assert "interests" in settings.preferences
        assert "טכנולוגיה" in settings.preferences["interests"]

@pytest.mark.asyncio
async def test_error_handling(learning_service):
    """בדיקת טיפול בשגיאות"""
    # ניסיון לנתח דפוסים של משתמש לא קיים
    patterns = await learning_service.analyze_user_patterns(999)
    
    # בדיקה שמוחזר מילון ריק במקרה של שגיאה
    assert patterns == {} 