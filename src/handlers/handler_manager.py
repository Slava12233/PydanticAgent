"""
מודול המכיל את מנהל ה-handlers של המערכת.
"""
import importlib
import os
from typing import Dict, List, Optional, Type
from .base_handler import BaseHandler, HandlerResponse

class HandlerManager:
    """
    מנהל ה-handlers של המערכת.
    אחראי על טעינה, רישום וניהול של כל ה-handlers.
    """
    
    def __init__(self):
        self._handlers: Dict[str, BaseHandler] = {}
        self._load_handlers()
    
    def _load_handlers(self):
        """
        טוען את כל ה-handlers מהתיקיות המתאימות.
        מחפש קבצים עם הסיומת _handler.py ומייבא אותם.
        """
        handlers_dir = os.path.dirname(__file__)
        
        # עובר על כל התיקיות בתוך handlers
        for root, _, files in os.walk(handlers_dir):
            for file in files:
                if file.endswith('_handler.py') and file != 'base_handler.py':
                    # מחלץ את שם המודול
                    module_path = os.path.join(root, file)
                    relative_path = os.path.relpath(module_path, os.path.dirname(handlers_dir))
                    module_name = os.path.splitext(relative_path)[0].replace(os.sep, '.')
                    
                    try:
                        # מייבא את המודול
                        importlib.import_module(f"handlers.{module_name}")
                    except ImportError as e:
                        print(f"שגיאה בטעינת handler {module_name}: {str(e)}")
    
    def register_handler(self, handler_type: str, handler_class: Type[BaseHandler]):
        """
        רושם handler חדש במערכת.
        
        Args:
            handler_type: סוג ה-handler
            handler_class: מחלקת ה-handler
        """
        if handler_type not in self._handlers:
            self._handlers[handler_type] = handler_class()
    
    def get_handler(self, handler_type: str) -> Optional[BaseHandler]:
        """
        מחזיר handler לפי סוג.
        
        Args:
            handler_type: סוג ה-handler המבוקש
            
        Returns:
            ה-handler אם נמצא, None אחרת
        """
        return self._handlers.get(handler_type)
    
    def get_all_handlers(self) -> List[BaseHandler]:
        """מחזיר רשימה של כל ה-handlers במערכת."""
        return list(self._handlers.values())
    
    async def handle_request(self, handler_type: str, intent: str, params: Dict = None) -> HandlerResponse:
        """
        מטפל בבקשה באמצעות ה-handler המתאים.
        
        Args:
            handler_type: סוג ה-handler הנדרש
            intent: הכוונה שזוהתה
            params: פרמטרים נוספים לטיפול בבקשה
            
        Returns:
            HandlerResponse עם תוצאת הטיפול
        """
        handler = self.get_handler(handler_type)
        if not handler:
            return HandlerResponse(
                success=False,
                message=f"לא נמצא handler מתאים לסוג {handler_type}",
                error="HANDLER_NOT_FOUND"
            )
            
        if not handler.can_handle(intent):
            return HandlerResponse(
                success=False,
                message=f"ה-handler {handler_type} אינו תומך בכוונה {intent}",
                error="INTENT_NOT_SUPPORTED"
            )
            
        try:
            return await handler.handle(intent, params)
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בטיפול בבקשה: {str(e)}",
                error="HANDLER_ERROR"
            )
    
    def get_supported_intents(self, handler_type: str = None) -> Dict[str, List[str]]:
        """
        מחזיר את כל הכוונות הנתמכות במערכת או ע"י handler ספציפי.
        
        Args:
            handler_type: סוג ה-handler (אופציונלי)
            
        Returns:
            מילון של כוונות נתמכות לפי סוג handler
        """
        if handler_type:
            handler = self.get_handler(handler_type)
            return {handler_type: handler.get_supported_intents()} if handler else {}
            
        return {
            h_type: handler.get_supported_intents()
            for h_type, handler in self._handlers.items()
        } 