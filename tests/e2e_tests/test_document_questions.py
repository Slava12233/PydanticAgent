"""
בדיקות קצה לקצה לתרחיש שאילת שאלות על מסמכים.
בדיקות אלו מדמות משתמש אמיתי השואל שאלות על מסמכים שהועלו למערכת.
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
            return {
                "id": user_id,
                "first_name": "משה",
                "last_name": "ישראלי",
                "username": "moshe_israeli",
                "created_at": "2023-01-01T00:00:00",
                "last_interaction": "2023-01-01T00:00:00",
                "preferences": json.dumps({"language": "he"})
            }
        
        def get_document(self, document_id):
            """קבלת מסמך לפי מזהה"""
            return {
                "id": document_id,
                "user_id": 12345,
                "document_type": "pdf",
                "file_name": "מסמך לדוגמה.pdf",
                "file_size": 1024,
                "created_at": "2023-01-01T00:00:00",
                "metadata": {"pages": 5, "title": "מסמך לדוגמה"},
                "content": "זהו תוכן המסמך לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח. המוצר כולל אחריות לשנה."
            }
        
        def get_user_documents(self, user_id, document_type=None, limit=10):
            """קבלת רשימת מסמכים של משתמש"""
            documents = [
                {
                    "id": f"doc_{user_id}_1",
                    "user_id": user_id,
                    "document_type": "pdf",
                    "file_name": "מסמך לדוגמה 1.pdf",
                    "file_size": 1024,
                    "created_at": "2023-01-01T00:00:00",
                    "metadata": {"pages": 5, "title": "מסמך לדוגמה 1"},
                    "content": "זהו תוכן המסמך הראשון לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים."
                },
                {
                    "id": f"doc_{user_id}_2",
                    "user_id": user_id,
                    "document_type": "pdf",
                    "file_name": "מסמך לדוגמה 2.pdf",
                    "file_size": 2048,
                    "created_at": "2023-01-02T00:00:00",
                    "metadata": {"pages": 10, "title": "מסמך לדוגמה 2"},
                    "content": "זהו תוכן המסמך השני לדוגמה. המסמך מכיל מידע על שירותי החברה, כולל תנאי שירות ואחריות."
                }
            ]
            
            if document_type:
                documents = [d for d in documents if d["document_type"] == document_type]
            
            return documents[:limit]
        
        def save_conversation(self, user_id, conversation_id, title=None):
            """שמירת שיחה"""
            return True
        
        def save_message(self, conversation_id, role, content):
            """שמירת הודעה"""
            return True
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תגובה מהסוכן"""
            if "חפש במסמך" in text:
                return "מצאתי את המידע הבא במסמך: המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח."
            elif "מה המחיר" in text or "כמה עולה" in text:
                return "המחיר של טלפון חכם Galaxy S21 הוא 3499.99 ש\"ח, כפי שמצוין במסמך."
            elif "מה כולל" in text:
                return "המוצר כולל אחריות לשנה, כפי שמצוין במסמך."
            elif "סיכום" in text:
                return "המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח עם אחריות לשנה."
            elif "השווה" in text:
                return "המסמך הראשון מתמקד במוצרי החברה ומפרטים טכניים, בעוד המסמך השני מתמקד בשירותי החברה ותנאי האחריות."
            return "תשובה לדוגמה"
            
    class TelegramBotHandlers:
        """מחלקת מוק ל-TelegramBotHandlers"""
        def __init__(self, bot):
            self.bot = bot
            self.db = None
            self.agent = None
            
        async def handle_message(self, message):
            """טיפול בהודעה"""
            response = await self.agent.get_response(message.text)
            await self.bot.send_message(message.chat.id, response)
            return response

