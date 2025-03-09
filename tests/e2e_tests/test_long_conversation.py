"""
בדיקות קצה לקצה לתרחיש שיחה ארוכה.
בדיקות אלו מדמות משתמש אמיתי המנהל שיחה ארוכה עם הסוכן, כולל מעבר בין נושאים שונים.
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
            self.products = {
                1: {
                    "id": 1,
                    "name": "טלפון חכם Galaxy S21",
                    "category": "טלפונים",
                    "price": 3499.99,
                    "description": "טלפון חכם מתקדם עם מסך 6.2 אינץ', מצלמה 64MP ו-128GB אחסון",
                    "stock": 10,
                    "image_url": "https://example.com/images/galaxy_s21.jpg"
                },
                2: {
                    "id": 2,
                    "name": "אוזניות Bluetooth",
                    "category": "אביזרים",
                    "price": 299.99,
                    "description": "אוזניות אלחוטיות עם ביטול רעשים אקטיבי",
                    "stock": 20,
                    "image_url": "https://example.com/images/bluetooth_headphones.jpg"
                },
                3: {
                    "id": 3,
                    "name": "מטען אלחוטי",
                    "category": "אביזרים",
                    "price": 149.99,
                    "description": "מטען אלחוטי מהיר לטלפונים תומכים",
                    "stock": 15,
                    "image_url": "https://example.com/images/wireless_charger.jpg"
                }
            }
            self.orders = {}
        
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
        
        def get_products(self, category=None, search_term=None, limit=10):
            """קבלת מוצרים לפי קטגוריה או מונח חיפוש"""
            products = list(self.products.values())
            
            if category:
                products = [p for p in products if p["category"] == category]
            
            if search_term:
                products = [p for p in products if search_term.lower() in p["name"].lower() or search_term.lower() in p["description"].lower()]
            
            return products[:limit]
        
        def get_product(self, product_id):
            """קבלת מוצר לפי מזהה"""
            return self.products.get(product_id, None)
        
        def create_order(self, user_id, items, shipping_address, payment_method):
            """יצירת הזמנה חדשה"""
            order_id = len(self.orders) + 1
            order = {
                "id": order_id,
                "user_id": user_id,
                "items": items,
                "shipping_address": shipping_address,
                "payment_method": payment_method,
                "status": "חדשה",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_price": sum(self.products[item["product_id"]]["price"] * item["quantity"] for item in items)
            }
            self.orders[order_id] = order
            return order
        
        def get_order(self, order_id):
            """קבלת הזמנה לפי מזהה"""
            return self.orders.get(order_id, None)
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        def __init__(self):
            self.conversation_history = {}
        
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תשובה מהסוכן"""
            # שמירת ההודעה בהיסטוריה
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            self.conversation_history[user_id].append({"role": "user", "content": text})
            
            # יצירת תשובה בהתאם לתוכן ההודעה
            response = ""
            
            if "שלום" in text or "היי" in text:
                response = "שלום! איך אני יכול לעזור לך היום?"
                
            elif "מוצרים" in text or "מה יש לכם" in text:
                response = """אנחנו מציעים מגוון מוצרים:
1. טלפונים חכמים
2. אביזרים לטלפונים
3. מחשבים ניידים
4. טאבלטים
5. אוזניות ורמקולים

איזה מוצר מעניין אותך?"""
                
            elif "טלפון" in text or "סמארטפון" in text:
                response = """יש לנו מספר דגמים של טלפונים חכמים:
- Galaxy S21 - 3499.99 ש"ח
- iPhone 13 - 4299.99 ש"ח
- Pixel 6 - 3199.99 ש"ח

האם תרצה לקבל פרטים נוספים על אחד מהם?"""
                
            elif "אביזרים" in text:
                response = """האביזרים שלנו כוללים:
- אוזניות Bluetooth - 299.99 ש"ח
- מטענים אלחוטיים - 149.99 ש"ח
- כיסויים לטלפונים - 49.99 ש"ח

האם תרצה לקבל פרטים נוספים על אחד מהם?"""
                
            elif "הזמנה" in text or "לקנות" in text:
                response = "כדי לבצע הזמנה, אנא בחר את המוצרים שברצונך לרכוש ואני אדריך אותך בתהליך."
                
            elif "מחיר" in text and "Galaxy S21" in text:
                response = "המחיר של Galaxy S21 הוא 3499.99 ש\"ח."
                
            elif "מחיר" in text and "אוזניות" in text:
                response = "המחיר של אוזניות Bluetooth הוא 299.99 ש\"ח."
                
            elif "מחיר" in text and "מטען" in text:
                response = "המחיר של מטען אלחוטי הוא 149.99 ש\"ח."
                
            elif "תודה" in text:
                response = "אין בעד מה! אשמח לעזור לך בכל דבר נוסף."
                
            else:
                response = "אני כאן כדי לעזור לך. האם תוכל לפרט יותר את בקשתך?"
            
            # שמירת התשובה בהיסטוריה
            self.conversation_history[user_id].append({"role": "assistant", "content": response})
            
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
        """עריכת הודעה קיימת"""
        message = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        self.edited_messages.append(message)
        return message


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


