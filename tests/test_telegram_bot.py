"""
בדיקות למודול telegram_bot
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import tempfile
import asyncio

from telegram import Update, User, Message, Document, Chat
from telegram.ext import ContextTypes

from src.bots.telegram_bot import TelegramBot, WAITING_FOR_DOCUMENT, WAITING_FOR_TITLE

class TestTelegramBot(unittest.TestCase):
    """בדיקות למודול telegram_bot"""
    
    def setUp(self):
        """הכנה לפני כל בדיקה"""
        # יצירת מופע של הבוט
        self.bot = TelegramBot()
        
        # יצירת אובייקטי מוק לטלגרם
        self.user = MagicMock(spec=User)
        self.user.id = 12345
        self.user.first_name = "Test"
        self.user.username = "test_user"
        
        self.chat = MagicMock(spec=Chat)
        self.chat.id = 12345
        
        self.message = MagicMock(spec=Message)
        self.message.message_id = 1
        self.message.chat = self.chat
        self.message.from_user = self.user
        self.message.text = "test message"
        self.message.reply_text = AsyncMock()
        
        # יצירת אובייקט Update מוק
        self.update = MagicMock(spec=Update)
        self.update.message = self.message
        self.update.effective_chat = self.chat
        self.update.effective_user = self.user
        
        # יצירת אובייקט Context מוק
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.bot = MagicMock()
        self.context.bot.send_message = AsyncMock()
        self.context.user_data = {}
    
    async def test_list_documents(self):
        """בדיקת פונקציית list_documents"""
        # הפעלת הפונקציה
        await self.bot.list_documents(self.update, self.context)
        
        # בדיקה שהפונקציה שלחה הודעה
        self.message.reply_text.assert_called_once()
        
        # בדיקה שההודעה מכילה את המילה "מסמכים"
        call_args = self.message.reply_text.call_args[0][0]
        self.assertIn("מסמכים", call_args)
    
    def test_list_documents_sync(self):
        """בדיקת פונקציית list_documents בצורה סינכרונית"""
        # הפעלת הפונקציה האסינכרונית בצורה סינכרונית
        asyncio.run(self.test_list_documents()) 