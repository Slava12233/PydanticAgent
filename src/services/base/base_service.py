"""
מודול המכיל את מחלקת הבסיס לשירותים
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class ServiceResponse:
    """
    מחלקה המייצגת תשובה משירות
    """
    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None
    ):
        """
        אתחול תשובת שירות
        
        Args:
            success: האם הפעולה הצליחה
            message: הודעה למשתמש
            data: נתונים נוספים (אופציונלי)
            error_details: פרטי שגיאה (אופציונלי)
        """
        self.success = success
        self.message = message
        self.data = data or {}
        self.error_details = error_details

class BaseService(ABC):
    """
    מחלקת בסיס לשירותים
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """אתחול השירות"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """סגירת השירות"""
        pass
    
    async def _handle_request(self, operation: str, func, data: Dict[str, Any], required_params: Optional[list] = None) -> ServiceResponse:
        """
        מטפל בבקשה לשירות
        
        Args:
            operation: שם הפעולה
            func: פונקציה לביצוע
            data: נתוני הבקשה
            required_params: פרמטרים נדרשים (אופציונלי)
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            # בדיקת פרמטרים נדרשים
            if required_params:
                missing_params = [param for param in required_params if param not in data]
                if missing_params:
                    return self._create_error_response(
                        "חסרים פרמטרים נדרשים",
                        f"הפרמטרים הבאים נדרשים: {', '.join(missing_params)}",
                        {'missing_params': missing_params}
                    )
            
            # ביצוע הפעולה
            return await func(data)
            
        except Exception as e:
            return self._create_error_response(
                f"שגיאה בביצוע {operation}",
                str(e),
                {'error': str(e)}
            )
    
    def _create_success_response(self, message: str, data: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """יוצר תשובת הצלחה"""
        return ServiceResponse(True, message, data)
    
    def _create_error_response(self, message: str, error_details: str, data: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """יוצר תשובת שגיאה"""
        return ServiceResponse(False, message, data, error_details) 