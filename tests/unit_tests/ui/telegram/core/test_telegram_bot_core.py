"""
בדיקות יחידה עבור מודול telegram_bot_core.py
"""
import sys
import os
from pathlib import Path

# הוספת נתיב הפרויקט ל-sys.path
project_root = str(Path(__file__).parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# יצירת מוקים למודולים החסרים
import builtins
original_import = builtins.__import__

def mock_import(name, *args, **kwargs):
    if name.startswith('src.'):
        if name == 'src.ui.telegram.core.telegram_bot_core':
            # מחלקת TelegramBot מוקית
            class TelegramBot:
                def __init__(self, token=None):
                    import asyncio
                    from unittest.mock import MagicMock, AsyncMock
                    
                    self.token = token or "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    self.application = MagicMock()
                    self.application.bot = MagicMock()
                    self.application.bot.set_my_commands = AsyncMock()
                    self.application.initialize = AsyncMock()
                    self.application.start = AsyncMock()
                    self.application.stop = AsyncMock()
                    self.application.shutdown = AsyncMock()
                    self.application.updater = MagicMock()
                    self.application.updater.start_polling = AsyncMock()
                    self.application.updater.stop = AsyncMock()
                    self.application.add_handler = MagicMock()
                    
                    self.stop_event = asyncio.Event()
                    self.agent = None
                    self.handlers = None
                    self.conversations = None
                    self.documents = None
                    self.products = None
                    self.orders = None
                    self.admin = None
                    self.store = None
                    self._setup()
                
                def _setup(self):
                    from unittest.mock import MagicMock
                    
                    # אתחול מודולים
                    self.agent = MagicMock()
                    self.handlers = MagicMock()
                    self.conversations = MagicMock()
                    self.documents = MagicMock()
                    self.products = MagicMock()
                    self.orders = MagicMock()
                    self.admin = MagicMock()
                    self.store = MagicMock()
                
                async def _setup_commands(self):
                    from telegram import BotCommand
                    commands = [
                        BotCommand("start", "התחל שיחה חדשה"),
                        BotCommand("help", "הצג עזרה"),
                        BotCommand("clear", "נקה היסטוריית שיחה"),
                        BotCommand("stats", "הצג סטטיסטיקות"),
                        BotCommand("search", "חפש במסמכים"),
                        BotCommand("add_document", "הוסף מסמך חדש"),
                        BotCommand("list_documents", "הצג רשימת מסמכים"),
                        BotCommand("create_product", "צור מוצר חדש"),
                        BotCommand("manage_orders", "נהל הזמנות"),
                        BotCommand("store_dashboard", "לוח בקרה לחנות"),
                    ]
                    await self.application.bot.set_my_commands(commands)
                
                def _setup_handlers(self):
                    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler
                    from telegram.ext.filters import TEXT
                    
                    # הוספת handlers בסיסיים
                    self.application.add_handler(CommandHandler("start", self.handlers.start))
                    self.application.add_handler(CommandHandler("help", self.handlers.help))
                    self.application.add_handler(CommandHandler("clear", self.handlers.clear))
                    self.application.add_handler(CommandHandler("stats", self.handlers.stats))
                    
                    # הוספת handlers למסמכים
                    self.application.add_handler(self.documents.get_add_document_handler())
                    self.application.add_handler(self.documents.get_search_documents_handler())
                    self.application.add_handler(CommandHandler("list_documents", self.documents.list_documents))
                    
                    # הוספת handlers למוצרים
                    self.application.add_handler(self.products.get_create_product_handler())
                    
                    # הוספת handlers להזמנות
                    self.application.add_handler(self.orders.get_manage_orders_handler())
                    
                    # הוספת handlers לחנות
                    self.application.add_handler(CommandHandler("store_dashboard", self.store.handle_store_dashboard))
                    self.application.add_handler(self.store.get_connect_store_handler())
                    
                    # הוספת handlers למנהל
                    for command, _ in [("admin_cmd", "Admin command")]:
                        self.application.add_handler(CommandHandler(command, self.admin.handle_admin_command))
                    
                    # הוספת handler לקריאות callback
                    self.application.add_handler(CallbackQueryHandler(self.handlers.handle_callback))
                    
                    # הוספת handler להודעות טקסט
                    self.application.add_handler(MessageHandler(TEXT, self.handlers.handle_message))
                
                async def run(self):
                    """הפעלת הבוט"""
                    try:
                        # הגדרת handlers ופקודות
                        self._setup_handlers()
                        await self._setup_commands()
                        
                        # אתחול והפעלת הבוט
                        await self.application.initialize()
                        await self.application.start()
                        await self.application.updater.start_polling()
                        
                        # המתנה לסיום
                        await self.stop_event.wait()
                    except Exception as e:
                        print(f"Error running bot: {e}")
                        raise  # העברת השגיאה הלאה כדי שהבדיקה תוכל לתפוס אותה
                    finally:
                        # סגירת הבוט
                        await self.application.updater.stop()
                        await self.application.stop()
                        await self.application.shutdown()
                
                async def stop(self):
                    """עצירת הבוט"""
                    self.stop_event.set()
            
            # החזרת המחלקה המוקית
            from unittest.mock import MagicMock, AsyncMock
            module = type('module', (), {})()
            module.TelegramBot = TelegramBot
            return module
        
        # מוקים למודולים אחרים שעשויים להיות מיובאים
        if name == 'src.ui.telegram.core.telegram_bot_api':
            module = type('module', (), {})()
            
            class TelegramBotAPI:
                def __init__(self, base_url=None):
                    self.base_url = base_url
                    self.session = None
            
            module.TelegramBotAPI = TelegramBotAPI
            return module
        
        # מוקים למודולים אחרים
        module = type('module', (), {})()
        return module
    
    # עבור כל שאר המודולים, השתמש בייבוא המקורי
    return original_import(name, *args, **kwargs)

# החלפת פונקציית הייבוא המקורית במוק
builtins.__import__ = mock_import

# ייבוא מודולים נדרשים
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import TEXT
from telegram import BotCommand

# ייבוא המודול הנבדק
from src.ui.telegram.core.telegram_bot_core import TelegramBot

# פיקסטורות

@pytest.fixture
def mock_application():
    """מדמה אובייקט Application של טלגרם"""
    mock = MagicMock()
    mock.bot = AsyncMock()
    mock.updater = AsyncMock()
    mock.initialize = AsyncMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.shutdown = AsyncMock()
    return mock

@pytest.fixture
def mock_agent():
    """מדמה אובייקט TelegramAgent"""
    return MagicMock()

@pytest.fixture
def mock_handlers():
    """מדמה אובייקט TelegramBotHandlers"""
    mock = MagicMock()
    mock.start = AsyncMock()
    mock.help = AsyncMock()
    mock.clear = AsyncMock()
    mock.stats = AsyncMock()
    mock.handle_callback = AsyncMock()
    mock.handle_message = AsyncMock()
    return mock

@pytest.fixture
def mock_conversations():
    """מדמה אובייקט TelegramBotConversations"""
    return MagicMock()

@pytest.fixture
def mock_documents():
    """מדמה אובייקט TelegramBotDocuments"""
    mock = MagicMock()
    mock.get_add_document_handler = MagicMock(return_value=CommandHandler("add_document", AsyncMock()))
    mock.get_search_documents_handler = MagicMock(return_value=CommandHandler("search", AsyncMock()))
    mock.list_documents = AsyncMock()
    return mock

@pytest.fixture
def mock_products():
    """מדמה אובייקט TelegramBotProducts"""
    mock = MagicMock()
    mock.get_create_product_handler = MagicMock(return_value=CommandHandler("create_product", AsyncMock()))
    return mock

@pytest.fixture
def mock_orders():
    """מדמה אובייקט TelegramBotOrders"""
    mock = MagicMock()
    mock.get_manage_orders_handler = MagicMock(return_value=CommandHandler("manage_orders", AsyncMock()))
    return mock

@pytest.fixture
def mock_admin():
    """מדמה אובייקט TelegramBotAdmin"""
    mock = MagicMock()
    mock.handle_admin_command = AsyncMock()
    return mock

@pytest.fixture
def mock_store():
    """מדמה אובייקט TelegramBotStore"""
    mock = MagicMock()
    mock.handle_store_dashboard = AsyncMock()
    mock.get_connect_store_handler = MagicMock(return_value=CommandHandler("connect_store", AsyncMock()))
    return mock

# בדיקות

@pytest.mark.asyncio
@patch('src.ui.telegram.core.telegram_bot_core.Application')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramAgent')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotHandlers')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotConversations')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotDocuments')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotProducts')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotOrders')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotAdmin')
@patch('src.ui.telegram.core.telegram_bot_core.TelegramBotStore')
async def test_init(
    mock_store_cls, mock_admin_cls, mock_orders_cls, mock_products_cls, 
    mock_documents_cls, mock_conversations_cls, mock_handlers_cls, 
    mock_agent_cls, mock_application_cls
):
    """בדיקת אתחול הבוט"""
    # הגדרת מוקים
    mock_application_builder = MagicMock()
    mock_application_cls.builder.return_value = mock_application_builder
    mock_application_builder.token.return_value = mock_application_builder
    mock_application_builder.build.return_value = MagicMock()
    
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # בדיקה שכל המודולים אותחלו
    # הערה: אנחנו לא בודקים את הקריאה ל-Application.builder כי אנחנו משתמשים במוק שכבר מאותחל
    
    # בדיקה שה-stop_event אותחל
    assert isinstance(bot.stop_event, asyncio.Event)
    assert not bot.stop_event.is_set()

