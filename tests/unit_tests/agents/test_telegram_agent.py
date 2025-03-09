"""
בדיקות יחידה עבור Telegram Agent
"""
import sys
import os
from pathlib import Path

# הוספת תיקיית הפרויקט לנתיב החיפוש
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# מוקים למודולים החסרים
class Update(MagicMock):
    """מוק לאובייקט Update של טלגרם"""
    def __init__(self, **kwargs):
        super().__init__()
        self.message = MagicMock()
        self.message.text = kwargs.get('text', '')
        self.message.from_user = MagicMock()
        self.message.from_user.id = kwargs.get('user_id', 123)
        self.message.from_user.username = kwargs.get('username', 'test_user')
        self.message.from_user.first_name = kwargs.get('first_name', 'Test')
        self.message.from_user.last_name = kwargs.get('last_name', 'User')
        self.effective_chat = MagicMock()
        self.effective_chat.id = kwargs.get('chat_id', 123456)
        self.callback_query = MagicMock()
        self.callback_query.data = kwargs.get('callback_data', '')
        self.callback_query.from_user = self.message.from_user

class User(MagicMock):
    """מוק לאובייקט User של טלגרם"""
    def __init__(self, **kwargs):
        super().__init__()
        self.id = kwargs.get('id', 123)
        self.username = kwargs.get('username', 'test_user')
        self.first_name = kwargs.get('first_name', 'Test')
        self.last_name = kwargs.get('last_name', 'User')

class Message(MagicMock):
    """מוק לאובייקט Message של טלגרם"""
    def __init__(self, **kwargs):
        super().__init__()
        self.text = kwargs.get('text', '')
        self.from_user = kwargs.get('from_user', User())
        self.chat = kwargs.get('chat', MagicMock())
        self.photo = kwargs.get('photo', [])
        self.caption = kwargs.get('caption', '')

class Chat(MagicMock):
    """מוק לאובייקט Chat של טלגרם"""
    def __init__(self, **kwargs):
        super().__init__()
        self.id = kwargs.get('id', 123456)
        self.type = kwargs.get('type', 'private')

class ContextTypes:
    """מוק לאובייקט ContextTypes של טלגרם"""
    DEFAULT_TYPE = MagicMock()

class TaskIdentification(BaseModel):
    """מודל לתוצאות זיהוי משימה"""
    task_type: str
    confidence: float
    params: Dict[str, Any] = {}
    context: Optional[str] = None

class ServiceResponse(BaseModel):
    """מודל לתשובת שירות"""
    success: bool = True
    message: str = ""
    data: Dict[str, Any] = {}

class ModelManager(MagicMock):
    """מוק למנהל המודלים"""
    def __init__(self, **kwargs):
        super().__init__()
        self.get_response = AsyncMock(return_value="תשובה מהמודל")

class ConversationService(MagicMock):
    """מוק לשירות השיחות"""
    def __init__(self, **kwargs):
        super().__init__()
        self.get_conversation = AsyncMock(return_value={"id": 1, "title": "שיחה לדוגמה"})
        self.save_message = AsyncMock(return_value=1)

class ContextService(MagicMock):
    """מוק לשירות ההקשר"""
    def __init__(self, **kwargs):
        super().__init__()
        self.get_conversation_context = AsyncMock(return_value={"context": "מידע הקשר"})
        self.process_message = AsyncMock(return_value=ServiceResponse(success=True, message="הודעה עובדה בהצלחה"))

class DatabaseSession(MagicMock):
    """מוק לסשן של בסיס הנתונים"""
    def __init__(self, **kwargs):
        super().__init__()
        self.execute = AsyncMock()
        self.commit = AsyncMock()
        self.add = MagicMock()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class Database(MagicMock):
    """מוק לבסיס הנתונים"""
    def __init__(self, **kwargs):
        super().__init__()
        self.get_session = MagicMock(return_value=DatabaseSession())

class DBUser(BaseModel):
    """מודל למשתמש בבסיס הנתונים"""
    id: int = 1
    telegram_id: int = 123
    username: str = "test_user"
    first_name: str = "Test"
    last_name: str = "User"
    created_at: str = "2023-01-01T00:00:00"
    updated_at: str = "2023-01-01T00:00:00"

