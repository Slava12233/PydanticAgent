import logging
import re
from typing import Optional, Dict, Any, List
from telegram import Message
from telegram.error import TelegramError
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import json
from pathlib import Path
import pytz
import os

from src.utils.logger import setup_logger

# Configure logging
logger = setup_logger('telegram_bot_utils')

# הגדרת אזור זמן ברירת מחדל
DEFAULT_TIMEZONE = pytz.timezone('Asia/Jerusalem')

async def safe_edit_message(message: Message, text: str, parse_mode: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Message]:
    """
    עורך הודעה בצורה בטוחה, מטפל בשגיאות אפשריות
    
    Args:
        message: אובייקט ההודעה לעריכה
        text: הטקסט החדש
        parse_mode: מצב פירוש (Markdown, HTML, וכו')
        user_id: מזהה המשתמש (אופציונלי)
        
    Returns:
        ההודעה המעודכנת או הודעה חדשה אם העריכה נכשלה
    """
    try:
        # ניסיון לערוך את ההודעה
        return await message.edit_text(text, parse_mode=parse_mode)
    except TelegramError as e:
        logger.error(f"Error editing message: {e}")
        
        # אם יש שגיאת Markdown, ננסה לשלוח ללא Markdown
        if "can't parse entities" in str(e) and parse_mode:
            try:
                # ניקוי תגיות Markdown/HTML
                clean_text = text
                if parse_mode == ParseMode.MARKDOWN:
                    clean_text = text.replace('*', '').replace('_', '').replace('`', '')
                elif parse_mode == ParseMode.HTML:
                    clean_text = re.sub(r'<[^>]+>', '', text)
                
                return await message.edit_text(clean_text, parse_mode=None)
            except Exception as e2:
                logger.error(f"Error editing message without formatting: {e2}")
        
        # אם העריכה נכשלה לגמרי, ננסה לשלוח הודעה חדשה
        if hasattr(message, 'reply_text'):
            try:
                return await message.reply_text(text, parse_mode=parse_mode)
            except Exception as e3:
                logger.error(f"Error sending new message: {e3}")
                
                # ניסיון אחרון - לשלוח הודעה פשוטה ללא עיצוב
                try:
                    clean_text = text.replace('*', '').replace('_', '').replace('`', '')
                    return await message.reply_text(clean_text, parse_mode=None)
                except Exception as e4:
                    logger.error(f"Final error sending plain message: {e4}")
    
    except Exception as e:
        logger.error(f"Unexpected error editing message: {e}")
        
        # ניסיון לשלוח הודעה חדשה במקרה של שגיאה לא צפויה
        if hasattr(message, 'reply_text'):
            try:
                return await message.reply_text("אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב.", parse_mode=None)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")
    
    return None

def clean_markdown(text: str) -> str:
    """
    מנקה תגיות Markdown מטקסט
    
    Args:
        text: הטקסט לניקוי
        
    Returns:
        הטקסט ללא תגיות Markdown
    """
    return text.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')

def clean_html(text: str) -> str:
    """
    מנקה תגיות HTML מטקסט
    
    Args:
        text: הטקסט לניקוי
        
    Returns:
        הטקסט ללא תגיות HTML
    """
    return re.sub(r'<[^>]+>', '', text)

