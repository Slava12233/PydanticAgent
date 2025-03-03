import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
from datetime import datetime, timezone, timedelta
import traceback
import asyncio
import time
import re
import json
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Message
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
from telegram.error import TelegramError
import httpx

# Import from our module structure
from src.core.config import TELEGRAM_TOKEN, ALLOWED_COMMANDS, ADMIN_COMMANDS, ADMIN_USER_ID, LOGFIRE_API_KEY, LOGFIRE_PROJECT
# Import the new database module
from src.database import db
from src.database.models import User, UserRole, Conversation, Message, WooCommerceStore
from src.database.operations import get_user_by_telegram_id
from src.database.rag_utils import add_document_from_file, search_documents
from src.agents.telegram_agent import TelegramAgent
from src.utils.logger import setup_logger, log_exception, log_database_operation, log_telegram_message
from src.handlers.admin_handler import (
    handle_admin_command, handle_admin_users, handle_admin_stats, 
    handle_admin_docs, handle_admin_models, handle_admin_config, 
    handle_admin_notify, handle_admin_callback, process_admin_action
)
from src.handlers.store_handler import (
    handle_store_dashboard, handle_connect_store_start, handle_store_url,
    handle_consumer_key, handle_consumer_secret, handle_confirmation,
    handle_store_callback, handle_store_stats, handle_store_orders,
    handle_store_products, handle_store_customers, handle_store_inventory
)
from src.tools.woocommerce_templates import get_template, get_all_template_keys

# פונקציית עזר לעריכת הודעות בצורה בטוחה
async def safe_edit_message(message, text, parse_mode=None, user_id=None):
    """
    עורך הודעה בצורה בטוחה, מטפל בשגיאות אפשריות
    
    Args:
        message: אובייקט ההודעה לעריכה
        text: הטקסט החדש
        parse_mode: מצב פירוש (Markdown, HTML, וכו')
        user_id: מזהה המשתמש (אופציונלי)
        
    Returns:
        ההודעה המעודכנת או הודעה חדשה אם העריכה נכשלה
    """
    logger = logging.getLogger('telegram_bot')
    
    try:
        # ניסיון לערוך את ההודעה
        return await message.edit_text(text, parse_mode=parse_mode)
    except TelegramError as e:
        logger.error(f"Error editing message: {e}")
        
        # אם יש שגיאת Markdown, ננסה לשלוח ללא Markdown
        if "can't parse entities" in str(e) and parse_mode:
            try:
                # ניקוי תגיות Markdown/HTML
                clean_text = text
                if parse_mode == ParseMode.MARKDOWN:
                    clean_text = text.replace('*', '').replace('_', '').replace('`', '')
                elif parse_mode == ParseMode.HTML:
                    import re
                    clean_text = re.sub(r'<[^>]+>', '', text)
                
                return await message.edit_text(clean_text, parse_mode=None)
            except Exception as e2:
                logger.error(f"Error editing message without formatting: {e2}")
        
        # אם העריכה נכשלה לגמרי, ננסה לשלוח הודעה חדשה
        if hasattr(message, 'reply_text'):
            try:
                return await message.reply_text(text, parse_mode=parse_mode)
            except Exception as e3:
                logger.error(f"Error sending new message: {e3}")
                
                # ניסיון אחרון - לשלוח הודעה פשוטה ללא עיצוב
                try:
                    clean_text = text.replace('*', '').replace('_', '').replace('`', '')
                    return await message.reply_text(clean_text, parse_mode=None)
                except Exception as e4:
                    logger.error(f"Final error sending plain message: {e4}")
    
    except Exception as e:
        logger.error(f"Unexpected error editing message: {e}")
        
        # ניסיון לשלוח הודעה חדשה במקרה של שגיאה לא צפויה
        if hasattr(message, 'reply_text'):
            try:
                return await message.reply_text("אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב.", parse_mode=None)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")
    
    return None

# מילות מפתח לזיהוי תבניות
template_keywords = {
    "setup": ["התקנה", "הגדרה", "התקנת", "להתקין", "להגדיר", "setup", "install", "configure"],
    "payment_gateways": ["תשלום", "שערי תשלום", "סליקה", "כרטיסי אשראי", "payment", "gateway", "credit card"],
    "shipping": ["משלוח", "משלוחים", "שליח", "דואר", "הובלה", "shipping", "delivery", "courier"],
    "tax": ["מס", "מיסים", "מע\"מ", "מע״מ", "חשבונית", "tax", "vat", "invoice"],
    "seo": ["קידום", "גוגל", "חיפוש", "seo", "google", "search", "קידום אורגני", "מילות מפתח"],
    "marketing": ["שיווק", "פרסום", "קמפיין", "מכירות", "marketing", "advertising", "campaign", "promotion"]
}

# Configure logging
logger = setup_logger('telegram_bot')

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = LOGFIRE_PROJECT

