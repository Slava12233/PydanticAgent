"""
כלי לוגים מתקדם לניטור ואיתור באגים
"""
import os
import logging
import traceback
import json
from datetime import datetime

# יצירת תיקיית לוגים אם היא לא קיימת
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# הגדרת קובץ הלוג
LOG_FILE = os.path.join(LOG_DIR, f'telegram_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# הגדרת פורמט הלוג
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# הגדרת רמת הלוג
LOG_LEVEL = logging.DEBUG

def setup_logger(name):
    """הגדרת לוגר עם כתיבה לקובץ ולמסוף"""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # מנקה הנדלרים קיימים
    if logger.handlers:
        logger.handlers.clear()
    
    # הנדלר לקובץ
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(LOG_LEVEL)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # הנדלר למסוף
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # הוספת ההנדלרים ללוגר
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_exception(logger, e, context=None):
    """תיעוד מפורט של חריגה"""
    error_details = {
        'error_type': type(e).__name__,
        'error_message': str(e),
        'traceback': traceback.format_exc(),
        'context': context or {}
    }
    
    logger.error(f"Exception details: {json.dumps(error_details, ensure_ascii=False, indent=2)}")
    
    # כתיבה לקובץ נפרד של שגיאות
    error_log_file = os.path.join(LOG_DIR, 'errors.log')
    with open(error_log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n--- {datetime.now().isoformat()} ---\n")
        f.write(json.dumps(error_details, ensure_ascii=False, indent=2))
        f.write("\n")
    
    return error_details

def log_database_operation(logger, operation, params=None, result=None, error=None):
    """תיעוד פעולות מסד נתונים"""
    log_data = {
        'operation': operation,
        'params': params or {},
        'timestamp': datetime.now().isoformat()
    }
    
    if result is not None:
        log_data['result'] = result
    
    if error is not None:
        log_data['error'] = {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc()
        }
        logger.error(f"Database operation failed: {json.dumps(log_data, ensure_ascii=False)}")
    else:
        logger.debug(f"Database operation: {json.dumps(log_data, ensure_ascii=False)}")
    
    return log_data

def log_telegram_message(logger, user_id, message_text, response=None, error=None):
    """תיעוד הודעות טלגרם"""
    log_data = {
        'user_id': user_id,
        'message_length': len(message_text) if message_text else 0,
        'message_preview': message_text[:20] + '...' if message_text and len(message_text) > 20 else message_text,
        'timestamp': datetime.now().isoformat()
    }
    
    if response is not None:
        log_data['response_length'] = len(response)
        log_data['response_preview'] = response[:20] + '...' if len(response) > 20 else response
    
    if error is not None:
        log_data['error'] = {
            'type': type(error).__name__,
            'message': str(error)
        }
        logger.error(f"Telegram message handling failed: {json.dumps(log_data, ensure_ascii=False)}")
    else:
        logger.info(f"Telegram message: {json.dumps(log_data, ensure_ascii=False)}")
    
    return log_data 