def truncate_text(text: str, max_length: int = 4096, suffix: str = '...') -> str:
    """
    מקצר טקסט לאורך מקסימלי מסוים
    
    Args:
        text: הטקסט לקיצור
        max_length: האורך המקסימלי
        suffix: הסיומת להוספה אם הטקסט קוצר
        
    Returns:
        הטקסט המקוצר
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_price(price: float, currency: str = '₪') -> str:
    """
    מעצב מחיר בפורמט מתאים
    
    Args:
        price: המחיר
        currency: סימן המטבע
        
    Returns:
        המחיר בפורמט מעוצב
    """
    return f"{price:,.2f} {currency}"

def format_date(date_str: str, format: str = '%Y-%m-%d') -> str:
    """
    מעצב תאריך בפורמט מתאים
    
    Args:
        date_str: התאריך כמחרוזת
        format: פורמט התאריך הרצוי
        
    Returns:
        התאריך בפורמט מעוצב
    """
    from datetime import datetime
    try:
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        return date.strftime(format)
    except:
        return date_str

def format_number(number: int) -> str:
    """
    מעצב מספר בפורמט מתאים
    
    Args:
        number: המספר לעיצוב
        
    Returns:
        המספר בפורמט מעוצב
    """
    return f"{number:,}"

def extract_command(text: str) -> tuple[str, str]:
    """
    מחלץ פקודה וארגומנטים מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        tuple של הפקודה והארגומנטים
    """
    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''
    return command, args

def is_valid_url(url: str) -> bool:
    """
    בודק אם כתובת URL תקינה
    
    Args:
        url: הכתובת לבדיקה
        
    Returns:
        האם הכתובת תקינה
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def is_valid_email(email: str) -> bool:
    """
    בודק אם כתובת אימייל תקינה
    
    Args:
        email: הכתובת לבדיקה
        
    Returns:
        האם הכתובת תקינה
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

def is_valid_phone(phone: str) -> bool:
    """
    בודק אם מספר טלפון תקין
    
    Args:
        phone: המספר לבדיקה
        
    Returns:
        האם המספר תקין
    """
    phone_pattern = re.compile(r'^\+?972|0(?:[23489]|5[0-9]|77)[1-9]\d{6}$')
    return bool(phone_pattern.match(phone))

def format_error_message(text: str) -> str:
    """
    עיצוב הודעת שגיאה
    
    Args:
        text: טקסט ההודעה
        
    Returns:
        הודעה מעוצבת
    """
    return f"❌ *שגיאה*\n{text}"

def format_success_message(message: str) -> str:
    """
    מעצב הודעת הצלחה בפורמט מתאים
    
    Args:
        message: ההודעה לעיצוב
        
    Returns:
        הודעת ההצלחה בפורמט מעוצב
    """
    return f"✅ *הצלחה*\n{message}"

def format_warning_message(message: str) -> str:
    """
    מעצב הודעת אזהרה בפורמט מתאים
    
    Args:
        message: ההודעה לעיצוב
        
    Returns:
        הודעת האזהרה בפורמט מעוצב
    """
    return f"⚠️ *אזהרה*\n{message}"

def format_info_message(message: str) -> str:
    """
    מעצב הודעת מידע בפורמט מתאים
    
    Args:
        message: ההודעה לעיצוב
        
    Returns:
        הודעת המידע בפורמט מעוצב
    """
    return f"ℹ️ *מידע*\n{message}"

def format_date(date: datetime, timezone: Optional[str] = None) -> str:
    """
    עיצוב תאריך
    
    Args:
        date: תאריך
        timezone: אזור זמן (אופציונלי)
        
    Returns:
        תאריך מעוצב
    """
    if timezone:
        tz = pytz.timezone(timezone)
        date = date.astimezone(tz)
    else:
        date = date.astimezone(DEFAULT_TIMEZONE)
    
    return date.strftime('%d/%m/%Y %H:%M')

def format_price(amount: float, currency: str = '₪') -> str:
    """
    עיצוב מחיר
    
    Args:
        amount: סכום
        currency: מטבע (ברירת מחדל: שקל)
        
    Returns:
        מחיר מעוצב
    """
    return f"{amount:,.2f} {currency}"

def format_number(number: int) -> str:
    """
    עיצוב מספר
    
    Args:
        number: מספר
        
    Returns:
        מספר מעוצב
    """
    return f"{number:,}"

def format_duration(seconds: int) -> str:
    """
    עיצוב משך זמן
    
    Args:
        seconds: שניות
        
    Returns:
        משך זמן מעוצב
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days} ימים")
    if hours > 0:
        parts.append(f"{hours} שעות")
    if minutes > 0:
        parts.append(f"{minutes} דקות")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} שניות")
    
    return " ו-".join(parts)

