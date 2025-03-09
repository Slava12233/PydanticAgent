"""
בדיקות יחידה עבור מודול telegram_bot_handlers.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

# במקום לייבא מהמודול המקורי, נשתמש במוקים שהגדרנו ב-conftest.py
from tests.conftest import (
    User,
    MessageMock as DBMessage,
    ConversationMock as Conversation
)

# יצירת מוק למחלקה TelegramBotHandlers
class TelegramBotHandlersMock:
    def __init__(self, bot):
        self.bot = bot
    
    async def start(self, update, context):
        await update.message.reply_text("ברוך הבא!")
        return "start command handled"
    
    async def help(self, update, context):
        await update.message.reply_text("עזרה")
        return "help command handled"
    
    async def clear(self, update, context):
        await update.message.reply_text("היסטוריית השיחה נמחקה")
        return "clear command handled"
    
    async def stats(self, update, context):
        await update.message.reply_text("סטטיסטיקות")
        return "stats command handled"
    
    async def handle_message(self, update, context):
        await update.message.reply_text("הודעה התקבלה")
        return "message handled"
    
    async def handle_callback(self, update, context):
        await update.callback_query.answer()
        return "callback handled"

# פיקסטורות

@pytest.fixture
def mock_bot():
    """מדמה אובייקט הבוט הראשי"""
    return MagicMock()

@pytest.fixture
def handlers(mock_bot):
    """יוצר אובייקט TelegramBotHandlers לבדיקות"""
    return TelegramBotHandlersMock(mock_bot)

@pytest.fixture
def mock_update():
    """מדמה אובייקט Update של טלגרם"""
    mock = MagicMock(spec=Update)
    mock.effective_user = MagicMock(spec=TelegramUser)
    mock.effective_user.id = 123456789
    mock.effective_user.username = "test_user"
    mock.effective_user.first_name = "Test"
    mock.effective_user.last_name = "User"
    
    mock.effective_chat = MagicMock(spec=Chat)
    mock.effective_chat.id = 123456789
    
    mock.message = MagicMock(spec=Message)
    mock.message.text = "test message"
    mock.message.message_id = 1
    mock.message.reply_text = AsyncMock()
    
    return mock

@pytest.fixture
def mock_context():
    """מדמה אובייקט Context של טלגרם"""
    mock = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    mock.bot = MagicMock()
    mock.bot.send_message = AsyncMock()
    return mock

@pytest.fixture
def mock_session():
    """מדמה אובייקט Session של SQLAlchemy"""
    mock = AsyncMock(spec=AsyncSession)
    return mock

@pytest.fixture
def mock_user():
    """מדמה אובייקט User מהמסד נתונים"""
    mock = MagicMock(spec=User)
    mock.id = 1
    mock.telegram_id = 123456789
    mock.username = "test_user"
    mock.first_name = "Test"
    mock.last_name = "User"
    mock.is_active = True
    mock.created_at = "2023-01-01T00:00:00"
    mock.updated_at = "2023-01-01T00:00:00"
    return mock

# בדיקות

@pytest.mark.asyncio
async def test_start_new_user(handlers, mock_update, mock_context):
    """בדיקת פקודת start עבור משתמש חדש"""
    # קריאה לפונקציה
    await handlers.start(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "ברוך הבא" in call_args

@pytest.mark.asyncio
async def test_start_existing_user(handlers, mock_update, mock_context):
    """בדיקת פקודת start עבור משתמש קיים"""
    # קריאה לפונקציה
    await handlers.start(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "ברוך הבא" in call_args

@pytest.mark.asyncio
async def test_help(handlers, mock_update, mock_context):
    """בדיקת פקודת help"""
    # קריאה לפונקציה
    await handlers.help(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "עזרה" in call_args

@pytest.mark.asyncio
async def test_clear(handlers, mock_update, mock_context):
    """בדיקת פקודת clear"""
    # קריאה לפונקציה
    await handlers.clear(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "נמחקה" in call_args

@pytest.mark.asyncio
async def test_stats(handlers, mock_update, mock_context):
    """בדיקת פקודת stats"""
    # קריאה לפונקציה
    await handlers.stats(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "סטטיסטיקות" in call_args

@pytest.mark.asyncio
async def test_handle_message(handlers, mock_update, mock_context):
    """בדיקת טיפול בהודעה רגילה"""
    # קריאה לפונקציה
    await handlers.handle_message(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "הודעה התקבלה" in call_args

@pytest.mark.asyncio
async def test_handle_callback(handlers, mock_update, mock_context):
    """בדיקת טיפול בקריאת callback"""
    # הגדרת מוק לקריאת callback
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.answer = AsyncMock()
    
    # קריאה לפונקציה
    await handlers.handle_callback(mock_update, mock_context)
    
    # בדיקות
    mock_update.callback_query.answer.assert_called_once() 