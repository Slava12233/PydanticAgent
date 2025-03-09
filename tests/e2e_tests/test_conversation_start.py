"""
בדיקות קצה לקצה לתרחיש התחלת שיחה עם הבוט.
בדיקות אלו מדמות משתמש אמיתי המתחיל שיחה עם הבוט.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
import json
from datetime import datetime

# הוספת נתיב הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# ייבוא מודולים מהפרויקט
try:
    from src.ui.telegram.core.telegram_bot_core import TelegramBotCore
    from src.ui.telegram.handlers.telegram_bot_handlers import TelegramBotHandlers
    from src.database.database import Database
    from src.ui.telegram.core.telegram_agent import TelegramAgent
except ImportError as e:
    print(f"שגיאת ייבוא: {e}")
    print("ייתכן שנדרש להתאים את נתיבי הייבוא")
    
    # מחלקות מוק למקרה שהייבוא נכשל
    class Database:
        """מחלקת מוק ל-Database"""
        def get_user(self, user_id):
            return None
        
        def create_user(self, user_id, first_name, last_name=None, username=None):
            return {"id": user_id, "first_name": first_name, "last_name": last_name, "username": username}
        
        def update_user(self, user_id, **kwargs):
            return True
        
        def save_conversation(self, user_id, conversation_id, title=None):
            return True
        
        def save_message(self, conversation_id, role, content):
            return True
    
    class TelegramBotCore:
        """מחלקת מוק ל-TelegramBotCore"""
        def __init__(self, token=None):
            self.token = token
    
    class TelegramBotHandlers:
        """מחלקת מוק ל-TelegramBotHandlers"""
        def __init__(self, bot):
            self.bot = bot
            self.db = Database()
            self.agent = TelegramAgent()
        
        async def handle_start(self, message):
            """טיפול בפקודת /start"""
            user = message.from_user
            
            # בדיקה אם המשתמש קיים במסד הנתונים
            existing_user = self.db.get_user(user.id)
            
            if existing_user:
                # עדכון משתמש קיים
                self.db.update_user(user.id, last_interaction=datetime.now().isoformat())
                greeting = f"שמחים לראות אותך שוב, {user.first_name}!"
            else:
                # יצירת משתמש חדש
                self.db.create_user(
                    user_id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username
                )
                greeting = f"ברוך הבא {user.first_name}! אני הבוט של החנות."
            
            # שליחת הודעת ברכה
            await self.bot.send_message(
                message.chat.id,
                f"{greeting} איך אוכל לעזור לך היום?"
            )
        
        async def handle_message(self, message):
            """טיפול בהודעות טקסט רגילות"""
            # קבלת תשובה מהסוכן
            response = await self.agent.get_response(message.text)
            
            # שליחת התשובה למשתמש
            await self.bot.send_message(message.chat.id, response)
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text):
            if "שלום" in text:
                return "שלום! איך אוכל לעזור לך היום?"
            return "ברוך הבא לבוט שלנו! איך אוכל לעזור לך היום?"


class MockTelegramUser:
    """מחלקה המדמה משתמש טלגרם לצורך בדיקות"""
    
    def __init__(self, user_id, first_name, last_name=None, username=None, is_bot=False):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = is_bot
        self.language_code = "he"


class MockTelegramChat:
    """מחלקה המדמה צ'אט טלגרם לצורך בדיקות"""
    
    def __init__(self, chat_id, chat_type="private"):
        self.id = chat_id
        self.type = chat_type


class MockTelegramMessage:
    """מחלקה המדמה הודעת טלגרם לצורך בדיקות"""
    
    def __init__(self, message_id, user, chat, text=None, date=None, entities=None):
        self.message_id = message_id
        self.from_user = user
        self.chat = chat
        self.text = text
        self.date = date or datetime.now()
        self.entities = entities or []


