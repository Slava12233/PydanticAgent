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
from src.models.database import User, WooCommerceProduct as Product
from src.services.database.users import UserManager
from src.utils.logger import setup_logger
from src.ui.telegram.utils.telegram_bot_utils import (
    format_price,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message
)

# Configure logging
logger = setup_logger('telegram_bot_products')

# מצבי שיחה
(
    WAITING_FOR_PRODUCT_NAME,
    WAITING_FOR_PRODUCT_DESCRIPTION,
    WAITING_FOR_PRODUCT_PRICE,
    WAITING_FOR_PRODUCT_SALE_PRICE,
    WAITING_FOR_PRODUCT_SKU,
    WAITING_FOR_PRODUCT_STOCK,
    WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS,
    WAITING_FOR_PRODUCT_CATEGORIES,
    WAITING_FOR_PRODUCT_IMAGES,
    WAITING_FOR_PRODUCT_CONFIRMATION,
    WAITING_FOR_PRODUCT_EDIT
) = range(11)

class TelegramBotProducts:
    """
    מחלקה לניהול מוצרים בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_create_product_handler(self) -> ConversationHandler:
        """
        יצירת handler ליצירת מוצר חדש
        
        Returns:
            ConversationHandler מוגדר ליצירת מוצר
        """
        return ConversationHandler(
            entry_points=[CommandHandler("create_product", self.create_product_start)],
            states={
                WAITING_FOR_PRODUCT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_name)
                ],
                WAITING_FOR_PRODUCT_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_description)
                ],
                WAITING_FOR_PRODUCT_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_price)
                ],
                WAITING_FOR_PRODUCT_SALE_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_sale_price)
                ],
                WAITING_FOR_PRODUCT_SKU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_sku)
                ],
                WAITING_FOR_PRODUCT_STOCK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_stock)
                ],
                WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_weight_dimensions)
                ],
                WAITING_FOR_PRODUCT_CATEGORIES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_categories)
                ],
                WAITING_FOR_PRODUCT_IMAGES: [
                    MessageHandler(filters.PHOTO | filters.Document.IMAGE, self.create_product_images),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.create_product_images)
                ],
                WAITING_FOR_PRODUCT_CONFIRMATION: [
                    CallbackQueryHandler(self.create_product_confirmation)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def create_product_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך יצירת מוצר"""
        user_id = update.effective_user.id
        logger.info(f"Create product command from user {user_id}")
        
        # איפוס נתוני המוצר בקונטקסט
        context.user_data['product'] = {}
        
        await update.message.reply_text(
            "🛍️ *יצירת מוצר חדש*\n\n"
            "אנא הזן את שם המוצר.\n\n"
            "לביטול התהליך, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRODUCT_NAME
    
    async def create_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם המוצר"""
        name = update.message.text
        context.user_data['product']['name'] = name
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא הזן תיאור מפורט למוצר.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRODUCT_DESCRIPTION
    
    async def create_product_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור המוצר"""
        description = update.message.text
        context.user_data['product']['description'] = description
        
        await update.message.reply_text(
            "יופי! עכשיו אנא הזן את מחיר המוצר (במספרים בלבד).",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRODUCT_PRICE
    
    async def create_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מחיר המוצר"""
        try:
            price = float(update.message.text)
            if price < 0:
                raise ValueError("המחיר חייב להיות חיובי")
            
            context.user_data['product']['price'] = price
            
            await update.message.reply_text(
                "האם יש מחיר מבצע למוצר?\n"
                "אם כן, הזן את מחיר המבצע (במספרים בלבד).\n"
                "אם לא, הקלד 0.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_PRODUCT_SALE_PRICE
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PRODUCT_PRICE
    
    async def create_product_sale_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מחיר מבצע למוצר"""
        try:
            sale_price = float(update.message.text)
            if sale_price < 0:
                raise ValueError("המחיר חייב להיות חיובי")
            
            if sale_price > context.user_data['product']['price']:
                await update.message.reply_text(
                    format_warning_message("מחיר המבצע גבוה מהמחיר הרגיל. אנא הזן מחיר נמוך יותר."),
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PRODUCT_SALE_PRICE
            
            context.user_data['product']['sale_price'] = sale_price if sale_price > 0 else None
            
            await update.message.reply_text(
                "אנא הזן את מק\"ט המוצר (SKU).",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_PRODUCT_SKU
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PRODUCT_SALE_PRICE
    
    async def create_product_sku(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מק\"ט המוצר"""
        sku = update.message.text
        context.user_data['product']['sku'] = sku
        
        await update.message.reply_text(
            "כמה יחידות יש במלאי? (הזן מספר)",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRODUCT_STOCK
    
    async def create_product_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כמות במלאי"""
        try:
            stock = int(update.message.text)
            if stock < 0:
                raise ValueError("הכמות חייבת להיות חיובית")
            
            context.user_data['product']['stock'] = stock
            
            await update.message.reply_text(
                "אנא הזן את משקל ומידות המוצר (לדוגמה: 500 גרם, 20x30x10 ס\"מ)",
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר שלם חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PRODUCT_STOCK
    
    async def create_product_weight_dimensions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת משקל ומידות המוצר"""
        weight_dimensions = update.message.text
        context.user_data['product']['weight_dimensions'] = weight_dimensions
        
        await update.message.reply_text(
            "אנא הזן את קטגוריות המוצר, מופרדות בפסיקים.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_PRODUCT_CATEGORIES
    
    async def create_product_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת קטגוריות המוצר"""
        categories = [cat.strip() for cat in update.message.text.split(',')]
        context.user_data['product']['categories'] = categories
        
        await update.message.reply_text(
            "אנא שלח תמונות של המוצר (עד 5 תמונות).\n"
            "כשתסיים, שלח 'סיום'.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.user_data['product']['images'] = []
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תמונות המוצר"""
        if update.message.text and update.message.text.lower() == 'סיום':
            if not context.user_data['product']['images']:
                await update.message.reply_text(
                    format_warning_message("לא נשלחו תמונות. האם אתה בטוח שברצונך להמשיך ללא תמונות?"),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("כן, המשך", callback_data="confirm_no_images"),
                            InlineKeyboardButton("לא, אוסיף תמונות", callback_data="add_images")
                        ]
                    ])
                )
                return WAITING_FOR_PRODUCT_CONFIRMATION
            
            # הצגת סיכום המוצר לאישור
            product = context.user_data['product']
            summary = (
                "🛍️ *סיכום פרטי המוצר:*\n\n"
                f"שם: {product['name']}\n"
                f"תיאור: {product['description']}\n"
                f"מחיר: {format_price(product['price'])}\n"
                f"מחיר מבצע: {format_price(product['sale_price']) if product['sale_price'] else 'אין'}\n"
                f"מק\"ט: {product['sku']}\n"
                f"מלאי: {product['stock']} יחידות\n"
                f"משקל ומידות: {product['weight_dimensions']}\n"
                f"קטגוריות: {', '.join(product['categories'])}\n"
                f"מספר תמונות: {len(product['images'])}\n\n"
                "האם לשמור את המוצר?"
            )
            
            await update.message.reply_text(
                summary,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("כן, שמור", callback_data="save_product"),
                        InlineKeyboardButton("לא, בטל", callback_data="cancel_product")
                    ]
                ])
            )
            
            return WAITING_FOR_PRODUCT_CONFIRMATION
        
        elif update.message.photo or (update.message.document and update.message.document.mime_type.startswith('image/')):
            if len(context.user_data['product']['images']) >= 5:
                await update.message.reply_text(
                    format_warning_message("הגעת למקסימום התמונות המותר (5). שלח 'סיום' להמשך."),
                    parse_mode=ParseMode.MARKDOWN
                )
                return WAITING_FOR_PRODUCT_IMAGES
            
            # שמירת התמונה
            file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
            context.user_data['product']['images'].append(file_id)
            
            await update.message.reply_text(
                format_success_message(f"התמונה נשמרה! ({len(context.user_data['product']['images'])}/5)\n"
                "שלח תמונה נוספת או 'סיום' לסיום."),
                parse_mode=ParseMode.MARKDOWN
            )
            
            return WAITING_FOR_PRODUCT_IMAGES
        
        else:
            await update.message.reply_text(
                format_error_message("אנא שלח תמונה או הקלד 'סיום'."),
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """אישור יצירת המוצר"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "save_product":
            try:
                product_data = context.user_data['product']
                
                async with db.get_session() as session:
                    # יצירת קטגוריות חדשות אם צריך
                    categories = []
                    for cat_name in product_data['categories']:
                        category = await session.scalar(
                            db.select(Category).where(Category.name == cat_name)
                        )
                        if not category:
                            category = Category(name=cat_name)
                            session.add(category)
                        categories.append(category)
                    
                    # יצירת המוצר
                    product = Product(
                        name=product_data['name'],
                        description=product_data['description'],
                        price=product_data['price'],
                        sale_price=product_data['sale_price'],
                        sku=product_data['sku'],
                        stock=product_data['stock'],
                        weight_dimensions=product_data['weight_dimensions'],
                        categories=categories,
                        images=product_data['images']
                    )
                    session.add(product)
                    await session.commit()
                
                await query.edit_message_text(
                    format_success_message("המוצר נשמר בהצלחה! 🎉"),
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except Exception as e:
                logger.error(f"Error saving product: {e}")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בשמירת המוצר: {str(e)}"),
                    parse_mode=ParseMode.MARKDOWN
                )
            
        elif query.data == "cancel_product":
            await query.edit_message_text(
                format_info_message("יצירת המוצר בוטלה."),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif query.data == "confirm_no_images":
            # המשך ללא תמונות
            product = context.user_data['product']
            summary = (
                "🛍️ *סיכום פרטי המוצר:*\n\n"
                f"שם: {product['name']}\n"
                f"תיאור: {product['description']}\n"
                f"מחיר: {format_price(product['price'])}\n"
                f"מחיר מבצע: {format_price(product['sale_price']) if product['sale_price'] else 'אין'}\n"
                f"מק\"ט: {product['sku']}\n"
                f"מלאי: {product['stock']} יחידות\n"
                f"משקל ומידות: {product['weight_dimensions']}\n"
                f"קטגוריות: {', '.join(product['categories'])}\n"
                "ללא תמונות\n\n"
                "האם לשמור את המוצר?"
            )
            
            await query.edit_message_text(
                summary,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("כן, שמור", callback_data="save_product"),
                        InlineKeyboardButton("לא, בטל", callback_data="cancel_product")
                    ]
                ])
            )
            
        elif query.data == "add_images":
            await query.edit_message_text(
                "אנא שלח תמונות של המוצר (עד 5 תמונות).\n"
                "כשתסיים, שלח 'סיום'.",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PRODUCT_IMAGES
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        return ConversationHandler.END
    
    async def handle_product_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """טיפול בקריאות callback הקשורות למוצרים"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('edit_product_'):
            product_id = int(query.data.split('_')[2])
            # טיפול בעריכת מוצר
            pass
        elif query.data.startswith('delete_product_'):
            product_id = int(query.data.split('_')[2])
            # טיפול במחיקת מוצר
            pass 