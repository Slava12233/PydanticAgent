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

from src.database import db
from src.database.models import (
    User,
    WooCommerceStore as Store,
    WooCommerceOrder as Order,
    WooCommerceShipping as Shipping
)
from src.database.operations import get_user_by_telegram_id
from src.utils.logger import setup_logger
from .telegram_bot_utils import (
    format_price,
    format_date,
    format_number,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message
)

# Configure logging
logger = setup_logger('telegram_bot_shipping')

# מצבי שיחה
(
    WAITING_FOR_SHIPPING_ACTION,
    WAITING_FOR_SHIPPING_METHOD,
    WAITING_FOR_SHIPPING_ADDRESS,
    WAITING_FOR_SHIPPING_NOTES,
    WAITING_FOR_SHIPPING_CONFIRMATION,
    WAITING_FOR_TRACKING_NUMBER,
    WAITING_FOR_DELIVERY_STATUS,
    WAITING_FOR_DELIVERY_NOTES
) = range(8)

# סוגי משלוח
SHIPPING_METHODS = {
    'self_pickup': 'איסוף עצמי',
    'store_delivery': 'משלוח מהחנות',
    'courier': 'שליח',
    'post_office': 'דואר ישראל',
    'express': 'משלוח אקספרס'
}

# סטטוסי משלוח
SHIPPING_STATUSES = {
    'pending': 'ממתין למשלוח',
    'processing': 'בהכנה',
    'shipped': 'נשלח',
    'in_transit': 'בדרך',
    'delivered': 'נמסר',
    'failed': 'נכשל',
    'returned': 'הוחזר'
}