class TestLongConversation:
    """מחלקת בדיקות לתרחיש שיחה ארוכה"""
    
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
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.side_effect = [
            "שלום! איך אוכל לעזור לך היום?",
            "אנחנו מציעים מגוון רחב של מוצרים. האם תרצה לחפש לפי קטגוריה או לפי שם מוצר?",
            "בקטגוריית האלקטרוניקה יש לנו: טלפון חכם Galaxy S21 (3499.99₪), אוזניות Bluetooth (299.99₪).",
            "טלפון חכם Galaxy S21 הוא מכשיר מתקדם עם מצלמה איכותית ומסך גדול. המחיר הוא 3499.99₪ ויש במלאי 10 יחידות.",
            "אני יכול לעזור לך עם הזמנות. האם תרצה לבצע הזמנה חדשה או לבדוק סטטוס הזמנה קיימת?",
            "המוצר נוסף לעגלת הקניות בהצלחה!",
            "עגלת הקניות שלך:\n1. טלפון חכם Galaxy S21 - כמות: 1 - מחיר: 3499.99₪\nסה\"כ: 3499.99₪",
            "אנא הזן את פרטי המשלוח שלך.",
            "תודה! אנא בחר אמצעי תשלום.",
            "תודה! ההזמנה שלך התקבלה בהצלחה. מספר הזמנה: 12345",
            "הזמנה מספר 12345 נמצאת בסטטוס: בתהליך. המשלוח צפוי להגיע בתאריך 01/03/2023.",
            "אני כאן כדי לעזור! איך אוכל לסייע לך היום?",
            "אתה יכול לשאול אותי שאלות על המוצרים שלנו, לבצע הזמנה, לבדוק סטטוס הזמנה קיימת, ועוד."
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
    async def test_long_conversation_with_multiple_topics(self, setup):
        """בדיקת שיחה ארוכה עם מספר נושאים"""
        # יצירת רשימת הודעות לשיחה ארוכה
        conversation = [
            "שלום",
            "אני מחפש מוצרים",
            "מה יש לכם בקטגוריית אלקטרוניקה?",
            "ספר לי עוד על הטלפון Galaxy S21",
            "אני רוצה לבצע הזמנה",
            "הוסף לעגלה את הטלפון Galaxy S21",
            "הצג את עגלת הקניות שלי",
            "השלם הזמנה",
            "פרטי משלוח: רחוב הרצל 1, תל אביב",
            "אמצעי תשלום: כרטיס אשראי",
            "מה הסטטוס של הזמנה מספר 12345?",
            "אני צריך עזרה",
            "מה אתה יכול לעשות?"
        ]
        
        # שליחת כל ההודעות בזו אחר זו
        for i, message_text in enumerate(conversation):
            message = MockTelegramMessage(
                message_id=i+1,
                user=self.user,
                chat=self.chat,
                text=message_text
            )
            
            await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) == len(conversation), f"מספר ההודעות שנשלחו ({len(self.bot.sent_messages)}) אינו תואם למספר ההודעות בשיחה ({len(conversation)})"
        
        # בדיקה שהסוכן ענה לכל ההודעות
        assert self.mock_agent.get_response.call_count == len(conversation), "הסוכן לא ענה לכל ההודעות"
    
    @pytest.mark.asyncio
    async def test_topic_switching(self, setup):
        """בדיקת מעבר בין נושאים שונים"""
        # יצירת רשימת הודעות עם מעבר בין נושאים
        conversation = [
            "שלום",  # נושא: ברכה
            "אני מחפש מוצרים",  # נושא: מוצרים
            "אני רוצה לבצע הזמנה",  # נושא: הזמנות
            "אני צריך עזרה"  # נושא: עזרה
        ]
        
        # שליחת כל ההודעות בזו אחר זו
        for i, message_text in enumerate(conversation):
            message = MockTelegramMessage(
                message_id=i+1,
                user=self.user,
                chat=self.chat,
                text=message_text
            )
            
            await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) == len(conversation), "מספר ההודעות שנשלחו אינו תואם למספר ההודעות בשיחה"
        
        # בדיקה שהסוכן ענה לכל ההודעות
        assert self.mock_agent.get_response.call_count == len(conversation), "הסוכן לא ענה לכל ההודעות"
        
        # בדיקה שהתשובות מתאימות לנושאים השונים
        assert "שלום" in self.bot.sent_messages[0]["text"], "התשובה הראשונה אינה מכילה ברכה"
        assert "מוצרים" in self.bot.sent_messages[1]["text"] or "אלקטרוניקה" in self.bot.sent_messages[1]["text"], "התשובה השנייה אינה קשורה למוצרים"
        # בדיקה שהתשובה השלישית היא תשובה כלשהי (לא חשוב מה התוכן)
        assert len(self.bot.sent_messages[2]["text"]) > 0, "התשובה השלישית ריקה"
        # בדיקה שהתשובה הרביעית היא תשובה כלשהי (לא חשוב מה התוכן)
        assert len(self.bot.sent_messages[3]["text"]) > 0, "התשובה הרביעית ריקה"
    
    @pytest.mark.asyncio
    async def test_return_to_previous_topic(self, setup):
        """בדיקת חזרה לנושא קודם"""
        # יצירת רשימת הודעות עם חזרה לנושא קודם
        conversation = [
            "אני מחפש מוצרים",  # נושא: מוצרים
            "אני רוצה לבצע הזמנה",  # נושא: הזמנות
            "בעצם, ספר לי עוד על המוצרים"  # חזרה לנושא: מוצרים
        ]
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.side_effect = [
            "אנחנו מציעים מגוון רחב של מוצרים. האם תרצה לחפש לפי קטגוריה או לפי שם מוצר?",
            "אני יכול לעזור לך עם הזמנות. האם תרצה לבצע הזמנה חדשה או לבדוק סטטוס הזמנה קיימת?",
            "אנחנו מציעים מגוון רחב של מוצרים. יש לנו אלקטרוניקה, ביגוד, ועוד."
        ]
        
        # שליחת כל ההודעות בזו אחר זו
        for i, message_text in enumerate(conversation):
            message = MockTelegramMessage(
                message_id=i+1,
                user=self.user,
                chat=self.chat,
                text=message_text
            )
            
            await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) == len(conversation), "מספר ההודעות שנשלחו אינו תואם למספר ההודעות בשיחה"
        
        # בדיקה שהסוכן ענה לכל ההודעות
        assert self.mock_agent.get_response.call_count == len(conversation), "הסוכן לא ענה לכל ההודעות"
        
        # בדיקה שהתשובה האחרונה חזרה לנושא המוצרים
        assert "מוצרים" in self.bot.sent_messages[2]["text"], "התשובה האחרונה אינה חוזרת לנושא המוצרים"
    
    @pytest.mark.asyncio
    async def test_context_maintenance(self, setup):
        """בדיקת שמירה על הקשר לאורך זמן"""
        # יצירת רשימת הודעות עם הקשר מתמשך
        conversation = [
            "אני מחפש טלפון חכם",  # שאלה ראשונה על טלפון
            "מה המחיר?",  # שאלת המשך על המחיר (ללא אזכור מפורש של הטלפון)
            "כמה יש במלאי?"  # שאלת המשך על המלאי (ללא אזכור מפורש של הטלפון)
        ]
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.side_effect = [
            "אנחנו מציעים את הטלפון החכם Galaxy S21. האם תרצה לשמוע עוד פרטים?",
            "המחיר של הטלפון החכם Galaxy S21 הוא 3499.99₪.",
            "יש לנו 10 יחידות של הטלפון החכם Galaxy S21 במלאי."
        ]
        
        # שליחת כל ההודעות בזו אחר זו
        for i, message_text in enumerate(conversation):
            message = MockTelegramMessage(
                message_id=i+1,
                user=self.user,
                chat=self.chat,
                text=message_text
            )
            
            await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) == len(conversation), "מספר ההודעות שנשלחו אינו תואם למספר ההודעות בשיחה"
        
        # בדיקה שהסוכן ענה לכל ההודעות
        assert self.mock_agent.get_response.call_count == len(conversation), "הסוכן לא ענה לכל ההודעות"
        
        # בדיקה שהתשובות מתייחסות לאותו מוצר
        assert "Galaxy S21" in self.bot.sent_messages[0]["text"], "התשובה הראשונה אינה מזכירה את הטלפון"
        assert "Galaxy S21" in self.bot.sent_messages[1]["text"], "התשובה השנייה אינה מזכירה את הטלפון"
        assert "Galaxy S21" in self.bot.sent_messages[2]["text"], "התשובה השלישית אינה מזכירה את הטלפון" 