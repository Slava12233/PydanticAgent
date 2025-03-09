"""
סוכן טלגרם המטפל בהודעות ופקודות
"""

import asyncio
import logging
import os
import sys
import traceback
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union, AsyncGenerator

import logfire
from openai import AsyncOpenAI
from sqlalchemy import text, select
from telegram import Update
from telegram.ext import ContextTypes

# הוספת נתיב הפרויקט ל-Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ייבוא מודולים מקומיים
from src.core.model_manager import ModelManager
from src.core.task_identification import identify_task, get_task_specific_prompt
from src.services.ai.context_service import context_service
from src.models.responses import ChatResponse, TaskIdentification, create_error_response
from src.database.database import db
from src.services.ai.conversation_service import conversation_service, ConversationService
from src.services.ai.memory_service import memory_service
from src.services.ai import (
    rag_search, 
    rag_document, 
    search_documents
)
from src.core.config import OPENAI_API_KEY
from src.models.database import User, Message, Conversation

# הגדרת פרויקט logfire מראש
if 'LOGFIRE_PROJECT' not in os.environ:
    os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'

logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')

logger = logging.getLogger(__name__)

class TelegramAgent:
    """סוכן טלגרם המטפל בהודעות ופקודות"""

    def __init__(self):
        """אתחול הסוכן"""
        self.model_manager = ModelManager()
        self.conversation_service = ConversationService()
        self.context_service = context_service
        logging.info("telegram_agent_initialized")

    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בפקודות
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        command = update.message.text.split()[0]
        user = await self._get_or_create_user(update.message.from_user)
        
        if command == "/start":
            await self._handle_start_command(update, context, user)
        elif command == "/help":
            await self._handle_help_command(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="פקודה לא מוכרת. נסה /help לקבלת עזרה"
            )

    async def handle_message(self, user_id: int, message_text: str, conversation_id: int) -> str:
        """
        טיפול בהודעות רגילות
        
        Args:
            user_id: מזהה המשתמש בטלגרם
            message_text: תוכן ההודעה
            conversation_id: מזהה השיחה
            
        Returns:
            תשובת המערכת
        """
        try:
            # קבלת המשתמש לפי מזהה טלגרם
            async with db.get_session() as session:
                user_query = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = user_query.scalars().first()
                
                if not user:
                    logger.error(f"לא נמצא משתמש עם telegram_id {user_id}")
                    return "אירעה שגיאה בקבלת פרטי המשתמש. אנא נסה שוב מאוחר יותר."
            
            # שמירת הודעת המשתמש בהקשר לפני שליחתה למודל
            await self.context_service.process_message(
                message=message_text,
                role="user",
                conversation_id=conversation_id
            )
            
            # קבלת זיכרונות רלוונטיים מהשיחה
            relevant_memories = await self.context_service._get_relevant_memories(
                query=message_text,
                limit=10,  # הגדלנו את מספר הזיכרונות שנשלפים
                min_similarity=0.0,  # הורדנו את סף הדמיון המינימלי
                conversation_id=conversation_id
            )
            
            # קבלת תשובה מהמודל
            response = await self.model_manager.get_response(
                message=message_text,
                context={"memories": relevant_memories}
            )
            
            # שמירת התשובה בהקשר
            await self.context_service.process_message(
                message=response,
                role="assistant",
                conversation_id=conversation_id
            )
            
            # שמירת ההודעה והתשובה במסד הנתונים
            await self._save_message(user_id, message_text, response, conversation_id)
            
            return response
            
        except Exception as e:
            error_message = f"אירעה שגיאה בעיבוד ההודעה: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            logfire.error("telegram_agent_error", error=str(e))
            return "מצטער, אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב."

    async def handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בהודעות מדיה
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        user = await self._get_or_create_user(update.message.from_user)
        
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            
            # שמירת התמונה
            photo_file = await context.bot.get_file(file_id)
            await photo_file.download_to_drive(f"media/{file_id}.jpg")
            
            # טיפול בכיתוב
            if caption:
                await self.handle_message(update, context)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="קיבלתי את התמונה. האם תרצה להוסיף תיאור?"
                )

    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
        """
        טיפול בשגיאות
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
            error: השגיאה שהתרחשה
        """
        logging.error(f"Error: {str(error)}")
        
        error_response = create_error_response(
            message="מצטער, התרחשה שגיאה. אנא נסה שוב מאוחר יותר.",
            error_code="TELEGRAM_ERROR",
            error_details=str(error)
        )
        
        if update:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_response.message
            )

    async def handle_callback_query(self, callback_query: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בכפתורים
        
        Args:
            callback_query: שאילתת הכפתור
            context: הקשר השיחה
        """
        query = callback_query.callback_query
        user = await self._get_or_create_user(query.from_user)
        
        # טיפול בפעולת הכפתור
        action = query.data
        if action.startswith("confirm_"):
            await self._handle_confirmation(query, context)
        elif action.startswith("cancel_"):
            await self._handle_cancellation(query, context)
        
        # עדכון הכפתור
        await query.answer()

    async def format_response(self, response: str) -> str:
        """
        פורמט תשובה לשליחה
        
        Args:
            response: התשובה המקורית
            
        Returns:
            התשובה מפורמטת
        """
        # הגבלת אורך ההודעה
        if len(response) > 4096:
            response = response[:4093] + "..."
        
        return response

    async def stream_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, response: str) -> None:
        """
        הזרמת תשובה למשתמש
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
            response: התשובה להזרמה
        """
        formatted_response = await self.format_response(response)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=formatted_response
        )

    async def _get_or_create_user(self, telegram_user: Any) -> User:
        """
        קבלת או יצירת משתמש
        
        Args:
            telegram_user: משתמש טלגרם
            
        Returns:
            אובייקט המשתמש
        """
        async with db.get_session() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == telegram_user.id)
            )
            user = user.scalars().first()
            
            if not user:
                new_user = User(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name
                )
                session.add(new_user)
                await session.commit()
                return new_user
            
            return user

    async def _save_message(self, user_id: int, message_text: str, response: str, conversation_id: int) -> None:
        """
        שמירת הודעה
        
        Args:
            user_id: מזהה המשתמש (telegram_id)
            message_text: תוכן ההודעה
            response: תשובת המערכת
            conversation_id: מזהה השיחה
        """
        try:
            # קבלת מזהה המשתמש הפנימי לפי telegram_id
            async with db.get_session() as session:
                user = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = user.scalars().first()
                
                if not user:
                    logger.error(f"לא נמצא משתמש עם telegram_id {user_id}")
                    return
                
                # שמירת ההודעה עם מזהה המשתמש הפנימי
                message = Message(
                    user_id=user.id,  # משתמשים במזהה הפנימי
                    content=message_text,
                    response=response,
                    conversation_id=conversation_id,
                    role="user"
                )
                session.add(message)
                await session.commit()
                
        except Exception as e:
            logger.error(f"שגיאה בשמירת הודעה: {str(e)}")
            logfire.error("message_save_error", error=str(e))

    async def _handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
        """
        טיפול בפקודת start
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
            user: המשתמש
        """
        welcome_message = f"שלום {user.first_name}! אני כאן כדי לעזור לך. במה אוכל לסייע?"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_message
        )

    async def _handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בפקודת help
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        help_message = """
        אני יכול לעזור לך במגוון נושאים:
        - ניהול מסמכים ומידע
        - ניהול חנות מקוונת
        - ניתוח נתונים ומכירות
        - פתרון בעיות טכניות
        - שיווק ופרסום
        
        פשוט שאל אותי כל שאלה ואשמח לעזור!
        """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_message
        )

    async def _handle_confirmation(self, query: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול באישור פעולה
        
        Args:
            query: שאילתת הכפתור
            context: הקשר השיחה
        """
        action_id = query.data.split("_")[1]
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"הפעולה {action_id} אושרה ✅"
        )

    async def _handle_cancellation(self, query: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בביטול פעולה
        
        Args:
            query: שאילתת הכפתור
            context: הקשר השיחה
        """
        action_id = query.data.split("_")[1]
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"הפעולה {action_id} בוטלה ❌"
        )

async def get_or_create_conversation(user_id: int) -> Conversation:
    """
    קבלת או יצירת שיחה
    
    Args:
        user_id: מזהה המשתמש
    
    Returns:
        שיחה
    """
    async with db.get_session() as session:
        conversation = await session.execute(
            select(Conversation).where(Conversation.user_id == user_id)
        )
        conversation = conversation.scalars().first()
        
        if not conversation:
            new_conversation = Conversation(
                user_id=user_id
            )
            session.add(new_conversation)
            await session.commit()
            return new_conversation
        
        return conversation
