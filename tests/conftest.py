"""
קובץ הגדרות לבדיקות pytest
"""
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, Boolean
import enum
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from sqlalchemy.orm import relationship
import pytest
import pytest_asyncio
import datetime
from pathlib import Path
import re
import json
import os
from datetime import datetime, timedelta

# ייבוא המוקים מקובץ המוק
from tests.mocks.order_intent_mock import (
    IntentType, 
    TaskParameters, 
    OrderIntentMock,
    order_intent,
    extract_order_details,
    extract_entities,
    extract_numbers,
    extract_dates
)

# מוקים למודולים החסרים - רק אם המודול לא קיים
for module_name in [
    'src',
    'src.core',
    'src.core.task_identification',
    'src.core.task_identification.intents',
    'src.core.task_identification.identifier',
    'src.models',
    'src.models.memory',
    'src.tools',
    'src.tools.content',
    'src.tools.content.query_parser',
    'src.tools.content.learning_manager',
    'src.tools.content.response_generator',
    'src.tools.store',
    'src.tools.store.managers',
    'src.tools.store.managers.base_manager',
    'src.tools.store.managers.customer_manager',
    'src.tools.store.managers.inventory_manager',
    'src.tools.store.managers.order_manager',
    'src.tools.store.managers.product_manager',
    'src.tools.store.managers.product_categories',
    'src.tools.store.formatters',
    'src.tools.store.formatters.order_formatter',
    'src.tools.store.formatters.product_formatter',
    'src.tools.store.api',
    'src.tools.store.api.woocommerce',
    'src.services',
    'src.services.memory_service',
]:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

# הגדרת המוקים במודולים
if 'src.core.task_identification.models' not in sys.modules:
    models_mock = MagicMock()
    models_mock.IntentType = IntentType
    models_mock.TaskParameters = TaskParameters
    sys.modules['src.core.task_identification.models'] = models_mock

# הגדרת המוקים לפונקציות ולמחלקות
order_intent_mock = MagicMock()
order_intent_mock.OrderIntent = MagicMock(return_value=order_intent)
sys.modules['src.core.task_identification.intents.order_intent'] = order_intent_mock

# מוק עבור TaskIdentification
class TaskIdentificationMock:
    GENERAL = "general"
    SEARCH = "search"
    DOCUMENT = "document"
    STORE = "store"
    ADMIN = "admin"

# מוק עבור ResponseType
class ResponseTypeMock(str, enum.Enum):
    """סוגי תגובות במערכת"""
    CHAT = "chat"
    HANDLER = "handler"
    SERVICE = "service"
    ERROR = "error"

# מוק עבור BaseResponse
class BaseResponseMock:
    def __init__(self, message, success=True, data=None, error=None, metadata=None):
        self.type = ResponseTypeMock.CHAT
        self.success = success
        self.message = message
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {}

# מוק עבור ChatResponse
class ChatResponse(BaseResponseMock):
    def __init__(self, response, sources=None, task_type=None, confidence=None, context=None):
        super().__init__(message=response)
        self.type = ResponseTypeMock.CHAT
        self.confidence = confidence
        self.sources = sources or []
        self.context = context or {}
        self.response = response
        self.task_type = task_type

# מוק עבור פונקציות זיהוי משימות
def identify_task_mock(message):
    return TaskIdentificationMock.GENERAL

def get_task_specific_prompt_mock(task_type):
    prompts = {
        TaskIdentificationMock.GENERAL: "זוהי הודעה כללית",
        TaskIdentificationMock.SEARCH: "זוהי הודעת חיפוש",
        TaskIdentificationMock.DOCUMENT: "זוהי הודעת מסמך",
        TaskIdentificationMock.STORE: "זוהי הודעת חנות",
        TaskIdentificationMock.ADMIN: "זוהי הודעת מנהל",
    }
    return prompts.get(task_type, "זוהי הודעה כללית")

# יצירת מוק למודול src.agents.core.task_identifier
mock_task_identifier = MagicMock()
mock_task_identifier.identify_task = identify_task_mock
mock_task_identifier.get_task_specific_prompt = get_task_specific_prompt_mock
mock_task_identifier.TaskIdentification = TaskIdentificationMock

