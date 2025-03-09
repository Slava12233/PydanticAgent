"""
מודול המכיל את השירות לתחזיות מלאי.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.services.base.base_service import BaseService, ServiceResponse
from ..api.woocommerce_api import WooCommerceAPI

class ForecastingService(BaseService):
    """
    שירות לתחזיות מלאי.
    מספק פעולות לחיזוי צריכת מלאי ונקודות הזמנה מחדש.
    """
    
    def __init__(self, api: WooCommerceAPI):
        """
        אתחול השירות.
        
        Args:
            api: מופע של WooCommerceAPI לתקשורת עם החנות
        """
        super().__init__()
        self.api = api
        self._safety_stock_days = 14  # ברירת מחדל למלאי בטחון
        self._lead_time_days = 7  # ברירת מחדל לזמן אספקה
    
    async def initialize(self) -> None:
        """אתחול השירות."""
        # אין צורך באתחול מיוחד כרגע
        pass
    
    async def shutdown(self) -> None:
        """סגירת השירות."""
        # אין צורך בסגירה מיוחדת כרגע
        pass
    
    def set_safety_stock_days(self, days: int) -> None:
        """
        קביעת ימי מלאי בטחון.
        
        Args:
            days: מספר הימים
        """
        self._safety_stock_days = days
    
    def set_lead_time_days(self, days: int) -> None:
        """
        קביעת זמן אספקה.
        
        Args:
            days: מספר הימים
        """
        self._lead_time_days = days
    
    async def forecast_inventory(
        self,
        product_id: int,
        days: int = 30
    ) -> ServiceResponse:
        """
        מבצע תחזית מלאי למוצר.
        
        Args:
            product_id: מזהה המוצר
            days: מספר ימים לתחזית
            
        Returns:
            ServiceResponse עם תוצאת התחזית
        """
        return await self._handle_request(
            'forecast_inventory',
            lambda _: self._forecast_inventory(product_id, days),
            {}
        )
    
    async def get_reorder_points(self) -> ServiceResponse:
        """
        מחזיר נקודות הזמנה מחדש לכל המוצרים.
        
        Returns:
            ServiceResponse עם נקודות ההזמנה
        """
        return await self._handle_request(
            'get_reorder_points',
            self._get_reorder_points,
            {}
        )
    
    async def get_seasonal_products(self) -> ServiceResponse:
        """
        מזהה מוצרים עונתיים.
        
        Returns:
            ServiceResponse עם המוצרים העונתיים
        """
        return await self._handle_request(
            'get_seasonal_products',
            self._get_seasonal_products,
            {}
        )
    
    # Private methods
    async def _forecast_inventory(self, product_id: int, days: int) -> ServiceResponse:
        """מטפל בתחזית מלאי."""
        # קבלת נתוני המוצר
        status, product = await self.api.get_product(product_id)
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצר",
                str(product.get('message', 'Unknown error')),
                product
            )
            
        # קבלת היסטוריית הזמנות
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 90 ימים אחורה לניתוח
        
        status, orders = await self.api.list_orders({
            'product': product_id,
            'after': start_date.isoformat(),
            'before': end_date.isoformat()
        })
        
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת היסטוריית הזמנות",
                str(orders.get('message', 'Unknown error')),
                orders
            )
            
        # חישוב קצב מכירות יומי
        total_sold = sum(
            sum(
                item.get('quantity', 0)
                for item in order.get('line_items', [])
                if item.get('product_id') == product_id
            )
            for order in orders
        )
        daily_sales = total_sold / 90 if total_sold > 0 else 0
        
        # חישוב תחזית
        current_stock = product.get('stock_quantity', 0)
        days_until_stockout = current_stock / daily_sales if daily_sales > 0 else float('inf')
        
        # חישוב נקודת הזמנה מחדש
        safety_stock = daily_sales * self._safety_stock_days
        reorder_point = safety_stock + (daily_sales * self._lead_time_days)
        
        # חישוב כמות מומלצת להזמנה
        recommended_order = max(0, reorder_point - current_stock)
        
        return self._create_success_response(
            "תחזית המלאי הופקה בהצלחה",
            {
                'current_stock': current_stock,
                'daily_sales': daily_sales,
                'days_until_stockout': days_until_stockout,
                'safety_stock': safety_stock,
                'reorder_point': reorder_point,
                'recommended_order': recommended_order,
                'forecast': {
                    'days': days,
                    'expected_sales': daily_sales * days,
                    'expected_stock': max(0, current_stock - (daily_sales * days)),
                    'needs_reorder': current_stock <= reorder_point
                }
            }
        )
    
    async def _get_reorder_points(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בחישוב נקודות הזמנה מחדש."""
        # קבלת כל המוצרים
        status, products = await self.api.list_products()
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת נתוני המוצרים",
                str(products.get('message', 'Unknown error')),
                products
            )
            
        reorder_points = []
        for product in products:
            product_id = product.get('id')
            forecast = await self.forecast_inventory(product_id)
            
            if forecast.success:
                reorder_points.append({
                    'product_id': product_id,
                    'name': product.get('name'),
                    'current_stock': product.get('stock_quantity', 0),
                    'reorder_point': forecast.data.get('reorder_point', 0),
                    'recommended_order': forecast.data.get('recommended_order', 0),
                    'needs_reorder': forecast.data.get('forecast', {}).get('needs_reorder', False)
                })
        
        return self._create_success_response(
            "נקודות ההזמנה מחדש חושבו בהצלחה",
            {'reorder_points': reorder_points}
        )
    
    async def _get_seasonal_products(self, _: Dict[str, Any]) -> ServiceResponse:
        """מטפל בזיהוי מוצרים עונתיים."""
        # קבלת היסטוריית הזמנות לשנה אחרונה
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        status, orders = await self.api.list_orders({
            'after': start_date.isoformat(),
            'before': end_date.isoformat()
        })
        
        if status != 200:
            return self._create_error_response(
                "שגיאה בקבלת היסטוריית הזמנות",
                str(orders.get('message', 'Unknown error')),
                orders
            )
            
        # ניתוח מכירות לפי חודשים
        monthly_sales = {}
        for order in orders:
            month = datetime.fromisoformat(order.get('date_created')).strftime('%Y-%m')
            for item in order.get('line_items', []):
                product_id = item.get('product_id')
                quantity = item.get('quantity', 0)
                
                if product_id not in monthly_sales:
                    monthly_sales[product_id] = {}
                    
                if month not in monthly_sales[product_id]:
                    monthly_sales[product_id][month] = 0
                    
                monthly_sales[product_id][month] += quantity
        
        # זיהוי מוצרים עם תנודתיות גבוהה
        seasonal_products = []
        for product_id, sales in monthly_sales.items():
            if len(sales) >= 3:  # לפחות 3 חודשי מכירות
                values = list(sales.values())
                avg = sum(values) / len(values)
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                
                if variance > (avg * 0.5):  # תנודתיות גבוהה
                    status, product = await self.api.get_product(product_id)
                    if status == 200:
                        seasonal_products.append({
                            'product_id': product_id,
                            'name': product.get('name'),
                            'monthly_sales': sales,
                            'average_sales': avg,
                            'variance': variance
                        })
        
        return self._create_success_response(
            "המוצרים העונתיים זוהו בהצלחה",
            {'seasonal_products': seasonal_products}
        ) 