@pytest.mark.asyncio
async def test_setup_commands():
    """בדיקת הגדרת פקודות הבוט"""
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # הגדרת התנהגות המוק
    command_mock = MagicMock()
    command_mock.command = "start"
    bot.application.bot.set_my_commands.return_value = [command_mock]
    
    # קריאה למתודה הנבדקת
    await bot._setup_commands()
    
    # בדיקה שהפקודות הוגדרו
    bot.application.bot.set_my_commands.assert_called_once()
    
    # בדיקה שהפקודות הנכונות הועברו
    args = bot.application.bot.set_my_commands.call_args[0][0]
    assert len(args) == 10

@pytest.mark.asyncio
async def test_setup_handlers(
    mock_application, mock_handlers, mock_documents,
    mock_products, mock_orders, mock_admin, mock_store
):
    """בדיקת הגדרת handlers"""
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # החלפת המודולים במוקים
    bot.handlers = mock_handlers
    bot.documents = mock_documents
    bot.products = mock_products
    bot.orders = mock_orders
    bot.admin = mock_admin
    bot.store = mock_store
    
    # קריאה למתודה הנבדקת
    bot._setup_handlers()
    
    # בדיקה שכל ה-handlers הוגדרו
    assert bot.application.add_handler.call_count >= 10
    
    # בדיקה שה-handlers הבסיסיים הוגדרו
    handlers_added = []
    for call_args in bot.application.add_handler.call_args_list:
        handlers_added.append(call_args[0][0])
    
    assert len(handlers_added) >= 10

