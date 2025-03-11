"""
מודול המכיל את ה-handler לטיפול בלקוחות.
"""
from typing import Dict, Any, List
from ..core.base_handler import BaseHandler, HandlerResponse

@BaseHandler.register('customer')
class CustomerHandler(BaseHandler):
    """
    Handler לטיפול בפעולות הקשורות ללקוחות.
    תומך בפעולות: יצירה, עדכון, מחיקה, רשימה, חיפוש והיסטוריה.
    """
    
    def __init__(self):
        super().__init__()
        self._supported_intents = [
            'create', 'update', 'delete',
            'list', 'search', 'history'
        ]
    
    def get_supported_intents(self) -> List[str]:
        """מחזיר את רשימת הכוונות הנתמכות."""
        return self._supported_intents
    
    async def handle(self, intent: str, params: Dict[str, Any] = None) -> HandlerResponse:
        """
        מטפל בבקשות הקשורות ללקוחות.
        
        Args:
            intent: הכוונה שזוהתה
            params: פרמטרים נוספים לטיפול בבקשה
            
        Returns:
            HandlerResponse עם תוצאת הטיפול
        """
        handlers = {
            'create': self._handle_create,
            'update': self._handle_update,
            'delete': self._handle_delete,
            'list': self._handle_list,
            'search': self._handle_search,
            'history': self._handle_history
        }
        
        handler = handlers.get(intent)
        if not handler:
            return HandlerResponse(
                success=False,
                message=f"הכוונה {intent} אינה נתמכת",
                error="INTENT_NOT_SUPPORTED"
            )
            
        return await handler(params or {})
    
    async def _handle_create(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל ביצירת לקוח חדש."""
        try:
            # כאן יבוא הקוד ליצירת לקוח
            return HandlerResponse(
                success=True,
                message="הלקוח נוצר בהצלחה",
                data={"customer_id": "789"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה ביצירת הלקוח: {str(e)}",
                error="CREATE_ERROR"
            )
    
    async def _handle_update(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בעדכון פרטי לקוח."""
        try:
            # כאן יבוא הקוד לעדכון לקוח
            return HandlerResponse(
                success=True,
                message="פרטי הלקוח עודכנו בהצלחה",
                data={"customer_id": params.get("id")}
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בעדכון פרטי הלקוח: {str(e)}",
                error="UPDATE_ERROR"
            )
    
    async def _handle_delete(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל במחיקת לקוח."""
        try:
            # כאן יבוא הקוד למחיקת לקוח
            return HandlerResponse(
                success=True,
                message="הלקוח נמחק בהצלחה",
                data={"customer_id": params.get("id")}
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה במחיקת הלקוח: {str(e)}",
                error="DELETE_ERROR"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בהצגת רשימת לקוחות."""
        try:
            # כאן יבוא הקוד להצגת רשימת לקוחות
            return HandlerResponse(
                success=True,
                message="רשימת הלקוחות הוחזרה בהצלחה",
                data={"customers": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת רשימת הלקוחות: {str(e)}",
                error="LIST_ERROR"
            )
    
    async def _handle_search(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בחיפוש לקוחות."""
        try:
            # כאן יבוא הקוד לחיפוש לקוחות
            return HandlerResponse(
                success=True,
                message="תוצאות החיפוש הוחזרו בהצלחה",
                data={"results": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בחיפוש לקוחות: {str(e)}",
                error="SEARCH_ERROR"
            )
    
    async def _handle_history(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בהצגת היסטוריית לקוח."""
        try:
            # כאן יבוא הקוד להצגת היסטוריה
            return HandlerResponse(
                success=True,
                message="היסטוריית הלקוח הוחזרה בהצלחה",
                data={
                    "customer_id": params.get("id"),
                    "history": []  # לדוגמה
                }
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת היסטוריית הלקוח: {str(e)}",
                error="HISTORY_ERROR"
            ) 