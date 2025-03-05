"""
מודול לתקשורת עם ה-API של ווקומרס
"""
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import httpx
from urllib.parse import urljoin
import json
import hmac
import hashlib
import base64
import os
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# קבועים
DEFAULT_TIMEOUT = 30  # שניות
DEFAULT_CACHE_TTL = 300  # 5 דקות בשניות

@lru_cache(maxsize=1)
def get_woocommerce_api() -> 'WooCommerceAPI':
    """
    מחזיר מופע של WooCommerceAPI.
    משתמש ב-lru_cache כדי לשמור מופע יחיד.
    
    Returns:
        WooCommerceAPI: מופע של WooCommerceAPI
    """
    # קריאת הגדרות מתוך משתני סביבה
    wc_url = os.getenv('WOOCOMMERCE_URL', 'http://localhost/wordpress')
    wc_consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY', '')
    wc_consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET', '')
    
    return WooCommerceAPI(
        url=wc_url,
        consumer_key=wc_consumer_key,
        consumer_secret=wc_consumer_secret
    )

@lru_cache(maxsize=1)
def get_cached_woocommerce_api() -> 'CachedWooCommerceAPI':
    """
    מחזיר מופע של CachedWooCommerceAPI.
    משתמש ב-lru_cache כדי לשמור מופע יחיד.
    
    Returns:
        CachedWooCommerceAPI: מופע של CachedWooCommerceAPI
    """
    base_api = get_woocommerce_api()
    return CachedWooCommerceAPI(base_api)

