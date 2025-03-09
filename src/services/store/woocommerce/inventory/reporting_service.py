"""
מודול המכיל את השירות לדוחות מלאי.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.services.base.base_service import BaseService, ServiceResponse
from ..api.woocommerce_api import WooCommerceAPI

class ReportingService(BaseService):
    """
    שירות לדוחות מלאי.
    מספק דוחות מקיפים על מצב המלאי, מגמות ותנועות.
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
    
    async def get_inventory_summary(self) -> ServiceResponse:
        """
        מפיק סיכום מלאי כללי.
        
        Returns:
            ServiceResponse עם סיכום המלאי
        """
        return await self._handle_request(
            'get_inventory_summary',
            self._get_inventory_summary,
            {}
        )
    
    async def get_stock_movements(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ServiceResponse:
        """
        מפיק דוח תנועות מלאי.
        
        Args:
            start_date: תאריך התחלה (אופציונלי)
            end_date: תאריך סיום (אופציונלי)
            
        Returns:
            ServiceResponse עם תנועות המלאי
        """
        params = {}
        if start_date:
            params['after'] = start_date.isoformat()
        if end_date:
            params['before'] = end_date.isoformat()
            
        return await self._handle_request(
            'get_stock_movements',
            self._get_stock_movements,
            params
        )
    
    async def get_category_report(self) -> ServiceResponse:
        """
        מפיק דוח מלאי לפי קטגוריות.
        
        Returns:
            ServiceResponse עם דוח הקטגוריות
        """
        return await self._handle_request(
            'get_category_report',
            self._get_category_report,
            {}
        )
    
    async def get_valuation_report(self) -> ServiceResponse:
        """
        מפיק דוח שווי מלאי.
        
        Returns:
            ServiceResponse עם דוח השווי
        """
        return await self._handle_request(
            'get_valuation_report',
            self._get_valuation_report,
            {}
        )
    
    # Private methods
    async def _get_inventory_summary(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בהפקת סיכום מלאי."""
        # קבלת כל המוצרים
        status, products = await self.api.list_products()
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצרים",
                str(products.get('message', 'Unknown error')),
                products
            )
            
        # חישוב סיכומים
        total_products = len(products)
        total_stock = sum(
            product.get('stock_quantity', 0)
            for product in products
        )
        total_value = sum(
            product.get('stock_quantity', 0) * float(product.get('price', 0))
            for product in products
        )
        out_of_stock = sum(
            1 for product in products
            if product.get('stock_status') == 'outofstock'
        )
        
        return self._create_success_response(
            "סיכום המלאי הופק בהצלחה",
            {
                'total_products': total_products,
                'total_stock': total_stock,
                'total_value': total_value,
                'out_of_stock': out_of_stock,
                'in_stock': total_products - out_of_stock,
                'average_stock_per_product': total_stock / total_products if total_products > 0 else 0
            }
        )
    
    async def _get_stock_movements(self, params: Dict[str, Any]) -> ServiceResponse:
        """מטפל בהפקת דוח תנועות מלאי."""
        # קבלת הזמנות בטווח התאריכים
        status, orders = await self.api.list_orders(params)
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני ההזמנות",
                str(orders.get('message', 'Unknown error')),
                orders
            )
            
        # ניתוח תנועות לפי מוצר
        movements = {}
        for order in orders:
            date = datetime.fromisoformat(order.get('date_created'))
            for item in order.get('line_items', []):
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)
                
                if product_id not in movements:
                    movements[product_id] = {
                        'product_id': product_id,
                        'name': item.get('name'),
                        'total_out': 0,
                        'movements': []
                    }
                    
                movements[product_id]['total_out'] += quantity
                movements[product_id]['movements'].append({
                    'date': date.isoformat(),
                    'quantity': quantity,
                    'order_id': order.get('id'),
                    'type': 'out'
                })
        
        return self._create_success_response(
            "דוח תנועות המלאי הופק בהצלחה",
            {'movements': list(movements.values())}
        )
    
    async def _get_category_report(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בהפקת דוח קטגוריות."""
        # קבלת כל הקטגוריות
        status, categories = await self.api.list_categories()
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני הקטגוריות",
                str(categories.get('message', 'Unknown error')),
                categories
            )
            
        # קבלת כל המוצרים
        status, products = await self.api.list_products()
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצרים",
                str(products.get('message', 'Unknown error')),
                products
            )
            
        # ניתוח מלאי לפי קטגוריה
        category_stats = {
            category.get('id'): {
                'id': category.get('id'),
                'name': category.get('name'),
                'total_products': 0,
                'total_stock': 0,
                'total_value': 0,
                'out_of_stock': 0
            }
            for category in categories
        }
        
        for product in products:
            for category in product.get('categories', []):
                category_id = category.get('id')
                if category_id in category_stats:
                    stats = category_stats[category_id]
                    stats['total_products'] += 1
                    stats['total_stock'] += product.get('stock_quantity', 0)
                    stats['total_value'] += (
                        product.get('stock_quantity', 0) *
                        float(product.get('price', 0))
                    )
                    if product.get('stock_status') == 'outofstock':
                        stats['out_of_stock'] += 1
        
        return self._create_success_response(
            "דוח הקטגוריות הופק בהצלחה",
            {'categories': list(category_stats.values())}
        )
    
    async def _get_valuation_report(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בהפקת דוח שווי מלאי."""
        # קבלת כל המוצרים
        status, products = await self.api.list_products()
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצרים",
                str(products.get('message', 'Unknown error')),
                products
            )
            
        # חישוב שווי לכל מוצר
        valuations = []
        total_value = 0
        
        for product in products:
            stock = product.get('stock_quantity', 0)
            price = float(product.get('price', 0))
            value = stock * price
            total_value += value
            
            if stock > 0:  # רק מוצרים עם מלאי
                valuations.append({
                    'product_id': product.get('id'),
                    'name': product.get('name'),
                    'stock': stock,
                    'price': price,
                    'value': value
                })
        
        # מיון לפי שווי
        valuations.sort(key=lambda x: x['value'], reverse=True)
        
        return self._create_success_response(
            "דוח שווי המלאי הופק בהצלחה",
            {
                'total_value': total_value,
                'valuations': valuations,
                'summary': {
                    'total_products_with_stock': len(valuations),
                    'average_value_per_product': total_value / len(valuations) if valuations else 0
                }
            }
        ) 