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
    BotSettings
)
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.utils import (
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message,
    escape_markdown_v2
)

# הגדרת לוגר
logger = setup_logger('telegram_bot_settings')

# מצבי שיחה
(
    WAITING_FOR_SETTINGS_ACTION,
    WAITING_FOR_LANGUAGE,
    WAITING_FOR_TIMEZONE,
    WAITING_FOR_CURRENCY,
    WAITING_FOR_THEME,
    WAITING_FOR_PRIVACY,
    WAITING_FOR_NOTIFICATIONS,
    WAITING_FOR_API_KEY,
    WAITING_FOR_CONFIRM
) = range(9)

class TelegramBotSettings:
    """
    מחלקה לניהול הגדרות הבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
        
    def get_settings_handler(self) -> ConversationHandler:
        """
        יצירת handler להגדרות
        
        Returns:
            ConversationHandler מוגדר להגדרות
        """
        return ConversationHandler(
            entry_points=[CommandHandler("settings", self.settings_start)],
            states={
                WAITING_FOR_SETTINGS_ACTION: [
                    CallbackQueryHandler(self.handle_settings_action)
                ],
                WAITING_FOR_LANGUAGE: [
                    CallbackQueryHandler(self.handle_language)
                ],
                WAITING_FOR_TIMEZONE: [
                    CallbackQueryHandler(self.handle_timezone)
                ],
                WAITING_FOR_CURRENCY: [
                    CallbackQueryHandler(self.handle_currency)
                ],
                WAITING_FOR_THEME: [
                    CallbackQueryHandler(self.handle_theme)
                ],
                WAITING_FOR_PRIVACY: [
                    CallbackQueryHandler(self.handle_privacy)
                ],
                WAITING_FOR_NOTIFICATIONS: [
                    CallbackQueryHandler(self.handle_notifications)
                ],
                WAITING_FOR_API_KEY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_api_key)
                ],
                WAITING_FOR_CONFIRM: [
                    CallbackQueryHandler(self.handle_confirm)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def settings_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך הגדרות"""
        user_id = update.effective_user.id
        logger.info(f"Settings command from user {user_id}")
        
        # איפוס נתוני ההגדרות בקונטקסט
        context.user_data['settings'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("שפה", callback_data="language"),
                InlineKeyboardButton("אזור זמן", callback_data="timezone")
            ],
            [
                InlineKeyboardButton("מטבע", callback_data="currency"),
                InlineKeyboardButton("עיצוב", callback_data="theme")
            ],
            [
                InlineKeyboardButton("פרטיות", callback_data="privacy"),
                InlineKeyboardButton("התראות", callback_data="notifications")
            ],
            [
                InlineKeyboardButton("מפתחות API", callback_data="api_keys"),
                InlineKeyboardButton("גיבוי", callback_data="backup")
            ]
        ]
        
        await update.message.reply_text(
            "⚙️ *הגדרות*\n\n"
            "בחר את ההגדרה שברצונך לשנות:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_SETTINGS_ACTION
    
    async def handle_settings_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת הגדרות"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['settings']['action'] = action
        
        if action == "language":
            keyboard = [
                [
                    InlineKeyboardButton("עברית", callback_data="he"),
                    InlineKeyboardButton("English", callback_data="en")
                ],
                [
                    InlineKeyboardButton("Русский", callback_data="ru"),
                    InlineKeyboardButton("العربية", callback_data="ar")
                ]
            ]
            
            await query.edit_message_text(
                "🌐 *בחירת שפה*\n\n"
                "בחר את השפה הרצויה:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_LANGUAGE
            
        elif action == "timezone":
            keyboard = [
                [
                    InlineKeyboardButton("ישראל (UTC+2)", callback_data="Asia/Jerusalem"),
                    InlineKeyboardButton("מוסקבה (UTC+3)", callback_data="Europe/Moscow")
                ],
                [
                    InlineKeyboardButton("לונדון (UTC)", callback_data="Europe/London"),
                    InlineKeyboardButton("ניו יורק (UTC-5)", callback_data="America/New_York")
                ]
            ]
            
            await query.edit_message_text(
                "🕒 *בחירת אזור זמן*\n\n"
                "בחר את אזור הזמן הרצוי:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_TIMEZONE
            
        elif action == "currency":
            keyboard = [
                [
                    InlineKeyboardButton("₪ שקל", callback_data="ILS"),
                    InlineKeyboardButton("$ דולר", callback_data="USD")
                ],
                [
                    InlineKeyboardButton("€ אירו", callback_data="EUR"),
                    InlineKeyboardButton("£ ליש\"ט", callback_data="GBP")
                ]
            ]
            
            await query.edit_message_text(
                "💰 *בחירת מטבע*\n\n"
                "בחר את המטבע הרצוי:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_CURRENCY
            
        elif action == "theme":
            keyboard = [
                [
                    InlineKeyboardButton("🌞 בהיר", callback_data="light"),
                    InlineKeyboardButton("🌚 כהה", callback_data="dark")
                ],
                [
                    InlineKeyboardButton("🎨 צבעוני", callback_data="colorful"),
                    InlineKeyboardButton("⚫ מינימליסטי", callback_data="minimal")
                ]
            ]
            
            await query.edit_message_text(
                "🎨 *בחירת עיצוב*\n\n"
                "בחר את העיצוב הרצוי:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_THEME
            
        elif action == "privacy":
            keyboard = [
                [
                    InlineKeyboardButton("🔒 מקסימלית", callback_data="max_privacy"),
                    InlineKeyboardButton("🔐 בינונית", callback_data="medium_privacy")
                ],
                [
                    InlineKeyboardButton("🔓 מינימלית", callback_data="min_privacy"),
                    InlineKeyboardButton("📊 מותאם אישית", callback_data="custom_privacy")
                ]
            ]
            
            await query.edit_message_text(
                "🔒 *הגדרות פרטיות*\n\n"
                "בחר את רמת הפרטיות הרצויה:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_PRIVACY
            
        elif action == "notifications":
            keyboard = [
                [
                    InlineKeyboardButton("🔔 הכל", callback_data="all_notifications"),
                    InlineKeyboardButton("🔕 כלום", callback_data="no_notifications")
                ],
                [
                    InlineKeyboardButton("⚡ חשוב בלבד", callback_data="important_only"),
                    InlineKeyboardButton("⚙️ מותאם אישית", callback_data="custom_notifications")
                ]
            ]
            
            await query.edit_message_text(
                "🔔 *הגדרות התראות*\n\n"
                "בחר את סוג ההתראות הרצוי:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_NOTIFICATIONS
            
        elif action == "api_keys":
            await query.edit_message_text(
                "🔑 *הגדרת מפתחות API*\n\n"
                "הזן את מפתח ה-API החדש:",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_API_KEY
            
        elif action == "backup":
            return await self.handle_backup(update, context)
    
    async def handle_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת שפה"""
        query = update.callback_query
        await query.answer()
        
        language = query.data
        context.user_data['settings']['language'] = language
        
        try:
            async with db.get_session() as session:
                # עדכון השפה בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.language = language
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("השפה עודכנה בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating language: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון השפה."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת אזור זמן"""
        query = update.callback_query
        await query.answer()
        
        timezone = query.data
        context.user_data['settings']['timezone'] = timezone
        
        try:
            async with db.get_session() as session:
                # עדכון אזור הזמן בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.timezone = timezone
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("אזור הזמן עודכן בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating timezone: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון אזור הזמן."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_currency(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת מטבע"""
        query = update.callback_query
        await query.answer()
        
        currency = query.data
        context.user_data['settings']['currency'] = currency
        
        try:
            async with db.get_session() as session:
                # עדכון המטבע בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.currency = currency
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("המטבע עודכן בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating currency: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון המטבע."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת עיצוב"""
        query = update.callback_query
        await query.answer()
        
        theme = query.data
        context.user_data['settings']['theme'] = theme
        
        try:
            async with db.get_session() as session:
                # עדכון העיצוב בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.theme = theme
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("העיצוב עודכן בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating theme: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון העיצוב."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_privacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת הגדרות פרטיות"""
        query = update.callback_query
        await query.answer()
        
        privacy = query.data
        context.user_data['settings']['privacy'] = privacy
        
        try:
            async with db.get_session() as session:
                # עדכון הגדרות הפרטיות בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.privacy_settings = privacy
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("הגדרות הפרטיות עודכנו בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating privacy settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון הגדרות הפרטיות."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת הגדרות התראות"""
        query = update.callback_query
        await query.answer()
        
        notifications = query.data
        context.user_data['settings']['notifications'] = notifications
        
        try:
            async with db.get_session() as session:
                # עדכון הגדרות ההתראות בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == query.from_user.id)
                )
                
                if user:
                    user.notification_settings = notifications
                    await session.commit()
                    
                    await query.edit_message_text(
                        format_success_message("הגדרות ההתראות עודכנו בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון הגדרות ההתראות."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהזנת מפתח API"""
        api_key = update.message.text
        context.user_data['settings']['api_key'] = api_key
        
        try:
            async with db.get_session() as session:
                # עדכון מפתח ה-API בבסיס הנתונים
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == update.effective_user.id)
                )
                
                if user:
                    user.api_key = api_key
                    await session.commit()
                    
                    await update.message.reply_text(
                        format_success_message("מפתח ה-API עודכן בהצלחה!"),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                else:
                    await update.message.reply_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
        except Exception as e:
            logger.error(f"Error updating API key: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בעדכון מפתח ה-API."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def handle_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בגיבוי הגדרות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת כל ההגדרות של המשתמש
                user = await session.scalar(
                    db.select(User)
                    .where(User.telegram_id == user_id)
                )
                
                if not user:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצא משתמש מחובר.\n"
                            "אנא התחבר מחדש בעזרת הפקודה /start."
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return ConversationHandler.END
                
                # יצירת גיבוי של ההגדרות
                settings_backup = {
                    'language': user.language,
                    'timezone': user.timezone,
                    'currency': user.currency,
                    'theme': user.theme,
                    'privacy_settings': user.privacy_settings,
                    'notification_settings': user.notification_settings
                }
                
                # שמירת הגיבוי בקובץ
                # TODO: להוסיף שמירה בפועל של הקובץ
                
                keyboard = [
                    [
                        InlineKeyboardButton("שחזר גיבוי", callback_data="restore_backup"),
                        InlineKeyboardButton("מחק גיבוי", callback_data="delete_backup")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    "💾 *גיבוי הגדרות*\n\n"
                    "הגיבוי נוצר בהצלחה!\n"
                    "מה תרצה לעשות?",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה ביצירת הגיבוי."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return WAITING_FOR_SETTINGS_ACTION 