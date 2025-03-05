"""
מודול המכיל את השירות לניהול הזמנות.
"""
from typing import Dict, Any, List, Optional
from src.services.base.base_service import BaseService, ServiceResponse
from ..api.woocommerce_api import WooCommerceAPI

class OrderService(BaseService):
    """
    שירות לניהול הזמנות בחנות.
    מספק פעולות ליצירה, עדכון, ביטול והחזרים של הזמנות.
    """
    
    def __init__(self, api: WooCommerceAPI):
        """
        אתחול השירות.
        
        Args:
            api: מופע של WooCommerceAPI לתקשורת עם החנות
        """
        super().__init__()
        self.api = api
    
    async def initialize(self) -> None:
        """אתחול השירות."""
        # אין צורך באתחול מיוחד כרגע
        pass
    
    async def shutdown(self) -> None:
        """סגירת השירות."""
        # אין צורך בסגירה מיוחדת כרגע
        pass
    
    async def create_order(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יוצר הזמנה חדשה.
        
        Args:
            data: נתוני ההזמנה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        required_params = ['line_items', 'billing']
        return await self._handle_request(
            'create_order',
            self._create_order,
            data,
            required_params
        )
    
    async def update_order(self, order_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        מעדכן הזמנה קיימת.
        
        Args:
            order_id: מזהה ההזמנה
            data: נתונים לעדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'update_order',
            lambda params: self._update_order(order_id, params),
            data
        )
    
    async def cancel_order(self, order_id: int, reason: Optional[str] = None) -> ServiceResponse:
        """
        מבטל הזמנה.
        
        Args:
            order_id: מזהה ההזמנה
            reason: סיבת הביטול (אופציונלי)
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        data = {
            'status': 'cancelled',
            'customer_note': reason if reason else 'ההזמנה בוטלה'
        }
        return await self._handle_request(
            'cancel_order',
            lambda params: self._update_order(order_id, params),
            data
        )
    
    async def refund_order(
        self,
        order_id: int,
        amount: float,
        reason: Optional[str] = None
    ) -> ServiceResponse:
        """
        מבצע החזר כספי להזמנה.
        
        Args:
            order_id: מזהה ההזמנה
            amount: סכום ההחזר
            reason: סיבת ההחזר (אופציונלי)
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        data = {
            'amount': str(amount),
            'reason': reason if reason else 'החזר כספי'
        }
        return await self._handle_request(
            'refund_order',
            lambda params: self._create_refund(order_id, params),
            data
        )
    
    async def get_order(self, order_id: int) -> ServiceResponse:
        """
        מחזיר הזמנה לפי מזהה.
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'get_order',
            lambda _: self._get_order(order_id),
            {}
        )
    
    async def list_orders(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מחזיר רשימת הזמנות.
        
        Args:
            params: פרמטרים לסינון וחיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_orders',
            self._list_orders,
            params or {}
        )
    
    async def get_order_status(self, order_id: int) -> ServiceResponse:
        """
        מחזיר את סטטוס ההזמנה.
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        response = await self.get_order(order_id)
        if not response.success:
            return response
            
        return self._create_success_response(
            "סטטוס ההזמנה הוחזר בהצלחה",
            {'status': response.data.get('status')}
        )
    
    # Private methods
    async def _create_order(self, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל ביצירת הזמנה."""
        status, response = await self.api.create_order(data)
        
        if status == 201:
            return self._create_success_response(
                "ההזמנה נוצרה בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה ביצירת ההזמנה",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _update_order(self, order_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל בעדכון הזמנה."""
        status, response = await self.api.update_order(order_id, data)
        
        if status == 200:
            return self._create_success_response(
                "ההזמנה עודכנה בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בעדכון ההזמנה",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_order(self, order_id: int) -> ServiceResponse:
        """מטפל בקבלת הזמנה."""
        status, response = await self.api.get_order(order_id)
        
        if status == 200:
            return self._create_success_response(
                "ההזמנה נמצאה בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בקבלת ההזמנה",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _list_orders(self, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת רשימת הזמנות."""
        status, response = await self.api.list_orders(params)
        
        if status == 200:
            return self._create_success_response(
                "רשימת ההזמנות הוחזרה בהצלחה",
                {'orders': response}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת ההזמנות",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _create_refund(self, order_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל ביצירת החזר כספי."""
        # כאן צריך להוסיף את הלוגיקה מול WooCommerce ליצירת החזר
        # כרגע זה רק מעדכן את סטטוס ההזמנה
        data['status'] = 'refunded'
        return await self._update_order(order_id, data) 