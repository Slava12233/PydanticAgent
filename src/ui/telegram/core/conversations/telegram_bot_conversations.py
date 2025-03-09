import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from ..telegram_agent import TelegramAgent
from src.database.database import db
from src.models.database import User, Conversation, Message
from src.services.database.users import UserManager
from src.utils.logger import setup_logger, log_telegram_message

# Configure logging
logger = setup_logger('telegram_bot_conversations')

# מצבי שיחה
(
    WAITING_FOR_DOCUMENT,
    WAITING_FOR_TITLE,
    WAITING_FOR_SEARCH_QUERY,
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
    WAITING_FOR_ORDER_ACTION,
    WAITING_FOR_ORDER_ID,
    WAITING_FOR_ORDER_STATUS,
    WAITING_FOR_CANCEL_REASON,
    WAITING_FOR_REFUND_AMOUNT,
    WAITING_FOR_REFUND_REASON,
    WAITING_FOR_FILTER_CRITERIA
) = range(21)

class TelegramBotConversations:
    """
    מחלקה לניהול שיחות ותהליכים מורכבים בבוט
    """
    
    def __init__(self, bot):
        """
        אתחול המחלקה
        
        Args:
            bot: הבוט הראשי
        """
        self.bot = bot
        self.agent = TelegramAgent()
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """
        עיבוד הודעה רגילה והפקת תשובה מהסוכן
        
        Args:
            update: אובייקט העדכון מטלגרם
            context: הקונטקסט של השיחה
            
        Returns:
            תשובת הסוכן או None אם אין תשובה
        """
        if not update.message or not update.message.text:
            return None
            
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        logger.info(f"Processing message from user {user_id}: {message_text}")
        
        # שמירת ההודעה במסד הנתונים
        async with db.get_session() as session:
            user = await UserManager.get_user_by_telegram_id(user_id, session)
            if not user:
                logger.warning(f"User {user_id} not found in database")
                return "אירעה שגיאה. אנא נסה להתחיל מחדש עם /start"
            
            conversation = await session.scalar(
                db.select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.created_at.desc())
            )
            
            if not conversation:
                conversation = Conversation(user_id=user.id)
                session.add(conversation)
                await session.commit()
            
            # שמירת ההודעה
            message = Message(
                user_id=user.id,
                conversation_id=conversation.id,
                content=message_text,
                direction='incoming'
            )
            session.add(message)
            await session.commit()
        
        # קבלת תשובה מהסוכן
        try:
            response = await self.agent.process_message(
                user_id=user_id,
                message=message_text,
                conversation_id=conversation.id
            )
            
            if response:
                # שמירת התשובה במסד הנתונים
                async with db.get_session() as session:
                    bot_message = Message(
                        user_id=user.id,
                        conversation_id=conversation.id,
                        content=response,
                        direction='outgoing'
                    )
                    session.add(bot_message)
                    await session.commit()
                
                return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב."
        
        return None
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        ביטול שיחה נוכחית
        
        Args:
            update: אובייקט העדכון מטלגרם
            context: הקונטקסט של השיחה
            
        Returns:
            ConversationHandler.END
        """
        user_id = update.effective_user.id
        logger.info(f"Canceling conversation for user {user_id}")
        
        # ניקוי נתוני הקונטקסט
        context.user_data.clear()
        
        await update.message.reply_text(
            "השיחה בוטלה. אתה יכול להתחיל שיחה חדשה או להשתמש בפקודות הזמינות.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END 