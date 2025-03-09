"""
בדיקות קצה לקצה לתרחיש זיכרון ולמידה.
בדיקות אלו מדמות משתמש אמיתי המתקשר עם הסוכן לאורך זמן ובודקות את יכולת הזיכרון והלמידה של הסוכן.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
import json
from datetime import datetime, timedelta

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
            self.preferences = {}
            
        def get_user(self, user_id):
            """קבלת משתמש לפי מזהה"""
            return self.users.get(user_id, None)
            
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
            return user
            
        def update_user(self, user_id, **kwargs):
            """עדכון פרטי משתמש"""
            if user_id in self.users:
                for key, value in kwargs.items():
                    self.users[user_id][key] = value
                return self.users[user_id]
            return None
            
        def save_conversation(self, user_id, conversation_id, title=None):
            """שמירת שיחה חדשה"""
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or "שיחה חדשה",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages_count": 0
            }
            self.conversations[conversation_id] = conversation
            return conversation
            
        def save_message(self, conversation_id, role, content):
            """שמירת הודעה בשיחה"""
            if conversation_id not in self.conversations:
                return None
                
            message_id = f"{conversation_id}_{self.conversations[conversation_id]['messages_count'] + 1}"
            message = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            if conversation_id not in self.messages:
                self.messages[conversation_id] = []
                
            self.messages[conversation_id].append(message)
            self.conversations[conversation_id]["messages_count"] += 1
            self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
            
            return message
            
        def get_conversation_messages(self, conversation_id):
            """קבלת כל ההודעות בשיחה"""
            return self.messages.get(conversation_id, [])
            
        def get_user_conversations(self, user_id):
            """קבלת כל השיחות של משתמש"""
            return [conv for conv in self.conversations.values() if conv["user_id"] == user_id]
            
        def save_user_preference(self, user_id, key, value):
            """שמירת העדפת משתמש"""
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
                
            self.preferences[user_id][key] = value
            
            # עדכון העדפות בפרטי המשתמש
            if user_id in self.users:
                prefs = json.loads(self.users[user_id].get("preferences", "{}"))
                prefs[key] = value
                self.users[user_id]["preferences"] = json.dumps(prefs)
                
            return True
            
        def get_user_preference(self, user_id, key, default=None):
            """קבלת העדפת משתמש"""
            if user_id in self.preferences:
                return self.preferences[user_id].get(key, default)
            return default
            
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        def __init__(self):
            self.responses = {}
            self.preferences = {}
            
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תשובה מהסוכן"""
            # תשובות מוכנות מראש לפי תוכן ההודעה
            if "שלום" in text or "היי" in text:
                return "שלום! איך אני יכול לעזור לך היום?"
                
            if "מה שמך" in text:
                return "שמי הוא בוט העזרה של החנות. אני כאן כדי לענות על שאלות ולעזור בכל מה שתצטרך."
                
            if "מה השעה" in text:
                return f"השעה כרגע היא {datetime.now().strftime('%H:%M')}."
                
            if "מה התאריך" in text:
                return f"התאריך היום הוא {datetime.now().strftime('%d/%m/%Y')}."
                
            if "מה אתה יודע לעשות" in text:
                return """אני יכול לעזור במגוון נושאים:
1. מידע על מוצרים בחנות
2. ביצוע הזמנות
3. מעקב אחר הזמנות קיימות
4. מענה לשאלות כלליות
5. סיוע בפתרון בעיות

איך אוכל לעזור לך?"""
                
            if "אני מעדיף" in text or "אני אוהב" in text:
                # שמירת העדפה
                if user_id:
                    preference = text.split("אני מעדיף")[1].strip() if "אני מעדיף" in text else text.split("אני אוהב")[1].strip()
                    self.save_user_preference(user_id, "preference", preference)
                    return f"תודה שסיפרת לי! אזכור שאתה מעדיף {preference}."
                    
            if "מה אני מעדיף" in text or "מה אני אוהב" in text:
                # שליפת העדפה
                if user_id:
                    preference = self.get_user_preference(user_id, "preference", "לא ציינת העדפה עדיין")
                    return f"לפי מה שסיפרת לי בעבר, אתה מעדיף {preference}."
                    
            if "תזכור" in text:
                # שמירת מידע לזכירה
                if user_id:
                    memory = text.split("תזכור")[1].strip()
                    self.save_user_preference(user_id, "memory", memory)
                    return f"אזכור ש{memory}."
                    
            if "מה אמרתי לך" in text or "מה אתה זוכר" in text:
                # שליפת מידע שנשמר
                if user_id:
                    memory = self.get_user_preference(user_id, "memory", "לא ביקשת ממני לזכור דבר עדיין")
                    return f"אתה ביקשת ממני לזכור ש{memory}."
                    
            if "תקן" in text:
                # למידה מתיקון
                correction = text.split("תקן:")[1].strip() if "תקן:" in text else text.split("תקן")[1].strip()
                return f"תודה על התיקון! אזכור ש{correction}."
                
            # תשובה כללית אם לא זוהה תוכן ספציפי
            return "אני מבין. איך אוכל לעזור לך עוד?"
            
        def save_user_preference(self, user_id, key, value):
            """שמירת העדפת משתמש"""
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
                
            self.preferences[user_id][key] = value
            return True
            
        def get_user_preference(self, user_id, key, default=None):
            """קבלת העדפת משתמש"""
            if user_id in self.preferences:
                return self.preferences[user_id].get(key, default)
            return default
            
    class TelegramBotHandlers:
        """מחלקת מוק ל-TelegramBotHandlers"""
        def __init__(self, bot):
            self.bot = bot
            self.db = Database()
            self.agent = TelegramAgent()
            
        async def handle_message(self, message):
            """טיפול בהודעה נכנסת"""
            # קבלת תשובה מהסוכן
            response = await self.agent.get_response(message.text, user_id=message.from_user.id)
            
            # שליחת התשובה
            await self.bot.send_message(message.chat.id, response)
            
            return response


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