class WooCommerceAPI:
    """
    מחלקה לתקשורת עם ה-API של ווקומרס
    """
    
    def __init__(self, url: str, consumer_key: str, consumer_secret: str, version: str = "wc/v3"):
        """
        אתחול המחלקה
        
        Args:
            url: כתובת החנות
            consumer_key: מפתח צרכן
            consumer_secret: סוד צרכן
            version: גרסת ה-API
        """
        self.store_url = url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.store_url}/wp-json/{version}"
        self.timeout = 30.0  # זמן המתנה מקסימלי לבקשות ב-API
        
        # הגדרת מגבלות קצב לבקשות
        self.rate_limit = 10  # מספר בקשות מקסימלי בשנייה
        self.last_request_time = 0
        
        logger.info(f"WooCommerce API initialized for store: {url}")
    
    async def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> Tuple[int, dict]:
        """
        ביצוע בקשה ל-API
        
        Args:
            method: שיטת HTTP (GET, POST, PUT, DELETE)
            endpoint: נקודת קצה ב-API
            params: פרמטרים לבקשה
            data: נתונים לשליחה בבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # שמירה על מגבלת קצב הבקשות
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.0 / self.rate_limit:
            await httpx.AsyncClient().sleep(1.0 / self.rate_limit - time_since_last_request)
        
        self.last_request_time = time.time()
        
        # בניית כתובת מלאה
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # הוספת פרמטרי אימות
        auth_params = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        }
        
        if params:
            params.update(auth_params)
        else:
            params = auth_params
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await client.post(url, params=params, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, params=params, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, params=params, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # בדיקת קוד תשובה
                if response.status_code >= 400:
                    logger.error(f"WooCommerce API error: {response.status_code} - {response.text}")
                
                # ניסיון לפענח את התשובה כ-JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"message": response.text}
                
                return response.status_code, response_data
                
        except httpx.RequestError as e:
            logger.error(f"WooCommerce API request error: {str(e)}")
            return 500, {"message": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"WooCommerce API unexpected error: {str(e)}")
            return 500, {"message": f"Unexpected error: {str(e)}"}
    
    async def test_connection(self) -> bool:
        """
        בדיקת חיבור לחנות
        
        Returns:
            bool: האם החיבור הצליח
        """
        try:
            # ניסיון לקבל מידע בסיסי על החנות
            status_code, response = await self._make_request("GET", "system_status")
            
            if status_code == 200 and isinstance(response, dict):
                logger.info(f"WooCommerce connection test successful: {self.store_url}")
                return True
            else:
                logger.warning(f"WooCommerce connection test failed: {status_code} - {response}")
                return False
                
        except Exception as e:
            logger.error(f"WooCommerce connection test error: {str(e)}")
            return False
    
    async def get_products(self, params: dict = None) -> List[dict]:
        """
        קבלת רשימת מוצרים
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            list: רשימת מוצרים
        """
        default_params = {
            "per_page": 20,
            "page": 1,
            "status": "publish"
        }
        
        if params:
            default_params.update(params)
        
        status_code, response = await self._make_request("GET", "products", params=default_params)
        
        if status_code == 200 and isinstance(response, list):
            return response
        else:
            logger.error(f"Failed to get products: {status_code} - {response}")
            return []
    
    async def get_product(self, product_id: int) -> Optional[dict]:
        """
        קבלת מוצר לפי מזהה
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            dict: נתוני המוצר
        """
        status_code, response = await self._make_request("GET", f"products/{product_id}")
        
        if status_code == 200 and isinstance(response, dict):
            return response
        else:
            logger.error(f"Failed to get product {product_id}: {status_code} - {response}")
            return None
    
    async def update_product(self, product_id: int, data: dict) -> Optional[dict]:
        """
        עדכון מוצר
        
        Args:
            product_id: מזהה המוצר
            data: נתונים לעדכון
            
        Returns:
            dict: נתוני המוצר המעודכן
        """
        status_code, response = await self._make_request("PUT", f"products/{product_id}", data=data)
        
        if status_code in (200, 201) and isinstance(response, dict):
            return response
        else:
            logger.error(f"Failed to update product {product_id}: {status_code} - {response}")
            return None
    
    async def get_orders(self, params: dict = None) -> List[dict]:
        """
        קבלת רשימת הזמנות
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            list: רשימת הזמנות
        """
        default_params = {
            "per_page": 20,
            "page": 1
        }
        
        if params:
            default_params.update(params)
        
        status_code, response = await self._make_request("GET", "orders", params=default_params)
        
        if status_code == 200 and isinstance(response, list):
            return response
        else:
            logger.error(f"Failed to get orders: {status_code} - {response}")
            return []
    
    async def get_order(self, order_id: int) -> Optional[dict]:
        """
        קבלת הזמנה לפי מזהה
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            dict: נתוני ההזמנה
        """
        status_code, response = await self._make_request("GET", f"orders/{order_id}")
        
        if status_code == 200 and isinstance(response, dict):
            return response
        else:
            logger.error(f"Failed to get order {order_id}: {status_code} - {response}")
            return None
    
    async def update_order(self, order_id: int, data: dict) -> Optional[dict]:
        """
        עדכון הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            data: נתונים לעדכון
            
        Returns:
            dict: נתוני ההזמנה המעודכנת
        """
        status_code, response = await self._make_request("PUT", f"orders/{order_id}", data=data)
        
        if status_code in (200, 201) and isinstance(response, dict):
            return response
        else:
            logger.error(f"Failed to update order {order_id}: {status_code} - {response}")
            return None
    
    async def get_customers(self, params: dict = None) -> List[dict]:
        """
        קבלת רשימת לקוחות
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            list: רשימת לקוחות
        """
        default_params = {
            "per_page": 20,
            "page": 1
        }
        
        if params:
            default_params.update(params)
        
        status_code, response = await self._make_request("GET", "customers", params=default_params)
        
        if status_code == 200 and isinstance(response, list):
            return response
        else:
            logger.error(f"Failed to get customers: {status_code} - {response}")
            return []
    
    async def get_store_info(self) -> dict:
        """
        קבלת מידע על החנות
        
        Returns:
            dict: מידע על החנות
        """
        # קבלת הגדרות החנות
        status_code, settings = await self._make_request("GET", "settings/general")
        
        if status_code != 200:
            logger.error(f"Failed to get store settings: {status_code} - {settings}")
            return {"name": "Unknown Store", "error": "Failed to get store info"}
        
        # קבלת סטטיסטיקות מכירות
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # קבלת הזמנות מהיום
        status_code, today_orders = await self._make_request("GET", "orders", params={
            "after": f"{today}T00:00:00",
            "per_page": 100
        })
        
        # קבלת הזמנות מאתמול
        status_code, yesterday_orders = await self._make_request("GET", "orders", params={
            "after": f"{yesterday}T00:00:00",
            "before": f"{today}T00:00:00",
            "per_page": 100
        })
        
        # חישוב סטטיסטיקות
        today_orders_count = len(today_orders) if isinstance(today_orders, list) else 0
        yesterday_orders_count = len(yesterday_orders) if isinstance(yesterday_orders, list) else 0
        
        today_sales = sum(float(order.get("total", 0)) for order in today_orders) if isinstance(today_orders, list) else 0
        yesterday_sales = sum(float(order.get("total", 0)) for order in yesterday_orders) if isinstance(yesterday_orders, list) else 0
        
        # קבלת מוצרים במלאי נמוך
        status_code, low_stock = await self._make_request("GET", "products", params={
            "stock_status": "instock",
            "per_page": 100
        })
        
        low_stock_count = 0
        if isinstance(low_stock, list):
            for product in low_stock:
                stock_quantity = product.get("stock_quantity")
                if stock_quantity is not None and stock_quantity <= 5:
                    low_stock_count += 1
        
        # קבלת הזמנות ממתינות
        status_code, pending_orders = await self._make_request("GET", "orders", params={
            "status": "pending",
            "per_page": 100
        })
        
        pending_orders_count = len(pending_orders) if isinstance(pending_orders, list) else 0
        
        # בניית מידע על החנות
        store_name = None
        for setting in settings:
            if setting.get("id") == "woocommerce_store_name":
                store_name = setting.get("value")
                break
        
        return {
            "name": store_name or "WooCommerce Store",
            "orders_today": today_orders_count,
            "sales_today": today_sales,
            "orders_yesterday": yesterday_orders_count,
            "sales_yesterday": yesterday_sales,
            "low_stock": low_stock_count,
            "pending_orders": pending_orders_count
        }

class CachedWooCommerceAPI:
    """
    מחלקה לתקשורת עם ה-API של ווקומרס עם מטמון
    """
    
    def __init__(self, api: WooCommerceAPI, cache_ttl: int = 300):
        """
        אתחול המחלקה
        
        Args:
            api: אובייקט API של WooCommerce
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        self.api = api
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.cache_timestamps = {}
        
        logger.info(f"CachedWooCommerceAPI initialized with TTL: {cache_ttl} seconds")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        בדיקה האם המטמון תקף
        
        Args:
            cache_key: מפתח המטמון
            
        Returns:
            bool: האם המטמון תקף
        """
        if cache_key not in self.cache_timestamps:
            return False
        
        timestamp = self.cache_timestamps[cache_key]
        current_time = time.time()
        
        return current_time - timestamp < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        קבלת ערך מהמטמון
        
        Args:
            cache_key: מפתח המטמון
            
        Returns:
            Any: הערך מהמטמון או None אם המטמון לא תקף
        """
        if not self._is_cache_valid(cache_key):
            return None
        
        return self.cache.get(cache_key)
    
    def _set_in_cache(self, cache_key: str, value: Any) -> None:
        """
        הגדרת ערך במטמון
        
        Args:
            cache_key: מפתח המטמון
            value: הערך לשמירה
        """
        self.cache[cache_key] = value
        self.cache_timestamps[cache_key] = time.time()
    
    def _clear_cache(self) -> None:
        """
        ניקוי המטמון
        """
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.debug("Cache cleared")
    
    async def get(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        ביצוע בקשת GET עם מטמון
        
        Args:
            endpoint: נקודת קצה ב-API
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # בניית מפתח מטמון
        cache_key = f"GET:{endpoint}:{json.dumps(params or {})}"
        
        # בדיקה אם יש תוצאה במטמון
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for: {cache_key}")
            return 200, cached_result
        
        # ביצוע הבקשה
        status_code, result = await self.api._make_request("GET", endpoint, params=params)
        
        # שמירה במטמון אם הבקשה הצליחה
        if status_code == 200:
            self._set_in_cache(cache_key, result)
        
        return status_code, result
    
    async def post(self, endpoint: str, data: dict = None, params: dict = None) -> Tuple[int, Any]:
        """
        ביצוע בקשת POST
        
        Args:
            endpoint: נקודת קצה ב-API
            data: נתונים לשליחה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # ניקוי המטמון בעת שינוי נתונים
        self._clear_cache()
        
        return await self.api._make_request("POST", endpoint, params=params, data=data)
    
    async def put(self, endpoint: str, data: dict = None, params: dict = None) -> Tuple[int, Any]:
        """
        ביצוע בקשת PUT
        
        Args:
            endpoint: נקודת קצה ב-API
            data: נתונים לשליחה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # ניקוי המטמון בעת שינוי נתונים
        self._clear_cache()
        
        return await self.api._make_request("PUT", endpoint, params=params, data=data)
    
    async def delete(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        ביצוע בקשת DELETE
        
        Args:
            endpoint: נקודת קצה ב-API
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # ניקוי המטמון בעת שינוי נתונים
        self._clear_cache()
        
        return await self.api._make_request("DELETE", endpoint, params=params) 