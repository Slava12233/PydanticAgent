"""
בדיקות למודול ניתוח מכירות
"""
import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.tools.managers.sales_analyzer import SalesAnalyzer, get_sales_report, get_top_selling_products

class AsyncTestCase(unittest.TestCase):
    """מחלקת בסיס לבדיקות אסינכרוניות"""
    
    def run_async(self, coro):
        """הרצת פונקציה אסינכרונית בבדיקה"""
        return asyncio.run(coro)

class TestSalesAnalyzer(AsyncTestCase):
    """בדיקות למנהל ניתוח מכירות"""
    
    def setUp(self):
        """הכנה לבדיקות"""
        # יצירת מופע API מדומה
        self.mock_api = MagicMock()
        
        # יצירת מנהל ניתוח מכירות עם ה-API המדומה
        self.sales_analyzer = SalesAnalyzer(self.mock_api, use_cache=False)
        
        # הגדרת התנהגות ברירת מחדל ל-API המדומה
        async def mock_make_request(method, endpoint, params=None, data=None):
            """פונקציה מדומה לביצוע בקשות API"""
            if endpoint == "orders":
                # החזרת רשימת הזמנות מדומה
                return 200, self._get_mock_orders()
            return 200, []
        
        self.mock_api._make_request = mock_make_request
    
    def _get_mock_orders(self):
        """יצירת רשימת הזמנות מדומה לבדיקות"""
        now = datetime.now()
        
        # יצירת 10 הזמנות מדומות
        orders = []
        for i in range(1, 11):
            # יצירת תאריך הזמנה (הזמנות מהחודש האחרון)
            order_date = now - timedelta(days=i * 3)
            
            # יצירת פריטים בהזמנה
            line_items = []
            for j in range(1, 4):  # 3 פריטים בכל הזמנה
                line_items.append({
                    "product_id": j,
                    "name": f"מוצר לדוגמה {j}",
                    "quantity": j,
                    "price": f"{j * 50}",
                    "total": f"{j * j * 50}",
                    "sku": f"SKU-{j}"
                })
            
            # יצירת ההזמנה
            orders.append({
                "id": i,
                "date_created": order_date.isoformat(),
                "status": "completed" if i % 3 != 0 else "processing",
                "total": str(sum(int(item["total"]) for item in line_items)),
                "customer_id": i % 5 + 1,  # 5 לקוחות שונים
                "line_items": line_items,
                "billing": {
                    "first_name": f"שם {i % 5 + 1}",
                    "last_name": f"משפחה {i % 5 + 1}",
                    "email": f"customer{i % 5 + 1}@example.com"
                }
            })
        
        return orders
    
    def test_init(self):
        """בדיקת אתחול מנהל ניתוח מכירות"""
        self.assertIsNotNone(self.sales_analyzer)
        self.assertEqual(self.sales_analyzer.api, self.mock_api)
        self.assertFalse(self.sales_analyzer.using_cache)
    
    def test_get_sales_by_period(self):
        """בדיקת קבלת נתוני מכירות לפי תקופה"""
        # הרצת הפונקציה
        result = self.run_async(self.sales_analyzer.get_sales_by_period())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertIn('total_sales', result)
        self.assertIn('total_orders', result)
        self.assertIn('sales_by_period', result)
        
        # בדיקה שהתקבלו נתונים
        self.assertGreater(result['total_sales'], 0)
        self.assertGreater(result['total_orders'], 0)
        self.assertGreater(len(result['sales_by_period']), 0)
    
    def test_get_top_products(self):
        """בדיקת קבלת המוצרים הנמכרים ביותר"""
        # הרצת הפונקציה
        result = self.run_async(self.sales_analyzer.get_top_products())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertIn('top_products', result)
        
        # בדיקה שהתקבלו מוצרים
        self.assertGreater(len(result['top_products']), 0)
        
        # בדיקת מבנה המוצר הראשון
        first_product = result['top_products'][0]
        self.assertIn('id', first_product)
        self.assertIn('name', first_product)
        self.assertIn('quantity_sold', first_product)
        self.assertIn('revenue', first_product)
    
    def test_get_customer_insights(self):
        """בדיקת קבלת תובנות על לקוחות"""
        # הרצת הפונקציה
        result = self.run_async(self.sales_analyzer.get_customer_insights())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertIn('customer_insights', result)
        
        # בדיקת מבנה התובנות
        insights = result['customer_insights']
        self.assertIn('total_customers', insights)
        self.assertIn('total_orders', insights)
        self.assertIn('total_revenue', insights)
        self.assertIn('top_customers', insights)
        
        # בדיקה שהתקבלו לקוחות
        self.assertGreater(insights['total_customers'], 0)
        self.assertGreater(len(insights['top_customers']), 0)
    
    def test_generate_sales_report(self):
        """בדיקת יצירת דוח מכירות"""
        # הרצת הפונקציה
        result = self.run_async(self.sales_analyzer.generate_sales_report())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertIn('report_type', result)
        self.assertIn('sales_summary', result)
        self.assertIn('top_products', result)
        self.assertIn('customer_insights', result)
        
        # בדיקת פורמט הדוח
        formatted_report = self.sales_analyzer.format_sales_report(result)
        self.assertIsInstance(formatted_report, str)
        self.assertIn('דוח מכירות', formatted_report)
        self.assertIn('סיכום מכירות', formatted_report)
        self.assertIn('מוצרים מובילים', formatted_report)

if __name__ == '__main__':
    unittest.main()
