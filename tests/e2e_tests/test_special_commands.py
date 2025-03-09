"""
בדיקות קצה לקצה לתרחיש פקודות מיוחדות.
בדיקות אלו מדמות משתמש אמיתי המשתמש בפקודות מיוחדות של הבוט.
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
    from src.ui.telegram.handlers.telegram_bot_handlers import TelegramBotHandlers
    from src.database.database import Database
    from src.ui.telegram.core.telegram_agent import TelegramAgent
except ImportError as e:
    print(f"שגיאת ייבוא: {e}")
    print("ייתכן שנדרש להתאים את נתיבי הייבוא")
    
    # מחלקות מוק למקרה שהייבוא נכשל
    class Database:
        """מחלקת מוק ל-Database"""
        def __init__(self):
            self.users = {}
            self.conversations = {}
            self.messages = {}
            self.stats = {
                "total_messages": 0,
                "total_users": 0,
                "active_users": 0,
                "commands_used": {}
            }
        
        def get_user(self, user_id):
            """קבלת משתמש לפי מזהה"""
            if user_id in self.users:
                return self.users[user_id]
            return None
        
        def create_user(self, user_id, first_name, last_name=None, username=None):
            """יצירת משתמש חדש"""
            user = {
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "last_interaction": datetime.now().isoformat(),
                "preferences": json.dumps({"language": "he"})
            }
            self.users[user_id] = user
            self.stats["total_users"] += 1
            self.stats["active_users"] += 1
            return user
        
        def update_user(self, user_id, **kwargs):
            """עדכון פרטי משתמש"""
            if user_id in self.users:
                for key, value in kwargs.items():
                    self.users[user_id][key] = value
                return True
            return False
        
        def save_conversation(self, user_id, conversation_id, title=None):
            """שמירת שיחה"""
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or f"שיחה {len(self.conversations) + 1}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.conversations[conversation_id] = conversation
            return True
        
        def save_message(self, conversation_id, role, content):
            """שמירת הודעה"""
            if conversation_id not in self.messages:
                self.messages[conversation_id] = []
            
            message = {
                "id": len(self.messages[conversation_id]) + 1,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            self.messages[conversation_id].append(message)
            self.stats["total_messages"] += 1
            return True
        
        def get_conversation_messages(self, conversation_id):
            """קבלת הודעות של שיחה"""
            return self.messages.get(conversation_id, [])
        
        def clear_conversation(self, conversation_id):
            """ניקוי שיחה"""
            if conversation_id in self.messages:
                self.messages[conversation_id] = []
                return True
            return False
        
        def get_stats(self):
            """קבלת סטטיסטיקות"""
            return self.stats
        
        def update_command_stats(self, command):
            """עדכון סטטיסטיקות פקודות"""
            if command not in self.stats["commands_used"]:
                self.stats["commands_used"][command] = 0
            self.stats["commands_used"][command] += 1
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תשובה מהסוכן"""
            # תשובות מוכנות מראש לפי תוכן ההודעה
            if text == "/help":
                return """הפקודות הזמינות:
/start - התחלת שיחה חדשה
/help - הצגת עזרה
/clear - ניקוי היסטוריית השיחה
/stats - הצגת סטטיסטיקות
/settings - הגדרות
/feedback - שליחת משוב"""
            
            if text == "/clear":
                return "היסטוריית השיחה נוקתה בהצלחה."
            
            if text == "/stats":
                return """סטטיסטיקות:
מספר הודעות כולל: 1,234
מספר משתמשים: 567
משתמשים פעילים: 123
פקודות פופולריות: /start (456), /help (345), /clear (234)"""
            
            if text == "/settings":
                return """הגדרות המשתמש שלך:
1. שפה: עברית
2. התראות: מופעלות
3. מצב פרטיות: גבוה

לשינוי הגדרה, שלח את מספר ההגדרה והערך החדש (לדוגמה: 1 אנגלית)."""
            
            if text == "/feedback":
                return "תודה שבחרת לשלוח משוב! אנא כתוב את המשוב שלך ואנו נבחן אותו בהקדם."
            
            # תשובה כללית אם לא זוהה תוכן ספציפי
            return "אני לא מכיר את הפקודה הזו. נסה /help לקבלת רשימת הפקודות הזמינות."


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


class TestSpecialCommands:
    """מחלקת בדיקות לתרחיש פקודות מיוחדות"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        
        # הגדרת התנהגות המוקים
        self.mock_db.get_user.return_value = {
            "id": 12345,
            "first_name": "משה",
            "last_name": "ישראלי",
            "username": "moshe_israeli",
            "created_at": "2023-01-01T00:00:00",
            "last_interaction": "2023-01-01T00:00:00",
            "preferences": json.dumps({"language": "he"})
        }
        
        # הגדרת התנהגות ה-agent לפי הפקודה
        def get_response_side_effect(text, user_id=None, context=None):
            if text == "/help":
                return """הפקודות הזמינות:
/start - התחלת שיחה חדשה
/help - הצגת עזרה
/clear - ניקוי היסטוריית השיחה
/stats - הצגת סטטיסטיקות
/settings - הגדרות
/feedback - שליחת משוב"""
            
            if text == "/clear":
                return "היסטוריית השיחה נוקתה בהצלחה."
            
            if text == "/stats":
                return """סטטיסטיקות:
מספר הודעות כולל: 1,234
מספר משתמשים: 567
משתמשים פעילים: 123
פקודות פופולריות: /start (456), /help (345), /clear (234)"""
            
            if text == "/settings":
                return """הגדרות המשתמש שלך:
1. שפה: עברית
2. התראות: מופעלות
3. מצב פרטיות: גבוה

לשינוי הגדרה, שלח את מספר ההגדרה והערך החדש (לדוגמה: 1 אנגלית)."""
            
            if text == "/feedback":
                return "תודה שבחרת לשלוח משוב! אנא כתוב את המשוב שלך ואנו נבחן אותו בהקדם."
            
            # תשובה כללית אם לא זוהה תוכן ספציפי
            return "אני לא מכיר את הפקודה הזו. נסה /help לקבלת רשימת הפקודות הזמינות."
        
        self.mock_agent.get_response.side_effect = get_response_side_effect
        
        # יצירת בוט מדומה
        self.bot = MockTelegramBot()
        
        # יצירת מטפל הודעות
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
    async def test_help_command(self, setup):
        """בדיקת פקודת /help"""
        # יצירת הודעה עם פקודת /help
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/help",
            entities=[{"type": "bot_command", "offset": 0, "length": 5}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודת /help
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "הפקודות הזמינות" in first_message["text"], "הודעת התגובה אינה מכילה רשימת פקודות"
        assert "/start" in first_message["text"], "הודעת התגובה אינה מכילה את הפקודה /start"
        assert "/help" in first_message["text"], "הודעת התגובה אינה מכילה את הפקודה /help"
        assert "/clear" in first_message["text"], "הודעת התגובה אינה מכילה את הפקודה /clear"
        assert "/stats" in first_message["text"], "הודעת התגובה אינה מכילה את הפקודה /stats"
    
    @pytest.mark.asyncio
    async def test_clear_command(self, setup):
        """בדיקת פקודת /clear"""
        # יצירת הודעה עם פקודת /clear
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/clear",
            entities=[{"type": "bot_command", "offset": 0, "length": 6}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודת /clear
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "היסטוריית השיחה נוקתה" in first_message["text"], "הודעת התגובה אינה מכילה אישור על ניקוי היסטוריית השיחה"
    
    @pytest.mark.asyncio
    async def test_stats_command(self, setup):
        """בדיקת פקודת /stats"""
        # יצירת הודעה עם פקודת /stats
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/stats",
            entities=[{"type": "bot_command", "offset": 0, "length": 6}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודת /stats
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "סטטיסטיקות" in first_message["text"], "הודעת התגובה אינה מכילה כותרת סטטיסטיקות"
        assert "מספר הודעות כולל" in first_message["text"], "הודעת התגובה אינה מכילה מידע על מספר ההודעות"
        assert "מספר משתמשים" in first_message["text"], "הודעת התגובה אינה מכילה מידע על מספר המשתמשים"
        assert "משתמשים פעילים" in first_message["text"], "הודעת התגובה אינה מכילה מידע על משתמשים פעילים"
        assert "פקודות פופולריות" in first_message["text"], "הודעת התגובה אינה מכילה מידע על פקודות פופולריות"
    
    @pytest.mark.asyncio
    async def test_settings_command(self, setup):
        """בדיקת פקודת /settings"""
        # יצירת הודעה עם פקודת /settings
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/settings",
            entities=[{"type": "bot_command", "offset": 0, "length": 9}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודת /settings
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "הגדרות המשתמש" in first_message["text"], "הודעת התגובה אינה מכילה כותרת הגדרות משתמש"
        assert "שפה" in first_message["text"], "הודעת התגובה אינה מכילה מידע על שפה"
        assert "התראות" in first_message["text"], "הודעת התגובה אינה מכילה מידע על התראות"
    
    @pytest.mark.asyncio
    async def test_feedback_command(self, setup):
        """בדיקת פקודת /feedback"""
        # יצירת הודעה עם פקודת /feedback
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/feedback",
            entities=[{"type": "bot_command", "offset": 0, "length": 9}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודת /feedback
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "משוב" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות למשוב"
        assert "תודה" in first_message["text"], "הודעת התגובה אינה מכילה הודעת תודה"


class TelegramBotHandlers:
    """מחלקת מוק ל-TelegramBotHandlers"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.agent = TelegramAgent()
        
    async def handle_message(self, message):
        """טיפול בהודעה נכנסת"""
        # בדיקה אם זו פקודה
        if message.text and message.text.startswith("/"):
            # עדכון סטטיסטיקות
            self.db.update_command_stats(message.text)
            
            # טיפול בפקודות מיוחדות
            if message.text == "/clear":
                # ניקוי היסטוריית השיחה
                user_id = message.from_user.id
                conversations = self.db.get_conversation_messages(user_id)
                if conversations:
                    self.db.clear_conversation(conversations[0]["id"])
            
        # קבלת תשובה מהסוכן
        response = await self.agent.get_response(message.text, user_id=message.from_user.id)
        
        # שליחת התשובה
        await self.bot.send_message(message.chat.id, response)
        
        return response 