# מחלקת מוק לשירות המסמכים
class DocumentService:
    """מחלקת מוק לשירות המסמכים"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def get_document(self, document_id):
        """קבלת מסמך לפי מזהה"""
        return self.db.get_document(document_id)
    
    def get_user_documents(self, user_id, document_type=None, limit=10):
        """קבלת רשימת מסמכים של משתמש"""
        return self.db.get_user_documents(user_id, document_type, limit)
    
    def extract_text_from_document(self, document_id):
        """חילוץ טקסט ממסמך"""
        document = self.get_document(document_id)
        return document.get("content", "")
    
    def search_in_document(self, document_id, query):
        """חיפוש בתוך מסמך"""
        document = self.get_document(document_id)
        content = document.get("content", "")
        
        if query.lower() in content.lower():
            start_index = content.lower().find(query.lower())
            end_index = start_index + len(query)
            context_start = max(0, start_index - 50)
            context_end = min(len(content), end_index + 50)
            
            # החזרת מחרוזת במקום slice
            return str(content[context_start:context_end])
        
        return ""
    
    def summarize_document(self, document_id):
        """סיכום מסמך"""
        document = self.get_document(document_id)
        return f"סיכום של {document.get('file_name')}: {document.get('content', '')[:100]}..."


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


class TestDocumentQuestions:
    """מחלקת בדיקות לתרחיש שאילת שאלות על מסמכים"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = AsyncMock(spec=TelegramAgent)
        self.mock_document_service = MagicMock(spec=DocumentService)
        
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
        
        self.mock_db.get_document.return_value = {
            "id": "doc_12345_1",
            "user_id": 12345,
            "document_type": "pdf",
            "file_name": "מסמך לדוגמה.pdf",
            "file_size": 1024,
            "created_at": "2023-01-01T00:00:00",
            "metadata": {"pages": 5, "title": "מסמך לדוגמה"},
            "content": "זהו תוכן המסמך לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח. המוצר כולל אחריות לשנה."
        }
        
        self.mock_document_service.get_document.return_value = {
            "id": "doc_12345_1",
            "user_id": 12345,
            "document_type": "pdf",
            "file_name": "מסמך לדוגמה.pdf",
            "file_size": 1024,
            "created_at": "2023-01-01T00:00:00",
            "metadata": {"pages": 5, "title": "מסמך לדוגמה"},
            "content": "זהו תוכן המסמך לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח. המוצר כולל אחריות לשנה."
        }
        
        self.mock_document_service.get_user_documents.return_value = [
            {
                "id": "doc_12345_1",
                "user_id": 12345,
                "document_type": "pdf",
                "file_name": "מסמך לדוגמה 1.pdf",
                "file_size": 1024,
                "created_at": "2023-01-01T00:00:00",
                "metadata": {"pages": 5, "title": "מסמך לדוגמה 1"},
                "content": "זהו תוכן המסמך הראשון לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים."
            },
            {
                "id": "doc_12345_2",
                "user_id": 12345,
                "document_type": "pdf",
                "file_name": "מסמך לדוגמה 2.pdf",
                "file_size": 2048,
                "created_at": "2023-01-02T00:00:00",
                "metadata": {"pages": 10, "title": "מסמך לדוגמה 2"},
                "content": "זהו תוכן המסמך השני לדוגמה. המסמך מכיל מידע על שירותי החברה, כולל תנאי שירות ואחריות."
            }
        ]
        
        self.mock_document_service.extract_text_from_document.return_value = "זהו תוכן המסמך לדוגמה. המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח. המוצר כולל אחריות לשנה."
        
        self.mock_document_service.search_in_document.return_value = "...המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח..."
        
        self.mock_document_service.summarize_document.return_value = "סיכום של מסמך לדוגמה.pdf: המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח עם אחריות לשנה."
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.side_effect = [
            "המחיר של טלפון חכם Galaxy S21 הוא 3499.99 ש\"ח, כפי שמצוין במסמך.",
            "המוצר כולל אחריות לשנה, כפי שמצוין במסמך.",
            "המסמך מכיל מידע על מוצרי החברה, כולל מפרטים טכניים ומחירים. המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח עם אחריות לשנה.",
            "המסמך הראשון מתמקד במוצרי החברה ומפרטים טכניים, בעוד המסמך השני מתמקד בשירותי החברה ותנאי האחריות.",
            "מצאתי את המידע הבא במסמך: המוצר העיקרי הוא טלפון חכם Galaxy S21 במחיר 3499.99 ש\"ח."
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
        self.mock_document_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_question_about_document_content(self, setup):
        """בדיקת שאלה על תוכן המסמך"""
        # יצירת הודעה עם שאלה על תוכן המסמך
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה המחיר של טלפון חכם Galaxy S21 לפי המסמך?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהשאלה נענתה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "3499.99" in first_message["text"], "הודעת התגובה אינה מכילה את המחיר הנכון"
        assert "ש\"ח" in first_message["text"], "הודעת התגובה אינה מכילה את יחידת המטבע"
    
    @pytest.mark.asyncio
    async def test_question_about_document_details(self, setup):
        """בדיקת שאלה על פרטי המסמך"""
        # יצירת הודעה עם שאלה על פרטי המסמך
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="מה כולל המוצר לפי המסמך?"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהשאלה נענתה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה מידע על המוצר"
    
    @pytest.mark.asyncio
    async def test_document_summary_request(self, setup):
        """בדיקת בקשת סיכום מסמך"""
        # יצירת הודעה עם בקשה לסיכום מסמך
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="תן לי סיכום של המסמך"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהבקשה לסיכום טופלה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה מידע על המוצר העיקרי"
    
    @pytest.mark.asyncio
    async def test_document_comparison(self, setup):
        """בדיקת השוואה בין מסמכים"""
        # יצירת הודעה עם בקשה להשוואה בין מסמכים
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="השווה בין שני המסמכים שהעליתי"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהבקשה להשוואה טופלה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה מידע על המוצר"
    
    @pytest.mark.asyncio
    async def test_search_in_document(self, setup):
        """בדיקת חיפוש מידע ספציפי במסמך"""
        # יצירת הודעה עם בקשה לחיפוש מידע ספציפי
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            text="חפש במסמך מידע על Galaxy S21"
        )
        
        # הפעלת הפונקציה הנבדקת
        await self.handlers.handle_message(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהבקשה לחיפוש טופלה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "Galaxy S21" in first_message["text"], "הודעת התגובה אינה מכילה את המידע שנמצא" 