"""
מודול המכיל את מחלקת הבסיס למערכת ה-handlers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass

@dataclass
class HandlerResponse:
    """מחלקה המייצגת תשובה מה-handler."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseHandler(ABC):
    """
    מחלקת בסיס לכל ה-handlers במערכת.
    מגדירה את הממשק הבסיסי שכל handler חייב לממש.
    """
    
    _handlers: Dict[str, Type['BaseHandler']] = {}
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    @classmethod
    def register(cls, handler_type: str) -> callable:
        """
        דקורטור לרישום handler חדש במערכת.
        
        Args:
            handler_type: סוג ה-handler (למשל: 'product', 'order', וכו')
            
        Returns:
            פונקציית wrapper לרישום ה-handler
        """
        def wrapper(handler_class: Type['BaseHandler']) -> Type['BaseHandler']:
            cls._handlers[handler_type] = handler_class
            return handler_class
        return wrapper
    
    @classmethod
    def get_handler(cls, handler_type: str) -> Optional[Type['BaseHandler']]:
        """
        מחזיר את ה-handler המתאים לסוג שהתקבל.
        
        Args:
            handler_type: סוג ה-handler המבוקש
            
        Returns:
            מחלקת ה-handler אם נמצאה, None אחרת
        """
        return cls._handlers.get(handler_type)
    
    @classmethod
    def get_all_handlers(cls) -> Dict[str, Type['BaseHandler']]:
        """מחזיר את כל ה-handlers הרשומים במערכת."""
        return cls._handlers
    
    @abstractmethod
    async def handle(self, intent: str, params: Dict[str, Any] = None) -> HandlerResponse:
        """
        מטפל בבקשה שהתקבלה.
        
        Args:
            intent: הכוונה שזוהתה
            params: פרמטרים נוספים לטיפול בבקשה
            
        Returns:
            HandlerResponse עם תוצאת הטיפול
        """
        pass
    
    @abstractmethod
    def get_supported_intents(self) -> List[str]:
        """מחזיר רשימה של כל הכוונות שה-handler תומך בהן."""
        pass
    
    def can_handle(self, intent: str) -> bool:
        """
        בודק אם ה-handler יכול לטפל בכוונה מסוימת.
        
        Args:
            intent: הכוונה לבדיקה
            
        Returns:
            True אם ה-handler תומך בכוונה, False אחרת
        """
        return intent in self.get_supported_intents() 