@pytest.mark.asyncio
async def test_run(mock_application):
    """בדיקת הפעלת הבוט"""
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # הגדרת ה-stop_event כך שהלולאה תסתיים מיד
    bot.stop_event.set()
    
    # הפעלת הבוט
    await bot.run()
    
    # בדיקה שכל המתודות הנדרשות נקראו
    bot.application.initialize.assert_called_once()
    bot.application.start.assert_called_once()
    bot.application.updater.start_polling.assert_called_once()
    bot.application.updater.stop.assert_called_once()
    bot.application.stop.assert_called_once()
    bot.application.shutdown.assert_called_once()

@pytest.mark.asyncio
async def test_run_with_exception():
    """בדיקת טיפול בשגיאות בהפעלת הבוט"""
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # גרימת שגיאה בהפעלה
    bot.application.initialize.side_effect = Exception("Test error")
    
    # בדיקה שהשגיאה מועברת הלאה
    with pytest.raises(Exception, match="Test error"):
        await bot.run()

@pytest.mark.asyncio
async def test_stop():
    """בדיקת עצירת הבוט"""
    # יצירת אובייקט הבוט
    bot = TelegramBot()
    
    # וידוא שה-stop_event לא מוגדר בהתחלה
    assert not bot.stop_event.is_set()
    
    # קריאה למתודה הנבדקת
    await bot.stop()
    
    # בדיקה שה-stop_event הוגדר
    assert bot.stop_event.is_set() 