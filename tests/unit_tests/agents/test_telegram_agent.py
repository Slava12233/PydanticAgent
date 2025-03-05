"""
בדיקות יחידה עבור TelegramAgent
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from datetime import datetime
from sqlalchemy import text

from telegram import Update, Message, Chat, User as TelegramUser
from telegram.constants import ChatType
from src.database import db
from src.database.models import User
from src.agents.telegram_agent import TelegramAgent

@pytest.fixture
def telegram_user():
    """פיקסצ'ר ליצירת משתמש טלגרם לבדיקות"""
    return TelegramUser(
        id=123456789,
        first_name="Test",
        is_bot=False,
        username="test_user"
    )

@pytest.fixture
def telegram_chat():
    """פיקסצ'ר ליצירת צ'אט טלגרם לבדיקות"""
    return Chat(
        id=123456789,
        type=ChatType.PRIVATE
    )

@pytest.fixture
def telegram_message(telegram_user, telegram_chat):
    """פיקסצ'ר ליצירת הודעת טלגרם לבדיקות"""
    return Message(
        message_id=1,
        date=datetime(2025, 3, 14),
        chat=telegram_chat,
        from_user=telegram_user,
        text="שלום, מה שלומך?"
    )

@pytest.fixture
def telegram_update(telegram_message):
    """פיקסצ'ר ליצירת עדכון טלגרם לבדיקות"""
    return Update(
        update_id=1,
        message=telegram_message
    )

@pytest.fixture
def telegram_context():
    """פיקסצ'ר ליצירת הקשר טלגרם לבדיקות"""
    return MagicMock()

@pytest_asyncio.fixture
async def test_user():
    """פיקסצ'ר ליצירת משתמש לבדיקות"""
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
async def telegram_agent():
    """פיקסצ'ר ליצירת Agent לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)

    # יצירת מופע של ה-Agent
    agent = TelegramAgent()

    yield agent

    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute(text("DELETE FROM messages"))

@pytest.mark.asyncio
async def test_handle_command(telegram_agent, telegram_update, telegram_context):
    """בדיקת טיפול בפקודות"""
    # יצירת הודעת start
    start_message = MagicMock()
    start_message.text = "/start"
    start_message.from_user = telegram_update.message.from_user
    start_message.chat = telegram_update.message.chat
    start_update = Update(update_id=2, message=start_message)

    # בדיקת פקודת start
    await telegram_agent.handle_command(start_update, telegram_context)
    telegram_context.bot.send_message.assert_called_once()
    assert "שלום" in telegram_context.bot.send_message.call_args[1]["text"]

@pytest.mark.asyncio
async def test_handle_message(telegram_agent, telegram_update, telegram_context, test_user):
    """בדיקת טיפול בהודעות רגילות"""
    # בדיקת הודעה רגילה
    await telegram_agent.handle_message(telegram_update, telegram_context)
    telegram_context.bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_media(telegram_agent, telegram_update, telegram_context):
    """בדיקת טיפול בהודעות מדיה"""
    # יצירת הודעת תמונה
    photo_message = MagicMock()
    photo_message.photo = [MagicMock()]
    photo_message.caption = "תמונה יפה"
    photo_message.from_user = telegram_update.message.from_user
    photo_message.chat = telegram_update.message.chat
    photo_update = Update(update_id=3, message=photo_message)

    # בדיקת טיפול בתמונה
    await telegram_agent.handle_media(photo_update, telegram_context)
    telegram_context.bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_error(telegram_agent, telegram_update, telegram_context):
    """בדיקת טיפול בשגיאות"""
    # יצירת שגיאה
    error = Exception("שגיאת בדיקה")

    # טיפול בשגיאה
    await telegram_agent.handle_error(telegram_update, telegram_context, error)
    telegram_context.bot.send_message.assert_called_once()
    assert "שגיאה" in telegram_context.bot.send_message.call_args[1]["text"]

@pytest.mark.asyncio
async def test_handle_callback_query(telegram_agent, telegram_context):
    """בדיקת טיפול בכפתורים"""
    # יצירת callback query
    callback_query = MagicMock()
    callback_query.data = "confirm_test"
    callback_query.message = MagicMock()
    callback_query.from_user = MagicMock()
    callback_query.from_user.id = 123456789
    callback_query.message.chat_id = 123456789
    callback_query.message.message_id = 1
    callback_update = Update(update_id=4, callback_query=callback_query)

    # טיפול בכפתור
    await telegram_agent.handle_callback_query(callback_update, telegram_context)
    callback_query.answer.assert_called_once()
    telegram_context.bot.edit_message_text.assert_called_once()
    assert "אושרה" in telegram_context.bot.edit_message_text.call_args[1]["text"]

@pytest.mark.asyncio
async def test_format_response(telegram_agent):
    """בדיקת פורמט תשובות"""
    # בדיקת תשובה רגילה
    response = await telegram_agent.format_response("זו תשובת בדיקה")
    assert response == "זו תשובת בדיקה"

    # בדיקת תשובה ארוכה
    long_response = "א" * 5000
    formatted_response = await telegram_agent.format_response(long_response)
    assert len(formatted_response) <= 4096
    assert formatted_response.endswith("...") 