class TelegramBotShipping:
    """
    מחלקה לניהול משלוחים בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_manage_shipping_handler(self) -> ConversationHandler:
        """
        יצירת handler לניהול משלוחים
        
        Returns:
            ConversationHandler מוגדר לניהול משלוחים
        """
        return ConversationHandler(
            entry_points=[CommandHandler("manage_shipping", self.manage_shipping_start)],
            states={
                WAITING_FOR_SHIPPING_ACTION: [
                    CallbackQueryHandler(self.handle_shipping_action)
                ],
                WAITING_FOR_SHIPPING_METHOD: [
                    CallbackQueryHandler(self.handle_shipping_method)
                ],
                WAITING_FOR_SHIPPING_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_shipping_address)
                ],
                WAITING_FOR_SHIPPING_NOTES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_shipping_notes)
                ],
                WAITING_FOR_SHIPPING_CONFIRMATION: [
                    CallbackQueryHandler(self.handle_shipping_confirmation)
                ],
                WAITING_FOR_TRACKING_NUMBER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_tracking_number)
                ],
                WAITING_FOR_DELIVERY_STATUS: [
                    CallbackQueryHandler(self.handle_delivery_status)
                ],
                WAITING_FOR_DELIVERY_NOTES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_delivery_notes)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def manage_shipping_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול משלוחים"""
        user_id = update.effective_user.id
        logger.info(f"Manage shipping command from user {user_id}")
        
        # איפוס נתוני המשלוח בקונטקסט
        context.user_data['shipping'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("משלוחים להיום", callback_data="today_deliveries"),
                InlineKeyboardButton("משלוחים בדרך", callback_data="in_transit")
            ],
            [
                InlineKeyboardButton("הזמנות לאיסוף", callback_data="pending_pickup"),
                InlineKeyboardButton("עדכן סטטוס", callback_data="update_status")
            ],
            [
                InlineKeyboardButton("הגדרות משלוחים", callback_data="shipping_settings")
            ]
        ]
        
        await update.message.reply_text(
            "🚚 *ניהול משלוחים*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_SHIPPING_ACTION
    
    async def handle_shipping_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת משלוח"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['shipping_action'] = action
        
        if action == "today_deliveries":
            return await self.show_today_deliveries(update, context)
            
        elif action == "in_transit":
            return await self.show_in_transit(update, context)
            
        elif action == "pending_pickup":
            return await self.show_pending_pickup(update, context)
            
        elif action == "update_status":
            await query.edit_message_text(
                "📦 *עדכון סטטוס משלוח*\n\n"
                "אנא הזן את מספר המשלוח:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_TRACKING_NUMBER
            
        elif action == "shipping_settings":
            return await self.show_shipping_settings(update, context)
    
    async def show_today_deliveries(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת משלוחים להיום"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            from datetime import datetime, time
            
            today_start = datetime.combine(datetime.today(), time.min)
            today_end = datetime.combine(datetime.today(), time.max)
            
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
                
                # קבלת משלוחים להיום
                deliveries = await session.scalars(
                    db.select(Shipping)
                    .where(
                        db.and_(
                            Shipping.store_id == store.id,
                            Shipping.delivery_date >= today_start,
                            Shipping.delivery_date <= today_end
                        )
                    )
                    .order_by(Shipping.delivery_date)
                )
                deliveries = list(deliveries)
                
                if not deliveries:
                    await query.edit_message_text(
                        format_info_message("אין משלוחים מתוכננים להיום."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_SHIPPING_ACTION
                
                message = "📅 *משלוחים להיום:*\n\n"
                
                for delivery in deliveries:
                    # קבלת ההזמנה המקושרת
                    order = await session.get(Order, delivery.order_id)
                    
                    message += (
                        f"🕒 {delivery.delivery_date.strftime('%H:%M')}\n"
                        f"📦 משלוח #{delivery.id}\n"
                        f"🛍️ הזמנה #{order.id}\n"
                        f"📍 כתובת: {delivery.address}\n"
                        f"📱 טלפון: {order.customer_phone}\n"
                        f"💰 לגבייה: {format_price(order.total_amount)}\n"
                        f"📝 הערות: {delivery.notes or 'אין'}\n"
                        f"🚚 סטטוס: {SHIPPING_STATUSES[delivery.status]}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("עדכן סטטוס", callback_data=f"update_status_{delivery.id}")
                        for delivery in deliveries[:2]  # מקסימום 2 כפתורים בשורה
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
            logger.error(f"Error showing today's deliveries: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת המשלוחים להיום."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SHIPPING_ACTION
    
    async def show_in_transit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת משלוחים בדרך"""
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
                
                # קבלת משלוחים בדרך
                in_transit = await session.scalars(
                    db.select(Shipping)
                    .where(
                        db.and_(
                            Shipping.store_id == store.id,
                            Shipping.status.in_(['shipped', 'in_transit'])
                        )
                    )
                    .order_by(Shipping.delivery_date)
                )
                deliveries = list(in_transit)
                
                if not deliveries:
                    await query.edit_message_text(
                        format_info_message("אין משלוחים בדרך כרגע."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_SHIPPING_ACTION
                
                message = "🚚 *משלוחים בדרך:*\n\n"
                
                for delivery in deliveries:
                    # קבלת ההזמנה המקושרת
                    order = await session.get(Order, delivery.order_id)
                    
                    message += (
                        f"📦 משלוח #{delivery.id}\n"
                        f"🛍️ הזמנה #{order.id}\n"
                        f"📅 תאריך משלוח: {format_date(delivery.delivery_date)}\n"
                        f"📍 כתובת: {delivery.address}\n"
                        f"🚚 שיטת משלוח: {SHIPPING_METHODS[delivery.method]}\n"
                        f"📝 מספר מעקב: {delivery.tracking_number or 'אין'}\n"
                        f"⏳ סטטוס: {SHIPPING_STATUSES[delivery.status]}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("סמן כנמסר", callback_data=f"mark_delivered_{delivery.id}")
                        for delivery in deliveries[:2]
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
            logger.error(f"Error showing in-transit deliveries: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת המשלוחים בדרך."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SHIPPING_ACTION
    
    async def show_pending_pickup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הזמנות לאיסוף עצמי"""
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
                
                # קבלת הזמנות לאיסוף
                pickups = await session.scalars(
                    db.select(Shipping)
                    .where(
                        db.and_(
                            Shipping.store_id == store.id,
                            Shipping.method == 'self_pickup',
                            Shipping.status == 'pending'
                        )
                    )
                    .order_by(Shipping.delivery_date)
                )
                deliveries = list(pickups)
                
                if not deliveries:
                    await query.edit_message_text(
                        format_info_message("אין הזמנות הממתינות לאיסוף."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return WAITING_FOR_SHIPPING_ACTION
                
                message = "🏪 *הזמנות לאיסוף:*\n\n"
                
                for delivery in deliveries:
                    # קבלת ההזמנה המקושרת
                    order = await session.get(Order, delivery.order_id)
                    
                    message += (
                        f"🛍️ הזמנה #{order.id}\n"
                        f"👤 שם: {order.customer_name}\n"
                        f"📱 טלפון: {order.customer_phone}\n"
                        f"📅 תאריך איסוף: {format_date(delivery.delivery_date)}\n"
                        f"💰 לתשלום: {format_price(order.total_amount)}\n"
                        f"📝 הערות: {delivery.notes or 'אין'}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("סמן כנאסף", callback_data=f"mark_picked_{delivery.id}")
                        for delivery in deliveries[:2]
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
            logger.error(f"Error showing pending pickups: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת ההזמנות לאיסוף."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SHIPPING_ACTION
    
    async def handle_tracking_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהזנת מספר מעקב"""
        tracking_number = update.message.text
        context.user_data['shipping']['tracking_number'] = tracking_number
        
        keyboard = [[
            InlineKeyboardButton(text, callback_data=f"status_{code}")
        ] for code, text in SHIPPING_STATUSES.items()]
        
        await update.message.reply_text(
            "בחר את הסטטוס החדש:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_DELIVERY_STATUS
    
    async def handle_delivery_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בעדכון סטטוס משלוח"""
        query = update.callback_query
        await query.answer()
        
        status = query.data.split('_')[1]
        context.user_data['shipping']['status'] = status
        
        await query.edit_message_text(
            "אנא הזן הערות לעדכון הסטטוס (או 'אין'):",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_DELIVERY_NOTES
    
    async def handle_delivery_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בהערות למשלוח"""
        notes = update.message.text
        shipping_data = context.user_data['shipping']
        
        try:
            async with db.get_session() as session:
                # קבלת המשלוח לפי מספר מעקב
                shipping = await session.scalar(
                    db.select(Shipping)
                    .where(Shipping.tracking_number == shipping_data['tracking_number'])
                )
                
                if not shipping:
                    await update.message.reply_text(
                        format_error_message("לא נמצא משלוח עם מספר המעקב שהוזן."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # עדכון סטטוס המשלוח
                shipping.status = shipping_data['status']
                shipping.notes = None if notes.lower() == 'אין' else notes
                await session.commit()
                
                await update.message.reply_text(
                    format_success_message(
                        f"סטטוס המשלוח עודכן בהצלחה!\n"
                        f"סטטוס חדש: {SHIPPING_STATUSES[shipping.status]}"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error updating shipping status: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בעדכון סטטוס המשלוח."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_shipping_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הגדרות משלוחים"""
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
                
                message = (
                    "⚙️ *הגדרות משלוחים*\n\n"
                    "*שיטות משלוח פעילות:*\n"
                    "• איסוף עצמי: ✅\n"
                    "• משלוח מהחנות: ✅\n"
                    "• שליח: ✅\n"
                    "• דואר ישראל: ❌\n"
                    "• משלוח אקספרס: ✅\n\n"
                    "*מחירי משלוח:*\n"
                    "• משלוח רגיל: ₪30\n"
                    "• משלוח מהיר: ₪50\n"
                    "• משלוח אקספרס: ₪70\n\n"
                    "*אזורי חלוקה:*\n"
                    "• מרכז: ✅\n"
                    "• צפון: ❌\n"
                    "• דרום: ❌\n"
                    "• ירושלים: ✅\n"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("הגדר שיטות משלוח", callback_data="set_methods"),
                        InlineKeyboardButton("הגדר מחירים", callback_data="set_prices")
                    ],
                    [
                        InlineKeyboardButton("הגדר אזורים", callback_data="set_areas"),
                        InlineKeyboardButton("זמני משלוח", callback_data="delivery_times")
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
            logger.error(f"Error showing shipping settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הגדרות המשלוחים."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_SHIPPING_ACTION 