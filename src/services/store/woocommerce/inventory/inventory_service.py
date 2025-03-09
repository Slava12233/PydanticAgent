"""
מודול המכיל את השירות לניהול מלאי.
"""
from typing import Dict, Any, List, Optional
from src.services.base.base_service import BaseService, ServiceResponse
from ..api.woocommerce_api import WooCommerceAPI

class InventoryService(BaseService):
    """
    שירות לניהול מלאי בחנות.
    מספק פעולות לבדיקה, עדכון ומעקב אחר מלאי.
    """
    
    def __init__(self, api: WooCommerceAPI):
        """
        אתחול השירות.
        
        Args:
            api: מופע של WooCommerceAPI לתקשורת עם החנות
        """
        super().__init__()
        self.api = api
        self._low_stock_threshold = 5  # ברירת מחדל לסף מלאי נמוך
    
    async def initialize(self) -> None:
        """אתחול השירות."""
        # אין צורך באתחול מיוחד כרגע
        pass
    
    async def shutdown(self) -> None:
        """סגירת השירות."""
        # אין צורך בסגירה מיוחדת כרגע
        pass
    
    def set_low_stock_threshold(self, threshold: int) -> None:
        """
        קביעת סף למלאי נמוך.
        
        Args:
            threshold: הסף החדש
        """
        self._low_stock_threshold = threshold
    
    async def check_stock(self, product_id: int) -> ServiceResponse:
        """
        בודק את המלאי של מוצר.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הבדיקה
        """
        return await self._handle_request(
            'check_stock',
            lambda _: self._check_stock(product_id),
            {}
        )
    
    async def update_stock(
        self,
        product_id: int,
        quantity: int,
        operation: str = 'set'
    ) -> ServiceResponse:
        """
        מעדכן את המלאי של מוצר.
        
        Args:
            product_id: מזהה המוצר
            quantity: הכמות לעדכון
            operation: סוג העדכון ('set', 'add', 'subtract')
            
        Returns:
            ServiceResponse עם תוצאת העדכון
        """
        data = {
            'quantity': quantity,
            'operation': operation
        }
        return await self._handle_request(
            'update_stock',
            lambda params: self._update_stock(product_id, params),
            data
        )
    
    async def get_low_stock_products(self) -> ServiceResponse:
        """
        מחזיר רשימה של מוצרים במלאי נמוך.
        
        Returns:
            ServiceResponse עם רשימת המוצרים
        """
        return await self._handle_request(
            'get_low_stock_products',
            self._get_low_stock_products,
            {}
        )
    
    async def get_out_of_stock_products(self) -> ServiceResponse:
        """
        מחזיר רשימה של מוצרים שאזלו מהמלאי.
        
        Returns:
            ServiceResponse עם רשימת המוצרים
        """
        return await self._handle_request(
            'get_out_of_stock_products',
            self._get_out_of_stock_products,
            {}
        )
    
    async def get_inventory_report(self) -> ServiceResponse:
        """
        מפיק דוח מלאי מקיף.
        
        Returns:
            ServiceResponse עם דוח המלאי
        """
        return await self._handle_request(
            'get_inventory_report',
            self._get_inventory_report,
            {}
        )
    
    # Private methods
    async def _check_stock(self, product_id: int) -> ServiceResponse:
        """מטפל בבדיקת מלאי."""
        status, response = await self.api.get_product(product_id)
        
        if status == 200:
            stock_quantity = response.get('stock_quantity', 0)
            stock_status = response.get('stock_status', 'outofstock')
            
            return self._create_success_response(
                "בדיקת המלאי הושלמה בהצלחה",
                {
                    'product_id': product_id,
                    'stock_quantity': stock_quantity,
                    'stock_status': stock_status,
                    'is_low_stock': stock_quantity <= self._low_stock_threshold,
                    'is_out_of_stock': stock_status == 'outofstock'
                }
            )
        
        return self._create_error_response(
            "שגיאה בבדיקת המלאי",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _update_stock(self, product_id: int, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בעדכון מלאי."""
        # קבלת המלאי הנוכחי
        status, response = await self.api.get_product(product_id)
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצר",
                str(response.get('message', 'Unknown error')),
                response
            )
            
        current_stock = response.get('stock_quantity', 0)
        operation = params.get('operation', 'set')
        quantity = params.get('quantity', 0)
        
        # חישוב הכמות החדשה
        if operation == 'set':
            new_stock = quantity
        elif operation == 'add':
            new_stock = current_stock + quantity
        elif operation == 'subtract':
            new_stock = current_stock - quantity
        else:
            return self._create_error_response(
                "סוג העדכון אינו תקין",
                f"Operation {operation} is not supported",
                params
            )
        
        # עדכון המלאי
        status, response = await self.api.update_product(
            product_id,
            {'stock_quantity': new_stock}
        )
        
        if status == 200:
            return self._create_success_response(
                "המלאי עודכן בהצלחה",
                {
                    'product_id': product_id,
                    'previous_stock': current_stock,
                    'new_stock': new_stock,
                    'operation': operation,
                    'quantity': quantity
                }
            )
        
        return self._create_error_response(
            "שגיאה בעדכון המלאי",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_low_stock_products(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת מוצרים במלאי נמוך."""
        status, response = await self.api.list_products({'stock_status': 'instock'})
        
        if status == 200:
            low_stock_products = [
                product for product in response
                if product.get('stock_quantity', 0) <= self._low_stock_threshold
            ]
            
            return self._create_success_response(
                "רשימת המוצרים במלאי נמוך הוחזרה בהצלחה",
                {'products': low_stock_products}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת המוצרים במלאי נמוך",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_out_of_stock_products(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בקבלת מוצרים שאזלו מהמלאי."""
        status, response = await self.api.list_products({'stock_status': 'outofstock'})
        
        if status == 200:
            return self._create_success_response(
                "רשימת המוצרים שאזלו מהמלאי הוחזרה בהצלחה",
                {'products': response}
            )
        
        return self._create_error_response(
            "שגיאה בקבלת רשימת המוצרים שאזלו מהמלאי",
            str(response.get('message', 'Unknown error')),
            response
        )
    
    async def _get_inventory_report(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בהפקת דוח מלאי."""
        # קבלת כל המוצרים
        status, response = await self.api.list_products()
        
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצרים",
                str(response.get('message', 'Unknown error')),
                response
            )
            
        # ניתוח הנתונים
        total_products = len(response)
        total_stock = sum(
            product.get('stock_quantity', 0)
            for product in response
        )
        low_stock_products = [
            product for product in response
            if product.get('stock_quantity', 0) <= self._low_stock_threshold
        ]
        out_of_stock_products = [
            product for product in response
            if product.get('stock_status') == 'outofstock'
        ]
        
        return self._create_success_response(
            "דוח המלאי הופק בהצלחה",
            {
                'summary': {
                    'total_products': total_products,
                    'total_stock': total_stock,
                    'average_stock': total_stock / total_products if total_products > 0 else 0,
                    'low_stock_count': len(low_stock_products),
                    'out_of_stock_count': len(out_of_stock_products)
                },
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products
            }
        ) 