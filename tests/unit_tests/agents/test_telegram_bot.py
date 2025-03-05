"""
בדיקות יחידה לבוט טלגרם
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, Chat, User as TelegramUser
from telegram.ext import ContextTypes

from src.agents.telegram_bot import TelegramBot
from src.database.database import db
from src.database.models import User, BotSettings
from src.services.conversation_service import ConversationService
from src.services.learning_service import LearningService

@pytest_asyncio.fixture
async def telegram_user():
    """פיקסצ'ר ליצירת משתמש טלגרם לבדיקות"""
    return TelegramUser(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="test_user",
        language_code="he"
    )

@pytest_asyncio.fixture
async def telegram_chat():
    """פיקסצ'ר ליצירת צ'אט טלגרם לבדיקות"""
    return Chat(
        id=123456789,
        type="private"
    )

@pytest_asyncio.fixture
async def telegram_message(telegram_user, telegram_chat):
    """פיקסצ'ר ליצירת הודעת טלגרם לבדיקות"""
    return Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=telegram_chat,
        from_user=telegram_user,
        text="שלום, מה שלומך?"
    )

@pytest_asyncio.fixture
async def telegram_update(telegram_message):
    """פיקסצ'ר ליצירת עדכון טלגרם לבדיקות"""
    return Update(
        update_id=1,
        message=telegram_message
    )

@pytest_asyncio.fixture
async def telegram_context():
    """פיקסצ'ר ליצירת קונטקסט טלגרם לבדיקות"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    return context

@pytest_asyncio.fixture
async def test_user():
    """פיקסצ'ר ליצירת משתמש בדיקה במסד הנתונים"""
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
async def telegram_bot():
    """פיקסצ'ר ליצירת בוט טלגרם לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת מופע של הבוט
    bot = TelegramBot(
        token="test_token",
        conversation_service=ConversationService(),
        learning_service=LearningService()
    )
    
    yield bot
    
    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute("DELETE FROM messages")
        await session.execute("DELETE FROM conversations")
        await session.execute("DELETE FROM bot_settings")
        await session.execute("DELETE FROM users")
        await session.commit()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_start_command(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת פקודת start"""
    # הרצת הפקודה
    await telegram_bot.start_command(telegram_update, telegram_context)
    
    # בדיקה שנשלחה הודעת ברוכים הבאים
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert "ברוך הבא" in args[1]["text"]

@pytest.mark.asyncio
async def test_help_command(telegram_bot, telegram_update, telegram_context):
    """בדיקת פקודת help"""
    # הרצת הפקודה
    await telegram_bot.help_command(telegram_update, telegram_context)
    
    # בדיקה שנשלחה הודעת עזרה
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert "הפקודות הזמינות" in args[1]["text"]

@pytest.mark.asyncio
async def test_handle_message(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת טיפול בהודעה רגילה"""
    # הרצת הטיפול בהודעה
    await telegram_bot.handle_message(telegram_update, telegram_context)
    
    # בדיקה שנשלחה תשובה
    telegram_context.bot.send_message.assert_called_once()
    
    # בדיקה שההודעה נשמרה במסד הנתונים
    async with db.get_session() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM messages WHERE content = :content",
            {"content": "שלום, מה שלומך?"}
        )
        count = result.scalar()
        assert count == 1

@pytest.mark.asyncio
async def test_handle_error(telegram_bot, telegram_update, telegram_context):
    """בדיקת טיפול בשגיאות"""
    # יצירת שגיאה
    error = Exception("שגיאת בדיקה")
    
    # הרצת הטיפול בשגיאה
    await telegram_bot.handle_error(telegram_update, telegram_context, error)
    
    # בדיקה שנשלחה הודעת שגיאה
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert "מצטער, אירעה שגיאה" in args[1]["text"]

@pytest.mark.asyncio
async def test_handle_intent(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת זיהוי וטיפול בכוונות"""
    # שינוי תוכן ההודעה לבקשת מזג אוויר
    telegram_update.message.text = "מה מזג האוויר היום?"
    
    # הרצת הטיפול בהודעה
    await telegram_bot.handle_message(telegram_update, telegram_context)
    
    # בדיקה שזוהתה כוונת מזג אוויר ונשלחה תשובה מתאימה
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert any(word in args[1]["text"].lower() for word in ["מזג", "אוויר", "טמפרטורה", "תחזית"])

@pytest.mark.asyncio
async def test_handle_multiple_messages(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת טיפול במספר הודעות ברצף"""
    messages = [
        "שלום, מה שלומך?",
        "אני מחפש מידע על בינה מלאכותית",
        "תודה רבה!"
    ]
    
    for message in messages:
        # עדכון תוכן ההודעה
        telegram_update.message.text = message
        
        # הרצת הטיפול בהודעה
        await telegram_bot.handle_message(telegram_update, telegram_context)
        
        # בדיקה שנשלחה תשובה
        assert telegram_context.bot.send_message.called
        telegram_context.bot.send_message.reset_mock()
    
    # בדיקה שכל ההודעות נשמרו במסד הנתונים
    async with db.get_session() as session:
        result = await session.execute("SELECT COUNT(*) FROM messages")
        count = result.scalar()
        assert count == len(messages)

@pytest.mark.asyncio
async def test_handle_media_message(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת טיפול בהודעות מדיה"""
    # יצירת הודעת תמונה
    photo_message = MagicMock()
    photo_message.photo = [MagicMock()]
    photo_message.caption = "תמונה יפה"
    telegram_update.message = photo_message
    
    # הרצת הטיפול בהודעה
    await telegram_bot.handle_message(telegram_update, telegram_context)
    
    # בדיקה שנשלחה תשובה מתאימה
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert "תמונה" in args[1]["text"].lower()

@pytest.mark.asyncio
async def test_handle_command_in_message(telegram_bot, telegram_update, telegram_context, test_user):
    """בדיקת זיהוי פקודות בתוך הודעות"""
    # שינוי תוכן ההודעה לכלול פקודה
    telegram_update.message.text = "/help בבקשה תעזור לי"
    
    # הרצת הטיפול בהודעה
    await telegram_bot.handle_message(telegram_update, telegram_context)
    
    # בדיקה שנשלחה הודעת עזרה
    telegram_context.bot.send_message.assert_called_once()
    args = telegram_context.bot.send_message.call_args
    assert "הפקודות הזמינות" in args[1]["text"] 