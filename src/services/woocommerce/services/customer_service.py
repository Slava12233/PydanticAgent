"""
מודול המכיל את השירות לניהול לקוחות.
"""
from typing import Dict, Any, List, Optional
from ..base.base_service import BaseService, ServiceResponse
from .woocommerce_api import WooCommerceAPI

class CustomerService(BaseService):
    """
    שירות לניהול לקוחות בחנות.
    מספק פעולות ליצירה, עדכון, מחיקה וחיפוש של לקוחות.
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
    
    async def create_customer(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יוצר לקוח חדש.
        
        Args:
            data: נתוני הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        required_params = ['email', 'first_name', 'last_name']
        return await self._handle_request(
            'create_customer',
            self._create_customer,
            data,
            required_params
        )
    
    async def update_customer(self, customer_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        מעדכן לקוח קיים.
        
        Args:
            customer_id: מזהה הלקוח
            data: נתונים לעדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'update_customer',
            lambda params: self._update_customer(customer_id, params),
            data
        )
    
    async def delete_customer(self, customer_id: int) -> ServiceResponse:
        """
        מוחק לקוח.
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'delete_customer',
            lambda _: self._delete_customer(customer_id),
            {}
        )
    
    async def get_customer(self, customer_id: int) -> ServiceResponse:
        """
        מחזיר לקוח לפי מזהה.
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'get_customer',
            lambda _: self._get_customer(customer_id),
            {}
        )
    
    async def list_customers(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מחזיר רשימת לקוחות.
        
        Args:
            params: פרמטרים לסינון וחיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_customers',
            self._list_customers,
            params or {}
        )
    
    async def search_customers(self, query: str) -> ServiceResponse:
        """
        מחפש לקוחות לפי מחרוזת חיפוש.
        
        Args:
            query: מחרוזת החיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {'search': query}
        return await self._handle_request(
            'search_customers',
            self._list_customers,
            params
        )
    
    async def get_customer_orders(self, customer_id: int) -> ServiceResponse:
        """
        מחזיר את ההזמנות של לקוח.
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {'customer': customer_id}
        return await self._handle_request(
            'get_customer_orders',
            self._list_customer_orders,
            params
        )
    
    # Private methods
    async def _create_customer(self, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל ביצירת לקוח."""
        status, response = await self.api.create_customer(data)
        
        if status == 201:
            return self._create_success_response(
                "הלקוח נוצר בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה ביצירת הלקוח",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _update_customer(self, customer_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל בעדכון לקוח."""
        status, response = await self.api.update_customer(customer_id, data)
        
        if status == 200:
            return self._create_success_response(
                "הלקוח עודכן בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בעדכון הלקוח",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _delete_customer(self, customer_id: int) -> ServiceResponse:
        """מטפל במחיקת לקוח."""
        status, response = await self.api.delete_customer(customer_id)
        
        if status == 200:
            return self._create_success_response(
                "הלקוח נמחק בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה במחיקת הלקוח",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_customer(self, customer_id: int) -> ServiceResponse:
        """מטפל בקבלת לקוח."""
        status, response = await self.api.get_customer(customer_id)
        
        if status == 200:
            return self._create_success_response(
                "הלקוח נמצא בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בקבלת הלקוח",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _list_customers(self, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת רשימת לקוחות."""
        status, response = await self.api.list_customers(params)
        
        if status == 200:
            return self._create_success_response(
                "רשימת הלקוחות הוחזרה בהצלחה",
                {'customers': response}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת הלקוחות",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _list_customer_orders(self, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת רשימת הזמנות של לקוח."""
        status, response = await self.api.list_orders(params)
        
        if status == 200:
            return self._create_success_response(
                "רשימת ההזמנות של הלקוח הוחזרה בהצלחה",
                {'orders': response}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת ההזמנות של הלקוח",
            str(response.get('message', 'Unknown error')),
            response
        ) 