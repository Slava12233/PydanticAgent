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
    WooCommerceStore,
    WooCommerceProduct as Product,
    WooCommerceOrder as Order,
    WooCommerceCustomer as Customer,
    WooCommercePayment as Payment
)
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.utils import (
    format_price,
    format_date,
    format_number,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message,
    escape_markdown_v2
)

# Configure logging
logger = setup_logger('telegram_bot_store')

# מצבי שיחה
(
    WAITING_FOR_STORE_ACTION,
    WAITING_FOR_STORE_URL,
    WAITING_FOR_STORE_NAME,
    WAITING_FOR_CONSUMER_KEY,
    WAITING_FOR_CONSUMER_SECRET,
    WAITING_FOR_STORE_CONFIRMATION,
    WAITING_FOR_STORE_SETTINGS
) = range(7)

class TelegramBotStore:
    """
    מחלקה לניהול החנות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_connect_store_handler(self) -> ConversationHandler:
        """
        יצירת handler לחיבור חנות חדשה
        
        Returns:
            ConversationHandler מוגדר לחיבור חנות
        """
        return ConversationHandler(
            entry_points=[CommandHandler("connect_store", self.start_connect_store)],
            states={
                WAITING_FOR_STORE_URL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.store_url)
                ],
                WAITING_FOR_STORE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.store_name)
                ],
                WAITING_FOR_CONSUMER_KEY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.consumer_key)
                ],
                WAITING_FOR_CONSUMER_SECRET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.consumer_secret)
                ],
                WAITING_FOR_STORE_CONFIRMATION: [
                    CallbackQueryHandler(self.connect_store_confirmation)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def start_connect_store(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך חיבור חנות"""
        user_id = update.effective_user.id
        
        # איפוס נתוני החנות
        context.user_data['store'] = {
            'store_url': '',
            'store_name': '',
            'consumer_key': '',
            'consumer_secret': ''
        }
        
        await update.message.reply_text(
            "בוא נחבר את חנות ה-WooCommerce שלך! 🏪\n\n"
            "ראשית, מהי כתובת האתר של החנות שלך?\n"
            "לדוגמה: https://mystore.com",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_STORE_URL
    
    async def store_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כתובת האתר של החנות"""
        store_url = update.message.text.strip()
        
        # בדיקת תקינות הכתובת
        if not store_url.startswith(('http://', 'https://')):
            await update.message.reply_text(
                format_warning_message(
                    "כתובת האתר חייבת להתחיל ב-http:// או https://\n"
                    "אנא נסה שוב."
                ),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_STORE_URL
        
        context.user_data['store']['store_url'] = store_url
        
        await update.message.reply_text(
            "מצוין! עכשיו, מהו השם של החנות שלך?",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_STORE_NAME
    
    async def store_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם החנות"""
        store_name = update.message.text.strip()
        context.user_data['store']['store_name'] = store_name
        
        await update.message.reply_text(
            "יופי! עכשיו אנחנו צריכים את מפתח ה-Consumer Key של WooCommerce.\n\n"
            "אם אינך יודע איך להשיג אותו, עקוב אחר ההוראות הבאות:\n"
            "1. היכנס לממשק הניהול של WordPress\n"
            "2. לך ל-WooCommerce > הגדרות > מתקדם > REST API\n"
            "3. לחץ על 'הוסף מפתח'\n"
            "4. תן לו שם (למשל 'Telegram Bot') והרשאות 'קריאה/כתיבה'\n"
            "5. לחץ על 'צור מפתח API'\n"
            "6. העתק את ה-Consumer Key",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_CONSUMER_KEY
    
    async def consumer_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מפתח הצרכן של WooCommerce"""
        consumer_key = update.message.text.strip()
        context.user_data['store']['consumer_key'] = consumer_key
        
        await update.message.reply_text(
            "כמעט סיימנו! עכשיו אנחנו צריכים את ה-Consumer Secret.\n"
            "זה מופיע באותו מסך שבו קיבלת את ה-Consumer Key.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_CONSUMER_SECRET
    
    async def consumer_secret(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת הסוד הצרכני של WooCommerce"""
        consumer_secret = update.message.text.strip()
        context.user_data['store']['consumer_secret'] = consumer_secret
        
        # הצגת סיכום הפרטים
        store = context.user_data['store']
        summary = (
            "*סיכום פרטי החנות:*\n\n"
            f"כתובת אתר: {store['store_url']}\n"
            f"שם החנות: {store['store_name']}\n"
            f"Consumer Key: {'*****' + store['consumer_key'][-4:] if store['consumer_key'] else 'לא סופק'}\n"
            f"Consumer Secret: {'*****' + store['consumer_secret'][-4:] if store['consumer_secret'] else 'לא סופק'}\n\n"
            "האם לשמור את פרטי החנות?"
        )
        
        keyboard = [[
            InlineKeyboardButton("כן, שמור", callback_data="save_store"),
            InlineKeyboardButton("לא, בטל", callback_data="cancel_store")
        ]]
        
        await update.message.reply_text(
            summary,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_STORE_CONFIRMATION
    
    async def connect_store_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """אישור חיבור החנות"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "save_store":
            try:
                store_data = context.user_data['store']
                user_id = update.effective_user.id
                
                async with db.get_session() as session:
                    # קבלת המשתמש לפי מזהה הטלגרם
                    user = await session.scalar(
                        db.select(User)
                        .where(User.telegram_id == user_id)
                    )
                    
                    if not user:
                        await query.edit_message_text(
                            format_error_message(
                                "לא נמצא משתמש במערכת. אנא פנה למנהל המערכת."
                            ),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                        return ConversationHandler.END
                    
                    # בדיקה אם כבר יש חנות למשתמש
                    existing_store = await session.scalar(
                        db.select(WooCommerceStore)
                        .where(WooCommerceStore.user_id == user.id)
                    )
                    
                    if existing_store:
                        await query.edit_message_text(
                            format_warning_message(
                                "כבר יש לך חנות מחוברת.\n"
                                "אנא מחק אותה תחילה אם ברצונך ליצור חנות חדשה."
                            ),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                        return ConversationHandler.END
                    
                    # יצירת החנות
                    store = WooCommerceStore(
                        store_url=store_data['store_url'],
                        store_name=store_data['store_name'],
                        consumer_key=store_data['consumer_key'],
                        consumer_secret=store_data['consumer_secret'],
                        user_id=user.id
                    )
                    session.add(store)
                    await session.commit()
                
                await query.edit_message_text(
                    format_success_message("החנות נוצרה בהצלחה! 🎉\n"
                    "אתה יכול להתחיל להוסיף מוצרים בעזרת הפקודה /create_product."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
            except Exception as e:
                logger.error(f"Error saving store: {e}")
                error_message = str(e)
                # מנקה תווים מיוחדים של Markdown מהודעת השגיאה
                error_message = error_message.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בשמירת החנות: {error_message}"),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            
        elif query.data == "cancel_store":
            await query.edit_message_text(
                format_info_message("יצירת החנות בוטלה."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def handle_store_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בלוח הבקרה של החנות"""
        user_id = update.effective_user.id
        logger.info(f"Store dashboard command from user {user_id}")
        
        try:
            async with db.get_session() as session:
                # קבלת המשתמש לפי מזהה הטלגרם
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == user_id)
                )
                
                if not user:
                    await update.message.reply_text(
                        format_error_message(
                            "לא נמצא משתמש במערכת. אנא פנה למנהל המערכת."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
                
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(WooCommerceStore)
                    .where(WooCommerceStore.user_id == user.id)
                )
                
                if not store:
                    await update.message.reply_text(
                        format_warning_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אתה יכול ליצור חנות חדשה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
                
                # חישוב סטטיסטיקות
                total_products = await session.scalar(
                    db.select(db.func.count(Product.id))
                    .where(Product.store_id == store.id)
                )
                
                total_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                    .where(Order.store_id == store.id)
                )
                
                total_revenue = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                    .where(Order.store_id == store.id)
                )
                
                # בניית הודעת לוח בקרה
                store_name_escaped = escape_markdown_v2(store.store_name)
                store_url_escaped = escape_markdown_v2(store.store_url)
                total_products_formatted = escape_markdown_v2(format_number(total_products))
                total_orders_formatted = escape_markdown_v2(format_number(total_orders))
                total_revenue_formatted = escape_markdown_v2(format_price(total_revenue or 0))
                
                message = (
                    f"🏪 *{store_name_escaped} \\- לוח בקרה*\n\n"
                    "*סטטיסטיקות:*\n"
                    f"• מוצרים: {total_products_formatted}\n"
                    f"• הזמנות: {total_orders_formatted}\n"
                    f"• הכנסות: {total_revenue_formatted}\n\n"
                    "*פרטי החנות:*\n"
                    f"🌐 אתר: {store_url_escaped}\n"
                    f"📞 טלפון: \n"
                    f"📧 אימייל: \n"
                    f"📍 כתובת: \n\n"
                    f"*תיאור:*\n"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("ערוך פרטי חנות", callback_data="edit_store"),
                        InlineKeyboardButton("הגדרות חנות", callback_data="store_settings")
                    ],
                    [
                        InlineKeyboardButton("ניהול מוצרים", callback_data="manage_products"),
                        InlineKeyboardButton("ניהול הזמנות", callback_data="manage_orders")
                    ],
                    [
                        InlineKeyboardButton("סטטיסטיקות מפורטות", callback_data="detailed_stats")
                    ]
                ]
                
                # שליחת ההודעה
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing store dashboard: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בהצגת לוח הבקרה."),
                parse_mode=ParseMode.MARKDOWN_V2
            ) 