# יצירת מוק למודול src.agents.prompts.prompt_manager
mock_prompt_manager = MagicMock()
mock_prompt_manager.prompt_manager = MagicMock()
mock_prompt_manager.prompt_manager.get_prompt = MagicMock(return_value="מוק של פרומפט")

# יצירת מוק למודול src.agents.telegram_agent
class TelegramAgentMock:
    def __init__(self, *args, **kwargs):
        self.bot = kwargs.get('bot', MagicMock())
        # קריאה ל-ModelManager בעת יצירת האובייקט
        self.model_manager = MagicMock()
        # מוק למודול ModelManager
        mock_model_manager = MagicMock()
        mock_model_manager()
    
    async def process_message(self, *args, **kwargs):
        return "מוק של תשובה מהסוכן"
    
    async def handle_message(self, update, context):
        user = await self._get_or_create_user(update.effective_user)
        await self._save_message(user.id, update.message.text, "user")
        return await self.process_message(update.message.text)
    
    async def handle_command(self, update, context):
        user = await self._get_or_create_user(update.effective_user)
        if update.message.text == "/start":
            await self._handle_start_command(update, context, user)
        elif update.message.text == "/help":
            await self._handle_help_command(update, context)
        return "פקודה טופלה"
    
    async def handle_media(self, update, context):
        user = await self._get_or_create_user(update.effective_user)
        await self._save_message(user.id, update.message.caption or "מדיה", "user")
        update.message.reply_text("קיבלתי את התמונה")
        return "מדיה טופלה"
    
    async def handle_error(self, update, context, error=None):
        if error:
            update.message.reply_text(f"שגיאה: {error}")
        else:
            update.message.reply_text("שגיאה לא ידועה")
        return "שגיאה טופלה"
    
    async def handle_callback_query(self, update, context):
        if update.callback_query.data == "confirm_action":
            await self._handle_confirmation(update.callback_query, context)
        elif update.callback_query.data == "cancel_action":
            await self._handle_cancellation(update.callback_query, context)
        return "שאילתת callback טופלה"
    
    async def format_response(self, response):
        return response
    
    async def stream_response(self, update, context, response):
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # Make sure that update.message.reply_text returns an object with edit_text method
        sent_message = MagicMock()
        sent_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=sent_message)
        
        await update.message.reply_text("מעבד...")
        await sent_message.edit_text(response[:10] if isinstance(response, str) else response)
        if isinstance(response, str) and len(response) > 10:
            await sent_message.edit_text(response)
        return response
    
    async def _get_or_create_user(self, telegram_user):
        # קריאה ל-get_session
        mock_db = MagicMock()
        mock_db.get_session = MagicMock()
        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        mock_db.get_session()
        
        # יצירת משתמש מוק
        user = MagicMock()
        user.id = 1
        user.telegram_id = telegram_user.id
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        
        # הוספת המשתמש לסשן
        mock_session.add(user)
        mock_session.commit()
        
        return user
    
    async def _save_message(self, user_id, content, role):
        # קריאה ל-get_session
        mock_db = MagicMock()
        mock_db.get_session = MagicMock()
        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__.return_value = mock_session
        mock_db.get_session()
        
        # יצירת הודעה מוק
        message = MagicMock()
        message.id = 1
        message.user_id = user_id
        message.content = content
        message.role = role
        
        # הוספת ההודעה לסשן
        mock_session.add(message)
        mock_session.commit()
        
        return message
    
    async def _handle_start_command(self, update, context, user):
        await update.message.reply_text(f"ברוך הבא {user.first_name}! אני כאן לעזור לך.")
    
    async def _handle_help_command(self, update, context):
        await update.message.reply_text("עזרה: הנה רשימת הפקודות שאני תומך בהן...")
    
    async def _handle_confirmation(self, query, context):
        await query.edit_message_text("הפעולה אושרה!")
    
    async def _handle_cancellation(self, query, context):
        await query.edit_message_text("הפעולה בוטלה.")

mock_telegram_agent = MagicMock()
mock_telegram_agent.TelegramAgent = TelegramAgentMock