def format_file_size(size_bytes: int) -> str:
    """
    עיצוב גודל קובץ
    
    Args:
        size_bytes: גודל בבתים
        
    Returns:
        גודל מעוצב
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

def format_percentage(value: float, total: float) -> str:
    """
    עיצוב אחוז
    
    Args:
        value: ערך
        total: סך הכל
        
    Returns:
        אחוז מעוצב
    """
    if total == 0:
        return "0%"
    return f"{(value / total * 100):.1f}%"

def validate_email(email: str) -> bool:
    """
    בדיקת תקינות כתובת אימייל
    
    Args:
        email: כתובת אימייל
        
    Returns:
        האם האימייל תקין
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    בדיקת תקינות מספר טלפון
    
    Args:
        phone: מספר טלפון
        
    Returns:
        האם הטלפון תקין
    """
    pattern = r'^(\+972|0)([23489]|5[0-9]|77)[0-9]{7}$'
    return bool(re.match(pattern, phone))

def validate_url(url: str) -> bool:
    """
    בדיקת תקינות כתובת URL
    
    Args:
        url: כתובת URL
        
    Returns:
        האם הכתובת תקינה
    """
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))

def sanitize_filename(filename: str) -> str:
    """
    ניקוי שם קובץ מתווים לא חוקיים
    
    Args:
        filename: שם הקובץ לניקוי
        
    Returns:
        שם קובץ נקי
    """
    # פיצול לשם קובץ וסיומת
    name, ext = os.path.splitext(filename)
    
    # הסרת תווים לא חוקיים
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # החלפת רווחים מרובים ברווח בודד
    name = re.sub(r'\s+', ' ', name)
    
    # הסרת רווחים מתחילת וסוף השם
    name = name.strip()
    
    # החזרת השם המלא עם הסיומת
    return name + ext

def load_json_file(file_path: str) -> Dict:
    """
    טעינת קובץ JSON
    
    Args:
        file_path: נתיב הקובץ
        
    Returns:
        תוכן הקובץ כמילון
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(data: Dict, file_path: str) -> bool:
    """
    שמירת נתונים לקובץ JSON
    
    Args:
        data: הנתונים לשמירה
        file_path: נתיב הקובץ
        
    Returns:
        האם השמירה הצליחה
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {file_path}: {e}")
        return False

def ensure_dir(dir_path: str) -> bool:
    """
    יצירת תיקייה אם לא קיימת
    
    Args:
        dir_path: נתיב התיקייה
        
    Returns:
        האם התיקייה קיימת או נוצרה בהצלחה
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory {dir_path}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """
    קבלת סיומת הקובץ
    
    Args:
        filename: שם הקובץ
        
    Returns:
        סיומת הקובץ
    """
    return Path(filename).suffix.lower()

