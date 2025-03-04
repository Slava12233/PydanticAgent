import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

from src.database import db
from src.database.models import User, Document
from src.database.operations import get_user_by_telegram_id
from src.database.rag_utils import add_document_from_file, search_documents
from src.utils.logger import setup_logger, log_telegram_message

# Configure logging
logger = setup_logger('telegram_bot_documents')

# מצבי שיחה
WAITING_FOR_DOCUMENT = 1
WAITING_FOR_TITLE = 2
WAITING_FOR_SEARCH_QUERY = 3

class TelegramBotDocuments:
    """
    מחלקה לניהול מסמכים בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
    
    def get_add_document_handler(self) -> ConversationHandler:
        """
        יצירת handler להוספת מסמך
        
        Returns:
            ConversationHandler מוגדר להוספת מסמך
        """
        return ConversationHandler(
            entry_points=[CommandHandler("add_document", self.add_document_start)],
            states={
                WAITING_FOR_DOCUMENT: [
                    MessageHandler(filters.Document.ALL, self.add_document_receive),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_document_receive)
                ],
                WAITING_FOR_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_document_title)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    def get_search_documents_handler(self) -> ConversationHandler:
        """
        יצירת handler לחיפוש במסמכים
        
        Returns:
            ConversationHandler מוגדר לחיפוש במסמכים
        """
        return ConversationHandler(
            entry_points=[CommandHandler("search", self.search_documents_start)],
            states={
                WAITING_FOR_SEARCH_QUERY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_documents_query)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.bot.conversations.cancel_conversation)]
        )
    
    async def add_document_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך הוספת מסמך"""
        user_id = update.effective_user.id
        logger.info(f"Add document command from user {user_id}")
        
        await update.message.reply_text(
            "📄 *הוספת מסמך למאגר הידע*\n\n"
            "אנא שלח לי את המסמך שברצונך להוסיף.\n"
            "אני תומך בקבצי טקסט, PDF, Word ועוד.\n\n"
            "לביטול התהליך, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_DOCUMENT
    
    async def add_document_receive(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת המסמך מהמשתמש"""
        user_id = update.effective_user.id
        
        # בדיקה אם נשלח קובץ או טקסט
        if update.message.document:
            file = update.message.document
            file_name = file.file_name
            logger.info(f"Received document from user {user_id}: {file_name}")
            
            # שמירת פרטי הקובץ בקונטקסט
            context.user_data['document_file'] = file
            context.user_data['document_type'] = 'file'
            
        elif update.message.text:
            text = update.message.text
            logger.info(f"Received text from user {user_id}: {text[:50]}...")
            
            # שמירת הטקסט בקונטקסט
            context.user_data['document_text'] = text
            context.user_data['document_type'] = 'text'
        
        await update.message.reply_text(
            "מעולה! עכשיו אנא תן כותרת למסמך שתעזור לזהות אותו בקלות.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_TITLE
    
    async def add_document_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """קבלת כותרת למסמך"""
        user_id = update.effective_user.id
        title = update.message.text
        
        logger.info(f"Received document title from user {user_id}: {title}")
        
        try:
            # הוספת המסמך למאגר
            if context.user_data.get('document_type') == 'file':
                file = context.user_data['document_file']
                telegram_file = await file.get_file()
                file_path = f"downloads/{file.file_name}"
                await telegram_file.download_to_drive(file_path)
                
                await add_document_from_file(
                    file_path=file_path,
                    title=title,
                    user_id=user_id
                )
                
            else:  # text
                text = context.user_data['document_text']
                await add_document_from_file(
                    content=text,
                    title=title,
                    user_id=user_id
                )
            
            await update.message.reply_text(
                "✅ המסמך נוסף בהצלחה למאגר הידע!\n\n"
                "אתה יכול לחפש בו בעזרת הפקודה /search.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            await update.message.reply_text(
                "❌ אירעה שגיאה בהוספת המסמך. אנא נסה שוב.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        
        return ConversationHandler.END
    
    async def search_documents_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """התחלת תהליך חיפוש במסמכים"""
        user_id = update.effective_user.id
        logger.info(f"Search documents command from user {user_id}")
        
        await update.message.reply_text(
            "🔍 *חיפוש במאגר הידע*\n\n"
            "אנא הזן את מילות החיפוש שלך.\n"
            "אחפש במאגר המסמכים ואחזיר את התוצאות הרלוונטיות ביותר.\n\n"
            "לביטול החיפוש, הקלד /cancel.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return WAITING_FOR_SEARCH_QUERY
    
    async def search_documents_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """חיפוש במסמכים לפי שאילתה"""
        user_id = update.effective_user.id
        query = update.message.text
        
        logger.info(f"Search query from user {user_id}: {query}")
        
        # הודעת המתנה
        wait_message = await update.message.reply_text(
            "🔍 מחפש במאגר הידע... אנא המתן."
        )
        
        try:
            # חיפוש במאגר הידע
            results = await search_documents(query, limit=5, min_similarity=0.1)
            
            if not results:
                await wait_message.edit_text(
                    "❌ לא נמצאו תוצאות מתאימות לחיפוש שלך.\n\n"
                    "אנא נסה שוב עם מילות חיפוש אחרות.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return ConversationHandler.END
            
            # בניית הודעת תוצאות
            response = "🔍 *תוצאות החיפוש:*\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. *{result.title}*\n"
                response += f"רלוונטיות: {result.similarity:.0%}\n"
                response += f"קטע רלוונטי:\n{result.content[:200]}...\n\n"
            
            await wait_message.edit_text(
                response,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            await wait_message.edit_text(
                "❌ אירעה שגיאה בחיפוש. אנא נסה שוב.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        return ConversationHandler.END
    
    async def list_documents(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """הצגת רשימת המסמכים"""
        user_id = update.effective_user.id
        logger.info(f"List documents command from user {user_id}")
        
        try:
            async with db.get_session() as session:
                # קבלת כל המסמכים
                documents = await session.scalars(
                    db.select(Document)
                    .order_by(Document.created_at.desc())
                )
                documents = list(documents)
                
                if not documents:
                    await update.message.reply_text(
                        "📚 *מאגר הידע*\n\n"
                        "אין מסמכים במאגר כרגע.\n"
                        "אתה יכול להוסיף מסמך חדש בעזרת הפקודה /add_document.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # בניית הודעת רשימת מסמכים
                response = "📚 *מאגר הידע*\n\n"
                for i, doc in enumerate(documents, 1):
                    response += f"{i}. *{doc.title}*\n"
                    response += f"נוסף ב: {doc.created_at.strftime('%d/%m/%Y')}\n\n"
                
                await update.message.reply_text(
                    response,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            await update.message.reply_text(
                "❌ אירעה שגיאה בהצגת רשימת המסמכים. אנא נסה שוב.",
                parse_mode=ParseMode.MARKDOWN
            ) 