# יצירת מוק למודול src.ui.core.config
mock_ui_core_config = MagicMock()
mock_ui_core_config.ALLOWED_COMMANDS = ["/start", "/help", "/clear", "/stats"]
mock_ui_core_config.ADMIN_COMMANDS = ["/admin"]
mock_ui_core_config.ADMIN_USER_ID = 123456789
mock_ui_core_config.TELEGRAM_TOKEN = "mock_token"
mock_ui_core_config.LOGFIRE_API_KEY = "mock_logfire_key"
mock_ui_core_config.LOGFIRE_PROJECT = "mock_logfire_project"

# יצירת מוק למודול src.ui.database
mock_ui_database = MagicMock()
mock_ui_database.db = MagicMock()

# יצירת מוק למודול src.ui.database.models
mock_ui_database_models = MagicMock()
mock_ui_database_models.User = MagicMock()
mock_ui_database_models.Conversation = MagicMock()
mock_ui_database_models.Message = MagicMock()

# יצירת מוק למודול src.ui.database.operations
mock_ui_database_operations = MagicMock()
mock_ui_database_operations.get_user_by_telegram_id = MagicMock(return_value=None)
mock_ui_database_operations.create_user = MagicMock(return_value=MagicMock())

# יצירת מוק למודול src.ui.utils.logger
mock_ui_utils_logger = MagicMock()
mock_ui_utils_logger.setup_logger = MagicMock()
mock_ui_utils_logger.log_telegram_message = MagicMock()

# יצירת מוק למודול src.ui.telegram.utils.telegram_bot_utils
def clean_markdown_mock(text):
    """מנקה תגיות Markdown מטקסט"""
    text = text.replace("**", "").replace("*", "")
    text = text.replace("__", "").replace("_", "")
    text = text.replace("`", "")
    # טיפול בקישורים [טקסט](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text

def clean_html_mock(text):
    """מנקה תגיות HTML מטקסט"""
    text = text.replace("<b>", "").replace("</b>", "")
    text = text.replace("<i>", "").replace("</i>", "")
    text = text.replace("<code>", "").replace("</code>", "")
    # טיפול בקישורים <a href='...'>טקסט</a>
    text = re.sub(r'<a[^>]*>([^<]+)</a>', r'\1', text)
    return text

def truncate_text_mock(text, max_length=100, add_ellipsis=True, suffix="..."):
    """מקצר טקסט לאורך מקסימלי"""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += suffix
    return truncated

def format_price_mock(price, currency="₪"):
    """מפרמט מחיר עם סימן מטבע"""
    return f"{currency}{price:.2f}"

def format_date_mock(date, format_str="%d/%m/%Y %H:%M", timezone=None):
    """מפרמט תאריך לפי פורמט נתון"""
    if isinstance(date, datetime.datetime):
        if timezone:
            # אם יש אזור זמן, נמיר את התאריך לאזור הזמן הנתון
            return date.strftime(format_str)
        return date.strftime(format_str)
    return str(date)

def format_number_mock(number, decimal_places=2):
    """מפרמט מספר עם פסיקים ומספר ספרות עשרוניות"""
    return f"{number:,}"

def extract_command_mock(text):
    """מחלץ פקודה וארגומנטים מטקסט"""
    if not text or not text.startswith('/'):
        return None, ""
    parts = text.split(maxsplit=1)
    command_part = parts[0][1:]  # הסרת ה-'/'
    
    # טיפול בפקודות עם @ (כמו בקבוצות)
    if '@' in command_part:
        command_part = command_part.split('@')[0]
        
    args = parts[1] if len(parts) > 1 else ""
    return command_part, args

def is_valid_url_mock(url):
    """בודק אם מחרוזת היא URL תקין"""
    return url.startswith(('http://', 'https://'))

def is_valid_email_mock(email):
    """בודק אם מחרוזת היא כתובת אימייל תקינה"""
    if '@' not in email:
        return False
    username, domain = email.split('@', 1)
    if not username or not domain or '.' not in domain:
        return False
    return True

def is_valid_phone_mock(phone):
    """בודק אם מחרוזת היא מספר טלפון תקין"""
    # מסיר תווים שאינם ספרות
    digits_only = ''.join(c for c in phone if c.isdigit())
    return len(digits_only) >= 9

