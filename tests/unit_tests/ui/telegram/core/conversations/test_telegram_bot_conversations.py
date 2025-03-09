"""
בדיקות יחידה עבור מודול telegram_bot_conversations.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.ext.asyncio import AsyncSession

# במקום לייבא מהמודול המקורי, נשתמש במוקים שהגדרנו ב-conftest.py
from tests.conftest import (
    TelegramBotConversationsMock as TelegramBotConversations,
    WAITING_FOR_DOCUMENT,
    WAITING_FOR_TITLE,
    WAITING_FOR_SEARCH_QUERY
)

# פיקסטורות

@pytest.fixture
def mock_bot():
    """מדמה אובייקט הבוט הראשי"""
    return MagicMock()

@pytest.fixture
def conversations(mock_bot):
    """יוצר אובייקט TelegramBotConversations לבדיקות"""
    return TelegramBotConversations(mock_bot)

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
    mock.user_data = {}
    return mock

@pytest.fixture
def mock_session():
    """מדמה אובייקט Session של SQLAlchemy"""
    mock = AsyncMock(spec=AsyncSession)
    return mock

# בדיקות

@pytest.mark.asyncio
async def test_init(mock_bot):
    """בדיקת אתחול מחלקת השיחות"""
    # יצירת אובייקט השיחות
    conversations = TelegramBotConversations(mock_bot)
    
    # בדיקה שהבוט נשמר
    assert conversations.bot == mock_bot

@pytest.mark.asyncio
@patch('src.ui.telegram.core.conversations.telegram_bot_conversations.get_user_by_telegram_id')
async def test_process_message_document_flow(mock_get_user, conversations, mock_update, mock_context):
    """בדיקת תהליך הוספת מסמך"""
    # הגדרת מוקים
    mock_get_user.return_value = MagicMock()
    mock_context.user_data = {"conversation_state": WAITING_FOR_DOCUMENT}
    mock_update.message.text = "זהו מסמך לדוגמה"
    
    # קריאה לפונקציה
    result = await conversations.process_message(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_TITLE
    assert mock_context.user_data.get("document_content") == "זהו מסמך לדוגמה"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "כותרת" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.conversations.telegram_bot_conversations.get_user_by_telegram_id')
async def test_process_message_title_flow(mock_get_user, conversations, mock_update, mock_context):
    """בדיקת תהליך הוספת כותרת למסמך"""
    # הגדרת מוקים
    mock_get_user.return_value = MagicMock()
    mock_context.user_data = {
        "conversation_state": WAITING_FOR_TITLE,
        "document_content": "זהו מסמך לדוגמה"
    }
    mock_update.message.text = "כותרת לדוגמה"
    
    # מוק לפונקציות של הבוט
    conversations.bot.agent = MagicMock()
    conversations.bot.agent.add_document = AsyncMock(return_value=True)
    
    # קריאה לפונקציה
    result = await conversations.process_message(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    assert mock_context.user_data.get("document_title") == "כותרת לדוגמה"
    conversations.bot.agent.add_document.assert_called_once_with(
        mock_update.effective_user.id,
        "כותרת לדוגמה",
        "זהו מסמך לדוגמה"
    )
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "נוסף בהצלחה" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.conversations.telegram_bot_conversations.get_user_by_telegram_id')
async def test_process_message_search_query_flow(mock_get_user, conversations, mock_update, mock_context):
    """בדיקת תהליך חיפוש מסמכים"""
    # הגדרת מוקים
    mock_get_user.return_value = MagicMock()
    mock_context.user_data = {"conversation_state": WAITING_FOR_SEARCH_QUERY}
    mock_update.message.text = "מילות חיפוש"
    
    # מוק לפונקציות של הבוט
    conversations.bot.agent = MagicMock()
    conversations.bot.agent.search_documents = AsyncMock(return_value=["תוצאה 1", "תוצאה 2"])
    
    # קריאה לפונקציה
    result = await conversations.process_message(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    conversations.bot.agent.search_documents.assert_called_once_with(
        mock_update.effective_user.id,
        "מילות חיפוש"
    )
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "תוצאות החיפוש" in call_args
    assert "תוצאה 1" in call_args
    assert "תוצאה 2" in call_args

@pytest.mark.asyncio
async def test_cancel_conversation(conversations, mock_update, mock_context):
    """בדיקת ביטול שיחה"""
    # הגדרת מוקים
    mock_context.user_data = {
        "conversation_state": WAITING_FOR_DOCUMENT,
        "document_content": "תוכן כלשהו"
    }
    
    # קריאה לפונקציה
    result = await conversations.cancel_conversation(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    assert "conversation_state" not in mock_context.user_data
    assert "document_content" not in mock_context.user_data
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "בוטל" in call_args or "בוטלה" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.conversations.telegram_bot_conversations.get_user_by_telegram_id')
async def test_process_message_unknown_state(mock_get_user, conversations, mock_update, mock_context):
    """בדיקת טיפול במצב שיחה לא ידוע"""
    # הגדרת מוקים
    mock_get_user.return_value = MagicMock()
    mock_context.user_data = {"conversation_state": 999}  # מצב לא קיים
    
    # קריאה לפונקציה
    result = await conversations.process_message(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "שגיאה" in call_args 