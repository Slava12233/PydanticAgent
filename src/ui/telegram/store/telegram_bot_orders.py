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
    WooCommerceOrder as Order,
    WooCommerceOrderItem as OrderItem,
    WooCommerceProduct as Product
)
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.telegram_bot_utils import (
    format_price,
    format_date,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message
)

# Configure logging
logger = setup_logger('telegram_bot_orders')

# מצבי שיחה
(
    WAITING_FOR_ORDER_ACTION,
    WAITING_FOR_ORDER_ID,
    WAITING_FOR_ORDER_STATUS,
    WAITING_FOR_CANCEL_REASON,
    WAITING_FOR_REFUND_AMOUNT,
    WAITING_FOR_REFUND_REASON,
    WAITING_FOR_FILTER_CRITERIA
) = range(7)

# סטטוסים אפשריים להזמנה
ORDER_STATUSES = {
    'pending': 'ממתין לאישור',
    'processing': 'בטיפול',
    'shipped': 'נשלח',
    'delivered': 'נמסר',
    'cancelled': 'בוטל',
    'refunded': 'זוכה'
}

class TelegramBotOrders:
    """
    מחלקה לניהול הזמנות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_manage_orders_handler(self) -> ConversationHandler:
        """
        יצירת handler לניהול הזמנות
        
        Returns:
            ConversationHandler מוגדר לניהול הזמנות
        """
        return ConversationHandler(
            entry_points=[CommandHandler("manage_orders", self.manage_orders_start)],
            states={
                WAITING_FOR_ORDER_ACTION: [
                    CallbackQueryHandler(self.handle_order_action)
                ],
                WAITING_FOR_ORDER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_order_id)
                ],
                WAITING_FOR_ORDER_STATUS: [
                    CallbackQueryHandler(self.handle_order_status)
                ],
                WAITING_FOR_CANCEL_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_cancel_reason)
                ],
                WAITING_FOR_REFUND_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_refund_amount)
                ],
                WAITING_FOR_REFUND_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_refund_reason)
                ],
                WAITING_FOR_FILTER_CRITERIA: [
                    CallbackQueryHandler(self.handle_filter_criteria)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def manage_orders_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול הזמנות"""
        user_id = update.effective_user.id
        logger.info(f"Manage orders command from user {user_id}")
        
        # איפוס נתוני ההזמנה בקונטקסט
        context.user_data['order_management'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("הצג הזמנות אחרונות", callback_data="view_recent_orders"),
                InlineKeyboardButton("חפש הזמנה", callback_data="search_order")
            ],
            [
                InlineKeyboardButton("הזמנות לפי סטטוס", callback_data="filter_by_status"),
                InlineKeyboardButton("הזמנות היום", callback_data="today_orders")
            ],
            [
                InlineKeyboardButton("סטטיסטיקות הזמנות", callback_data="order_stats")
            ]
        ]
        
        await update.message.reply_text(
            "📦 *ניהול הזמנות*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_ORDER_ACTION
    
    async def handle_order_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת ניהול הזמנות"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['order_management']['action'] = action
        
        if action == "view_recent_orders":
            return await self.show_recent_orders(update, context)
            
        elif action == "search_order":
            await query.edit_message_text(
                "אנא הזן את מספר ההזמנה שברצונך לחפש:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_ORDER_ID
            
        elif action == "filter_by_status":
            keyboard = [[
                InlineKeyboardButton(status_text, callback_data=f"status_{status_code}")
            ] for status_code, status_text in ORDER_STATUSES.items()]
            
            await query.edit_message_text(
                "בחר סטטוס להצגת הזמנות:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_FOR_FILTER_CRITERIA
            
        elif action == "today_orders":
            return await self.show_today_orders(update, context)
            
        elif action == "order_stats":
            return await self.show_order_stats(update, context)
    
    async def show_recent_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הזמנות אחרונות"""
        query = update.callback_query
        
        try:
            async with db.get_session() as session:
                # קבלת 5 ההזמנות האחרונות
                recent_orders = await session.scalars(
                    db.select(Order)
                    .order_by(Order.created_at.desc())
                    .limit(5)
                )
                orders = list(recent_orders)
                
                if not orders:
                    await query.edit_message_text(
                        format_info_message("אין הזמנות במערכת."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # בניית הודעת הזמנות
                message = "📦 *הזמנות אחרונות:*\n\n"
                for order in orders:
                    message += (
                        f"🔹 *הזמנה #{order.id}*\n"
                        f"תאריך: {format_date(order.created_at)}\n"
                        f"סטטוס: {ORDER_STATUSES[order.status]}\n"
                        f"סכום: {format_price(order.total_amount)}\n"
                        f"פריטים: {len(order.items)}\n\n"
                    )
                
                keyboard = [[
                    InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                ]]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing recent orders: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת ההזמנות האחרונות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ORDER_ACTION
    
    async def handle_order_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בחיפוש הזמנה לפי מספר"""
        try:
            order_id = int(update.message.text)
            
            async with db.get_session() as session:
                order = await session.get(Order, order_id)
                
                if not order:
                    await update.message.reply_text(
                        format_error_message(f"לא נמצאה הזמנה מספר {order_id}."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_ORDER_ID
                
                # הצגת פרטי ההזמנה
                items_details = []
                total_items = 0
                for item in order.items:
                    product = await session.get(Product, item.product_id)
                    items_details.append(
                        f"• {item.quantity}x {product.name} - "
                        f"{format_price(item.price * item.quantity)}"
                    )
                    total_items += item.quantity
                
                message = (
                    f"📦 *פרטי הזמנה #{order.id}*\n\n"
                    f"📅 תאריך: {format_date(order.created_at)}\n"
                    f"📊 סטטוס: {ORDER_STATUSES[order.status]}\n"
                    f"💰 סכום כולל: {format_price(order.total_amount)}\n"
                    f"📝 פריטים ({total_items}):\n"
                    f"{chr(10).join(items_details)}\n\n"
                    f"🏠 כתובת למשלוח:\n"
                    f"{order.shipping_address}\n\n"
                    f"📞 פרטי קשר:\n"
                    f"שם: {order.customer_name}\n"
                    f"טלפון: {order.customer_phone}\n"
                    f"אימייל: {order.customer_email}\n"
                )
                
                if order.notes:
                    message += f"\n📝 הערות:\n{order.notes}\n"
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "עדכן סטטוס",
                            callback_data=f"update_status_{order.id}"
                        ),
                        InlineKeyboardButton(
                            "בטל הזמנה",
                            callback_data=f"cancel_order_{order.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "זיכוי הזמנה",
                            callback_data=f"refund_order_{order.id}"
                        ),
                        InlineKeyboardButton(
                            "חזור לתפריט",
                            callback_data="back_to_menu"
                        )
                    ]
                ]
                
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                return WAITING_FOR_ORDER_ACTION
                
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר הזמנה תקין."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_ORDER_ID
            
        except Exception as e:
            logger.error(f"Error handling order ID: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בחיפוש ההזמנה."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_ORDER_ID
    
    async def handle_order_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בעדכון סטטוס הזמנה"""
        query = update.callback_query
        await query.answer()
        
        try:
            # קבלת מזהה ההזמנה והסטטוס החדש
            _, order_id = query.data.split('_')[1:]
            order_id = int(order_id)
            
            keyboard = [[
                InlineKeyboardButton(status_text, callback_data=f"set_status_{order_id}_{status_code}")
            ] for status_code, status_text in ORDER_STATUSES.items()]
            
            await query.edit_message_text(
                f"בחר סטטוס חדש להזמנה #{order_id}:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return WAITING_FOR_ORDER_STATUS
            
        except Exception as e:
            logger.error(f"Error handling order status: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בעדכון הסטטוס."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_ORDER_ACTION
    
    async def handle_cancel_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בסיבת ביטול הזמנה"""
        order_id = context.user_data['order_management'].get('order_id')
        reason = update.message.text
        
        try:
            async with db.get_session() as session:
                order = await session.get(Order, order_id)
                if not order:
                    await update.message.reply_text(
                        format_error_message("ההזמנה לא נמצאה."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # עדכון סטטוס ההזמנה וסיבת הביטול
                order.status = 'cancelled'
                order.cancel_reason = reason
                await session.commit()
                
                await update.message.reply_text(
                    format_success_message(f"הזמנה #{order_id} בוטלה בהצלחה."),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בביטול ההזמנה."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    async def handle_refund_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בסכום הזיכוי"""
        try:
            refund_amount = float(update.message.text)
            if refund_amount <= 0:
                raise ValueError("הסכום חייב להיות חיובי")
            
            context.user_data['order_management']['refund_amount'] = refund_amount
            
            await update.message.reply_text(
                "אנא הזן את סיבת הזיכוי:",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_REFUND_REASON
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן סכום חיובי תקין."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_REFUND_AMOUNT
    
    async def handle_refund_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בסיבת הזיכוי"""
        order_id = context.user_data['order_management'].get('order_id')
        refund_amount = context.user_data['order_management'].get('refund_amount')
        reason = update.message.text
        
        try:
            async with db.get_session() as session:
                order = await session.get(Order, order_id)
                if not order:
                    await update.message.reply_text(
                        format_error_message("ההזמנה לא נמצאה."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # עדכון סטטוס ההזמנה ופרטי הזיכוי
                order.status = 'refunded'
                order.refund_amount = refund_amount
                order.refund_reason = reason
                await session.commit()
                
                await update.message.reply_text(
                    format_success_message(
                        f"הזמנה #{order_id} זוכתה בהצלחה.\n"
                        f"סכום הזיכוי: {format_price(refund_amount)}"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error refunding order: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בביצוע הזיכוי."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    async def handle_filter_criteria(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בסינון הזמנות לפי קריטריונים"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "back_to_menu":
                return await self.manage_orders_start(update, context)
            
            # קבלת הסטטוס לסינון
            status = query.data.split('_')[1]
            
            async with db.get_session() as session:
                # קבלת הזמנות לפי סטטוס
                orders = await session.scalars(
                    db.select(Order)
                    .where(Order.status == status)
                    .order_by(Order.created_at.desc())
                )
                orders = list(orders)
                
                if not orders:
                    await query.edit_message_text(
                        format_info_message(f"אין הזמנות בסטטוס {ORDER_STATUSES[status]}."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_ORDER_ACTION
                
                # בניית הודעת הזמנות
                message = f"📦 *הזמנות בסטטוס {ORDER_STATUSES[status]}:*\n\n"
                for order in orders:
                    message += (
                        f"🔹 *הזמנה #{order.id}*\n"
                        f"תאריך: {format_date(order.created_at)}\n"
                        f"סכום: {format_price(order.total_amount)}\n"
                        f"פריטים: {len(order.items)}\n\n"
                    )
                
                keyboard = [[
                    InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                ]]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error filtering orders: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בסינון ההזמנות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ORDER_ACTION
    
    async def show_today_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הזמנות של היום"""
        query = update.callback_query
        
        try:
            from datetime import datetime, time
            
            today_start = datetime.combine(datetime.today(), time.min)
            today_end = datetime.combine(datetime.today(), time.max)
            
            async with db.get_session() as session:
                # קבלת הזמנות של היום
                orders = await session.scalars(
                    db.select(Order)
                    .where(
                        db.and_(
                            Order.created_at >= today_start,
                            Order.created_at <= today_end
                        )
                    )
                    .order_by(Order.created_at.desc())
                )
                orders = list(orders)
                
                if not orders:
                    await query.edit_message_text(
                        format_info_message("אין הזמנות להיום."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_ORDER_ACTION
                
                # חישוב סטטיסטיקות
                total_amount = sum(order.total_amount for order in orders)
                total_items = sum(len(order.items) for order in orders)
                status_counts = {}
                for order in orders:
                    status_counts[order.status] = status_counts.get(order.status, 0) + 1
                
                # בניית הודעת סיכום
                message = (
                    "📅 *הזמנות היום:*\n\n"
                    f"סה\"כ הזמנות: {len(orders)}\n"
                    f"סה\"כ פריטים: {total_items}\n"
                    f"סה\"כ מכירות: {format_price(total_amount)}\n\n"
                    "*התפלגות סטטוסים:*\n"
                )
                
                for status, count in status_counts.items():
                    message += f"{ORDER_STATUSES[status]}: {count}\n"
                
                message += "\n*פירוט ההזמנות:*\n\n"
                
                for order in orders:
                    message += (
                        f"🔹 *הזמנה #{order.id}*\n"
                        f"שעה: {order.created_at.strftime('%H:%M')}\n"
                        f"סטטוס: {ORDER_STATUSES[order.status]}\n"
                        f"סכום: {format_price(order.total_amount)}\n"
                        f"פריטים: {len(order.items)}\n\n"
                    )
                
                keyboard = [[
                    InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                ]]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing today's orders: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הזמנות היום."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ORDER_ACTION
    
    async def show_order_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת סטטיסטיקות הזמנות"""
        query = update.callback_query
        
        try:
            from datetime import datetime, timedelta
            
            # חישוב תאריכים
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            async with db.get_session() as session:
                # סטטיסטיקות כלליות
                total_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                )
                
                total_amount = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                )
                
                # הזמנות השבוע
                week_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                    .where(Order.created_at >= week_ago)
                )
                
                week_amount = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                    .where(Order.created_at >= week_ago)
                )
                
                # הזמנות החודש
                month_orders = await session.scalar(
                    db.select(db.func.count(Order.id))
                    .where(Order.created_at >= month_ago)
                )
                
                month_amount = await session.scalar(
                    db.select(db.func.sum(Order.total_amount))
                    .where(Order.created_at >= month_ago)
                )
                
                # התפלגות סטטוסים
                status_counts = await session.execute(
                    db.select(
                        Order.status,
                        db.func.count(Order.id).label('count')
                    )
                    .group_by(Order.status)
                )
                status_stats = dict(status_counts)
                
                message = (
                    "📊 *סטטיסטיקות הזמנות*\n\n"
                    "*סה\"כ:*\n"
                    f"• הזמנות: {total_orders:,}\n"
                    f"• מכירות: {format_price(total_amount or 0)}\n\n"
                    "*השבוע האחרון:*\n"
                    f"• הזמנות: {week_orders:,}\n"
                    f"• מכירות: {format_price(week_amount or 0)}\n\n"
                    "*החודש האחרון:*\n"
                    f"• הזמנות: {month_orders:,}\n"
                    f"• מכירות: {format_price(month_amount or 0)}\n\n"
                    "*התפלגות סטטוסים:*\n"
                )
                
                for status, count in status_stats.items():
                    message += f"• {ORDER_STATUSES[status]}: {count:,}\n"
                
                keyboard = [[
                    InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                ]]
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing order stats: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הסטטיסטיקות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_ORDER_ACTION 