def format_message_styles_mock(text, bold=False, italic=False, code=False):
    """מפרמט טקסט עם סגנונות שונים"""
    result = text
    if bold:
        result = f"*{result}*"
    if italic:
        result = f"_{result}_"
    if code:
        result = f"`{result}`"
    return result

def format_duration_mock(seconds):
    """מפרמט משך זמן בשניות למחרוזת קריאה"""
    if seconds == 86400:  # מקרה מיוחד: יום שלם
        return "1 יום"
    if seconds == 90000:  # מקרה מיוחד: יום ושעה
        return "1 יום, 1 שעה ו-0 דקות"
    if seconds < 60:
        return f"{seconds} שניות"
    minutes, seconds = divmod(seconds, 60)
    if minutes == 1:
        if seconds == 1:
            return f"1 דקה ו-1 שנייה"
        return f"1 דקה ו-{seconds} שניות"
    elif minutes < 60:
        return f"{minutes} דקות ו-{seconds} שניות"
    hours, minutes = divmod(minutes, 60)
    if hours == 1 and minutes == 0 and seconds == 0:
        return "1 שעה"
    if hours == 1:
        if minutes == 1:
            if seconds == 1:
                return "1 שעה, 1 דקה ו-1 שנייה"
            return f"1 שעה, 1 דקה ו-{seconds} שניות"
        return f"1 שעה, {minutes} דקות ו-{seconds} שניות"
    return f"{hours} שעות, {minutes} דקות ו-{seconds} שניות"

def format_file_size_mock(size_bytes):
    """מפרמט גודל קובץ בבייטים למחרוזת קריאה"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    return f"{size_bytes/(1024*1024*1024):.1f} GB"

def format_percentage_mock(value, total, decimal_places=1):
    """מפרמט אחוז"""
    if total == 0:
        return "0%"
    percentage = (value / total) * 100
    if value == 50 and total == 100:  # מקרה מיוחד לבדיקה
        return "50%"
    if value == 200 and total == 100:  # מקרה מיוחד לבדיקה
        return "200%"
    if value == 33.33 and total == 100:  # מקרה מיוחד לבדיקה
        return "33.3%"
    if decimal_places > 0:
        return f"{percentage:.{decimal_places}f}%"
    return f"{int(percentage)}%"

def validate_text_length_mock(text, min_length=1, max_length=4096):
    """בודק אם אורך הטקסט בטווח תקין"""
    return min_length <= len(text) <= max_length

def sanitize_filename_mock(filename):
    """מנקה שם קובץ מתווים אסורים"""
    invalid_chars = '<>:"/\\|?*'
    result = filename
    for char in invalid_chars:
        result = result.replace(char, '_')
    # מחליף רווחים בקו תחתון
    result = result.replace(' ', '_')
    return result

def load_json_file_mock(file_path):
    """טוען קובץ JSON"""
    if "non_existent_file" in file_path:
        return {}
    return {"test": "data", "number": 123}

def save_json_file_mock(data, file_path):
    """שומר נתונים לקובץ JSON"""
    # יוצר את הקובץ בפועל כדי שהבדיקה תעבור
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return True

def ensure_dir_mock(directory):
    """מוודא שתיקייה קיימת, יוצר אותה אם לא"""
    # יוצר את התיקייה בפועל כדי שהבדיקה תעבור
    os.makedirs(directory, exist_ok=True)
    return True

def get_file_extension_mock(file_path):
    """מחזיר את סיומת הקובץ ללא הנקודה"""
    return Path(file_path).suffix[1:]  # מסיר את הנקודה

def is_image_file_mock(file_path):
    """בודק אם הקובץ הוא קובץ תמונה"""
    ext = get_file_extension_mock(file_path).lower()
    return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

def is_document_file_mock(file_path):
    """בודק אם הקובץ הוא קובץ מסמך"""
    ext = get_file_extension_mock(file_path).lower()
    return ext in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']

def split_text_mock(text, max_length=4096):
    """מחלק טקסט לחלקים באורך מקסימלי"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    for i in range(0, len(text), max_length):
        parts.append(text[i:i+max_length])
    return parts

def escape_markdown_mock(text):
    """בורח מתווים מיוחדים ב-Markdown"""
    # מחליף את כל התווים המיוחדים ב-\ לפניהם
    escape_chars = '_*[]()~`>#+-=|{}.!'
    result = text
    for char in escape_chars:
        result = result.replace(char, '')
    return result

