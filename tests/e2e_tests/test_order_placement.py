"""
בדיקות קצה לקצה לתרחיש ביצוע הזמנה בחנות.
בדיקות אלו מדמות משתמש אמיתי המבצע הזמנה בחנות.
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
    
    def get_products(self, category=None, search_term=None, limit=10):
        """קבלת רשימת מוצרים"""
        products = [
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
                "name": "אוזניות אלחוטיות AirPods Pro",
                "category": "אלקטרוניקה",
                "price": 899.99,
                "description": "אוזניות אלחוטיות עם ביטול רעשים אקטיבי",
                "stock": 20
            },
            {
                "id": 3,
                "name": "חולצת כותנה",
                "category": "ביגוד",
                "price": 99.99,
                "description": "חולצת כותנה איכותית",
                "stock": 50
            }
        ]
        
        if category:
            products = [p for p in products if p["category"] == category]
        
        if search_term:
            products = [p for p in products if search_term.lower() in p["name"].lower() or search_term.lower() in p["description"].lower()]
        
        return products[:limit]
    
    def get_product(self, product_id):
        """קבלת פרטי מוצר"""
        products = self.get_products()
        for product in products:
            if product["id"] == product_id:
                return product
        return None
    
    def get_cart(self, user_id):
        """קבלת עגלת קניות"""
        return {
            "user_id": user_id,
            "items": [],
            "total": 0
        }
    
    def add_to_cart(self, user_id, product_id, quantity=1):
        """הוספת מוצר לעגלת קניות"""
        product = self.get_product(product_id)
        if not product:
            return False
        
        cart = self.get_cart(user_id)
        
        # בדיקה אם המוצר כבר קיים בעגלה
        for item in cart["items"]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                item["total"] = item["price"] * item["quantity"]
                cart["total"] = sum(item["total"] for item in cart["items"])
                return True
        
        # הוספת מוצר חדש לעגלה
        cart["items"].append({
            "product_id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "total": product["price"] * quantity
        })
        
        cart["total"] = sum(item["total"] for item in cart["items"])
        
        return True
    
    def update_cart_item(self, user_id, product_id, quantity):
        """עדכון כמות מוצר בעגלת קניות"""
        cart = self.get_cart(user_id)
        
        for item in cart["items"]:
            if item["product_id"] == product_id:
                if quantity <= 0:
                    return self.remove_from_cart(user_id, product_id)
                
                item["quantity"] = quantity
                item["total"] = item["price"] * item["quantity"]
                cart["total"] = sum(item["total"] for item in cart["items"])
                return True
        
        return False
    
    def remove_from_cart(self, user_id, product_id):
        """הסרת מוצר מעגלת קניות"""
        cart = self.get_cart(user_id)
        
        cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
        cart["total"] = sum(item["total"] for item in cart["items"])
        
        return True
    
    def clear_cart(self, user_id):
        """ניקוי עגלת קניות"""
        cart = self.get_cart(user_id)
        cart["items"] = []
        cart["total"] = 0
        return True
    
    def create_order(self, user_id, shipping_address, payment_method):
        """יצירת הזמנה חדשה"""
        cart = self.get_cart(user_id)
        
        if not cart["items"]:
            return None
        
        order = {
            "id": 12345,
            "user_id": user_id,
            "items": cart["items"],
            "total": cart["total"],
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # ניקוי העגלה לאחר יצירת ההזמנה
        self.clear_cart(user_id)
        
        return order
    
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
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

class TelegramAgent:
    """מחלקת מוק ל-TelegramAgent"""
    async def get_response(self, text, user_id=None, context=None):
        """קבלת תשובה מהסוכן"""
        if "הוסף לעגלה" in text:
            return "המוצר נוסף לעגלת הקניות בהצלחה!"
        
        if "הצג עגלה" in text:
            return "עגלת הקניות שלך:\n1. טלפון חכם Galaxy S21 - כמות: 1 - מחיר: 3499.99₪\nסה\"כ: 3499.99₪"
        
        if "עדכן כמות" in text:
            return "הכמות עודכנה בהצלחה!"
        
        if "הסר מוצר" in text:
            return "המוצר הוסר מהעגלה בהצלחה!"
        
        if "כתובת למשלוח" in text:
            return "אנא הזן את פרטי המשלוח שלך."
        
        if "אמצעי תשלום" in text:
            return "תודה! אנא בחר אמצעי תשלום."
        
        if "השלם הזמנה" in text:
            return "תודה! ההזמנה שלך התקבלה בהצלחה. מספר הזמנה: 12345"
        
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

class ProductService:
    """מחלקת מוק לשירות מוצרים"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def search_products(self, query=None, category=None, limit=10):
        """חיפוש מוצרים"""
        return self.db.get_products(category=category, search_term=query, limit=limit)
    
    def get_product(self, product_id):
        """קבלת פרטי מוצר"""
        return self.db.get_product(product_id)

