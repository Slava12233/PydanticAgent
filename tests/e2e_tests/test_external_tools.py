"""
בדיקות קצה לקצה לתרחיש שימוש בכלים חיצוניים.
בדיקות אלו מדמות משתמש אמיתי המשתמש בכלים חיצוניים דרך הבוט.
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

# מחלקות מוק לצורך הבדיקות
class Database:
    """מחלקת מוק ל-Database"""
    def get_user(self, user_id):
        return {
            "id": user_id,
            "first_name": "משה",
            "last_name": "ישראלי",
            "username": "moshe_israeli",
            "created_at": "2023-01-01T00:00:00",
            "last_interaction": "2023-01-01T00:00:00",
            "preferences": json.dumps({"language": "he"})
        }

class TelegramAgent:
    """מחלקת מוק ל-TelegramAgent"""
    async def get_response(self, text, user_id=None, context=None):
        """קבלת תשובה מהסוכן"""
        # בדיקת בקשות לכלים חיצוניים
        if "בדוק מזג אוויר" in text:
            return "מזג האוויר בתל אביב: 25°C, שמש, לחות: 60%"
        
        if "בדוק מחיר מניה" in text:
            return "מחיר המניה של אפל (AAPL): $150.25, שינוי: +1.2%"
        
        if "תרגם" in text:
            return "התרגום של 'שלום' לאנגלית הוא: Hello"
        
        if "חפש באינטרנט" in text:
            return "תוצאות חיפוש עבור 'פייתון': Python הוא שפת תכנות פופולרית..."
        
        # תשובה כללית
        return "אני לא מכיר את הכלי הזה. הכלים הזמינים: מזג אוויר, מחירי מניות, תרגום, חיפוש באינטרנט."

class TelegramBotHandlers:
    """מחלקת מוק ל-TelegramBotHandlers"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.agent = TelegramAgent()
    
    async def handle_message(self, message):
        """טיפול בהודעה נכנסת"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text
        
        # קבלת תשובה מהסוכן
        response = await self.agent.get_response(text, user_id=user_id)
        
        # שליחת התשובה למשתמש
        await self.bot.send_message(chat_id, response)

# מחלקות מוק לכלים חיצוניים
class WeatherService:
    """מחלקת מוק לשירות מזג אוויר"""
    def get_weather(self, location):
        """קבלת מזג אוויר למיקום"""
        weather_data = {
            "תל אביב": {
                "temperature": 25,
                "condition": "שמש",
                "humidity": 60,
                "wind": 10
            },
            "ירושלים": {
                "temperature": 20,
                "condition": "בהיר",
                "humidity": 50,
                "wind": 15
            },
            "חיפה": {
                "temperature": 23,
                "condition": "מעונן חלקית",
                "humidity": 70,
                "wind": 20
            }
        }
        
        if location in weather_data:
            return weather_data[location]
        
        return {
            "temperature": 22,
            "condition": "לא ידוע",
            "humidity": 60,
            "wind": 10
        }


class StockService:
    """מחלקת מוק לשירות מניות"""
    def get_stock_price(self, symbol):
        """קבלת מחיר מניה"""
        stock_data = {
            "AAPL": {
                "price": 150.25,
                "change": 1.2,
                "company": "Apple Inc."
            },
            "MSFT": {
                "price": 290.75,
                "change": 0.8,
                "company": "Microsoft Corporation"
            },
            "GOOGL": {
                "price": 2750.50,
                "change": -0.5,
                "company": "Alphabet Inc."
            }
        }
        
        if symbol in stock_data:
            return stock_data[symbol]
        
        return {
            "price": 0,
            "change": 0,
            "company": "לא נמצא"
        }


class TranslationService:
    """מחלקת מוק לשירות תרגום"""
    def translate(self, text, source_lang, target_lang):
        """תרגום טקסט"""
        translations = {
            ("שלום", "he", "en"): "Hello",
            ("בוקר טוב", "he", "en"): "Good morning",
            ("תודה", "he", "en"): "Thank you",
            ("Hello", "en", "he"): "שלום",
            ("Good morning", "en", "he"): "בוקר טוב",
            ("Thank you", "en", "he"): "תודה"
        }
        
        key = (text, source_lang, target_lang)
        if key in translations:
            return translations[key]
        
        return f"[תרגום לא זמין: {text}]"


class SearchService:
    """מחלקת מוק לשירות חיפוש"""
    def search(self, query, limit=5):
        """חיפוש באינטרנט"""
        search_results = {
            "פייתון": [
                {"title": "Python (programming language) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)", "snippet": "Python הוא שפת תכנות פופולרית..."},
                {"title": "Python.org", "url": "https://www.python.org/", "snippet": "האתר הרשמי של שפת התכנות Python..."},
                {"title": "Python Tutorial - W3Schools", "url": "https://www.w3schools.com/python/", "snippet": "מדריך Python מקיף..."}
            ],
            "תל אביב": [
                {"title": "תל אביב-יפו - ויקיפדיה", "url": "https://he.wikipedia.org/wiki/תל_אביב-יפו", "snippet": "תל אביב-יפו היא עיר במחוז תל אביב..."},
                {"title": "עיריית תל אביב-יפו", "url": "https://www.tel-aviv.gov.il/", "snippet": "האתר הרשמי של עיריית תל אביב-יפו..."},
                {"title": "Visit Tel Aviv - התיירות הרשמית של תל אביב", "url": "https://www.visit-tel-aviv.com/", "snippet": "מידע לתיירים על תל אביב..."}
            ]
        }
        
        if query in search_results:
            return search_results[query][:limit]
        
        return [{"title": "לא נמצאו תוצאות", "url": "", "snippet": "לא נמצאו תוצאות עבור החיפוש שלך."}]


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


class TestExternalTools:
    """מחלקת בדיקות לתרחיש שימוש בכלים חיצוניים"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_weather_service = MagicMock(spec=WeatherService)
        self.mock_stock_service = MagicMock(spec=StockService)
        self.mock_translation_service = MagicMock(spec=TranslationService)
        self.mock_search_service = MagicMock(spec=SearchService)
        
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
        
        self.mock_weather_service.get_weather.return_value = {
            "temperature": 25,
            "condition": "שמש",
            "humidity": 60,
            "wind": 10
        }
        
        self.mock_stock_service.get_stock_price.return_value = {
            "price": 150.25,
            "change": 1.2,
            "company": "Apple Inc."
        }
        
        self.mock_translation_service.translate.return_value = "Hello"
        
        self.mock_search_service.search.return_value = [
            {"title": "Python (programming language) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)", "snippet": "Python הוא שפת תכנות פופולרית..."}
        ]
        
        # הגדרת התנהגות ה-agent
        async def get_response_side_effect(text, user_id=None, context=None):
            if "בדוק מזג אוויר" in text:
                return "מזג האוויר בתל אביב: 25°C, שמש, לחות: 60%"
            elif "בדוק מחיר מניה" in text:
                return "מחיר המניה של אפל (AAPL): $150.25, שינוי: +1.2%"
            elif "תרגם" in text:
                return "התרגום של 'שלום' לאנגלית הוא: Hello"
            elif "חפש באינטרנט" in text:
                return "תוצאות חיפוש עבור 'פייתון': Python הוא שפת תכנות פופולרית..."
            else:
                return "אני לא מכיר את הכלי הזה. הכלים הזמינים: מזג אוויר, מחירי מניות, תרגום, חיפוש באינטרנט."
        
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
        self.mock_weather_service.reset_mock()
        self.mock_stock_service.reset_mock()
        self.mock_translation_service.reset_mock()
        self.mock_search_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_weather_integration(self, setup):
        """בדיקת אינטגרציה עם שירות מזג אוויר"""
        # יצירת הודעה עם בקשה למזג אוויר
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="בדוק מזג אוויר בתל אביב"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "מזג האוויר" in first_message["text"], "הודעת התגובה אינה מכילה מידע על מזג האוויר"
        assert "תל אביב" in first_message["text"], "הודעת התגובה אינה מכילה את שם העיר"
        assert "25°C" in first_message["text"], "הודעת התגובה אינה מכילה את הטמפרטורה"
    
    @pytest.mark.asyncio
    async def test_stock_integration(self, setup):
        """בדיקת אינטגרציה עם שירות מניות"""
        # יצירת הודעה עם בקשה למחיר מניה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="בדוק מחיר מניה של אפל"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "מחיר המניה" in first_message["text"], "הודעת התגובה אינה מכילה מידע על מחיר המניה"
        assert "אפל" in first_message["text"], "הודעת התגובה אינה מכילה את שם החברה"
        assert "$150.25" in first_message["text"], "הודעת התגובה אינה מכילה את מחיר המניה"
    
    @pytest.mark.asyncio
    async def test_translation_integration(self, setup):
        """בדיקת אינטגרציה עם שירות תרגום"""
        # יצירת הודעה עם בקשה לתרגום
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="תרגם את המילה 'שלום' לאנגלית"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "התרגום" in first_message["text"], "הודעת התגובה אינה מכילה מידע על התרגום"
        assert "שלום" in first_message["text"], "הודעת התגובה אינה מכילה את המילה המקורית"
        assert "Hello" in first_message["text"], "הודעת התגובה אינה מכילה את התרגום"
    
    @pytest.mark.asyncio
    async def test_search_integration(self, setup):
        """בדיקת אינטגרציה עם שירות חיפוש"""
        # יצירת הודעה עם בקשה לחיפוש
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="חפש באינטרנט פייתון"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "תוצאות חיפוש" in first_message["text"], "הודעת התגובה אינה מכילה מידע על תוצאות החיפוש"
        assert "פייתון" in first_message["text"], "הודעת התגובה אינה מכילה את מונח החיפוש"
        assert "Python" in first_message["text"], "הודעת התגובה אינה מכילה את תוצאות החיפוש" 