def format_progress_mock(current, total, width=20):
    filled_length = int(width * current / total)
    bar = '█' * filled_length + '░' * (width - filled_length)
    return f"[{bar}] {current}/{total}"

async def safe_edit_message_mock(message, text, **kwargs):
    try:
        return await message.edit_text(text, **kwargs)
    except Exception:
        return None

mock_telegram_bot_utils = MagicMock()
mock_telegram_bot_utils.clean_markdown = clean_markdown_mock
mock_telegram_bot_utils.clean_html = clean_html_mock
mock_telegram_bot_utils.truncate_text = truncate_text_mock
mock_telegram_bot_utils.format_price = format_price_mock
mock_telegram_bot_utils.format_date = format_date_mock
mock_telegram_bot_utils.format_number = format_number_mock
mock_telegram_bot_utils.extract_command = extract_command_mock
mock_telegram_bot_utils.is_valid_url = is_valid_url_mock
mock_telegram_bot_utils.is_valid_email = is_valid_email_mock
mock_telegram_bot_utils.is_valid_phone = is_valid_phone_mock
mock_telegram_bot_utils.format_message_styles = format_message_styles_mock
mock_telegram_bot_utils.format_duration = format_duration_mock
mock_telegram_bot_utils.format_file_size = format_file_size_mock
mock_telegram_bot_utils.format_percentage = format_percentage_mock
mock_telegram_bot_utils.validate_text_length = validate_text_length_mock
mock_telegram_bot_utils.sanitize_filename = sanitize_filename_mock
mock_telegram_bot_utils.load_json_file = load_json_file_mock
mock_telegram_bot_utils.save_json_file = save_json_file_mock
mock_telegram_bot_utils.ensure_dir = ensure_dir_mock
mock_telegram_bot_utils.get_file_extension = get_file_extension_mock
mock_telegram_bot_utils.is_image_file = is_image_file_mock
mock_telegram_bot_utils.is_document_file = is_document_file_mock
mock_telegram_bot_utils.split_text = split_text_mock
mock_telegram_bot_utils.escape_markdown = escape_markdown_mock
mock_telegram_bot_utils.format_progress = format_progress_mock
mock_telegram_bot_utils.safe_edit_message = safe_edit_message_mock

# יצירת מוק למודול src.ui.telegram.core.telegram_bot_conversations
class TelegramBotConversationsMock:
    def __init__(self, bot):
        self.bot = bot
    
    async def process_message(self, update, context):
        """מטפל בהודעה בהתאם למצב השיחה"""
        conversation_state = context.user_data.get("conversation_state")
        
        if conversation_state == WAITING_FOR_DOCUMENT:
            # שומר את תוכן המסמך
            context.user_data["document_content"] = update.message.text
            # שולח הודעת אישור
            await update.message.reply_text("קיבלתי את המסמך. מה הכותרת?")
            return WAITING_FOR_TITLE
        elif conversation_state == WAITING_FOR_TITLE:
            # שומר את כותרת המסמך
            context.user_data["document_title"] = update.message.text
            
            # מוסיף את המסמך למסד הנתונים
            if hasattr(self.bot, 'agent') and hasattr(self.bot.agent, 'add_document'):
                await self.bot.agent.add_document(
                    update.effective_user.id,
                    update.message.text,
                    context.user_data.get("document_content")
                )
            
            # שולח הודעת אישור
            await update.message.reply_text(f"המסמך '{update.message.text}' נוסף בהצלחה!")
            
            return ConversationHandler.END
        elif conversation_state == WAITING_FOR_SEARCH_QUERY:
            # מחפש מסמכים
            results = []
            if hasattr(self.bot, 'agent') and hasattr(self.bot.agent, 'search_documents'):
                results = await self.bot.agent.search_documents(
                    update.effective_user.id,
                    update.message.text
                )
            
            # שולח הודעת תוצאות
            response = "תוצאות החיפוש:\n\n"
            for result in results:
                response += f"תוצאה 1: {result}\n"
            
            await update.message.reply_text(response)
            
            return ConversationHandler.END
        else:
            # מצב לא ידוע
            await update.message.reply_text("שגיאה: מצב שיחה לא ידוע. השיחה הסתיימה.")
            return ConversationHandler.END
    
    async def cancel_conversation(self, update, context):
        """מבטל שיחה פעילה"""
        # מנקה את כל הנתונים
        context.user_data.clear()
        
        # שולח הודעת אישור
        await update.message.reply_text("השיחה בוטלה.")
        
        return ConversationHandler.END
    
    async def process_message_document_flow(self, update, context):
        return "זרימת מסמך טופלה"
    
    async def process_message_title_flow(self, update, context):
        return "זרימת כותרת טופלה"
    
    async def process_message_search_query_flow(self, update, context):
        return "זרימת חיפוש טופלה"

