import logging
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler
)
from telegram.constants import ParseMode

from src.database import db
from src.database.models import (
    User,
    WooCommerceStore as Store,
    WooCommerceOrder as Order,
    WooCommercePayment as Payment
)
from src.database.operations import get_user_by_telegram_id
from src.core.config import PAYMENT_PROVIDER_TOKEN
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
logger = setup_logger('telegram_bot_payments')

# מצבי שיחה
(
    WAITING_FOR_PAYMENT_ACTION,
    WAITING_FOR_PAYMENT_AMOUNT,
    WAITING_FOR_PAYMENT_DESCRIPTION,
    WAITING_FOR_PAYMENT_METHOD,
    WAITING_FOR_PAYMENT_CONFIRMATION,
    WAITING_FOR_REFUND_AMOUNT,
    WAITING_FOR_REFUND_REASON
) = range(7)

# סוגי תשלום
PAYMENT_METHODS = {
    'credit_card': 'כרטיס אשראי',
    'bit': 'ביט',
    'paypal': 'PayPal',
    'bank_transfer': 'העברה בנקאית',
    'cash': 'מזומן'
}

class TelegramBotPayments:
    """
    מחלקה לניהול תשלומים בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_manage_payments_handler(self) -> ConversationHandler:
        """
        יצירת handler לניהול תשלומים
        
        Returns:
            ConversationHandler מוגדר לניהול תשלומים
        """
        return ConversationHandler(
            entry_points=[CommandHandler("manage_payments", self.manage_payments_start)],
            states={
                WAITING_FOR_PAYMENT_ACTION: [
                    CallbackQueryHandler(self.handle_payment_action)
                ],
                WAITING_FOR_PAYMENT_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_payment_amount)
                ],
                WAITING_FOR_PAYMENT_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_payment_description)
                ],
                WAITING_FOR_PAYMENT_METHOD: [
                    CallbackQueryHandler(self.handle_payment_method)
                ],
                WAITING_FOR_PAYMENT_CONFIRMATION: [
                    CallbackQueryHandler(self.handle_payment_confirmation)
                ],
                WAITING_FOR_REFUND_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_refund_amount)
                ],
                WAITING_FOR_REFUND_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_refund_reason)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def manage_payments_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול תשלומים"""
        user_id = update.effective_user.id
        logger.info(f"Manage payments command from user {user_id}")
        
        # איפוס נתוני התשלום בקונטקסט
        context.user_data['payment'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("קבל תשלום", callback_data="receive_payment"),
                InlineKeyboardButton("בצע החזר", callback_data="make_refund")
            ],
            [
                InlineKeyboardButton("תשלומים אחרונים", callback_data="recent_payments"),
                InlineKeyboardButton("דוח תשלומים", callback_data="payment_report")
            ],
            [
                InlineKeyboardButton("הגדרות תשלום", callback_data="payment_settings")
            ]
        ]
        
        await update.message.reply_text(
            "💳 *ניהול תשלומים*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_PAYMENT_ACTION
    
    async def handle_payment_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת תשלום"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['payment_action'] = action
        
        if action == "receive_payment":
            await query.edit_message_text(
                "💰 *קבלת תשלום*\n\n"
                "אנא הזן את סכום התשלום (במספרים בלבד):",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PAYMENT_AMOUNT
            
        elif action == "make_refund":
            await query.edit_message_text(
                "↩️ *ביצוע החזר*\n\n"
                "אנא הזן את סכום ההחזר (במספרים בלבד):",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_REFUND_AMOUNT
            
        elif action == "recent_payments":
            return await self.show_recent_payments(update, context)
            
        elif action == "payment_report":
            return await self.show_payment_report(update, context)
            
        elif action == "payment_settings":
            return await self.show_payment_settings(update, context)
    
    async def handle_payment_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סכום התשלום"""
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("הסכום חייב להיות חיובי")
            
            context.user_data['payment']['amount'] = amount
            
            await update.message.reply_text(
                "מעולה! עכשיו אנא הזן תיאור לתשלום:",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_PAYMENT_DESCRIPTION
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PAYMENT_AMOUNT
    
    async def handle_payment_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור התשלום"""
        description = update.message.text
        context.user_data['payment']['description'] = description
        
        keyboard = [[
            InlineKeyboardButton(text, callback_data=f"method_{code}")
        ] for code, text in PAYMENT_METHODS.items()]
        
        await update.message.reply_text(
            "בחר את אמצעי התשלום:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_PAYMENT_METHOD
    
    async def handle_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת אמצעי תשלום"""
        query = update.callback_query
        await query.answer()
        
        method = query.data.split('_')[1]
        context.user_data['payment']['method'] = method
        
        payment = context.user_data['payment']
        summary = (
            "💳 *סיכום התשלום:*\n\n"
            f"סכום: {format_price(payment['amount'])}\n"
            f"תיאור: {payment['description']}\n"
            f"אמצעי תשלום: {PAYMENT_METHODS[payment['method']]}\n\n"
            "האם לבצע את התשלום?"
        )
        
        keyboard = [[
            InlineKeyboardButton("כן, בצע תשלום", callback_data="confirm_payment"),
            InlineKeyboardButton("לא, בטל", callback_data="cancel_payment")
        ]]
        
        await query.edit_message_text(
            summary,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_PAYMENT_CONFIRMATION
    
    async def handle_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """אישור ביצוע התשלום"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm_payment":
            try:
                payment_data = context.user_data['payment']
                user_id = update.effective_user.id
                
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
                    
                    # יצירת התשלום
                    payment = Payment(
                        store_id=store.id,
                        amount=payment_data['amount'],
                        description=payment_data['description'],
                        method=payment_data['method'],
                        status='pending'
                    )
                    session.add(payment)
                    await session.commit()
                    
                    # טיפול בתשלום לפי סוג אמצעי התשלום
                    if payment_data['method'] == 'credit_card':
                        # שליחת בקשת תשלום בכרטיס אשראי
                        await query.message.reply_invoice(
                            title=payment_data['description'],
                            description=f"תשלום עבור {payment_data['description']}",
                            payload=str(payment.id),
                            provider_token=PAYMENT_PROVIDER_TOKEN,
                            currency="ILS",
                            prices=[LabeledPrice("סכום", int(payment_data['amount'] * 100))]
                        )
                        
                    elif payment_data['method'] == 'bit':
                        # הצגת פרטי תשלום ביט
                        bit_details = (
                            "📱 *תשלום באמצעות ביט*\n\n"
                            f"סכום: {format_price(payment_data['amount'])}\n"
                            f"מספר טלפון לתשלום: {store.phone}\n\n"
                            "אנא שלח צילום מסך של אישור התשלום."
                        )
                        await query.edit_message_text(
                            bit_details,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                    elif payment_data['method'] == 'bank_transfer':
                        # הצגת פרטי חשבון בנק
                        bank_details = (
                            "🏦 *תשלום בהעברה בנקאית*\n\n"
                            f"סכום: {format_price(payment_data['amount'])}\n"
                            "פרטי חשבון:\n"
                            f"בנק: {store.bank_name}\n"
                            f"סניף: {store.bank_branch}\n"
                            f"חשבון: {store.bank_account}\n\n"
                            "אנא שלח אישור העברה."
                        )
                        await query.edit_message_text(
                            bank_details,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                    else:
                        await query.edit_message_text(
                            format_success_message(
                                f"התשלום נוצר בהצלחה!\n"
                                f"מזהה תשלום: {payment.id}"
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                
            except Exception as e:
                logger.error(f"Error processing payment: {e}")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בביצוע התשלום: {str(e)}"),
                    parse_mode=ParseMode.MARKDOWN
                )
            
        elif query.data == "cancel_payment":
            await query.edit_message_text(
                format_info_message("התשלום בוטל."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def handle_refund_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סכום ההחזר"""
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("הסכום חייב להיות חיובי")
            
            context.user_data['refund'] = {'amount': amount}
            
            await update.message.reply_text(
                "אנא הזן את סיבת ההחזר:",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_REFUND_REASON
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_REFUND_AMOUNT
    
    async def handle_refund_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת סיבת ההחזר"""
        reason = update.message.text
        refund_data = context.user_data['refund']
        refund_data['reason'] = reason
        
        try:
            user_id = update.effective_user.id
            
            async with db.get_session() as session:
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.owner_id == user_id)
                )
                
                if not store:
                    await update.message.reply_text(
                        format_error_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אנא חבר חנות תחילה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # יצירת ההחזר
                refund = Payment(
                    store_id=store.id,
                    amount=-refund_data['amount'],  # סכום שלילי להחזר
                    description=f"החזר: {refund_data['reason']}",
                    method='refund',
                    status='completed'
                )
                session.add(refund)
                await session.commit()
                
                await update.message.reply_text(
                    format_success_message(
                        f"ההחזר בוצע בהצלחה!\n"
                        f"סכום: {format_price(refund_data['amount'])}\n"
                        f"סיבה: {refund_data['reason']}"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            await update.message.reply_text(
                format_error_message(f"אירעה שגיאה בביצוע ההחזר: {str(e)}"),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_recent_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת תשלומים אחרונים"""
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
                
                # קבלת 10 התשלומים האחרונים
                recent_payments = await session.scalars(
                    db.select(Payment)
                    .where(Payment.store_id == store.id)
                    .order_by(Payment.created_at.desc())
                    .limit(10)
                )
                payments = list(recent_payments)
                
                if not payments:
                    await query.edit_message_text(
                        format_info_message("אין תשלומים במערכת."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                message = "💳 *תשלומים אחרונים:*\n\n"
                
                for payment in payments:
                    message += (
                        f"{'🔴 החזר' if payment.amount < 0 else '🟢 תשלום'}\n"
                        f"סכום: {format_price(abs(payment.amount))}\n"
                        f"תיאור: {payment.description}\n"
                        f"אמצעי תשלום: {PAYMENT_METHODS.get(payment.method, payment.method)}\n"
                        f"סטטוס: {payment.status}\n"
                        f"תאריך: {format_date(payment.created_at)}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("קבל תשלום", callback_data="receive_payment"),
                        InlineKeyboardButton("בצע החזר", callback_data="make_refund")
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
            logger.error(f"Error showing recent payments: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת התשלומים האחרונים."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_PAYMENT_ACTION
    
    async def show_payment_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת דוח תשלומים"""
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
                
                # חישוב סטטיסטיקות תשלומים
                total_payments = await session.scalar(
                    db.select(db.func.count(Payment.id))
                    .where(
                        db.and_(
                            Payment.store_id == store.id,
                            Payment.amount > 0
                        )
                    )
                )
                
                total_refunds = await session.scalar(
                    db.select(db.func.count(Payment.id))
                    .where(
                        db.and_(
                            Payment.store_id == store.id,
                            Payment.amount < 0
                        )
                    )
                )
                
                total_income = await session.scalar(
                    db.select(db.func.sum(Payment.amount))
                    .where(
                        db.and_(
                            Payment.store_id == store.id,
                            Payment.amount > 0
                        )
                    )
                )
                
                total_refunded = await session.scalar(
                    db.select(db.func.sum(db.func.abs(Payment.amount)))
                    .where(
                        db.and_(
                            Payment.store_id == store.id,
                            Payment.amount < 0
                        )
                    )
                )
                
                # התפלגות לפי אמצעי תשלום
                payment_methods = await session.execute(
                    db.select(
                        Payment.method,
                        db.func.count(Payment.id).label('count'),
                        db.func.sum(Payment.amount).label('total')
                    )
                    .where(Payment.store_id == store.id)
                    .group_by(Payment.method)
                )
                
                message = (
                    "📊 *דוח תשלומים*\n\n"
                    "*סיכום:*\n"
                    f"• סה\"כ תשלומים: {format_number(total_payments)}\n"
                    f"• סה\"כ החזרים: {format_number(total_refunds)}\n"
                    f"• סה\"כ הכנסות: {format_price(total_income or 0)}\n"
                    f"• סה\"כ החזרים: {format_price(total_refunded or 0)}\n"
                    f"• נטו: {format_price((total_income or 0) - (total_refunded or 0))}\n\n"
                    "*התפלגות לפי אמצעי תשלום:*\n"
                )
                
                for method, count, total in payment_methods:
                    message += (
                        f"• {PAYMENT_METHODS.get(method, method)}:\n"
                        f"  - עסקאות: {format_number(count)}\n"
                        f"  - סה\"כ: {format_price(total)}\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("ייצא לאקסל", callback_data="export_report"),
                        InlineKeyboardButton("שלח במייל", callback_data="email_report")
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
            logger.error(f"Error showing payment report: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת דוח התשלומים."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_PAYMENT_ACTION
    
    async def show_payment_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת הגדרות תשלום"""
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
                    "⚙️ *הגדרות תשלום*\n\n"
                    "*פרטי חשבון בנק:*\n"
                    f"• בנק: {store.bank_name or 'לא הוגדר'}\n"
                    f"• סניף: {store.bank_branch or 'לא הוגדר'}\n"
                    f"• חשבון: {store.bank_account or 'לא הוגדר'}\n\n"
                    "*אמצעי תשלום פעילים:*\n"
                    "• כרטיס אשראי: ✅\n"
                    "• ביט: ✅\n"
                    "• PayPal: ❌\n"
                    "• העברה בנקאית: ✅\n"
                    "• מזומן: ✅\n"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("עדכן פרטי בנק", callback_data="update_bank"),
                        InlineKeyboardButton("אמצעי תשלום", callback_data="payment_methods")
                    ],
                    [
                        InlineKeyboardButton("הגדר API", callback_data="setup_api"),
                        InlineKeyboardButton("עמלות", callback_data="fees")
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
            logger.error(f"Error showing payment settings: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הגדרות התשלום."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_PAYMENT_ACTION 