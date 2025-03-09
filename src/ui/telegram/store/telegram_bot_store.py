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
    WooCommerceCustomer as Customer,
    WooCommercePayment as Payment
)
from src.services.database.users import UserManager
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
logger = setup_logger('telegram_bot_store')

# מצבי שיחה
(
    WAITING_FOR_STORE_ACTION,
    WAITING_FOR_STORE_NAME,
    WAITING_FOR_STORE_DESCRIPTION,
    WAITING_FOR_STORE_ADDRESS,
    WAITING_FOR_STORE_PHONE,
    WAITING_FOR_STORE_EMAIL,
    WAITING_FOR_STORE_WEBSITE,
    WAITING_FOR_STORE_LOGO,
    WAITING_FOR_STORE_CONFIRMATION,
    WAITING_FOR_STORE_SETTINGS
) = range(10)

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
            entry_points=[CommandHandler("connect_store", self.connect_store_start)],
            states={
                WAITING_FOR_STORE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_name)
                ],
                WAITING_FOR_STORE_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_description)
                ],
                WAITING_FOR_STORE_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_address)
                ],
                WAITING_FOR_STORE_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_phone)
                ],
                WAITING_FOR_STORE_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_email)
                ],
                WAITING_FOR_STORE_WEBSITE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_website)
                ],
                WAITING_FOR_STORE_LOGO: [
                    MessageHandler(filters.PHOTO | filters.Document.IMAGE, self.connect_store_logo),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.connect_store_logo)
                ],
                WAITING_FOR_STORE_CONFIRMATION: [
                    CallbackQueryHandler(self.connect_store_confirmation)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def connect_store_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך חיבור חנות"""
        user_id = update.effective_user.id
        logger.info(f"Connect store command from user {user_id}")
        
        # איפוס נתוני החנות בקונטקסט
        context.user_data['store'] = {}
        
        await update.message.reply_text(
            "🏪 *חיבור חנות חדשה*\n\n"
            "אנא הזן את שם החנות.\n\n"
            "לביטול התהליך, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_NAME
    
    async def connect_store_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם החנות"""
        name = update.message.text
        context.user_data['store']['name'] = name
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא הזן תיאור קצר לחנות.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_DESCRIPTION
    
    async def connect_store_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור החנות"""
        description = update.message.text
        context.user_data['store']['description'] = description
        
        await update.message.reply_text(
            "יופי! עכשיו אנא הזן את כתובת החנות.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_ADDRESS
    
    async def connect_store_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כתובת החנות"""
        address = update.message.text
        context.user_data['store']['address'] = address
        
        await update.message.reply_text(
            "מצוין! עכשיו אנא הזן מספר טלפון ליצירת קשר.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_PHONE
    
    async def connect_store_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת טלפון החנות"""
        phone = update.message.text
        
        # בדיקת תקינות מספר הטלפון
        from src.ui.telegram.utils.telegram_bot_utils import is_valid_phone
        if not is_valid_phone(phone):
            await update.message.reply_text(
                format_error_message("מספר הטלפון אינו תקין. אנא נסה שוב."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_STORE_PHONE
        
        context.user_data['store']['phone'] = phone
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא הזן כתובת אימייל.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_EMAIL
    
    async def connect_store_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת אימייל החנות"""
        email = update.message.text
        
        # בדיקת תקינות האימייל
        from src.ui.telegram.utils.telegram_bot_utils import is_valid_email
        if not is_valid_email(email):
            await update.message.reply_text(
                format_error_message("כתובת האימייל אינה תקינה. אנא נסה שוב."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_STORE_EMAIL
        
        context.user_data['store']['email'] = email
        
        await update.message.reply_text(
            "יופי! עכשיו אנא הזן את כתובת האתר של החנות (אופציונלי).\n"
            "אם אין אתר, הקלד 'אין'.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_WEBSITE
    
    async def connect_store_website(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת אתר החנות"""
        website = update.message.text
        
        if website.lower() != 'אין':
            # בדיקת תקינות כתובת האתר
            from src.ui.telegram.utils.telegram_bot_utils import is_valid_url
            if not is_valid_url(website):
                await update.message.reply_text(
                    format_error_message("כתובת האתר אינה תקינה. אנא נסה שוב."),
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_STORE_WEBSITE
        
        context.user_data['store']['website'] = None if website.lower() == 'אין' else website
        
        await update.message.reply_text(
            "כמעט סיימנו! אנא שלח לוגו לחנות.\n"
            "אם אין לוגו, הקלד 'אין'.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_STORE_LOGO
    
    async def connect_store_logo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת לוגו החנות"""
        if update.message.text and update.message.text.lower() == 'אין':
            context.user_data['store']['logo'] = None
        elif update.message.photo:
            context.user_data['store']['logo'] = update.message.photo[-1].file_id
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            context.user_data['store']['logo'] = update.message.document.file_id
        else:
            await update.message.reply_text(
                format_error_message("אנא שלח תמונה או הקלד 'אין'."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_STORE_LOGO
        
        # הצגת סיכום פרטי החנות
        store = context.user_data['store']
        summary = (
            "🏪 *סיכום פרטי החנות:*\n\n"
            f"שם: {store['name']}\n"
            f"תיאור: {store['description']}\n"
            f"כתובת: {store['address']}\n"
            f"טלפון: {store['phone']}\n"
            f"אימייל: {store['email']}\n"
            f"אתר: {store['website'] or 'אין'}\n"
            f"לוגו: {'יש' if store['logo'] else 'אין'}\n\n"
            "האם לשמור את פרטי החנות?"
        )
        
        keyboard = [[
            InlineKeyboardButton("כן, שמור", callback_data="save_store"),
            InlineKeyboardButton("לא, בטל", callback_data="cancel_store")
        ]]
        
        await update.message.reply_text(
            summary,
            parse_mode=ParseMode.MARKDOWN,
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
                    # בדיקה אם כבר יש חנות למשתמש
                    existing_store = await session.scalar(
                        db.select(Store)
                        .where(Store.owner_id == user_id)
                    )
                    
                    if existing_store:
                        await query.edit_message_text(
                            format_warning_message(
                                "כבר יש לך חנות מחוברת.\n"
                                "אנא מחק אותה תחילה אם ברצונך ליצור חנות חדשה."
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return ConversationHandler.END
                    
                    # יצירת החנות
                    store = Store(
                        name=store_data['name'],
                        description=store_data['description'],
                        address=store_data['address'],
                        phone=store_data['phone'],
                        email=store_data['email'],
                        website=store_data['website'],
                        logo=store_data['logo'],
                        owner_id=user_id
                    )
                    session.add(store)
                    await session.commit()
                
                await query.edit_message_text(
                    format_success_message("החנות נוצרה בהצלחה! 🎉\n"
                    "אתה יכול להתחיל להוסיף מוצרים בעזרת הפקודה /create_product."),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                logger.error(f"Error saving store: {e}")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בשמירת החנות: {str(e)}"),
                    parse_mode=ParseMode.MARKDOWN
                )
            
        elif query.data == "cancel_store":
            await query.edit_message_text(
                format_info_message("יצירת החנות בוטלה."),
                parse_mode=ParseMode.MARKDOWN
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
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.owner_id == user_id)
                )
                
                if not store:
                    await update.message.reply_text(
                        format_warning_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אתה יכול ליצור חנות חדשה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
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
                message = (
                    f"🏪 *{store.name} - לוח בקרה*\n\n"
                    "*סטטיסטיקות:*\n"
                    f"• מוצרים: {format_number(total_products)}\n"
                    f"• הזמנות: {format_number(total_orders)}\n"
                    f"• הכנסות: {format_price(total_revenue or 0)}\n\n"
                    "*פרטי החנות:*\n"
                    f"📞 טלפון: {store.phone}\n"
                    f"📧 אימייל: {store.email}\n"
                    f"🌐 אתר: {store.website or 'אין'}\n"
                    f"📍 כתובת: {store.address}\n\n"
                    f"*תיאור:*\n{store.description}\n"
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
                
                # שליחת ההודעה עם הלוגו אם יש
                if store.logo:
                    await update.message.reply_photo(
                        photo=store.logo,
                        caption=message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text(
                        message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                
        except Exception as e:
            logger.error(f"Error showing store dashboard: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בהצגת לוח הבקרה."),
                parse_mode=ParseMode.MARKDOWN
            ) 