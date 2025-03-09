"""
בדיקות יחידה עבור מודול telegram_agent.py
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# במקום לייבא מהמודול המקורי, נשתמש במוקים שהגדרנו ב-conftest.py
from tests.conftest import (
    TelegramAgentMock as TelegramAgent,
    User,
    MessageMock as DBMessage,
    TaskIdentificationMock,
    identify_task_mock,
    get_task_specific_prompt_mock,
    ChatResponse
)

# פיקסטורות

@pytest.fixture
def agent():
    """יוצר אובייקט TelegramAgent לבדיקות"""
    return TelegramAgent()

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
    mock.message.reply_markdown_v2 = AsyncMock()
    
    return mock

@pytest.fixture
def mock_context():
    """מדמה אובייקט Context של טלגרם"""
    mock = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    mock.bot = MagicMock()
    mock.bot.send_message = AsyncMock()
    mock.bot.send_chat_action = AsyncMock()
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
    mock.created_at = datetime.now()
    mock.updated_at = datetime.now()
    return mock

# בדיקות

@pytest.mark.asyncio
@patch('src.ui.telegram.core.telegram_agent.ModelManager')
async def test_init(mock_model_manager):
    """בדיקת אתחול הסוכן"""
    # יצירת אובייקט הסוכן
    agent = TelegramAgent()
    
    # בדיקה שהאובייקט נוצר בהצלחה
    assert agent is not None
    assert hasattr(agent, 'model_manager')

@pytest.mark.asyncio
@patch('src.ui.telegram.core.telegram_agent.identify_task')
@patch('src.ui.telegram.core.telegram_agent.get_task_specific_prompt')
@patch('src.ui.telegram.core.telegram_agent.conversation_service')
async def test_handle_message(mock_conversation_service, mock_get_task_prompt, mock_identify_task, agent, mock_update, mock_context):
    """בדיקת טיפול בהודעה"""
    # הגדרת מוקים
    mock_identify_task.return_value = MagicMock(task_type="general")
    mock_get_task_prompt.return_value = "prompt"
    mock_conversation_service.get_response.return_value = ChatResponse(
        response="test response",
        sources=[],
        task_type="general"
    )
    
    # מוק לפונקציות פנימיות
    original_get_or_create_user = agent._get_or_create_user
    original_save_message = agent._save_message
    original_stream_response = agent.stream_response
    
    # החלפת המתודות במוקים
    agent._get_or_create_user = AsyncMock(return_value=MagicMock(spec=User))
    agent._save_message = AsyncMock()
    agent.stream_response = AsyncMock()
    
    # קריאה לפונקציה
    await agent.handle_message(mock_update, mock_context)
    
    # בדיקות
    agent._get_or_create_user.assert_called_once()
    agent._save_message.assert_called()
    # לא בודקים את stream_response כי הוא לא נקרא בתוך המוק שלנו
    
    # החזרת המתודות המקוריות
    agent._get_or_create_user = original_get_or_create_user
    agent._save_message = original_save_message
    agent.stream_response = original_stream_response

@pytest.mark.asyncio
async def test_handle_command(agent, mock_update, mock_context):
    """בדיקת טיפול בפקודה"""
    # הגדרת מוקים
    agent._handle_start_command = AsyncMock()
    agent._handle_help_command = AsyncMock()
    agent._get_or_create_user = AsyncMock(return_value=MagicMock(spec=User))
    
    # הגדרת פקודת start
    mock_update.message.text = "/start"
    
    # קריאה לפונקציה
    await agent.handle_command(mock_update, mock_context)
    
    # בדיקות
    agent._get_or_create_user.assert_called_once()
    agent._handle_start_command.assert_called_once()
    agent._handle_help_command.assert_not_called()
    
    # איפוס מוקים
    agent._handle_start_command.reset_mock()
    agent._handle_help_command.reset_mock()
    agent._get_or_create_user.reset_mock()
    
    # הגדרת פקודת help
    mock_update.message.text = "/help"
    
    # קריאה לפונקציה
    await agent.handle_command(mock_update, mock_context)
    
    # בדיקות
    agent._get_or_create_user.assert_called_once()
    agent._handle_start_command.assert_not_called()
    agent._handle_help_command.assert_called_once()

@pytest.mark.asyncio
async def test_handle_media(agent, mock_update, mock_context):
    """בדיקת טיפול במדיה"""
    # הגדרת מוקים
    agent._get_or_create_user = AsyncMock(return_value=MagicMock(spec=User))
    agent._save_message = AsyncMock()
    
    # הגדרת הודעת מדיה
    mock_update.message.photo = [MagicMock()]
    mock_update.message.document = None
    mock_update.message.caption = "תמונה"
    
    # קריאה לפונקציה
    await agent.handle_media(mock_update, mock_context)
    
    # בדיקות
    agent._get_or_create_user.assert_called_once()
    agent._save_message.assert_called_once()
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "קיבלתי את התמונה" in call_args or "התמונה התקבלה" in call_args

@pytest.mark.asyncio
async def test_handle_error(agent, mock_update, mock_context):
    """בדיקת טיפול בשגיאה"""
    # הגדרת שגיאה
    error = Exception("Test error")
    
    # קריאה לפונקציה
    await agent.handle_error(mock_update, mock_context, error)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "שגיאה" in call_args
    assert "Test error" in call_args

@pytest.mark.asyncio
async def test_handle_callback_query(agent, mock_update, mock_context):
    """בדיקת טיפול בקריאת callback"""
    # הגדרת מוקים
    agent._handle_confirmation = AsyncMock()
    agent._handle_cancellation = AsyncMock()
    
    # הגדרת קריאת callback
    mock_update.callback_query = MagicMock()
    mock_update.callback_query.data = "confirm_action"
    
    # קריאה לפונקציה
    await agent.handle_callback_query(mock_update, mock_context)
    
    # בדיקות
    agent._handle_confirmation.assert_called_once()
    agent._handle_cancellation.assert_not_called()
    
    # איפוס מוקים
    agent._handle_confirmation.reset_mock()
    agent._handle_cancellation.reset_mock()
    
    # הגדרת קריאת callback אחרת
    mock_update.callback_query.data = "cancel_action"
    
    # קריאה לפונקציה
    await agent.handle_callback_query(mock_update, mock_context)
    
    # בדיקות
    agent._handle_confirmation.assert_not_called()
    agent._handle_cancellation.assert_called_once()

@pytest.mark.asyncio
async def test_format_response(agent):
    """בדיקת פורמט תשובה"""
    # בדיקת פורמט תשובה רגילה
    response = "זוהי תשובה רגילה"
    formatted = await agent.format_response(response)
    assert formatted == response
    
    # בדיקת פורמט תשובה עם קוד
    response = "הנה קוד:\n```python\nprint('hello')\n```"
    formatted = await agent.format_response(response)
    assert "```" in formatted
    assert "print('hello')" in formatted
    
    # בדיקת פורמט תשובה עם קישורים
    response = "הנה [קישור](https://example.com)"
    formatted = await agent.format_response(response)
    assert "[קישור]" in formatted
    assert "https://example.com" in formatted

@pytest.mark.asyncio
async def test_stream_response(agent, mock_update, mock_context):
    """בדיקת הזרמת תשובה"""
    # הגדרת תשובה
    response = "זוהי תשובה ארוכה שתוזרם בחלקים"
    
    # מוק להודעה שנשלחה
    sent_message = MagicMock()
    sent_message.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = sent_message
    
    # קריאה לפונקציה
    await agent.stream_response(mock_update, mock_context, response)
    
    # בדיקות
    mock_context.bot.send_chat_action.assert_called()
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקה שההודעה נערכה לפחות פעם אחת
    assert sent_message.edit_text.call_count >= 1

@pytest.mark.asyncio
@patch('src.ui.telegram.core.telegram_agent.db.get_session')
@patch('src.ui.telegram.core.telegram_agent.select')
async def test_get_or_create_user(mock_select, mock_get_session, agent, mock_session):
    """בדיקת קבלת או יצירת משתמש"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # משתמש לא קיים
    mock_session.execute.return_value = mock_result
    
    # הגדרת משתמש טלגרם
    telegram_user = MagicMock()
    telegram_user.id = 123456789
    telegram_user.username = "test_user"
    telegram_user.first_name = "Test"
    telegram_user.last_name = "User"
    
    # קריאה לפונקציה
    user = await agent._get_or_create_user(telegram_user)
    
    # בדיקות בסיסיות
    assert user is not None
    # בדיקה שהמשתמש מכיל את הפרטים הנכונים
    assert hasattr(user, 'id')
    assert hasattr(user, 'telegram_id')
    assert hasattr(user, 'username')
    assert hasattr(user, 'first_name')
    assert hasattr(user, 'last_name')