# Configure and initialize Logfire for monitoring
import logfire
# נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
try:
    logfire.configure(
        token=LOGFIRE_API_KEY,
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
except (AttributeError, ImportError):
    # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
    logfire.configure(token=LOGFIRE_API_KEY)
# הגבלת ניטור HTTP לכותרות בלבד ללא תוכן הבקשה
logfire.instrument_httpx(capture_headers=True, capture_body=False)

# מצבים לשיחה עם הבוט
WAITING_FOR_DOCUMENT = 1
WAITING_FOR_TITLE = 2
WAITING_FOR_SEARCH_QUERY = 3

# מצבים לתהליך יצירת מוצר
WAITING_FOR_PRODUCT_NAME = 10
WAITING_FOR_PRODUCT_DESCRIPTION = 11
WAITING_FOR_PRODUCT_PRICE = 12
WAITING_FOR_PRODUCT_SALE_PRICE = 13
WAITING_FOR_PRODUCT_SKU = 14
WAITING_FOR_PRODUCT_STOCK = 15
WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS = 16
WAITING_FOR_PRODUCT_CATEGORIES = 17
WAITING_FOR_PRODUCT_IMAGES = 18
WAITING_FOR_PRODUCT_CONFIRMATION = 19
WAITING_FOR_PRODUCT_EDIT = 20

# מצבים לתהליך ניהול הזמנות
WAITING_FOR_ORDER_ACTION = 26
WAITING_FOR_ORDER_ID = 20
WAITING_FOR_ORDER_STATUS = 21
WAITING_FOR_CANCEL_REASON = 22
WAITING_FOR_REFUND_AMOUNT = 23
WAITING_FOR_REFUND_REASON = 24
WAITING_FOR_FILTER_CRITERIA = 25

class TelegramBot:
    def __init__(self):
        """אתחול הבוט"""
        self.agent = TelegramAgent()
        self.application = None
        self.commands = []
        self.typing_status = {}  # מילון לשמירת סטטוס ההקלדה של כל משתמש
        
    async def run(self):
        """הפעלת הבוט"""
        # הגדרת ברירות מחדל
        defaults = Defaults(
            parse_mode=ParseMode.MARKDOWN,
            tzinfo=timezone.utc
        )
        
        # יצירת אפליקציית הבוט
        self.application = Application.builder() \
            .token(TELEGRAM_TOKEN) \
            .defaults(defaults) \
            .read_timeout(30) \
            .write_timeout(30) \
            .connect_timeout(30) \
            .pool_timeout(30) \
            .build()
        
        # הגדרת פקודות
        self.commands = [
            BotCommand("start", "התחלת שיחה עם הבוט"),
            BotCommand("help", "הצגת עזרה"),
            BotCommand("clear", "ניקוי היסטוריית השיחה"),
            BotCommand("stats", "הצגת סטטיסטיקות"),
            BotCommand("search", "חיפוש במסמכים"),
            BotCommand("add_document", "הוספת מסמך חדש"),
            BotCommand("list_documents", "הצגת רשימת המסמכים"),
            BotCommand("create_product", "יצירת מוצר חדש"),
            BotCommand("manage_orders", "ניהול הזמנות"),
            BotCommand("store", "ניהול החנות"),
            BotCommand("daily_report", "הצגת דוח יומי"),
            BotCommand("weekly_report", "הצגת דוח שבועי"),
            BotCommand("monthly_report", "הצגת דוח חודשי"),
            BotCommand("update_keywords", "עדכון מילות מפתח")
        ]
        
        # הוספת פקודות אדמין
        admin_commands = [
            BotCommand("admin", "פקודות אדמין"),
            BotCommand("admin_users", "ניהול משתמשים"),
            BotCommand("admin_stats", "סטטיסטיקות מערכת"),
            BotCommand("admin_docs", "ניהול מסמכים"),
            BotCommand("admin_models", "ניהול מודלים"),
            BotCommand("admin_config", "הגדרות מערכת"),
            BotCommand("admin_notify", "שליחת הודעה לכל המשתמשים")
        ]
        
        # רישום פקודות
        await self.application.bot.set_my_commands(self.commands)
        
        # רישום פקודות אדמין למשתמש האדמין
        if ADMIN_USER_ID:
            try:
                admin_id = int(ADMIN_USER_ID)
                await self.application.bot.set_my_commands(
                    self.commands + admin_commands,
                    scope=telegram.BotCommandScopeChat(chat_id=admin_id)
                )
            except (ValueError, TelegramError) as e:
                logger.error(f"Error setting admin commands: {e}")
        
        # הוספת פקודות חנות
        self.application.add_handler(CommandHandler("store", self.handle_store_dashboard))
        self.application.add_handler(CommandHandler("connect_store", self.handle_connect_store_start))
        self.application.add_handler(CommandHandler("products", self.handle_store_products))
        self.application.add_handler(CommandHandler("orders", self.handle_store_orders))
        self.application.add_handler(CommandHandler("customers", self.handle_store_customers))
        self.application.add_handler(CommandHandler("inventory", self.handle_store_inventory))
        
        # הוספת מטפל לקריאות callback
        self.application.add_handler(CallbackQueryHandler(self.handle_admin_callback, pattern=r'^admin_'))
        self.application.add_handler(CallbackQueryHandler(self.handle_store_callback, pattern=r'^store_'))
        
        # הוספת מטפל לשיחה להוספת מסמך
        add_document_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("add_document", self.add_document_start)],
            states={
                WAITING_FOR_DOCUMENT: [MessageHandler(filters.Document.ALL, self.add_document_receive)],
                WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_document_title)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(add_document_conv_handler)
        
        # הוספת מטפל לשיחה לחיפוש במסמכים
        search_documents_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("search_documents", self.search_documents_start)],
            states={
                WAITING_FOR_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_documents_query)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(search_documents_conv_handler)
        
        # הוספת מטפל לשיחה ליצירת מוצר
        create_product_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("create_product", self.create_product_start)],
            states={
                WAITING_FOR_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_name)],
                WAITING_FOR_PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_description)],
                WAITING_FOR_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_price)],
                WAITING_FOR_PRODUCT_SALE_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_sale_price),
                    CallbackQueryHandler(self.handle_sale_price_callback)
                ],
                WAITING_FOR_PRODUCT_SKU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_sku)],
                WAITING_FOR_PRODUCT_STOCK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_stock),
                    CallbackQueryHandler(self.handle_stock_callback)
                ],
                WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_weight_dimensions),
                    CallbackQueryHandler(self.handle_dimensions_callback)
                ],
                WAITING_FOR_PRODUCT_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_categories)],
                WAITING_FOR_PRODUCT_IMAGES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_images_text),
                    MessageHandler(filters.PHOTO, self.create_product_images_photo),
                    CallbackQueryHandler(self.handle_image_description_callback, pattern="^(add|skip)_image_description$"),
                    CallbackQueryHandler(self.handle_more_images_callback, pattern="^(add_more_images|finish_images)$")
                ],
                WAITING_FOR_PRODUCT_CONFIRMATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_confirmation),
                    CallbackQueryHandler(self.handle_product_callback)
                ],
                WAITING_FOR_PRODUCT_EDIT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_product_edit),
                    MessageHandler(filters.PHOTO, self.create_product_images_photo)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(create_product_conv_handler)
        
        # הוספת מטפל לשיחה לניהול הזמנות
        manage_orders_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("manage_orders", self.manage_orders_start)],
            states={
                WAITING_FOR_ORDER_ACTION: [CallbackQueryHandler(self.get_order_id, pattern=r'^order_action_')],
                WAITING_FOR_ORDER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_order_id)],
                WAITING_FOR_ORDER_STATUS: [CallbackQueryHandler(self.update_order_status, pattern=r'^order_status_')],
                WAITING_FOR_CANCEL_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.cancel_order_reason)],
                WAITING_FOR_REFUND_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.refund_order_amount)],
                WAITING_FOR_REFUND_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.refund_order_reason)],
                WAITING_FOR_FILTER_CRITERIA: [CallbackQueryHandler(self.filter_orders, pattern=r'^filter_')],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(manage_orders_conv_handler)
        
        # הוספת פקודות בסיסיות
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("clear", self.clear))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("list_documents", self.list_documents_command))
        self.application.add_handler(CommandHandler("search", self.search_documents_start))
        
        # הוספת מטפל להודעות טקסט רגילות
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # הוספת פקודות דוחות ועדכון מילות מפתח
        self.application.add_handler(CommandHandler("daily_report", self.daily_report))
        self.application.add_handler(CommandHandler("weekly_report", self.weekly_report))
        self.application.add_handler(CommandHandler("monthly_report", self.monthly_report))
        self.application.add_handler(CommandHandler("update_keywords", self.update_keywords))
        
        # הוספת מטפלי פקודות אדמין
        self.application.add_handler(CommandHandler("admin", self.handle_admin_command))
        self.application.add_handler(CommandHandler("admin_users", self.handle_admin_users))
        self.application.add_handler(CommandHandler("admin_stats", self.handle_admin_stats))
        self.application.add_handler(CommandHandler("admin_docs", self.handle_admin_docs))
        self.application.add_handler(CommandHandler("admin_models", self.handle_admin_models))
        self.application.add_handler(CommandHandler("admin_config", self.handle_admin_config))
        self.application.add_handler(CommandHandler("admin_notify", self.handle_admin_notify))
        
        # הפעלת הבוט
        logger.info("Starting Telegram bot")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # שמירת האפליקציה כדי שנוכל לסגור אותה בעתיד
        self.application = self.application
        
        # לא סוגרים את הבוט כאן, הוא ימשיך לרוץ עד שהמשתמש יסגור אותו
        # או עד שהתוכנית תיסגר

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        welcome_message = (
            f"שלום {user.first_name}! 👋\n\n"
            "אני סוכן AI מומחה לניהול חנויות ווקומרס, כאן כדי לעזור לך לנהל את החנות שלך בצורה חכמה ויעילה.\n\n"
            "🛍️ מה אני יכול לעשות עבורך?\n"
            "• ניהול מוצרים - הוספה, עריכה ומחיקה של מוצרים\n"
            "• טיפול בהזמנות - צפייה, עדכון סטטוס ומעקב\n"
            "• ניהול מלאי - התראות על מלאי נמוך ועדכון כמויות\n"
            "• ניתוח מכירות - דוחות, מגמות והמלצות לשיפור\n"
            "• ניהול לקוחות - מידע על לקוחות והיסטוריית רכישות\n\n"
            
            "🔗 כדי להתחיל, חבר את חנות הווקומרס שלך באמצעות הפקודה /connect_store\n"
            "📊 לצפייה בדאשבורד החנות, השתמש בפקודה /store\n\n"
            
            "✨ יתרונות השימוש בסוכן ווקומרס:\n"
            "• חיסכון בזמן - ניהול החנות ישירות מטלגרם\n"
            "• התראות בזמן אמת - קבלת עדכונים על הזמנות חדשות ומלאי נמוך\n"
            "• תובנות עסקיות - ניתוח מכירות וזיהוי מגמות\n"
            "• ממשק טבעי - תקשורת בשפה טבעית ללא צורך בלמידת ממשק חדש\n\n"
            
            "הקלד /help לרשימת כל הפקודות הזמינות."
        )
        # Log the start command
        logfire.info('command_start', user_id=user.id, username=user.username)
        
        try:
            # שליחת ההודעה ללא parse_mode
            await update.message.reply_text(welcome_message, parse_mode=None)
            logger.info(f"Start message sent to user {user.id}")
        except Exception as e:
            logger.error(f"Error sending start message: {e}")
            # ניסיון לשלוח הודעה פשוטה יותר במקרה של שגיאה
            try:
                simple_welcome = f"שלום {user.first_name}! אני כאן כדי לעזור לך בניהול חנות הווקומרס שלך. הקלד /help לרשימת הפקודות."
                await update.message.reply_text(simple_welcome, parse_mode=None)
            except Exception as simple_error:
                logger.error(f"Error sending simple start message: {simple_error}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        user = update.effective_user
        
        # Log the help command
        logfire.info('command_help', user_id=user.id, username=user.username)
        
        # בניית רשימת הפקודות הזמינות
        commands_list = "\n".join([f"/{cmd} - {desc}" for cmd, desc in ALLOWED_COMMANDS])
        
        # בדיקה אם המשתמש הוא מנהל
        is_admin_user = False
        session = await db.get_session()
        try:
            from src.handlers.admin_handler import is_admin
            is_admin_user = await is_admin(user.id, session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
        
        # הוספת פקודות מנהל אם המשתמש הוא מנהל
        if is_admin_user:
            admin_commands_list = "\n".join([f"/{cmd} - {desc}" for cmd, desc in ADMIN_COMMANDS])
            commands_list += "\n\n🔐 פקודות מנהל:\n" + admin_commands_list
        
        help_message = (
            "🛍️ *עזרה ורשימת פקודות - סוכן ווקומרס*\n\n"
            "אני סוכן AI מומחה לניהול חנויות ווקומרס. אני יכול לעזור לך לנהל את החנות שלך באמצעות שיחה טבעית ופקודות פשוטות.\n\n"
            "📋 *פקודות זמינות:*\n"
            f"{commands_list}\n\n"
            "🛒 *ניהול חנות ווקומרס:*\n"
            "• השתמש בפקודה /connect_store כדי לחבר את חנות הווקומרס שלך\n"
            "• השתמש בפקודה /store כדי לגשת לדאשבורד ניהול החנות\n"
            "• השתמש בפקודה /products לניהול מוצרים\n"
            "• השתמש בפקודה /orders לניהול הזמנות\n"
            "• השתמש בפקודה /customers לניהול לקוחות\n"
            "• השתמש בפקודה /sales לצפייה בדוחות מכירות\n"
            "• השתמש בפקודה /inventory לניהול מלאי\n\n"
            "• שאל אותי שאלות בשפה טבעית על החנות שלך, כמו:\n"
            "  - 'כמה מכירות היו לי היום?'\n"
            "  - 'מהם המוצרים הפופולריים ביותר?'\n"
            "  - 'אילו מוצרים במלאי נמוך?'\n"
            "  - 'מה הסטטוס של ההזמנה האחרונה?'\n"
        )
        
        try:
            # ניסיון לשלוח את ההודעה עם Markdown
            await update.message.reply_text(help_message, parse_mode="Markdown")
            logger.info(f"Help message sent to user {user.id}")
        except Exception as e:
            logger.error(f"Error sending help message with Markdown: {e}")
            try:
                # ניסיון לשלוח ללא Markdown
                await update.message.reply_text(help_message, parse_mode=None)
                logger.info(f"Help message sent to user {user_id} without Markdown")
            except Exception as simple_error:
                logger.error(f"Error sending help message without Markdown: {simple_error}")
                try:
                    # ניסיון לשלוח הודעה פשוטה יותר
                    simple_help = "רשימת פקודות זמינות:\n/start - התחלת שיחה\n/help - עזרה\n/clear - ניקוי היסטוריה\n/stats - סטטיסטיקות\n/search - חיפוש במסמכים\n/list_documents - רשימת מסמכים"
                    await update.message.reply_text(simple_help, parse_mode=None)
                except Exception as very_simple_error:
                    logger.error(f"Error sending simple help message: {very_simple_error}")

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /clear command."""
        user_id = update.effective_user.id
        # Log the clear command
        logfire.info('command_clear', user_id=user_id)
        db.clear_chat_history(user_id)
        await update.message.reply_text("היסטוריית השיחה נמחקה! 🗑️")
        
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /stats command - show database statistics."""
        user_id = update.effective_user.id
        
        # Log the stats command
        logfire.info('command_stats', user_id=user_id)
        
        try:
            # Get statistics from database
            message_count = db.get_message_count()
            user_count = db.get_user_count()
            
            # Get user's personal stats
            user_history = db.get_chat_history(user_id)
            user_message_count = len(user_history)
            
            stats_message = (
                "📊 סטטיסטיקות הבוט:\n\n"
                f"סה\"כ הודעות במערכת: {message_count}\n"
                f"מספר משתמשים ייחודיים: {user_count}\n\n"
                f"הסטטיסטיקות שלך:\n"
                f"מספר ההודעות שלך: {user_message_count}\n"
            )
            
            await update.message.reply_text(stats_message)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            logfire.error('stats_error', user_id=user_id, error=str(e))
            await update.message.reply_text("אירעה שגיאה בהצגת הסטטיסטיקות. אנא נסה שוב מאוחר יותר.")
    
    async def search_documents_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך חיפוש במסמכים"""
        user_id = update.effective_user.id
        logfire.info('command_search_documents_start', user_id=user_id)
        
        await update.message.reply_text(
            "🔍 *חיפוש במאגר הידע*\n\n"
            "אנא הזן את מילות החיפוש שלך. אחפש במאגר המסמכים ואחזיר את התוצאות הרלוונטיות ביותר.\n\n"
            "לביטול החיפוש, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_SEARCH_QUERY
    
    async def search_documents_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """חיפוש במסמכים לפי שאילתה"""
        user_id = update.effective_user.id
        query = update.message.text.strip()
        
        logfire.info('search_documents_query', user_id=user_id, query=query)
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            "🔍 מחפש במאגר הידע... אנא המתן."
        )
        
        try:
            # חיפוש במאגר הידע
            from src.services.rag_service import RAGService
            rag_service = RAGService()
            results = await rag_service.search_documents(query, limit=5, min_similarity=0.1)
            
            if not results:
                await wait_message.edit_text(
                    "❌ לא נמצאו תוצאות מתאימות לחיפוש שלך.\n\n"
                    "אנא נסה שוב עם מילות חיפוש אחרות או הוסף מסמכים רלוונטיים למאגר הידע."
                )
                return ConversationHandler.END
            
            # בניית הודעת תוצאות
            response_text = f"🔍 *תוצאות חיפוש עבור: \"{query}\"*\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'ללא כותרת')
                source = result.get('source', 'לא ידוע')
                similarity = result.get('similarity_percentage', 0)
                
                response_text += f"*{i}. {title}*\n"
                response_text += f"מקור: {source}\n"
                response_text += f"רלוונטיות: {similarity}%\n"
                
                # חיתוך התוכן לאורך סביר להצגה
                content = result.get('content', '')
                content_preview = content[:150] + "..." if len(content) > 150 else content
                response_text += f"תוכן: {content_preview}\n\n"
            
            response_text += "להוספת מסמכים נוספים למאגר הידע, השתמש בפקודה /add_document."
            
            # שליחת התוצאות
            try:
                await wait_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
            except Exception as msg_error:
                # אם יש בעיה עם ה-Markdown, ננסה לשלוח ללא עיצוב
                logger.warning(f"Error sending formatted message: {msg_error}")
                await wait_message.edit_text(response_text)
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            logfire.error('search_documents_error', user_id=user_id, query=query, error=str(e))
            await wait_message.edit_text(
                "❌ אירעה שגיאה בחיפוש. אנא נסה שוב מאוחר יותר.\n\n"
                f"פרטי השגיאה: {str(e)}\n\n"
                "אם הבעיה נמשכת, פנה למנהל המערכת."
            )
        
        return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """ביטול שיחה פעילה"""
        user_id = update.effective_user.id
        
        # ניקוי קבצים זמניים אם יש
        if user_id in self.document_uploads and 'file_path' in self.document_uploads[user_id]:
            try:
                file_path = self.document_uploads[user_id]['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            
            # מחיקת המידע הזמני
            del self.document_uploads[user_id]
        
        # ניקוי נתוני מוצר זמניים אם יש
        if 'product_data' in context.user_data:
            context.user_data.pop('product_data', None)
        
        logfire.info('conversation_cancelled', user_id=user_id)
        await update.message.reply_text("הפעולה בוטלה.")
        return ConversationHandler.END
    
    # פונקציות לתהליך יצירת מוצר
    
    async def create_product_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך יצירת מוצר"""
        user_id = update.effective_user.id
        logfire.info('command_create_product_start', user_id=user_id)
        
        # בדיקה אם המשתמש חיבר חנות
        session = await db.get_session()
        try:
            from src.handlers.store_handler import is_store_connected
            store_connected = await is_store_connected(user_id, session)
            await session.commit()
            
            if not store_connected:
                await update.message.reply_text(
                    "❌ *לא ניתן ליצור מוצר*\n\n"
                    "עדיין לא חיברת את חנות ה-WooCommerce שלך לבוט.\n"
                    "כדי לחבר את החנות, השתמש בפקודה /connect_store.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            # אתחול מילון לשמירת נתוני המוצר
            context.user_data['product_data'] = {}
            
            # יצירת סרגל התקדמות ויזואלי
            progress_bar = "🔵⚪⚪⚪⚪⚪"  # שלב 1 מתוך 6
            
            # הצגת הסבר על תהליך יצירת המוצר
            await update.message.reply_text(
                f"🛍️ *יצירת מוצר חדש ב-WooCommerce*\n\n"
                f"{progress_bar} *שלב 1/6: שם המוצר*\n\n"
                "אני אלווה אותך בתהליך יצירת מוצר חדש בחנות שלך.\n"
                "התהליך כולל מספר שלבים:\n"
                "1️⃣ שם המוצר\n"
                "2️⃣ תיאור המוצר\n"
                "3️⃣ מחיר המוצר\n"
                "4️⃣ מחיר מבצע (אופציונלי)\n"
                "5️⃣ מק\"ט (אופציונלי)\n"
                "6️⃣ מלאי (אופציונלי)\n"
                "7️⃣ מידות (אופציונלי)\n"
                "8️⃣ קטגוריות\n"
                "9️⃣ תמונות (אופציונלי)\n"
                "10️⃣ אישור ויצירת המוצר\n\n"
                "בכל שלב תוכל להקליד /cancel כדי לבטל את התהליך.\n\n"
                "נתחיל! מה יהיה שם המוצר?",
                parse_mode='Markdown'
            )
            
            return WAITING_FOR_PRODUCT_NAME
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in create_product_start: {str(e)}")
            await update.message.reply_text(
                "❌ אירעה שגיאה בהתחלת תהליך יצירת המוצר. אנא נסה שוב מאוחר יותר."
            )
            return ConversationHandler.END
        finally:
            await session.close()
    
    async def create_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם המוצר"""
        user_id = update.effective_user.id
        product_name = update.message.text.strip()
        
        # בדיקת תקינות השם
        if len(product_name) < 3:
            await update.message.reply_text(
                "❌ שם המוצר קצר מדי. אנא הזן שם באורך של לפחות 3 תווים."
            )
            return WAITING_FOR_PRODUCT_NAME
        
        # שמירת שם המוצר
        context.user_data['product_data']['name'] = product_name
        
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅🔵⚪⚪⚪⚪"  # שלב 2 מתוך 6
        
        # מעבר לשלב הבא
        await update.message.reply_text(
            f"✅ שם המוצר נשמר: *{product_name}*\n\n"
            f"{progress_bar} *שלב 2/6: תיאור המוצר*\n\n"
            "עכשיו, אנא הזן תיאור מפורט למוצר.\n"
            "התיאור יוצג בדף המוצר ויעזור ללקוחות להבין את המוצר.",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_DESCRIPTION
    
    async def create_product_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור המוצר"""
        user_id = update.effective_user.id
        product_description = update.message.text.strip()
        
        # בדיקת תקינות התיאור
        if len(product_description) < 20:
            await update.message.reply_text(
                "❌ תיאור המוצר קצר מדי. אנא הזן תיאור מפורט יותר (לפחות 20 תווים)."
            )
            return WAITING_FOR_PRODUCT_DESCRIPTION
        
        # שמירת תיאור המוצר
        context.user_data['product_data']['description'] = product_description
        
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅🔵⚪⚪⚪"  # שלב 3 מתוך 6
        
        # מעבר לשלב הבא
        await update.message.reply_text(
            f"✅ תיאור המוצר נשמר בהצלחה!\n\n"
            f"{progress_bar} *שלב 3/6: מחיר המוצר*\n\n"
            "עכשיו, אנא הזן את המחיר הרגיל של המוצר.\n"
            "לדוגמה: 99.90 או 100",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_PRICE
    
    async def create_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מחיר המוצר"""
        user_id = update.effective_user.id
        price_text = update.message.text.strip()
        
        # ניקוי סימני מטבע ורווחים
        price_text = price_text.replace('₪', '').replace('$', '').replace('€', '').strip()
        
        # בדיקת תקינות המחיר
        try:
            price = float(price_text.replace(',', '.'))
            if price <= 0:
                raise ValueError("המחיר חייב להיות חיובי")
        except ValueError:
            await update.message.reply_text(
                "❌ המחיר שהזנת אינו תקין. אנא הזן מספר חיובי (לדוגמה: 99.90)."
            )
            return WAITING_FOR_PRODUCT_PRICE
        
        # שמירת מחיר המוצר
        context.user_data['product_data']['regular_price'] = f"{price:.2f}"
        
        # שאלה על מחיר מבצע
        keyboard = [
            [InlineKeyboardButton("כן, אוסיף מחיר מבצע", callback_data='add_sale_price')],
            [InlineKeyboardButton("לא, המשך לשלב הבא", callback_data='skip_sale_price')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅🔵⚪⚪"  # שלב 4 מתוך 6
        
        await update.message.reply_text(
            f"✅ מחיר המוצר נשמר: *{price:.2f}₪*\n\n"
            f"{progress_bar} *שלב 4/6: קטגוריות המוצר*\n\n"
            "עכשיו, אנא הזן את הקטגוריות של המוצר, מופרדות בפסיקים.\n"
            "לדוגמה: ביגוד, חולצות, אופנת גברים",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_CATEGORIES
    
    async def create_product_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת קטגוריות המוצר"""
        user_id = update.effective_user.id
        categories_text = update.message.text.strip()
        
        # פיצול הקטגוריות לרשימה
        categories = [cat.strip() for cat in categories_text.split(',') if cat.strip()]
        
        # בדיקת תקינות הקטגוריות
        if not categories:
            await update.message.reply_text(
                "❌ לא הזנת קטגוריות. אנא הזן לפחות קטגוריה אחת."
            )
            return WAITING_FOR_PRODUCT_CATEGORIES
        
        # שמירת קטגוריות המוצר
        context.user_data['product_data']['categories'] = categories
        
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅✅🔵⚪"  # שלב 5 מתוך 6
        
        # מעבר לשלב הבא
        await update.message.reply_text(
            f"✅ קטגוריות המוצר נשמרו: *{', '.join(categories)}*\n\n"
            f"{progress_bar} *שלב 5/6: תמונות המוצר*\n\n"
            "עכשיו, אנא שלח תמונות של המוצר. תוכל לשלוח מספר תמונות בזו אחר זו.\n"
            "כשתסיים, הקלד 'סיום' או 'דלג' כדי לדלג על שלב זה.",
            parse_mode='Markdown'
        )
        
        # אתחול רשימת תמונות
        if 'images' not in context.user_data['product_data']:
            context.user_data['product_data']['images'] = []
        
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def handle_sale_price_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לשאלה על מחיר מבצע"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_sale_price":
            # המשתמש רוצה להוסיף מחיר מבצע
            await query.edit_message_text(
                "🏷️ *הזנת מחיר מבצע*\n\n"
                "אנא הזן את מחיר המבצע למוצר (במספרים בלבד).\n"
                "המחיר צריך להיות נמוך ממחיר הרגיל.\n\n"
                "לדוגמה: 79.90\n\n"
                "💡 *טיפ:* ניתן להזין מספרים עם נקודה עשרונית. סימני מטבע (₪, $) יוסרו אוטומטית.",
                parse_mode='Markdown'
            )
            return WAITING_FOR_PRODUCT_SALE_PRICE
        else:
            # המשתמש לא רוצה להוסיף מחיר מבצע, ממשיך לשלב הבא
            return await self.ask_for_sku(update, context)
    
    async def create_product_sale_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מחיר מבצע למוצר"""
        user_id = update.effective_user.id
        sale_price_text = update.message.text.strip()
        
        # אם המשתמש רוצה לדלג
        if sale_price_text.lower() in ["דלג", "להמשיך", "skip", "next"]:
            return await self.ask_for_sku(update, context)
        
        # ניקוי המחיר מסימנים מיוחדים
        sale_price_text = sale_price_text.replace('₪', '').replace('$', '').replace(',', '').strip()
        
        # בדיקת תקינות המחיר
        try:
            sale_price = float(sale_price_text)
            regular_price = float(context.user_data['product_data']['regular_price'])
            
            if sale_price <= 0:
                raise ValueError("המחיר חייב להיות חיובי")
                
            # בדיקה שמחיר המבצע נמוך מהמחיר הרגיל
            if sale_price >= regular_price:
                await update.message.reply_text(
                    f"❌ מחיר המבצע ({sale_price}₪) חייב להיות נמוך מהמחיר הרגיל ({regular_price}₪).\n"
                    "אנא הזן מחיר מבצע נמוך יותר, או הקלד 'דלג' כדי לדלג על שלב זה."
                )
                return WAITING_FOR_PRODUCT_SALE_PRICE
                
        except ValueError:
            await update.message.reply_text(
                "❌ המחיר שהזנת אינו תקין. אנא הזן מספר חיובי (לדוגמה: 79.90), או הקלד 'דלג' כדי לדלג על שלב זה."
            )
            return WAITING_FOR_PRODUCT_SALE_PRICE
        
        # שמירת מחיר המבצע
        context.user_data['product_data']['sale_price'] = str(sale_price)
        
        # המשך לשלב הבא
        return await self.ask_for_sku(update, context)
    
    async def ask_for_sku(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """שאלה על מק"ט (SKU) למוצר"""
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅✅🔵⚪⚪"  # שלב 4 מתוך 7
        
        # בדיקה אם זו קריאה מ-callback או מהודעה רגילה
        if update.callback_query:
            message_func = update.callback_query.edit_message_text
        else:
            message_func = update.message.reply_text
        
        await message_func(
            f"{progress_bar} *שלב 4/7: מק\"ט (SKU) למוצר*\n\n"
            "אנא הזן מק\"ט (מספר קטלוגי) למוצר.\n"
            "המק\"ט משמש לזיהוי ייחודי של המוצר במערכת.\n\n"
            "לדוגמה: ABC-123\n\n"
            "💡 *טיפ:* אם אין לך מק\"ט, הקלד 'דלג' והמערכת תיצור מק\"ט אוטומטי.",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_SKU
    
    async def create_product_sku(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מק"ט (SKU) למוצר"""
        user_id = update.effective_user.id
        sku_text = update.message.text.strip()
        
        # אם המשתמש רוצה לדלג
        if sku_text.lower() in ["דלג", "להמשיך", "skip", "next"]:
            # יצירת מק"ט אוטומטי מבוסס על שם המוצר ותאריך
            product_name = context.user_data['product_data']['name']
            timestamp = datetime.now().strftime("%y%m%d%H%M")
            auto_sku = f"{product_name[:3].replace(' ', '')}-{timestamp}"
            context.user_data['product_data']['sku'] = auto_sku
            
            await update.message.reply_text(
                f"✅ נוצר מק\"ט אוטומטי: *{auto_sku}*",
                parse_mode='Markdown'
            )
        else:
            # בדיקת תקינות המק"ט
            if len(sku_text) < 2:
                await update.message.reply_text(
                    "❌ המק\"ט קצר מדי. אנא הזן מק\"ט באורך של לפחות 2 תווים, או הקלד 'דלג' ליצירת מק\"ט אוטומטי."
                )
                return WAITING_FOR_PRODUCT_SKU
            
            if len(sku_text) > 50:
                await update.message.reply_text(
                    "❌ המק\"ט ארוך מדי. אנא הזן מק\"ט באורך של עד 50 תווים, או הקלד 'דלג' ליצירת מק\"ט אוטומטי."
                )
                return WAITING_FOR_PRODUCT_SKU
            
            # שמירת המק"ט
            context.user_data['product_data']['sku'] = sku_text
            
            await update.message.reply_text(
                f"✅ המק\"ט נשמר: *{sku_text}*",
                parse_mode='Markdown'
            )
        
        # המשך לשלב הבא - ניהול מלאי
        return await self.ask_for_stock(update, context)
    
    async def ask_for_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """שאלה על ניהול מלאי למוצר"""
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅✅✅🔵⚪"  # שלב 5 מתוך 7
        
        # שאלה על ניהול מלאי
        keyboard = [
            [InlineKeyboardButton("כן, יש מלאי למוצר", callback_data="manage_stock")],
            [InlineKeyboardButton("לא, ללא ניהול מלאי", callback_data="skip_stock")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{progress_bar} *שלב 5/7: ניהול מלאי*\n\n"
            "האם ברצונך לנהל מלאי למוצר זה?\n"
            "ניהול מלאי יאפשר לך לעקוב אחר כמות המוצרים במלאי ולהציג הודעת 'אזל מהמלאי' כשהמלאי נגמר.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_STOCK
    
    async def handle_stock_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לשאלה על ניהול מלאי"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "manage_stock":
            # המשתמש רוצה לנהל מלאי
            await query.edit_message_text(
                "📦 *הזנת כמות מלאי*\n\n"
                "אנא הזן את כמות המוצרים במלאי (מספר שלם).\n"
                "לדוגמה: 50",
                parse_mode='Markdown'
            )
            return WAITING_FOR_PRODUCT_STOCK
        else:
            # המשתמש לא רוצה לנהל מלאי, ממשיך לשלב הבא
            context.user_data['product_data']['manage_stock'] = False
            context.user_data['product_data']['stock_status'] = "instock"  # ברירת מחדל: במלאי
            return await self.ask_for_weight_dimensions(update, context)
    
    async def create_product_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כמות מלאי למוצר"""
        user_id = update.effective_user.id
        stock_text = update.message.text.strip()
        
        # בדיקת תקינות כמות המלאי
        try:
            stock_quantity = int(stock_text)
            if stock_quantity < 0:
                raise ValueError("כמות המלאי חייבת להיות חיובית")
                
        except ValueError:
            await update.message.reply_text(
                "❌ כמות המלאי שהזנת אינה תקינה. אנא הזן מספר שלם חיובי (לדוגמה: 50)."
            )
            return WAITING_FOR_PRODUCT_STOCK
        
        # שמירת נתוני המלאי
        context.user_data['product_data']['manage_stock'] = True
        context.user_data['product_data']['stock_quantity'] = stock_quantity
        
        # קביעת סטטוס מלאי אוטומטית
        if stock_quantity > 0:
            context.user_data['product_data']['stock_status'] = "instock"  # במלאי
        else:
            context.user_data['product_data']['stock_status'] = "outofstock"  # אזל מהמלאי
        
        await update.message.reply_text(
            f"✅ כמות המלאי נשמרה: *{stock_quantity}* יחידות",
            parse_mode='Markdown'
        )
        
        # המשך לשלב הבא - משקל ומידות
        return await self.ask_for_weight_dimensions(update, context)
    
    async def ask_for_weight_dimensions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """שאלה על משקל ומידות המוצר"""
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅✅✅✅🔵"  # שלב 6 מתוך 7
        
        # בדיקה אם זו קריאה מ-callback או מהודעה רגילה
        if update.callback_query:
            message_func = update.callback_query.edit_message_text
        else:
            message_func = update.message.reply_text
        
        # שאלה על משקל ומידות
        keyboard = [
            [InlineKeyboardButton("כן, יש משקל ומידות", callback_data="add_dimensions")],
            [InlineKeyboardButton("לא, להמשיך לקטגוריות", callback_data="skip_dimensions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message_func(
            f"{progress_bar} *שלב 6/7: משקל ומידות המוצר*\n\n"
            "האם ברצונך להוסיף מידע על משקל ומידות המוצר?\n"
            "מידע זה חשוב לחישוב עלויות משלוח ולהצגת מידע מדויק ללקוחות.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS
    
    async def create_product_weight_dimensions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת משקל ומידות המוצר"""
        user_id = update.effective_user.id
        dimensions_text = update.message.text.strip()
        
        # פרסור הטקסט לחלקים
        try:
            # מצפה לפורמט: "משקל: X ק"ג, אורך: Y ס"מ, רוחב: Z ס"מ, גובה: W ס"מ"
            parts = dimensions_text.split(',')
            dimensions = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # ניקוי יחידות מידה
                    value = value.replace('ק"ג', '').replace('קג', '').replace('kg', '')
                    value = value.replace('ס"מ', '').replace('סמ', '').replace('cm', '')
                    value = value.strip()
                    
                    # המרה למספר
                    try:
                        value = float(value)
                        
                        # שמירה בהתאם לסוג המידה
                        if 'משקל' in key or 'weight' in key:
                            dimensions['weight'] = value
                        elif 'אורך' in key or 'length' in key:
                            dimensions['length'] = value
                        elif 'רוחב' in key or 'width' in key:
                            dimensions['width'] = value
                        elif 'גובה' in key or 'height' in key:
                            dimensions['height'] = value
                    except ValueError:
                        pass
            
            # בדיקה שיש לפחות משקל או מידה אחת
            if not dimensions:
                raise ValueError("לא זוהו מידות תקינות")
            
            # שמירת המידות
            for key, value in dimensions.items():
                context.user_data['product_data'][key] = value
            
            # הצגת המידות שנשמרו
            dimensions_display = []
            if 'weight' in dimensions:
                dimensions_display.append(f"משקל: {dimensions['weight']} ק\"ג")
            if 'length' in dimensions:
                dimensions_display.append(f"אורך: {dimensions['length']} ס\"מ")
            if 'width' in dimensions:
                dimensions_display.append(f"רוחב: {dimensions['width']} ס\"מ")
            if 'height' in dimensions:
                dimensions_display.append(f"גובה: {dimensions['height']} ס\"מ")
            
            dimensions_text = ", ".join(dimensions_display)
            
            await update.message.reply_text(
                f"✅ המידות נשמרו:\n{dimensions_text}",
                parse_mode='Markdown'
            )
                    
            # המשך לשלב הבא - קטגוריות
            return await self.ask_for_categories(update, context)
                    
        except Exception as e:
            await update.message.reply_text(
                "❌ הפורמט שהזנת אינו תקין. אנא הזן את המידות בפורמט הבא:\n"
                "משקל: X ק\"ג, אורך: Y ס\"מ, רוחב: Z ס\"מ, גובה: W ס\"מ\n\n"
                "אתה יכול להזין רק חלק מהמידות, לדוגמה:\n"
                "משקל: 1.5 ק\"ג, אורך: 20 ס\"מ"
            )
            return WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS
    
    async def handle_dimensions_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לשאלה על משקל ומידות"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_dimensions":
            # המשתמש רוצה להוסיף משקל ומידות
            await query.edit_message_text(
                "📏 *הזנת משקל ומידות המוצר*\n\n"
                "אנא הזן את משקל ומידות המוצר בפורמט הבא:\n"
                "משקל: X ק\"ג, אורך: Y ס\"מ, רוחב: Z ס\"מ, גובה: W ס\"מ\n\n"
                "לדוגמה: משקל: 1.5 ק\"ג, אורך: 20 ס\"מ, רוחב: 15 ס\"מ, גובה: 10 ס\"מ\n\n"
                "💡 *טיפ:* אתה יכול להזין רק חלק מהמידות, לדוגמה רק משקל או רק אורך ורוחב.",
                        parse_mode='Markdown'
                    )
            return WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS
        else:
            # המשתמש לא רוצה להוסיף משקל ומידות, ממשיך לשלב הבא
            return await self.ask_for_categories(update, context)
    
    async def ask_for_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """שאלה על קטגוריות המוצר"""
        user_id = update.effective_user.id
        categories_text = update.message.text.strip()
        
        # פיצול קטגוריות לרשימה
        categories = [cat.strip() for cat in categories_text.split(',') if cat.strip()]
        
        # בדיקת תקינות הקטגוריות
        if not categories:
            await update.message.reply_text(
                "❌ לא זוהו קטגוריות תקינות. אנא הזן קטגוריות מופרדות בפסיקים."
            )
            return WAITING_FOR_PRODUCT_CATEGORIES
        
        # שמירת קטגוריות
        context.user_data['product_data']['categories'] = categories
        
        # יצירת סרגל התקדמות ויזואלי - הסתיים
        progress_bar = "✅✅✅✅✅✅✅"  # שלב 7 מתוך 7 - הסתיים
        
        # בקשת תמונות
        await update.message.reply_text(
            f"✅ הקטגוריות נשמרו: *{', '.join(categories)}*\n\n"
            f"{progress_bar} *שלב הבא: תמונות המוצר (אופציונלי)*\n\n"
            "עכשיו, אתה יכול לשלוח תמונות למוצר.\n"
            "אפשרויות:\n"
            "1️⃣ שלח תמונה ישירות בצ'אט\n"
            "2️⃣ שלח קישור לתמונה באינטרנט\n"
            "3️⃣ הקלד 'דלג' כדי להמשיך ללא תמונות\n\n"
            "💡 *טיפ:* תמונות איכותיות מגדילות את סיכויי המכירה! מומלץ לשלוח תמונות ברורות ובאיכות גבוהה.\n\n"
            "🔄 להתחלה מחדש: /cancel",
                        parse_mode='Markdown'
                    )
        
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_images_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בטקסט בשלב התמונות"""
        user_id = update.effective_user.id
        text = update.message.text.strip().lower()
        
        # בדיקה אם המשתמש רוצה לסיים או לדלג
        if text in ['סיום', 'סיימתי', 'finish', 'done', 'דלג', 'skip']:
            # מעבר לשלב הבא
            return await self.show_product_confirmation(update, context)
        
        # אחרת, הודעה שצריך לשלוח תמונה או לסיים
        await update.message.reply_text(
            "אנא שלח תמונות של המוצר או הקלד 'סיום' כדי להמשיך לשלב הבא."
        )
        
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_images_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תמונות המוצר"""
        user_id = update.effective_user.id
        photo = update.message.photo[-1]  # הגדול ביותר
        
        # קבלת קובץ התמונה
        file = await context.bot.get_file(photo.file_id)
        file_url = file.file_path
        
        # הוספת התמונה לרשימת התמונות
        if 'images' not in context.user_data['product_data']:
            context.user_data['product_data']['images'] = []
        
        context.user_data['product_data']['images'].append({
            'src': file_url,
            'alt': f"תמונת מוצר {len(context.user_data['product_data']['images']) + 1}"
        })
        
        # הודעה על קבלת התמונה
        await update.message.reply_text(
            f"✅ התמונה התקבלה בהצלחה! (תמונה {len(context.user_data['product_data']['images'])})\n\n"
            "תוכל לשלוח תמונות נוספות או להקליד 'סיום' כדי להמשיך לשלב הבא."
        )
        
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def handle_image_description_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לשאלה על תיאור תמונה"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_image_description":
            # המשתמש רוצה להוסיף תיאור לתמונה
            await query.edit_message_text(
                "📝 *הזנת תיאור לתמונה*\n\n"
                "אנא הזן תיאור קצר וממוקד לתמונה.\n"
                "תיאור טוב מתאר את מה שרואים בתמונה ומדגיש את התכונות החשובות של המוצר.\n\n"
                "לדוגמה: \"כיסא משרדי שחור עם משענת גב ארגונומית, מבט מהצד\"",
                parse_mode='Markdown'
            )
            context.user_data['waiting_for_image_description'] = True
            return WAITING_FOR_PRODUCT_IMAGES
        else:
            # המשתמש לא רוצה להוסיף תיאור, שואל אם רוצה להוסיף תמונות נוספות
            keyboard = [
                [InlineKeyboardButton("כן, הוסף תמונה נוספת", callback_data="add_more_images")],
                [InlineKeyboardButton("לא, המשך לאישור", callback_data="finish_images")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ התמונה נוספה בהצלחה!\n\n"
                f"האם ברצונך להוסיף תמונות נוספות?",
                reply_markup=reply_markup
            )
            return WAITING_FOR_PRODUCT_IMAGES
    
    async def ask_for_more_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """שאלה על מספר תמונות נוספות"""
        user_id = update.effective_user.id
        logfire.info('command_add_more_images', user_id=user_id)
        
        await update.message.reply_text(
            "🖼️ *הוספת תמונות נוספות*\n\n"
            "אנא הזן מספר תמונות נוספות שברצונך להוסיף.\n"
            "לדוגמה: 2 או 3 או 4 תמונות.\n\n"
            "💡 *טיפ:* מומלץ להוסיף תמונות שונות ואיכותיות כדי להגדיל את סיכויי המכירה!\n\n"
            "🔄 להתחלה מחדש: /cancel",
                parse_mode='Markdown'
            )
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def handle_more_images_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לשאלה על מספר תמונות נוספות"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_more_images":
            # המשתמש רוצה להוסיף תמונות נוספות
            await query.edit_message_text(
                "🖼️ *הוספת תמונות נוספות*\n\n"
                "אנא שלח תמונה נוספת למוצר.\n"
                "אפשרויות:\n"
                "1️⃣ שלח תמונה ישירות בצ'אט\n"
                "2️⃣ שלח קישור לתמונה באינטרנט\n\n"
                "💡 *טיפ:* מומלץ להוסיף מספר תמונות מזוויות שונות של המוצר.",
                parse_mode='Markdown'
            )
            return WAITING_FOR_PRODUCT_IMAGES
        else:
            # המשתמש רוצה להסתיים, ממשיך לשלב האישור
            return await self.show_product_confirmation(update, context)
    
    async def handle_image_description_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור לתמונה"""
        user_id = update.effective_user.id
        description_text = update.message.text.strip()
        
        # בדיקה שאנחנו מחכים לתיאור תמונה
        if not context.user_data.get('waiting_for_image_description', False):
            # אם לא מחכים לתיאור, ייתכן שזו תמונה חדשה או פקודה אחרת
            return await self.create_product_images_text(update, context)
        
        # שמירת התיאור לתמונה האחרונה
        last_image_index = context.user_data.get('last_image_index', 0)
        if 0 <= last_image_index < len(context.user_data['product_data']['images']):
            context.user_data['product_data']['images'][last_image_index]['alt'] = description_text
            
            # שמירה גם במילון התיאורים לצורך תאימות עם קוד קיים
            image_src = context.user_data['product_data']['images'][last_image_index].get('src', '')
            if image_src:
                context.user_data['product_data']['image_descriptions'][image_src] = description_text
        
        # ניקוי משתנה העזר
        context.user_data.pop('waiting_for_image_description', None)
        
        # שאלה אם רוצה להוסיף תמונות נוספות
        keyboard = [
            [InlineKeyboardButton("כן, הוסף תמונה נוספת", callback_data="add_more_images")],
            [InlineKeyboardButton("לא, המשך לאישור", callback_data="finish_images")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ תיאור התמונה נשמר בהצלחה!\n\n"
            f"האם ברצונך להוסיף תמונות נוספות?",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def show_product_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת סיכום המוצר לאישור"""
        user_id = update.effective_user.id
        
        # יצירת סרגל התקדמות ויזואלי
        progress_bar = "✅✅✅✅✅🔵"  # שלב 6 מתוך 6
        
        # פורמוט הנתונים להצגה
        product_data = context.user_data['product_data']
        
        # פונקציה לפורמוט הנתונים
        def format_product_preview(data):
            preview = f"*{data.get('name', 'ללא שם')}*\n\n"
            
            # תיאור
            description = data.get('description', '')
            if len(description) > 100:
                description = description[:97] + "..."
            preview += f"*תיאור:*\n{description}\n\n"
            
            # מחיר
            preview += f"*מחיר:* {data.get('regular_price', '0')}₪\n"
            
            # מחיר מבצע
            if 'sale_price' in data and data['sale_price']:
                preview += f"*מחיר מבצע:* {data['sale_price']}₪\n"
            
            # מק"ט
            if 'sku' in data and data['sku']:
                preview += f"*מק\"ט:* {data['sku']}\n"
            
            # מלאי
            if 'stock_quantity' in data and data['stock_quantity']:
                preview += f"*כמות במלאי:* {data['stock_quantity']} יחידות\n"
            
            # קטגוריות
            if 'categories' in data and data['categories']:
                preview += f"*קטגוריות:* {', '.join(data['categories'])}\n"
            
            # תמונות
            if 'images' in data and data['images']:
                preview += f"*תמונות:* {len(data['images'])} תמונות\n"
            
            return preview
        
        # הצגת סיכום המוצר
        product_preview = format_product_preview(product_data)
        
        # כפתורי אישור/עריכה
        keyboard = [
            [InlineKeyboardButton("✅ אישור ויצירת המוצר", callback_data='confirm_product')],
            [InlineKeyboardButton("✏️ עריכת פרטים", callback_data='edit_product')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{progress_bar} *שלב 6/6: אישור המוצר*\n\n"
            f"להלן פרטי המוצר שהזנת:\n\n"
            f"{product_preview}\n\n"
            f"האם ברצונך ליצור את המוצר עם הפרטים הללו?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_PRODUCT_CONFIRMATION
    
    async def create_product_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """יצירת המוצר לאחר אישור"""
        user_id = update.effective_user.id
        text = update.message.text.strip().lower()
        
        # בדיקה אם המשתמש אישר
        if text not in ['אישור', 'confirm', 'כן', 'yes']:
            await update.message.reply_text(
                "אם ברצונך לאשר את יצירת המוצר, אנא הקלד 'אישור'.\n"
                "אם ברצונך לערוך את פרטי המוצר, הקלד 'עריכה'.\n"
                "אם ברצונך לבטל את התהליך, הקלד /cancel."
            )
            return WAITING_FOR_PRODUCT_CONFIRMATION
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            "⏳ יוצר את המוצר... אנא המתן."
        )
        
        # קבלת נתוני המוצר
        product_data = context.user_data['product_data']
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # יצירת מנהל מוצרים
            from src.tools.managers.product_manager import ProductManager
            product_manager = ProductManager(api)
            
            # יצירת המוצר
            created_product = await product_manager.create_product(product_data)
            
            if not created_product:
                await wait_message.edit_text(
                    "❌ לא ניתן ליצור את המוצר. אנא נסה שוב או בדוק את הלוגים לפרטים נוספים."
                )
                return ConversationHandler.END
            
            # פורמוט המוצר להצגה
            from src.tools.managers.product_manager import format_product_for_display
            product_display = format_product_for_display(created_product)
            
            # הודעת הצלחה
            await wait_message.edit_text(
                f"✅ *המוצר נוצר בהצלחה!*\n\n"
                f"מזהה המוצר: {created_product.get('id')}\n"
                f"קישור לצפייה במוצר: [לחץ כאן]({created_product.get('permalink')})\n\n"
                f"{product_display}",
                parse_mode='Markdown'
            )
            
            # ניקוי נתוני המוצר
            context.user_data.pop('product_data', None)
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה ביצירת המוצר: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def handle_product_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בתשובה לאישור מוצר"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm_product":
            # המשתמש אישר את המוצר
            await query.edit_message_text(
                "🎉 תודה על האישור! המוצר נוסף בהצלחה לחנות שלך.",
                        parse_mode='Markdown'
                    )
            return ConversationHandler.END
        else:
            # המשתמש רוצה להסיק שינויים
            return await self.edit_product_details(update, context)
    
    async def edit_product_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הוספת פעולות לעריכת פרטי המוצר"""
        user_id = update.effective_user.id
        logfire.info('command_edit_product', user_id=user_id)
        
        # בדיקה אם המשתמש רוצה להוסיף תמונות נוספות
        if 'images' in context.user_data['product_data']:
            await update.message.reply_text(
                "🖼️ *הוספת תמונות נוספות*\n\n"
                "אנא הזן מספר תמונות נוספות שברצונך להוסיף.\n"
                "לדוגמה: 2 או 3 או 4 תמונות.\n\n"
                "💡 *טיפ:* מומלץ להוסיף תמונות שונות ואיכותיות כדי להגדיל את סיכויי המכירה!\n\n"
                "🔄 להתחלה מחדש: /cancel",
                parse_mode='Markdown'
            )
            return WAITING_FOR_PRODUCT_IMAGES
        
        # אם אין שינויים, ממשיך לשלב האישור 
        return await self.show_product_confirmation(update, context)

    async def handle_product_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הוספת פעולות לעריכת פרטי המוצר"""
        user_id = update.effective_user.id
        logfire.info('command_edit_product', user_id=user_id)
        
        # בדיקה איזה שדה המשתמש רוצה לערוך
        edit_text = update.message.text.strip().lower()
        
        # עדכון השדה המתאים
        if "שם" in edit_text or "name" in edit_text:
            await update.message.reply_text("אנא הזן את השם החדש למוצר:")
            context.user_data['editing_field'] = 'name'
        elif "תיאור" in edit_text or "description" in edit_text:
            await update.message.reply_text("אנא הזן את התיאור החדש למוצר:")
            context.user_data['editing_field'] = 'description'
        elif "מחיר" in edit_text or "price" in edit_text:
            await update.message.reply_text("אנא הזן את המחיר החדש למוצר:")
            context.user_data['editing_field'] = 'regular_price'
        elif "מבצע" in edit_text or "sale" in edit_text:
            await update.message.reply_text("אנא הזן את מחיר המבצע החדש למוצר:")
            context.user_data['editing_field'] = 'sale_price'
        elif "מק\"ט" in edit_text or "sku" in edit_text:
            await update.message.reply_text("אנא הזן את המק\"ט החדש למוצר:")
            context.user_data['editing_field'] = 'sku'
        elif "מלאי" in edit_text or "stock" in edit_text:
            await update.message.reply_text("אנא הזן את כמות המלאי החדשה למוצר:")
            context.user_data['editing_field'] = 'stock_quantity'
        elif "קטגוריה" in edit_text or "category" in edit_text:
            await update.message.reply_text("אנא הזן את הקטגוריות החדשות למוצר (מופרדות בפסיקים):")
            context.user_data['editing_field'] = 'categories'
        elif "תמונה" in edit_text or "image" in edit_text:
            await update.message.reply_text(
                "אנא שלח תמונה חדשה למוצר, או הקלד קישור לתמונה."
            )
            context.user_data['editing_field'] = 'images'
            return WAITING_FOR_PRODUCT_EDIT
        else:
            # אם לא זוהה שדה ספציפי, מציג את כל האפשרויות
            await update.message.reply_text(
                "איזה פרט ברצונך לערוך?\n\n"
                "אפשרויות:\n"
                "• שם המוצר\n"
                "• תיאור המוצר\n"
                "• מחיר המוצר\n"
                "• מחיר מבצע\n"
                "• מק\"ט\n"
                "• מלאי\n"
                "• קטגוריות\n"
                "• תמונות\n\n"
                "אנא הקלד את השדה שברצונך לערוך."
            )
            return WAITING_FOR_PRODUCT_EDIT
        
        return WAITING_FOR_PRODUCT_EDIT

    # פונקציות לניהול מסמכים
    
    async def add_document_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך הוספת מסמך"""
        user_id = update.effective_user.id
        logfire.info('command_add_document_start', user_id=user_id)
        
        await update.message.reply_text(
            "📄 *הוספת מסמך למאגר הידע*\n\n"
            "אנא שלח לי קובץ טקסט (TXT, PDF, DOCX, וכו') שברצונך להוסיף למאגר הידע.\n"
            "הקובץ יהיה זמין לחיפוש ולשימוש בשיחות עתידיות.\n\n"
            "לביטול התהליך, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_DOCUMENT
    
    async def add_document_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת קובץ מסמך מהמשתמש"""
        user_id = update.effective_user.id
        document = update.message.document
        file_name = document.file_name
        
        # יצירת תיקיית מסמכים אם לא קיימת
        os.makedirs('documents', exist_ok=True)
        
        # הורדת הקובץ
        file = await context.bot.get_file(document.file_id)
        file_path = f"documents/{file_name}"
        await file.download_to_drive(file_path)
        
        # שמירת מידע על הקובץ
        self.document_uploads[user_id] = {
            'file_path': file_path,
            'file_name': file_name,
            'mime_type': document.mime_type
        }
        
        logfire.info('document_received', user_id=user_id, file_name=file_name, mime_type=document.mime_type)
        
        await update.message.reply_text(
            f"✅ הקובץ *{file_name}* התקבל בהצלחה!\n\n"
            "אנא הזן כותרת או תיאור קצר למסמך זה. "
            "התיאור יעזור לזהות את המסמך בחיפושים עתידיים.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_TITLE
    
    async def add_document_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כותרת למסמך"""
        user_id = update.effective_user.id
        title = update.message.text.strip()
        
        if user_id not in self.document_uploads:
            await update.message.reply_text(
                "❌ אירעה שגיאה בתהליך העלאת המסמך. אנא נסה שוב."
            )
            return ConversationHandler.END
        
        file_info = self.document_uploads[user_id]
        file_path = file_info['file_path']
        file_name = file_info['file_name']
        
        # הוספת המסמך למאגר הידע
        try:
            # יצירת מטא-דאטה עם הכותרת
            metadata = {
                "title": title,
                "uploaded_by": user_id,
                "original_filename": file_name
            }
            
            # קריאה לפונקציה add_document_from_file
            from src.services.rag_service import RAGService
            rag_service = RAGService()
            document_id = await rag_service.add_document_from_file(
                file_path=file_path,
                title=title,
                source="telegram_upload",
                metadata=metadata
            )
            
            logfire.info('document_added', user_id=user_id, file_name=file_name, title=title, document_id=document_id)
            
            await update.message.reply_text(
                f"✅ המסמך *{file_name}* נוסף בהצלחה למאגר הידע!\n\n"
                f"כותרת: *{title}*\n\n"
                "המסמך יהיה זמין לחיפוש ולשימוש בשיחות עתידיות.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # ניקוי הקובץ הזמני
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing temporary file: {e}")
            
            # ניקוי המידע הזמני
            del self.document_uploads[user_id]
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error adding document to knowledge base: {e}")
            logfire.error('document_add_error', user_id=user_id, file_name=file_name, error=str(e))
            
            await update.message.reply_text(
                f"❌ אירעה שגיאה בהוספת המסמך למאגר הידע: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            # ניקוי הקובץ הזמני
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            
            # ניקוי המידע הזמני
            del self.document_uploads[user_id]
            
            return ConversationHandler.END
    
    # פונקציות לניהול הזמנות
    
    async def manage_orders_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול הזמנות"""
        user_id = update.effective_user.id
        logfire.info('command_manage_orders_start', user_id=user_id)
        
        # בדיקה אם המשתמש חיבר חנות
        session = await db.get_session()
        try:
            from src.handlers.store_handler import is_store_connected
            store_connected = await is_store_connected(user_id, session)
            await session.commit()
            
            if not store_connected:
                await update.message.reply_text(
                    "❌ *לא ניתן לנהל הזמנות*\n\n"
                    "עדיין לא חיברת את חנות ה-WooCommerce שלך לבוט.\n"
                    "כדי לחבר את החנות, השתמש בפקודה /connect_store.",
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            # הצגת אפשרויות ניהול הזמנות
            keyboard = [
                [InlineKeyboardButton("🔍 חיפוש הזמנה לפי מזהה", callback_data="search_order_id")],
                [InlineKeyboardButton("📊 הצגת הזמנות אחרונות", callback_data="recent_orders")],
                [InlineKeyboardButton("🔄 עדכון סטטוס הזמנה", callback_data="update_order_status")],
                [InlineKeyboardButton("❌ ביטול הזמנה", callback_data="cancel_order")],
                [InlineKeyboardButton("💰 ביצוע החזר כספי", callback_data="refund_order")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🛒 *ניהול הזמנות WooCommerce*\n\n"
                "ברוך הבא למערכת ניהול ההזמנות! מה תרצה לעשות?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return WAITING_FOR_ORDER_ID
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in manage_orders_start: {str(e)}")
            await update.message.reply_text(
                "❌ אירעה שגיאה בהתחלת תהליך ניהול ההזמנות. אנא נסה שוב מאוחר יותר."
            )
            return ConversationHandler.END
        finally:
            await session.close()
    
    async def get_order_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מזהה הזמנה"""
        user_id = update.effective_user.id
        order_id_text = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if order_id_text.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # בדיקת תקינות מזהה ההזמנה
        try:
            order_id = int(order_id_text)
            if order_id <= 0:
                raise ValueError("מזהה הזמנה חייב להיות מספר חיובי")
        except ValueError:
            await update.message.reply_text(
                "❌ מזהה הזמנה לא תקין. אנא הזן מספר חיובי (לדוגמה: 123)."
            )
            return WAITING_FOR_ORDER_ID
        
        # שמירת מזהה ההזמנה
        context.user_data['order_id'] = order_id
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            f"🔍 מחפש את הזמנה מספר {order_id}... אנא המתן."
        )
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # קבלת פרטי ההזמנה
            from src.tools.managers.order_manager import get_order
            success, message, order = await get_order(
                store_url=api.store_url,
                consumer_key=api.consumer_key,
                consumer_secret=api.consumer_secret,
                order_id=str(order_id)
            )
            
            if not success or not order:
                await wait_message.edit_text(
                    f"❌ {message}"
                )
                return ConversationHandler.END
            
            # שמירת פרטי ההזמנה
            context.user_data['order'] = order
            
            # פורמוט ההזמנה להצגה
            from src.tools.managers.order_manager import format_order_for_display
            order_display = format_order_for_display(order)
            
            # הצגת פרטי ההזמנה
            await wait_message.edit_text(
                f"✅ *נמצאה הזמנה {order_id}*\n\n"
                f"{order_display}\n\n"
                "מה תרצה לעשות עם הזמנה זו?",
                parse_mode='Markdown'
            )
            
            # הצגת אפשרויות פעולה על ההזמנה
            keyboard = [
                [InlineKeyboardButton("🔄 עדכון סטטוס", callback_data="update_status")],
                [InlineKeyboardButton("❌ ביטול הזמנה", callback_data="cancel_order")],
                [InlineKeyboardButton("💰 ביצוע החזר כספי", callback_data="refund_order")],
                [InlineKeyboardButton("📝 הוספת הערה", callback_data="add_note")],
                [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "בחר פעולה:",
                reply_markup=reply_markup
            )
            
            return WAITING_FOR_ORDER_STATUS
            
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה בקבלת פרטי ההזמנה: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def update_order_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """עדכון סטטוס הזמנה"""
        user_id = update.effective_user.id
        status_text = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if status_text.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # קבלת מזהה ההזמנה
        order_id = context.user_data.get('order_id')
        if not order_id:
            await update.message.reply_text(
                "❌ לא נמצא מזהה הזמנה. אנא התחל את התהליך מחדש."
            )
            return ConversationHandler.END
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            f"🔄 מעדכן את סטטוס הזמנה {order_id}... אנא המתן."
        )
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # עדכון סטטוס ההזמנה
            from src.tools.managers.order_manager import update_order_status as update_status
            success, message, updated_order = await update_status(
                store_url=api.store_url,
                consumer_key=api.consumer_key,
                consumer_secret=api.consumer_secret,
                order_id=str(order_id),
                status=status_text
            )
            
            if not success or not updated_order:
                await wait_message.edit_text(
                    f"❌ {message}"
                )
                return ConversationHandler.END
            
            # פורמוט ההזמנה המעודכנת להצגה
            from src.tools.managers.order_manager import format_order_for_display
            order_display = format_order_for_display(updated_order)
            
            # הצגת פרטי ההזמנה המעודכנת
            await wait_message.edit_text(
                f"✅ *הזמנה {order_id} עודכנה בהצלחה*\n\n"
                f"{order_display}",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה בעדכון ההזמנה: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def cancel_order_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סיבת ביטול הזמנה"""
        user_id = update.effective_user.id
        reason = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if reason.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # קבלת מזהה ההזמנה
        order_id = context.user_data.get('order_id')
        if not order_id:
            await update.message.reply_text(
                "❌ לא נמצא מזהה הזמנה. אנא התחל את התהליך מחדש."
            )
            return ConversationHandler.END
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            f"❌ מבטל את הזמנה {order_id}... אנא המתן."
        )
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # ביטול ההזמנה
            from src.tools.managers.order_manager import cancel_order
            success, message, updated_order = await cancel_order(
                store_url=api.store_url,
                consumer_key=api.consumer_key,
                consumer_secret=api.consumer_secret,
                order_id=str(order_id),
                reason=reason
            )
            
            if not success or not updated_order:
                await wait_message.edit_text(
                    f"❌ {message}"
                )
                return ConversationHandler.END
            
            # פורמוט ההזמנה המעודכנת להצגה
            from src.tools.managers.order_manager import format_order_for_display
            order_display = format_order_for_display(updated_order)
            
            # הצגת פרטי ההזמנה המעודכנת
            await wait_message.edit_text(
                f"✅ *הזמנה {order_id} בוטלה בהצלחה*\n\n"
                f"סיבת הביטול: {reason}\n\n"
                f"{order_display}",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה בביטול ההזמנה: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def refund_order_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סכום החזר כספי"""
        user_id = update.effective_user.id
        amount_text = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if amount_text.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # בדיקה אם המשתמש רוצה החזר מלא
        if amount_text.lower() in ["מלא", "הכל", "full", "all"]:
            context.user_data['refund_amount'] = None  # סימון להחזר מלא
            
            # מעבר לשלב הבא - סיבת ההחזר
            await update.message.reply_text(
                "✅ נבחר החזר כספי מלא.\n\n"
                "אנא הזן את סיבת ההחזר הכספי:"
            )
            
            return WAITING_FOR_ORDER_REFUND_REASON
        
        # בדיקת תקינות הסכום
        try:
            amount = float(amount_text.replace('₪', '').replace(',', '.').strip())
            if amount <= 0:
                raise ValueError("סכום ההחזר חייב להיות חיובי")
        except ValueError:
            await update.message.reply_text(
                "❌ סכום לא תקין. אנא הזן מספר חיובי (לדוגמה: 99.90) או הקלד 'מלא' להחזר מלא."
            )
            return WAITING_FOR_ORDER_REFUND_AMOUNT
        
        # שמירת סכום ההחזר
        context.user_data['refund_amount'] = amount
        
        # מעבר לשלב הבא - סיבת ההחזר
        await update.message.reply_text(
            f"✅ נבחר החזר כספי בסך {amount}₪.\n\n"
            "אנא הזן את סיבת ההחזר הכספי:"
        )
        
        return WAITING_FOR_ORDER_REFUND_REASON
    
    async def refund_order_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סיבת החזר כספי"""
        user_id = update.effective_user.id
        reason = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if reason.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # קבלת מזהה ההזמנה וסכום ההחזר
        order_id = context.user_data.get('order_id')
        amount = context.user_data.get('refund_amount')
        
        if not order_id:
            await update.message.reply_text(
                "❌ לא נמצא מזהה הזמנה. אנא התחל את התהליך מחדש."
            )
            return ConversationHandler.END
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            f"💰 מבצע החזר כספי להזמנה {order_id}... אנא המתן."
        )
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # ביצוע החזר כספי
            from src.tools.managers.order_manager import refund_order
            success, message, updated_order = await refund_order(
                store_url=api.store_url,
                consumer_key=api.consumer_key,
                consumer_secret=api.consumer_secret,
                order_id=str(order_id),
                amount=amount,
                reason=reason
            )
            
            if not success or not updated_order:
                await wait_message.edit_text(
                    f"❌ {message}"
                )
                return ConversationHandler.END
            
            # פורמוט ההזמנה המעודכנת להצגה
            from src.tools.managers.order_manager import format_order_for_display
            order_display = format_order_for_display(updated_order)
            
            # הצגת פרטי ההזמנה המעודכנת
            amount_text = f"{amount}₪" if amount is not None else "מלא"
            await wait_message.edit_text(
                f"✅ *בוצע החזר כספי {amount_text} להזמנה {order_id} בהצלחה*\n\n"
                f"סיבת ההחזר: {reason}\n\n"
                f"{order_display}",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error refunding order {order_id}: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה בביצוע ההחזר הכספי: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def filter_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """סינון הזמנות לפי פרמטרים"""
        user_id = update.effective_user.id
        filters_text = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לבטל
        if filters_text.lower() in ["ביטול", "cancel", "/cancel"]:
            await update.message.reply_text("הפעולה בוטלה.")
            return ConversationHandler.END
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            "🔍 מחפש הזמנות... אנא המתן."
        )
        
        try:
            # קבלת חיבור לחנות
            from src.handlers.store_handler import get_store_connection
            success, message, api = await get_store_connection(user_id)
            
            if not success or not api:
                await wait_message.edit_text(
                    f"❌ לא ניתן להתחבר לחנות: {message}\n\n"
                    "אנא בדוק את פרטי החיבור שלך ונסה שוב."
                )
                return ConversationHandler.END
            
            # חילוץ פרמטרים לסינון מהטקסט
            from src.tools.managers.order_manager import get_orders_from_text
            result = get_orders_from_text(filters_text)
            
            if not result["success"]:
                await wait_message.edit_text(
                    f"❌ {result['message']}"
                )
                return ConversationHandler.END
            
            # קבלת ההזמנות המסוננות
            orders = result.get("orders", [])
            
            if not orders:
                await wait_message.edit_text(
                    "❌ לא נמצאו הזמנות התואמות את החיפוש."
                )
                return ConversationHandler.END
            
            # פורמוט רשימת ההזמנות להצגה
            from src.tools.managers.order_manager import format_orders_list_for_display
            orders_display = format_orders_list_for_display(orders)
            
            # הצגת רשימת ההזמנות
            await wait_message.edit_text(
                f"✅ *נמצאו {len(orders)} הזמנות*\n\n"
                f"{orders_display}",
                parse_mode='Markdown'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error filtering orders: {str(e)}")
            
            await wait_message.edit_text(
                f"❌ אירעה שגיאה בחיפוש הזמנות: {str(e)}\n\n"
                "אנא נסה שוב מאוחר יותר."
            )
            
            return ConversationHandler.END
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בהודעות טקסט רגילות"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # לוג של ההודעה הנכנסת
        logger.info(f"Received message from user {user_id}: {message_text[:100]}")
        logfire.info('message_received', user_id=user_id, message=message_text[:100])
        
        # בדיקה אם זו הודעה ראשונה או שיחה חדשה
        is_new_conversation = False
        if 'last_activity' not in context.user_data or (datetime.now() - context.user_data.get('last_activity', datetime.now())).total_seconds() > 3600:
            # אם עברה יותר משעה מהפעילות האחרונה, נחשיב זאת כשיחה חדשה
            is_new_conversation = True
            logger.info(f"Starting new conversation for user {user_id} (timeout)")
        
        # עדכון זמן הפעילות האחרונה
        context.user_data['last_activity'] = datetime.now()
        
        # שמירת ההודעה במסד הנתונים
        session = await db.get_session()
        try:
            # קבלת או יצירת משתמש
            logger.info(f"Getting or creating user {user_id}")
            user = await get_user_by_telegram_id(user_id, session)
            
            # יצירת שיחה אם לא קיימת או אם זו שיחה חדשה
            if 'conversation_id' not in context.user_data or is_new_conversation:
                logger.info(f"Creating new conversation for user {user_id}")
                conversation = Conversation(user_id=user.id)
                session.add(conversation)
                await session.flush()
                context.user_data['conversation_id'] = conversation.id
            
            # שמירת ההודעה
            logger.info(f"Saving message from user {user_id}")
            message = Message(
                conversation_id=context.user_data['conversation_id'],
                role="user",
                content=message_text
            )
            session.add(message)
            await session.commit()
            
            # לוג של שמירת ההודעה
            logger.info(f"Saved message from user {user_id}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving message: {e}")
            logger.exception("Exception details:")
        finally:
            await session.close()
        
        # הצגת סימון הקלדה
        logger.info(f"Showing typing indicator for user {user_id}")
        self.typing_status[user_id] = True
        
        # הפעלת פונקציה אסינכרונית שתציג את סימון ההקלדה
        async def show_typing():
            try:
                while self.typing_status.get(user_id, False):
                    try:
                        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                        await asyncio.sleep(4)  # סימון ההקלדה נמשך כ-5 שניות, אז נשלח כל 4 שניות
                    except Exception as e:
                        logger.error(f"Error in typing loop: {e}")
                        break
            except Exception as e:
                logger.error(f"Error in show_typing function: {e}")
        
        # הפעלת הפונקציה ברקע
        asyncio.create_task(show_typing())
        
        try:
            # העברת ההודעה לסוכן לעיבוד
            logger.info(f"Processing message from user {user_id} with agent")
            
            # שליפת היסטוריית השיחה אם יש
            history = None
            try:
                # שימוש בפונקציה הסינכרונית של db לקבלת היסטוריית השיחה
                history = db.get_chat_history(user_id)
                logger.info(f"Retrieved chat history for user {user_id}: {len(history) if history else 0} messages")
            except Exception as db_error:
                logger.error(f"Error retrieving conversation history: {db_error}")
            
            # העברת ההיסטוריה ישירות כפרמטר
            response = await self.agent.process_message(message_text, user_id, {"history": history} if history else None)
            
            # טיפול בתשובה ארוכה מדי או עם תגיות לא תקינות
            try:
                # ניקוי התשובה מתגיות Markdown/HTML לא תקינות
                clean_response = response
                # הגבלת אורך התשובה ל-4000 תווים (מגבלת טלגרם)
                if len(clean_response) > 4000:
                    clean_response = clean_response[:3997] + "..."
                
                # שליחת התשובה למשתמש ללא parse_mode
                logger.info(f"Sending response to user {user_id}")
                await update.message.reply_text(clean_response, parse_mode=None)
            except Exception as send_error:
                logger.error(f"Error sending message: {send_error}")
                # ניסיון לשלוח הודעה פשוטה יותר במקרה של שגיאה
                try:
                    simple_response = "מצטער, אירעה שגיאה בעיבוד התשובה. אנא נסה שוב או נסח את השאלה בצורה אחרת."
                    await update.message.reply_text(simple_response, parse_mode=None)
                except Exception as simple_error:
                    logger.error(f"Error sending simple message: {simple_error}")
            
            # שמירת התשובה במסד הנתונים
            logger.info(f"Saving response for user {user_id}")
            session = await db.get_session()
            try:
                # שמירת התשובה
                message = Message(
                    conversation_id=context.user_data['conversation_id'],
                    role="assistant",
                    content=response
                )
                session.add(message)
                await session.commit()
                
                # לוג של שמירת התשובה
                logger.info(f"Saved response to user {user_id}")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving response: {e}")
                logger.exception("Exception details:")
            finally:
                await session.close()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.exception("Exception details:")
            try:
                await update.message.reply_text(
                    "מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר.",
                    parse_mode=None
                )
            except Exception as reply_error:
                logger.error(f"Error sending error message: {reply_error}")
        
        # כיבוי סימון ההקלדה
        self.typing_status[user_id] = False

    async def list_documents_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת רשימת המסמכים במאגר הידע"""
        user_id = update.effective_user.id
        logfire.info('command_list_documents', user_id=user_id)
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            "📋 מקבל רשימת מסמכים... אנא המתן."
        )
        
        try:
            # קבלת רשימת המסמכים
            from src.services.rag_service import list_documents
            documents = await list_documents()
            
            if not documents:
                await safe_edit_message(
                    wait_message,
                    "📂 *מאגר הידע*\n\n"
                    "אין מסמכים במאגר הידע כרגע.\n\n"
                    "להוספת מסמך חדש, השתמש בפקודה /add_document.",
                    parse_mode=ParseMode.MARKDOWN,
                    user_id=user_id
                )
                return
            
            # פונקציה לניקוי תווים מיוחדים ב-Markdown
            def escape_markdown(text):
                if not text:
                    return "לא ידוע"
                # החלפת תווים מיוחדים ב-Markdown
                special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in special_chars:
                    text = text.replace(char, f"\\{char}")
                return text
            
            # בניית הודעת רשימת מסמכים
            response_text = f"📂 *מאגר הידע - {len(documents)} מסמכים*\n\n"
            
            for i, doc in enumerate(documents, 1):
                # הצגת פרטי המסמך
                doc_title = escape_markdown(doc.get('title', 'ללא כותרת'))
                doc_source = escape_markdown(doc.get('source', 'לא ידוע'))
                doc_created = doc.get('created_at', 'לא ידוע')
                
                # המרת תאריך לפורמט קריא יותר אם קיים
                if doc_created and doc_created != 'לא ידוע':
                    try:
                        from datetime import datetime
                        created_date = datetime.fromisoformat(doc_created)
                        doc_created = created_date.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                
                response_text += f"*{i}. {doc_title}*\n"
                response_text += f"מקור: {doc_source}\n"
                response_text += f"נוסף בתאריך: {doc_created}\n"
                
                # הוספת מידע נוסף אם קיים
                if 'metadata' in doc and doc['metadata']:
                    if 'original_filename' in doc['metadata']:
                        filename = escape_markdown(doc['metadata']['original_filename'])
                        response_text += f"שם קובץ: {filename}\n"
                
                response_text += "\n"
            
            response_text += "לחיפוש במסמכים, השתמש בפקודה /search_documents.\n"
            response_text += "להוספת מסמך חדש, השתמש בפקודה /add_document."
            
            # בדיקה אם ההודעה ארוכה מדי
            if len(response_text) > 4000:
                # חלוקת ההודעה לחלקים קצרים יותר
                response_text = f"📂 *מאגר הידע - {len(documents)} מסמכים*\n\n"
                response_text += "רשימת המסמכים ארוכה מדי להצגה מלאה. להלן רשימה מקוצרת:\n\n"
                
                for i, doc in enumerate(documents, 1):
                    doc_title = escape_markdown(doc.get('title', 'ללא כותרת'))
                    response_text += f"{i}. {doc_title}\n"
                
                response_text += "\nלחיפוש במסמכים, השתמש בפקודה /search_documents.\n"
                response_text += "להוספת מסמך חדש, השתמש בפקודה /add_document."
            
            # שימוש בפונקציית safe_edit_message
            await safe_edit_message(
                wait_message,
                response_text,
                parse_mode=ParseMode.MARKDOWN,
                user_id=user_id
            )
            logger.info(f"Document list sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            logfire.error('list_documents_error', user_id=user_id, error=str(e))
            
            # שימוש בפונקציית safe_edit_message גם למקרה של שגיאה
            await safe_edit_message(
                wait_message,
                "❌ אירעה שגיאה בקבלת רשימת המסמכים. אנא נסה שוב מאוחר יותר.",
                user_id=user_id
            )

    async def daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        הצגת דוח יומי על ביצועי הסוכן
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # בדיקת הרשאות
        user_record = await get_user_by_telegram_id(user.id)
        if not user_record or user_record.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            await update.message.reply_text(
                "⛔ אין לך הרשאות לצפות בדוחות. רק מנהלים יכולים לצפות בדוחות ביצועים."
            )
            return
        
        # שליחת הודעת טעינה
        loading_message = await update.message.reply_text("⏳ מייצר דוח יומי, אנא המתן...")
        
        try:
            # יצירת הדוח
            report = await self.agent.generate_report(report_type="daily")
            
            # שליחת הדוח
            await safe_edit_message(loading_message, report, parse_mode=ParseMode.MARKDOWN, user_id=user.id)
            
            # תיעוד
            logfire.info("daily_report_generated", user_id=user.id)
            
        except Exception as e:
            error_message = f"⚠️ אירעה שגיאה בעת יצירת הדוח: {str(e)}"
            await safe_edit_message(loading_message, error_message, user_id=user.id)
            logfire.error("daily_report_error", error=str(e), traceback=traceback.format_exc())
    
    async def weekly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        הצגת דוח שבועי על ביצועי הסוכן
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # בדיקת הרשאות
        user_record = await get_user_by_telegram_id(user.id)
        if not user_record or user_record.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            await update.message.reply_text(
                "⛔ אין לך הרשאות לצפות בדוחות. רק מנהלים יכולים לצפות בדוחות ביצועים."
            )
            return
        
        # שליחת הודעת טעינה
        loading_message = await update.message.reply_text("⏳ מייצר דוח שבועי, אנא המתן...")
        
        try:
            # יצירת הדוח
            report = await self.agent.generate_report(report_type="weekly")
            
            # שליחת הדוח
            await safe_edit_message(loading_message, report, parse_mode=ParseMode.MARKDOWN, user_id=user.id)
            
            # תיעוד
            logfire.info("weekly_report_generated", user_id=user.id)
            
        except Exception as e:
            error_message = f"⚠️ אירעה שגיאה בעת יצירת הדוח: {str(e)}"
            await safe_edit_message(loading_message, error_message, user_id=user.id)
            logfire.error("weekly_report_error", error=str(e), traceback=traceback.format_exc())
    
    async def monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        הצגת דוח חודשי על ביצועי הסוכן
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # בדיקת הרשאות
        user_record = await get_user_by_telegram_id(user.id)
        if not user_record or user_record.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            await update.message.reply_text(
                "⛔ אין לך הרשאות לצפות בדוחות. רק מנהלים יכולים לצפות בדוחות ביצועים."
            )
            return
        
        # שליחת הודעת טעינה
        loading_message = await update.message.reply_text("⏳ מייצר דוח חודשי, אנא המתן...")
        
        try:
            # יצירת הדוח
            report = await self.agent.generate_report(report_type="monthly")
            
            # שליחת הדוח
            await safe_edit_message(loading_message, report, parse_mode=ParseMode.MARKDOWN, user_id=user.id)
            
            # תיעוד
            logfire.info("monthly_report_generated", user_id=user.id)
            
        except Exception as e:
            error_message = f"⚠️ אירעה שגיאה בעת יצירת הדוח: {str(e)}"
            await safe_edit_message(loading_message, error_message, user_id=user.id)
            logfire.error("monthly_report_error", error=str(e), traceback=traceback.format_exc())
    
    async def update_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        עדכון אוטומטי של מילות מפתח
        """
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # בדיקת הרשאות
        user_record = await get_user_by_telegram_id(user.id)
        if not user_record or user_record.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            await update.message.reply_text(
                "⛔ אין לך הרשאות לעדכן מילות מפתח. רק מנהלים יכולים לעדכן מילות מפתח."
            )
            return
        
        # שליחת הודעת טעינה
        loading_message = await update.message.reply_text("⏳ מעדכן מילות מפתח, אנא המתן...")
        
        try:
            # קבלת ציון מינימלי מהפרמטרים (אם יש)
            min_score = 0.5  # ברירת מחדל
            if context.args and len(context.args) > 0:
                try:
                    min_score = float(context.args[0])
                except ValueError:
                    await update.message.reply_text(
                        "⚠️ ערך לא תקין לציון מינימלי. משתמש בערך ברירת המחדל (0.5)."
                    )
            
            # עדכון מילות המפתח
            result = await self.agent.update_keywords(min_score=min_score)
            
            # שליחת התוצאה
            await safe_edit_message(loading_message, result, parse_mode=ParseMode.MARKDOWN, user_id=user.id)
            
            # תיעוד
            logfire.info("keywords_updated", user_id=user.id, min_score=min_score)
            
        except Exception as e:
            logfire.error(f"Error updating keywords: {str(e)}", user_id=user.id, error=str(e))
            await safe_edit_message(loading_message, f"שגיאה בעדכון מילות המפתח: {str(e)}", user_id=user.id)

    # מתודות אדמין שקוראות למתודות המקוריות מקובץ admin_handler.py
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_command(update, context, session)
    
    async def handle_admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_users(update, context, session)
    
    async def handle_admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_stats(update, context, session)
    
    async def handle_admin_docs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_docs(update, context, session)
    
    async def handle_admin_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_models(update, context, session)
    
    async def handle_admin_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_config(update, context, session)
    
    async def handle_admin_notify(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_notify(update, context, session)
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-admin_handler"""
        async with db.get_session() as session:
            await handle_admin_callback(update, context, session)
    
    # מתודות חנות שקוראות למתודות המקוריות מקובץ store_handler.py
    async def handle_store_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_dashboard(update, context, session)
    
    async def handle_store_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_products(update, context, session)
    
    async def handle_store_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_orders(update, context, session)
    
    async def handle_store_customers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_customers(update, context, session)
    
    async def handle_store_inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_inventory(update, context, session)
    
    async def handle_store_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        async with db.get_session() as session:
            await handle_store_callback(update, context, session)
    
    async def handle_connect_store_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """מעביר את הקריאה למתודה המקורית ב-store_handler"""
        return await handle_connect_store_start(update, context)