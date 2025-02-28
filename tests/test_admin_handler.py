"""
בדיקות למודול admin_handler
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from telegram import Update, User, Message, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.models import UserRole
from src.handlers.admin_handler import (
    is_admin, 
    admin_required, 
    handle_admin_command,
    handle_admin_users,
    handle_admin_stats,
    handle_admin_docs,
    handle_admin_models,
    handle_admin_config,
    handle_admin_notify,
    handle_admin_callback
)

class TestAdminHandler(unittest.TestCase):
    """בדיקות למודול admin_handler"""
    
    def setUp(self):
        """הכנה לפני כל בדיקה"""
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
        self.update.effective_message = self.message
        
        # יצירת אובייקט Context מוק
        self.context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.bot = MagicMock()
        self.context.bot.send_message = AsyncMock()
        self.context.user_data = {}
        
        # יצירת מוק לסשן מסד נתונים
        self.session = MagicMock()
        
        # מוק למשתמש מנהל
        self.admin_user = MagicMock()
        self.admin_user.role = UserRole.ADMIN
        
        # מוק למשתמש רגיל
        self.regular_user = MagicMock()
        self.regular_user.role = UserRole.USER
    
    @patch('src.handlers.admin_handler.get_user_by_telegram_id')
    async def test_is_admin_with_admin_user(self, mock_get_user):
        """בדיקה שפונקציית is_admin מחזירה True למשתמש מנהל"""
        # הגדרת התנהגות המוק
        mock_get_user.return_value = self.admin_user
        
        # הפעלת הפונקציה
        result = await is_admin(self.user.id, self.session)
        
        # בדיקת התוצאה
        self.assertTrue(result)
        mock_get_user.assert_called_once_with(self.user.id, self.session)
    
    @patch('src.handlers.admin_handler.get_user_by_telegram_id')
    async def test_is_admin_with_regular_user(self, mock_get_user):
        """בדיקה שפונקציית is_admin מחזירה False למשתמש רגיל"""
        # הגדרת התנהגות המוק
        mock_get_user.return_value = self.regular_user
        
        # הפעלת הפונקציה
        result = await is_admin(self.user.id, self.session)
        
        # בדיקת התוצאה
        self.assertFalse(result)
        mock_get_user.assert_called_once_with(self.user.id, self.session)
    
    @patch('src.handlers.admin_handler.is_admin')
    async def test_admin_required_with_admin_user(self, mock_is_admin):
        """בדיקה שפונקציית admin_required מחזירה True למשתמש מנהל"""
        # הגדרת התנהגות המוק
        mock_is_admin.return_value = True
        
        # הפעלת הפונקציה
        result = await admin_required(self.update, self.context, self.session)
        
        # בדיקת התוצאה
        self.assertTrue(result)
        mock_is_admin.assert_called_once_with(self.user.id, self.session)
        self.message.reply_text.assert_not_called()
    
    @patch('src.handlers.admin_handler.is_admin')
    async def test_admin_required_with_regular_user(self, mock_is_admin):
        """בדיקה שפונקציית admin_required מחזירה False למשתמש רגיל ושולחת הודעת שגיאה"""
        # הגדרת התנהגות המוק
        mock_is_admin.return_value = False
        
        # הפעלת הפונקציה
        result = await admin_required(self.update, self.context, self.session)
        
        # בדיקת התוצאה
        self.assertFalse(result)
        mock_is_admin.assert_called_once_with(self.user.id, self.session)
        self.message.reply_text.assert_called_once()
        # בדיקה שהודעת השגיאה מכילה את המילה "הרשאות"
        self.assertIn("הרשאות", self.message.reply_text.call_args[0][0])
    
    @patch('src.handlers.admin_handler.admin_required')
    async def test_handle_admin_command(self, mock_admin_required):
        """בדיקת פונקציית handle_admin_command"""
        # הגדרת התנהגות המוק
        mock_admin_required.return_value = True
        
        # הפעלת הפונקציה
        await handle_admin_command(self.update, self.context, self.session)
        
        # בדיקת התוצאה
        mock_admin_required.assert_called_once_with(self.update, self.context, self.session)
        self.message.reply_text.assert_called_once()
        # בדיקה שהפרמטר reply_markup הוא מסוג InlineKeyboardMarkup
        self.assertIsInstance(self.message.reply_text.call_args[1]['reply_markup'], InlineKeyboardMarkup)
    
    @patch('src.handlers.admin_handler.admin_required')
    async def test_handle_admin_command_not_admin(self, mock_admin_required):
        """בדיקת פונקציית handle_admin_command כאשר המשתמש אינו מנהל"""
        # הגדרת התנהגות המוק
        mock_admin_required.return_value = False
        
        # הפעלת הפונקציה
        await handle_admin_command(self.update, self.context, self.session)
        
        # בדיקת התוצאה
        mock_admin_required.assert_called_once_with(self.update, self.context, self.session)
        # בדיקה שלא נשלחה הודעה נוספת (מעבר להודעת השגיאה שנשלחת בתוך admin_required)
        self.message.reply_text.assert_not_called()

if __name__ == '__main__':
    unittest.main() 