"""
בדיקות יחידה למודולי הבוט
"""
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
import pytz
import json

from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes

from src.database.models import (
    User, 
    WooCommerceStore,
    WooCommerceProduct,
    WooCommerceOrder,
    WooCommerceCustomer,
    WooCommerceOrderItem
)
from src.bots.telegram_bot_core import TelegramBot
from src.bots.telegram_bot_handlers import TelegramBotHandlers
from src.bots.telegram_bot_conversations import TelegramBotConversations
from src.bots.telegram_bot_documents import TelegramBotDocuments
from src.bots.telegram_bot_products import TelegramBotProducts
from src.bots.telegram_bot_orders import TelegramBotOrders
from src.bots.telegram_bot_store import TelegramBotStore
from src.bots.telegram_bot_customers import TelegramBotCustomers
from src.bots.telegram_bot_payments import TelegramBotPayments
from src.bots.telegram_bot_shipping import TelegramBotShipping
from src.bots.telegram_bot_analytics import TelegramBotAnalytics
from src.bots.telegram_bot_notifications import TelegramBotNotifications
from src.bots.telegram_bot_settings import TelegramBotSettings
from src.bots.telegram_bot_scheduler import TelegramBotScheduler
from src.bots.telegram_bot_logger import TelegramBotLogger
from src.bots.telegram_bot_api import TelegramBotAPI
from src.bots.telegram_bot_utils import (
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message,
    format_price,
    format_number,
    format_date,
    sanitize_filename,
    truncate_text,
    escape_markdown,
    create_progress_bar,
    validate_email,
    validate_phone,
    validate_url
)

# הגדרת פיקסטורות
@pytest.fixture
def telegram_user():
    """פיקסטורה למשתמש טלגרם"""
    return TelegramUser(id=123, is_bot=False, first_name='Test')

@pytest.fixture
def telegram_chat():
    """פיקסטורה לצ'אט טלגרם"""
    return Chat(id=123, type='private')

@pytest.fixture
def telegram_message(telegram_user, telegram_chat):
    """פיקסטורה להודעת טלגרם"""
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=telegram_chat,
        from_user=telegram_user,
        text='/start'
    )
    # הגדרת בוט מדומה
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    message._bot = bot
    return message

@pytest.fixture
def telegram_update(telegram_message):
    """פיקסטורה ליצירת אובייקט Update מדומה"""
    return Update(update_id=1, message=telegram_message)

@pytest.fixture
def telegram_context():
    """פיקסטורה ליצירת אובייקט Context מדומה"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture
def telegram_bot():
    """פיקסטורה לבוט טלגרם"""
    bot = TelegramBot()
    return bot

@pytest.fixture
def mock_session():
    """פיקסטורה ליצירת סשן מדומה"""
    session = AsyncMock()
    session.execute.return_value.scalar.return_value = None
    return session

@pytest.fixture
def mock_bot():
    """פיקסטורה ליצירת בוט מדומה"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

# בדיקות לפונקציות עזר
@pytest.mark.parametrize("text,expected", [
    ("test", "✅ *הצלחה*\ntest"),
    ("", "✅ *הצלחה*\n"),
])
def test_format_success_message(text, expected):
    """בדיקת פונקציית עיצוב הודעת הצלחה"""
    assert format_success_message(text) == expected

@pytest.mark.parametrize("text,expected", [
    ("test", "❌ *שגיאה*\ntest"),
    ("", "❌ *שגיאה*\n"),
])
def test_format_error_message(text, expected):
    """בדיקת פונקציית עיצוב הודעת שגיאה"""
    assert format_error_message(text) == expected

@pytest.mark.parametrize("text,expected", [
    ("test", "⚠️ *אזהרה*\ntest"),
    ("", "⚠️ *אזהרה*\n"),
])
def test_format_warning_message(text, expected):
    """בדיקת פונקציית עיצוב הודעת אזהרה"""
    assert format_warning_message(text) == expected

