"""
מודול המכיל את ה-handler לטיפול בהזמנות.
"""
from typing import Dict, Any, List
from src.handlers.base_handler import BaseHandler, HandlerResponse

@BaseHandler.register('order')
class OrderHandler(BaseHandler):
    """
    Handler לטיפול בפעולות הקשורות להזמנות.
    תומך בפעולות: יצירה, עדכון, ביטול, החזר כספי, סטטוס, רשימה ומשלוח.
    """
    
    def __init__(self):
        super().__init__()
        self._supported_intents = [
            'create', 'update', 'cancel',
            'refund', 'status', 'list',
            'shipping'
        ]
    
    def get_supported_intents(self) -> List[str]:
        """מחזיר את רשימת הכוונות הנתמכות."""
        return self._supported_intents
    
    async def handle(self, intent: str, params: Dict[str, Any] = None) -> HandlerResponse:
        """
        מטפל בבקשות הקשורות להזמנות.
        
        Args:
            intent: הכוונה שזוהתה
            params: פרמטרים נוספים לטיפול בבקשה
            
        Returns:
            HandlerResponse עם תוצאת הטיפול
        """
        handlers = {
            'create': self._handle_create,
            'update': self._handle_update,
            'cancel': self._handle_cancel,
            'refund': self._handle_refund,
            'status': self._handle_status,
            'list': self._handle_list,
            'shipping': self._handle_shipping
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
        """מטפל ביצירת הזמנה חדשה."""
        try:
            # כאן יבוא הקוד ליצירת הזמנה
            return HandlerResponse(
                success=True,
                message="ההזמנה נוצרה בהצלחה",
                data={"order_id": "123"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה ביצירת ההזמנה: {str(e)}",
                error="CREATE_ERROR"
            )
    
    async def _handle_update(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בעדכון הזמנה."""
        try:
            # כאן יבוא הקוד לעדכון הזמנה
            return HandlerResponse(
                success=True,
                message="ההזמנה עודכנה בהצלחה",
                data={"order_id": params.get("id")}
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בעדכון ההזמנה: {str(e)}",
                error="UPDATE_ERROR"
            )
    
    async def _handle_cancel(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בביטול הזמנה."""
        try:
            # כאן יבוא הקוד לביטול הזמנה
            return HandlerResponse(
                success=True,
                message="ההזמנה בוטלה בהצלחה"
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בביטול ההזמנה: {str(e)}",
                error="CANCEL_ERROR"
            )
    
    async def _handle_refund(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בהחזר כספי להזמנה."""
        try:
            # כאן יבוא הקוד להחזר כספי
            return HandlerResponse(
                success=True,
                message="ההחזר הכספי בוצע בהצלחה",
                data={"refund_id": "456"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בביצוע החזר כספי: {str(e)}",
                error="REFUND_ERROR"
            )
    
    async def _handle_status(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בבדיקת סטטוס הזמנה."""
        try:
            # כאן יבוא הקוד לבדיקת סטטוס
            return HandlerResponse(
                success=True,
                message="סטטוס ההזמנה הוחזר בהצלחה",
                data={"status": "בטיפול"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בבדיקת סטטוס ההזמנה: {str(e)}",
                error="STATUS_ERROR"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בהצגת רשימת הזמנות."""
        try:
            # כאן יבוא הקוד להצגת רשימת הזמנות
            return HandlerResponse(
                success=True,
                message="רשימת ההזמנות הוחזרה בהצלחה",
                data={"orders": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת רשימת ההזמנות: {str(e)}",
                error="LIST_ERROR"
            )
    
    async def _handle_shipping(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בניהול משלוח להזמנה."""
        try:
            # כאן יבוא הקוד לניהול משלוח
            return HandlerResponse(
                success=True,
                message="פרטי המשלוח עודכנו בהצלחה",
                data={"tracking_id": "789"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בניהול משלוח: {str(e)}",
                error="SHIPPING_ERROR"
            ) 