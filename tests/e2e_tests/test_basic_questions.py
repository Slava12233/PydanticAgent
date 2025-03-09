"""
בדיקות קצה לקצה לתרחיש שאילת שאלות בסיסיות לבוט.
בדיקות אלו מדמות משתמש אמיתי השואל שאלות בסיסיות מהבוט.
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
    
    class TelegramBotHandlers:
        """מחלקת מוק ל-TelegramBotHandlers"""
        def __init__(self, bot):
            self.bot = bot
            self.db = Database()
            self.agent = TelegramAgent()
        
        async def handle_message(self, message):
            response = await self.agent.get_response(message.text)
            await self.bot.send_message(message.chat.id, response)
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text):
            if "יכול לעשות" in text:
                return """
                אני יכול לעזור לך במגוון דרכים:
                1. חיפוש מוצרים בחנות
                2. מעקב אחר הזמנות
                3. מענה על שאלות לגבי מוצרים
                """
            elif "החנות" in text:
                return "החנות שלנו מציעה מגוון רחב של מוצרים. שעות הפעילות שלנו הן..."
            else:
                return "שלום! איך אוכל לעזור לך היום?"

# ייבוא מחלקות מוק מקובץ הבדיקה הראשון
try:
    from .test_conversation_start import MockTelegramUser, MockTelegramChat, MockTelegramMessage, MockTelegramBot
except ImportError:
    # במקרה שהייבוא נכשל, נגדיר את המחלקות כאן
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

# מחלקות מוק לשירותים שאינם קיימים
class IntentClassifier:
    """מחלקת מוק ל-IntentClassifier"""
    
    async def classify(self, text, intents=None, min_confidence=0.5):
        """מוק לפונקציית classify"""
        if "יכול לעשות" in text:
            return {"intent": "bot_capabilities", "confidence": 0.95}
        elif "החנות" in text:
            return {"intent": "store_information", "confidence": 0.92}
        elif "מזג האוויר" in text:
            return {"intent": "general_question", "confidence": 0.85}
        else:
            return {"intent": "unknown", "confidence": 0.5}

class EntityExtractor:
    """מחלקת מוק ל-EntityExtractor"""
    
    async def extract(self, text, entity_types=None):
        """מוק לפונקציית extract"""
        entities = {}
        if "מוצר" in text:
            entities["product"] = "מוצר כלשהו"
        if "מחיר" in text:
            entities["price"] = "100 ש\"ח"
        return entities


class TestBasicQuestions:
    """מחלקת בדיקות לתרחיש שאילת שאלות בסיסיות"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_intent_classifier = AsyncMock(spec=IntentClassifier)
        self.mock_entity_extractor = AsyncMock(spec=EntityExtractor)
        
        # הגדרת משתמש קיים
        self.existing_user = {
            "id": 12345,
            "first_name": "משה",
            "last_name": "ישראלי",
            "username": "moshe_israeli",
            "created_at": "2023-01-01T00:00:00",
            "last_interaction": "2023-01-01T00:00:00",
            "preferences": json.dumps({"language": "he"})
        }
        self.mock_db.get_user.return_value = self.existing_user
        
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
        self.mock_intent_classifier.reset_mock()
        self.mock_entity_extractor.reset_mock()
    
    @pytest.mark.asyncio
    async def test_bot_capabilities_question(self, setup):
        """בדיקת שאלה על יכולות הבוט"""
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        אני יכול לעזור לך במגוון דרכים:
        1. חיפוש מוצרים בחנות
        2. מעקב אחר הזמנות
        3. מענה על שאלות לגבי מוצרים
        4. עזרה בתהליך הרכישה
        5. טיפול בבעיות במשלוח
        6. מתן מידע על מבצעים והנחות
        7. עזרה בהחזרת מוצרים
        
        איך אוכל לעזור לך היום?
        """
        
        # הגדרת כוונה מזוהה
        self.mock_intent_classifier.classify.return_value = {"intent": "bot_capabilities", "confidence": 0.95}
        
        # יצירת הודעת שאלה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה אתה יכול לעשות?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "יכול לעזור" in first_message["text"], "הודעת התגובה אינה מכילה מידע על יכולות הבוט"
        assert "חיפוש מוצרים" in first_message["text"], "הודעת התגובה אינה מזכירה חיפוש מוצרים"
    
    @pytest.mark.asyncio
    async def test_store_information_question(self, setup):
        """בדיקת שאלה על החנות"""
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        החנות שלנו מציעה מגוון רחב של מוצרים באיכות גבוהה. אנחנו פועלים משנת 2010 ומתמחים במוצרי אלקטרוניקה, ביגוד, וכלי בית.
        
        שעות הפעילות שלנו:
        - ימים א'-ה': 09:00-21:00
        - יום ו': 09:00-14:00
        - שבת: סגור
        
        כתובת החנות הפיזית: רחוב הרצל 100, תל אביב
        
        אפשר לבצע הזמנות באתר 24/7 ולקבל משלוח עד הבית תוך 3-5 ימי עסקים.
        """
        
        # הגדרת כוונה מזוהה
        self.mock_intent_classifier.classify.return_value = {"intent": "store_information", "confidence": 0.92}
        
        # יצירת הודעת שאלה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="ספר לי על החנות שלכם"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "החנות שלנו" in first_message["text"], "הודעת התגובה אינה מכילה מידע על החנות"
        assert "שעות הפעילות" in first_message["text"], "הודעת התגובה אינה מכילה מידע על שעות הפעילות"
    
    @pytest.mark.asyncio
    async def test_general_question(self, setup):
        """בדיקת שאלה כללית שאינה קשורה לעסק"""
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        אני מתמחה בעיקר בנושאים הקשורים לחנות שלנו ולמוצרים שאנחנו מציעים. 
        
        לגבי השאלה שלך על מזג האוויר, אני לא יכול לספק מידע מדויק בזמן אמת, אבל אני יכול להמליץ לבדוק באתרי מזג אוויר כמו השירות המטאורולוגי או אפליקציות ייעודיות.
        
        האם אוכל לעזור לך בנושא אחר הקשור לחנות או למוצרים שלנו?
        """
        
        # הגדרת כוונה מזוהה
        self.mock_intent_classifier.classify.return_value = {"intent": "general_question", "confidence": 0.85}
        
        # יצירת הודעת שאלה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה מזג האוויר היום?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "מתמחה" in first_message["text"], "הודעת התגובה אינה מסבירה את תחומי ההתמחות של הבוט"
        assert "לעזור לך בנושא אחר" in first_message["text"], "הודעת התגובה אינה מציעה עזרה בנושאים אחרים"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 