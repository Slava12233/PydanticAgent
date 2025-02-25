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

# Configure and initialize Logfire for monitoring
import logfire
logfire.configure()
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
            "אני בוט AI שיכול לעזור לך בכל נושא.\n"
            "פשוט שלח לי הודעה ואשמח לעזור!\n\n"
            "הקלד /help לרשימת הפקודות."
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
            "אנא שלח לי קובץ טקסט (.txt) שברצונך להוסיף למערכת הידע.\n"
            "המסמך יכול להכיל מידע אישי, מתכונים, הוראות, או כל מידע אחר שתרצה שאזכור בשיחות שלנו.\n\n"
            "💡 *טיפ:* מומלץ לארגן את המידע בצורה ברורה עם כותרות וסעיפים.\n"
            "גודל מקסימלי: 10MB\n\n"
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
                "❌ לא זיהיתי קובץ. אנא שלח קובץ טקסט (.txt).\n"
                "אם ברצונך לבטל, הקלד /cancel."
            )
            return WAITING_FOR_DOCUMENT
        
        document = update.message.document
        file_name = document.file_name
        
        # בדיקה אם זה קובץ טקסט
        if not file_name.lower().endswith('.txt'):
            await update.message.reply_text(
                "❌ אני יכול לעבד רק קבצי טקסט (.txt) כרגע.\n"
                "אנא המר את הקובץ לפורמט טקסט ונסה שוב.\n"
                "אם ברצונך לבטל, הקלד /cancel."
            )
            return WAITING_FOR_DOCUMENT
        
        # בדיקת גודל הקובץ (מקסימום 10MB)
        if document.file_size > 10 * 1024 * 1024:  # 10MB
            await update.message.reply_text(
                "❌ הקובץ גדול מדי. הגודל המקסימלי הוא 10MB.\n"
                "אנא חלק את הקובץ לקבצים קטנים יותר ונסה שוב."
            )
            return WAITING_FOR_DOCUMENT
        
        # הודעת המתנה
        wait_message = await update.message.reply_text("⏳ מוריד את הקובץ... אנא המתן.")
        
        try:
            # הורדת הקובץ
            file = await context.bot.get_file(document.file_id)
            download_path = f"temp_{user_id}_{file_name}"
            await file.download_to_drive(download_path)
            
            # עדכון הודעת ההמתנה
            await wait_message.edit_text("✅ הקובץ התקבל בהצלחה! מעבד את הקובץ...")
            
            # בדיקת תוכן הקובץ
            try:
                with open(download_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # בדיקה שהקובץ לא ריק
                    if not content.strip():
                        os.remove(download_path)
                        await wait_message.edit_text(
                            "❌ הקובץ ריק. אנא שלח קובץ עם תוכן."
                        )
                        return WAITING_FOR_DOCUMENT
                    
                    # בדיקה שהקובץ לא גדול מדי בתווים
                    if len(content) > 1000000:  # ~1MB של טקסט
                        os.remove(download_path)
                        await wait_message.edit_text(
                            "❌ הקובץ מכיל יותר מדי טקסט. אנא חלק אותו לקבצים קטנים יותר."
                        )
                        return WAITING_FOR_DOCUMENT
            except UnicodeDecodeError:
                os.remove(download_path)
                await wait_message.edit_text(
                    "❌ לא הצלחתי לקרוא את הקובץ. אנא ודא שהקובץ הוא טקסט בקידוד UTF-8."
                )
                return WAITING_FOR_DOCUMENT
            
            # שמירת מידע על הקובץ
            self.document_uploads[user_id] = {
                'file_path': download_path,
                'original_name': file_name,
                'file_size': document.file_size,
                'content_length': len(content)
            }
            
            logfire.info('document_received', user_id=user_id, file_name=file_name, file_size=document.file_size)
            
            # בקשת כותרת למסמך
            await wait_message.edit_text(
                f"✅ קובץ *{file_name}* התקבל בהצלחה!\n\n"
                f"אנא הזן כותרת למסמך זה (תיאור קצר של תוכן המסמך):\n\n"
                f"לדוגמה: 'מידע על המשפחה שלי', 'מתכונים אהובים', 'הוראות הפעלה למכשיר X'",
                parse_mode='Markdown'
            )
            return WAITING_FOR_TITLE
            
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            logfire.error('document_download_error', user_id=user_id, file_name=file_name, error=str(e))
            
            # ניסיון למחוק את הקובץ הזמני במקרה של שגיאה
            try:
                if os.path.exists(download_path):
                    os.remove(download_path)
            except:
                pass
            
            await wait_message.edit_text(
                "❌ אירעה שגיאה בהורדת הקובץ. אנא נסה שוב מאוחר יותר."
            )
            return WAITING_FOR_DOCUMENT
    
    async def add_document_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כותרת למסמך"""
        user_id = update.effective_user.id
        title = update.message.text
        
        if user_id not in self.document_uploads:
            await update.message.reply_text(
                "❌ אירעה שגיאה. אנא התחל את התהליך מחדש עם /add_document."
            )
            return ConversationHandler.END
        
        # בדיקת אורך הכותרת
        if len(title) > 100:
            await update.message.reply_text(
                "❌ הכותרת ארוכה מדי. אנא הזן כותרת קצרה יותר (עד 100 תווים)."
            )
            return WAITING_FOR_TITLE
        
        # הוספת הכותרת למידע על המסמך
        self.document_uploads[user_id]['title'] = title
        
        # שליחת הודעת המתנה
        wait_message = await update.message.reply_text("⏳ מעבד את המסמך... אנא המתן.")
        
        try:
            # הוספת המסמך למערכת RAG
            doc_info = self.document_uploads[user_id]
            
            # הוספת מטא-דאטה
            metadata = {
                "uploaded_by": user_id, 
                "original_filename": doc_info['original_name'],
                "upload_date": datetime.utcnow().isoformat(),
                "file_size": doc_info.get('file_size', 0),
                "content_length": doc_info.get('content_length', 0)
            }
            
            doc_id = await add_document_from_file(
                file_path=doc_info['file_path'],
                title=doc_info['title'],
                source="telegram_upload",
                metadata=metadata
            )
            
            # מחיקת הקובץ הזמני
            os.remove(doc_info['file_path'])
            
            # מחיקת המידע הזמני
            del self.document_uploads[user_id]
            
            logfire.info('document_added_success', user_id=user_id, doc_id=doc_id, title=title)
            
            # קריאת מידע על המסמך שנוסף
            with db.Session() as session:
                from src.database.models import Document, DocumentChunk
                document = session.query(Document).filter(Document.id == doc_id).first()
                chunks_count = session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
                
                # הכנת הודעת סיכום
                success_message = (
                    f"✅ המסמך '*{title}*' נוסף בהצלחה למערכת הידע! 📚\n\n"
                    f"**פרטי המסמך:**\n"
                    f"🆔 מזהה: {doc_id}\n"
                    f"📄 שם קובץ מקורי: {doc_info['original_name']}\n"
                    f"📊 מספר קטעים שנוצרו: {chunks_count}\n\n"
                    f"**כיצד להשתמש במסמך?**\n"
                    f"פשוט שאל אותי שאלות הקשורות למידע שבמסמך, ואני אשלב את המידע בתשובותיי.\n"
                    f"לדוגמה: 'מה המידע שיש לך על {title}?'\n\n"
                    f"**לחיפוש במסמכים:**\n"
                    f"השתמש בפקודה /search_documents כדי לחפש מידע ספציפי במסמכים שלך."
                )
            
            await wait_message.edit_text(success_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            logfire.error('document_add_error', user_id=user_id, error=str(e))
            
            # ניסיון למחוק את הקובץ הזמני במקרה של שגיאה
            try:
                if os.path.exists(self.document_uploads[user_id]['file_path']):
                    os.remove(self.document_uploads[user_id]['file_path'])
            except:
                pass
            
            # מחיקת המידע הזמני
            if user_id in self.document_uploads:
                del self.document_uploads[user_id]
            
            await wait_message.edit_text(
                "❌ אירעה שגיאה בהוספת המסמך. אנא נסה שוב מאוחר יותר.\n"
                "אם הבעיה נמשכת, פנה למנהל המערכת."
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
                    "נסה לחפש בצורה אחרת או השתמש במילות מפתח שונות."
                )
                return ConversationHandler.END
            
            # בניית הודעת תוצאות
            response = f"🔍 *נמצאו {len(results)} תוצאות עבור '{query}'*\n\n"
            
            for i, result in enumerate(results, 1):
                similarity_percentage = int(result['similarity'] * 100)
                response += f"📄 *תוצאה {i}* (התאמה: {similarity_percentage}%)\n"
                response += f"*מסמך:* {result['title']}\n"
                response += f"*מקור:* {result['source']}\n"
                
                # הגבלת אורך התוכן המוצג והדגשת מילות מפתח
                content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                response += f"*תוכן:* {content_preview}\n\n"
            
            # הוספת הסבר כיצד להשתמש במידע
            response += (
                "*כיצד להשתמש במידע זה?*\n"
                "פשוט שאל אותי שאלה הקשורה למידע שמצאת, ואני אשלב את המידע בתשובה שלי."
            )
            
            logfire.info('search_documents_success', user_id=user_id, query=query, results_count=len(results))
            await wait_message.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            logfire.error('search_documents_error', user_id=user_id, query=query, error=str(e))
            await wait_message.edit_text(
                "❌ אירעה שגיאה בחיפוש. אנא נסה שוב מאוחר יותר.\n"
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
                
                # קריאה ל-Agent עם תמיכה ב-RAG
                try:
                    response = await self.agent.get_response(user_id, message_text, history, use_rag=True)
                    logger.info(f"Got response for user {user_id}")
                except Exception as agent_error:
                    log_exception(logger, agent_error, {'operation': 'agent_get_response', 'user_id': user_id})
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