@pytest.mark.parametrize("text,expected", [
    ("test", "ℹ️ *מידע*\ntest"),
    ("", "ℹ️ *מידע*\n"),
])
def test_format_info_message(text, expected):
    """בדיקת פונקציית עיצוב הודעת מידע"""
    assert format_info_message(text) == expected

@pytest.mark.parametrize("price,currency,expected", [
    (1234.56, '₪', '1,234.56 ₪'),
    (1234.56, '$', '1,234.56 $'),
    (0, '₪', '0.00 ₪'),
])
def test_format_price(price, currency, expected):
    """בדיקת פונקציית עיצוב מחיר"""
    assert format_price(price, currency) == expected

@pytest.mark.parametrize("number,expected", [
    (1234567, '1,234,567'),
    (0, '0'),
    (-1234, '-1,234'),
])
def test_format_number(number, expected):
    """בדיקת פונקציית עיצוב מספר"""
    assert format_number(number) == expected

@pytest.mark.parametrize("email,expected", [
    ('test@example.com', True),
    ('invalid-email', False),
    ('test@test', False),
])
def test_validate_email(email, expected):
    """בדיקת פונקציית בדיקת אימייל"""
    assert validate_email(email) == expected

@pytest.mark.parametrize("phone,expected", [
    ('0501234567', True),
    ('+972501234567', True),
    ('123456', False),
])
def test_validate_phone(phone, expected):
    """בדיקת פונקציית בדיקת טלפון"""
    assert validate_phone(phone) == expected

@pytest.mark.parametrize("url,expected", [
    ('https://example.com', True),
    ('http://test.com', True),
    ('invalid-url', False),
])
def test_validate_url(url, expected):
    """בדיקת פונקציית בדיקת URL"""
    assert validate_url(url) == expected

@pytest.mark.parametrize("filename,expected", [
    ('file:name*.txt', 'filename.txt'),
    ('test/file.txt', 'testfile.txt'),
])
def test_sanitize_filename(filename, expected):
    """בדיקת פונקציית ניקוי שם קובץ"""
    assert sanitize_filename(filename) == expected

@pytest.mark.parametrize("text,max_length,suffix,expected", [
    ('a' * 200, 100, '...', 'a' * 97 + '...'),
    ('short text', 100, '...', 'short text'),
])
def test_truncate_text(text, max_length, suffix, expected):
    """בדיקת פונקציית קיצור טקסט"""
    assert truncate_text(text, max_length, suffix) == expected

@pytest.mark.parametrize("text,expected", [
    ('*bold* _italic_', '\\*bold\\* \\_italic\\_'),
    ('normal text', 'normal text'),
])
def test_escape_markdown(text, expected):
    """בדיקת פונקציית הסרת תווים מיוחדים"""
    assert escape_markdown(text) == expected

@pytest.mark.parametrize("current,total,style,expected", [
    (1, 3, 'default', '🔵⚪⚪'),
    (2, 3, 'default', '✅🔵⚪'),
    (3, 3, 'default', '✅✅🔵'),
])
def test_create_progress_bar(current, total, style, expected):
    """בדיקת פונקציית יצירת סרגל התקדמות"""
    assert create_progress_bar(current, total, style) == expected

# בדיקות למחלקות הבוט
@pytest.mark.asyncio
async def test_telegram_bot_init(telegram_bot):
    """בדיקת אתחול הבוט"""
    assert telegram_bot is not None
    assert isinstance(telegram_bot, TelegramBot)

@pytest.mark.asyncio
async def test_telegram_bot_handlers_start(telegram_update, telegram_context, mock_session):
    """בדיקת פקודת start"""
    mock_user = MagicMock()
    mock_user.first_name = "Test"
    
    with patch('src.database.operations.get_user_by_telegram_id') as mock_get_user, \
         patch('src.database.db.get_session', return_value=mock_session):
        # הגדרת ערך החזרה כמשתמש מדומה
        mock_get_user.return_value = mock_user
        handlers = TelegramBotHandlers(MagicMock())
        result = await handlers.start(telegram_update, telegram_context)
        assert result is True