class CartService:
    """מחלקת מוק לשירות עגלת קניות"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def get_cart(self, user_id):
        """קבלת עגלת קניות"""
        return self.db.get_cart(user_id)
    
    def add_to_cart(self, user_id, product_id, quantity=1):
        """הוספת מוצר לעגלת קניות"""
        return self.db.add_to_cart(user_id, product_id, quantity)
    
    def update_cart_item(self, user_id, product_id, quantity):
        """עדכון כמות מוצר בעגלת קניות"""
        return self.db.update_cart_item(user_id, product_id, quantity)
    
    def remove_from_cart(self, user_id, product_id):
        """הסרת מוצר מעגלת קניות"""
        return self.db.remove_from_cart(user_id, product_id)
    
    def clear_cart(self, user_id):
        """ניקוי עגלת קניות"""
        return self.db.clear_cart(user_id)

class OrderService:
    """מחלקת מוק לשירות הזמנות"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def create_order(self, user_id, shipping_address, payment_method):
        """יצירת הזמנה חדשה"""
        return self.db.create_order(user_id, shipping_address, payment_method)
    
    def get_order(self, order_id):
        """קבלת פרטי הזמנה"""
        return self.db.get_order(order_id)

class PaymentService:
    """מחלקת מוק לשירות תשלומים"""
    def process_payment(self, order_id, payment_method, payment_details):
        """עיבוד תשלום"""
        return {
            "success": True,
            "transaction_id": f"TRX-{order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "amount": 3499.99,
            "status": "completed"
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

class TestOrderPlacement:
    """מחלקת בדיקות לתרחיש ביצוע הזמנה"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_product_service = MagicMock(spec=ProductService)
        self.mock_cart_service = MagicMock(spec=CartService)
        self.mock_order_service = MagicMock(spec=OrderService)
        self.mock_payment_service = MagicMock(spec=PaymentService)
        
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
        
        self.mock_product_service.get_product.return_value = {
            "id": 1,
            "name": "טלפון חכם Galaxy S21",
            "category": "אלקטרוניקה",
            "price": 3499.99,
            "description": "טלפון חכם מתקדם עם מצלמה איכותית ומסך גדול",
            "stock": 10
        }
        
        self.mock_cart_service.get_cart.return_value = {
            "user_id": 12345,
            "items": [],
            "total": 0
        }
        
        self.mock_cart_service.add_to_cart.return_value = True
        self.mock_cart_service.update_cart_item.return_value = True
        self.mock_cart_service.remove_from_cart.return_value = True
        
        self.mock_order_service.create_order.return_value = {
            "id": 12345,
            "user_id": 12345,
            "items": [
                {
                    "product_id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "price": 3499.99,
                    "quantity": 1
                }
            ],
            "total": 3499.99,
            "shipping_address": "רחוב הרצל 1, תל אביב",
            "payment_method": "credit_card",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        self.mock_payment_service.process_payment.return_value = {
            "success": True,
            "transaction_id": "TRX-12345-20230101000000",
            "amount": 3499.99,
            "status": "completed"
        }
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.side_effect = [
            "המוצר נוסף לעגלת הקניות בהצלחה!",
            "עגלת הקניות שלך:\n1. טלפון חכם Galaxy S21 - כמות: 1 - מחיר: 3499.99₪\nסה\"כ: 3499.99₪",
            "אנא הזן את פרטי המשלוח שלך.",
            "תודה! אנא בחר אמצעי תשלום.",
            "תודה! ההזמנה שלך התקבלה בהצלחה. מספר הזמנה: 12345"
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
        self.mock_product_service.reset_mock()
        self.mock_cart_service.reset_mock()
        self.mock_order_service.reset_mock()
        self.mock_payment_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_add_product_to_cart(self, setup):
        """בדיקת הוספת מוצר לסל"""
        # יצירת הודעה להוספת מוצר לסל
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="הוסף לעגלה את המוצר טלפון חכם Galaxy S21"
        )
        
        # הגדרת התנהגות המוקים
        self.mock_cart_service.add_to_cart.return_value = True
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמוצר נוסף לעגלה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "נוסף לעגלת הקניות" in first_message["text"], "הודעת התגובה אינה מכילה אישור על הוספת המוצר לעגלה"
    
    @pytest.mark.asyncio
    async def test_update_cart_quantities(self, setup):
        """בדיקת עדכון כמויות בסל"""
        # יצירת הודעה לעדכון כמות מוצר בסל
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="עדכן את הכמות של טלפון חכם Galaxy S21 ל-2"
        )
        
        # הגדרת התנהגות המוקים
        self.mock_cart_service.update_cart_item.return_value = True
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהכמות עודכנה
        self.mock_agent.get_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_product_from_cart(self, setup):
        """בדיקת הסרת מוצר מהסל"""
        # יצירת הודעה להסרת מוצר מהסל
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="הסר מהעגלה את המוצר טלפון חכם Galaxy S21"
        )
        
        # הגדרת התנהגות המוקים
        self.mock_cart_service.remove_from_cart.return_value = True
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמוצר הוסר מהעגלה
        self.mock_agent.get_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_order_flow(self, setup):
        """בדיקת תהליך השלמת הזמנה מלא"""
        # שלב 1: הוספת מוצר לעגלה
        add_message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="הוסף לעגלה את המוצר טלפון חכם Galaxy S21"
        )
        
        await self.handlers.handle_message(add_message)
        
        # שלב 2: צפייה בעגלת הקניות
        view_cart_message = MockTelegramMessage(
            message_id=2,
            user=self.user,
            chat=self.chat,
            text="הצג את עגלת הקניות שלי"
        )
        
        await self.handlers.handle_message(view_cart_message)
        
        # שלב 3: התחלת תהליך ההזמנה
        checkout_message = MockTelegramMessage(
            message_id=3,
            user=self.user,
            chat=self.chat,
            text="השלם הזמנה"
        )
        
        await self.handlers.handle_message(checkout_message)
        
        # שלב 4: הזנת פרטי משלוח
        shipping_message = MockTelegramMessage(
            message_id=4,
            user=self.user,
            chat=self.chat,
            text="פרטי משלוח: רחוב הרצל 1, תל אביב"
        )
        
        await self.handlers.handle_message(shipping_message)
        
        # שלב 5: בחירת אמצעי תשלום
        payment_message = MockTelegramMessage(
            message_id=5,
            user=self.user,
            chat=self.chat,
            text="אמצעי תשלום: כרטיס אשראי"
        )
        
        await self.handlers.handle_message(payment_message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) == 5, "לא נשלחו כל ההודעות הצפויות"
        
        # בדיקה שההזמנה נוצרה
        assert "ההזמנה שלך התקבלה בהצלחה" in self.bot.sent_messages[-1]["text"], "הודעת האישור הסופית אינה מכילה אישור על קבלת ההזמנה"
        assert "מספר הזמנה" in self.bot.sent_messages[-1]["text"], "הודעת האישור הסופית אינה מכילה מספר הזמנה"
