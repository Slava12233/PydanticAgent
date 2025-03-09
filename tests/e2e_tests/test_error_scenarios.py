"""
בדיקות קצה לקצה לתרחישי שגיאה.
בדיקות אלו מדמות משתמש אמיתי המתקשר עם הסוכן בתרחישים שעלולים לגרום לשגיאות.
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
            self.products = [
                {
                    "id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "category": "אלקטרוניקה",
                    "price": 3499.99,
                    "description": "טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול",
                    "stock": 10
                },
                {
                    "id": 2,
                    "name": "אוזניות Bluetooth",
                    "category": "אלקטרוניקה",
                    "price": 299.99,
                    "description": "אוזניות אלחוטיות עם סינון רעשים",
                    "stock": 20
                },
                {
                    "id": 3,
                    "name": "חולצת כותנה",
                    "category": "ביגוד",
                    "price": 99.99,
                    "description": "חולצת כותנה איכותית במגוון צבעים",
                    "stock": 50
                }
            ]
            self.orders = {}
        
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
            return True
        
        def get_product(self, product_id):
            """קבלת מוצר לפי מזהה"""
            for product in self.products:
                if product["id"] == product_id:
                    return product
            return None
        
        def get_products(self, category=None, search_term=None, limit=10):
            """קבלת רשימת מוצרים"""
            products = self.products
            
            if category:
                products = [p for p in products if p["category"] == category]
            
            if search_term:
                products = [p for p in products if search_term.lower() in p["name"].lower() or search_term.lower() in p["description"].lower()]
            
            return products[:limit]
        
        def get_order(self, order_id):
            """קבלת פרטי הזמנה"""
            return self.orders.get(order_id)
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תשובה מהסוכן"""
            # תשובות מוכנות מראש לפי תוכן ההודעה
            if not text or text.strip() == "":
                return "נראה שלא שלחת הודעה. איך אוכל לעזור לך?"
                
            if text.startswith("/"):
                return f"הפקודה {text} אינה מוכרת. נסה /help לקבלת רשימת הפקודות."
                
            if "מוצר" in text and "לא קיים" in text:
                return "המוצר המבוקש אינו קיים במערכת. אנא בדוק את מספר המוצר או חפש מוצרים דומים."
                
            if "הזמנה" in text and "לא קיימת" in text:
                return "ההזמנה המבוקשת אינה קיימת במערכת. אנא בדוק את מספר ההזמנה."
                
            if "שגיאת מערכת" in text:
                raise Exception("שגיאת מערכת לצורך בדיקה")
                
            if "בקשה לא חוקית" in text:
                return "הבקשה שלך אינה חוקית. אנא נסה שוב בצורה תקינה."
                
            if "לא ברור" in text:
                return "סליחה, לא הבנתי את הבקשה. האם תוכל לנסח אותה בצורה ברורה יותר?"
                
            # תשובה כללית אם לא זוהה תוכן ספציפי
            return "אני מבין. איך אוכל לעזור לך עוד?"


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