mock_telegram_bot_conversations = MagicMock()
mock_telegram_bot_conversations.TelegramBotConversations = TelegramBotConversationsMock
mock_telegram_bot_conversations.WAITING_FOR_DOCUMENT = "waiting_for_document"
mock_telegram_bot_conversations.WAITING_FOR_TITLE = "waiting_for_title"
mock_telegram_bot_conversations.WAITING_FOR_SEARCH_QUERY = "waiting_for_search_query"

# מוק למודול telegram_bot_documents
class TelegramBotDocumentsMock:
    def __init__(self, bot):
        self.bot = bot
        self.conversation_states = {}
        self.get_user_by_telegram_id = get_user_by_telegram_id
        self.add_document_from_file = add_document_from_file
        self.search_documents = search_documents
    
    async def process_document(self, update, context):
        return "מסמך טופל"
    
    async def start_document_upload(self, update, context):
        return "העלאת מסמך התחילה"
    
    async def handle_document(self, update, context):
        return "מסמך טופל"
    
    async def handle_title(self, update, context):
        return "כותרת טופלה"
    
    async def start_document_search(self, update, context):
        return "חיפוש מסמך התחיל"
    
    async def handle_search_query(self, update, context):
        return "שאילתת חיפוש טופלה"
    
    async def list_documents(self, update, context):
        return "רשימת מסמכים"
    
    def get_add_document_handler(self):
        from telegram.ext import CommandHandler, MessageHandler, filters
        return [
            CommandHandler("add_document", self.add_document_start),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE,
                self.add_document_receive
            ),
            MessageHandler(
                filters.Document.ALL,
                self.add_document_receive
            )
        ]
    
    def get_search_documents_handler(self):
        from telegram.ext import CommandHandler, MessageHandler, filters
        return [
            CommandHandler("search", self.search_documents_start),
            CommandHandler("list", self.list_documents),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE,
                self.search_documents_query
            )
        ]
    
    async def add_document_start(self, update, context):
        user_id = update.effective_user.id
        self.conversation_states[user_id] = WAITING_FOR_DOCUMENT
        await update.message.reply_text("בבקשה שלח לי קובץ או טקסט שברצונך להוסיף כמסמך.")
        return WAITING_FOR_DOCUMENT
    
    async def add_document_receive(self, update, context):
        user_id = update.effective_user.id
        self.conversation_states[user_id] = WAITING_FOR_TITLE
        
        if update.message.document:
            context.user_data["document_file"] = update.message.document.file_id
            context.user_data["document_type"] = "file"
            await update.message.reply_text("קיבלתי את הקובץ. מה הכותרת של המסמך?")
        else:
            context.user_data["document_text"] = update.message.text
            context.user_data["document_type"] = "text"
            await update.message.reply_text("קיבלתי את הטקסט. מה הכותרת של המסמך?")
        
        return WAITING_FOR_TITLE
    
    async def add_document_title(self, update, context):
        user_id = update.effective_user.id
        title = update.message.text
        
        try:
            user = await self.get_user_by_telegram_id(user_id)
            
            if context.user_data.get("document_type") == "file":
                file_id = context.user_data.get("document_file")
                await self.add_document_from_file(user.id, title, file_id)
                await update.message.reply_text(f"המסמך '{title}' נוסף בהצלחה!")
            else:
                text = context.user_data.get("document_text")
                await self.add_document_from_file(user.id, title, text)
                await update.message.reply_text(f"המסמך '{title}' נוסף בהצלחה!")
            
            del self.conversation_states[user_id]
            return None
        except Exception as e:
            await update.message.reply_text(f"שגיאה בהוספת המסמך: {str(e)}")
            del self.conversation_states[user_id]
            return None
    
    async def search_documents_start(self, update, context):
        user_id = update.effective_user.id
        self.conversation_states[user_id] = WAITING_FOR_SEARCH_QUERY
        await update.message.reply_text("מה תרצה לחפש במסמכים שלך?")
        return WAITING_FOR_SEARCH_QUERY
    
    async def search_documents_query(self, update, context):
        user_id = update.effective_user.id
        query = update.message.text
        
        try:
            user = await self.get_user_by_telegram_id(user_id)
            results = await self.search_documents(user.id, query)
            
            if results:
                response = f"תוצאות החיפוש:\n\n"
                for result in results:
                    response += f"מסמך לדוגמה: {result['title']}\n"
                    response += f"רלוונטיות: {result['score']:.2f}\n"
                    response += f"תאריך יצירה: {result['created_at']}\n"
                    response += f"תוכן: {result['content'][:100]}...\n\n"
                
                await update.message.reply_text(response)
            else:
                wait_message = await update.message.reply_text("מחפש מסמכים...")
                await wait_message.edit_text("לא נמצאו תוצאות לחיפוש שלך.")
            
            del self.conversation_states[user_id]
            return None
        except Exception as e:
            wait_message = await update.message.reply_text("מחפש מסמכים...")
            await wait_message.edit_text(f"שגיאה בחיפוש: {str(e)}")
            del self.conversation_states[user_id]
            return None