def is_image_file(filename: str) -> bool:
    """
    בדיקה האם הקובץ הוא תמונה
    
    Args:
        filename: שם הקובץ
        
    Returns:
        האם הקובץ הוא תמונה
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return get_file_extension(filename) in image_extensions

def is_document_file(filename: str) -> bool:
    """
    בדיקה האם הקובץ הוא מסמך
    
    Args:
        filename: שם הקובץ
        
    Returns:
        האם הקובץ הוא מסמך
    """
    document_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.rtf'}
    return get_file_extension(filename) in document_extensions

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    קיצור טקסט לאורך מקסימלי
    
    Args:
        text: הטקסט
        max_length: אורך מקסימלי
        suffix: סיומת לטקסט מקוצר
        
    Returns:
        טקסט מקוצר
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def split_text(text: str, max_length: int = 4096) -> List[str]:
    """
    פיצול טקסט לחלקים לפי אורך מקסימלי
    
    Args:
        text: הטקסט
        max_length: אורך מקסימלי לכל חלק
        
    Returns:
        רשימת חלקי הטקסט
    """
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        # חיפוש נקודת פיצול מתאימה
        split_point = max_length
        while split_point > 0 and not text[split_point].isspace():
            split_point -= 1
        
        if split_point == 0:
            # אם לא נמצאה נקודת פיצול, פיצול בכוח
            split_point = max_length
        
        parts.append(text[:split_point])
        text = text[split_point:].lstrip()
    
    return parts

def escape_markdown(text: str) -> str:
    """
    הסרת תווים מיוחדים מטקסט Markdown
    
    Args:
        text: הטקסט
        
    Returns:
        טקסט נקי
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

def generate_progress_bar(value: float, total: float, length: int = 20) -> str:
    """
    יצירת שורת התקדמות
    
    Args:
        value: ערך נוכחי
        total: ערך מקסימלי
        length: אורך השורה
        
    Returns:
        שורת התקדמות
    """
    if total == 0:
        percentage = 0
    else:
        percentage = value / total
    
    filled = int(length * percentage)
    bar = '█' * filled + '░' * (length - filled)
    percent = percentage * 100
    
    return f"[{bar}] {percent:.1f}%"

def create_progress_bar(current: int, total: int, style: str = 'default') -> str:
    """
    יצירת סרגל התקדמות ויזואלי
    
    Args:
        current: שלב נוכחי
        total: סך כל השלבים
        style: סגנון הסרגל (default/emoji/minimal)
        
    Returns:
        סרגל התקדמות ויזואלי
    """
    styles = {
        'default': {
            'completed': '✅',
            'current': '🔵',
            'remaining': '⚪'
        },
        'emoji': {
            'completed': '🟢',
            'current': '🔵',
            'remaining': '⭕'
        },
        'minimal': {
            'completed': '●',
            'current': '○',
            'remaining': '○'
        }
    }
    
    # בחירת סגנון
    icons = styles.get(style, styles['default'])
    
    # יצירת הסרגל
    progress = ''
    for i in range(total):
        if i < current - 1:
            progress += icons['completed']
        elif i == current - 1:
            progress += icons['current']
        else:
            progress += icons['remaining']
    
    return progress

def format_progress_message(
    current: int,
    total: int,
    title: str,
    message: str,
    style: str = 'default'
) -> str:
    """
    עיצוב הודעת התקדמות מלאה
    
    Args:
        current: שלב נוכחי
        total: סך כל השלבים
        title: כותרת השלב
        message: תוכן ההודעה
        style: סגנון הסרגל
        
    Returns:
        הודעה מעוצבת עם סרגל התקדמות
    """
    progress_bar = create_progress_bar(current, total, style)
    
    return (
        f"{progress_bar}\n"
        f"*שלב {current}/{total}: {title}*\n\n"
        f"{message}"
    )

def create_step_message(
    step: int,
    total_steps: int,
    title: str,
    success_message: Optional[str] = None,
    next_message: str = "",
    style: str = 'default'
) -> str:
    """
    יצירת הודעת שלב בתהליך
    
    Args:
        step: מספר השלב הנוכחי
        total_steps: סך כל השלבים
        title: כותרת השלב
        success_message: הודעת הצלחה לשלב הקודם (אופציונלי)
        next_message: הודעה לשלב הבא
        style: סגנון הסרגל
        
    Returns:
        הודעה מעוצבת לשלב
    """
    progress_bar = create_progress_bar(step, total_steps, style)
    
    message = ""
    if success_message:
        message += f"✅ {success_message}\n\n"
    
    message += (
        f"{progress_bar} *שלב {step}/{total_steps}: {title}*\n\n"
        f"{next_message}"
    )
    
    return message 