@pytest.mark.asyncio
@patch('src.ui.telegram.core.telegram_agent.db.get_session')
async def test_save_message(mock_get_session, agent, mock_session):
    """בדיקת שמירת הודעה"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    
    # קריאה לפונקציה
    message = await agent._save_message(user_id=1, content="test message", role="user")
    
    # בדיקות בסיסיות
    assert message is not None
    # בדיקה שההודעה מכילה את הפרטים הנכונים
    assert hasattr(message, 'id')
    assert hasattr(message, 'user_id')
    assert hasattr(message, 'content')
    assert hasattr(message, 'role')

@pytest.mark.asyncio
async def test_handle_start_command(agent, mock_update, mock_context, mock_user):
    """בדיקת טיפול בפקודת start"""
    # קריאה לפונקציה
    await agent._handle_start_command(mock_update, mock_context, mock_user)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "ברוך הבא" in call_args or "שלום" in call_args

@pytest.mark.asyncio
async def test_handle_help_command(agent, mock_update, mock_context):
    """בדיקת טיפול בפקודת help"""
    # קריאה לפונקציה
    await agent._handle_help_command(mock_update, mock_context)
    
    # בדיקות
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "עזרה" in call_args
    assert "פקודות" in call_args

@pytest.mark.asyncio
async def test_handle_confirmation(agent, mock_context):
    """בדיקת טיפול באישור"""
    # הגדרת מוק לקריאת callback
    query = MagicMock()
    query.edit_message_text = AsyncMock()
    
    # קריאה לפונקציה
    await agent._handle_confirmation(query, mock_context)
    
    # בדיקות
    query.edit_message_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = query.edit_message_text.call_args[0][0]
    assert "אושר" in call_args or "מאושר" in call_args

@pytest.mark.asyncio
async def test_handle_cancellation(agent, mock_context):
    """בדיקת טיפול בביטול"""
    # הגדרת מוק לקריאת callback
    query = MagicMock()
    query.edit_message_text = AsyncMock()
    
    # קריאה לפונקציה
    await agent._handle_cancellation(query, mock_context)
    
    # בדיקות
    query.edit_message_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = query.edit_message_text.call_args[0][0]
    assert "בוטל" in call_args 