"""
מודול המכיל את ה-handler לטיפול בבקשות עזרה.
"""
from typing import Dict, Any, List
from ..base_handler import BaseHandler, HandlerResponse

@BaseHandler.register('help')
class HelpHandler(BaseHandler):
    """
    Handler לטיפול בפעולות הקשורות לעזרה.
    תומך בפעולות: עזרה כללית, עזרה ספציפית, שגיאות והגדרות.
    """
    
    def __init__(self):
        super().__init__()
        self._supported_intents = [
            'general', 'specific', 'errors',
            'settings'
        ]
    
    def get_supported_intents(self) -> List[str]:
        """מחזיר את רשימת הכוונות הנתמכות."""
        return self._supported_intents
    
    async def handle(self, intent: str, params: Dict[str, Any] = None) -> HandlerResponse:
        """
        מטפל בבקשות הקשורות לעזרה.
        
        Args:
            intent: הכוונה שזוהתה
            params: פרמטרים נוספים לטיפול בבקשה
            
        Returns:
            HandlerResponse עם תוצאת הטיפול
        """
        handlers = {
            'general': self._handle_general,
            'specific': self._handle_specific,
            'errors': self._handle_errors,
            'settings': self._handle_settings
        }
        
        handler = handlers.get(intent)
        if not handler:
            return HandlerResponse(
                success=False,
                message=f"הכוונה {intent} אינה נתמכת",
                error="INTENT_NOT_SUPPORTED"
            )
            
        return await handler(params or {})
    
    async def _handle_general(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בבקשות עזרה כלליות."""
        try:
            # כאן יבוא הקוד להצגת עזרה כללית
            return HandlerResponse(
                success=True,
                message="ברוך הבא למערכת! הנה כמה דברים שאני יכול לעזור בהם:",
                data={
                    "categories": {
                        "products": "ניהול מוצרים (הוספה, עדכון, מחיקה)",
                        "orders": "טיפול בהזמנות ומשלוחים",
                        "customers": "ניהול לקוחות ופרטיהם",
                        "inventory": "מעקב וניהול מלאי",
                        "analytics": "דוחות וניתוח נתונים"
                    },
                    "common_commands": [
                        "/help - הצגת תפריט זה",
                        "/products - ניהול מוצרים",
                        "/orders - ניהול הזמנות",
                        "/inventory - ניהול מלאי"
                    ]
                }
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת עזרה כללית: {str(e)}",
                error="GENERAL_HELP_ERROR"
            )
    
    async def _handle_specific(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בבקשות עזרה ספציפיות."""
        try:
            topic = params.get("topic", "")
            # כאן יבוא הקוד להצגת עזרה ספציפית
            return HandlerResponse(
                success=True,
                message=f"הנה עזרה בנושא {topic}:",
                data={
                    "topic": topic,
                    "instructions": [],  # יש למלא לפי הנושא
                    "examples": [],
                    "related_topics": []
                }
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת עזרה ספציפית: {str(e)}",
                error="SPECIFIC_HELP_ERROR"
            )
    
    async def _handle_errors(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בבקשות עזרה לשגיאות."""
        try:
            error_code = params.get("error_code", "")
            # כאן יבוא הקוד לטיפול בשגיאות
            return HandlerResponse(
                success=True,
                message=f"הנה מידע על השגיאה {error_code}:",
                data={
                    "error_code": error_code,
                    "description": "",  # יש למלא לפי קוד השגיאה
                    "solution": "",
                    "common_causes": []
                }
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בטיפול בשגיאה: {str(e)}",
                error="ERROR_HELP_ERROR"
            )
    
    async def _handle_settings(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בבקשות עזרה להגדרות."""
        try:
            setting = params.get("setting", "")
            # כאן יבוא הקוד להצגת עזרה בהגדרות
            return HandlerResponse(
                success=True,
                message=f"הנה עזרה בנושא הגדרות {setting}:",
                data={
                    "setting": setting,
                    "instructions": [],  # יש למלא לפי ההגדרה
                    "options": {},
                    "default_values": {}
                }
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת עזרה להגדרות: {str(e)}",
                error="SETTINGS_HELP_ERROR"
            ) 