import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job
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
    WooCommerceOrderItem as OrderItem,
    ScheduledTask
)
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.utils import (
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message,
    format_date,
    escape_markdown_v2
)

# הגדרת לוגר
logger = setup_logger('telegram_bot_scheduler')

# מצבי שיחה
(
    WAITING_FOR_SCHEDULER_ACTION,
    WAITING_FOR_TASK_TYPE,
    WAITING_FOR_TASK_NAME,
    WAITING_FOR_TASK_SCHEDULE,
    WAITING_FOR_TASK_PARAMS,
    WAITING_FOR_TASK_CONFIRM
) = range(6)

class TelegramBotScheduler:
    """
    מחלקה לניהול מתזמן משימות אוטומטיות
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
    def get_scheduler_handler(self) -> ConversationHandler:
        """
        יצירת handler למתזמן
        
        Returns:
            ConversationHandler מוגדר למתזמן
        """
        return ConversationHandler(
            entry_points=[CommandHandler("scheduler", self.scheduler_start)],
            states={
                WAITING_FOR_SCHEDULER_ACTION: [
                    CallbackQueryHandler(self.handle_scheduler_action)
                ],
                WAITING_FOR_TASK_TYPE: [
                    CallbackQueryHandler(self.handle_task_type)
                ],
                WAITING_FOR_TASK_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_task_name)
                ],
                WAITING_FOR_TASK_SCHEDULE: [
                    CallbackQueryHandler(self.handle_task_schedule)
                ],
                WAITING_FOR_TASK_PARAMS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_task_params)
                ],
                WAITING_FOR_TASK_CONFIRM: [
                    CallbackQueryHandler(self.handle_task_confirm)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def scheduler_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך תזמון משימות"""
        user_id = update.effective_user.id
        logger.info(f"Scheduler command from user {user_id}")
        
        # איפוס נתוני המתזמן בקונטקסט
        context.user_data['scheduler'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("צור משימה חדשה", callback_data="create_task"),
                InlineKeyboardButton("משימות פעילות", callback_data="active_tasks")
            ],
            [
                InlineKeyboardButton("הגדרות מתזמן", callback_data="scheduler_settings"),
                InlineKeyboardButton("היסטוריית משימות", callback_data="task_history")
            ]
        ]
        
        await update.message.reply_text(
            "⏰ *מתזמן משימות*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_SCHEDULER_ACTION
    
    async def handle_scheduler_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת מתזמן"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['scheduler']['action'] = action
        
        if action == "create_task":
            keyboard = [
                [
                    InlineKeyboardButton("דוח יומי", callback_data="daily_report"),
                    InlineKeyboardButton("דוח שבועי", callback_data="weekly_report")
                ],
                [
                    InlineKeyboardButton("גיבוי נתונים", callback_data="backup_data"),
                    InlineKeyboardButton("ניקוי מערכת", callback_data="system_cleanup")
                ],
                [
                    InlineKeyboardButton("תזכורת", callback_data="reminder"),
                    InlineKeyboardButton("משימה מותאמת", callback_data="custom_task")
                ]
            ]
            
            await query.edit_message_text(
                "📋 *יצירת משימה חדשה*\n\n"
                "בחר את סוג המשימה:",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_TASK_TYPE
            
        elif action == "active_tasks":
            return await self.show_active_tasks(update, context)
            
        elif action == "scheduler_settings":
            return await self.show_scheduler_settings(update, context)
            
        elif action == "task_history":
            return await self.show_task_history(update, context)
    
    async def handle_task_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת סוג משימה"""
        query = update.callback_query
        await query.answer()
        
        task_type = query.data
        context.user_data['scheduler']['task_type'] = task_type
        
        await query.edit_message_text(
            f"📝 *הגדרת משימת {task_type}*\n\n"
            "הזן שם למשימה:",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_TASK_NAME
    
    async def handle_task_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהזנת שם משימה"""
        task_name = update.message.text
        context.user_data['scheduler']['task_name'] = task_name
        
        keyboard = [
            [
                InlineKeyboardButton("כל יום", callback_data="daily"),
                InlineKeyboardButton("כל שבוע", callback_data="weekly")
            ],
            [
                InlineKeyboardButton("כל חודש", callback_data="monthly"),
                InlineKeyboardButton("כל שעה", callback_data="hourly")
            ],
            [
                InlineKeyboardButton("מותאם אישית", callback_data="custom")
            ]
        ]
        
        await update.message.reply_text(
            "⏰ *תזמון משימה*\n\n"
            "בחר את תדירות המשימה:",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_TASK_SCHEDULE
    
    async def handle_task_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת תזמון משימה"""
        query = update.callback_query
        await query.answer()
        
        schedule = query.data
        context.user_data['scheduler']['schedule'] = schedule
        
        # הגדרת הפרמטרים הנדרשים לפי סוג המשימה
        task_type = context.user_data['scheduler']['task_type']
        
        if task_type == "daily_report":
            await query.edit_message_text(
                "📊 *הגדרת דוח יומי*\n\n"
                "הזן את סוגי הנתונים שברצונך לכלול בדוח (מופרדים בפסיקים):",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        elif task_type == "weekly_report":
            await query.edit_message_text(
                "📈 *הגדרת דוח שבועי*\n\n"
                "הזן את סוגי הנתונים שברצונך לכלול בדוח (מופרדים בפסיקים):",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        elif task_type == "backup_data":
            await query.edit_message_text(
                "💾 *הגדרת גיבוי נתונים*\n\n"
                "הזן את נתיב התיקייה לגיבוי:",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        elif task_type == "system_cleanup":
            await query.edit_message_text(
                "🧹 *הגדרת ניקוי מערכת*\n\n"
                "הזן את סוגי הנתונים למחיקה (מופרדים בפסיקים):",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        elif task_type == "reminder":
            await query.edit_message_text(
                "🔔 *הגדרת תזכורת*\n\n"
                "הזן את תוכן התזכורת:",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        elif task_type == "custom_task":
            await query.edit_message_text(
                "⚙️ *הגדרת משימה מותאמת*\n\n"
                "הזן את הפרמטרים למשימה (בפורמט JSON):",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return WAITING_FOR_TASK_PARAMS
    
    async def handle_task_params(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהזנת פרמטרים למשימה"""
        params = update.message.text
        context.user_data['scheduler']['params'] = params
        
        # הצגת סיכום המשימה
        task_type = context.user_data['scheduler']['task_type']
        task_name = context.user_data['scheduler']['task_name']
        schedule = context.user_data['scheduler']['schedule']
        
        await update.message.reply_text(
            "📋 *סיכום משימה*\n\n"
            f"*סוג:* {task_type}\n"
            f"*שם:* {task_name}\n"
            f"*תזמון:* {schedule}\n"
            f"*פרמטרים:* {params}\n\n"
            "האם לאשר את המשימה?",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("אשר", callback_data="confirm"),
                    InlineKeyboardButton("בטל", callback_data="cancel")
                ]
            ])
        )
        
        return WAITING_FOR_TASK_CONFIRM
    
    async def handle_task_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול באישור המשימה"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm":
            try:
                task_data = context.user_data['scheduler']
                
                async with db.get_session() as session:
                    # שמירת המשימה בבסיס הנתונים
                    task = ScheduledTask(
                        type=task_data['task_type'],
                        name=task_data['task_name'],
                        schedule=task_data['schedule'],
                        params=task_data['params'],
                        user_id=query.from_user.id,
                        status='active'
                    )
                    session.add(task)
                    await session.commit()
                    
                    # הוספת המשימה למתזמן
                    if task_data['schedule'] == 'daily':
                        trigger = CronTrigger(hour=0, minute=0)
                    elif task_data['schedule'] == 'weekly':
                        trigger = CronTrigger(day_of_week=0, hour=0, minute=0)
                    elif task_data['schedule'] == 'monthly':
                        trigger = CronTrigger(day=1, hour=0, minute=0)
                    elif task_data['schedule'] == 'hourly':
                        trigger = IntervalTrigger(hours=1)
                    else:
                        # TODO: טיפול בתזמון מותאם אישית
                        trigger = IntervalTrigger(days=1)
                    
                    self.scheduler.add_job(
                        self.execute_task,
                        trigger=trigger,
                        args=[task.id],
                        id=str(task.id)
                    )
                    
                    await query.edit_message_text(
                        format_success_message(
                            "המשימה נוצרה בהצלחה!\n"
                            f"תזמון: {task_data['schedule']}"
                        ),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    
            except Exception as e:
                logger.error(f"Error creating task: {e}")
                await query.edit_message_text(
                    format_error_message("אירעה שגיאה ביצירת המשימה."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        else:
            await query.edit_message_text(
                format_info_message("יצירת המשימה בוטלה."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return ConversationHandler.END
    
    async def show_active_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת משימות פעילות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת משימות פעילות
                tasks = await session.execute(
                    db.select(ScheduledTask)
                    .where(
                        db.and_(
                            ScheduledTask.user_id == user_id,
                            ScheduledTask.status == 'active'
                        )
                    )
                    .order_by(ScheduledTask.created_at)
                )
                
                if not tasks:
                    await query.edit_message_text(
                        format_info_message("אין משימות פעילות כרגע."),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return ConversationHandler.END
                
                message = "📋 *משימות פעילות*\n\n"
                
                for task in tasks:
                    message += (
                        f"*שם:* {task.name}\n"
                        f"*סוג:* {task.type}\n"
                        f"*תזמון:* {task.schedule}\n"
                        "-------------------\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("השהה משימה", callback_data="pause_task"),
                        InlineKeyboardButton("מחק משימה", callback_data="delete_task")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing active tasks: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת המשימות הפעילות."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return WAITING_FOR_SCHEDULER_ACTION
    
    async def show_scheduler_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הגדרות מתזמן"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת הגדרות מתזמן של המשתמש
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
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ הפעל מתזמן" if user.scheduler_enabled else "❌ הפעל מתזמן",
                            callback_data="toggle_scheduler"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ התראות משימות" if user.task_notifications else "❌ התראות משימות",
                            callback_data="toggle_task_notifications"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✅ לוג משימות" if user.task_logging else "❌ לוג משימות",
                            callback_data="toggle_task_logging"
                        )
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    "⚙️ *הגדרות מתזמן*\n\n"
                    "לחץ על כפתור כדי להפעיל/לכבות:",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing scheduler settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת הגדרות המתזמן."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return WAITING_FOR_SCHEDULER_ACTION
    
    async def show_task_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת היסטוריית משימות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת היסטוריית משימות
                tasks = await session.execute(
                    db.select(ScheduledTask)
                    .where(
                        db.and_(
                            ScheduledTask.user_id == user_id,
                            ScheduledTask.status == 'completed'
                        )
                    )
                    .order_by(ScheduledTask.completed_at.desc())
                    .limit(10)
                )
                
                if not tasks:
                    await query.edit_message_text(
                        format_info_message("אין היסטוריית משימות."),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return ConversationHandler.END
                
                message = "📜 *היסטוריית משימות*\n\n"
                
                for task in tasks:
                    message += (
                        f"*שם:* {task.name}\n"
                        f"*סוג:* {task.type}\n"
                        f"*הושלם:* {task.completed_at.strftime('%d/%m/%Y %H:%M')}\n"
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
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing task history: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בטעינת היסטוריית המשימות."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        return WAITING_FOR_SCHEDULER_ACTION
    
    async def execute_task(self, task_id: int):
        """
        הרצת משימה מתוזמנת
        
        Args:
            task_id: מזהה המשימה
        """
        try:
            async with db.get_session() as session:
                # קבלת פרטי המשימה
                task = await session.scalar(
                    db.select(ScheduledTask)
                    .where(ScheduledTask.id == task_id)
                )
                
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return
                
                # ביצוע המשימה לפי הסוג
                if task.type == "daily_report":
                    await self.generate_daily_report(task)
                    
                elif task.type == "weekly_report":
                    await self.generate_weekly_report(task)
                    
                elif task.type == "backup_data":
                    await self.backup_data(task)
                    
                elif task.type == "system_cleanup":
                    await self.cleanup_system(task)
                    
                elif task.type == "reminder":
                    await self.send_reminder(task)
                    
                elif task.type == "custom_task":
                    await self.execute_custom_task(task)
                
                # עדכון סטטוס המשימה
                task.status = 'completed'
                task.completed_at = datetime.now()
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
    
    async def generate_daily_report(self, task: ScheduledTask):
        """
        יצירת דוח יומי
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה ליצירת דוח יומי
        pass
    
    async def generate_weekly_report(self, task: ScheduledTask):
        """
        יצירת דוח שבועי
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה ליצירת דוח שבועי
        pass
    
    async def backup_data(self, task: ScheduledTask):
        """
        גיבוי נתונים
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה לגיבוי נתונים
        pass
    
    async def cleanup_system(self, task: ScheduledTask):
        """
        ניקוי מערכת
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה לניקוי מערכת
        pass
    
    async def send_reminder(self, task: ScheduledTask):
        """
        שליחת תזכורת
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה לשליחת תזכורת
        pass
    
    async def execute_custom_task(self, task: ScheduledTask):
        """
        הרצת משימה מותאמת אישית
        
        Args:
            task: המשימה המתוזמנת
        """
        # TODO: להוסיף לוגיקה להרצת משימה מותאמת אישית
        pass 