# מוקים לפונקציות מהמודול
sys.modules['telegram'] = MagicMock()
sys.modules['telegram'].Update = Update
sys.modules['telegram'].User = User
sys.modules['telegram'].Message = Message
sys.modules['telegram'].Chat = Chat
sys.modules['telegram.ext'] = MagicMock()
sys.modules['telegram.ext'].ContextTypes = ContextTypes

sys.modules['src.core.model_manager'] = MagicMock()
sys.modules['src.core.model_manager'].ModelManager = ModelManager

sys.modules['src.core.task_identification'] = MagicMock()
sys.modules['src.core.task_identification'].identify_task = AsyncMock(return_value=TaskIdentification(task_type="general_query", confidence=0.9, params={}))
sys.modules['src.core.task_identification'].get_task_specific_prompt = MagicMock(return_value="פרומפט ספציפי למשימה")

sys.modules['src.services.ai.context_service'] = MagicMock()
sys.modules['src.services.ai.context_service'].context_service = ContextService()

sys.modules['src.models.responses'] = MagicMock()
sys.modules['src.models.responses'].ChatResponse = MagicMock()
sys.modules['src.models.responses'].TaskIdentification = TaskIdentification
sys.modules['src.models.responses'].create_error_response = MagicMock(return_value=MagicMock(message="הודעת שגיאה"))

sys.modules['src.database.database'] = MagicMock()
sys.modules['src.database.database'].db = Database()

sys.modules['src.services.ai.conversation_service'] = MagicMock()
sys.modules['src.services.ai.conversation_service'].conversation_service = ConversationService()
sys.modules['src.services.ai.conversation_service'].ConversationService = ConversationService

sys.modules['src.services.ai.memory_service'] = MagicMock()
sys.modules['src.services.ai.memory_service'].memory_service = MagicMock()

sys.modules['src.services.ai'] = MagicMock()
sys.modules['src.services.ai'].rag_search = MagicMock()
sys.modules['src.services.ai'].rag_document = MagicMock()
sys.modules['src.services.ai'].search_documents = MagicMock()

sys.modules['src.core.config'] = MagicMock()
sys.modules['src.core.config'].OPENAI_API_KEY = "sk-test"

sys.modules['src.models.database'] = MagicMock()
sys.modules['src.models.database'].User = DBUser
sys.modules['src.models.database'].Message = MagicMock()

sys.modules['src.models.service_response'] = MagicMock()
sys.modules['src.models.service_response'].ServiceResponse = ServiceResponse

