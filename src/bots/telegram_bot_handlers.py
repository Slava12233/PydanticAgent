import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from sqlalchemy import select
from datetime import datetime

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
                
                welcome_message = (
                    f"👋 *ברוך הבא {user.first_name}!*\n\n"
                    "אני בוט AI חכם שיכול לעזור לך בניהול חנות ה-WooCommerce שלך.\n\n"
                    "🛍️ *מה אני יכול לעשות?*\n"
                    "• ניהול מוצרים והזמנות\n"
                    "• מעקב אחר מלאי ומכירות\n"
                    "• ניתוח נתונים וסטטיסטיקות\n"
                    "• שמירת מסמכים ומידע\n"
                    "• מענה על שאלות בעברית\n\n"
                    "🏪 *חיבור החנות:*\n"
                    "כדי להתחיל, השתמש בפקודה /connect_store לחיבור חנות ה-WooCommerce שלך.\n\n"
                    "📚 *מערכת המסמכים:*\n"
                    "אני תומך במגוון סוגי קבצים כולל PDF, Word, Excel ועוד.\n"
                    "השתמש בפקודה /add_document כדי להתחיל.\n\n"
                    "הקלד /help לרשימת כל הפקודות הזמינות."
                )
                
                await update.message.reply_text(
                    format_success_message(welcome_message),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # משתמש קיים
                welcome_back_message = (
                    f"👋 *ברוך הבא בחזרה {user.first_name}!*\n\n"
                    "מה תרצה לעשות היום?\n\n"
                    "🏪 *ניהול החנות:*\n"
                    "• /store_dashboard - לוח בקרה\n"
                    "• /manage_products - ניהול מוצרים\n"
                    "• /manage_orders - ניהול הזמנות\n\n"
                    "📊 *סטטיסטיקות ומידע:*\n"
                    "• /stats - נתוני החנות\n"
                    "• /search - חיפוש במאגר הידע\n\n"
                    "הקלד /help לרשימת כל הפקודות הזמינות."
                )
                
                await update.message.reply_text(
                    format_info_message(welcome_back_message),
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
        if not update.message or not update.message.text:
            return

        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.info(f"Received message from user {user_id}: {message_text[:50]}...")
        
        # שמירת ההודעה במסד הנתונים
        async with db.get_session() as session:
            user = await get_user_by_telegram_id(user_id, session)
            if not user:
                logger.error(f"User {user_id} not found")
                return

            try:
                # מציאת שיחה פעילה
                conversation = await session.execute(
                    select(Conversation)
                    .where(Conversation.user_id == user.id)
                    .where(Conversation.is_active == True)
                    .order_by(Conversation.updated_at.desc())
                )
                conversation = conversation.scalar_one_or_none()
                
                # אם אין שיחה פעילה, נבדוק אם יש שיחה לא פעילה מהיום
                if not conversation:
                    today = datetime.now().date()
                    conversation = await session.execute(
                        select(Conversation)
                        .where(Conversation.user_id == user.id)
                        .where(Conversation.created_at >= today)
                        .order_by(Conversation.updated_at.desc())
                    )
                    conversation = conversation.scalar_one_or_none()
                    
                    # אם נמצאה שיחה מהיום, נפעיל אותה מחדש
                    if conversation:
                        conversation.is_active = True
                        await session.commit()
                        logger.info(f"Reactivated conversation {conversation.id} for user {user_id}")
                    else:
                        # אם אין שיחה מהיום, ניצור חדשה
                        conversation = Conversation(
                            user_id=user.id,
                            title="שיחה חדשה",
                            is_active=True
                        )
                        session.add(conversation)
                        await session.commit()
                        logger.info(f"Created new conversation with ID {conversation.id} for user {user_id}")

                # עדכון זמן העדכון האחרון של השיחה
                conversation.updated_at = datetime.now()
                await session.commit()

                # העברת ההודעה לטיפול הסוכן עם מזהה השיחה
                response_text = await self.bot.agent.handle_message(
                    user_id=user_id,
                    message_text=message_text,
                    conversation_id=conversation.id
                )
                
                # שליחת התשובה למשתמש
                await update.message.reply_text(response_text)
                
            except Exception as e:
                logger.error(f"Error processing message with agent: {str(e)}")
                await update.message.reply_text(
                    format_error_message("מצטער, אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב.")
                )
            
            await session.commit()  # שמירת כל השינויים
    
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