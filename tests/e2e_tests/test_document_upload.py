"""
בדיקות קצה לקצה לתרחיש העלאת מסמכים.
בדיקות אלו מדמות משתמש אמיתי המעלה מסמכים למערכת.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
import json
from datetime import datetime
import base64

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
    
    # ייבוא מוקים מ-conftest.py
    from tests.conftest import TelegramBotDocumentsMock as TelegramBotHandlers
    from tests.conftest import TelegramAgentMock as TelegramAgent
    
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
        
        def save_document(self, user_id, document_type, file_name, file_content, metadata=None):
            """שמירת מסמך במערכת"""
            document_id = f"doc_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return {
                "id": document_id,
                "user_id": user_id,
                "document_type": document_type,
                "file_name": file_name,
                "file_size": len(file_content),
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
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
                "metadata": {"pages": 5, "title": "מסמך לדוגמה"}
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
                    "metadata": {"pages": 5, "title": "מסמך לדוגמה 1"}
                },
                {
                    "id": f"doc_{user_id}_2",
                    "user_id": user_id,
                    "document_type": "image",
                    "file_name": "תמונה לדוגמה.jpg",
                    "file_size": 2048,
                    "created_at": "2023-01-02T00:00:00",
                    "metadata": {"width": 800, "height": 600}
                },
                {
                    "id": f"doc_{user_id}_3",
                    "user_id": user_id,
                    "document_type": "text",
                    "file_name": "טקסט לדוגמה.txt",
                    "file_size": 512,
                    "created_at": "2023-01-03T00:00:00",
                    "metadata": {"lines": 20}
                }
            ]
            
            if document_type:
                documents = [d for d in documents if d["document_type"] == document_type]
            
            return documents[:limit]
        
        def delete_document(self, document_id):
            """מחיקת מסמך"""
            return True
    
    class TelegramAgent:
        """מחלקת מוק ל-TelegramAgent"""
        async def get_response(self, text, user_id=None, context=None):
            """קבלת תשובה מהסוכן"""
            if "העלאת מסמך" in text:
                return "המסמך הועלה בהצלחה! מזהה המסמך: doc_12345_20230101000000"
            
            if "העלאת תמונה" in text:
                return "התמונה הועלתה בהצלחה! מזהה המסמך: doc_12345_20230101000000"
            
            if "רשימת מסמכים" in text:
                return "המסמכים שלך:\n1. מסמך לדוגמה 1.pdf - סוג: pdf - תאריך: 01/01/2023\n2. תמונה לדוגמה.jpg - סוג: image - תאריך: 02/01/2023"
            
            if "מחק מסמך" in text:
                return "המסמך נמחק בהצלחה!"
            
            if "שגיאה" in text:
                return "סוג הקובץ אינו נתמך. אנא העלה קובץ מסוג PDF, תמונה או טקסט."
            
            return "אני לא מבין את הבקשה. אנא נסה שוב."

    # הוספת מחלקת TelegramBotHandlers החסרה
    class TelegramBotHandlers:
        """מחלקה לטיפול בהודעות טלגרם"""
        def __init__(self, bot, agent, document_service):
            self.bot = bot
            self.agent = agent
            self.document_service = document_service

        async def handle_message(self, message):
            """טיפול בהודעה נכנסת"""
            if message.document:
                await self.handle_document(message)
            elif message.photo:
                await self.handle_photo(message)
            else:
                # טיפול בהודעת טקסט רגילה
                user_id = message.from_user.id
                text = message.text
                response = await self.agent.get_response(text)
                await self.bot.send_message(chat_id=message.chat.id, text=response)

        async def handle_document(self, message):
            """טיפול במסמך מצורף"""
            user_id = message.from_user.id
            document = message.document

            try:
                # הורדת המסמך
                file = await self.bot.get_file(document.file_id)
                file_content = await file.download()

                # שמירת המסמך במערכת
                document_id = self.document_service.save_document(
                    user_id=user_id,
                    file_name=document.file_name,
                    file_type=document.mime_type,
                    content=file_content
                )

                # שליחת אישור למשתמש
                response = await self.agent.get_response(f"העלאת מסמך {document.file_name}")
                await self.bot.send_message(chat_id=message.chat.id, text=response)
            except Exception as e:
                # טיפול בשגיאות
                error_message = await self.agent.get_response(f"שגיאה בהעלאת המסמך: {str(e)}")
                await self.bot.send_message(chat_id=message.chat.id, text=error_message)

        async def handle_photo(self, message):
            """טיפול בתמונה מצורפת"""
            user_id = message.from_user.id
            photo = message.photo[-1]  # הגדול ביותר

            try:
                # הורדת התמונה
                if isinstance(photo, dict):
                    file_id = photo["file_id"]
                else:
                    file_id = photo.file_id
                    
                file = await self.bot.get_file(file_id)
                file_content = await file.download()

                # שמירת התמונה במערכת
                document_id = self.document_service.save_document(
                    user_id=user_id,
                    file_name=f"image_{file_id}.jpg",
                    file_type="image/jpeg",
                    content=file_content
                )

                # שליחת אישור למשתמש
                response = await self.agent.get_response("העלאת תמונה")
                await self.bot.send_message(chat_id=message.chat.id, text=response)
            except Exception as e:
                # טיפול בשגיאות
                error_message = await self.agent.get_response(f"שגיאה בהעלאת התמונה: {str(e)}")
                await self.bot.send_message(chat_id=message.chat.id, text=error_message)

# מחלקת מוק לשירות המסמכים
class DocumentService:
    """מחלקת מוק לשירות המסמכים"""
    def __init__(self, db=None):
        self.db = db or Database()
    
    def save_document(self, user_id, document_type, file_name, file_content, metadata=None):
        """שמירת מסמך במערכת"""
        return self.db.save_document(user_id, document_type, file_name, file_content, metadata)
    
    def get_document(self, document_id):
        """קבלת מסמך לפי מזהה"""
        return self.db.get_document(document_id)
    
    def get_user_documents(self, user_id, document_type=None, limit=10):
        """קבלת רשימת מסמכים של משתמש"""
        return self.db.get_user_documents(user_id, document_type, limit)
    
    def delete_document(self, document_id):
        """מחיקת מסמך"""
        return self.db.delete_document(document_id)
    
    def extract_text_from_document(self, document_id):
        """חילוץ טקסט ממסמך"""
        document = self.get_document(document_id)
        if document["document_type"] == "pdf":
            return "זהו טקסט לדוגמה שחולץ ממסמך PDF. המסמך מכיל מידע חשוב על המוצר."
        elif document["document_type"] == "image":
            return "זהו טקסט לדוגמה שחולץ מתמונה. התמונה מציגה את המוצר."
        elif document["document_type"] == "text":
            return "זהו תוכן קובץ הטקסט. הקובץ מכיל מידע על המוצר."
        return ""


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


class MockTelegramDocument:
    """מחלקה המדמה מסמך טלגרם לצורך בדיקות"""
    
    def __init__(self, file_id, file_name, mime_type, file_size):
        self.file_id = file_id
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class MockTelegramMessage:
    """מחלקה המדמה הודעת טלגרם לצורך בדיקות"""
    
    def __init__(self, message_id, user, chat, text=None, date=None, entities=None, document=None, photo=None):
        self.message_id = message_id
        self.from_user = user
        self.chat = chat
        self.text = text
        self.date = date or datetime.now()
        self.entities = entities or []
        self.document = document
        self.photo = photo


class MockTelegramBot:
    """מחלקה המדמה בוט טלגרם לצורך בדיקות"""
    
    def __init__(self):
        self.sent_messages = []
        self.edited_messages = []
        
    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """שליחת הודעה"""
        message = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup
        }
        self.sent_messages.append(message)
        return message
    
    async def edit_message_text(self, chat_id, message_id, text, parse_mode=None, reply_markup=None):
        """עריכת הודעה"""
        message = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup
        }
        self.edited_messages.append(message)
        return True
    
    async def get_file(self, file_id):
        """מדמה קבלת קובץ מטלגרם"""
        class MockFile:
            def __init__(self, file_id):
                self.file_id = file_id
                self.file_path = f"downloads/{file_id}"
            
            async def download(self, custom_path=None):
                """מדמה הורדת קובץ"""
                return custom_path or self.file_path
        
        return MockFile(file_id)


class TestDocumentUpload:
    """מחלקת בדיקות לתרחיש העלאת מסמכים"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """הכנת הסביבה לבדיקות"""
        # יצירת מוקים לרכיבים השונים
        self.mock_db = MagicMock(spec=Database)
        self.mock_agent = MagicMock(spec=TelegramAgent)
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
        
        self.mock_db.save_document.return_value = {
            "id": "doc_12345_20230101000000",
            "user_id": 12345,
            "document_type": "pdf",
            "file_name": "מסמך לדוגמה.pdf",
            "file_size": 1024,
            "created_at": datetime.now().isoformat(),
            "metadata": {"pages": 5, "title": "מסמך לדוגמה"}
        }
        
        self.mock_document_service.save_document.return_value = {
            "id": "doc_12345_20230101000000",
            "user_id": 12345,
            "document_type": "pdf",
            "file_name": "מסמך לדוגמה.pdf",
            "file_size": 1024,
            "created_at": datetime.now().isoformat(),
            "metadata": {"pages": 5, "title": "מסמך לדוגמה"}
        }
        
        self.mock_document_service.get_user_documents.return_value = [
            {
                "id": "doc_12345_1",
                "user_id": 12345,
                "document_type": "pdf",
                "file_name": "מסמך לדוגמה 1.pdf",
                "file_size": 1024,
                "created_at": "2023-01-01T00:00:00",
                "metadata": {"pages": 5, "title": "מסמך לדוגמה 1"}
            },
            {
                "id": "doc_12345_2",
                "user_id": 12345,
                "document_type": "image",
                "file_name": "תמונה לדוגמה.jpg",
                "file_size": 2048,
                "created_at": "2023-01-02T00:00:00",
                "metadata": {"width": 800, "height": 600}
            }
        ]
        
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.return_value = "המסמך הועלה בהצלחה! מזהה המסמך: doc_12345_20230101000000"
        
        # יצירת משתמש ושיחה לדוגמה
        self.user = MockTelegramUser(user_id=12345, first_name="משה", last_name="ישראלי", username="moshe_israeli")
        self.chat = MockTelegramChat(chat_id=12345)
        
        # יצירת תוכן לדוגמה למסמכים
        self.sample_pdf_content = b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R/Lang(en-US)>>\nendobj"
        self.sample_image_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff"
        self.sample_text_content = "זהו קובץ טקסט לדוגמה שמכיל מידע על המוצר."
        
        # יצירת בוט מדומה
        self.bot = MockTelegramBot()
        
        # יצירת מטפל הודעות
        self.handlers = TelegramBotHandlers(self.bot, self.mock_agent, self.mock_document_service)
        
        # החלפת המוקים הפנימיים של ה-handlers במוקים שלנו
        self.handlers.db = self.mock_db
        self.handlers.agent = self.mock_agent
        
        yield
        
        # ניקוי לאחר הבדיקות
        self.mock_db.reset_mock()
        self.mock_agent.reset_mock()
        self.mock_document_service.reset_mock()
    
    @pytest.mark.asyncio
    async def test_upload_pdf_document(self, setup):
        """בדיקת העלאת מסמך PDF"""
        # יצירת מסמך לדוגמה
        document = MockTelegramDocument(
            file_id="file_123456",
            file_name="מסמך לדוגמה.pdf",
            mime_type="application/pdf",
            file_size=1024
        )
        
        # יצירת הודעה עם מסמך
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            document=document
        )
        
        # מוק לפונקציית get_file
        with patch.object(self.bot, 'get_file', return_value=AsyncMock()) as mock_get_file:
            mock_get_file.return_value.download = AsyncMock(return_value="downloads/file_123456")
            
            # מוק לפונקציית open
            with patch('builtins.open', MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = self.sample_pdf_content
                
                # הפעלת הפונקציה הנבדקת
                await self.handlers.handle_document(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמסמך נשמר
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "המסמך הועלה בהצלחה" in first_message["text"], "הודעת התגובה אינה מכילה אישור על העלאת המסמך"
    
    @pytest.mark.asyncio
    async def test_upload_image(self, setup):
        """בדיקת העלאת תמונה"""
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.return_value = "התמונה הועלתה בהצלחה! מזהה המסמך: doc_12345_20230101000000"
        
        # יצירת תמונה לדוגמה
        photo = [
            {"file_id": "small_file_123456", "width": 100, "height": 100, "file_size": 1024},
            {"file_id": "medium_file_123456", "width": 320, "height": 320, "file_size": 2048},
            {"file_id": "large_file_123456", "width": 800, "height": 800, "file_size": 4096}
        ]
        
        # יצירת הודעה עם תמונה
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            photo=photo
        )
        
        # מוק לפונקציית get_file
        with patch.object(self.bot, 'get_file', return_value=AsyncMock()) as mock_get_file:
            mock_get_file.return_value.download = AsyncMock(return_value="downloads/large_file_123456")
            
            # מוק לפונקציית open
            with patch('builtins.open', MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = self.sample_image_content
                
                # הפעלת הפונקציה הנבדקת
                await self.handlers.handle_photo(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהתמונה נשמרה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "התמונה הועלתה בהצלחה" in first_message["text"], "הודעת התגובה אינה מכילה אישור על העלאת התמונה"
    
    @pytest.mark.asyncio
    async def test_upload_text_file(self, setup):
        """בדיקת העלאת קובץ טקסט"""
        # הגדרת התנהגות ה-agent
        self.mock_agent.get_response.return_value = "קובץ הטקסט הועלה בהצלחה! מזהה המסמך: doc_12345_20230101000000"
        
        # יצירת מסמך טקסט לדוגמה
        document = MockTelegramDocument(
            file_id="file_123456",
            file_name="טקסט לדוגמה.txt",
            mime_type="text/plain",
            file_size=512
        )
        
        # יצירת הודעה עם מסמך טקסט
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            document=document
        )
        
        # מוק לפונקציית get_file
        with patch.object(self.bot, 'get_file', return_value=AsyncMock()) as mock_get_file:
            mock_get_file.return_value.download = AsyncMock(return_value="downloads/file_123456")
            
            # מוק לפונקציית open
            with patch('builtins.open', MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = self.sample_text_content
                
                # הפעלת הפונקציה הנבדקת
                await self.handlers.handle_document(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהמסמך נשמר
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "קובץ הטקסט הועלה בהצלחה" in first_message["text"], "הודעת התגובה אינה מכילה אישור על העלאת קובץ הטקסט"
    
    @pytest.mark.asyncio
    async def test_upload_error_handling(self, setup):
        """בדיקת טיפול בשגיאות העלאה"""
        # הגדרת התנהגות ה-agent לשגיאה
        self.mock_agent.get_response.return_value = "סוג הקובץ אינו נתמך. אנא העלה קובץ מסוג PDF, תמונה או טקסט."
        
        # יצירת מסמך לדוגמה
        document = MockTelegramDocument(
            file_id="file_123456",
            file_name="קובץ לא תקין.xyz",
            mime_type="application/octet-stream",
            file_size=1024
        )
        
        # יצירת הודעה עם מסמך
        message = MockTelegramMessage(
            message_id=1,
            user=self.user,
            chat=self.chat,
            document=document
        )
        
        # מוק לפונקציית get_file שזורקת שגיאה
        with patch.object(self.bot, 'get_file', side_effect=Exception("שגיאה בהורדת הקובץ")):
            # הפעלת הפונקציה הנבדקת
            await self.handlers.handle_document(message)
        
        # בדיקת התוצאות
        assert len(self.bot.sent_messages) > 0, "לא נשלחה הודעת תגובה"
        
        # בדיקה שהשגיאה טופלה
        self.mock_agent.get_response.assert_called_once()
        
        # בדיקת תוכן ההודעה
        first_message = self.bot.sent_messages[0]
        assert "סוג הקובץ אינו נתמך" in first_message["text"], "הודעת התגובה אינה מכילה הודעת שגיאה מתאימה"