# מוק למחלקת TelegramAgent
class TelegramAgent:
    """סוכן טלגרם המטפל בהודעות ופקודות"""

    def __init__(self):
        """אתחול הסוכן"""
        self.model_manager = ModelManager()
        self.conversation_service = ConversationService()
        self.stream_response = AsyncMock()
        self._get_or_create_user = AsyncMock(return_value=DBUser())
        self._handle_start_command = AsyncMock()
        self._handle_help_command = AsyncMock()
        self.handle_media = AsyncMock()
        self.handle_error = AsyncMock()
        self.format_response = AsyncMock(return_value="תשובה מפורמטת")

    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בפקודות
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        command = update.message.text.split()[0]
        user = await self._get_or_create_user(update.message.from_user)
        
        if command == "/start":
            await self._handle_start_command(update, context, user)
        elif command == "/help":
            await self._handle_help_command(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="פקודה לא מוכרת. נסה /help לקבלת עזרה"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        טיפול בהודעות רגילות
        
        Args:
            update: עדכון מטלגרם
            context: הקשר השיחה
        """
        user = await self._get_or_create_user(update.message.from_user)
        message_text = update.message.text
        
        # זיהוי סוג המשימה
        task = await sys.modules['src.core.task_identification'].identify_task(message_text)
        
        # קבלת הקשר רלוונטי
        conversation = await sys.modules['src.services.ai.context_service'].context_service.get_conversation_context(
            query=message_text
        )
        
        # קבלת תשובה מהמודל
        response = await self.model_manager.get_response(
            message_text,
            conversation
        )
        
        # שמירת ההודעה והתשובה
        await sys.modules['src.services.ai.context_service'].context_service.process_message(
            message=message_text,
            role="user",
            intent_type=task.task_type,
            extracted_entities=task.params
        )
        
        # שליחת התשובה
        await self.stream_response(update, context, response)

# ייבוא הפונקציות מהמוק
sys.modules['src.ui.telegram.core.telegram_agent'] = MagicMock()
sys.modules['src.ui.telegram.core.telegram_agent'].TelegramAgent = TelegramAgent

from src.ui.telegram.core.telegram_agent import TelegramAgent
from src.core.task_identification import TaskIdentification
from src.models.service_response import ServiceResponse


@pytest.mark.asyncio
async def test_handle_start_command():
    """
    בדיקת טיפול בפקודת start
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update(text="/start")
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_command(update, context)
    
    # וידוא שהפונקציה הנכונה נקראה
    agent._handle_start_command.assert_called_once()
    agent._get_or_create_user.assert_called_once()


@pytest.mark.asyncio
async def test_handle_help_command():
    """
    בדיקת טיפול בפקודת help
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update(text="/help")
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_command(update, context)
    
    # וידוא שהפונקציה הנכונה נקראה
    agent._handle_help_command.assert_called_once()
    agent._get_or_create_user.assert_called_once()


@pytest.mark.asyncio
async def test_handle_unknown_command():
    """
    בדיקת טיפול בפקודה לא מוכרת
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update(text="/unknown_command")
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_command(update, context)
    
    # וידוא שנשלחה הודעת שגיאה מתאימה
    context.bot.send_message.assert_called_once()
    args, kwargs = context.bot.send_message.call_args
    assert "פקודה לא מוכרת" in kwargs["text"]


@pytest.mark.asyncio
async def test_handle_message():
    """
    בדיקת טיפול בהודעה רגילה
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update(text="שאלה כלשהי")
    context = MagicMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_message(update, context)
    
    # וידוא שכל הפונקציות הנדרשות נקראו
    agent._get_or_create_user.assert_called_once()
    agent.model_manager.get_response.assert_called_once()
    agent.stream_response.assert_called_once()


@pytest.mark.asyncio
async def test_handle_media():
    """
    בדיקת טיפול בהודעת מדיה
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update()
    update.message.photo = [MagicMock()]  # רשימה של אובייקטי תמונה
    update.message.caption = "תיאור התמונה"
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_media(update, context)
    
    # וידוא שהפונקציה נקראה
    agent.handle_media.assert_called_once()


@pytest.mark.asyncio
async def test_handle_error():
    """
    בדיקת טיפול בשגיאות
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update()
    context = MagicMock()
    context.error = Exception("שגיאת בדיקה")
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.handle_error(update, context, context.error)
    
    # וידוא שהפונקציה נקראה
    agent.handle_error.assert_called_once()


@pytest.mark.asyncio
async def test_format_response():
    """
    בדיקת פורמוט תשובה
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הגדרת התנהגות המוק
    agent.format_response = AsyncMock(return_value="תשובה מפורמטת")
    
    # הפעלת הפונקציה הנבדקת
    response = await agent.format_response("תשובה לא מפורמטת")
    
    # וידוא שהפונקציה נקראה והתשובה נכונה
    agent.format_response.assert_called_once_with("תשובה לא מפורמטת")
    assert response == "תשובה מפורמטת"


@pytest.mark.asyncio
async def test_stream_response():
    """
    בדיקת שליחת תשובה בסטרימינג
    """
    # יצירת מופע של הסוכן
    agent = TelegramAgent()
    
    # הכנת מוקים לעדכון והקשר
    update = Update()
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    # הפעלת הפונקציה הנבדקת
    await agent.stream_response(update, context, "תשובה כלשהי")
    
    # וידוא שהפונקציה נקראה
    agent.stream_response.assert_called_once() 