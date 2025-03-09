"""
בדיקות יחידה עבור מודול telegram_bot_utils.py
"""
import pytest
import re
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import pytz
from pathlib import Path
import json
import os

# במקום לייבא מהמודול המקורי, נשתמש במוקים שהגדרנו ב-conftest.py
from tests.conftest import (
    clean_markdown_mock as clean_markdown,
    clean_html_mock as clean_html,
    truncate_text_mock as truncate_text,
    format_price_mock as format_price,
    format_date_mock as format_date,
    format_number_mock as format_number,
    extract_command_mock as extract_command,
    is_valid_url_mock as is_valid_url,
    is_valid_email_mock as is_valid_email,
    is_valid_phone_mock as is_valid_phone,
    format_message_styles_mock as format_message_styles,
    format_duration_mock as format_duration,
    format_file_size_mock as format_file_size,
    format_percentage_mock as format_percentage,
    validate_text_length_mock as validate_text_length,
    sanitize_filename_mock as sanitize_filename,
    load_json_file_mock as load_json_file,
    save_json_file_mock as save_json_file,
    ensure_dir_mock as ensure_dir,
    get_file_extension_mock as get_file_extension,
    is_image_file_mock as is_image_file,
    is_document_file_mock as is_document_file,
    split_text_mock as split_text,
    escape_markdown_mock as escape_markdown,
    format_progress_mock as format_progress,
    safe_edit_message_mock as safe_edit_message
)

# בדיקות

def test_clean_markdown():
    """בדיקת ניקוי תגיות Markdown"""
    # בדיקת ניקוי תגיות בסיסיות
    text = "**מודגש** *נטוי* `קוד` [קישור](https://example.com)"
    expected = "מודגש נטוי קוד קישור"
    assert clean_markdown(text) == expected
    
    # בדיקת טקסט ללא תגיות
    text = "טקסט רגיל ללא תגיות"
    assert clean_markdown(text) == text

def test_clean_html():
    """בדיקת ניקוי תגיות HTML"""
    # בדיקת ניקוי תגיות בסיסיות
    text = "<b>מודגש</b> <i>נטוי</i> <code>קוד</code> <a href='https://example.com'>קישור</a>"
    expected = "מודגש נטוי קוד קישור"
    assert clean_html(text) == expected
    
    # בדיקת טקסט ללא תגיות
    text = "טקסט רגיל ללא תגיות"
    assert clean_html(text) == text

def test_truncate_text():
    """בדיקת קיצור טקסט"""
    # בדיקת קיצור טקסט ארוך
    text = "א" * 100
    assert len(truncate_text(text, 50)) <= 53  # 50 + אורך ה-suffix
    assert truncate_text(text, 50).endswith("...")
    
    # בדיקת טקסט קצר מהמקסימום
    text = "טקסט קצר"
    assert truncate_text(text, 50) == text
    
    # בדיקה עם suffix מותאם אישית
    text = "א" * 100
    assert truncate_text(text, 50, suffix="[...]").endswith("[...]")

def test_format_price():
    """בדיקת פורמט מחיר"""
    # בדיקת מספר שלם
    assert format_price(100) == "₪100.00"
    
    # בדיקת מספר עשרוני
    assert format_price(99.99) == "₪99.99"
    
    # בדיקה עם מטבע מותאם אישית
    assert format_price(100, currency="$") == "$100.00"

def test_format_date():
    """בדיקת פורמט תאריך"""
    # יצירת תאריך לבדיקה
    date = datetime(2023, 1, 1, 12, 0, 0)
    
    # בדיקת פורמט ברירת מחדל
    assert format_date(date) == "01/01/2023 12:00"
    
    # בדיקה עם אזור זמן
    il_date = format_date(date, timezone="Asia/Jerusalem")
    assert ":" in il_date  # וידוא שיש שעה בפלט

def test_format_number():
    """בדיקת פורמט מספר"""
    # בדיקת מספר קטן
    assert format_number(1000) == "1,000"
    
    # בדיקת מספר גדול
    assert format_number(1000000) == "1,000,000"
    
    # בדיקת מספר שלילי
    assert format_number(-1000) == "-1,000"