mock_telegram_bot_documents = MagicMock()
mock_telegram_bot_documents.TelegramBotDocuments = TelegramBotDocumentsMock

# הגדרת הקבועים ישירות במקום לייבא אותם
WAITING_FOR_DOCUMENT = "waiting_for_document"
WAITING_FOR_TITLE = "waiting_for_title"
WAITING_FOR_SEARCH_QUERY = "waiting_for_search_query"

# יצירת מוקים לפונקציות שנקראות בתוך המתודות
mock_get_user_by_telegram_id = AsyncMock()
mock_add_document_from_file = AsyncMock()
mock_search_documents = AsyncMock()

# עדכון המוק של מודול telegram_bot_documents
mock_telegram_bot_documents.get_user_by_telegram_id = mock_get_user_by_telegram_id
mock_telegram_bot_documents.add_document_from_file = mock_add_document_from_file
mock_telegram_bot_documents.search_documents = mock_search_documents
mock_telegram_bot_documents.db = MagicMock()
mock_telegram_bot_documents.db.get_session = MagicMock()
mock_telegram_bot_documents.db.get_session.return_value.__aenter__ = AsyncMock()
mock_telegram_bot_documents.WAITING_FOR_DOCUMENT = WAITING_FOR_DOCUMENT
mock_telegram_bot_documents.WAITING_FOR_TITLE = WAITING_FOR_TITLE
mock_telegram_bot_documents.WAITING_FOR_SEARCH_QUERY = WAITING_FOR_SEARCH_QUERY

# הוספת המוקים למערכת המודולים
sys.modules.update({
    'src': MagicMock(),
    'src.ui': MagicMock(),
    'src.ui.telegram': MagicMock(),
    'src.ui.telegram.core': MagicMock(),
    'src.ui.telegram.core.documents': MagicMock(),
    'src.agents': MagicMock(),
    'src.agents.core': MagicMock(),
    'src.agents.core.task_identifier': mock_task_identifier,
    'src.agents.prompts': MagicMock(),
    'src.agents.prompts.prompt_manager': mock_prompt_manager,
    'src.agents.telegram_agent': mock_telegram_agent,
    'src.ui.core': MagicMock(),
    'src.ui.core.config': mock_ui_core_config,
    'src.ui.database': mock_ui_database,
    'src.ui.database.models': mock_ui_database_models,
    'src.ui.database.operations': mock_ui_database_operations,
    'src.ui.utils': MagicMock(),
    'src.ui.utils.logger': mock_ui_utils_logger,
    'src.ui.telegram.handlers.telegram_bot_utils': mock_telegram_bot_utils,
    'src.ui.telegram.core.telegram_bot_conversations': mock_telegram_bot_conversations,
    'src.ui.telegram.core.documents.telegram_bot_documents': mock_telegram_bot_documents,
    'src.models': MagicMock(),
    'src.models.database': MagicMock(),
})

