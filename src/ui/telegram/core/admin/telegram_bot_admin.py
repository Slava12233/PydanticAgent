import logging
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from telegram.constants import ParseMode

from src.database.database import db
from src.models.database import (
    User,
    WooCommerceStore as Store,
    WooCommerceProduct as Product,
    WooCommerceOrder as Order,
    WooCommerceCategory as Category
)
from src.services.database.users import UserManager
from src.core.config import ADMIN_USER_ID, ADMIN_COMMANDS
from src.utils.logger import setup_logger
from src.ui.telegram.utils.telegram_bot_utils import (
    format_price,
    format_date,
    format_number,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message
)

# Configure logging
logger = setup_logger('telegram_bot_admin')

# מצבי שיחה
(
    WAITING_FOR_ADMIN_ACTION,
    WAITING_FOR_USER_ID,
    WAITING_FOR_USER_ROLE,
    WAITING_FOR_BACKUP_TYPE,
    WAITING_FOR_RESTORE_FILE,
    WAITING_FOR_CONFIRMATION,
    WAITING_FOR_BROADCAST_MESSAGE,
    WAITING_FOR_MAINTENANCE_MODE
) = range(8)

class TelegramBotAdmin:
    """
    מחלקה לניהול פונקציות מתקדמות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בפקודות מנהל"""
        user_id = update.effective_user.id
        command = update.message.text.split()[0][1:]  # הסרת ה-/ מתחילת הפקודה
        
        # בדיקה שהמשתמש הוא מנהל
        if user_id != ADMIN_USER_ID:
            logger.warning(f"Unauthorized admin command attempt from user {user_id}")
            await update.message.reply_text(
                format_error_message("אין לך הרשאות לבצע פעולה זו."),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        logger.info(f"Admin command {command} from user {user_id}")
        
        # טיפול בפקודות שונות
        if command == "system_stats":
            await self.show_system_stats(update, context)
        elif command == "manage_users":
            await self.show_user_management(update, context)
        elif command == "backup":
            await self.start_backup(update, context)
        elif command == "restore":
            await self.start_restore(update, context)
        elif command == "broadcast":
            await self.start_broadcast(update, context)
        elif command == "maintenance":
            await self.toggle_maintenance_mode(update, context)
        elif command == "logs":
            await self.show_logs(update, context)
    
    async def show_system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת סטטיסטיקות מערכת"""
        try:
            async with db.get_session() as session:
                # סטטיסטיקות משתמשים
                total_users = await session.scalar(
                    db.select(db.func.count(User.id))
                )
                active_users = await session.scalar(
                    db.select(db.func.count(User.id))
                    .where(User.is_active == True)
                )
                
                # סטטיסטיקות חנויות
                total_stores = await session.scalar(
                    db.select(db.func.count(Store.id))
                )
                active_stores = await session.scalar(
                    db.select(db.func.count(Store.id))
                    .where(Store.is_active == True)
                )
                
                # סטטיסטיקות מוצרים
                total_products = await session.scalar(
                    db.select(db.func.count(Product.id))
                )
                total_categories = await session.scalar(
                    db.select(db.func.count(Category.id))
                )
                
                # סטטיסטיקות הזמנות
                total_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                )
                total_revenue = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                )
                
                # חישוב ממוצעים
                avg_products_per_store = total_products / total_stores if total_stores > 0 else 0
                avg_orders_per_store = total_orders / total_stores if total_stores > 0 else 0
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
                
                message = (
                    "📊 *סטטיסטיקות מערכת*\n\n"
                    "*משתמשים:*\n"
                    f"• סה\"כ משתמשים: {format_number(total_users)}\n"
                    f"• משתמשים פעילים: {format_number(active_users)}\n"
                    f"• אחוז פעילים: {(active_users/total_users*100 if total_users > 0 else 0):.1f}%\n\n"
                    "*חנויות:*\n"
                    f"• סה\"כ חנויות: {format_number(total_stores)}\n"
                    f"• חנויות פעילות: {format_number(active_stores)}\n"
                    f"• אחוז פעילות: {(active_stores/total_stores*100 if total_stores > 0 else 0):.1f}%\n\n"
                    "*מוצרים:*\n"
                    f"• סה\"כ מוצרים: {format_number(total_products)}\n"
                    f"• קטגוריות: {format_number(total_categories)}\n"
                    f"• ממוצע למוצרים לחנות: {avg_products_per_store:.1f}\n\n"
                    "*הזמנות:*\n"
                    f"• סה\"כ הזמנות: {format_number(total_orders)}\n"
                    f"• סה\"כ הכנסות: {format_price(total_revenue or 0)}\n"
                    f"• ממוצע הזמנות לחנות: {avg_orders_per_store:.1f}\n"
                    f"• ממוצע לסכום הזמנה: {format_price(avg_order_value)}\n"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("ניהול משתמשים", callback_data="admin_manage_users"),
                        InlineKeyboardButton("ניהול חנויות", callback_data="admin_manage_stores")
                    ],
                    [
                        InlineKeyboardButton("גיבוי מערכת", callback_data="admin_backup"),
                        InlineKeyboardButton("שחזור מערכת", callback_data="admin_restore")
                    ],
                    [
                        InlineKeyboardButton("הודעה גלובלית", callback_data="admin_broadcast"),
                        InlineKeyboardButton("מצב תחזוקה", callback_data="admin_maintenance")
                    ]
                ]
                
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing system stats: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בהצגת הסטטיסטיקות."),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def show_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת ממשק ניהול משתמשים"""
        try:
            async with db.get_session() as session:
                # קבלת רשימת המשתמשים האחרונים
                recent_users = await session.scalars(
                    db.select(User)
                    .order_by(User.created_at.desc())
                    .limit(10)
                )
                users = list(recent_users)
                
                message = "👥 *ניהול משתמשים*\n\n*משתמשים אחרונים:*\n\n"
                
                for user in users:
                    message += (
                        f"🔹 *{user.username or 'ללא שם משתמש'}*\n"
                        f"ID: `{user.id}`\n"
                        f"נוצר: {format_date(user.created_at)}\n"
                        f"סטטוס: {'✅ פעיל' if user.is_active else '❌ לא פעיל'}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("חפש משתמש", callback_data="admin_search_user"),
                        InlineKeyboardButton("חסום משתמש", callback_data="admin_block_user")
                    ],
                    [
                        InlineKeyboardButton("שנה הרשאות", callback_data="admin_change_role"),
                        InlineKeyboardButton("מחק משתמש", callback_data="admin_delete_user")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="admin_back_to_menu")
                    ]
                ]
                
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing user management: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בהצגת ניהול המשתמשים."),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def start_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """התחלת תהליך גיבוי"""
        keyboard = [
            [
                InlineKeyboardButton("גיבוי מלא", callback_data="backup_full"),
                InlineKeyboardButton("גיבוי נתונים", callback_data="backup_data")
            ],
            [
                InlineKeyboardButton("גיבוי הגדרות", callback_data="backup_settings"),
                InlineKeyboardButton("גיבוי קבצים", callback_data="backup_files")
            ]
        ]
        
        await update.message.reply_text(
            "💾 *גיבוי מערכת*\n\n"
            "בחר את סוג הגיבוי הרצוי:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def start_restore(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """התחלת תהליך שחזור"""
        await update.message.reply_text(
            "📥 *שחזור מערכת*\n\n"
            "אנא שלח את קובץ הגיבוי לשחזור.\n"
            "*שים לב:* פעולה זו תחליף את כל הנתונים הקיימים!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """התחלת תהליך שליחת הודעה גלובלית"""
        await update.message.reply_text(
            "📢 *הודעה גלובלית*\n\n"
            "אנא הזן את ההודעה שברצונך לשלוח לכל המשתמשים.\n"
            "ניתן להשתמש בעיצוב Markdown.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def toggle_maintenance_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הפעלת/כיבוי מצב תחזוקה"""
        keyboard = [
            [
                InlineKeyboardButton("הפעל מצב תחזוקה", callback_data="maintenance_on"),
                InlineKeyboardButton("כבה מצב תחזוקה", callback_data="maintenance_off")
            ]
        ]
        
        await update.message.reply_text(
            "🔧 *מצב תחזוקה*\n\n"
            "בחר את הפעולה הרצויה:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת לוגים אחרונים"""
        try:
            # קריאת 50 השורות האחרונות מקובץ הלוג
            with open('logs/bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]
            
            message = "📋 *לוגים אחרונים:*\n\n```\n"
            message += "".join(lines)
            message += "```"
            
            # שליחת הלוגים כקובץ אם הם ארוכים מדי
            if len(message) > 4000:
                with open('logs/recent.log', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                await update.message.reply_document(
                    document=open('logs/recent.log', 'rb'),
                    caption="📋 לוגים אחרונים",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN
                )
            
        except Exception as e:
            logger.error(f"Error showing logs: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בהצגת הלוגים."),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בקריאות callback של מנהל"""
        query = update.callback_query
        await query.answer()
        
        # בדיקה שהמשתמש הוא מנהל
        if query.from_user.id != ADMIN_USER_ID:
            logger.warning(f"Unauthorized admin callback attempt from user {query.from_user.id}")
            await query.edit_message_text(
                format_error_message("אין לך הרשאות לבצע פעולה זו."),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        action = query.data.split('_')[1]
        
        if action == "manage_users":
            await self.show_user_management(update, context)
        elif action == "backup":
            await self.start_backup(update, context)
        elif action == "restore":
            await self.start_restore(update, context)
        elif action == "broadcast":
            await self.start_broadcast(update, context)
        elif action == "maintenance":
            await self.toggle_maintenance_mode(update, context)
        elif action == "back_to_menu":
            await self.show_system_stats(update, context) 