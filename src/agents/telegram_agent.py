"""
סוכן טלגרם המטפל בהודעות ופקודות
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
import logfire
from typing import Optional, Dict, Any, AsyncGenerator, List
import logging
import json
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.sql import select
from telegram import Update
from telegram.ext import ContextTypes

# הוספת נתיב הפרויקט ל-Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ייבוא מודולים מקומיים
from src.agents.core.model_manager import ModelManager
from src.agents.core.task_identifier import identify_task, get_task_specific_prompt
from src.tools.common_tools.context_manager import ConversationContext, understand_context
from src.agents.models.responses import ChatResponse, TaskIdentification, AgentContext
from src.database.database import db
from src.services.conversation_service import conversation_service, ConversationService
from src.services.memory_service import memory_service
from src.services.rag_service import rag_service
from src.services.learning_service import learning_service
from src.core.config import OPENAI_API_KEY
from src.database.models import User, Message

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
        self.context_manager = ConversationContext()
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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בהודעות רגילות
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        user = await self._get_or_create_user(update.message.from_user)
        message_text = update.message.text
        
        # זיהוי סוג המשימה
        task = await identify_task(message_text)
        
        # קבלת הקשר רלוונטי
        conversation = await self.conversation_service.get_conversation_context(
            user_id=user.id,
            query=message_text
        )
        
        # הבנת הקשר מההיסטוריה
        context_data = understand_context(
            message_text,
            conversation.get("recent_messages", []),
            self.context_manager
        )
        
        # קבלת תשובה מהמודל
        response = await self.model_manager.get_response(message_text, context_data)
        
        # שמירת ההודעה והתשובה
        await self._save_message(user.id, message_text, "user")
        await self._save_message(user.id, response, "assistant")
        
        # שליחת התשובה
        await self.stream_response(update, context, response)

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
        
        error_message = "מצטער, התרחשה שגיאה. אנא נסה שוב מאוחר יותר."
        if update:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
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
                text("SELECT * FROM users WHERE telegram_id = :telegram_id"),
                {"telegram_id": telegram_user.id}
            )
            user = user.fetchone()
            
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
            
            return User(**dict(user))

    async def _save_message(self, user_id: int, content: str, role: str) -> None:
        """
        שמירת הודעה
        
        Args:
            user_id: מזהה המשתמש
            content: תוכן ההודעה
            role: תפקיד השולח
        """
        async with db.get_session() as session:
            message = Message(
                user_id=user_id,
                content=content,
                role=role
            )
            session.add(message)
            await session.commit()

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
