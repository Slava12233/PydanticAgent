import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.core.config import ALLOWED_COMMANDS
from src.database import db
from src.database.models import User, Conversation, Message
from src.database.operations import get_user_by_telegram_id, create_user
from src.utils.logger import setup_logger, log_telegram_message
from .telegram_bot_utils import (
    format_success_message,
    format_error_message,
    format_info_message,
    format_warning_message
)

# Configure logging
logger = setup_logger('telegram_bot_handlers')

class TelegramBotHandlers:
    """
    מחלקה לטיפול בפקודות בסיסיות של הבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת start"""
        user_id = update.effective_user.id
        logger.info(f"Start command from user {user_id} ({update.effective_user.username})")
        
        async with db.get_session() as session:
            user = await get_user_by_telegram_id(user_id, session)
            
            if not user:
                # יצירת משתמש חדש
                user = await create_user(
                    session,
                    telegram_id=user_id,
                    username=update.effective_user.username or '',
                    first_name=update.effective_user.first_name or '',
                    last_name=update.effective_user.last_name or ''
                )
                
                if not user:
                    await update.message.reply_text(
                        format_error_message("אירעה שגיאה ביצירת המשתמש. אנא נסה שוב מאוחר יותר."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                await update.message.reply_text(
                    format_success_message(
                        "ברוך הבא! המשתמש נוצר בהצלחה.\n"
                        "השתמש בפקודת /help כדי לראות את הפקודות הזמינות."
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # משתמש קיים
                await update.message.reply_text(
                    format_info_message(
                        f"ברוך הבא בחזרה {user.first_name}!\n"
                        "השתמש בפקודת /help כדי לראות את הפקודות הזמינות."
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
        return True
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת help"""
        user_id = update.effective_user.id
        logger.info(f"Help command from user {user_id}")
        
        help_message = (
            "*🤖 פקודות זמינות:*\n\n"
            "🏪 *ניהול חנות:*\n"
            "/store_dashboard - לוח בקרה של החנות\n"
            "/connect_store - חיבור חנות חדשה\n\n"
            "📦 *ניהול מוצרים:*\n"
            "/create_product - יצירת מוצר חדש\n"
            "/manage_products - ניהול מוצרים\n\n"
            "📝 *ניהול הזמנות:*\n"
            "/manage_orders - ניהול הזמנות\n"
            "/order_stats - סטטיסטיקות הזמנות\n\n"
            "📚 *מאגר ידע:*\n"
            "/add_document - הוספת מסמך למאגר\n"
            "/search - חיפוש במאגר הידע\n"
            "/list_documents - רשימת מסמכים\n\n"
            "📊 *כללי:*\n"
            "/stats - הצגת סטטיסטיקות\n"
            "/clear - ניקוי היסטוריית שיחה\n"
            "/help - הצגת עזרה זו\n"
        )
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
        await log_telegram_message(update.message, "help", help_message)
        return True
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת clear"""
        user_id = update.effective_user.id
        logger.info(f"Clear command from user {user_id}")
        
        async with db.get_session() as session:
            # מחיקת כל ההודעות של המשתמש
            await session.execute(
                Message.__table__.delete().where(Message.user_id == user_id)
            )
            await session.commit()
        
        await update.message.reply_text("היסטוריית השיחה נמחקה בהצלחה! 🗑")
        await log_telegram_message(update.message, "clear")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודת stats"""
        user_id = update.effective_user.id
        logger.info(f"Stats command from user {user_id}")
        
        try:
            async with db.get_session() as session:
                # קבלת סטטיסטיקות כלליות
                message_count = await session.scalar(
                    db.select(db.func.count(Message.id))
                )
                user_count = await session.scalar(
                    db.select(db.func.count(User.id))
                )
                
                # סטטיסטיקות של המשתמש הנוכחי
                user_message_count = await session.scalar(
                    db.select(db.func.count(Message.id))
                    .where(Message.user_id == user_id)
                )
            
            stats_message = (
                "📊 *סטטיסטיקות המערכת:*\n\n"
                f"סה\"כ הודעות במערכת: {message_count}\n"
                f"מספר משתמשים ייחודיים: {user_count}\n\n"
                f"*הסטטיסטיקות שלך:*\n"
                f"מספר ההודעות שלך: {user_message_count}\n"
            )
            
            await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
            await log_telegram_message(update.message, "stats")
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text(
                "אירעה שגיאה בהצגת הסטטיסטיקות. אנא נסה שוב מאוחר יותר."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בהודעות טקסט רגילות"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.info(f"Received message from user {user_id}: {message_text[:50]}...")
        
        # שמירת ההודעה במסד הנתונים
        async with db.get_session() as session:
            user = await get_user_by_telegram_id(session, user_id)
            if user:
                message = Message(
                    user_id=user.id,
                    content=message_text,
                    direction='incoming'
                )
                session.add(message)
                await session.commit()
        
        # העברת ההודעה לטיפול של ה-agent
        response = await self.bot.conversations.process_message(update, context)
        if response:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בקריאות callback"""
        query = update.callback_query
        data = query.data
        
        logger.info(f"Received callback query: {data}")
        
        # העברת הקריאה למודול המתאים
        if data.startswith('store_'):
            await self.bot.store.handle_store_callback(update, context)
        elif data.startswith('product_'):
            await self.bot.products.handle_product_callback(update, context)
        elif data.startswith('order_'):
            await self.bot.orders.handle_order_callback(update, context)
        elif data.startswith('admin_'):
            await self.bot.admin.handle_admin_callback(update, context)
        else:
            logger.warning(f"Unknown callback query: {data}")
            await query.answer("פעולה לא מוכרת") 