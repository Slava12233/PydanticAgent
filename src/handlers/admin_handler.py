"""
מודול לטיפול בפקודות מנהל
"""
import logging
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.models import User, UserRole, Document, Message
from src.database.operations import get_user_by_telegram_id, update_user, get_all_users, get_all_documents, get_user_by_id, update_user_role
from src.core.config import ADMIN_USER_ID

logger = logging.getLogger(__name__)

async def is_admin(telegram_id: int, session: AsyncSession) -> bool:
    """
    בדיקה האם המשתמש הוא מנהל
    """
    # בדיקה לפי מזהה טלגרם של מנהל ראשי
    if telegram_id == ADMIN_USER_ID:
        return True
    
    # בדיקה לפי תפקיד בבסיס הנתונים
    user = await get_user_by_telegram_id(telegram_id, session)
    if user and user.role == UserRole.ADMIN:
        return True
    
    return False

async def admin_required(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> bool:
    """
    דקורטור וירטואלי לבדיקת הרשאות מנהל
    מחזיר True אם המשתמש הוא מנהל, אחרת False ושולח הודעת שגיאה
    """
    if not update.effective_user:
        await update.effective_message.reply_text("שגיאה: לא ניתן לזהות את המשתמש")
        return False
    
    telegram_id = update.effective_user.id
    
    if not await is_admin(telegram_id, session):
        await update.effective_message.reply_text("⛔ אין לך הרשאות מנהל לביצוע פעולה זו")
        return False
    
    return True

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin - תפריט ניהול ראשי
    """
    if not await admin_required(update, context, session):
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 ניהול משתמשים", callback_data="admin_users")],
        [InlineKeyboardButton("📊 סטטיסטיקות מערכת", callback_data="admin_stats")],
        [InlineKeyboardButton("📄 ניהול מסמכים", callback_data="admin_docs")],
        [InlineKeyboardButton("🤖 ניהול מודלים", callback_data="admin_models")],
        [InlineKeyboardButton("⚙️ הגדרות מערכת", callback_data="admin_config")],
        [InlineKeyboardButton("📢 שליחת התראות", callback_data="admin_notify")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "🔐 *לוח בקרה למנהל*\n\n"
        "ברוך הבא למערכת הניהול. בחר אפשרות:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_users - ניהול משתמשים
    """
    if not await admin_required(update, context, session):
        return
    
    users = await get_all_users(session)
    
    # יצירת מקלדת עם כפתורים לפעולות ניהול משתמשים
    keyboard = [
        [InlineKeyboardButton("🔍 הצג רשימת משתמשים", callback_data="list_users")],
        [InlineKeyboardButton("🚫 חסום משתמש", callback_data="block_user")],
        [InlineKeyboardButton("✅ בטל חסימת משתמש", callback_data="unblock_user")],
        [InlineKeyboardButton("👑 הענק הרשאות מנהל", callback_data="grant_admin")],
        [InlineKeyboardButton("👤 הסר הרשאות מנהל", callback_data="revoke_admin")],
        [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_count = len(users)
    admin_count = sum(1 for user in users if user.role == UserRole.ADMIN)
    blocked_count = sum(1 for user in users if user.role == UserRole.BLOCKED)
    
    await update.effective_message.reply_text(
        f"👥 *ניהול משתמשים*\n\n"
        f"סה\"כ משתמשים: {user_count}\n"
        f"מנהלים: {admin_count}\n"
        f"משתמשים חסומים: {blocked_count}\n\n"
        f"בחר פעולה:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_stats - סטטיסטיקות מערכת
    """
    if not await admin_required(update, context, session):
        return
    
    # איסוף נתונים סטטיסטיים
    users = await get_all_users(session)
    documents = await get_all_documents(session)
    
    user_count = len(users)
    doc_count = len(documents)
    
    # TODO: להוסיף שאילתות נוספות לסטטיסטיקות מתקדמות
    
    await update.effective_message.reply_text(
        f"📊 *סטטיסטיקות מערכת*\n\n"
        f"👥 *משתמשים*\n"
        f"סה\"כ משתמשים: {user_count}\n"
        f"מנהלים: {sum(1 for user in users if user.role == UserRole.ADMIN)}\n"
        f"משתמשים רגילים: {sum(1 for user in users if user.role == UserRole.USER)}\n"
        f"משתמשים חסומים: {sum(1 for user in users if user.role == UserRole.BLOCKED)}\n\n"
        f"📄 *מסמכים*\n"
        f"סה\"כ מסמכים: {doc_count}\n\n"
        f"💬 *הודעות*\n"
        f"סה\"כ הודעות: [בפיתוח]\n"
        f"הודעות היום: [בפיתוח]\n\n"
        f"⚙️ *מערכת*\n"
        f"זמן פעילות: [בפיתוח]\n"
        f"גרסה: 1.0.0\n",
        parse_mode="Markdown"
    )

async def handle_admin_docs(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_docs - ניהול מסמכים
    """
    if not await admin_required(update, context, session):
        return
    
    keyboard = [
        [InlineKeyboardButton("📋 הצג כל המסמכים", callback_data="list_all_docs")],
        [InlineKeyboardButton("🗑️ מחק מסמך", callback_data="delete_doc")],
        [InlineKeyboardButton("🔄 רענן מסמכים", callback_data="refresh_docs")],
        [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "📄 *ניהול מסמכים*\n\n"
        "בחר פעולה:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_models(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_models - ניהול מודלים
    """
    if not await admin_required(update, context, session):
        return
    
    keyboard = [
        [InlineKeyboardButton("🔄 שנה מודל ברירת מחדל", callback_data="change_default_model")],
        [InlineKeyboardButton("⚙️ הגדר הגבלות שימוש", callback_data="set_usage_limits")],
        [InlineKeyboardButton("📊 סטטיסטיקות שימוש במודלים", callback_data="model_usage_stats")],
        [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "🤖 *ניהול מודלים*\n\n"
        "בחר פעולה:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_config(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_config - הגדרות מערכת
    """
    if not await admin_required(update, context, session):
        return
    
    keyboard = [
        [InlineKeyboardButton("🔄 שנה הגדרות מערכת", callback_data="change_system_settings")],
        [InlineKeyboardButton("💾 גיבוי מערכת", callback_data="backup_system")],
        [InlineKeyboardButton("📤 ייצוא נתונים", callback_data="export_data")],
        [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "⚙️ *הגדרות מערכת*\n\n"
        "בחר פעולה:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בפקודת /admin_notify - שליחת התראות
    """
    if not await admin_required(update, context, session):
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 שלח הודעה לכל המשתמשים", callback_data="notify_all")],
        [InlineKeyboardButton("👤 שלח הודעה למשתמש ספציפי", callback_data="notify_user")],
        [InlineKeyboardButton("🔙 חזרה לתפריט הראשי", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "📢 *שליחת התראות*\n\n"
        "בחר פעולה:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    טיפול בלחיצות על כפתורים במערכת הניהול
    """
    query = update.callback_query
    await query.answer()
    
    if not await admin_required(update, context, session):
        return
    
    callback_data = query.data
    
    # ניתוב לפונקציות המתאימות לפי סוג הכפתור
    if callback_data == "admin":
        await handle_admin_command(update, context, session)
    elif callback_data == "admin_users":
        await handle_admin_users(update, context, session)
    elif callback_data == "admin_stats":
        await handle_admin_stats(update, context, session)
    elif callback_data == "admin_docs":
        await handle_admin_docs(update, context, session)
    elif callback_data == "admin_models":
        await handle_admin_models(update, context, session)
    elif callback_data == "admin_config":
        await handle_admin_config(update, context, session)
    elif callback_data == "admin_notify":
        await handle_admin_notify(update, context, session)
    elif callback_data == "list_users":
        await handle_list_users(update, context, session)
    elif callback_data == "grant_admin":
        await handle_grant_admin(update, context, session)
    elif callback_data == "revoke_admin":
        await handle_revoke_admin(update, context, session)
    elif callback_data == "block_user":
        await handle_block_user(update, context, session)
    elif callback_data == "unblock_user":
        await handle_unblock_user(update, context, session)
    # TODO: להוסיף טיפול בכפתורים נוספים
    else:
        await query.edit_message_text(
            f"פעולה '{callback_data}' בפיתוח...",
            parse_mode="Markdown"
        )

async def handle_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    הצגת רשימת המשתמשים במערכת
    """
    if not await admin_required(update, context, session):
        return
    
    users = await get_all_users(session)
    
    if not users:
        await update.callback_query.edit_message_text(
            "אין משתמשים במערכת",
            parse_mode="Markdown"
        )
        return
    
    # יצירת טקסט עם רשימת המשתמשים
    user_list = "👥 *רשימת משתמשים*\n\n"
    
    for i, user in enumerate(users, 1):
        role_emoji = "👑" if user.role == UserRole.ADMIN else "🚫" if user.role == UserRole.BLOCKED else "👤"
        username = f"@{user.username}" if user.username else "ללא שם משתמש"
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "ללא שם"
        
        user_list += f"{i}. {role_emoji} *{name}* ({username})\n"
        user_list += f"   מזהה: `{user.id}`\n"
        user_list += f"   תפקיד: {user.role.value}\n"
        user_list += f"   הצטרף: {user.created_at.strftime('%d/%m/%Y')}\n\n"
    
    # הוספת כפתור חזרה
    keyboard = [[InlineKeyboardButton("🔙 חזרה", callback_data="admin_users")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        user_list,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_grant_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    הענקת הרשאות מנהל למשתמש
    """
    if not await admin_required(update, context, session):
        return
    
    # שמירת המצב בקונטקסט
    context.user_data["admin_action"] = "grant_admin"
    
    await update.callback_query.edit_message_text(
        "👑 *הענקת הרשאות מנהל*\n\n"
        "אנא שלח את מזהה המשתמש (ID) שברצונך להעניק לו הרשאות מנהל.\n"
        "ניתן למצוא את המזהה ברשימת המשתמשים.",
        parse_mode="Markdown"
    )

async def handle_revoke_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    הסרת הרשאות מנהל ממשתמש
    """
    if not await admin_required(update, context, session):
        return
    
    # שמירת המצב בקונטקסט
    context.user_data["admin_action"] = "revoke_admin"
    
    await update.callback_query.edit_message_text(
        "👤 *הסרת הרשאות מנהל*\n\n"
        "אנא שלח את מזהה המשתמש (ID) שברצונך להסיר ממנו הרשאות מנהל.\n"
        "ניתן למצוא את המזהה ברשימת המשתמשים.",
        parse_mode="Markdown"
    )

async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    חסימת משתמש
    """
    if not await admin_required(update, context, session):
        return
    
    # שמירת המצב בקונטקסט
    context.user_data["admin_action"] = "block_user"
    
    await update.callback_query.edit_message_text(
        "🚫 *חסימת משתמש*\n\n"
        "אנא שלח את מזהה המשתמש (ID) שברצונך לחסום.\n"
        "ניתן למצוא את המזהה ברשימת המשתמשים.",
        parse_mode="Markdown"
    )

async def handle_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> None:
    """
    ביטול חסימת משתמש
    """
    if not await admin_required(update, context, session):
        return
    
    # שמירת המצב בקונטקסט
    context.user_data["admin_action"] = "unblock_user"
    
    await update.callback_query.edit_message_text(
        "✅ *ביטול חסימת משתמש*\n\n"
        "אנא שלח את מזהה המשתמש (ID) שברצונך לבטל את חסימתו.\n"
        "ניתן למצוא את המזהה ברשימת המשתמשים.",
        parse_mode="Markdown"
    )

async def process_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncSession) -> bool:
    """
    עיבוד פעולות מנהל שדורשות קלט נוסף
    מחזיר True אם הפעולה טופלה, אחרת False
    """
    if not context.user_data.get("admin_action"):
        return False
    
    action = context.user_data["admin_action"]
    user_id_text = update.message.text.strip()
    
    try:
        user_id = int(user_id_text)
    except ValueError:
        await update.message.reply_text("❌ מזהה לא תקין. אנא שלח מספר בלבד.")
        return True
    
    user = await get_user_by_id(user_id, session)
    if not user:
        await update.message.reply_text("❌ משתמש לא נמצא. אנא בדוק את המזהה ונסה שוב.")
        return True
    
    if action == "grant_admin":
        if user.role == UserRole.ADMIN:
            await update.message.reply_text("⚠️ למשתמש זה כבר יש הרשאות מנהל.")
        else:
            await update_user_role(user_id, UserRole.ADMIN, session)
            await update.message.reply_text(f"✅ הרשאות מנהל הוענקו בהצלחה למשתמש {user.first_name or user.username or user_id}.")
    
    elif action == "revoke_admin":
        if user.role != UserRole.ADMIN:
            await update.message.reply_text("⚠️ למשתמש זה אין הרשאות מנהל.")
        else:
            await update_user_role(user_id, UserRole.USER, session)
            await update.message.reply_text(f"✅ הרשאות מנהל הוסרו בהצלחה ממשתמש {user.first_name or user.username or user_id}.")
    
    elif action == "block_user":
        if user.role == UserRole.BLOCKED:
            await update.message.reply_text("⚠️ משתמש זה כבר חסום.")
        else:
            await update_user_role(user_id, UserRole.BLOCKED, session)
            await update.message.reply_text(f"✅ משתמש {user.first_name or user.username or user_id} נחסם בהצלחה.")
    
    elif action == "unblock_user":
        if user.role != UserRole.BLOCKED:
            await update.message.reply_text("⚠️ משתמש זה אינו חסום.")
        else:
            await update_user_role(user_id, UserRole.USER, session)
            await update.message.reply_text(f"✅ החסימה של משתמש {user.first_name or user.username or user_id} הוסרה בהצלחה.")
    
    # איפוס המצב
    del context.user_data["admin_action"]
    return True 