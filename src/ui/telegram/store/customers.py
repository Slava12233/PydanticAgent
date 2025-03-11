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
    WooCommerceCustomer as Customer
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
    is_valid_email,
    is_valid_phone
)

# Configure logging
logger = setup_logger('telegram_bot_customers')

# מצבי שיחה
(
    WAITING_FOR_CUSTOMER_ACTION,
    WAITING_FOR_CUSTOMER_NAME,
    WAITING_FOR_CUSTOMER_PHONE,
    WAITING_FOR_CUSTOMER_EMAIL,
    WAITING_FOR_CUSTOMER_ADDRESS,
    WAITING_FOR_CUSTOMER_NOTES,
    WAITING_FOR_CUSTOMER_CONFIRMATION,
    WAITING_FOR_CUSTOMER_SEARCH,
    WAITING_FOR_CUSTOMER_EDIT,
    WAITING_FOR_CUSTOMER_DELETE
) = range(10)

class TelegramBotCustomers:
    """
    מחלקה לניהול לקוחות בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_manage_customers_handler(self) -> ConversationHandler:
        """
        יצירת handler לניהול לקוחות
        
        Returns:
            ConversationHandler מוגדר לניהול לקוחות
        """
        return ConversationHandler(
            entry_points=[CommandHandler("manage_customers", self.manage_customers_start)],
            states={
                WAITING_FOR_CUSTOMER_ACTION: [
                    CallbackQueryHandler(self.handle_customer_action)
                ],
                WAITING_FOR_CUSTOMER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_name)
                ],
                WAITING_FOR_CUSTOMER_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_phone)
                ],
                WAITING_FOR_CUSTOMER_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_email)
                ],
                WAITING_FOR_CUSTOMER_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_address)
                ],
                WAITING_FOR_CUSTOMER_NOTES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_notes)
                ],
                WAITING_FOR_CUSTOMER_CONFIRMATION: [
                    CallbackQueryHandler(self.handle_customer_confirmation)
                ],
                WAITING_FOR_CUSTOMER_SEARCH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_customer_search)
                ],
                WAITING_FOR_CUSTOMER_EDIT: [
                    CallbackQueryHandler(self.handle_customer_edit)
                ],
                WAITING_FOR_CUSTOMER_DELETE: [
                    CallbackQueryHandler(self.handle_customer_delete)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def manage_customers_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך ניהול לקוחות"""
        user_id = update.effective_user.id
        logger.info(f"Manage customers command from user {user_id}")
        
        # איפוס נתוני הלקוח בקונטקסט
        context.user_data['customer'] = {}
        
        keyboard = [
            [
                InlineKeyboardButton("הוסף לקוח חדש", callback_data="add_customer"),
                InlineKeyboardButton("חפש לקוח", callback_data="search_customer")
            ],
            [
                InlineKeyboardButton("לקוחות אחרונים", callback_data="recent_customers"),
                InlineKeyboardButton("לקוחות מועדפים", callback_data="vip_customers")
            ],
            [
                InlineKeyboardButton("ייצוא רשימת לקוחות", callback_data="export_customers")
            ]
        ]
        
        await update.message.reply_text(
            "👥 *ניהול לקוחות*\n\n"
            "מה תרצה לעשות?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_CUSTOMER_ACTION
    
    async def handle_customer_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """טיפול בבחירת פעולת ניהול לקוחות"""
        query = update.callback_query
        await query.answer()
        
        action = query.data
        context.user_data['customer_action'] = action
        
        if action == "add_customer":
            await query.edit_message_text(
                "👤 *הוספת לקוח חדש*\n\n"
                "אנא הזן את שם הלקוח:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_CUSTOMER_NAME
            
        elif action == "search_customer":
            await query.edit_message_text(
                "🔍 *חיפוש לקוח*\n\n"
                "אנא הזן שם, טלפון או אימייל של הלקוח:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_CUSTOMER_SEARCH
            
        elif action == "recent_customers":
            return await self.show_recent_customers(update, context)
            
        elif action == "vip_customers":
            return await self.show_vip_customers(update, context)
            
        elif action == "export_customers":
            return await self.export_customers(update, context)
    
    async def handle_customer_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם הלקוח"""
        name = update.message.text
        context.user_data['customer']['name'] = name
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא הזן את מספר הטלפון של הלקוח:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_CUSTOMER_PHONE
    
    async def handle_customer_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת טלפון הלקוח"""
        phone = update.message.text
        
        if not is_valid_phone(phone):
            await update.message.reply_text(
                format_error_message("מספר הטלפון אינו תקין. אנא נסה שוב."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_CUSTOMER_PHONE
        
        context.user_data['customer']['phone'] = phone
        
        await update.message.reply_text(
            "מצוין! עכשיו אנא הזן את כתובת האימייל של הלקוח:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_CUSTOMER_EMAIL
    
    async def handle_customer_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת אימייל הלקוח"""
        email = update.message.text
        
        if not is_valid_email(email):
            await update.message.reply_text(
                format_error_message("כתובת האימייל אינה תקינה. אנא נסה שוב."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_CUSTOMER_EMAIL
        
        context.user_data['customer']['email'] = email
        
        await update.message.reply_text(
            "יופי! עכשיו אנא הזן את כתובת המשלוח של הלקוח:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_CUSTOMER_ADDRESS
    
    async def handle_customer_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כתובת הלקוח"""
        address = update.message.text
        context.user_data['customer']['address'] = address
        
        await update.message.reply_text(
            "כמעט סיימנו! אנא הזן הערות נוספות על הלקוח (אופציונלי).\n"
            "אם אין הערות, הקלד 'אין':",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_CUSTOMER_NOTES
    
    async def handle_customer_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת הערות על הלקוח"""
        notes = update.message.text
        context.user_data['customer']['notes'] = None if notes.lower() == 'אין' else notes
        
        # הצגת סיכום פרטי הלקוח
        customer = context.user_data['customer']
        summary = (
            "👤 *סיכום פרטי הלקוח:*\n\n"
            f"שם: {customer['name']}\n"
            f"טלפון: {customer['phone']}\n"
            f"אימייל: {customer['email']}\n"
            f"כתובת: {customer['address']}\n"
            f"הערות: {customer['notes'] or 'אין'}\n\n"
            "האם לשמור את פרטי הלקוח?"
        )
        
        keyboard = [[
            InlineKeyboardButton("כן, שמור", callback_data="save_customer"),
            InlineKeyboardButton("לא, בטל", callback_data="cancel_customer")
        ]]
        
        await update.message.reply_text(
            summary,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return WAITING_FOR_CUSTOMER_CONFIRMATION
    
    async def handle_customer_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """אישור שמירת הלקוח"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "save_customer":
            try:
                customer_data = context.user_data['customer']
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
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return ConversationHandler.END
                    
                    # בדיקה אם כבר יש חנות למשתמש
                    store = await session.scalar(
                        db.select(Store)
                        .where(Store.user_id == user.id)
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
                    
                    # בדיקה אם הלקוח כבר קיים
                    existing_customer = await session.scalar(
                        db.select(Customer)
                        .where(
                            db.or_(
                                Customer.phone == customer_data['phone'],
                                Customer.email == customer_data['email']
                            )
                        )
                    )
                    
                    if existing_customer:
                        await query.edit_message_text(
                            format_warning_message(
                                "לקוח עם מספר טלפון או אימייל זהה כבר קיים במערכת."
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return ConversationHandler.END
                    
                    # יצירת הלקוח
                    customer = Customer(
                        store_id=store.id,
                        name=customer_data['name'],
                        phone=customer_data['phone'],
                        email=customer_data['email'],
                        address=customer_data['address'],
                        notes=customer_data['notes']
                    )
                    session.add(customer)
                    await session.commit()
                
                await query.edit_message_text(
                    format_success_message("הלקוח נשמר בהצלחה! 🎉"),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                logger.error(f"Error saving customer: {e}")
                error_message = str(e)
                # מנקה תווים מיוחדים של Markdown מהודעת השגיאה
                error_message = error_message.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בשמירת הלקוח: {error_message}"),
                    parse_mode=ParseMode.MARKDOWN
                )
            
        elif query.data == "cancel_customer":
            await query.edit_message_text(
                format_info_message("הוספת הלקוח בוטלה."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def handle_customer_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """חיפוש לקוח"""
        search_query = update.message.text
        user_id = update.effective_user.id
        
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
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.user_id == user.id)
                )
                
                if not store:
                    await update.message.reply_text(
                        format_error_message(
                            "לא נמצאה חנות מחוברת.\n"
                            "אנא חבר חנות תחילה בעזרת הפקודה /connect_store."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # חיפוש לקוחות
                customers = await session.scalars(
                    db.select(Customer)
                    .where(
                        db.and_(
                            Customer.store_id == store.id,
                            db.or_(
                                Customer.name.ilike(f"%{search_query}%"),
                                Customer.phone.ilike(f"%{search_query}%"),
                                Customer.email.ilike(f"%{search_query}%")
                            )
                        )
                    )
                )
                customers = list(customers)
                
                if not customers:
                    await update.message.reply_text(
                        format_info_message("לא נמצאו לקוחות התואמים לחיפוש."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                message = "🔍 *תוצאות החיפוש:*\n\n"
                
                for customer in customers:
                    # קבלת סטטיסטיקות הזמנות של הלקוח
                    total_orders = await session.scalar(
                        db.select(db.func.count(Order.id))
                        .where(Order.customer_id == customer.id)
                    )
                    
                    total_spent = await session.scalar(
                        db.select(db.func.sum(Order.total_amount))
                        .where(Order.customer_id == customer.id)
                    )
                    
                    message += (
                        f"👤 *{customer.name}*\n"
                        f"📞 טלפון: {customer.phone}\n"
                        f"📧 אימייל: {customer.email}\n"
                        f"📦 הזמנות: {format_number(total_orders)}\n"
                        f"💰 סה\"כ קניות: {format_price(total_spent or 0)}\n\n"
                    )
                
                keyboard = []
                for customer in customers:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"ערוך את {customer.name}",
                            callback_data=f"edit_customer_{customer.id}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton("חזור לתפריט", callback_data="back_to_menu")
                ])
                
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            await update.message.reply_text(
                format_error_message("אירעה שגיאה בחיפוש הלקוחות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_CUSTOMER_EDIT
    
    async def show_recent_customers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת לקוחות אחרונים"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
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
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.user_id == user.id)
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
                
                # קבלת 10 הלקוחות האחרונים
                recent_customers = await session.scalars(
                    db.select(Customer)
                    .where(Customer.store_id == store.id)
                    .order_by(Customer.created_at.desc())
                    .limit(10)
                )
                customers = list(recent_customers)
                
                if not customers:
                    await query.edit_message_text(
                        format_info_message("אין לקוחות במערכת."),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                message = "👥 *לקוחות אחרונים:*\n\n"
                
                for customer in customers:
                    # קבלת סטטיסטיקות הזמנות של הלקוח
                    total_orders = await session.scalar(
                        db.select(db.func.count(Order.id))
                        .where(Order.customer_id == customer.id)
                    )
                    
                    total_spent = await session.scalar(
                        db.select(db.func.sum(Order.total_amount))
                        .where(Order.customer_id == customer.id)
                    )
                    
                    message += (
                        f"👤 *{customer.name}*\n"
                        f"נוצר: {format_date(customer.created_at)}\n"
                        f"📦 הזמנות: {format_number(total_orders)}\n"
                        f"💰 סה\"כ קניות: {format_price(total_spent or 0)}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("הוסף לקוח", callback_data="add_customer"),
                        InlineKeyboardButton("חפש לקוח", callback_data="search_customer")
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
            logger.error(f"Error showing recent customers: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת הלקוחות האחרונים."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_CUSTOMER_ACTION
    
    async def show_vip_customers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """הצגת לקוחות VIP"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
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
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.user_id == user.id)
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
                
                # קבלת לקוחות VIP (לפי סכום קניות)
                vip_customers = await session.execute(
                    db.select(
                        Customer,
                        db.func.count(Order.id).label('total_orders'),
                        db.func.sum(Order.total_amount).label('total_spent')
                    )
                    .join(Order)
                    .where(Customer.store_id == store.id)
                    .group_by(Customer)
                    .order_by(db.text('total_spent DESC'))
                    .limit(10)
                )
                
                message = "👑 *לקוחות VIP:*\n\n"
                
                for customer, total_orders, total_spent in vip_customers:
                    message += (
                        f"👤 *{customer.name}*\n"
                        f"📞 טלפון: {customer.phone}\n"
                        f"📧 אימייל: {customer.email}\n"
                        f"📦 הזמנות: {format_number(total_orders)}\n"
                        f"💰 סה\"כ קניות: {format_price(total_spent)}\n\n"
                    )
                
                keyboard = [
                    [
                        InlineKeyboardButton("שלח הודעה ל-VIP", callback_data="message_vip"),
                        InlineKeyboardButton("הנחה ל-VIP", callback_data="discount_vip")
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
            logger.error(f"Error showing VIP customers: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בהצגת לקוחות ה-VIP."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return WAITING_FOR_CUSTOMER_ACTION
    
    async def export_customers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """ייצוא רשימת לקוחות"""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
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
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # קבלת החנות של המשתמש
                store = await session.scalar(
                    db.select(Store)
                    .where(Store.user_id == user.id)
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
                
                # ייצוא לקוחות לקובץ CSV
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # כותרות העמודות
                writer.writerow([
                    'שם',
                    'טלפון',
                    'אימייל',
                    'כתובת',
                    'תאריך הצטרפות',
                    'מספר הזמנות',
                    'סה"כ קניות',
                    'הערות'
                ])
                
                # קבלת כל הלקוחות עם סטטיסטיקות
                customers = await session.execute(
                    db.select(
                        Customer,
                        db.func.count(Order.id).label('total_orders'),
                        db.func.sum(Order.total_amount).label('total_spent')
                    )
                    .join(Order, isouter=True)
                    .where(Customer.store_id == store.id)
                    .group_by(Customer)
                )
                
                # כתיבת נתוני הלקוחות
                for customer, total_orders, total_spent in customers:
                    writer.writerow([
                        customer.name,
                        customer.phone,
                        customer.email,
                        customer.address,
                        customer.created_at.strftime('%Y-%m-%d'),
                        total_orders,
                        total_spent or 0,
                        customer.notes or ''
                    ])
                
                # שמירת הקובץ
                with open('customers.csv', 'w', encoding='utf-8') as f:
                    f.write(output.getvalue())
                
                # שליחת הקובץ
                await query.message.reply_document(
                    document=open('customers.csv', 'rb'),
                    filename=f'customers_{store.name}.csv',
                    caption="📋 רשימת לקוחות מלאה"
                )
                
                await query.edit_message_text(
                    format_success_message("רשימת הלקוחות יוצאה בהצלחה!"),
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error exporting customers: {e}")
            await query.edit_message_text(
                format_error_message("אירעה שגיאה בייצוא רשימת הלקוחות."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END 