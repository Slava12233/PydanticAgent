"""
מודול המכיל את השירות לניהול הזמנות.
"""
from typing import Dict, Any, List, Optional
from src.services.base.base_service import BaseService, ServiceResponse
from src.woocommerce.api.api import WooCommerceAPI

class OrderService(BaseService):
    """
    שירות לניהול הזמנות בחנות.
    מספק פעולות ליצירה, עדכון, מחיקה וחיפוש של הזמנות.
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
    
    async def get_order(self, order_id: int) -> ServiceResponse:
        """
        מקבל מידע על הזמנה.
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'get_order',
            self._get_order,
            order_id
        )
    
    async def list_orders(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מקבל רשימת הזמנות.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_orders',
            self._list_orders,
            params or {}
        )
    
    async def update_order_status(self, order_id: int, status: str) -> ServiceResponse:
        """
        עדכון סטטוס הזמנה.
        
        Args:
            order_id: מזהה ההזמנה
            status: הסטטוס החדש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        data = {"status": status}
        return await self._handle_request(
            'update_order_status',
            self._update_order,
            order_id,
            data
        )
    
    async def search_orders(self, query: str) -> ServiceResponse:
        """
        חיפוש הזמנות לפי מחרוזת חיפוש.
        
        Args:
            query: מחרוזת החיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'search': query,
            'per_page': 20
        }
        
        return await self._handle_request(
            'search_orders',
            self._list_orders,
            params
        )
    
    async def get_orders_by_customer(self, customer_id: int) -> ServiceResponse:
        """
        קבלת הזמנות של לקוח מסוים.
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'customer': customer_id,
            'per_page': 50
        }
        
        return await self._handle_request(
            'get_orders_by_customer',
            self._list_orders,
            params
        )
    
    async def get_orders_by_status(self, status: str) -> ServiceResponse:
        """
        קבלת הזמנות לפי סטטוס.
        
        Args:
            status: סטטוס ההזמנות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'status': status,
            'per_page': 50
        }
        
        return await self._handle_request(
            'get_orders_by_status',
            self._list_orders,
            params
        )
    
    async def get_recent_orders(self, limit: int = 10) -> ServiceResponse:
        """
        קבלת ההזמנות האחרונות.
        
        Args:
            limit: מספר ההזמנות לקבלה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'per_page': limit,
            'orderby': 'date',
            'order': 'desc'
        }
        
        return await self._handle_request(
            'get_recent_orders',
            self._list_orders,
            params
        )
    
    async def _get_order(self, order_id: int) -> ServiceResponse:
        """
        קבלת מידע על הזמנה - מימוש פנימי.
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.get_order(order_id)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת ההזמנה: {status_code}",
                data=response
            )
    
    async def _list_orders(self, params: Dict[str, Any]) -> ServiceResponse:
        """
        קבלת רשימת הזמנות - מימוש פנימי.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.get_orders(params)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת רשימת ההזמנות: {status_code}",
                data=response
            )
    
    async def _update_order(self, order_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        עדכון הזמנה - מימוש פנימי.
        
        Args:
            order_id: מזהה ההזמנה
            data: נתוני העדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.update_order(order_id, data)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response,
                message="ההזמנה עודכנה בהצלחה"
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בעדכון ההזמנה: {status_code}",
                data=response
            ) 