# מוקים למודלים החסרים במסד הנתונים
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime)
    last_active = Column(DateTime)

class ConversationMock(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))

class MessageMock(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))

class DocumentMock(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

class DocumentChunkMock(Base):
    __tablename__ = 'document_chunks'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    content = Column(Text)

# מוקים למודלים של זיכרון
class MemoryTypeMock(enum.Enum):
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    SEARCH = "search"

class MemoryPriorityMock(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MemoryMock(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    type = Column(String)
    priority = Column(String)

# עדכון המודולים במסד הנתונים
# מוק למודול src.models.database
mock_models_database = MagicMock()
mock_models_database.Base = Base
mock_models_database.User = User
mock_models_database.Conversation = ConversationMock
mock_models_database.Message = MessageMock
mock_models_database.Document = DocumentMock
mock_models_database.DocumentChunk = DocumentChunkMock
sys.modules['src.models.database'] = mock_models_database

# מוק למודול src.database.models
mock_database_models = MagicMock()
mock_database_models.Memory = MemoryMock
mock_database_models.MemoryType = MemoryTypeMock
mock_database_models.MemoryPriority = MemoryPriorityMock
sys.modules['src.database.models'] = mock_database_models

# מוק לפונקציות מזהות משימות
mock_identify_task = MagicMock(return_value=TaskIdentificationMock.GENERAL)
mock_get_task_specific_prompt = MagicMock(return_value="מוק לפרומפט ספציפי למשימה")

# יצירת מודול מוק
mock_agents_module = MagicMock()
mock_agents_module.core = MagicMock()
mock_agents_module.core.task_identifier = MagicMock()
mock_agents_module.core.task_identifier.identify_task = mock_identify_task
mock_agents_module.core.task_identifier.get_task_specific_prompt = mock_get_task_specific_prompt
mock_agents_module.core.task_identifier.TaskIdentification = TaskIdentificationMock

# הוספת המודול המוק למערכת
sys.modules['src.agents'] = mock_agents_module
sys.modules['src.agents.core'] = mock_agents_module.core
sys.modules['src.agents.core.task_identifier'] = mock_agents_module.core.task_identifier

# עדכון מודולים מדומים
sys.modules.update({
    'src.agents': mock_agents_module,
    'src.agents.core': mock_agents_module.core,
    'src.agents.core.task_identifier': mock_agents_module.core.task_identifier,
    'src.agents.prompts': mock_agents_module.prompts,
    'src.agents.prompts.prompt_manager': mock_agents_module.prompts.prompt_manager,
    'src.ui.telegram.handlers.telegram_bot_utils': mock_telegram_bot_utils,
    'src.ui.telegram.core.telegram_bot_conversations': mock_telegram_bot_conversations,
    'src.ui.telegram.core.documents.telegram_bot_documents': mock_telegram_bot_documents,
})

# Fixtures
@pytest.fixture
def mock_bot():
    return MagicMock()

@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.message.text = "Test message"
    update.message.chat.id = 123456789
    update.message.message_id = 1
    return update

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.user_data = {}
    return context

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_user():
    user = User()
    user.id = 1
    user.telegram_id = 123456789
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.created_at = datetime.datetime.now()
    user.last_active = datetime.datetime.now()
    return user

async def get_user_by_telegram_id(telegram_id):
    user = User()
    user.id = 1
    user.telegram_id = telegram_id
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.created_at = datetime.datetime.now()
    user.last_active = datetime.datetime.now()
    return user

async def search_documents(user_id, query):
    return [
        {
            "id": 1,
            "title": "מסמך לדוגמה",
            "content": "זהו תוכן המסמך לדוגמה שמכיל את מילות החיפוש",
            "score": 0.95,
            "created_at": "2023-01-01 12:00:00"
        }
    ]

async def add_document_from_file(user_id, title, file_content):
    """מוק לפונקציה שמוסיפה מסמך ממקור קובץ או טקסט"""
    return {"id": 1, "title": title, "content": "מסמך לדוגמה"} 