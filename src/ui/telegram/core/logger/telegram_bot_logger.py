"""
מודול לניהול לוגים של הבוט
"""
import logging
import os
from datetime import datetime
from typing import Optional
import logfire

class TelegramBotLogger:
    """מחלקה לניהול לוגים של הבוט"""
    
    def __init__(self, name: str = 'telegram_bot'):
        """
        אתחול הלוגר
        
        Args:
            name: שם הלוגר
        """
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        הגדרת הלוגר
        
        Returns:
            אובייקט הלוגר
        """
        # יצירת תיקיית לוגים אם לא קיימת
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # הגדרת קובץ הלוג
        log_file = os.path.join(log_dir, f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        # יצירת הלוגר
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # הגדרת פורמט
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # הוספת handler לקובץ
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # הוספת handler למסוף
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """רישום הודעת מידע"""
        self.logger.info(message)
        logfire.log(level="info", message=message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """רישום הודעת אזהרה"""
        self.logger.warning(message)
        logfire.log(level="warning", message=message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """רישום הודעת שגיאה"""
        self.logger.error(message)
        logfire.log(level="error", message=message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """רישום הודעת דיבאג"""
        self.logger.debug(message)
        logfire.log(level="debug", message=message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """רישום הודעה קריטית"""
        self.logger.critical(message)
        logfire.log(level="critical", message=message, **kwargs)
    
    def exception(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """רישום חריגה"""
        self.logger.exception(message, exc_info=exc_info)
        logfire.log(level="error", message=message, exc_info=exc_info, **kwargs)

class JsonFormatter(logging.Formatter):
    """
    פורמטר להודעות בפורמט JSON
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        פורמט הודעת לוג ל-JSON
        
        Args:
            record: רשומת לוג
            
        Returns:
            הודעה בפורמט JSON
        """
        # מידע בסיסי
        message = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'name': record.name,
            'filename': record.filename,
            'line_number': record.lineno,
            'message': record.getMessage()
        }
        
        # הוספת מידע על שגיאות
        if record.exc_info:
            message['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # הוספת מידע נוסף
        if hasattr(record, 'extra'):
            message['extra'] = record.extra
        
        return json.dumps(message, ensure_ascii=False)

def setup_logger(
    name: str,
    log_dir: str = 'logs',
    level: int = logging.INFO,
    **kwargs
) -> logging.Logger:
    """
    פונקציית עזר ליצירת לוגר
    
    Args:
        name: שם הלוגר
        log_dir: תיקיית לוגים
        level: רמת לוג
        **kwargs: פרמטרים נוספים
        
    Returns:
        אובייקט הלוגר
    """
    logger = TelegramBotLogger(
        name=name,
        log_dir=log_dir,
        level=level,
        **kwargs
    )
    return logger.get_logger() 