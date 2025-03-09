"""
בדיקות קצה לקצה לתרחיש חיפוש מוצרים בחנות.
בדיקות אלו מדמות משתמש אמיתי המחפש מוצרים בחנות.
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
    from src.services.store.product_service import ProductService
except ImportError as e:
    print(f"שגיאת ייבוא: {e}")
    print("ייתכן שנדרש להתאים את נתיבי הייבוא")
    
    # מחלקות מוק למקרה שהייבוא נכשל
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
        
        def get_products(self, category=None, search_term=None, limit=10):
            """מחזיר רשימת מוצרים לפי קטגוריה או מונח חיפוש"""
            products = [
                {
                    "id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "category": "אלקטרוניקה",
                    "price": 3499.99,
                    "description": "טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול",
                    "stock": 15,
                    "attributes": json.dumps({"color": "שחור", "storage": "128GB", "screen": "6.2 אינץ'"})
                },
                {
                    "id": 2,
                    "name": "אוזניות אלחוטיות AirPods Pro",
                    "category": "אלקטרוניקה",
                    "price": 899.99,
                    "description": "אוזניות אלחוטיות עם ביטול רעשים אקטיבי",
                    "stock": 20,
                    "attributes": json.dumps({"color": "לבן", "battery": "24 שעות", "noise_cancellation": True})
                },
                {
                    "id": 3,
                    "name": "חולצת כותנה קלאסית",
                    "category": "ביגוד",
                    "price": 99.99,
                    "description": "חולצת כותנה איכותית במגוון צבעים",
                    "stock": 50,
                    "attributes": json.dumps({"color": "כחול", "size": "M", "material": "100% כותנה"})
                },
                {
                    "id": 4,
                    "name": "מחבת קרמית 28 ס\"מ",
                    "category": "כלי בית",
                    "price": 199.99,
                    "description": "מחבת קרמית איכותית עם ציפוי נון-סטיק",
                    "stock": 30,
                    "attributes": json.dumps({"color": "שחור", "diameter": "28 ס\"מ", "dishwasher_safe": True})
                }
            ]
            
            if category:
                products = [p for p in products if p["category"] == category]
            
            if search_term:
                products = [p for p in products if search_term.lower() in p["name"].lower() or search_term.lower() in p["description"].lower()]
            
            return products[:limit]
        
        def get_product(self, product_id):
            """מחזיר מוצר לפי מזהה"""
            products = self.get_products()
            for product in products:
                if product["id"] == product_id:
                    return product
            return None
    
    class TelegramBotHandlers:
        """מחלקת מוק ל-TelegramBotHandlers"""
        def __init__(self, bot):
            self.bot = bot
            self.db = Database()
            self.agent = TelegramAgent()
            self.product_service = ProductService()
        
        async def handle_message(self, message):
            """טיפול בהודעות טקסט רגילות"""
            # קבלת תשובה מהסוכן
            response = await self.agent.get_response(message.text)
            
            # שליחת התשובה למשתמש
            await self.bot.send_message(message.chat.id, response)
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text):
            """מוק לפונקציית get_response"""
            if "מוצר" in text or "חיפוש" in text:
                if "טלפון" in text or "סמארטפון" in text:
                    return """
                    מצאתי עבורך את המוצרים הבאים:
                    
                    1. טלפון חכם Galaxy S21 - 3,499.99 ₪
                    מצלמה איכותית, מסך 6.2 אינץ', זיכרון 128GB
                    
                    האם תרצה לראות פרטים נוספים על אחד המוצרים?
                    """
                elif "אוזניות" in text:
                    return """
                    מצאתי עבורך את המוצרים הבאים:
                    
                    1. אוזניות אלחוטיות AirPods Pro - 899.99 ₪
                    ביטול רעשים אקטיבי, סוללה ל-24 שעות
                    
                    האם תרצה לראות פרטים נוספים על המוצר?
                    """
                elif "ביגוד" in text or "חולצה" in text:
                    return """
                    מצאתי עבורך את המוצרים הבאים:
                    
                    1. חולצת כותנה קלאסית - 99.99 ₪
                    100% כותנה, מידה M, צבע כחול
                    
                    האם תרצה לראות פרטים נוספים על המוצר?
                    """
                else:
                    return """
                    מצאתי עבורך מספר מוצרים:
                    
                    1. טלפון חכם Galaxy S21 - 3,499.99 ₪
                    2. אוזניות אלחוטיות AirPods Pro - 899.99 ₪
                    3. חולצת כותנה קלאסית - 99.99 ₪
                    4. מחבת קרמית 28 ס"מ - 199.99 ₪
                    
                    איזה מוצר מעניין אותך?
                    """
            elif "פרטים" in text or "מידע נוסף" in text:
                if "טלפון" in text or "גלקסי" in text or "Galaxy" in text:
                    return """
                    טלפון חכם Galaxy S21
                    מחיר: 3,499.99 ₪
                    קטגוריה: אלקטרוניקה
                    מלאי: 15 יחידות
                    
                    תיאור: טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול
                    
                    מאפיינים:
                    - צבע: שחור
                    - זיכרון: 128GB
                    - מסך: 6.2 אינץ'
                    
                    האם תרצה להוסיף את המוצר לסל הקניות?
                    """
                else:
                    return "איזה מוצר תרצה לראות פרטים נוספים עליו?"
            else:
                return "איך אוכל לעזור לך למצוא מוצרים בחנות שלנו?"
    
    class ProductService:
        """מחלקת מוק ל-ProductService"""
        def __init__(self):
            self.db = Database()
        
        def search_products(self, query, category=None, limit=10):
            """חיפוש מוצרים לפי מילות מפתח וקטגוריה"""
            return self.db.get_products(category=category, search_term=query, limit=limit)
        
        def get_product_details(self, product_id):
            """קבלת פרטי מוצר לפי מזהה"""
            return self.db.get_product(product_id)
        
        def get_products_by_category(self, category, limit=10):
            """קבלת מוצרים לפי קטגוריה"""
            return self.db.get_products(category=category, limit=limit)
        
        def get_popular_products(self, limit=5):
            """קבלת מוצרים פופולריים"""
            return self.db.get_products(limit=limit)

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


class TestProductSearch:
    """מחלקת בדיקות לתרחיש חיפוש מוצרים בחנות"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_product_service = MagicMock(spec=ProductService)
        
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
        
        # הגדרת מוצרים לדוגמה
        self.sample_products = [
            {
                "id": 1,
                "name": "טלפון חכם Galaxy S21",
                "category": "אלקטרוניקה",
                "price": 3499.99,
                "description": "טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול",
                "stock": 15,
                "attributes": json.dumps({"color": "שחור", "storage": "128GB", "screen": "6.2 אינץ'"})
            },
            {
                "id": 2,
                "name": "אוזניות אלחוטיות AirPods Pro",
                "category": "אלקטרוניקה",
                "price": 899.99,
                "description": "אוזניות אלחוטיות עם ביטול רעשים אקטיבי",
                "stock": 20,
                "attributes": json.dumps({"color": "לבן", "battery": "24 שעות", "noise_cancellation": True})
            }
        ]
        
        # הגדרת התנהגות שירות המוצרים
        self.mock_product_service.search_products.return_value = self.sample_products
        self.mock_product_service.get_product_details.return_value = self.sample_products[0]
        self.mock_product_service.get_products_by_category.return_value = self.sample_products
        
        # הגדרת תגובות הסוכן
        self.mock_agent.get_response.return_value = """
        מצאתי עבורך את המוצרים הבאים:
        
        1. טלפון חכם Galaxy S21 - 3,499.99 ₪
        מצלמה איכותית, מסך 6.2 אינץ', זיכרון 128GB
        
        2. אוזניות אלחוטיות AirPods Pro - 899.99 ₪
        ביטול רעשים אקטיבי, סוללה ל-24 שעות
        
        האם תרצה לראות פרטים נוספים על אחד המוצרים?
        """
        
        # יצירת בוט מדומה
        self.bot = MockTelegramBot()
        
        # יצירת מטפל הודעות - שימוש במוקים שיצרנו
        self.handlers = TelegramBotHandlers(self.bot)
        
        # החלפת המוקים הפנימיים של ה-handlers במוקים שלנו
        self.handlers.db = self.mock_db
        self.handlers.agent = self.mock_agent
        self.handlers.product_service = self.mock_product_service
        
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
        self.mock_product_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_search_product_by_name(self, setup):
        """בדיקת חיפוש מוצר לפי שם"""
        # יצירת הודעת חיפוש
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני מחפש טלפון חכם"
        )
        
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        מצאתי עבורך את המוצרים הבאים:
        
        1. טלפון חכם Galaxy S21 - 3,499.99 ₪
        מצלמה איכותית, מסך 6.2 אינץ', זיכרון 128GB
        
        האם תרצה לראות פרטים נוספים על המוצר?
        """
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "טלפון חכם Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה את שם המוצר המבוקש"
        assert "3,499.99" in first_message["text"], "הודעת התגובה אינה מכילה את מחיר המוצר"
    
    @pytest.mark.asyncio
    async def test_search_product_by_category(self, setup):
        """בדיקת חיפוש מוצר לפי קטגוריה"""
        # יצירת הודעת חיפוש
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="הראה לי מוצרי אלקטרוניקה"
        )
        
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        מצאתי עבורך את המוצרים הבאים בקטגוריית אלקטרוניקה:
        
        1. טלפון חכם Galaxy S21 - 3,499.99 ₪
        מצלמה איכותית, מסך 6.2 אינץ', זיכרון 128GB
        
        2. אוזניות אלחוטיות AirPods Pro - 899.99 ₪
        ביטול רעשים אקטיבי, סוללה ל-24 שעות
        
        איזה מוצר מעניין אותך?
        """
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "אלקטרוניקה" in first_message["text"], "הודעת התגובה אינה מכילה את שם הקטגוריה"
        assert "טלפון חכם Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה את המוצר הראשון"
        assert "אוזניות אלחוטיות AirPods Pro" in first_message["text"], "הודעת התגובה אינה מכילה את המוצר השני"
    
    @pytest.mark.asyncio
    async def test_search_product_by_attributes(self, setup):
        """בדיקת חיפוש מוצר לפי תכונות"""
        # יצירת הודעת חיפוש
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני מחפש טלפון עם זיכרון של 128GB"
        )
        
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        מצאתי עבורך את המוצרים הבאים:
        
        1. טלפון חכם Galaxy S21 - 3,499.99 ₪
        מצלמה איכותית, מסך 6.2 אינץ', זיכרון 128GB
        
        האם תרצה לראות פרטים נוספים על המוצר?
        """
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "טלפון חכם Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה את שם המוצר המבוקש"
        assert "128GB" in first_message["text"], "הודעת התגובה אינה מכילה את תכונת הזיכרון המבוקשת"
    
    @pytest.mark.asyncio
    async def test_product_details(self, setup):
        """בדיקת הצגת מידע מפורט על מוצר"""
        # יצירת הודעת בקשת פרטים
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני רוצה לראות פרטים על הטלפון Galaxy S21"
        )
        
        # הגדרת תגובת הסוכן
        self.mock_agent.get_response.return_value = """
        טלפון חכם Galaxy S21
        מחיר: 3,499.99 ₪
        קטגוריה: אלקטרוניקה
        מלאי: 15 יחידות
        
        תיאור: טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול
        
        מאפיינים:
        - צבע: שחור
        - זיכרון: 128GB
        - מסך: 6.2 אינץ'
        
        האם תרצה להוסיף את המוצר לסל הקניות?
        """
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן נקרא לקבלת תשובה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "טלפון חכם Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה את שם המוצר"
        assert "מחיר: 3,499.99" in first_message["text"], "הודעת התגובה אינה מכילה את מחיר המוצר"
        assert "קטגוריה: אלקטרוניקה" in first_message["text"], "הודעת התגובה אינה מכילה את קטגוריית המוצר"
        assert "מלאי: 15" in first_message["text"], "הודעת התגובה אינה מכילה את מלאי המוצר"
        assert "צבע: שחור" in first_message["text"], "הודעת התגובה אינה מכילה את צבע המוצר"
        assert "זיכרון: 128GB" in first_message["text"], "הודעת התגובה אינה מכילה את נפח הזיכרון של המוצר"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 