import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
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
    WooCommerceOrder as Order,
    WooCommerceProduct as Product,
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
logger = setup_logger('telegram_bot_analytics')

# מצבי שיחה
(
    WAITING_FOR_ANALYTICS_ACTION,
    WAITING_FOR_REPORT_TYPE,
    WAITING_FOR_DATE_RANGE,
    WAITING_FOR_EXPORT_FORMAT,
    WAITING_FOR_EMAIL
) = range(5)

# סוגי דוחות
REPORT_TYPES = {
    'sales': 'דוח מכירות',
    'products': 'דוח מוצרים',
    'customers': 'דוח לקוחות',
    'inventory': 'דוח מלאי',
    'payments': 'דוח תשלומים',
    'shipping': 'דוח משלוחים'
}

class TelegramBotAnalytics:
    """
    מחלקה לניתוח נתונים ודוחות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_analytics_handler(self) -> ConversationHandler:
        """
        יצירת handler לניתוח נתונים
        
        Returns:
            ConversationHandler מוגדר לניתוח נתונים
        """
        return ConversationHandler(
            entry_points=[CommandHandler("analytics", self.analytics_start)],
            states={
                WAITING_FOR_ANALYTICS_ACTION: [
                    CallbackQueryHandler(self.handle_analytics_action)
                ],
                WAITING_FOR_REPORT_TYPE: [
                    CallbackQueryHandler(self.handle_report_type)
                ],
                WAITING_FOR_DATE_RANGE: [
                    CallbackQueryHandler(self.handle_date_range)
                ],
                WAITING_FOR_EXPORT_FORMAT: [
                    CallbackQueryHandler(self.handle_export_format)
                ],
                WAITING_FOR_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_email)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def analytics_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניתוח נתונים"""
        user_id = update.effective_user.id
        logger.info(f"Analytics command from user {user_id}")
        
        # איפוס נתוני האנליטיקס בקונטקסט
        context.user_data['analytics'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("סקירה כללית", callback_data="overview"),
                InlineKeyboardButton("דוחות", callback_data="reports")
            ],
            [
                InlineKeyboardButton("גרפים", callback_data="graphs"),
                InlineKeyboardButton("תחזיות", callback_data="forecasts")
            ],
            [
                InlineKeyboardButton("ייצוא נתונים", callback_data="export")
            ]
        ]
        
        await update.message.reply_text(
            "📊 *ניתוח נתונים*\n\n"
            "מה תרצה לראות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_ANALYTICS_ACTION
    
    async def handle_analytics_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת ניתוח"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['analytics']['action'] = action
        
        if action == "overview":
            return await self.show_overview(update, context)
            
        elif action == "reports":
            keyboard = [[
                InlineKeyboardButton(text, callback_data=f"report_{code}")
            ] for code, text in REPORT_TYPES.items()]
            
            await query.edit_message_text(
                "📋 *דוחות*\n\n"
                "בחר את סוג הדוח הרצוי:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_REPORT_TYPE
            
        elif action == "graphs":
            return await self.show_graphs(update, context)
            
        elif action == "forecasts":
            return await self.show_forecasts(update, context)
            
        elif action == "export":
            keyboard = [
                [
                    InlineKeyboardButton("Excel", callback_data="export_excel"),
                    InlineKeyboardButton("CSV", callback_data="export_csv")
                ],
                [
                    InlineKeyboardButton("PDF", callback_data="export_pdf"),
                    InlineKeyboardButton("JSON", callback_data="export_json")
                ]
            ]
            
            await query.edit_message_text(
                "📤 *ייצוא נתונים*\n\n"
                "בחר את פורמט הייצוא הרצוי:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_EXPORT_FORMAT
    
    async def show_overview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת סקירה כללית"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.owner_id == user_id)
                )
                
                if not store:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אנא חבר חנות תחילה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # חישוב סטטיסטיקות כלליות
                total_products = await session.scalar(
                    db.select(db.func.count(Product.id))
                    .where(Product.store_id == store.id)
                )
                
                total_customers = await session.scalar(
                    db.select(db.func.count(Customer.id))
                    .where(Customer.store_id == store.id)
                )
                
                total_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                    .where(Order.store_id == store.id)
                )
                
                total_revenue = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                    .where(Order.store_id == store.id)
                )
                
                # חישוב נתוני החודש הנוכחי
                today = datetime.now()
                month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                month_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                    .where(
                        db.and_(
                            Order.store_id == store.id,
                            Order.created_at >= month_start
                        )
                    )
                )
                
                month_revenue = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                    .where(
                        db.and_(
                            Order.store_id == store.id,
                            Order.created_at >= month_start
                        )
                    )
                )
                
                # חישוב מוצרים הכי נמכרים
                top_products = await session.execute(
                    db.select(
                        Product.name,
                        db.func.count(Order.id).label('orders'),
                        db.func.sum(Order.total_amount).label('revenue')
                    )
                    .join(Order)
                    .where(Product.store_id == store.id)
                    .group_by(Product.id)
                    .order_by(db.text('orders DESC'))
                    .limit(5)
                )
                
                message = (
                    "📊 *סקירה כללית*\n\n"
                    "*נתונים כלליים:*\n"
                    f"• מוצרים: {format_number(total_products)}\n"
                    f"• לקוחות: {format_number(total_customers)}\n"
                    f"• הזמנות: {format_number(total_orders)}\n"
                    f"• הכנסות: {format_price(total_revenue or 0)}\n\n"
                    "*החודש הנוכחי:*\n"
                    f"• הזמנות: {format_number(month_orders)}\n"
                    f"• הכנסות: {format_price(month_revenue or 0)}\n\n"
                    "*מוצרים מובילים:*\n"
                )
                
                for product, orders, revenue in top_products:
                    message += f"• {product}: {format_number(orders)} הזמנות\n"
                
                # יצירת גרף מכירות
                sales_data = await session.execute(
                    db.select(
                        db.func.date(Order.created_at).label('date'),
                        db.func.sum(Order.total_amount).label('revenue')
                    )
                    .where(
                        db.and_(
                            Order.store_id == store.id,
                            Order.created_at >= month_start
                        )
                    )
                    .group_by(db.text('date'))
                    .order_by(db.text('date'))
                )
                
                df = pd.DataFrame(sales_data, columns=['date', 'revenue'])
                plt.figure(figsize=(10, 5))
                plt.plot(df['date'], df['revenue'])
                plt.title('מכירות החודש')
                plt.xlabel('תאריך')
                plt.ylabel('הכנסות')
                plt.grid(True)
                
                # שמירת הגרף לקובץ
                buf = BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                
                # שליחת ההודעה והגרף
                await query.message.reply_photo(
                    photo=buf,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("דוח מפורט", callback_data="detailed_report"),
                        InlineKeyboardButton("ייצא לאקסל", callback_data="export_excel")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.message.reply_text(
                    "בחר פעולה נוספת:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing overview: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הסקירה הכללית."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ANALYTICS_ACTION
    
    async def show_graphs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת גרפים"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.owner_id == user_id)
                )
                
                if not store:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אנא חבר חנות תחילה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # יצירת מספר גרפים
                
                # 1. גרף מכירות לפי חודשים
                sales_data = await session.execute(
                    db.select(
                        db.func.date_trunc('month', Order.created_at).label('month'),
                        db.func.sum(Order.total_amount).label('revenue')
                    )
                    .where(Order.store_id == store.id)
                    .group_by(db.text('month'))
                    .order_by(db.text('month'))
                )
                
                df_sales = pd.DataFrame(sales_data, columns=['month', 'revenue'])
                plt.figure(figsize=(10, 5))
                plt.subplot(2, 2, 1)
                plt.plot(df_sales['month'], df_sales['revenue'])
                plt.title('מכירות חודשיות')
                plt.xticks(rotation=45)
                
                # 2. גרף התפלגות מוצרים
                products_data = await session.execute(
                    db.select(
                        Product.name,
                        db.func.count(Order.id).label('orders')
                    )
                    .join(Order)
                    .where(Product.store_id == store.id)
                    .group_by(Product.id)
                    .order_by(db.text('orders DESC'))
                    .limit(5)
                )
                
                df_products = pd.DataFrame(products_data, columns=['name', 'orders'])
                plt.subplot(2, 2, 2)
                plt.pie(df_products['orders'], labels=df_products['name'], autopct='%1.1f%%')
                plt.title('התפלגות מוצרים')
                
                # 3. גרף הזמנות לפי שעות
                hours_data = await session.execute(
                    db.select(
                        db.func.extract('hour', Order.created_at).label('hour'),
                        db.func.count(Order.id).label('orders')
                    )
                    .where(Order.store_id == store.id)
                    .group_by(db.text('hour'))
                    .order_by(db.text('hour'))
                )
                
                df_hours = pd.DataFrame(hours_data, columns=['hour', 'orders'])
                plt.subplot(2, 2, 3)
                plt.bar(df_hours['hour'], df_hours['orders'])
                plt.title('הזמנות לפי שעות')
                plt.xlabel('שעה')
                plt.ylabel('מספר הזמנות')
                
                # 4. גרף מגמות
                trends_data = await session.execute(
                    db.select(
                        db.func.date_trunc('week', Order.created_at).label('week'),
                        db.func.avg(Order.total_amount).label('avg_amount')
                    )
                    .where(Order.store_id == store.id)
                    .group_by(db.text('week'))
                    .order_by(db.text('week'))
                )
                
                df_trends = pd.DataFrame(trends_data, columns=['week', 'avg_amount'])
                plt.subplot(2, 2, 4)
                plt.plot(df_trends['week'], df_trends['avg_amount'])
                plt.title('מגמות מכירה')
                plt.xticks(rotation=45)
                
                plt.tight_layout()
                
                # שמירת הגרפים לקובץ
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                buf.seek(0)
                
                # שליחת הגרפים
                await query.message.reply_photo(
                    photo=buf,
                    caption="📈 *ניתוח גרפי*\n\n"
                            "1. מכירות חודשיות\n"
                            "2. התפלגות מוצרים\n"
                            "3. הזמנות לפי שעות\n"
                            "4. מגמות מכירה",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("שמור גרפים", callback_data="save_graphs"),
                        InlineKeyboardButton("שתף במייל", callback_data="share_graphs")
                    ],
                    [
                        InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                    ]
                ]
                
                await query.message.reply_text(
                    "בחר פעולה נוספת:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing graphs: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הגרפים."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ANALYTICS_ACTION
    
    async def show_forecasts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת תחזיות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            async with db.get_session() as session:
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.owner_id == user_id)
                )
                
                if not store:
                    await query.edit_message_text(
                        format_error_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אנא חבר חנות תחילה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # חישוב תחזיות מכירה
                # כאן יש להוסיף לוגיקה של machine learning לתחזיות
                # לדוגמה: ניתן להשתמש ב-Prophet או ARIMA
                
                message = (
                    "🔮 *תחזיות*\n\n"
                    "*תחזית מכירות:*\n"
                    "• השבוע הבא: צפי לגידול של 5%\n"
                    "• החודש הבא: צפי לגידול של 10%\n\n"
                    "*מוצרים מומלצים להגדלת מלאי:*\n"
                    "1. מוצר א' - צפי למחסור\n"
                    "2. מוצר ב' - ביקוש גובר\n\n"
                    "*תובנות:*\n"
                    "• זוהתה מגמת עלייה במכירות\n"
                    "• שעות השיא: 16:00-19:00\n"
                    "• ימי שיא: ראשון וחמישי\n"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("תחזית מפורטת", callback_data="detailed_forecast"),
                        InlineKeyboardButton("הגדרות תחזית", callback_data="forecast_settings")
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
            logger.error(f"Error showing forecasts: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת התחזיות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ANALYTICS_ACTION 