"""
בדיקות יחידה עבור מודול telegram_bot_documents.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, User as TelegramUser, Message, Chat, Document as TelegramDocument
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler
from sqlalchemy.ext.asyncio import AsyncSession

from src.ui.telegram.core.documents.telegram_bot_documents import TelegramBotDocuments, WAITING_FOR_DOCUMENT, WAITING_FOR_TITLE, WAITING_FOR_SEARCH_QUERY

# פיקסטורות

@pytest.fixture
def mock_bot():
    """מדמה אובייקט הבוט הראשי"""
    return MagicMock()

@pytest.fixture
def documents_handler(mock_bot):
    """יוצר אובייקט TelegramBotDocuments לבדיקות"""
    return TelegramBotDocuments(mock_bot)

@pytest.fixture
def mock_update():
    """מדמה אובייקט Update של טלגרם"""
    mock = MagicMock(spec=Update)
    mock.effective_user = MagicMock(spec=TelegramUser)
    mock.effective_user.id = 123456789
    mock.effective_user.username = "test_user"
    mock.effective_user.first_name = "Test"
    mock.effective_user.last_name = "User"
    
    mock.effective_chat = MagicMock(spec=Chat)
    mock.effective_chat.id = 123456789
    
    mock.message = MagicMock(spec=Message)
    mock.message.text = "test message"
    mock.message.message_id = 1
    mock.message.reply_text = AsyncMock()
    
    return mock

@pytest.fixture
def mock_context():
    """מדמה אובייקט Context של טלגרם"""
    mock = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    mock.bot = MagicMock()
    mock.bot.send_message = AsyncMock()
    mock.user_data = {}
    return mock

@pytest.fixture
def mock_session():
    """מדמה אובייקט Session של SQLAlchemy"""
    mock = AsyncMock(spec=AsyncSession)
    return mock

# בדיקות

@pytest.mark.asyncio
async def test_init(mock_bot):
    """בדיקת אתחול מחלקת המסמכים"""
    # יצירת אובייקט המסמכים
    documents = TelegramBotDocuments(mock_bot)
    
    # בדיקה שהבוט נשמר
    assert documents.bot == mock_bot

def test_get_add_document_handler(documents_handler):
    """בדיקת יצירת handler להוספת מסמך"""
    # קריאה לפונקציה
    handler = documents_handler.get_add_document_handler()
    
    # בדיקות
    assert isinstance(handler, ConversationHandler)
    
    # בדיקת מצבי השיחה
    assert WAITING_FOR_DOCUMENT in handler.states
    assert WAITING_FOR_TITLE in handler.states
    
    # בדיקת נקודות כניסה
    assert len(handler.entry_points) == 1
    assert isinstance(handler.entry_points[0], CommandHandler)
    assert handler.entry_points[0].command == "add_document"

def test_get_search_documents_handler(documents_handler):
    """בדיקת יצירת handler לחיפוש מסמכים"""
    # קריאה לפונקציה
    handler = documents_handler.get_search_documents_handler()
    
    # בדיקות
    assert isinstance(handler, ConversationHandler)
    
    # בדיקת מצבי השיחה
    assert WAITING_FOR_SEARCH_QUERY in handler.states
    
    # בדיקת נקודות כניסה
    assert len(handler.entry_points) == 1
    assert isinstance(handler.entry_points[0], CommandHandler)
    assert handler.entry_points[0].command == "search"

@pytest.mark.asyncio
async def test_add_document_start(documents_handler, mock_update, mock_context):
    """בדיקת התחלת תהליך הוספת מסמך"""
    # קריאה לפונקציה
    result = await documents_handler.add_document_start(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_DOCUMENT
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "מסמך" in call_args
    assert "הוספת" in call_args

@pytest.mark.asyncio
async def test_add_document_receive_text(documents_handler, mock_update, mock_context):
    """בדיקת קבלת מסמך טקסט"""
    # הגדרת הודעת טקסט
    mock_update.message.text = "זהו מסמך לדוגמה"
    
    # קריאה לפונקציה
    result = await documents_handler.add_document_receive(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_TITLE
    assert mock_context.user_data.get("document_content") == "זהו מסמך לדוגמה"
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "כותרת" in call_args

@pytest.mark.asyncio
async def test_add_document_receive_file(documents_handler, mock_update, mock_context):
    """בדיקת קבלת מסמך כקובץ"""
    # הגדרת קובץ
    mock_document = MagicMock(spec=TelegramDocument)
    mock_document.file_id = "test_file_id"
    mock_document.file_name = "test_document.txt"
    mock_update.message.document = mock_document
    mock_update.message.text = None
    
    # מוק לפונקציות של הבוט
    mock_context.bot.get_file = AsyncMock()
    mock_file = AsyncMock()
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"test content"))
    mock_context.bot.get_file.return_value = mock_file
    
    # קריאה לפונקציה
    result = await documents_handler.add_document_receive(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_TITLE
    assert "document_content" in mock_context.user_data
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "כותרת" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.add_document_from_file')
async def test_add_document_title(mock_add_document, mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת הוספת כותרת למסמך"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.return_value = MagicMock()
    mock_add_document.return_value = True
    
    # הגדרת נתוני משתמש
    mock_context.user_data = {
        "document_content": "זהו מסמך לדוגמה"
    }
    mock_update.message.text = "כותרת לדוגמה"
    
    # קריאה לפונקציה
    result = await documents_handler.add_document_title(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_add_document.assert_called_once()
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "נוסף בהצלחה" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.add_document_from_file')
async def test_add_document_title_error(mock_add_document, mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת טיפול בשגיאות בהוספת כותרת למסמך"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.return_value = MagicMock()
    mock_add_document.side_effect = Exception("שגיאת בדיקה")
    
    # הגדרת נתוני משתמש
    mock_context.user_data = {
        "document_content": "זהו מסמך לדוגמה"
    }
    mock_update.message.text = "כותרת לדוגמה"
    
    # קריאה לפונקציה
    result = await documents_handler.add_document_title(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_add_document.assert_called_once()
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "שגיאה" in call_args

@pytest.mark.asyncio
async def test_search_documents_start(documents_handler, mock_update, mock_context):
    """בדיקת התחלת תהליך חיפוש מסמכים"""
    # קריאה לפונקציה
    result = await documents_handler.search_documents_start(mock_update, mock_context)
    
    # בדיקות
    assert result == WAITING_FOR_SEARCH_QUERY
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "חיפוש" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.search_documents')
async def test_search_documents_query(mock_search_documents, mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת חיפוש מסמכים"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.return_value = MagicMock()
    
    # הגדרת תוצאות חיפוש
    mock_document = MagicMock()
    mock_document.title = "מסמך לדוגמה"
    mock_document.content = "תוכן המסמך"
    mock_document.created_at = "2023-01-01"
    mock_search_documents.return_value = [
        (mock_document, 0.95)
    ]
    
    # הגדרת שאילתת חיפוש
    mock_update.message.text = "מילות חיפוש"
    
    # קריאה לפונקציה
    result = await documents_handler.search_documents_query(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_search_documents.assert_called_once_with(mock_session, "מילות חיפוש")
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "תוצאות החיפוש" in call_args
    assert "מסמך לדוגמה" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.search_documents')
async def test_search_documents_query_no_results(mock_search_documents, mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת חיפוש מסמכים ללא תוצאות"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.return_value = MagicMock()
    
    # הגדרת תוצאות חיפוש ריקות
    mock_search_documents.return_value = []
    
    # הגדרת שאילתת חיפוש
    mock_update.message.text = "מילות חיפוש"
    
    # מוק להודעת המתנה
    wait_message = MagicMock()
    wait_message.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = wait_message
    
    # קריאה לפונקציה
    result = await documents_handler.search_documents_query(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_search_documents.assert_called_once_with(mock_session, "מילות חיפוש")
    
    # בדיקת תוכן ההודעה
    call_args = wait_message.edit_text.call_args[0][0]
    assert "לא נמצאו תוצאות" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.search_documents')
async def test_search_documents_query_error(mock_search_documents, mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת טיפול בשגיאות בחיפוש מסמכים"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.return_value = MagicMock()
    
    # הגדרת שגיאה בחיפוש
    mock_search_documents.side_effect = Exception("שגיאת בדיקה")
    
    # הגדרת שאילתת חיפוש
    mock_update.message.text = "מילות חיפוש"
    
    # מוק להודעת המתנה
    wait_message = MagicMock()
    wait_message.edit_text = AsyncMock()
    mock_update.message.reply_text.return_value = wait_message
    
    # קריאה לפונקציה
    result = await documents_handler.search_documents_query(mock_update, mock_context)
    
    # בדיקות
    assert result == ConversationHandler.END
    mock_search_documents.assert_called_once_with(mock_session, "מילות חיפוש")
    
    # בדיקת תוכן ההודעה
    call_args = wait_message.edit_text.call_args[0][0]
    assert "שגיאה" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
async def test_list_documents(mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת רשימת מסמכים"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user
    
    # הגדרת מסמכים למשתמש
    mock_document1 = MagicMock()
    mock_document1.title = "מסמך ראשון"
    mock_document1.created_at = "2023-01-01"
    
    mock_document2 = MagicMock()
    mock_document2.title = "מסמך שני"
    mock_document2.created_at = "2023-01-02"
    
    mock_user.documents = [mock_document1, mock_document2]
    
    # קריאה לפונקציה
    await documents_handler.list_documents(mock_update, mock_context)
    
    # בדיקות
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "רשימת המסמכים" in call_args
    assert "מסמך ראשון" in call_args
    assert "מסמך שני" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
async def test_list_documents_empty(mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת רשימת מסמכים ריקה"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user
    
    # הגדרת משתמש ללא מסמכים
    mock_user.documents = []
    
    # קריאה לפונקציה
    await documents_handler.list_documents(mock_update, mock_context)
    
    # בדיקות
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "לא נמצאו מסמכים" in call_args

@pytest.mark.asyncio
@patch('src.ui.telegram.core.documents.telegram_bot_documents.db.get_session')
@patch('src.ui.telegram.core.documents.telegram_bot_documents.get_user_by_telegram_id')
async def test_list_documents_error(mock_get_user, mock_get_session, documents_handler, mock_update, mock_context, mock_session):
    """בדיקת טיפול בשגיאות בהצגת רשימת מסמכים"""
    # הגדרת מוקים
    mock_get_session.return_value.__aenter__.return_value = mock_session
    mock_get_user.side_effect = Exception("שגיאת בדיקה")
    
    # קריאה לפונקציה
    await documents_handler.list_documents(mock_update, mock_context)
    
    # בדיקות
    mock_get_user.assert_called_once_with(mock_update.effective_user.id, mock_session)
    mock_update.message.reply_text.assert_called_once()
    
    # בדיקת תוכן ההודעה
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "שגיאה" in call_args 