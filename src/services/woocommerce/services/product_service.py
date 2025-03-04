"""
מודול המכיל את השירות לניהול מוצרים.
"""
from typing import Dict, Any, List, Optional
from ..base.base_service import BaseService, ServiceResponse
from .woocommerce_api import WooCommerceAPI

class ProductService(BaseService):
    """
    שירות לניהול מוצרים בחנות.
    מספק פעולות ליצירה, עדכון, מחיקה וחיפוש של מוצרים.
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
    
    async def create_product(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יוצר מוצר חדש.
        
        Args:
            data: נתוני המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        required_params = ['name', 'regular_price']
        return await self._handle_request(
            'create_product',
            self._create_product,
            data,
            required_params
        )
    
    async def update_product(self, product_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        מעדכן מוצר קיים.
        
        Args:
            product_id: מזהה המוצר
            data: נתונים לעדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'update_product',
            lambda params: self._update_product(product_id, params),
            data
        )
    
    async def delete_product(self, product_id: int) -> ServiceResponse:
        """
        מוחק מוצר.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'delete_product',
            lambda _: self._delete_product(product_id),
            {}
        )
    
    async def get_product(self, product_id: int) -> ServiceResponse:
        """
        מחזיר מוצר לפי מזהה.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'get_product',
            lambda _: self._get_product(product_id),
            {}
        )
    
    async def list_products(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מחזיר רשימת מוצרים.
        
        Args:
            params: פרמטרים לסינון וחיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_products',
            self._list_products,
            params or {}
        )
    
    async def search_products(self, query: str) -> ServiceResponse:
        """
        מחפש מוצרים לפי מחרוזת חיפוש.
        
        Args:
            query: מחרוזת החיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {'search': query}
        return await self._handle_request(
            'search_products',
            self._list_products,
            params
        )
    
    # Private methods
    async def _create_product(self, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל ביצירת מוצר."""
        status, response = await self.api.create_product(data)
        
        if status == 201:
            return self._create_success_response(
                "המוצר נוצר בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה ביצירת המוצר",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _update_product(self, product_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """מטפל בעדכון מוצר."""
        status, response = await self.api.update_product(product_id, data)
        
        if status == 200:
            return self._create_success_response(
                "המוצר עודכן בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בעדכון המוצר",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _delete_product(self, product_id: int) -> ServiceResponse:
        """מטפל במחיקת מוצר."""
        status, response = await self.api.delete_product(product_id)
        
        if status == 200:
            return self._create_success_response(
                "המוצר נמחק בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה במחיקת המוצר",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_product(self, product_id: int) -> ServiceResponse:
        """מטפל בקבלת מוצר."""
        status, response = await self.api.get_product(product_id)
        
        if status == 200:
            return self._create_success_response(
                "המוצר נמצא בהצלחה",
                response
            )
        
        return self._create_error_response(
            "שגיאה בקבלת המוצר",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _list_products(self, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת רשימת מוצרים."""
        status, response = await self.api.list_products(params)
        
        if status == 200:
            return self._create_success_response(
                "רשימת המוצרים הוחזרה בהצלחה",
                {'products': response}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת המוצרים",
            str(response.get('message', 'Unknown error')),
            response
        ) 