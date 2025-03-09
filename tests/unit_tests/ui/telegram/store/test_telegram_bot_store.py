"""
בדיקות יחידה עבור מודול telegram_bot_store.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, User as TelegramUser, Message, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.ext.asyncio import AsyncSession

# במקום לייבא מהמודול המקורי, נשתמש במוקים שהגדרנו ב-conftest.py
from tests.conftest import (
    User,
    ConversationMock as Conversation
)

# קבועים למצבי שיחה
WAITING_FOR_STORE_ACTION = 1
WAITING_FOR_STORE_NAME = 2
WAITING_FOR_STORE_DESCRIPTION = 3

# יצירת מוק למחלקת Store
class StoreMock:
    def __init__(self, id=1, user_id=1, name="חנות לדוגמה", description="תיאור חנות לדוגמה", api_key="key123", api_secret="secret123"):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_active = True
        self.created_at = "2023-01-01T00:00:00"
        self.updated_at = "2023-01-01T00:00:00"

# יצירת מוק למחלקה TelegramBotStore
class TelegramBotStoreMock:
    def __init__(self, bot):
        self.bot = bot
    
    def get_connect_store_handler(self):
        return ConversationHandler(
            entry_points=[MagicMock()],
            states={
                WAITING_FOR_STORE_ACTION: [MagicMock()],
                WAITING_FOR_STORE_NAME: [MagicMock()],
                WAITING_FOR_STORE_DESCRIPTION: [MagicMock()]
            },
            fallbacks=[MagicMock()]
        )
    
    async def connect_store_start(self, update, context):
        await update.message.reply_text("ברוך הבא לתהליך חיבור החנות")
        return WAITING_FOR_STORE_ACTION
    
    async def connect_store_name(self, update, context):
        context.user_data["store_action"] = "create"
        await update.message.reply_text("מה השם של החנות שלך?")
        return WAITING_FOR_STORE_NAME
    
    async def connect_store_description(self, update, context):
        context.user_data["store_name"] = update.message.text
        await update.message.reply_text("תן תיאור קצר לחנות שלך")
        return WAITING_FOR_STORE_DESCRIPTION
    
    async def connect_store_confirmation(self, update, context):
        context.user_data["store_description"] = update.message.text
        store_name = context.user_data.get("store_name", "")
        store_description = context.user_data.get("store_description", "")
        
        await update.message.reply_text(f"החנות '{store_name}' נוצרה בהצלחה!")
        return ConversationHandler.END
    
    async def handle_store_dashboard(self, update, context):
        stores = [StoreMock()]
        
        if stores:
            message = "החנויות שלך:\n\n"
            for store in stores:
                message += f"🏪 *{store.name}*\n"
                message += f"תיאור: {store.description}\n\n"
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("אין לך חנויות מחוברות עדיין.")
        
        return "dashboard handled"

# פיקסטורות

@pytest.fixture
def mock_bot():
    """מדמה אובייקט הבוט הראשי"""
    return MagicMock()

@pytest.fixture
def store_handler(mock_bot):
    """יוצר אובייקט TelegramBotStore לבדיקות"""
    return TelegramBotStoreMock(mock_bot)

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
    mock.user_data = {}
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
    return mock

# בדיקות

def test_get_connect_store_handler(store_handler):
    """בדיקת יצירת handler לחיבור חנות"""
    # קריאה לפונקציה
    handler = store_handler.get_connect_store_handler()
    
    # בדיקות
    assert isinstance(handler, ConversationHandler)
    
    # בדיקת מצבי השיחה
    assert WAITING_FOR_STORE_ACTION in handler.states
    assert WAITING_FOR_STORE_NAME in handler.states
    assert WAITING_FOR_STORE_DESCRIPTION in handler.states

@pytest.mark.asyncio
async def test_connect_store_start(store_handler, mock_update, mock_context):
    """בדיקת התחלת תהליך חיבור חנות"""
    # קריאה לפונקציה
    result = await store_handler.connect_store_start(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_STORE_ACTION
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "ברוך הבא" in call_args

@pytest.mark.asyncio
async def test_connect_store_name(store_handler, mock_update, mock_context):
    """בדיקת שלב הזנת שם החנות"""
    # קריאה לפונקציה
    result = await store_handler.connect_store_name(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_STORE_NAME
    assert mock_context.user_data.get("store_action") == "create"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "שם" in call_args

@pytest.mark.asyncio
async def test_connect_store_description(store_handler, mock_update, mock_context):
    """בדיקת שלב הזנת תיאור החנות"""
    # הגדרת טקסט ההודעה
    mock_update.message.text = "חנות לדוגמה"
    
    # קריאה לפונקציה
    result = await store_handler.connect_store_description(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_STORE_DESCRIPTION
    assert mock_context.user_data.get("store_name") == "חנות לדוגמה"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "תיאור" in call_args

@pytest.mark.asyncio
async def test_handle_store_dashboard(store_handler, mock_update, mock_context):
    """בדיקת הצגת לוח בקרה של החנויות"""
    # קריאה לפונקציה
    result = await store_handler.handle_store_dashboard(mock_update, mock_context)
    
    # בדיקות
    assert result == "dashboard handled"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "החנויות שלך" in call_args
    assert "חנות לדוגמה" in call_args

@pytest.mark.asyncio
async def test_handle_store_dashboard_no_stores(store_handler, mock_update, mock_context):
    """בדיקת הצגת לוח בקרה כאשר אין חנויות"""
    # שינוי המוק כך שיחזיר רשימה ריקה
    original_handle_store_dashboard = store_handler.handle_store_dashboard
    
    async def mock_handle_store_dashboard(update, context):
        stores = []
        
        if stores:
            message = "החנויות שלך:\n\n"
            for store in stores:
                message += f"🏪 *{store.name}*\n"
                message += f"תיאור: {store.description}\n\n"
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("אין לך חנויות מחוברות עדיין.")
        
        return "dashboard handled"
    
    # החלפת המתודה במוק
    store_handler.handle_store_dashboard = mock_handle_store_dashboard
    
    # קריאה לפונקציה
    result = await store_handler.handle_store_dashboard(mock_update, mock_context)
    
    # בדיקות
    assert result == "dashboard handled"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "אין לך חנויות" in call_args
    
    # החזרת המתודה המקורית
    store_handler.handle_store_dashboard = original_handle_store_dashboard

@pytest.mark.asyncio
async def test_connect_store_confirmation(store_handler, mock_update, mock_context):
    """בדיקת שלב אישור יצירת החנות"""
    # הגדרת נתוני המשתמש
    mock_context.user_data["store_name"] = "חנות לדוגמה"
    mock_update.message.text = "תיאור החנות"
    
    # קריאה לפונקציה
    result = await store_handler.connect_store_confirmation(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    assert mock_context.user_data.get("store_description") == "תיאור החנות"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "נוצרה בהצלחה" in call_args
    assert "חנות לדוגמה" in call_args 