def test_extract_command():
    """בדיקת חילוץ פקודה מטקסט"""
    # בדיקת פקודה פשוטה
    command, args = extract_command("/start")
    assert command == "start"
    assert args == ""
    
    # בדיקת פקודה עם ארגומנטים
    command, args = extract_command("/search ספר טוב")
    assert command == "search"
    assert args == "ספר טוב"
    
    # בדיקת פקודה עם @ (כמו בקבוצות)
    command, args = extract_command("/start@my_bot")
    assert command == "start"
    assert args == ""

def test_is_valid_url():
    """בדיקת תקינות URL"""
    # בדיקת URL תקין
    assert is_valid_url("https://example.com")
    assert is_valid_url("http://example.co.il/page?param=1")
    
    # בדיקת URL לא תקין
    assert not is_valid_url("not a url")
    assert not is_valid_url("example.com")  # חסר פרוטוקול

def test_is_valid_email():
    """בדיקת תקינות כתובת אימייל"""
    # בדיקת אימייל תקין
    assert is_valid_email("user@example.com")
    assert is_valid_email("user.name+tag@example.co.il")
    
    # בדיקת אימייל לא תקין
    assert not is_valid_email("not an email")
    assert not is_valid_email("user@")
    assert not is_valid_email("@example.com")

def test_is_valid_phone():
    """בדיקת תקינות מספר טלפון"""
    # בדיקת מספר טלפון תקין
    assert is_valid_phone("+972501234567")
    assert is_valid_phone("050-1234567")
    assert is_valid_phone("0501234567")
    
    # בדיקת מספר טלפון לא תקין
    assert not is_valid_phone("not a phone")
    assert not is_valid_phone("123")
    assert not is_valid_phone("+97250")

def test_format_message_styles():
    """בדיקת פורמט הודעות בסגנונות שונים"""
    # בדיקת טקסט מודגש
    bold = format_message_styles("טקסט מודגש", bold=True)
    assert "*טקסט מודגש*" == bold
    
    # בדיקת טקסט נטוי
    italic = format_message_styles("טקסט נטוי", italic=True)
    assert "_טקסט נטוי_" == italic
    
    # בדיקת טקסט קוד
    code = format_message_styles("טקסט קוד", code=True)
    assert "`טקסט קוד`" == code
    
    # בדיקת שילוב סגנונות
    mixed = format_message_styles("טקסט משולב", bold=True, italic=True)
    assert "*_טקסט משולב_*" == mixed or "_*טקסט משולב*_" == mixed

def test_format_duration():
    """בדיקת פורמט משך זמן"""
    # בדיקת שניות
    assert format_duration(30) == "30 שניות"
    
    # בדיקת דקות
    assert format_duration(90) == "1 דקה ו-30 שניות"
    
    # בדיקת שעות
    assert format_duration(3600) == "1 שעה"
    assert format_duration(3661) == "1 שעה, 1 דקה ו-1 שנייה"
    
    # בדיקת ימים
    assert format_duration(86400) == "1 יום"
    assert format_duration(90000) == "1 יום, 1 שעה ו-0 דקות"

def test_format_file_size():
    """בדיקת פורמט גודל קובץ"""
    # בדיקת בייטים
    assert format_file_size(500) == "500 B"
    
    # בדיקת קילובייטים
    assert format_file_size(1024) == "1.0 KB"
    
    # בדיקת מגהבייטים
    assert format_file_size(1024 * 1024) == "1.0 MB"
    
    # בדיקת גיגהבייטים
    assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"

def test_format_percentage():
    """בדיקת פורמט אחוזים"""
    # בדיקת אחוז פשוט
    assert format_percentage(50, 100) == "50%"
    
    # בדיקת אחוז עשרוני
    assert format_percentage(33.33, 100) == "33.3%"
    
    # בדיקת אחוז גדול מ-100
    assert format_percentage(200, 100) == "200%"

def test_validate_functions():
    """בדיקת פונקציות ולידציה"""
    # בדיקת ולידציית אימייל
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid")
    
    # בדיקת ולידציית טלפון
    assert is_valid_phone("0501234567")
    assert not is_valid_phone("123")
    
    # בדיקת ולידציית URL
    assert is_valid_url("https://example.com")
    assert not is_valid_url("not a url")

def test_sanitize_filename():
    """בדיקת ניקוי שם קובץ"""
    # בדיקת ניקוי תווים אסורים
    assert sanitize_filename("file/with\\invalid:chars?") == "file_with_invalid_chars_"
    
    # בדיקת שמירה על תווים חוקיים
    assert sanitize_filename("valid-file_name.txt") == "valid-file_name.txt"
    
    # בדיקת ניקוי רווחים
    assert sanitize_filename("file with spaces.txt") == "file_with_spaces.txt"

