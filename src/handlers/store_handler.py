"""
מודול לטיפול בפקודות ניהול חנות ווקומרס
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import random

from src.database.models import User, UserRole
from src.database.operations import get_user_by_telegram_id

logger = logging.getLogger(__name__)

# מצבי שיחה לתהליך חיבור החנות
WAITING_FOR_STORE_URL = 1
WAITING_FOR_CONSUMER_KEY = 2
WAITING_FOR_CONSUMER_SECRET = 3
WAITING_FOR_CONFIRMATION = 4

# פונקציות עזר

async def is_store_connected(user_id: int, session: AsyncSession) -> bool:
    """
    בדיקה האם המשתמש כבר חיבר חנות
    """
    # בשלב זה נחזיר True כברירת מחדל לצורך בדיקה
    # TODO: לממש בדיקה אמיתית מול מסד הנתונים
    return True

async def get_store_basic_data(user_id: int, session: AsyncSession) -> Dict[str, Any]:
    """
    קבלת נתונים בסיסיים מהחנות
    """
    # בשלב זה נחזיר נתונים לדוגמה - בהמשך נממש שליפה אמיתית מה-API של ווקומרס
    # TODO: לממש שליפת נתונים אמיתית מה-API של ווקומרס
    return {
        "name": "החנות המדהימה שלי",
        "orders_today": 12,
        "sales_today": 3750,
        "low_stock": 5,
        "pending_orders": 8,
        "total_products": 156,
        "total_customers": 87,
        "monthly_revenue": 42500,
        "popular_products": [
            {"name": "חולצת כותנה", "sales": 24, "revenue": 2400},
            {"name": "מכנסי ג'ינס", "sales": 18, "revenue": 3600},
            {"name": "נעלי ספורט", "sales": 15, "revenue": 4500}
        ]
    }

# פונקציות טיפול בפקודות

async def handle_store_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /store - דאשבורד ניהול חנות ווקומרס
    """
    user_id = update.effective_user.id
    
    # בדיקה אם המשתמש כבר חיבר חנות
    store_connected = await is_store_connected(user_id, session)
    
    if not store_connected:
        # אם אין חיבור לחנות, מציגים אפשרות לחיבור
        keyboard = [
            [InlineKeyboardButton("🔗 חבר את החנות שלך", callback_data="connect_store")],
            [InlineKeyboardButton("ℹ️ מידע על השירות", callback_data="store_info")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏪 *ברוך הבא לסוכן ניהול חנות ווקומרס*\n\n"
            "נראה שעדיין לא חיברת את החנות שלך.\n"
            "כדי להתחיל, עליך לחבר את חנות הווקומרס שלך לסוכן.\n\n"
            "בחר אפשרות:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # אם יש חיבור לחנות, מציגים את הדאשבורד המלא
    keyboard = [
        [InlineKeyboardButton("📊 סטטיסטיקות מכירות", callback_data="store_stats")],
        [InlineKeyboardButton("📦 ניהול מוצרים", callback_data="store_products")],
        [InlineKeyboardButton("🛒 הזמנות אחרונות", callback_data="store_orders")],
        [InlineKeyboardButton("💰 דוחות כספיים", callback_data="store_finance")],
        [InlineKeyboardButton("👥 ניהול לקוחות", callback_data="store_customers")],
        [InlineKeyboardButton("🔔 התראות חנות", callback_data="store_alerts")],
        [InlineKeyboardButton("⚙️ הגדרות חיבור", callback_data="store_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # קבלת נתונים בסיסיים מהחנות
    store_data = await get_store_basic_data(user_id, session)
    
    # בניית רשימת מוצרים פופולריים
    popular_products_text = ""
    if "popular_products" in store_data:
        for i, product in enumerate(store_data["popular_products"], 1):
            popular_products_text += f"  {i}. {product['name']} - {product['sales']} יחידות ({product['revenue']}₪)\n"
    
    await update.message.reply_text(
        f"🏪 *דאשבורד החנות שלך: {store_data['name']}*\n\n"
        f"📈 *סיכום מהיר:*\n"
        f"• הזמנות היום: {store_data['orders_today']}\n"
        f"• מכירות היום: {store_data['sales_today']}₪\n"
        f"• מוצרים במלאי נמוך: {store_data['low_stock']}\n"
        f"• הזמנות ממתינות: {store_data['pending_orders']}\n"
        f"• סה\"כ מוצרים: {store_data.get('total_products', 'לא זמין')}\n"
        f"• סה\"כ לקוחות: {store_data.get('total_customers', 'לא זמין')}\n"
        f"• הכנסות חודשיות: {store_data.get('monthly_revenue', 'לא זמין')}₪\n\n"
        f"🔝 *מוצרים מובילים:*\n{popular_products_text}\n"
        f"בחר אפשרות לניהול החנות:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_connect_store_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    התחלת תהליך חיבור חנות ווקומרס
    """
    await update.message.reply_text(
        "🔗 *חיבור חנות ווקומרס*\n\n"
        "כדי לחבר את החנות שלך, אנחנו צריכים את כתובת האתר שלך ומפתחות API.\n\n"
        "שלב 1: הזן את כתובת האתר שלך (לדוגמה: https://mystore.com)",
        parse_mode="Markdown"
    )
    return WAITING_FOR_STORE_URL

async def handle_store_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת כתובת אתר החנות
    """
    store_url = update.message.text.strip()
    
    # בדיקה בסיסית של תקינות ה-URL
    if not store_url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ כתובת לא תקינה. אנא הזן כתובת מלאה הכוללת http:// או https://"
        )
        return WAITING_FOR_STORE_URL
    
    # שמירת ה-URL בהקשר המשתמש
    context.user_data['store_url'] = store_url
    
    # הנחיות ליצירת מפתחות API בווקומרס
    await update.message.reply_text(
        f"✅ כתובת האתר נשמרה: {store_url}\n\n"
        "שלב 2: יצירת מפתחות API\n\n"
        "1. היכנס לממשק הניהול של ווקומרס\n"
        "2. לך להגדרות -> מתקדם -> REST API\n"
        "3. צור מפתח חדש עם הרשאות קריאה/כתיבה\n"
        "4. העתק את ה-Consumer Key ושלח אותו כאן"
    )
    return WAITING_FOR_CONSUMER_KEY

async def handle_consumer_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת מפתח צרכן (Consumer Key)
    """
    consumer_key = update.message.text.strip()
    
    # בדיקה בסיסית של תקינות המפתח
    if len(consumer_key) < 10:
        await update.message.reply_text(
            "❌ מפתח לא תקין. מפתח צרכן אמור להיות ארוך יותר. אנא בדוק ונסה שוב."
        )
        return WAITING_FOR_CONSUMER_KEY
    
    # שמירת המפתח בהקשר המשתמש
    context.user_data['consumer_key'] = consumer_key
    
    await update.message.reply_text(
        "✅ מפתח הצרכן נשמר!\n\n"
        "שלב 3: העתק את ה-Consumer Secret ושלח אותו כאן"
    )
    return WAITING_FOR_CONSUMER_SECRET

async def handle_consumer_secret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת סוד צרכן (Consumer Secret)
    """
    consumer_secret = update.message.text.strip()
    
    # בדיקה בסיסית של תקינות הסוד
    if len(consumer_secret) < 10:
        await update.message.reply_text(
            "❌ סוד לא תקין. סוד צרכן אמור להיות ארוך יותר. אנא בדוק ונסה שוב."
        )
        return WAITING_FOR_CONSUMER_SECRET
    
    # שמירת הסוד בהקשר המשתמש
    context.user_data['consumer_secret'] = consumer_secret
    
    # הצגת סיכום הפרטים לאישור
    store_url = context.user_data.get('store_url', '')
    consumer_key = context.user_data.get('consumer_key', '')
    masked_key = consumer_key[:4] + '*' * (len(consumer_key) - 8) + consumer_key[-4:] if len(consumer_key) > 8 else '****'
    masked_secret = '*' * len(consumer_secret)
    
    await update.message.reply_text(
        "📋 *סיכום פרטי החיבור:*\n\n"
        f"כתובת החנות: {store_url}\n"
        f"מפתח צרכן: {masked_key}\n"
        f"סוד צרכן: {masked_secret}\n\n"
        "האם הפרטים נכונים? הקלד 'כן' לאישור או 'לא' לביטול.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_CONFIRMATION

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> int:
    """
    קבלת אישור לחיבור החנות
    """
    confirmation = update.message.text.strip().lower()
    
    if confirmation in ['כן', 'yes', 'y', 'אישור', 'confirm']:
        # שמירת פרטי החיבור במסד הנתונים
        # TODO: לממש שמירה אמיתית במסד הנתונים
        
        store_url = context.user_data.get('store_url', '')
        consumer_key = context.user_data.get('consumer_key', '')
        consumer_secret = context.user_data.get('consumer_secret', '')
        
        # שמירת החנות במסד הנתונים
        user_id = update.effective_user.id
        try:
            from src.database.operations import create_store
            await create_store(
                user_id=user_id,
                store_url=store_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                session=session
            )
            logger.info(f"חנות חדשה נוצרה למשתמש {user_id}")
        except Exception as e:
            logger.error(f"שגיאה ביצירת חנות: {str(e)}")
        
        # ניקוי נתוני המשתמש
        context.user_data.pop('store_url', None)
        context.user_data.pop('consumer_key', None)
        context.user_data.pop('consumer_secret', None)
        
        # הודעת הצלחה
        await update.message.reply_text(
            "✅ *החנות חוברה בהצלחה!*\n\n"
            f"החנות שלך ב-{store_url} חוברה בהצלחה לסוכן.\n"
            "כעת תוכל לנהל את החנות שלך ישירות מהצ'אט.\n\n"
            "הקלד /store כדי לפתוח את דאשבורד החנות.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    elif confirmation in ['לא', 'no', 'n', 'ביטול', 'cancel']:
        # ניקוי נתוני המשתמש
        context.user_data.pop('store_url', None)
        context.user_data.pop('consumer_key', None)
        context.user_data.pop('consumer_secret', None)
        
        # הודעת ביטול
        await update.message.reply_text(
            "❌ *תהליך החיבור בוטל*\n\n"
            "תהליך חיבור החנות בוטל לבקשתך.\n"
            "תוכל להתחיל מחדש בכל עת על ידי הקלדת /connect_store.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    else:
        # הודעת שגיאה
        await update.message.reply_text(
            "❓ לא הבנתי את תשובתך.\n"
            "אנא הקלד 'כן' לאישור או 'לא' לביטול."
        )
        return WAITING_FOR_CONFIRMATION

async def handle_store_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בבקשת סטטיסטיקות מכירות
    """
    query = update.callback_query
    await query.answer()
    
    # בשלב זה נציג נתונים לדוגמה - בהמשך נממש שליפה אמיתית מה-API של ווקומרס
    # TODO: לממש שליפת נתונים אמיתית מה-API של ווקומרס
    
    user_id = update.effective_user.id
    store_data = await get_store_basic_data(user_id, session)
    
    # בניית רשימת מוצרים פופולריים
    popular_products_text = ""
    if "popular_products" in store_data:
        for i, product in enumerate(store_data["popular_products"], 1):
            popular_products_text += f"{i}. {product['name']} - {product['sales']} יחידות ({product['revenue']}₪)\n"
    
    stats_text = (
        "📊 *סטטיסטיקות מכירות מפורטות*\n\n"
        "*היום:*\n"
        f"• הזמנות: {store_data['orders_today']}\n"
        f"• מכירות: {store_data['sales_today']}₪\n"
        f"• ממוצע להזמנה: {int(store_data['sales_today'] / max(store_data['orders_today'], 1))}₪\n\n"
        
        "*השבוע:*\n"
        f"• הזמנות: {store_data['orders_today'] * 5}\n"
        f"• מכירות: {store_data['sales_today'] * 5}₪\n"
        f"• ממוצע להזמנה: {int(store_data['sales_today'] / max(store_data['orders_today'], 1))}₪\n\n"
        
        "*החודש:*\n"
        f"• הזמנות: {store_data['orders_today'] * 20}\n"
        f"• מכירות: {store_data.get('monthly_revenue', store_data['sales_today'] * 20)}₪\n"
        f"• ממוצע להזמנה: {int((store_data.get('monthly_revenue', store_data['sales_today'] * 20)) / max(store_data['orders_today'] * 20, 1))}₪\n\n"
        
        "*השוואה לחודש קודם:*\n"
        f"• שינוי במכירות: +{random.randint(5, 25)}%\n"
        f"• שינוי בהזמנות: +{random.randint(3, 20)}%\n"
        f"• שינוי בממוצע להזמנה: +{random.randint(1, 10)}%\n\n"
        
        "*מוצרים מובילים:*\n"
        f"{popular_products_text}\n"
        
        "*קטגוריות מובילות:*\n"
        "1. ביגוד - 45% מהמכירות\n"
        "2. הנעלה - 30% מהמכירות\n"
        "3. אקססוריז - 15% מהמכירות\n"
        "4. אחר - 10% מהמכירות"
    )
    
    # כפתור חזרה לדאשבורד הראשי
    keyboard = [
        [InlineKeyboardButton("📈 הצג גרף מכירות", callback_data="sales_graph")],
        [InlineKeyboardButton("📊 דוח מפורט", callback_data="detailed_report")],
        [InlineKeyboardButton("🔙 חזרה לדאשבורד", callback_data="back_to_store")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_store_orders(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בבקשת הזמנות אחרונות
    """
    query = update.callback_query
    await query.answer()
    
    # בשלב זה נציג נתונים לדוגמה - בהמשך נממש שליפה אמיתית מה-API של ווקומרס
    # TODO: לממש שליפת נתונים אמיתית מה-API של ווקומרס
    
    # הזמנות אחרונות
    recent_orders = [
        {"id": "1001", "time": "לפני שעה", "status": "ממתין לתשלום", "customer": "ישראל ישראלי", "amount": 350, "items": 2, "phone": "050-1234567"},
        {"id": "1000", "time": "לפני 3 שעות", "status": "בטיפול", "customer": "שרה כהן", "amount": 520, "items": 3, "phone": "052-7654321"},
        {"id": "999", "time": "לפני 5 שעות", "status": "נשלח", "customer": "דוד לוי", "amount": 180, "items": 1, "phone": "054-9876543"},
        {"id": "998", "time": "אתמול", "status": "הושלם", "customer": "רחל אברהם", "amount": 750, "items": 4, "phone": "053-1122334"},
        {"id": "997", "time": "אתמול", "status": "בוטל", "customer": "יעקב כהן", "amount": 420, "items": 2, "phone": "058-5566778"}
    ]
    
    # סיכום סטטוס הזמנות
    order_status_summary = {
        "ממתין לתשלום": 3,
        "בטיפול": 5,
        "נשלח": 8,
        "הושלם": 12,
        "בוטל": 2
    }
    
    # בניית טקסט סיכום סטטוס הזמנות
    status_summary_text = ""
    for status, count in order_status_summary.items():
        status_summary_text += f"• {status}: {count}\n"
    
    orders_text = (
        "🛒 *הזמנות אחרונות*\n\n"
        
        "*סיכום סטטוס הזמנות:*\n"
        f"{status_summary_text}\n"
        
        "*הזמנות אחרונות:*\n"
    )
    
    # הוספת הזמנות אחרונות
    for order in recent_orders:
        status_emoji = "⏳"
        if order["status"] == "בטיפול":
            status_emoji = "🔄"
        elif order["status"] == "נשלח":
            status_emoji = "📦"
        elif order["status"] == "הושלם":
            status_emoji = "✅"
        elif order["status"] == "בוטל":
            status_emoji = "❌"
        
        orders_text += (
            f"*הזמנה #{order['id']}* ({order['time']})\n"
            f"• סטטוס: {status_emoji} {order['status']}\n"
            f"• לקוח: {order['customer']}\n"
            f"• טלפון: {order['phone']}\n"
            f"• סכום: {order['amount']}₪\n"
            f"• פריטים: {order['items']}\n\n"
        )
    
    # כפתורים לניהול הזמנות וחזרה לדאשבורד
    keyboard = [
        [InlineKeyboardButton("🔍 פרטי הזמנה", callback_data="order_details")],
        [InlineKeyboardButton("📦 עדכון סטטוס", callback_data="update_order_status")],
        [InlineKeyboardButton("📱 שליחת SMS ללקוח", callback_data="send_sms_to_customer")],
        [InlineKeyboardButton("🖨️ הדפסת חשבונית", callback_data="print_invoice")],
        [InlineKeyboardButton("🔙 חזרה לדאשבורד", callback_data="back_to_store")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        orders_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_store_products(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בבקשת ניהול מוצרים
    """
    query = update.callback_query
    await query.answer()
    
    # בשלב זה נציג נתונים לדוגמה - בהמשך נממש שליפה אמיתית מה-API של ווקומרס
    # TODO: לממש שליפת נתונים אמיתית מה-API של ווקומרס
    
    user_id = update.effective_user.id
    store_data = await get_store_basic_data(user_id, session)
    
    # בניית רשימת מוצרים פופולריים
    popular_products_text = ""
    if "popular_products" in store_data:
        for i, product in enumerate(store_data["popular_products"], 1):
            popular_products_text += f"{i}. {product['name']} - מלאי: {random.randint(15, 50)} יח'\n"
    
    # מוצרים במלאי נמוך
    low_stock_products = [
        {"name": "חולצת פולו", "stock": 2, "price": 120},
        {"name": "כובע קיץ", "stock": 3, "price": 80},
        {"name": "גרביים", "stock": 5, "price": 30},
        {"name": "חגורת עור", "stock": 4, "price": 150},
        {"name": "צעיף חורף", "stock": 1, "price": 100}
    ]
    
    # מוצרים שאזל המלאי
    out_of_stock_products = [
        {"name": "תיק גב", "price": 250},
        {"name": "צמיד עור", "price": 120},
        {"name": "משקפי שמש", "price": 180},
        {"name": "כפפות חורף", "price": 90}
    ]
    
    products_text = (
        "📦 *ניהול מוצרים*\n\n"
        
        "*סיכום מלאי:*\n"
        f"• סה\"כ מוצרים: {store_data.get('total_products', 150)}\n"
        f"• מוצרים במלאי: {store_data.get('total_products', 150) - len(low_stock_products) - len(out_of_stock_products)}\n"
        f"• מוצרים במלאי נמוך: {len(low_stock_products)}\n"
        f"• מוצרים שאזל המלאי: {len(out_of_stock_products)}\n\n"
        
        "*מוצרים פופולריים:*\n"
        f"{popular_products_text}\n"
        
        "*מוצרים במלאי נמוך:*\n"
    )
    
    # הוספת מוצרים במלאי נמוך
    for i, product in enumerate(low_stock_products, 1):
        products_text += f"{i}. ⚠️ {product['name']} - מלאי: {product['stock']} יח' (מחיר: {product['price']}₪)\n"
    
    products_text += "\n*מוצרים אזל המלאי:*\n"
    
    # הוספת מוצרים שאזל המלאי
    for i, product in enumerate(out_of_stock_products, 1):
        products_text += f"{i}. ❌ {product['name']} - מלאי: 0 יח' (מחיר: {product['price']}₪)\n"
    
    # כפתורים לניהול מוצרים וחזרה לדאשבורד
    keyboard = [
        [InlineKeyboardButton("🔍 חיפוש מוצר", callback_data="search_product")],
        [InlineKeyboardButton("📝 עדכון מלאי", callback_data="update_inventory")],
        [InlineKeyboardButton("➕ הוספת מוצר", callback_data="add_product")],
        [InlineKeyboardButton("🏷️ ניהול מבצעים", callback_data="manage_sales")],
        [InlineKeyboardButton("🔄 סנכרון מלאי", callback_data="sync_inventory")],
        [InlineKeyboardButton("🔙 חזרה לדאשבורד", callback_data="back_to_store")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        products_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_store_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בלחיצות על כפתורים בדאשבורד החנות
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # ניתוב לפונקציות המתאימות לפי סוג הכפתור
    if callback_data == "connect_store":
        await query.edit_message_text(
            "🔗 *חיבור חנות ווקומרס*\n\n"
            "כדי להתחיל את תהליך החיבור, אנא הקלד את הפקודה:\n"
            "/connect_store",
            parse_mode="Markdown"
        )
    elif callback_data == "store_info":
        await query.edit_message_text(
            "ℹ️ *מידע על שירות ניהול חנות ווקומרס*\n\n"
            "הסוכן שלנו מאפשר לך לנהל את חנות הווקומרס שלך ישירות מטלגרם!\n\n"
            "*יתרונות:*\n"
            "• ניהול הזמנות בקלות\n"
            "• מעקב אחר מכירות ומלאי\n"
            "• התראות בזמן אמת\n"
            "• עדכון מהיר של סטטוס הזמנות\n"
            "• ניהול מוצרים ומלאי\n\n"
            "להתחלת תהליך החיבור, הקלד /connect_store",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 חזרה", callback_data="back_to_store")]
            ])
        )
    elif callback_data == "store_stats":
        await handle_store_stats(update, context, session)
    elif callback_data == "store_orders":
        await handle_store_orders(update, context, session)
    elif callback_data == "store_products":
        await handle_store_products(update, context, session)
    elif callback_data == "back_to_store":
        # חזרה לדאשבורד הראשי
        await handle_store_dashboard(update, context, session)
    else:
        # פונקציונליות בפיתוח
        await query.edit_message_text(
            f"🔧 הפונקציה '{callback_data}' נמצאת בפיתוח ותהיה זמינה בקרוב.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 חזרה לדאשבורד", callback_data="back_to_store")]
            ])
        ) 