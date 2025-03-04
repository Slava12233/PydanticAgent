import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    Defaults,
    ConversationHandler,
    CallbackQueryHandler
)
from telegram.constants import ParseMode

# Import from our module structure
from src.core.config import TELEGRAM_TOKEN, ALLOWED_COMMANDS, ADMIN_COMMANDS, ADMIN_USER_ID, LOGFIRE_API_KEY, LOGFIRE_PROJECT
from src.utils.logger import setup_logger, log_exception, log_database_operation, log_telegram_message

# Import handlers
from .telegram_bot_handlers import TelegramBotHandlers
from .telegram_bot_conversations import TelegramBotConversations
from .telegram_bot_documents import TelegramBotDocuments
from .telegram_bot_products import TelegramBotProducts
from .telegram_bot_orders import TelegramBotOrders
from .telegram_bot_admin import TelegramBotAdmin
from .telegram_bot_store import TelegramBotStore

# Configure logging
logger = setup_logger('telegram_bot')

# Configure and initialize Logfire for monitoring
import logfire
try:
    logfire.configure(
        token=LOGFIRE_API_KEY,
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
except (AttributeError, ImportError):
    logfire.configure(token=LOGFIRE_API_KEY)
logfire.instrument_httpx(capture_headers=True, capture_body=False)

class TelegramBot:
    """
    המחלקה הראשית של הבוט טלגרם.
    מנהלת את כל הפונקציונליות של הבוט דרך מודולים שונים.
    """
    
    def __init__(self):
        """אתחול הבוט והמודולים השונים"""
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # אתחול המודולים
        self.handlers = TelegramBotHandlers(self)
        self.conversations = TelegramBotConversations(self)
        self.documents = TelegramBotDocuments(self)
        self.products = TelegramBotProducts(self)
        self.orders = TelegramBotOrders(self)
        self.admin = TelegramBotAdmin(self)
        self.store = TelegramBotStore(self)
        
        # הגדרת הפקודות
        self._setup_commands()
        
        # הגדרת ה-handlers
        self._setup_handlers()
        
        logger.info("TelegramBot initialized successfully")
    
    def _setup_commands(self):
        """הגדרת הפקודות הזמינות בבוט"""
        commands = [
            BotCommand("start", "התחל שיחה עם הבוט"),
            BotCommand("help", "הצג עזרה ורשימת פקודות"),
            BotCommand("clear", "נקה את היסטוריית השיחה"),
            BotCommand("stats", "הצג סטטיסטיקות"),
            BotCommand("search", "חפש במאגר הידע"),
            BotCommand("add_document", "הוסף מסמך למאגר הידע"),
            BotCommand("list_documents", "הצג רשימת מסמכים"),
            BotCommand("create_product", "צור מוצר חדש"),
            BotCommand("manage_orders", "נהל הזמנות"),
            BotCommand("store_dashboard", "לוח בקרה של החנות"),
        ]
        
        self.application.bot.set_my_commands(commands)
    
    def _setup_handlers(self):
        """הגדרת כל ה-handlers של הבוט"""
        # Basic command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help))
        self.application.add_handler(CommandHandler("clear", self.handlers.clear))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats))
        
        # Document handlers
        self.application.add_handler(self.documents.get_add_document_handler())
        self.application.add_handler(self.documents.get_search_documents_handler())
        self.application.add_handler(CommandHandler("list_documents", self.documents.list_documents))
        
        # Product handlers
        self.application.add_handler(self.products.get_create_product_handler())
        
        # Order handlers
        self.application.add_handler(self.orders.get_manage_orders_handler())
        
        # Store handlers
        self.application.add_handler(CommandHandler("store_dashboard", self.store.handle_store_dashboard))
        self.application.add_handler(self.store.get_connect_store_handler())
        
        # Admin handlers
        for command_name, _ in ADMIN_COMMANDS:
            self.application.add_handler(CommandHandler(command_name, self.admin.handle_admin_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handlers.handle_callback))
        
        # Message handler - should be last
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))
        
        logger.info("All handlers set up successfully")
    
    async def run(self):
        """הפעלת הבוט"""
        logger.info("Starting the bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
        logger.info("Bot stopped") 