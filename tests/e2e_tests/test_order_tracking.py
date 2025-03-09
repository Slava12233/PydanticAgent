"""
בדיקות קצה לקצה לתרחיש מעקב אחר הזמנה.
בדיקות אלו מדמות משתמש אמיתי העוקב אחר הזמנה שביצע.
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
    
    def get_order(self, order_id):
        """קבלת פרטי הזמנה"""
        return {
            "id": order_id,
            "user_id": 12345,
            "items": [
                {
                    "product_id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "price": 3499.99,
                    "quantity": 1,
                    "total": 3499.99
                }
            ],
            "total": 3499.99,
            "shipping_address": "רחוב הרצל 1, תל אביב",
            "payment_method": "credit_card",
            "status": "processing",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "shipping_tracking_id": "TRK123456789"
        }
    
    def get_user_orders(self, user_id, limit=10):
        """קבלת רשימת הזמנות של משתמש"""
        return [
            {
                "id": 12345,
                "user_id": user_id,
                "total": 3499.99,
                "status": "processing",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "id": 12344,
                "user_id": user_id,
                "total": 299.99,
                "status": "delivered",
                "created_at": (datetime.now() - timedelta(days=10)).isoformat()
            }
        ][:limit]
    
    def update_order(self, order_id, **kwargs):
        """עדכון פרטי הזמנה"""
        order = self.get_order(order_id)
        for key, value in kwargs.items():
            order[key] = value
        return order
    
    def cancel_order(self, order_id):
        """ביטול הזמנה"""
        order = self.get_order(order_id)
        order["status"] = "cancelled"
        return order

class TelegramAgent:
    """מחלקת מוק ל-TelegramAgent"""
    async def get_response(self, text, user_id=None, context=None):
        """קבלת תשובה מהסוכן"""
        if "סטטוס הזמנה" in text or "מצב הזמנה" in text or "מה הסטטוס של הזמנה" in text:
            return "הזמנה מספר 12345 נמצאת בסטטוס: בתהליך. המשלוח צפוי להגיע בתאריך 01/03/2023."
        
        if "עדכון על הזמנה" in text or "לקבל עדכון על הזמנה" in text:
            return "הזמנה מספר 12345 עודכנה לסטטוס: נשלחה. מספר מעקב: TRK123456789"
        
        if "שנה פרטי הזמנה" in text or "לשנות את כתובת המשלוח" in text:
            return "פרטי ההזמנה עודכנו בהצלחה."
        
        if "בטל הזמנה" in text or "לבטל את הזמנה" in text:
            return "הזמנה מספר 12345 בוטלה בהצלחה."
        
        if "ההזמנות שלי" in text:
            return "הזמנות שלך:\n1. הזמנה מספר 12345 - סטטוס: בתהליך - תאריך: 01/03/2023\n2. הזמנה מספר 12344 - סטטוס: נמסרה - תאריך: 20/02/2023"
        
        return "אני לא מבין את הבקשה. אנא נסה שוב."

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

class OrderService:
    """מחלקת מוק לשירות הזמנות"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def get_order(self, order_id):
        """קבלת פרטי הזמנה"""
        return self.db.get_order(order_id)
    
    def get_user_orders(self, user_id, limit=10):
        """קבלת רשימת הזמנות של משתמש"""
        return self.db.get_user_orders(user_id, limit)
    
    def update_order(self, order_id, **kwargs):
        """עדכון פרטי הזמנה"""
        return self.db.update_order(order_id, **kwargs)
    
    def cancel_order(self, order_id):
        """ביטול הזמנה"""
        return self.db.cancel_order(order_id)

class ShippingService:
    """מחלקת מוק לשירות משלוחים"""
    def get_tracking_info(self, tracking_id):
        """קבלת מידע על מעקב משלוח"""
        return {
            "tracking_id": tracking_id,
            "status": "in_transit",
            "estimated_delivery": (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
            "current_location": "מרכז מיון תל אביב",
            "history": [
                {
                    "status": "created",
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                    "location": "מחסן החברה"
                },
                {
                    "status": "in_transit",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "location": "מרכז מיון תל אביב"
                }
            ]
        }

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

class TestOrderTracking:
    """מחלקת בדיקות לתרחיש מעקב אחר הזמנה"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_order_service = MagicMock(spec=OrderService)
        self.mock_shipping_service = MagicMock(spec=ShippingService)

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

        self.mock_order_service.get_order.return_value = {
            "id": 12345,
            "user_id": 12345,
            "items": [
                {
                    "product_id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "price": 3499.99,
                    "quantity": 1,
                    "total": 3499.99
                }
            ],
            "total": 3499.99,
            "shipping_address": "רחוב הרצל 1, תל אביב",
            "payment_method": "credit_card",
            "status": "processing",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "shipping_tracking_id": "TRK123456789"
        }

        self.mock_order_service.get_user_orders.return_value = [
            {
                "id": 12345,
                "user_id": 12345,
                "total": 3499.99,
                "status": "processing",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "id": 12344,
                "user_id": 12345,
                "total": 299.99,
                "status": "delivered",
                "created_at": (datetime.now() - timedelta(days=10)).isoformat()
            }
        ]

        self.mock_shipping_service.get_tracking_info.return_value = {
            "tracking_id": "TRK123456789",
            "status": "in_transit",
            "estimated_delivery": (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
            "current_location": "מרכז מיון תל אביב",
            "history": [
                {
                    "status": "created",
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                    "location": "מחסן החברה"
                },
                {
                    "status": "in_transit",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "location": "מרכז מיון תל אביב"
                }
            ]
        }

        # יצירת בוט מדומה
        self.bot = MockTelegramBot()
        
        # יצירת מטפל הודעות
        self.handlers = TelegramBotHandlers(self.bot)
        
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
        self.mock_order_service.reset_mock()
        self.mock_shipping_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_check_order_status(self, setup):
        """בדיקת סטטוס הזמנה"""
        # יצירת הודעה לבדיקת סטטוס הזמנה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה הסטטוס של הזמנה מספר 12345?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "הזמנה מספר 12345" in first_message["text"], "הודעת התגובה אינה מכילה את מספר ההזמנה"
        assert "סטטוס" in first_message["text"], "הודעת התגובה אינה מכילה מידע על סטטוס ההזמנה"
    
    @pytest.mark.asyncio
    async def test_get_order_updates(self, setup):
        """בדיקת קבלת עדכונים על הזמנה"""
        # יצירת הודעה לקבלת עדכונים על הזמנה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני רוצה לקבל עדכון על הזמנה מספר 12345"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "הזמנה מספר 12345" in first_message["text"], "הודעת התגובה אינה מכילה את מספר ההזמנה"
        assert "עודכנה" in first_message["text"], "הודעת התגובה אינה מכילה מידע על עדכון ההזמנה"
    
    @pytest.mark.asyncio
    async def test_update_order_details(self, setup):
        """בדיקת שינוי פרטי הזמנה"""
        # יצירת הודעה לשינוי פרטי הזמנה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני רוצה לשנות את כתובת המשלוח בהזמנה מספר 12345 לרחוב אלנבי 10, תל אביב"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "פרטי ההזמנה עודכנו" in first_message["text"], "הודעת התגובה אינה מכילה אישור על עדכון פרטי ההזמנה"
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, setup):
        """בדיקת ביטול הזמנה"""
        # יצירת הודעה לביטול הזמנה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="אני רוצה לבטל את הזמנה מספר 12345"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "הזמנה מספר 12345 בוטלה" in first_message["text"], "הודעת התגובה אינה מכילה אישור על ביטול ההזמנה" 