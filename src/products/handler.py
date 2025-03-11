"""
מודול המכיל את ה-handler לטיפול במוצרים.
"""
from typing import Dict, Any, List
from src.handlers.base_handler import BaseHandler, HandlerResponse

@BaseHandler.register('product')
class ProductHandler(BaseHandler):
    """
    Handler לטיפול בפעולות הקשורות למוצרים.
    תומך בפעולות: יצירה, עדכון, מחיקה, רשימה, חיפוש.
    """
    
    def __init__(self):
        super().__init__()
        self._supported_intents = [
            'create', 'update', 'delete',
            'list', 'search', 'categories',
            'images'
        ]
    
    def get_supported_intents(self) -> List[str]:
        """מחזיר את רשימת הכוונות הנתמכות."""
        return self._supported_intents
    
    async def handle(self, intent: str, params: Dict[str, Any] = None) -> HandlerResponse:
        """
        מטפל בבקשות הקשורות למוצרים.
        
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
            'categories': self._handle_categories,
            'images': self._handle_images
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
        """מטפל ביצירת מוצר חדש."""
        try:
            # כאן יבוא הקוד ליצירת מוצר
            return HandlerResponse(
                success=True,
                message="המוצר נוצר בהצלחה",
                data={"product_id": "123"}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה ביצירת המוצר: {str(e)}",
                error="CREATE_ERROR"
            )
    
    async def _handle_update(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בעדכון מוצר."""
        try:
            # כאן יבוא הקוד לעדכון מוצר
            return HandlerResponse(
                success=True,
                message="המוצר עודכן בהצלחה",
                data={"product_id": params.get("id")}
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בעדכון המוצר: {str(e)}",
                error="UPDATE_ERROR"
            )
    
    async def _handle_delete(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל במחיקת מוצר."""
        try:
            # כאן יבוא הקוד למחיקת מוצר
            return HandlerResponse(
                success=True,
                message="המוצר נמחק בהצלחה"
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה במחיקת המוצר: {str(e)}",
                error="DELETE_ERROR"
            )
    
    async def _handle_list(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בהצגת רשימת מוצרים."""
        try:
            # כאן יבוא הקוד להצגת רשימת מוצרים
            return HandlerResponse(
                success=True,
                message="רשימת המוצרים הוחזרה בהצלחה",
                data={"products": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בהצגת רשימת המוצרים: {str(e)}",
                error="LIST_ERROR"
            )
    
    async def _handle_search(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בחיפוש מוצרים."""
        try:
            # כאן יבוא הקוד לחיפוש מוצרים
            return HandlerResponse(
                success=True,
                message="תוצאות החיפוש הוחזרו בהצלחה",
                data={"results": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בחיפוש מוצרים: {str(e)}",
                error="SEARCH_ERROR"
            )
    
    async def _handle_categories(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בניהול קטגוריות מוצרים."""
        try:
            # כאן יבוא הקוד לניהול קטגוריות
            return HandlerResponse(
                success=True,
                message="פעולת הקטגוריות בוצעה בהצלחה",
                data={"categories": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בניהול קטגוריות: {str(e)}",
                error="CATEGORIES_ERROR"
            )
    
    async def _handle_images(self, params: Dict[str, Any]) -> HandlerResponse:
        """מטפל בניהול תמונות מוצרים."""
        try:
            # כאן יבוא הקוד לניהול תמונות
            return HandlerResponse(
                success=True,
                message="פעולת התמונות בוצעה בהצלחה",
                data={"images": []}  # לדוגמה
            )
        except Exception as e:
            return HandlerResponse(
                success=False,
                message=f"שגיאה בניהול תמונות: {str(e)}",
                error="IMAGES_ERROR"
            ) 