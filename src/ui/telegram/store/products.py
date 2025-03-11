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
from telegram.error import TelegramError
from sqlalchemy import select, and_

from src.database.database import db
from src.models.database import User, WooCommerceProduct as Product, WooCommerceCategory, WooCommerceStore, WooCommerceProductCategory
from src.services.database.users import UserManager
from src.services.store.woocommerce.services.product_service import ProductService
from src.services.store.woocommerce.api.woocommerce_api import WooCommerceAPI
from src.utils.logger import setup_logger
from src.ui.telegram.utils.utils import (
    format_price,
    format_date,
    format_number,
    format_success_message,
    format_error_message,
    format_warning_message,
    format_info_message,
    escape_markdown_v2
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
    WAITING_FOR_PRODUCT_EDIT,
    WAITING_FOR_PRODUCT_SELECTION
) = range(12)

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
        
        # בדיקה אם המשתמש קיים במערכת
        async with db.get_session() as session:
            user = await UserManager.get_user_by_telegram_id(user_id, session)
            
            if not user:
                await update.message.reply_text(
                    format_error_message("לא נמצא משתמש במערכת. אנא פנה למנהל המערכת."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return ConversationHandler.END
            
            # בדיקה אם יש למשתמש חנות מקושרת
            store = await session.scalar(
                db.select(WooCommerceStore).where(WooCommerceStore.user_id == user.id)
            )
            
            if not store:
                await update.message.reply_text(
                    format_error_message("לא נמצאה חנות מקושרת למשתמש. אנא חבר חנות תחילה באמצעות הפקודה /connect_store"),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return ConversationHandler.END
        
        # איפוס נתוני המוצר בקונטקסט
        context.user_data['product'] = {}
        
        await update.message.reply_text(
            "🛍️ *יצירת מוצר חדש*\n\n"
            "אנא הזן את שם המוצר.\n\n"
            "לביטול התהליך, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_PRODUCT_NAME
    
    async def create_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת שם המוצר"""
        name = update.message.text
        context.user_data['product']['name'] = name
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא הזן תיאור מפורט למוצר.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_PRODUCT_DESCRIPTION
    
    async def create_product_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת תיאור המוצר"""
        description = update.message.text
        context.user_data['product']['description'] = description
        
        await update.message.reply_text(
            "יופי! עכשיו אנא הזן את מחיר המוצר (במספרים בלבד).",
            parse_mode=ParseMode.MARKDOWN_V2
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
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            return WAITING_FOR_PRODUCT_SALE_PRICE
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN_V2
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
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return WAITING_FOR_PRODUCT_SALE_PRICE
            
            context.user_data['product']['sale_price'] = sale_price if sale_price > 0 else None
            
            await update.message.reply_text(
                "אנא הזן את מק\"ט המוצר (SKU).",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            return WAITING_FOR_PRODUCT_SKU
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_PRODUCT_SALE_PRICE
    
    async def create_product_sku(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת מק\"ט המוצר"""
        sku = update.message.text
        context.user_data['product']['sku'] = sku
        
        await update.message.reply_text(
            "כמה יחידות יש במלאי? (הזן מספר)",
            parse_mode=ParseMode.MARKDOWN_V2
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
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            return WAITING_FOR_PRODUCT_WEIGHT_DIMENSIONS
            
        except ValueError:
            await update.message.reply_text(
                format_error_message("אנא הזן מספר שלם חיובי בלבד."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_PRODUCT_STOCK
    
    async def create_product_weight_dimensions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת משקל ומידות המוצר"""
        weight_dimensions = update.message.text
        context.user_data['product']['weight_dimensions'] = weight_dimensions
        
        await update.message.reply_text(
            "אנא הזן את קטגוריות המוצר, מופרדות בפסיקים.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_PRODUCT_CATEGORIES
    
    async def create_product_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת קטגוריות המוצר"""
        categories = [cat.strip() for cat in update.message.text.split(',')]
        context.user_data['product']['categories'] = categories
        
        await update.message.reply_text(
            "אנא שלח תמונות של המוצר (עד 5 תמונות).\n"
            "כשתסיים, שלח 'סיום'.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        context.user_data['product']['images'] = []
        return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        קבלת תמונות המוצר
        
        Args:
            update: אובייקט העדכון
            context: אובייקט הקונטקסט
            
        Returns:
            שלב השיחה הבא
        """
        if not context.user_data.get('product', {}).get('images'):
            context.user_data['product']['images'] = []
        
        if update.message.text and update.message.text.strip() == "סיום":
            # הצגת סיכום המוצר לאישור
            product = context.user_data['product']
            
            # עיבוד הנתונים לפני הצגה כדי למנוע שגיאות Markdown
            product_name = escape_markdown_v2(product['name'])
            product_description = escape_markdown_v2(product['description'])
            product_sku = escape_markdown_v2(product['sku'])
            product_weight_dimensions = escape_markdown_v2(product['weight_dimensions'])
            product_categories = escape_markdown_v2(', '.join(product['categories']))
            
            summary = escape_markdown_v2(
                f"🛍️ *סיכום פרטי המוצר:*\n\n"
                f"שם: {product_name}\n"
                f"תיאור: {product_description}\n"
                f"מחיר: {format_price(product['price'])}\n"
                f"מחיר מבצע: {format_price(product['sale_price']) if product['sale_price'] else 'אין'}\n"
                f"מק\"ט: {product_sku}\n"
                f"מלאי: {product['stock']} יחידות\n"
                f"משקל ומידות: {product_weight_dimensions}\n"
                f"קטגוריות: {product_categories}\n"
                f"מספר תמונות: {len(product['images'])}\n\n"
                f"האם לשמור את המוצר?"
            )
            
            await update.message.reply_text(
                summary,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("כן, שמור", callback_data="save_product"),
                        InlineKeyboardButton("לא, בטל", callback_data="cancel_product")
                    ]
                ])
            )
            
            return WAITING_FOR_PRODUCT_CONFIRMATION
        
        elif update.message.photo or (update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/')):
            if len(context.user_data['product']['images']) >= 5:
                await update.message.reply_text(
                    format_warning_message("הגעת למקסימום התמונות המותר (5). שלח 'סיום' להמשך."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return WAITING_FOR_PRODUCT_IMAGES
            
            # שמירת התמונה
            try:
                file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
                
                # בדיקה שה-file_id תקין
                file = await context.bot.get_file(file_id)
                if not file or not file.file_path:
                    await update.message.reply_text(
                        format_error_message("לא ניתן לקבל את התמונה. אנא נסה שוב או שלח תמונה אחרת."),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return WAITING_FOR_PRODUCT_IMAGES
                
                context.user_data['product']['images'].append(file_id)
                
                await update.message.reply_text(
                    format_success_message(f"התמונה נשמרה! ({len(context.user_data['product']['images'])}/5)\n"
                    "שלח תמונה נוספת או 'סיום' לסיום."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                return WAITING_FOR_PRODUCT_IMAGES
            except Exception as e:
                logger.error(f"שגיאה בשמירת תמונה: {e}")
                await update.message.reply_text(
                    format_error_message(f"אירעה שגיאה בשמירת התמונה: {escape_markdown_v2(str(e))}"),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                return WAITING_FOR_PRODUCT_IMAGES
        
        else:
            await update.message.reply_text(
                format_info_message("אנא שלח תמונה או הקלד 'סיום' לסיום הוספת תמונות."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_PRODUCT_IMAGES
    
    async def create_product_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """אישור יצירת המוצר"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "save_product":
            try:
                product_data = context.user_data['product']
                user_id = update.effective_user.id
                
                # הודעת עדכון למשתמש שהתהליך התחיל
                try:
                    await query.edit_message_text(
                        format_info_message("מתחיל בתהליך יצירת המוצר... אנא המתן."),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                except TelegramError as e:
                    logger.error(f"שגיאה בעדכון הודעה: {e}")
                    # ניסיון לשלוח הודעה חדשה במקום לערוך
                    await query.message.reply_text(
                        format_info_message("מתחיל בתהליך יצירת המוצר... אנא המתן."),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                
                async with db.get_session() as session:
                    # קבלת המשתמש לפי מזהה הטלגרם
                    user = await session.scalar(
                        db.select(User).where(User.telegram_id == user_id)
                    )
                    
                    if not user:
                        await query.message.reply_text(
                            format_error_message("לא נמצא משתמש במערכת. אנא פנה למנהל המערכת."),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                        return ConversationHandler.END
                    
                    # קבלת החנות של המשתמש
                    store = await session.scalar(
                        db.select(WooCommerceStore).where(WooCommerceStore.user_id == user.id)
                    )
                    
                    if not store:
                        await query.message.reply_text(
                            format_error_message("לא נמצאה חנות מקושרת למשתמש. אנא הגדר חנות תחילה."),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                        return ConversationHandler.END
                    
                    # יצירת מוצר חדש במסד הנתונים
                    product = Product(
                        user_id=user.id,
                        store_id=store.id,
                        name=product_data['name'],
                        description=product_data['description'],
                        price=product_data['price'],
                        sale_price=product_data['sale_price'] if product_data['sale_price'] else None,
                        sku=product_data['sku'],
                        stock=product_data['stock'],
                        weight_dimensions=product_data['weight_dimensions'],
                        status='draft'
                    )
                    
                    session.add(product)
                    await session.commit()
                    await session.refresh(product)
                    
                    # הוספת קטגוריות למוצר
                    categories = []
                    for category_name in product_data['categories']:
                        # בדיקה אם הקטגוריה קיימת
                        category = await session.scalar(
                            db.select(WooCommerceCategory).where(
                                and_(
                                    WooCommerceCategory.name == category_name,
                                    WooCommerceCategory.store_id == store.id
                                )
                            )
                        )
                        
                        if category:
                            categories.append(category)
                            # קישור הקטגוריה למוצר
                            product_category = WooCommerceProductCategory(
                                product_id=product.id,
                                category_id=category.id
                            )
                            session.add(product_category)
                    
                    await session.commit()
                
                # הכנת נתוני המוצר עבור WooCommerce
                product_service = ProductService(store.url, store.consumer_key, store.consumer_secret)
                
                # הכנת תמונות (אם יש)
                image_urls = []
                image_errors = []
                for file_id in product_data.get('images', []):
                    try:
                        file = await context.bot.get_file(file_id)
                        if file and file.file_path:
                            image_urls.append(file.file_path)
                        else:
                            logger.warning(f"קובץ תמונה לא תקין: {file_id}")
                            image_errors.append(f"קובץ תמונה לא תקין: {file_id}")
                    except Exception as e:
                        error_msg = f"שגיאה בקבלת קובץ תמונה: {str(e)}"
                        logger.error(error_msg)
                        image_errors.append(error_msg)
                
                try:
                    # הכנת נתוני המוצר לשליחה ל-WooCommerce
                    woo_product_data = {
                        'name': product_data['name'],
                        'description': product_data['description'],
                        'regular_price': str(product_data['price']),
                        'sale_price': str(product_data['sale_price']) if product_data['sale_price'] else '',
                        'sku': product_data['sku'],
                        'manage_stock': True,
                        'stock_quantity': product_data['stock'],
                        'weight': product_data['weight_dimensions'].split(',')[0].strip() if ',' in product_data['weight_dimensions'] else product_data['weight_dimensions'],
                        'status': 'draft'
                    }
                    
                    # הוספת קטגוריות
                    woo_product_data['categories'] = []
                    for category in categories:
                        if category.woo_id > 0:  # רק קטגוריות שכבר קיימות ב-WooCommerce
                            woo_product_data['categories'].append({
                                'id': category.woo_id
                            })
                    
                    # עדכון הודעה למשתמש
                    try:
                        await query.edit_message_text(
                            format_info_message("יוצר את המוצר בחנות... אנא המתן."),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    except TelegramError as e:
                        logger.error(f"שגיאה בעדכון הודעה: {e}")
                        # ניסיון לשלוח הודעה חדשה במקום לערוך
                        await query.message.reply_text(
                            format_info_message("יוצר את המוצר בחנות... אנא המתן."),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    
                    # יצירת המוצר ב-WooCommerce (ללא תמונות תחילה)
                    response = await product_service.create_product(woo_product_data)
                    
                    if response.success:
                        woo_product_id = response.data.get('id', 0)
                        
                        # עדכון ה-woo_id במסד הנתונים המקומי
                        async with db.get_session() as session:
                            product = await session.get(Product, product.id)
                            if product:
                                product.woo_id = woo_product_id
                                product.status = response.data.get('status', 'draft')
                                await session.commit()
                        
                        # הוספת תמונות למוצר (אם יש)
                        image_success_count = 0
                        image_error_messages = []
                        
                        if image_urls:
                            try:
                                await query.edit_message_text(
                                    format_info_message(f"המוצר נוצר בהצלחה! מוסיף תמונות... אנא המתן."),
                                    parse_mode=ParseMode.MARKDOWN_V2
                                )
                            except TelegramError as e:
                                logger.error(f"שגיאה בעדכון הודעה: {e}")
                                await query.message.reply_text(
                                    format_info_message(f"המוצר נוצר בהצלחה! מוסיף תמונות... אנא המתן."),
                                    parse_mode=ParseMode.MARKDOWN_V2
                                )
                            
                            # עדכון תמונת המוצר
                            for i, image_url in enumerate(image_urls):
                                try:
                                    image_response = await product_service.update_product_image(woo_product_id, image_url)
                                    if image_response.success:
                                        image_success_count += 1
                                    else:
                                        error_msg = f"שגיאה בהוספת תמונה {i+1}: {image_response.error if hasattr(image_response, 'error') else 'שגיאה לא ידועה'}"
                                        logger.error(error_msg)
                                        image_error_messages.append(error_msg)
                                except Exception as img_e:
                                    error_msg = f"שגיאה בהוספת תמונה {i+1}: {str(img_e)}"
                                    logger.error(error_msg)
                                    image_error_messages.append(error_msg)
                        
                        # הכנת הודעת סיכום
                        success_message = f"המוצר נשמר בהצלחה ונוצר בחנות! 🎉\nמזהה בחנות: {woo_product_id}"
                        
                        # הוספת מידע על תמונות
                        if image_urls:
                            success_message += f"\n\nתמונות שהועלו בהצלחה: {image_success_count}/{len(image_urls)}"
                            if image_error_messages:
                                error_summary = escape_markdown_v2("\n".join(image_error_messages[:3]))
                                if len(image_error_messages) > 3:
                                    error_summary += f"\n\\.\\.\\. ועוד {len(image_error_messages) - 3} שגיאות נוספות"
                                success_message += f"\n\nשגיאות תמונה:\n{error_summary}"
                        
                        try:
                            await query.edit_message_text(
                                format_success_message(success_message),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                        except TelegramError as e:
                            logger.error(f"שגיאה בעדכון הודעה: {e}")
                            await query.message.reply_text(
                                format_success_message(success_message),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                    else:
                        try:
                            await query.edit_message_text(
                                format_warning_message(f"המוצר נשמר במסד הנתונים אך לא נוצר בחנות.\nשגיאה: {response.error if hasattr(response, 'error') else 'שגיאה לא ידועה'}"),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                        except TelegramError as e:
                            logger.error(f"שגיאה בעדכון הודעה: {e}")
                            await query.message.reply_text(
                                format_warning_message(f"המוצר נשמר במסד הנתונים אך לא נוצר בחנות.\nשגיאה: {response.error if hasattr(response, 'error') else 'שגיאה לא ידועה'}"),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                except Exception as e:
                    logger.error(f"Error syncing product to WooCommerce: {e}")
                    try:
                        await query.edit_message_text(
                            format_warning_message(f"המוצר נשמר במסד הנתונים אך לא נוצר בחנות.\nשגיאה: {str(e)}"),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    except TelegramError as te:
                        logger.error(f"שגיאה בעדכון הודעה: {te}")
                        await query.message.reply_text(
                            format_warning_message(f"המוצר נשמר במסד הנתונים אך לא נוצר בחנות.\nשגיאה: {str(e)}"),
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
            except Exception as e:
                error_message = escape_markdown_v2(f"אירעה שגיאה בשמירת המוצר: {str(e)}")
                logger.error(f"Error saving product: {e}")
                try:
                    await query.edit_message_text(
                        format_error_message(error_message),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                except TelegramError as te:
                    logger.error(f"שגיאה בעדכון הודעה: {te}")
                    await query.message.reply_text(
                        format_error_message(error_message),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
            
            # ניקוי נתוני הקונטקסט
            context.user_data.clear()
            return ConversationHandler.END
            
        elif query.data == "cancel_product":
            await query.edit_message_text(
                format_info_message("יצירת המוצר בוטלה."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            # ניקוי נתוני הקונטקסט
            context.user_data.clear()
            return ConversationHandler.END
        
        elif query.data == "confirm_no_images":
            # המשך ללא תמונות
            product = context.user_data['product']
            
            # עיבוד הנתונים לפני הצגה כדי למנוע שגיאות Markdown
            product_name = escape_markdown_v2(product['name'])
            product_description = escape_markdown_v2(product['description'])
            product_sku = escape_markdown_v2(product['sku'])
            product_weight_dimensions = escape_markdown_v2(product['weight_dimensions'])
            product_categories = escape_markdown_v2(', '.join(product['categories']))
            
            summary = escape_markdown_v2(
                f"🛍️ *סיכום פרטי המוצר:*\n\n"
                f"שם: {product_name}\n"
                f"תיאור: {product_description}\n"
                f"מחיר: {format_price(product['price'])}\n"
                f"מחיר מבצע: {format_price(product['sale_price']) if product['sale_price'] else 'אין'}\n"
                f"מק\"ט: {product_sku}\n"
                f"מלאי: {product['stock']} יחידות\n"
                f"משקל ומידות: {product_weight_dimensions}\n"
                f"קטגוריות: {product_categories}\n"
                f"ללא תמונות\n\n"
                f"האם לשמור את המוצר?"
            )
            
            await query.edit_message_text(
                summary,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("כן, שמור", callback_data="save_product"),
                        InlineKeyboardButton("לא, בטל", callback_data="cancel_product")
                    ]
                ])
            )
            return WAITING_FOR_PRODUCT_CONFIRMATION
            
        elif query.data == "add_images":
            await query.edit_message_text(
                "אנא שלח תמונות של המוצר (עד 5 תמונות).\n"
                "כשתסיים, שלח 'סיום'.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_PRODUCT_IMAGES
    
    async def handle_product_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        טיפול בלחיצות על כפתורים בתפריט המוצרים
        
        Args:
            update: אובייקט העדכון
            context: אובייקט הקונטקסט
            
        Returns:
            שלב השיחה הבא
        """
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_product":
            await query.edit_message_text(
                format_info_message("בוא נתחיל ביצירת מוצר חדש. מה שם המוצר?"),
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return WAITING_FOR_PRODUCT_NAME
        
        elif query.data == "list_products":
            # קבלת רשימת המוצרים
            try:
                # שליחת הודעת טעינה
                await query.edit_message_text(
                    format_info_message("מקבל רשימת מוצרים מהחנות... אנא המתן."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                product_service = self.get_product_service()
                response = await product_service.get_products()
                
                if response.success and response.data:
                    products = response.data
                    
                    # יצירת רשימת מוצרים עם כפתורים
                    keyboard = []
                    for i in range(0, len(products), 2):
                        row = []
                        for j in range(2):
                            if i + j < len(products):
                                product = products[i + j]
                                product_name = escape_markdown_v2(product['name'])[:20] + "..." if len(product['name']) > 20 else escape_markdown_v2(product['name'])
                                row.append(InlineKeyboardButton(f"{product['id']} - {product_name}", callback_data=f"view_product_{product['id']}"))
                        if row:
                            keyboard.append(row)
                    keyboard.append([InlineKeyboardButton("חזרה", callback_data="back_to_products_menu")])
                    
                    await query.edit_message_text(
                        format_success_message(f"מצאתי {len(products)} מוצרים בחנות. בחר מוצר לצפייה:"),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return WAITING_FOR_PRODUCT_SELECTION
                else:
                    error_message = "לא נמצאו מוצרים בחנות" if not response.data else f"שגיאה בקבלת מוצרים: {response.error}"
                    await query.edit_message_text(
                        format_error_message(error_message),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("חזרה", callback_data="back_to_products_menu")
                        ]])
                    )
                    return WAITING_FOR_PRODUCT_SELECTION
            except Exception as e:
                logger.error(f"שגיאה בקבלת רשימת מוצרים: {e}")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בקבלת רשימת המוצרים: {escape_markdown_v2(str(e))}"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("חזרה", callback_data="back_to_products_menu")
                    ]])
                )
                return WAITING_FOR_PRODUCT_SELECTION
        
        elif query.data.startswith("view_product_"):
            product_id = query.data.split("_")[-1]
            
            try:
                # שליחת הודעת טעינה
                await query.edit_message_text(
                    format_info_message(f"מקבל מידע על מוצר {product_id}... אנא המתן."),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                product_service = self.get_product_service()
                response = await product_service.get_product(product_id)
                
                if response.success and response.data:
                    product = response.data
                    
                    # עיבוד הנתונים לפני הצגה כדי למנוע שגיאות Markdown
                    product_name = escape_markdown_v2(product['name'])
                    product_description = escape_markdown_v2(product['description'])
                    product_sku = escape_markdown_v2(product.get('sku', 'לא צוין'))
                    
                    # הכנת מידע על קטגוריות
                    categories = []
                    for category in product.get('categories', []):
                        categories.append(category.get('name', ''))
                    categories_text = escape_markdown_v2(', '.join(categories)) if categories else "אין"
                    
                    # פרטי המוצר
                    product_info = escape_markdown_v2(
                        f"*פרטי המוצר:*\n\n"
                        f"*שם:* {product_name}\n"
                        f"*מזהה:* {product['id']}\n"
                        f"*מק\"ט:* {product_sku}\n"
                        f"*מחיר:* {format_price(product['price'])}\n"
                        f"*מחיר מבצע:* {format_price(product['sale_price']) if product.get('sale_price') else 'אין'}\n"
                        f"*מלאי:* {product.get('stock_quantity', 0)} יחידות\n"
                        f"*קטגוריות:* {categories_text}\n\n"
                        f"*תיאור:*\n{product_description}\n\n"
                    )
                    
                    # כפתורי פעולות
                    keyboard = [
                        [InlineKeyboardButton("עריכה", callback_data=f"edit_product_{product_id}")],
                        [InlineKeyboardButton("מחיקה", callback_data=f"delete_product_{product_id}")],
                        [InlineKeyboardButton("חזרה לרשימה", callback_data="list_products")]
                    ]
                    
                    await query.edit_message_text(
                        format_success_message(product_info),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                    # שליחת תמונות המוצר (אם יש)
                    if product.get('images'):
                        images_text = format_info_message(f"תמונות המוצר ({len(product['images'])}):")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=images_text,
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                        
                        for image in product['images'][:5]:  # הגבלה ל-5 תמונות
                            try:
                                await context.bot.send_photo(
                                    chat_id=update.effective_chat.id,
                                    photo=image['src']
                                )
                            except Exception as img_e:
                                logger.error(f"שגיאה בשליחת תמונת מוצר: {img_e}")
                                await context.bot.send_message(
                                    chat_id=update.effective_chat.id,
                                    text=format_error_message(f"לא ניתן להציג תמונה: {escape_markdown_v2(str(img_e))}"),
                                    parse_mode=ParseMode.MARKDOWN_V2
                                )
                    
                    return WAITING_FOR_PRODUCT_SELECTION
                else:
                    error_message = escape_markdown_v2(
                        f"לא נמצא מוצר עם מזהה {product_id}" if not response.data else 
                        f"שגיאה בקבלת מוצר: {response.error if hasattr(response, 'error') else 'שגיאה לא ידועה'}"
                    )
                    await query.edit_message_text(
                        format_error_message(error_message),
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("חזרה לרשימה", callback_data="list_products")
                        ]])
                    )
                    return WAITING_FOR_PRODUCT_SELECTION
            except Exception as e:
                logger.error(f"שגיאה בקבלת מידע על מוצר: {e}")
                await query.edit_message_text(
                    format_error_message(f"אירעה שגיאה בקבלת מידע על המוצר: {escape_markdown_v2(str(e))}"),
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("חזרה לרשימה", callback_data="list_products")
                    ]])
                )
                return WAITING_FOR_PRODUCT_SELECTION
    
    async def show_products_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        הצגת תפריט ניהול מוצרים
        
        Args:
            update: אובייקט העדכון
            context: אובייקט הקונטקסט
            
        Returns:
            שלב השיחה הבא
        """
        keyboard = [
            [InlineKeyboardButton("יצירת מוצר חדש", callback_data="add_product")],
            [InlineKeyboardButton("צפייה במוצרים", callback_data="list_products")],
            [InlineKeyboardButton("חזרה לתפריט הראשי", callback_data="back_to_main_menu")]
        ]
        
        await update.message.reply_text(
            format_info_message("*תפריט ניהול מוצרים*\n\nבחר את הפעולה הרצויה:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        return WAITING_FOR_PRODUCT_SELECTION