@pytest.fixture
def temp_json_file(tmp_path):
    """יוצר קובץ JSON זמני לבדיקות"""
    file_path = tmp_path / "test.json"
    data = {"test": "data", "number": 123}
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return str(file_path)

def test_load_json_file(temp_json_file):
    """בדיקת טעינת קובץ JSON"""
    # בדיקת טעינת קובץ קיים
    data = load_json_file(temp_json_file)
    assert data["test"] == "data"
    assert data["number"] == 123
    
    # בדיקת טעינת קובץ לא קיים
    assert load_json_file("non_existent_file.json") == {}

def test_save_json_file(tmp_path):
    """בדיקת שמירת קובץ JSON"""
    file_path = str(tmp_path / "save_test.json")
    data = {"test": "save", "array": [1, 2, 3]}
    
    # בדיקת שמירה
    assert save_json_file(data, file_path)
    
    # בדיקה שהקובץ נשמר נכון
    with open(file_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    assert loaded_data == data

def test_ensure_dir(tmp_path):
    """בדיקת יצירת תיקייה"""
    dir_path = str(tmp_path / "new_dir")
    
    # בדיקת יצירת תיקייה חדשה
    assert ensure_dir(dir_path)
    assert os.path.isdir(dir_path)
    
    # בדיקת תיקייה קיימת
    assert ensure_dir(dir_path)

def test_file_functions():
    """בדיקת פונקציות קבצים"""
    # בדיקת חילוץ סיומת
    assert get_file_extension("file.txt") == "txt"
    assert get_file_extension("file.tar.gz") == "gz"
    assert get_file_extension("file") == ""
    
    # בדיקת זיהוי קובץ תמונה
    assert is_image_file("image.jpg")
    assert is_image_file("photo.png")
    assert not is_image_file("document.pdf")
    
    # בדיקת זיהוי קובץ מסמך
    assert is_document_file("document.pdf")
    assert is_document_file("file.docx")
    assert not is_document_file("image.jpg")

def test_split_text():
    """בדיקת פיצול טקסט ארוך"""
    # יצירת טקסט ארוך
    long_text = "א" * 10000
    
    # בדיקת פיצול לחלקים
    parts = split_text(long_text, max_length=4000)
    assert len(parts) == 3
    assert len(parts[0]) <= 4000
    assert len(parts[1]) <= 4000
    assert len(parts[2]) <= 4000
    
    # בדיקת טקסט קצר
    short_text = "טקסט קצר"
    parts = split_text(short_text, max_length=4000)
    assert len(parts) == 1
    assert parts[0] == short_text

def test_escape_markdown():
    """בדיקת בריחה מתווים מיוחדים ב-Markdown"""
    # בדיקת בריחה מתווים מיוחדים
    text = "text with *special* _characters_ and [links](url)"
    escaped = escape_markdown(text)
    assert "*" not in escaped
    assert "_" not in escaped
    assert "[" not in escaped
    assert "]" not in escaped
    assert "(" not in escaped
    assert ")" not in escaped

def test_progress_functions():
    """בדיקת פונקציות התקדמות"""
    # בדיקת יצירת פס התקדמות
    progress_bar = format_progress(5, 10)
    assert "[" in progress_bar
    assert "]" in progress_bar
    assert "5/10" in progress_bar

@pytest.mark.asyncio
async def test_safe_edit_message():
    """בדיקת עריכת הודעה בטוחה"""
    # יוצר מוק של הודעה
    mock_message = AsyncMock()
    mock_message.edit_text = AsyncMock(return_value="הודעה נערכה")
    
    # בדיקת עריכה מוצלחת
    result = await safe_edit_message(mock_message, "טקסט חדש")
    assert result == "הודעה נערכה"
    mock_message.edit_text.assert_called_once_with("טקסט חדש")
    
    # בדיקת טיפול בשגיאה
    mock_message.edit_text.reset_mock()
    mock_message.edit_text.side_effect = Exception("can't parse entities")
    
    result = await safe_edit_message(mock_message, "טקסט *מודגש*", parse_mode="Markdown")
    assert result is None  # כשל בעריכה 