@pytest.mark.asyncio
async def test_telegram_bot_handlers_help(telegram_update, telegram_context, mock_bot):
    """בדיקת פקודת help"""
    mock_log = AsyncMock()
    mock_message = AsyncMock()
    mock_message.text = "/help"
    mock_message._bot = mock_bot
    mock_message.reply_text = AsyncMock()
    mock_message.chat = telegram_update.message.chat
    mock_message.from_user = telegram_update.message.from_user
    mock_message.message_id = 1
    mock_message.date = datetime.now()
    mock_message.effective_user = telegram_update.message.from_user
    
    # Create a new Update object with our mock message
    new_update = Update(update_id=1)
    new_update._unfreeze()
    new_update.message = mock_message
    new_update._freeze()
    
    with patch('src.utils.logger.log_telegram_message', mock_log), \
         patch('src.utils.logger.setup_logger', return_value=MagicMock()):
        handlers = TelegramBotHandlers(MagicMock())
        result = await handlers.help(new_update, telegram_context)
        assert result is True
        assert mock_log.call_count == 1
        mock_message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_telegram_bot_conversations_cancel(telegram_update, telegram_context, mock_bot):
    """בדיקת ביטול שיחה"""
    telegram_update.message._bot = mock_bot
    conversations = TelegramBotConversations(MagicMock())
    result = await conversations.cancel_conversation(telegram_update, telegram_context)
    assert result is not None

# בדיקות למחלקת הלוגר
@pytest.mark.asyncio
async def test_telegram_bot_logger_init():
    """בדיקת אתחול הלוגר"""
    logger = TelegramBotLogger()
    assert logger is not None
    assert isinstance(logger.logger, logging.Logger)

@pytest.mark.asyncio
async def test_telegram_bot_logger_methods():
    """בדיקת מתודות הלוגר"""
    with patch('logfire.log') as mock_log:
        logger = TelegramBotLogger()
        
        # בדיקת מתודות הלוגר
        logger.info("Test info message")
        mock_log.assert_called_with(level="info", message="Test info message")
        
        logger.warning("Test warning message")
        mock_log.assert_called_with(level="warning", message="Test warning message")
        
        logger.error("Test error message")
        mock_log.assert_called_with(level="error", message="Test error message")
        
        logger.debug("Test debug message")
        mock_log.assert_called_with(level="debug", message="Test debug message")
        
        logger.critical("Test critical message")
        mock_log.assert_called_with(level="critical", message="Test critical message")
        
        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.exception("Test exception message", exc_info=e)
            mock_log.assert_called_with(level="error", message="Test exception message", exc_info=e)

# בדיקות למחלקת ה-API
@pytest.mark.asyncio
async def test_telegram_bot_api_init():
    """בדיקת אתחול ה-API"""
    api = TelegramBotAPI('https://api.example.com')
    assert api is not None
    assert api.base_url == 'https://api.example.com'

@pytest.mark.asyncio
async def test_telegram_bot_api_methods():
    """בדיקת מתודות ה-API"""
    api = TelegramBotAPI('https://api.example.com')
    
    # Mock the session's request methods
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={'status': 'success'})
    mock_response.raise_for_status = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()

    mock_session = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.get.return_value = mock_response
    mock_session.post = AsyncMock()
    mock_session.post.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()

    api.session = mock_session

    # Test GET request
    response = await api.get('/test')
    assert response == {'status': 'success'}
    mock_session.get.assert_called_once()

    # Test POST request
    response = await api.post('/test', {'data': 'test'})
    assert response == {'status': 'success'}
    mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_telegram_bot_api_error_handling():
    """בדיקת טיפול בשגיאות ב-API"""
    async with TelegramBotAPI('https://api.example.com') as api:
        # Mock session to raise an exception
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock(side_effect=Exception("Test error"))
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        mock_session.get.return_value = mock_response
        
        api.session = mock_session
        
        # Test error handling
        with pytest.raises(Exception):
            await api.get('/test')

if __name__ == '__main__':
    pytest.main(['-v', '--cov=src/bots', '--cov-report=term-missing']) 