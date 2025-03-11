"""
מודול לטיפול בפקודות ניהול חנות ווקומרס
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import random

from src.database.models import User, UserRole, WooCommerceStore
from src.database.operations import get_user_by_telegram_id
from sqlalchemy import select

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
    # בדיקה אמיתית מול מסד הנתונים
    result = await session.execute(
        select(WooCommerceStore).where(
            WooCommerceStore.user_id == user_id,
            WooCommerceStore.is_active == True
        )
    )
    
    store = result.scalars().first()
    return store is not None

async def get_store_basic_data(user_id: int, session: AsyncSession) -> Dict[str, Any]:
    """
    קבלת נתונים בסיסיים מהחנות
    """
    # ניסיון לקבל נתונים אמיתיים מה-API של ווקומרס
    try:
        # קבלת פרטי החנות מהמסד נתונים
        result = await session.execute(
            select(WooCommerceStore).where(
                WooCommerceStore.user_id == user_id,
                WooCommerceStore.is_active == True
            )
        )
        
        store = result.scalars().first()
        if not store:
            return {"error": "לא נמצאה חנות מחוברת"}
        
        # כאן יש לבצע קריאה אמיתית ל-API של ווקומרס
        # לצורך הדוגמה, נחזיר נתונים פיקטיביים
        return {
            "name": store.store_name or "החנות שלי",
            "url": store.store_url,
            "products_count": random.randint(10, 100),
            "orders_count": random.randint(5, 50),
            "customers_count": random.randint(20, 200)
        }
        
    except Exception as e:
        logger.error(f"שגיאה בקבלת נתוני חנות: {str(e)}")
        return {"error": f"שגיאה בקבלת נתוני חנות: {str(e)}"}

# פקודות ניהול חנות

async def start_store_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    התחלת תהליך חיבור חנות ווקומרס
    """
    user = update.effective_user
    
    # בדיקה אם המשתמש כבר חיבר חנות
    async with AsyncSession() as session:
        db_user = await get_user_by_telegram_id(user.id, session)
        
        if not db_user:
            await update.message.reply_text(
                "אינך רשום במערכת. אנא הירשם תחילה באמצעות הפקודה /start"
            )
            return ConversationHandler.END
        
        if await is_store_connected(db_user.id, session):
            keyboard = [
                [InlineKeyboardButton("כן, חבר חנות חדשה", callback_data="reconnect_store")],
                [InlineKeyboardButton("לא, השאר את החנות הנוכחית", callback_data="keep_store")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "כבר יש לך חנות מחוברת. האם ברצונך להחליף אותה?",
                reply_markup=reply_markup
            )
            return WAITING_FOR_CONFIRMATION
    
    # שמירת נתוני המשתמש בקונטקסט
    context.user_data["user_id"] = db_user.id
    
    await update.message.reply_text(
        "ברוך הבא לתהליך חיבור חנות ווקומרס!\n\n"
        "אנא שלח את כתובת האתר של החנות שלך (לדוגמה: https://mystore.com)"
    )
    
    return WAITING_FOR_STORE_URL

async def store_url_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת כתובת החנות מהמשתמש
    """
    store_url = update.message.text.strip()
    
    # בדיקת תקינות הכתובת
    if not store_url.startswith(("http://", "https://")):
        store_url = "https://" + store_url
    
    # שמירת הכתובת בקונטקסט
    context.user_data["store_url"] = store_url
    
    await update.message.reply_text(
        f"מצוין! כתובת החנות שהזנת היא: {store_url}\n\n"
        "עכשיו, אנא שלח את מפתח הצרכן (Consumer Key) של ה-API של ווקומרס.\n"
        "ניתן למצוא אותו בלוח הבקרה של ווקומרס תחת WooCommerce > Settings > Advanced > REST API"
    )
    
    return WAITING_FOR_CONSUMER_KEY

async def consumer_key_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת מפתח הצרכן מהמשתמש
    """
    consumer_key = update.message.text.strip()
    
    # שמירת המפתח בקונטקסט
    context.user_data["consumer_key"] = consumer_key
    
    await update.message.reply_text(
        "מצוין! עכשיו, אנא שלח את הסוד הצרכני (Consumer Secret) של ה-API של ווקומרס.\n"
        "ניתן למצוא אותו באותו מקום בלוח הבקרה של ווקומרס"
    )
    
    return WAITING_FOR_CONSUMER_SECRET

async def consumer_secret_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    קבלת הסוד הצרכני מהמשתמש וסיום תהליך החיבור
    """
    consumer_secret = update.message.text.strip()
    
    # שמירת הסוד בקונטקסט
    context.user_data["consumer_secret"] = consumer_secret
    
    # שמירת פרטי החנות במסד הנתונים
    store_url = context.user_data.get("store_url")
    consumer_key = context.user_data.get("consumer_key")
    user_id = context.user_data.get("user_id")
    
    try:
        async with AsyncSession() as session:
            # בדיקה אם כבר יש חנות פעילה למשתמש
            result = await session.execute(
                select(WooCommerceStore).where(
                    WooCommerceStore.user_id == user_id,
                    WooCommerceStore.is_active == True
                )
            )
            
            existing_store = result.scalars().first()
            
            if existing_store:
                # עדכון החנות הקיימת
                existing_store.store_url = store_url
                existing_store.consumer_key = consumer_key
                existing_store.consumer_secret = consumer_secret
            else:
                # יצירת חנות חדשה
                new_store = WooCommerceStore(
                    user_id=user_id,
                    store_url=store_url,
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                    is_active=True
                )
                session.add(new_store)
            
            await session.commit()
            
            await update.message.reply_text(
                f"מצוין! החנות שלך חוברה בהצלחה!\n\n"
                f"כתובת החנות: {store_url}\n\n"
                "עכשיו תוכל להשתמש בפקודות ניהול החנות כמו:\n"
                "/store_info - הצגת מידע על החנות\n"
                "/products - ניהול מוצרים\n"
                "/orders - ניהול הזמנות"
            )
            
            # ניקוי נתוני המשתמש מהקונטקסט
            context.user_data.clear()
            
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"שגיאה בשמירת פרטי חנות: {str(e)}")
        
        await update.message.reply_text(
            f"אירעה שגיאה בחיבור החנות: {str(e)}\n"
            "אנא נסה שוב מאוחר יותר או פנה לתמיכה"
        )
        
        return ConversationHandler.END

async def cancel_store_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    ביטול תהליך חיבור החנות
    """
    await update.message.reply_text(
        "תהליך חיבור החנות בוטל. תוכל להתחיל שוב בכל עת באמצעות הפקודה /connect_store"
    )
    
    # ניקוי נתוני המשתמש מהקונטקסט
    context.user_data.clear()
    
    return ConversationHandler.END

async def handle_store_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    טיפול בתשובת המשתמש לגבי החלפת חנות קיימת
    """
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    
    if choice == "reconnect_store":
        # המשתמש בחר להחליף את החנות הקיימת
        async with AsyncSession() as session:
            db_user = await get_user_by_telegram_id(update.effective_user.id, session)
            context.user_data["user_id"] = db_user.id
        
        await query.edit_message_text(
            "אנא שלח את כתובת האתר של החנות החדשה שלך (לדוגמה: https://mystore.com)"
        )
        
        return WAITING_FOR_STORE_URL
    else:
        # המשתמש בחר להשאיר את החנות הקיימת
        await query.edit_message_text(
            "החנות הנוכחית נשארה מחוברת. תוכל להשתמש בפקודות ניהול החנות כרגיל."
        )
        
        return ConversationHandler.END

async def get_store_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    הצגת מידע על החנות המחוברת
    """
    user = update.effective_user
    
    async with AsyncSession() as session:
        db_user = await get_user_by_telegram_id(user.id, session)
        
        if not db_user:
            await update.message.reply_text(
                "אינך רשום במערכת. אנא הירשם תחילה באמצעות הפקודה /start"
            )
            return
        
        if not await is_store_connected(db_user.id, session):
            await update.message.reply_text(
                "אין לך חנות מחוברת. אנא חבר חנות תחילה באמצעות הפקודה /connect_store"
            )
            return
        
        # קבלת נתוני החנות
        store_data = await get_store_basic_data(db_user.id, session)
        
        if "error" in store_data:
            await update.message.reply_text(
                f"אירעה שגיאה בקבלת נתוני החנות: {store_data['error']}"
            )
            return
        
        # הצגת נתוני החנות
        await update.message.reply_text(
            f"📊 *מידע על החנות שלך* 📊\n\n"
            f"*שם החנות:* {store_data['name']}\n"
            f"*כתובת:* {store_data['url']}\n\n"
            f"*סטטיסטיקה:*\n"
            f"- מוצרים: {store_data['products_count']}\n"
            f"- הזמנות: {store_data['orders_count']}\n"
            f"- לקוחות: {store_data['customers_count']}\n\n"
            f"השתמש בפקודות הבאות לניהול החנות:\n"
            f"/products - ניהול מוצרים\n"
            f"/orders - ניהול הזמנות\n"
            f"/customers - ניהול לקוחות",
            parse_mode="Markdown"
        )

async def disconnect_store(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    ניתוק החנות המחוברת
    """
    user = update.effective_user
    
    async with AsyncSession() as session:
        db_user = await get_user_by_telegram_id(user.id, session)
        
        if not db_user:
            await update.message.reply_text(
                "אינך רשום במערכת. אנא הירשם תחילה באמצעות הפקודה /start"
            )
            return
        
        if not await is_store_connected(db_user.id, session):
            await update.message.reply_text(
                "אין לך חנות מחוברת."
            )
            return
        
        # מציאת החנות הפעילה
        result = await session.execute(
            select(WooCommerceStore).where(
                WooCommerceStore.user_id == db_user.id,
                WooCommerceStore.is_active == True
            )
        )
        
        store = result.scalars().first()
        
        if store:
            # סימון החנות כלא פעילה
            store.is_active = False
            await session.commit()
            
            await update.message.reply_text(
                "החנות נותקה בהצלחה. תוכל לחבר חנות חדשה באמצעות הפקודה /connect_store"
            )
        else:
            await update.message.reply_text(
                "לא נמצאה חנות פעילה לניתוק."
            )

# פונקציות עזר נוספות

def get_store_connection_handler() -> ConversationHandler:
    """
    יצירת ה-ConversationHandler לתהליך חיבור החנות
    """
    return ConversationHandler(
        entry_points=[],  # יש להוסיף את נקודות הכניסה המתאימות
        states={
            WAITING_FOR_STORE_URL: [],  # יש להוסיף את ההנדלרים המתאימים
            WAITING_FOR_CONSUMER_KEY: [],
            WAITING_FOR_CONSUMER_SECRET: [],
            WAITING_FOR_CONFIRMATION: []
        },
        fallbacks=[]  # יש להוסיף את ההנדלרים המתאימים
    ) 