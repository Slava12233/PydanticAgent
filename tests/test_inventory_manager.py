"""
בדיקות למודול ניהול מלאי
"""
import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.tools.managers.inventory_manager import (
    InventoryManager, 
    format_inventory_forecast,
    format_inventory_report
)

class AsyncTestCase(unittest.TestCase):
    """מחלקת בסיס לבדיקות אסינכרוניות"""
    
    def run_async(self, coro):
        """הרצת פונקציה אסינכרונית בבדיקה"""
        return asyncio.run(coro)

class TestInventoryManager(AsyncTestCase):
    """בדיקות למנהל מלאי"""
    
    def setUp(self):
        """הכנה לבדיקות"""
        # יצירת מופע API מדומה
        self.mock_api = MagicMock()
        
        # יצירת מנהל מלאי עם ה-API המדומה
        self.inventory_manager = InventoryManager(self.mock_api, use_cache=False)
        
        # הגדרת התנהגות ברירת מחדל ל-API המדומה
        async def mock_make_request(method, endpoint, params=None, data=None):
            """פונקציה מדומה לביצוע בקשות API"""
            if endpoint.startswith("products/"):
                # החזרת מוצר מדומה
                return 200, self._get_mock_product(int(endpoint.split("/")[1]))
            elif endpoint == "products":
                # החזרת רשימת מוצרים מדומה
                return 200, self._get_mock_products()
            elif endpoint == "orders":
                # החזרת רשימת הזמנות מדומה
                return 200, self._get_mock_orders()
            return 200, []
        
        self.mock_api._make_request = mock_make_request
        
        # הגדרת התנהגות ברירת מחדל לפונקציות API נוספות
        async def mock_get(endpoint, params=None):
            """פונקציה מדומה לביצוע בקשות GET"""
            status_code, data = await mock_make_request("GET", endpoint, params=params)
            return data
        
        async def mock_put(endpoint, data=None):
            """פונקציה מדומה לביצוע בקשות PUT"""
            status_code, response_data = await mock_make_request("PUT", endpoint, data=data)
            return response_data
        
        self.mock_api.get = mock_get
        self.mock_api.put = mock_put
    
    def _get_mock_product(self, product_id):
        """יצירת מוצר מדומה לבדיקות"""
        return {
            "id": product_id,
            "name": f"מוצר לדוגמה {product_id}",
            "sku": f"SKU-{product_id}",
            "manage_stock": True,
            "in_stock": True,
            "stock_quantity": product_id * 10,
            "stock_status": "instock",
            "backorders_allowed": False,
            "backorders": "no",
            "low_stock_amount": product_id * 2,
            "price": f"{product_id * 50}"
        }
    
    def _get_mock_products(self):
        """יצירת רשימת מוצרים מדומה לבדיקות"""
        products = []
        for i in range(1, 11):
            product = self._get_mock_product(i)
            
            # הגדרת מוצרים מסוימים עם מלאי נמוך
            if i in [3, 7]:
                product["stock_quantity"] = product["low_stock_amount"] - 1
            
            # הגדרת מוצרים מסוימים שאזלו מהמלאי
            if i in [5, 9]:
                product["stock_quantity"] = 0
                product["in_stock"] = False
                product["stock_status"] = "outofstock"
            
            products.append(product)
        
        return products
    
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
        """בדיקת אתחול מנהל מלאי"""
        self.assertIsNotNone(self.inventory_manager)
        self.assertEqual(self.inventory_manager.api, self.mock_api)
        self.assertFalse(self.inventory_manager.using_cache)
    
    def test_get_product_stock(self):
        """בדיקת קבלת מידע על מלאי של מוצר ספציפי"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.get_product_stock(1))
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertEqual(result["product_id"], 1)
        self.assertEqual(result["product_name"], "מוצר לדוגמה 1")
        self.assertEqual(result["stock_quantity"], 10)
        self.assertEqual(result["low_stock_amount"], 2)
    
    def test_update_product_stock(self):
        """בדיקת עדכון מלאי של מוצר"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.update_product_stock(
            product_id=1,
            stock_quantity=20,
            manage_stock=True,
            in_stock=True,
            low_stock_amount=5
        ))
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "מוצר לדוגמה 1")
    
    def test_add_to_stock(self):
        """בדיקת הוספת כמות למלאי קיים"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.add_to_stock(
            product_id=1,
            quantity_to_add=5
        ))
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "מוצר לדוגמה 1")
    
    def test_remove_from_stock(self):
        """בדיקת הורדת כמות מהמלאי הקיים"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.remove_from_stock(
            product_id=1,
            quantity_to_remove=5
        ))
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "מוצר לדוגמה 1")
    
    def test_get_low_stock_products(self):
        """בדיקת קבלת רשימת מוצרים עם מלאי נמוך"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.get_low_stock_products())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        # בדיקה שהמוצרים עם מלאי נמוך נמצאים ברשימה
        product_ids = [product["id"] for product in result]
        self.assertIn(3, product_ids)  # מוצר עם מלאי נמוך
        self.assertIn(7, product_ids)  # מוצר עם מלאי נמוך
        
        # בדיקת שדות התראה
        for product in result:
            self.assertIn("alert_level", product)
            self.assertIn("alert_emoji", product)
            self.assertIn("alert_message", product)
    
    def test_get_out_of_stock_products(self):
        """בדיקת קבלת רשימת מוצרים שאזלו מהמלאי"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.get_out_of_stock_products())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        # בדיקה שהמוצרים שאזלו מהמלאי נמצאים ברשימה
        product_ids = [product["id"] for product in result]
        self.assertIn(5, product_ids)  # מוצר שאזל מהמלאי
        self.assertIn(9, product_ids)  # מוצר שאזל מהמלאי
    
    def test_forecast_inventory(self):
        """בדיקת תחזית מלאי למוצר ספציפי"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.forecast_inventory(
            product_id=1,
            days=30
        ))
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertEqual(result["product_id"], 1)
        self.assertEqual(result["product_name"], "מוצר לדוגמה 1")
        self.assertIn("current_stock", result)
        self.assertIn("daily_sales_avg", result)
        self.assertIn("forecasted_end_stock", result)
        self.assertIn("daily_forecast", result)
        
        # בדיקת תחזית יומית
        self.assertGreater(len(result["daily_forecast"]), 0)
        self.assertEqual(len(result["daily_forecast"]), 30)  # 30 ימים
    
    def test_get_inventory_report(self):
        """בדיקת הפקת דוח מלאי כללי"""
        # הרצת הפונקציה
        result = self.run_async(self.inventory_manager.get_inventory_report())
        
        # בדיקת התוצאה
        self.assertIsNotNone(result)
        self.assertIn("summary", result)
        self.assertIn("out_of_stock_products", result)
        self.assertIn("low_stock_products", result)
        
        # בדיקת סיכום
        summary = result["summary"]
        self.assertEqual(summary["total_products"], 10)
        self.assertGreater(summary["products_with_stock_management"], 0)
        self.assertGreater(summary["total_stock_value"], 0)
        self.assertEqual(summary["out_of_stock_count"], 2)  # 2 מוצרים שאזלו מהמלאי
    
    def test_format_inventory_forecast(self):
        """בדיקת פורמט תחזית מלאי לתצוגה"""
        # יצירת תחזית מדומה
        forecast = {
            "product_id": 1,
            "product_name": "מוצר לדוגמה 1",
            "sku": "SKU-1",
            "current_stock": 10,
            "daily_sales_avg": 0.5,
            "days_until_empty": 20,
            "out_of_stock_date": (datetime.now() + timedelta(days=20)).isoformat(),
            "forecast_days": 30,
            "forecasted_end_stock": 0,
            "will_be_out_of_stock": True,
            "reorder_recommendation": True,
            "daily_forecast": [
                {
                    "date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "forecasted_stock": 9.5,
                    "daily_sales": 0.5
                }
            ],
            "historical_data": {
                "days_analyzed": 90,
                "total_sold": 45
            }
        }
        
        # הרצת הפונקציה
        result = format_inventory_forecast(forecast)
        
        # בדיקת התוצאה
        self.assertIsInstance(result, str)
        self.assertIn("מוצר לדוגמה 1", result)
        self.assertIn("10 יחידות", result)
        self.assertIn("0.5 יחידות", result)
        self.assertIn("יש להזמין מלאי נוסף בהקדם", result)
    
    def test_format_inventory_report(self):
        """בדיקת פורמט דוח מלאי לתצוגה"""
        # יצירת דוח מדומה
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_products": 10,
                "products_with_stock_management": 10,
                "total_stock_value": 2750,
                "out_of_stock_count": 2,
                "low_stock_count": 2
            },
            "out_of_stock_products": [
                {
                    "id": 5,
                    "name": "מוצר לדוגמה 5",
                    "sku": "SKU-5"
                },
                {
                    "id": 9,
                    "name": "מוצר לדוגמה 9",
                    "sku": "SKU-9"
                }
            ],
            "low_stock_products": [
                {
                    "id": 3,
                    "name": "מוצר לדוגמה 3",
                    "sku": "SKU-3",
                    "stock_quantity": 5,
                    "low_stock_threshold": 6
                },
                {
                    "id": 7,
                    "name": "מוצר לדוגמה 7",
                    "sku": "SKU-7",
                    "stock_quantity": 13,
                    "low_stock_threshold": 14
                }
            ]
        }
        
        # הרצת הפונקציה
        result = format_inventory_report(report)
        
        # בדיקת התוצאה
        self.assertIsInstance(result, str)
        self.assertIn("דוח מלאי", result)
        self.assertIn("10", result)  # מספר מוצרים
        self.assertIn("2750", result)  # ערך מלאי
        self.assertIn("מוצר לדוגמה 5", result)  # מוצר שאזל מהמלאי
        self.assertIn("מוצר לדוגמה 3", result)  # מוצר עם מלאי נמוך

if __name__ == '__main__':
    unittest.main()
