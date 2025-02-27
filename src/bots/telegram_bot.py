import logging
import os
from typing import Dict
from datetime import datetime, timezone
import traceback
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    Defaults,
    ConversationHandler
)
import httpx

# Import from our module structure
from src.core.config import TELEGRAM_TOKEN, ALLOWED_COMMANDS
# Import the new database module
from src.database.database import db
from src.database.rag_utils import add_document_from_file, search_documents
from src.agents.telegram_agent import TelegramAgent
# Import the new logger module
from src.utils.logger import setup_logger, log_exception, log_database_operation, log_telegram_message

# Configure logging
logger = setup_logger('telegram_bot')

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'

# Configure and initialize Logfire for monitoring
import logfire
# נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
try:
    logfire.configure(
        token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7',
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
except (AttributeError, ImportError):
    # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
    logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')
# הגבלת ניטור HTTP לכותרות בלבד ללא תוכן הבקשה
logfire.instrument_httpx(capture_headers=True, capture_body=False)

# מצבים לשיחה עם הבוט
WAITING_FOR_DOCUMENT = 1
WAITING_FOR_TITLE = 2
WAITING_FOR_SEARCH_QUERY = 3

class TelegramBot:
    def __init__(self):
        """Initialize the bot with OpenAI agent."""
        self.agent = TelegramAgent()
        self.typing_status: Dict[int, bool] = {}
        # מילון לשמירת מידע זמני על מסמכים בתהליך העלאה
        self.document_uploads: Dict[int, Dict] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        welcome_message = (
            f"שלום {user.first_name}! 👋\n\n"
            "אני בוט AI חכם שיכול לעזור לך בכל נושא ולשמור על מידע אישי עבורך.\n\n"
            "🤖 מה אני יכול לעשות?\n"
            "• לענות על שאלות בעברית\n"
            "• לשמור היסטוריית שיחות\n"
            "• לקבל ולעבד מסמכים במגוון פורמטים\n"
            "• לחפש מידע במסמכים שהעלית\n"
            "• לשלב מידע מהמסמכים בתשובות שלי\n\n"
            
            "📚 מערכת המסמכים החכמה\n"
            "אני תומך במגוון סוגי קבצים כולל PDF, Word, Excel, PowerPoint, HTML וטקסט.\n"
            "פשוט השתמש בפקודה /add_document כדי להתחיל.\n\n"
            
            "הקלד /help לרשימת כל הפקודות הזמינות."
        )
        # Log the start command
        logfire.info('command_start', user_id=user.id, username=user.username)
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_text = "הפקודות הזמינות:\n\n"
        for command, description in ALLOWED_COMMANDS:
            help_text += f"/{command} - {description}\n"
        
        # הוספת מידע על פקודות RAG
        help_text += "\nפקודות למערכת מסמכים (RAG):\n"
        help_text += "/add_document - הוספת מסמך למערכת הידע\n"
        help_text += "/search_documents - חיפוש במסמכים\n"
        help_text += "/list_documents - הצגת רשימת המסמכים שלך\n"
        
        # הוספת מידע על סוגי קבצים נתמכים
        help_text += "\nסוגי קבצים נתמכים למערכת הידע:\n"
        help_text += "📄 מסמכים: PDF, Word (DOCX)\n"
        help_text += "📊 גיליונות: Excel (XLSX)\n"
        help_text += "📑 מצגות: PowerPoint (PPTX)\n"
        help_text += "🌐 אינטרנט: HTML, HTM\n"
        help_text += "📝 טקסט: TXT, MD, JSON, XML, CSV\n"
        
        # Log the help command
        logfire.info('command_help', user_id=update.effective_user.id)
        await update.message.reply_text(help_text)

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /clear command."""
        user_id = update.effective_user.id
        # Log the clear command
        logfire.info('command_clear', user_id=user_id)
        db.clear_chat_history(user_id)
        await update.message.reply_text("היסטוריית השיחה נמחקה! 🗑️")
        
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /stats command - show database statistics."""
        user_id = update.effective_user.id
        
        # Log the stats command
        logfire.info('command_stats', user_id=user_id)
        
        try:
            # Get statistics from database
            message_count = db.get_message_count()
            user_count = db.get_user_count()
            
            # Get user's personal stats
            user_history = db.get_chat_history(user_id)
            user_message_count = len(user_history)
            
            stats_message = (
                "📊 סטטיסטיקות הבוט:\n\n"
                f"סה\"כ הודעות במערכת: {message_count}\n"
                f"מספר משתמשים ייחודיים: {user_count}\n\n"
                f"הסטטיסטיקות שלך:\n"
                f"מספר ההודעות שלך: {user_message_count}\n"
            )
            
            await update.message.reply_text(stats_message)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            logfire.error('stats_error', user_id=user_id, error=str(e))
            await update.message.reply_text("אירעה שגיאה בהצגת הסטטיסטיקות. אנא נסה שוב מאוחר יותר.")

    # פקודות חדשות למערכת RAG

    async def add_document_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך הוספת מסמך"""
        user_id = update.effective_user.id
        logfire.info('command_add_document_start', user_id=user_id)
        
        await update.message.reply_text(
            "📚 *הוספת מסמך למערכת הידע האישית שלך*\n\n"
            "אנא שלח לי קובץ מסמך (PDF, Word, Excel, PowerPoint, HTML או טקסט).\n"
            "המסמך יכול להכיל מידע אישי, מתכונים, הוראות, או כל מידע אחר שתרצה שאזכור בשיחות שלנו.\n\n"
            "💡 *טיפ:* מומלץ לארגן את המידע בצורה ברורה עם כותרות וסעיפים.\n"
            "גודל מקסימלי: 20MB\n\n"
            "אם ברצונך לבטל את התהליך, הקלד /cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_DOCUMENT
    
    async def add_document_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת קובץ מסמך מהמשתמש"""
        user_id = update.effective_user.id
        
        # בדיקה אם נשלח קובץ
        if not update.message.document:
            await update.message.reply_text(
                "❌ לא זיהיתי קובץ. אנא שלח קובץ מסמך (PDF, Word, Excel, PowerPoint, HTML או טקסט).\n"
                "אם ברצונך לבטל, הקלד /cancel."
            )
            return WAITING_FOR_DOCUMENT
        
        document = update.message.document
        file_name = document.file_name
        
        # בדיקה אם זה סוג קובץ נתמך
        supported_extensions = {
            'מסמכים': ['.pdf', '.docx'],
            'גיליונות': ['.xlsx'],
            'מצגות': ['.pptx'],
            'אינטרנט': ['.html', '.htm'],
            'טקסט': ['.txt', '.md', '.json', '.xml', '.csv']
        }
        
        # שטוח את כל הסיומות הנתמכות לרשימה אחת
        all_supported_extensions = [ext for group in supported_extensions.values() for ext in group]
        
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in all_supported_extensions:
            # מציאת הקטגוריה של כל סוג קובץ לתצוגה מסודרת
            extensions_by_category = "\n".join([
                f"• {category}: {', '.join(exts)}" 
                for category, exts in supported_extensions.items()
            ])
            
            await update.message.reply_text(
                f"❌ סוג הקובץ {file_ext} אינו נתמך כרגע.\n\n"
                f"הסוגים הנתמכים הם:\n{extensions_by_category}\n\n"
                "אם ברצונך לבטל, הקלד /cancel."
            )
            return WAITING_FOR_DOCUMENT
        
        # בדיקת גודל הקובץ (מקסימום 20MB)
        if document.file_size > 20 * 1024 * 1024:  # 20MB
            size_mb = document.file_size / (1024 * 1024)
            await update.message.reply_text(
                f"❌ הקובץ גדול מדי ({size_mb:.1f}MB). הגודל המקסימלי הוא 20MB.\n"
                "אנא חלק את הקובץ לקבצים קטנים יותר או דחס אותו ונסה שוב."
            )
            return WAITING_FOR_DOCUMENT
        
        # זיהוי סוג הקובץ לתצוגה ידידותית
        file_type_display = "קובץ"
        for category, extensions in supported_extensions.items():
            if file_ext in extensions:
                file_type_display = f"{category} ({file_ext})"
                break
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            f"⏳ מוריד את ה{file_type_display}... אנא המתן."
        )
        
        try:
            # הורדת הקובץ
            file = await context.bot.get_file(document.file_id)
            download_path = f"temp_{user_id}_{file_name}"
            await file.download_to_drive(download_path)
            
            # לוג על הורדת הקובץ
            file_size_mb = document.file_size / (1024 * 1024)
            logfire.info(
                'document_downloaded', 
                user_id=user_id, 
                file_type=file_ext,
                file_size_mb=f"{file_size_mb:.2f}",
                file_name=file_name
            )
            
            # עדכון הודעת ההמתנה
            await safe_edit_message(
                wait_message,
                f"✅ הקובץ התקבל בהצלחה!\n"
                f"סוג: {file_type_display}\n"
                f"גודל: {file_size_mb:.2f}MB\n\n"
                f"המערכת תעבד את הקובץ בשלב הבא...",
                user_id=user_id
            )
            
            # שמירת נתיב הקובץ בהקשר לשימוש בשלב הבא
            context.user_data['document_path'] = download_path
            context.user_data['document_name'] = file_name
            context.user_data['document_type'] = file_ext
            
            # בקשת כותרת למסמך
            await update.message.reply_text(
                "🔤 אנא הזן כותרת למסמך שתעזור לך לזהות אותו בעתיד.\n\n"
                "לדוגמה: 'מתכון עוגת שוקולד', 'הוראות הפעלה למכשיר X', 'סיכום פגישה 12.5.2023'\n\n"
                "או הקלד 'דלג' כדי להשתמש בשם הקובץ כברירת מחדל."
            )
            
            return WAITING_FOR_TITLE
            
        except Exception as e:
            # מחיקת הקובץ אם קיים
            if 'download_path' in locals() and os.path.exists(download_path):
                os.remove(download_path)
                
            logfire.error("document_download_error", user_id=user_id, error=str(e))
            await update.message.reply_text(
                f"❌ אירעה שגיאה בהורדת הקובץ: {str(e)}\n"
                "אנא נסה שוב מאוחר יותר או נסה קובץ אחר."
            )
            return ConversationHandler.END
    
    async def add_document_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כותרת למסמך והוספתו למערכת RAG"""
        user_id = update.effective_user.id
        title = update.message.text.strip()
        
        # בדיקה אם המשתמש רוצה לדלג על הכותרת
        if title.lower() in ['דלג', 'skip', 'default']:
            title = None  # נשתמש בשם הקובץ כברירת מחדל
        
        # הודעת המתנה
        wait_message = await update.message.reply_text("⏳ מוסיף את המסמך למערכת הידע... אנא המתן.")
        
        try:
            # קבלת נתיב הקובץ מההקשר
            download_path = context.user_data.get('document_path')
            file_name = context.user_data.get('document_name')
            file_type = context.user_data.get('document_type')
            
            if not download_path or not os.path.exists(download_path):
                await wait_message.edit_text(
                    "❌ אירעה שגיאה. אנא התחל את התהליך מחדש עם /add_document."
                )
                return ConversationHandler.END
            
            # מטא-דאטה למסמך
            metadata = {
                "user_id": user_id,
                "username": update.effective_user.username,
                "upload_source": "telegram_bot",
                "original_filename": file_name,
                "file_type": file_type
            }
            
            # הוספת המסמך למערכת RAG
            try:
                doc_id = await add_document_from_file(
                    file_path=download_path,
                    title=title,  # אם None, יתבצע שימוש בשם הקובץ
                    source=f"telegram_{file_type.replace('.', '')}",  # למשל: telegram_pdf, telegram_docx
                    metadata=metadata
                )
                
                # מחיקת הקובץ הזמני - עם מנגנון ניסיונות חוזרים
                file_deleted = False
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(download_path):
                            os.remove(download_path)
                            file_deleted = True
                            break
                    except Exception as cleanup_error:
                        logfire.warning(
                            'document_cleanup_retry', 
                            user_id=user_id, 
                            error=str(cleanup_error),
                            attempt=attempt + 1,
                            max_attempts=max_attempts
                        )
                        # המתנה קצרה לפני ניסיון נוסף
                        await asyncio.sleep(1)
                
                if not file_deleted:
                    logfire.error(
                        'document_cleanup_failed', 
                        user_id=user_id, 
                        file_path=download_path,
                        attempts=max_attempts
                    )
                
                # ניקוי נתוני המשתמש
                context.user_data.pop('document_path', None)
                context.user_data.pop('document_name', None)
                context.user_data.pop('document_type', None)
                
                # קריאת מידע על המסמך שנוסף
                with db.Session() as session:
                    from src.database.models import Document, DocumentChunk
                    document = session.query(Document).filter(Document.id == doc_id).first()
                    chunks_count = session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
                    
                    # שימוש בכותרת שנשמרה במסד הנתונים (במקרה שהשתמשנו בברירת מחדל)
                    actual_title = document.title if document else (title or file_name)
                    
                    # הכנת הודעת סיכום
                    success_message = (
                        f"✅ המסמך '*{actual_title}*' נוסף בהצלחה למערכת הידע! 📚\n\n"
                        f"**פרטי המסמך:**\n"
                        f"🆔 מזהה: {doc_id}\n"
                        f"📄 סוג קובץ: {file_type}\n"
                        f"📊 מספר קטעים שנוצרו: {chunks_count}\n\n"
                        f"**כיצד להשתמש במסמך?**\n"
                        f"פשוט שאל אותי שאלות הקשורות למידע שבמסמך, ואני אשלב את המידע בתשובותיי.\n"
                        f"לדוגמה: 'מה המידע שיש לך על {actual_title}?'\n\n"
                        f"**לחיפוש במסמכים:**\n"
                        f"השתמש בפקודה /search_documents כדי לחפש מידע ספציפי במסמכים שלך."
                    )
                
                await safe_edit_message(wait_message, success_message, parse_mode='Markdown', user_id=user_id)
                
            except Exception as e:
                logfire.error('document_processing_error', user_id=user_id, error=str(e))
                await wait_message.edit_text(
                    f"❌ אירעה שגיאה בעיבוד המסמך: {str(e)}\n"
                    "אנא נסה שוב עם קובץ אחר."
                )
                
                # מחיקת הקובץ הזמני במקרה של שגיאה
                if os.path.exists(download_path):
                    os.remove(download_path)
                
                return ConversationHandler.END
            
        except Exception as e:
            logfire.error('document_add_error', user_id=user_id, error=str(e))
            
            # ניסיון למחוק את הקובץ הזמני במקרה של שגיאה - עם מנגנון ניסיונות חוזרים
            download_path = context.user_data.get('document_path')
            if download_path:
                file_deleted = False
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if os.path.exists(download_path):
                            os.remove(download_path)
                            file_deleted = True
                            break
                    except Exception as cleanup_error:
                        logfire.warning(
                            'document_cleanup_retry', 
                            user_id=user_id, 
                            error=str(cleanup_error),
                            attempt=attempt + 1,
                            max_attempts=max_attempts
                        )
                        # המתנה קצרה לפני ניסיון נוסף
                        await asyncio.sleep(1)
                
                if not file_deleted:
                    logfire.error(
                        'document_cleanup_failed', 
                        user_id=user_id, 
                        file_path=download_path,
                        attempts=max_attempts
                    )
            
            # הודעת שגיאה מותאמת למשתמש
            error_message = str(e)
            if "הקובץ נעול על ידי תהליך אחר" in error_message:
                await wait_message.edit_text(
                    f"❌ אירעה שגיאה בהוספת המסמך: הקובץ נעול על ידי תהליך אחר.\n"
                    f"אנא ודא שהקובץ אינו פתוח בתוכנה אחרת ונסה שוב מאוחר יותר."
                )
            elif "WinError 32" in error_message and "being used by another process" in error_message:
                await wait_message.edit_text(
                    f"❌ אירעה שגיאה בהוספת המסמך: הקובץ נעול על ידי תהליך אחר.\n"
                    f"אנא ודא שהקובץ אינו פתוח בתוכנה אחרת ונסה שוב מאוחר יותר."
                )
            elif "parse entities" in error_message.lower():
                try:
                    # ניסיון לשלוח הודעה פשוטה ללא עיצוב
                    await wait_message.edit_text(
                        f"❌ אירעה שגיאה בהוספת המסמך.\n"
                        "אנא נסה שוב מאוחר יותר."
                    )
                except Exception as edit_error:
                    # אם גם זה נכשל, ננסה לשלוח הודעה חדשה במקום לערוך
                    logfire.error('message_edit_failed', user_id=user_id, error=str(edit_error))
                    await update.message.reply_text(
                        f"❌ אירעה שגיאה בהוספת המסמך.\n"
                        "אנא נסה שוב מאוחר יותר."
                    )
            else:
                await wait_message.edit_text(
                    f"❌ אירעה שגיאה בהוספת המסמך: {str(e)}\n"
                    "אנא נסה שוב מאוחר יותר."
                )
            
        return ConversationHandler.END
    
    async def search_documents_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך חיפוש במסמכים"""
        user_id = update.effective_user.id
        logfire.info('command_search_documents_start', user_id=user_id)
        
        await update.message.reply_text(
            "🔍 *חיפוש במסמכים האישיים שלך*\n\n"
            "אנא הקלד את מה שברצונך לחפש במסמכים שהעלית למערכת.\n"
            "לדוגמה: 'מידע על המשפחה שלי', 'מתי נולד אחי', וכדומה.\n\n"
            "אם ברצונך לבטל את החיפוש, הקלד /cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_SEARCH_QUERY
    
    async def search_documents_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """ביצוע חיפוש במסמכים לפי שאילתה"""
        user_id = update.effective_user.id
        query = update.message.text
        
        # שליחת הודעת המתנה
        wait_message = await update.message.reply_text("🔍 מחפש במסמכים... אנא המתן.")
        
        try:
            # חיפוש במסמכים
            results = await search_documents(query, limit=5, min_similarity=0.0)
            
            if not results:
                await wait_message.edit_text(
                    "❌ לא נמצאו תוצאות מתאימות לחיפוש שלך.\n\n"
                    "💡 טיפים לחיפוש יעיל יותר:\n"
                    "• נסה להשתמש במילות מפתח ספציפיות\n"
                    "• בדוק שאין שגיאות כתיב\n"
                    "• נסה לחפש בעברית או באנגלית\n"
                    "• אם חיפשת ביטוי מדויק, נסה לחפש מילים בודדות\n\n"
                    "אם עדיין לא מצאת, ייתכן שהמידע לא קיים במסמכים שהעלית."
                )
                return ConversationHandler.END
            
            # לוג על תוצאות החיפוש
            logfire.info(
                'search_documents_results', 
                user_id=user_id, 
                query=query, 
                results_count=len(results),
                top_similarity=results[0]['similarity'] if results else 0
            )
            
            # בניית הודעת תוצאות
            response = f"🔍 *תוצאות חיפוש עבור:* '{query}'\n\n"
            
            # הוספת סיכום תוצאות
            response += f"*נמצאו {len(results)} תוצאות רלוונטיות*\n\n"
            
            # הצגת התוצאות
            for i, result in enumerate(results, 1):
                similarity_percentage = int(result['similarity'] * 100)
                
                # זיהוי סוג הקובץ לפי המקור
                file_type_icon = "📄"
                source = result['source']
                if "pdf" in source:
                    file_type_icon = "📕"
                elif "docx" in source:
                    file_type_icon = "📘"
                elif "xlsx" in source:
                    file_type_icon = "📊"
                elif "pptx" in source:
                    file_type_icon = "📑"
                elif "html" in source:
                    file_type_icon = "🌐"
                
                # הוספת מידע על התוצאה
                response += f"{file_type_icon} *תוצאה {i}* (התאמה: {similarity_percentage}%)\n"
                response += f"*מסמך:* {result['title']}\n"
                
                # הוספת תאריך העלאה אם קיים
                if 'upload_date' in result and result['upload_date']:
                    upload_date = result['upload_date'].split('T')[0] if 'T' in result['upload_date'] else result['upload_date']
                    response += f"*הועלה:* {upload_date}\n"
                
                # הגבלת אורך התוכן המוצג
                content_preview = result['content']
                if len(content_preview) > 250:
                    # חיתוך בגבול מילה
                    content_preview = content_preview[:247] + "..."
                
                # הדגשת מילות החיפוש בתוכן
                # פשוט מוסיף סימני * לפני ואחרי מילות החיפוש
                query_words = query.split()
                for word in query_words:
                    if len(word) > 2:  # רק מילים באורך 3 תווים ומעלה
                        # החלפה רק אם המילה מופיעה כמילה שלמה
                        content_preview = content_preview.replace(f" {word} ", f" *{word}* ")
                
                response += f"*תוכן:* {content_preview}\n\n"
            
            # הוספת הסבר כיצד להשתמש במידע
            response += (
                "*כיצד להשתמש במידע זה?*\n"
                "• שאל אותי שאלה ספציפית על המידע שמצאת\n"
                "• אוכל לשלב את המידע מהמסמכים בתשובות שלי\n"
                "• לדוגמה: 'מה המידע שיש לך על X מהמסמך Y?'\n\n"
                "לחיפוש נוסף, השתמש שוב בפקודה /search_documents"
            )
            
            await safe_edit_message(
                wait_message,
                f"✅ *תוצאות החיפוש עבור:* '{query}'\n\n{response}",
                parse_mode='Markdown',
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            logfire.error('search_documents_error', user_id=user_id, query=query, error=str(e))
            await wait_message.edit_text(
                "❌ אירעה שגיאה בחיפוש. אנא נסה שוב מאוחר יותר.\n\n"
                f"פרטי השגיאה: {str(e)}\n\n"
                "אם הבעיה נמשכת, פנה למנהל המערכת."
            )
        
        return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """ביטול שיחה פעילה"""
        user_id = update.effective_user.id
        
        # ניקוי קבצים זמניים אם יש
        if user_id in self.document_uploads and 'file_path' in self.document_uploads[user_id]:
            try:
                file_path = self.document_uploads[user_id]['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            
            # מחיקת המידע הזמני
            del self.document_uploads[user_id]
        
        logfire.info('conversation_cancelled', user_id=user_id)
        await update.message.reply_text("הפעולה בוטלה.")
        return ConversationHandler.END

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user_id = update.effective_user.id
        message_text = update.message.text

        # Show typing indicator
        self.typing_status[user_id] = True
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            # Log the incoming message
            log_telegram_message(logger, user_id, message_text)
            
            # Create a Logfire span to track the entire message handling process
            with logfire.span('handle_telegram_message', user_id=user_id, message_length=len(message_text)):
                # Get chat history
                try:
                    history = db.get_chat_history(user_id)
                    logger.debug(f"Retrieved chat history for user {user_id}: {len(history)} messages")
                except Exception as db_error:
                    log_exception(logger, db_error, {'operation': 'get_chat_history', 'user_id': user_id})
                    history = []  # Use empty history if retrieval fails
                
                # בדיקה אם זו פקודה להחלפת מודל
                if message_text.startswith('/switch_model'):
                    parts = message_text.split()
                    if len(parts) > 1:
                        new_model = parts[1]
                        # בדיקה אם המודל תקין
                        valid_models = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'claude-3-opus', 'claude-3-sonnet']
                        if any(model in new_model for model in valid_models):
                            # עדכון המודל העיקרי
                            old_model = self.agent.primary_model_name
                            
                            # בדיקה אם המודל הוא של Anthropic
                            if 'claude' in new_model:
                                model_prefix = "anthropic:"
                            else:
                                model_prefix = "openai:"
                                
                            # אם המודל כבר מכיל prefix, לא נוסיף אותו שוב
                            if ':' not in new_model:
                                new_model_with_prefix = f"{model_prefix}{new_model}"
                            else:
                                new_model_with_prefix = new_model
                                
                            self.agent = TelegramAgent(new_model_with_prefix)
                            response = f"המודל הוחלף בהצלחה מ-{old_model} ל-{new_model_with_prefix}"
                            logger.info(f"Model switched for user {user_id} from {old_model} to {new_model_with_prefix}")
                        else:
                            response = f"המודל {new_model} אינו נתמך. המודלים הנתמכים הם: {', '.join(valid_models)}"
                    else:
                        response = "אנא ציין את שם המודל הרצוי. לדוגמה: /switch_model gpt-3.5-turbo"
                # בדיקה אם זו פקודת עזרה
                elif message_text.startswith('/help'):
                    response = (
                        "הפקודות הזמינות בבוט:\n\n"
                        "/help - הצגת רשימת הפקודות הזמינות\n"
                        "/models - הצגת המודלים הנוכחיים בשימוש\n"
                        "/switch_model [model_name] - החלפת המודל העיקרי (לדוגמה: /switch_model gpt-3.5-turbo)\n"
                        "/set_fallback [model_name] - הגדרת מודל גיבוי (לדוגמה: /set_fallback gpt-3.5-turbo)\n"
                        "/clear - מחיקת היסטוריית השיחה והתחלת שיחה חדשה\n"
                        "/searchdocuments [query] - חיפוש במסמכים האישיים שלך\n\n"
                        "מודלים זמינים: gpt-4, gpt-3.5-turbo, gpt-4o, claude-3-opus, claude-3-sonnet\n\n"
                        "שים לב: אם יש בעיות עם מכסת השימוש ב-API, נסה להחליף למודל אחר באמצעות הפקודה /switch_model"
                    )
                # בדיקה אם זו פקודה להגדרת מודל גיבוי
                elif message_text.startswith('/set_fallback'):
                    parts = message_text.split()
                    if len(parts) > 1:
                        new_fallback = parts[1]
                        # בדיקה אם המודל תקין
                        valid_models = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'claude-3-opus', 'claude-3-sonnet']
                        if any(model in new_fallback for model in valid_models):
                            # בדיקה אם המודל הוא של Anthropic
                            if 'claude' in new_fallback:
                                model_prefix = "anthropic:"
                            else:
                                model_prefix = "openai:"
                                
                            # אם המודל כבר מכיל prefix, לא נוסיף אותו שוב
                            if ':' not in new_fallback:
                                new_fallback_with_prefix = f"{model_prefix}{new_fallback}"
                            else:
                                new_fallback_with_prefix = new_fallback
                                
                            old_fallback = self.agent.fallback_model_name
                            self.agent.fallback_model_name = new_fallback_with_prefix
                            self.agent.fallback_agent = None  # איפוס הסוכן כדי שיאותחל מחדש בפעם הבאה
                            
                            response = f"מודל הגיבוי הוחלף בהצלחה מ-{old_fallback} ל-{new_fallback_with_prefix}"
                            logger.info(f"Fallback model set for user {user_id} from {old_fallback} to {new_fallback_with_prefix}")
                        else:
                            response = f"המודל {new_fallback} אינו נתמך. המודלים הנתמכים הם: {', '.join(valid_models)}"
                    else:
                        response = "אנא ציין את שם מודל הגיבוי הרצוי. לדוגמה: /set_fallback gpt-3.5-turbo"
                # בדיקה אם זו פקודה להצגת המודלים הנוכחיים
                elif message_text.startswith('/models'):
                    primary_model = self.agent.primary_model_name
                    fallback_model = self.agent.fallback_model_name
                    
                    response = (
                        f"המודלים הנוכחיים בשימוש:\n\n"
                        f"מודל עיקרי: {primary_model}\n"
                        f"מודל גיבוי: {fallback_model}\n\n"
                        f"לשינוי המודל העיקרי, השתמש בפקודה: /switch_model [model_name]\n"
                        f"לשינוי מודל הגיבוי, השתמש בפקודה: /set_fallback [model_name]"
                    )
                # קריאה ל-Agent עם תמיכה ב-RAG
                else:
                    try:
                        response = await self.agent.get_response(user_id, message_text, history, use_rag=True)
                        logger.info(f"Got response for user {user_id}")
                    except Exception as agent_error:
                        log_exception(logger, agent_error, {'operation': 'agent_get_response', 'user_id': user_id})
                        # בדיקה אם השגיאה קשורה למכסה
                        error_message = str(agent_error).lower()
                        if "quota" in error_message or "exceeded" in error_message or "429" in error_message:
                            response = (
                                "מצטער, חרגנו ממכסת השימוש ב-API של OpenAI. "
                                "אנא נסה להשתמש במודל אחר באמצעות הפקודה /switch_model gpt-3.5-turbo"
                            )
                        else:
                            response = "מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר."
                
                # Send response
                await update.message.reply_text(response)
                log_telegram_message(logger, user_id, message_text, response)

        except Exception as e:
            error_context = {
                'user_id': user_id,
                'message_length': len(message_text) if message_text else 0
            }
            log_exception(logger, e, error_context)
            # Log the error in Logfire
            with logfire.span('message_handling_error'):
                logfire.error(str(e))
            
            # Send error message to user
            await update.message.reply_text("מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר.")
        finally:
            # Clear typing status
            self.typing_status[user_id] = False

    async def list_documents(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת רשימת המסמכים שהמשתמש העלה למערכת"""
        user_id = update.effective_user.id
        
        # לוג על הפעלת הפקודה
        logfire.info('command_list_documents', user_id=user_id)
        
        # הודעת המתנה
        wait_message = await update.message.reply_text("⏳ מאחזר את רשימת המסמכים שלך... אנא המתן.")
        
        try:
            # אתחול מסד הנתונים אם צריך
            if db.engine is None:
                db.init_db()
            
            # שליפת רשימת המסמכים של המשתמש
            with db.Session() as session:
                from src.database.models import Document
                
                # חיפוש מסמכים שהועלו על ידי המשתמש הנוכחי
                # בדיקה במטא-דאטה של המסמך
                documents = session.query(Document).all()
                
                # סינון רק מסמכים של המשתמש הנוכחי
                user_documents = []
                for doc in documents:
                    try:
                        metadata = doc.doc_metadata
                        if metadata and isinstance(metadata, dict) and metadata.get('user_id') == user_id:
                            user_documents.append(doc)
                    except:
                        # אם יש בעיה בפענוח המטא-דאטה, נדלג על המסמך
                        continue
            
            if not user_documents:
                await wait_message.edit_text(
                    "📚 *אין לך מסמכים במערכת*\n\n"
                    "עדיין לא העלית מסמכים למערכת הידע האישית שלך.\n"
                    "השתמש בפקודה /add_document כדי להוסיף מסמך חדש.",
                    parse_mode='Markdown'
                )
                return
            
            # מיון המסמכים לפי תאריך העלאה (מהחדש לישן)
            user_documents.sort(key=lambda x: x.upload_date, reverse=True)
            
            # בניית הודעת תשובה
            response = f"📚 *המסמכים שלך במערכת ({len(user_documents)})*\n\n"
            
            for i, doc in enumerate(user_documents, 1):
                # זיהוי סוג הקובץ לפי המקור
                file_type_icon = "📄"
                source = doc.source
                if "pdf" in source:
                    file_type_icon = "📕"
                elif "docx" in source:
                    file_type_icon = "📘"
                elif "xlsx" in source:
                    file_type_icon = "📊"
                elif "pptx" in source:
                    file_type_icon = "📑"
                elif "html" in source:
                    file_type_icon = "🌐"
                
                # פורמט תאריך העלאה
                upload_date = doc.upload_date.strftime("%d/%m/%Y") if doc.upload_date else "לא ידוע"
                
                # הוספת מידע על המסמך
                response += f"{i}. {file_type_icon} *{doc.title}*\n"
                response += f"   📅 הועלה: {upload_date}\n"
                
                # הוספת מידע על סוג הקובץ אם קיים במטא-דאטה
                try:
                    metadata = doc.doc_metadata
                    if metadata and isinstance(metadata, dict):
                        file_type = metadata.get('file_type', '')
                        if file_type:
                            response += f"   🔖 סוג: {file_type}\n"
                        
                        # הוספת שם הקובץ המקורי אם קיים
                        original_filename = metadata.get('original_filename', '')
                        if original_filename and original_filename != doc.title:
                            response += f"   📎 שם קובץ: {original_filename}\n"
                except:
                    # אם יש בעיה בפענוח המטא-דאטה, נדלג על המידע הנוסף
                    pass
                
                # הוספת תוכן קצר מהמסמך
                content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                content_preview = content_preview.replace('\n', ' ')
                response += f"   💬 תוכן: {content_preview}\n\n"
            
            # הוספת הסבר כיצד להשתמש במסמכים
            response += (
                "*כיצד להשתמש במסמכים שלך?*\n"
                "• שאל אותי שאלות על המידע שבמסמכים\n"
                "• חפש מידע ספציפי עם /search_documents\n"
                "• הוסף מסמכים נוספים עם /add_document\n"
            )
            
            await safe_edit_message(wait_message, response, parse_mode='Markdown', user_id=user_id)
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            logfire.error('list_documents_error', user_id=user_id, error=str(e))
            await wait_message.edit_text(
                "❌ אירעה שגיאה בהצגת רשימת המסמכים.\n"
                "אנא נסה שוב מאוחר יותר."
            )

    async def run(self):
        """Start the bot."""
        try:
            # Log application startup
            logfire.info('telegram_bot_starting')
            
            # הגדרת Defaults עם tzinfo בלבד
            defaults = Defaults(
                tzinfo=timezone.utc
            )
            
            # Create the Application with defaults and increased timeouts
            application = Application.builder()\
                .token(TELEGRAM_TOKEN)\
                .defaults(defaults)\
                .read_timeout(30.0)\
                .write_timeout(30.0)\
                .connect_timeout(30.0)\
                .pool_timeout(30.0)\
                .build()
            
            # הגדרת ConversationHandler להוספת מסמכים
            add_document_handler = ConversationHandler(
                entry_points=[CommandHandler("add_document", self.add_document_start)],
                states={
                    WAITING_FOR_DOCUMENT: [MessageHandler(filters.ATTACHMENT, self.add_document_receive)],
                    WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_document_title)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            )
            
            # הגדרת ConversationHandler לחיפוש במסמכים
            search_documents_handler = ConversationHandler(
                entry_points=[CommandHandler("search_documents", self.search_documents_start)],
                states={
                    WAITING_FOR_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_documents_query)],
                },
                fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            )
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(CommandHandler("clear", self.clear))
            application.add_handler(CommandHandler("stats", self.stats))
            application.add_handler(add_document_handler)
            application.add_handler(search_documents_handler)
            application.add_handler(CommandHandler("list_documents", self.list_documents))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            # Log successful initialization
            logfire.info('telegram_bot_initialized')
            
            # Start the bot with improved settings
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                # הגבלת סוגי העדכונים רק לאלה שאנחנו באמת צריכים
                allowed_updates=["message", "edited_message", "callback_query", "chat_member"],
                # הגדרת זמן ארוך יותר בין בקשות עדכון
                poll_interval=5.0,
                # הגדרת מספר ניסיונות חוזרים
                bootstrap_retries=5
            )
            
            # שומר על הבוט פעיל
            logger.info("Bot is running. Press Ctrl+C to stop")
            # נשאר בלולאה אינסופית עד שיש הפרעה
            while True:
                await asyncio.sleep(1)
            
        except Exception as e:
            # Log any startup errors
            logfire.error('telegram_bot_startup_error', error=str(e))
            logger.error(f"Error starting bot: {e}")
            raise 

# הוספת פונקציית עזר לעריכת הודעות עם טיפול בשגיאות פרסור
async def safe_edit_message(message, text, parse_mode=None, user_id=None):
    """
    פונקציית עזר לעריכת הודעות עם טיפול בשגיאות פרסור
    
    Args:
        message: הודעת טלגרם לעריכה
        text: הטקסט החדש
        parse_mode: מצב פרסור (Markdown, HTML, וכו')
        user_id: מזהה המשתמש (לצורך לוגים)
    
    Returns:
        ההודעה המעודכנת
    """
    try:
        # ניסיון לערוך את ההודעה עם פרסור
        if parse_mode:
            return await message.edit_text(text, parse_mode=parse_mode)
        else:
            return await message.edit_text(text)
    except Exception as e:
        # אם יש שגיאת פרסור ישויות, ננסה לשלוח ללא עיצוב
        if "parse entities" in str(e).lower() or "can't parse entities" in str(e).lower():
            if user_id:
                logfire.warning('message_format_error', user_id=user_id, error=str(e))
            
            # הסרת סימוני Markdown
            plain_text = text
            if parse_mode == 'Markdown' or parse_mode == 'MarkdownV2':
                plain_text = plain_text.replace('*', '').replace('_', '').replace('`', '').replace('**', '')
            
            # ניסיון לשלוח ללא עיצוב
            try:
                return await message.edit_text(plain_text)
            except Exception as edit_error:
                if user_id:
                    logfire.error('message_edit_failed', user_id=user_id, error=str(edit_error))
                # אם גם זה נכשל, נחזיר את השגיאה המקורית
                raise e
        else:
            # אם זו שגיאה אחרת, נזרוק אותה שוב
            raise 