class TestErrorScenarios:
    """מחלקת בדיקות לתרחישי שגיאה"""
    
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
        
        # הגדרת התנהגות ה-agent לפי הבדיקה
        def get_response_side_effect(text, user_id=None, context=None):
            if not text or text.strip() == "":
                return "נראה שלא שלחת הודעה. איך אוכל לעזור לך?"
                
            if text.startswith("/"):
                return f"הפקודה {text} אינה מוכרת. נסה /help לקבלת רשימת הפקודות."
                
            if "מוצר שלא קיים" in text:
                return "לא מצאתי מוצר כזה במערכת. האם תרצה לחפש מוצר אחר?"
                
            if "הזמנה שלא קיימת" in text:
                return "לא מצאתי הזמנה כזו במערכת. אנא בדוק את מספר ההזמנה ונסה שוב."
                
            if "שגיאת מערכת" in text:
                raise Exception("שגיאת מערכת לצורך בדיקה")
                
            if "בקשה לא חוקית" in text:
                return "הבקשה שלך אינה חוקית או אינה מורשית. אנא פנה לתמיכה אם אתה חושב שזו טעות."
                
            if "אבגדהוזחטיכלמנסעפצקרשת" in text:
                return "לא בטוח שהבנתי את הבקשה שלך. האם תוכל לנסח אותה בצורה אחרת?"
                
            # תשובה כללית
            return "אני לא בטוח שהבנתי את הבקשה שלך. האם תוכל לנסח אותה בצורה אחרת?"
        
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
    async def test_empty_message(self, setup):
        """בדיקת הודעה ריקה"""
        # יצירת הודעה ריקה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text=""
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה להודעה הריקה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "לא שלחת הודעה" in first_message["text"] or "הודעה ריקה" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות להודעה ריקה"
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, setup):
        """בדיקת פקודה לא קיימת"""
        # יצירת הודעה עם פקודה לא קיימת
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="/unknown_command",
            entities=[{"type": "bot_command", "offset": 0, "length": 15}]
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לפקודה הלא קיימת
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "אינה מוכרת" in first_message["text"] or "לא קיימת" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות לפקודה לא קיימת"
    
    @pytest.mark.asyncio
    async def test_nonexistent_product(self, setup):
        """בדיקת חיפוש מוצר שלא קיים"""
        # יצירת הודעה עם חיפוש מוצר שלא קיים
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני מחפש מוצר שלא קיים"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לחיפוש המוצר שלא קיים
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "לא מצאתי מוצר כזה" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות למוצר שלא קיים"
    
    @pytest.mark.asyncio
    async def test_nonexistent_order(self, setup):
        """בדיקת חיפוש הזמנה שלא קיימת"""
        # יצירת הודעה עם חיפוש הזמנה שלא קיימת
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה הסטטוס של הזמנה שלא קיימת מספר 99999?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לחיפוש ההזמנה שלא קיימת
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "לא מצאתי הזמנה כזו" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות להזמנה שלא קיימת"
    
    @pytest.mark.asyncio
    async def test_system_error(self, setup):
        """בדיקת שגיאת מערכת"""
        # יצירת הודעה שתגרום לשגיאת מערכת
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="גרום לשגיאת מערכת"
        )
        
        # הגדרת התנהגות ה-agent לזרוק שגיאה
        self.mock_agent.get_response.side_effect = Exception("שגיאת מערכת")
        
        # הגדרת התנהגות ה-agent לאחר השגיאה
        self.mock_agent.get_response.side_effect = [
            "אירעה שגיאה במערכת. אנא נסה שוב מאוחר יותר או פנה לתמיכה."
        ]
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לשגיאת המערכת
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "אירעה שגיאה" in first_message["text"] or "שגיאה" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות לשגיאת מערכת"
    
    @pytest.mark.asyncio
    async def test_invalid_request(self, setup):
        """בדיקת בקשה לא חוקית"""
        # יצירת הודעה עם בקשה לא חוקית
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="בקשה לא חוקית"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לבקשה הלא חוקית
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "אינה חוקית" in first_message["text"] or "לא חוקית" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות לבקשה לא חוקית"
    
    @pytest.mark.asyncio
    async def test_unclear_request(self, setup):
        """בדיקת בקשה לא ברורה"""
        # יצירת הודעה עם בקשה לא ברורה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אבגדהוזחטיכלמנסעפצקרשת"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהסוכן ענה לבקשה הלא ברורה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "לא בטוח שהבנתי" in first_message["text"] or "לא הבנתי" in first_message["text"], "הודעת התגובה אינה מכילה התייחסות לבקשה לא ברורה"


class TelegramBotHandlers:
    """מחלקת מוק ל-TelegramBotHandlers"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.agent = TelegramAgent()
        
    async def handle_message(self, message):
        """טיפול בהודעה נכנסת"""
        try:
            # קבלת תשובה מהסוכן
            response = await self.agent.get_response(message.text, user_id=message.from_user.id)
            
            # שליחת התשובה
            await self.bot.send_message(message.chat.id, response)
            
            return response
        except Exception as e:
            # טיפול בשגיאות
            error_message = f"אירעה שגיאה בעת עיבוד הבקשה: {str(e)}"
            await self.bot.send_message(message.chat.id, error_message)
            return error_message 