import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
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
    Notification,
    NotificationType
)
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.utils import (
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message
)

# הגדרת לוגר
logger = setup_logger('telegram_bot_notifications')

# מצבי שיחה
(
    WAITING_FOR_NOTIFICATION_ACTION,
    WAITING_FOR_NOTIFICATION_TYPE,
    WAITING_FOR_NOTIFICATION_MESSAGE,
    WAITING_FOR_NOTIFICATION_SCHEDULE,
    WAITING_FOR_NOTIFICATION_CONFIRM
) = range(5)

class TelegramBotNotifications:
    """
    מחלקה לניהול התראות והודעות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
        
    def get_notifications_handler(self) -> ConversationHandler:
        """
        יצירת handler לניהול התראות
        
        Returns:
            ConversationHandler מוגדר לניהול התראות
        """
        return ConversationHandler(
            entry_points=[CommandHandler("notifications", self.notifications_start)],
            states={
                WAITING_FOR_NOTIFICATION_ACTION: [
                    CallbackQueryHandler(self.handle_notification_action)
                ],
                WAITING_FOR_NOTIFICATION_TYPE: [
                    CallbackQueryHandler(self.handle_notification_type)
                ],
                WAITING_FOR_NOTIFICATION_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notification_message)
                ],
                WAITING_FOR_NOTIFICATION_SCHEDULE: [
                    CallbackQueryHandler(self.handle_notification_schedule)
                ],
                WAITING_FOR_NOTIFICATION_CONFIRM: [
                    CallbackQueryHandler(self.handle_notification_confirm)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def notifications_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול התראות"""
        user_id = update.effective_user.id
        logger.info(f"Notifications command from user {user_id}")
        
        # איפוס נתוני ההתראות בקונטקסט
        context.user_data['notification'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("צור התראה חדשה", callback_data="create_notification"),
                InlineKeyboardButton("התראות פעילות", callback_data="active_notifications")
            ],
            [
                InlineKeyboardButton("הגדרות התראות", callback_data="notification_settings"),
                InlineKeyboardButton("היסטוריית התראות", callback_data="notification_history")
            ]
        ]
        
        await update.message.reply_text(
            "🔔 *ניהול התראות*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_NOTIFICATION_ACTION
    
    async def handle_notification_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת התראה"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['notification']['action'] = action
        
        if action == "create_notification":
            keyboard = [
                [
                    InlineKeyboardButton("התראת מערכת", callback_data="system"),
                    InlineKeyboardButton("התראת משתמש", callback_data="user")
                ],
                [
                    InlineKeyboardButton("התראת מלאי", callback_data="inventory"),
                    InlineKeyboardButton("התראת הזמנה", callback_data="order")
                ],
                [
                    InlineKeyboardButton("התראת תשלום", callback_data="payment"),
                    InlineKeyboardButton("התראת משלוח", callback_data="shipping")
                ]
            ]
            
            await query.edit_message_text(
                "🔔 *יצירת התראה חדשה*\n\n"
                "בחר את סוג ההתראה:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_NOTIFICATION_TYPE
            
        elif action == "active_notifications":
            return await self.show_active_notifications(update, context)
            
        elif action == "notification_settings":
            return await self.show_notification_settings(update, context)
            
        elif action == "notification_history":
            return await self.show_notification_history(update, context)
    
    async def handle_notification_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת סוג התראה"""
        query = update.callback_query
        await query.answer()
        
        notification_type = query.data
        context.user_data['notification']['type'] = notification_type
        
        await query.edit_message_text(
            f"📝 *יצירת התראת {notification_type}*\n\n"
            "הזן את תוכן ההתראה:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_NOTIFICATION_MESSAGE
    
    async def handle_notification_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהזנת תוכן ההתראה"""
        message = update.message.text
        context.user_data['notification']['message'] = message
        
        keyboard = [
            [
                InlineKeyboardButton("מיידי", callback_data="immediate"),
                InlineKeyboardButton("בעוד שעה", callback_data="hour")
            ],
            [
                InlineKeyboardButton("בעוד יום", callback_data="day"),
                InlineKeyboardButton("בעוד שבוע", callback_data="week")
            ],
            [
                InlineKeyboardButton("מותאם אישית", callback_data="custom")
            ]
        ]
        
        await update.message.reply_text(
            "⏰ *תזמון התראה*\n\n"
            "מתי לשלוח את ההתראה?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_NOTIFICATION_SCHEDULE
    
    async def handle_notification_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת תזמון ההתראה"""
        query = update.callback_query
        await query.answer()
        
        schedule = query.data
        context.user_data['notification']['schedule'] = schedule
        
        # חישוב זמן השליחה
        now = datetime.now()
        if schedule == "immediate":
            send_time = now
        elif schedule == "hour":
            send_time = now + timedelta(hours=1)
        elif schedule == "day":
            send_time = now + timedelta(days=1)
        elif schedule == "week":
            send_time = now + timedelta(weeks=1)
        else:
            # TODO: טיפול בתזמון מותאם אישית
            send_time = now
        
        context.user_data['notification']['send_time'] = send_time
        
        # הצגת סיכום ההתראה
        notification_type = context.user_data['notification']['type']
        message = context.user_data['notification']['message']
        
        await query.edit_message_text(
            "📋 *סיכום התראה*\n\n"
            f"*סוג:* {notification_type}\n"
            f"*תוכן:* {message}\n"
            f"*מועד שליחה:* {send_time.strftime('%d/%m/%Y %H:%M')}\n\n"
            "האם לאשר את ההתראה?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("אשר", callback_data="confirm"),
                    InlineKeyboardButton("בטל", callback_data="cancel")
                ]
            ])
        )
        
        return WAITING_FOR_NOTIFICATION_CONFIRM
    
    async def handle_notification_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול באישור ההתראה"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm":
            try:
                notification_data = context.user_data['notification']
                
                async with db.get_session() as session:
                    # שמירת ההתראה בבסיס הנתונים
                    notification = Notification(
                        type=notification_data['type'],
                        message=notification_data['message'],
                        send_time=notification_data['send_time'],
                        user_id=query.from_user.id,
                        status='pending'
                    )
                    session.add(notification)
                    await session.commit()
                
                await query.edit_message_text(
                    format_success_message(
                        "ההתראה נוצרה בהצלחה!\n"
                        f"תישלח ב-{notification_data['send_time'].strftime('%d/%m/%Y %H:%M')}"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                logger.error(f"Error creating notification: {e}")
                await query.edit_message_text(
                    format_error_message("אירעה שגיאה ביצירת ההתראה."),
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await query.edit_message_text(
                format_info_message("יצירת ההתראה בוטלה."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    async def show_active_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת התראות פעילות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת התראות פעילות
                notifications = await session.execute(
                    db.select(Notification)
                    .where(
                        db.and_(
                            Notification.user_id == user_id,
                            Notification.status == 'pending'
                        )
                    )
                    .order_by(Notification.send_time)
                )
                
                if not notifications:
                    await query.edit_message_text(
                        format_info_message("אין התראות פעילות כרגע."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                message = "🔔 *התראות פעילות*\n\n"
                
                for notification in notifications:
                    message += (
                        f"*סוג:* {notification.type}\n"
                        f"*תוכן:* {notification.message}\n"
                        f"*מועד שליחה:* {notification.send_time.strftime('%d/%m/%Y %H:%M')}\n"
                        "-------------------\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("מחק התראה", callback_data="delete_notification"),
                        InlineKeyboardButton("ערוך התראה", callback_data="edit_notification")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing active notifications: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת ההתראות הפעילות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_NOTIFICATION_ACTION
    
    async def show_notification_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הגדרות התראות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת הגדרות התראות של המשתמש
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
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ התראות מערכת" if user.system_notifications else "❌ התראות מערכת",
                            callback_data="toggle_system_notifications"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ התראות הזמנות" if user.order_notifications else "❌ התראות הזמנות",
                            callback_data="toggle_order_notifications"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ התראות תשלומים" if user.payment_notifications else "❌ התראות תשלומים",
                            callback_data="toggle_payment_notifications"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ התראות משלוחים" if user.shipping_notifications else "❌ התראות משלוחים",
                            callback_data="toggle_shipping_notifications"
                        )
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    "⚙️ *הגדרות התראות*\n\n"
                    "לחץ על כפתור כדי להפעיל/לכבות:",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing notification settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת הגדרות ההתראות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_NOTIFICATION_ACTION
    
    async def show_notification_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת היסטוריית התראות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת היסטוריית התראות
                notifications = await session.execute(
                    db.select(Notification)
                    .where(
                        db.and_(
                            Notification.user_id == user_id,
                            Notification.status == 'sent'
                        )
                    )
                    .order_by(Notification.send_time.desc())
                    .limit(10)
                )
                
                if not notifications:
                    await query.edit_message_text(
                        format_info_message("אין היסטוריית התראות."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                message = "📜 *היסטוריית התראות*\n\n"
                
                for notification in notifications:
                    message += (
                        f"*סוג:* {notification.type}\n"
                        f"*תוכן:* {notification.message}\n"
                        f"*נשלח:* {notification.send_time.strftime('%d/%m/%Y %H:%M')}\n"
                        "-------------------\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("נקה היסטוריה", callback_data="clear_history"),
                        InlineKeyboardButton("ייצא לקובץ", callback_data="export_history")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing notification history: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת היסטוריית ההתראות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_NOTIFICATION_ACTION 