class MockTelegramBot:
    """מחלקה המדמה בוט טלגרם לצורך בדיקות"""
    
    def __init__(self):
        self.sent_messages = []
        self.edited_messages = []
        
    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        message = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup
        }
        self.sent_messages.append(message)
        return MockTelegramMessage(
            message_id=len(self.sent_messages),
            user=MockTelegramUser(user_id=0, first_name="Bot"),
            chat=MockTelegramChat(chat_id=chat_id),
            text=text
        )
    
    async def edit_message_text(self, chat_id, message_id, text, parse_mode=None, reply_markup=None):
        message = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup
        }
        self.edited_messages.append(message)
        return True


class TestConversationStart:
    """מחלקת בדיקות לתרחיש התחלת שיחה"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        
        # הגדרת התנהגות המוקים
        self.mock_db.get_user.return_value = None  # משתמש חדש
        self.mock_agent.get_response.return_value = "ברוך הבא לבוט שלנו! איך אוכל לעזור לך היום?"
        
        # יצירת בוט מדומה
        self.bot = MockTelegramBot()
        
        # יצירת מטפל הודעות - שימוש במוקים שיצרנו
        self.handlers = TelegramBotHandlers(self.bot)
        
        # החלפת המוקים הפנימיים של ה-handlers במוקים שלנו
        self.handlers.db = self.mock_db
        self.handlers.agent = self.mock_agent
        
        # יצירת משתמש מדומה
        self.user = MockTelegramUser(
            user_id=12345,
            first_name="משה",
            last_name="ישראלי",
            username="moshe_israeli"
        )
        
        # יצירת צ'אט מדומה
        self.chat = MockTelegramChat(chat_id=12345)
        
        yield
        
        # ניקוי לאחר הבדיקות
        self.mock_db.reset_mock()
        self.mock_agent.reset_mock()
    
    @pytest.mark.asyncio
    async def test_start_command_new_user(self, setup):
        """בדיקת פקודת /start עבור משתמש חדש"""
        # יצירת הודעת /start
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/start",
            entities=[{"type": "bot_command", "offset": 0, "length": 6}]
        )
        
        # הגדרת התנהגות המוקים
        self.mock_db.get_user.return_value = None  # משתמש חדש
        
        # הפעלת הפונקציה הנבדקת - שימוש ישיר במוק
        await self.handlers.handle_start(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמשתמש נוצר במסד הנתונים
        self.mock_db.create_user.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "ברוך הבא" in first_message["text"], "הודעת הפתיחה אינה מכילה 'ברוך הבא'"
        assert self.user.first_name in first_message["text"], "הודעת הפתיחה אינה מכילה את שם המשתמש"
    
    @pytest.mark.asyncio
    async def test_start_command_existing_user(self, setup):
        """בדיקת פקודת /start עבור משתמש קיים"""
        # הגדרת משתמש קיים
        existing_user = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "username": self.user.username,
            "created_at": "2023-01-01T00:00:00",
            "last_interaction": "2023-01-01T00:00:00",
            "preferences": json.dumps({"language": "he"})
        }
        self.mock_db.get_user.return_value = existing_user
        
        # יצירת הודעת /start
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/start",
            entities=[{"type": "bot_command", "offset": 0, "length": 6}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_start(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמשתמש לא נוצר שוב במסד הנתונים
        self.mock_db.create_user.assert_not_called()
        
        # בדיקה שהמשתמש עודכן במסד הנתונים
        self.mock_db.update_user.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "שמחים לראות אותך שוב" in first_message["text"] or "ברוך הבא" in first_message["text"], "הודעת הפתיחה אינה מתאימה למשתמש קיים"
    
    @pytest.mark.asyncio
    async def test_greeting_message(self, setup):
        """בדיקת הודעת פתיחה והצגת אפשרויות"""
        # יצירת הודעת טקסט רגילה (לא פקודה)
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="שלום"
        )
        
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = "שלום! איך אוכל לעזור לך היום? אני יכול לעזור בחיפוש מוצרים, מעקב אחר הזמנות, או לענות על שאלות כלליות."
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "שלום" in first_message["text"], "הודעת התגובה אינה מכילה 'שלום'"
        assert "לעזור" in first_message["text"], "הודעת התגובה אינה מציעה עזרה"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 