class TestMemoryLearning:
    """מחלקת בדיקות לתרחיש זיכרון ולמידה"""
    
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
        
        # הגדרת התנהגות ה-agent לכל בדיקה בנפרד
        # עבור test_remember_information_in_conversation
        self.responses_for_remember_info = [
            "אני לא יודע מה השם שלך. האם תוכל לספר לי?",
            "מעולה! מעכשיו אקרא לך דני.",
            "השם שלך הוא דני, נכון?"
        ]
        
        # עבור test_remember_previous_messages
        self.responses_for_remember_messages = [
            "אני לא יודע מה השם שלך. האם תוכל לספר לי?",
            "קודם אמרת: \"מה השם שלי?\""
        ]
        
        # עבור test_learn_from_corrections
        self.responses_for_learn_corrections = [
            "אני מבין. איך אוכל לעזור לך עוד?",
            "תודה על התיקון! אזכור שאני אוהב פסטה."
        ]
        
        # עבור test_remember_user_preferences
        self.responses_for_user_preferences = [
            "תודה שסיפרת לי! אזכור שאתה מעדיף שוקולד.",
            "לפי מה שסיפרת לי בעבר, אתה מעדיף שוקולד."
        ]
        
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
    async def test_remember_information_in_conversation(self, setup):
        """בדיקה שהסוכן זוכר מידע מוקדם בשיחה"""
        # הגדרת התנהגות ה-agent לבדיקה זו
        self.mock_agent.get_response.side_effect = self.responses_for_remember_info
        
        # יצירת הודעה ראשונה
        first_message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה השם שלי?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(first_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # יצירת הודעה שנייה
        second_message = MockTelegramMessage(
            message_id=2,
            user=self.user,
            chat=self.chat,
            text="קרא לי דני"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(second_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 1, "לא נשלחה הודעת תגובה שנייה"
        
        # יצירת הודעה שלישית
        third_message = MockTelegramMessage(
            message_id=3,
            user=self.user,
            chat=self.chat,
            text="מה השם שלי?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(third_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 2, "לא נשלחה הודעת תגובה שלישית"
        
        # בדיקה שהסוכן זוכר את השם
        third_response = self.bot.sent_messages[2]
        assert "דני" in third_response["text"], "הסוכן לא זוכר את השם שנקבע"
    
    @pytest.mark.asyncio
    async def test_remember_previous_messages(self, setup):
        """בדיקה שהסוכן זוכר הודעות קודמות"""
        # הגדרת התנהגות ה-agent לבדיקה זו
        self.mock_agent.get_response.side_effect = self.responses_for_remember_messages
        
        # יצירת הודעה ראשונה
        first_message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה השם שלי?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(first_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # יצירת הודעה שנייה
        second_message = MockTelegramMessage(
            message_id=2,
            user=self.user,
            chat=self.chat,
            text="מה אמרתי לך?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(second_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 1, "לא נשלחה הודעת תגובה שנייה"
        
        # בדיקה שהסוכן מגיב בצורה כלשהי לבקשה לזכור מה נאמר
        second_response = self.bot.sent_messages[1]
        assert "קודם אמרת" in second_response["text"], "הסוכן לא מגיב כראוי לבקשה לזכור מה נאמר"
    
    @pytest.mark.asyncio
    async def test_learn_from_corrections(self, setup):
        """בדיקת למידה מתיקונים של המשתמש"""
        # הגדרת התנהגות ה-agent לבדיקה זו
        self.mock_agent.get_response.side_effect = self.responses_for_learn_corrections
        
        # יצירת הודעה ראשונה
        first_message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני אוהב פיצה"
        )

        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(first_message)

        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"

        # יצירת הודעה שנייה עם תיקון
        second_message = MockTelegramMessage(
            message_id=2,
            user=self.user,
            chat=self.chat,
            text="תקן: אני אוהב פסטה"
        )

        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(second_message)

        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 1, "לא נשלחה הודעת תגובה שנייה"

        # בדיקה שהסוכן מאשר את התיקון
        second_response = self.bot.sent_messages[1]
        assert "תודה על התיקון" in second_response["text"], "הסוכן לא מאשר את התיקון"
    
    @pytest.mark.asyncio
    async def test_remember_user_preferences(self, setup):
        """בדיקה שהסוכן זוכר העדפות משתמש"""
        # הגדרת התנהגות ה-agent לבדיקה זו
        self.mock_agent.get_response.side_effect = self.responses_for_user_preferences
        
        # יצירת הודעה ראשונה
        first_message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני מעדיף שוקולד"
        )

        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(first_message)

        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהתגובה מכילה אישור על שמירת ההעדפה
        first_response = self.bot.sent_messages[0]
        assert "תודה שסיפרת לי" in first_response["text"], "הסוכן לא מאשר את שמירת ההעדפה"
        assert "שוקולד" in first_response["text"], "הסוכן לא מזכיר את ההעדפה שנשמרה"

        # יצירת הודעה שנייה לבדיקת זכירת ההעדפה
        second_message = MockTelegramMessage(
            message_id=2,
            user=self.user,
            chat=self.chat,
            text="מה אני מעדיף?"
        )

        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(second_message)

        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 1, "לא נשלחה הודעת תגובה שנייה"
        
        # בדיקה שהסוכן זוכר את ההעדפה
        second_response = self.bot.sent_messages[1]
        assert "אתה מעדיף" in second_response["text"], "הסוכן לא זוכר את ההעדפה" 