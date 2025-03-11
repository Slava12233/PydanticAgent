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
from woocommerce import API
import backoff

logger = logging.getLogger(__name__)

# קבועים
DEFAULT_TIMEOUT = 180  # שניות - הגדלנו את זמן התגובה המקסימלי
DEFAULT_CACHE_TTL = 300  # 5 דקות בשניות
MAX_RETRIES = 3  # מספר ניסיונות מקסימלי

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
    wc_application_password = os.getenv('WOOCOMMERCE_APPLICATION_PASSWORD', '')
    wc_username = os.getenv('WOOCOMMERCE_USERNAME', '')
    
    return WooCommerceAPI(
        url=wc_url,
        consumer_key=wc_consumer_key,
        consumer_secret=wc_consumer_secret,
        application_password=wc_application_password,
        username=wc_username
    )

@lru_cache(maxsize=1)
def get_cached_woocommerce_api() -> 'CachedWooCommerceAPI':
    """
    מחזיר מופע של CachedWooCommerceAPI.
    משתמש ב-lru_cache כדי לשמור מופע יחיד.
    
    Returns:
        CachedWooCommerceAPI: מופע של CachedWooCommerceAPI
    """
    return CachedWooCommerceAPI(api=get_woocommerce_api())

class WooCommerceAPI:
    """
    מחלקה לתקשורת עם ה-API של ווקומרס
    """
    
    def __init__(
        self, 
        url: str, 
        consumer_key: str, 
        consumer_secret: str,
        application_password: str = None,
        username: str = None,
        version: str = "wc/v3"
    ):
        """
        אתחול המחלקה
        
        Args:
            url: כתובת האתר
            consumer_key: מפתח צרכן
            consumer_secret: סוד צרכן
            application_password: סיסמת אפליקציה (אופציונלי)
            username: שם משתמש (אופציונלי)
            version: גרסת ה-API
        """
        self.url = url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.application_password = application_password
        self.username = username
        self.version = version
        self.api_url = f"{self.url}/wp-json/{version}"
        
        # יצירת מופע של ספריית WooCommerce
        self.wcapi = API(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            version=self.version,
            timeout=DEFAULT_TIMEOUT
        )
        
        # הגדרת כותרות HTTP
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # אם יש סיסמת אפליקציה ושם משתמש, נוסיף אותם לכותרות
        if self.application_password and self.username:
            auth_string = f"{self.username}:{self.application_password}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            self.headers["Authorization"] = f"Basic {auth_header}"
    
    def _execute_with_retry(self, operation_name, operation_func, *args, **kwargs):
        """
        מבצע פעולה עם ניסיונות חוזרים במקרה של כישלון
        
        Args:
            operation_name: שם הפעולה (לצורכי לוג)
            operation_func: פונקציית הפעולה לביצוע
            *args, **kwargs: פרמטרים לפונקציה
            
        Returns:
            תוצאת הפעולה
        """
        retries = 0
        last_error = None
        
        while retries < MAX_RETRIES:
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                retries += 1
                last_error = e
                wait_time = 2 ** retries  # exponential backoff
                
                logger.warning(
                    f"שגיאה בפעולת {operation_name} (ניסיון {retries}/{MAX_RETRIES}): {str(e)}. "
                    f"ממתין {wait_time} שניות לפני ניסיון חוזר."
                )
                
                time.sleep(wait_time)
        
        # אם הגענו לכאן, כל הניסיונות נכשלו
        logger.error(f"כל הניסיונות לבצע {operation_name} נכשלו. שגיאה אחרונה: {str(last_error)}")
        raise last_error
    
    async def get(self, endpoint: str, params: dict = None) -> Tuple[int, dict]:
        """
        שליחת בקשת GET ל-API
        
        Args:
            endpoint: נקודת הקצה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{self.api_url}/{endpoint}",
                params=params or {},
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def get_products(self, params: dict = None) -> Tuple[int, dict]:
        """
        קבלת רשימת מוצרים
        
        Args:
            params: פרמטרים לסינון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get("products", params)
    
    async def get_product(self, product_id: int) -> Tuple[int, dict]:
        """
        קבלת מוצר לפי מזהה
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get(f"products/{product_id}")
    
    async def create_product(self, product_data: dict) -> Tuple[int, dict]:
        """
        יצירת מוצר חדש
        
        Args:
            product_data: נתוני המוצר
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.api_url}/products",
                json=product_data,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def update_product_image(self, product_id: int, image_url: str) -> Tuple[int, dict]:
        """
        עדכון תמונת מוצר
        
        Args:
            product_id: מזהה המוצר
            image_url: כתובת התמונה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        image_data = {
            "images": [
                {
                    "src": image_url,
                    "position": 0
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.put(
                f"{self.api_url}/products/{product_id}",
                json=image_data,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def update_product(self, product_id: int, data: dict) -> Tuple[int, dict]:
        """
        עדכון מוצר
        
        Args:
            product_id: מזהה המוצר
            data: נתוני העדכון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.put(
                f"{self.api_url}/products/{product_id}",
                json=data,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def delete_product(self, product_id: int, force: bool = False) -> Tuple[int, dict]:
        """
        מחיקת מוצר
        
        Args:
            product_id: מזהה המוצר
            force: האם למחוק לצמיתות
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        params = {"force": "true"} if force else {}
        
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.delete(
                f"{self.api_url}/products/{product_id}",
                params=params,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def get_categories(self, params: dict = None) -> Tuple[int, dict]:
        """
        קבלת רשימת קטגוריות
        
        Args:
            params: פרמטרים לסינון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get("products/categories", params)
    
    async def create_category(self, data: dict) -> Tuple[int, dict]:
        """
        יצירת קטגוריה חדשה
        
        Args:
            data: נתוני הקטגוריה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{self.api_url}/products/categories",
                json=data,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def get_orders(self, params: dict = None) -> Tuple[int, dict]:
        """
        קבלת רשימת הזמנות
        
        Args:
            params: פרמטרים לסינון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get("orders", params)
    
    async def get_order(self, order_id: int) -> Tuple[int, dict]:
        """
        קבלת הזמנה לפי מזהה
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get(f"orders/{order_id}")
    
    async def update_order(self, order_id: int, data: dict) -> Tuple[int, dict]:
        """
        עדכון הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            data: נתוני העדכון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.put(
                f"{self.api_url}/orders/{order_id}",
                json=data,
                headers=self.headers,
                auth=(self.consumer_key, self.consumer_secret)
            )
            return response.status_code, response.json()
    
    async def get_customers(self, params: dict = None) -> Tuple[int, dict]:
        """
        קבלת רשימת לקוחות
        
        Args:
            params: פרמטרים לסינון
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        return await self.get("customers", params)
    
    async def get_store_info(self) -> dict:
        """
        קבלת מידע על החנות
        
        Returns:
            dict: מידע על החנות
        """
        try:
            # ניסיון לקבל מידע בסיסי על החנות
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(
                    f"{self.url}/wp-json",
                    headers=self.headers,
                    auth=(self.consumer_key, self.consumer_secret)
                )
                
                if response.status_code != 200:
                    logger.error(f"שגיאה בקבלת מידע על החנות: {response.status_code}")
                    return {"error": f"שגיאה בקבלת מידע על החנות: {response.status_code}"}
                
                basic_info = response.json()
                
                # ניסיון לקבל מידע נוסף על החנות מ-WooCommerce
                settings_response = await client.get(
                    f"{self.api_url}/settings/general",
                    headers=self.headers,
                    auth=(self.consumer_key, self.consumer_secret)
                )
                
                if settings_response.status_code != 200:
                    logger.warning(f"שגיאה בקבלת הגדרות החנות: {settings_response.status_code}")
                    settings = {}
                else:
                    settings = {item['id']: item['value'] for item in settings_response.json()}
                
                # שילוב המידע
                store_info = {
                    "name": basic_info.get('name', ''),
                    "description": basic_info.get('description', ''),
                    "url": basic_info.get('url', self.url),
                    "settings": settings
                }
                
                return store_info
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת מידע על החנות: {str(e)}")
            return {"error": str(e)}


class CachedWooCommerceAPI:
    """
    מחלקה לתקשורת עם ה-API של ווקומרס עם מטמון
    """
    
    def __init__(self, api: WooCommerceAPI, cache_ttl: int = 300):
        """
        אתחול המחלקה
        
        Args:
            api: מופע של WooCommerceAPI
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        self.api = api
        self.cache_ttl = cache_ttl
        self.cache = {}  # מטמון פשוט מבוסס מילון
        self.cache_timestamps = {}  # זמני יצירה של פריטי המטמון
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        בדיקה אם פריט במטמון עדיין תקף
        
        Args:
            cache_key: מפתח המטמון
            
        Returns:
            bool: האם הפריט תקף
        """
        if cache_key not in self.cache or cache_key not in self.cache_timestamps:
            return False
        
        timestamp = self.cache_timestamps[cache_key]
        now = datetime.now()
        age = (now - timestamp).total_seconds()
        
        return age < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        קבלת פריט מהמטמון
        
        Args:
            cache_key: מפתח המטמון
            
        Returns:
            Any: הפריט מהמטמון, או None אם לא נמצא או פג תוקף
        """
        if self._is_cache_valid(cache_key):
            logger.debug(f"נמצא במטמון: {cache_key}")
            return self.cache[cache_key]
        
        # מחיקת פריטים שפג תוקפם
        if cache_key in self.cache:
            del self.cache[cache_key]
            del self.cache_timestamps[cache_key]
        
        return None
    
    def _set_in_cache(self, cache_key: str, value: Any) -> None:
        """
        שמירת פריט במטמון
        
        Args:
            cache_key: מפתח המטמון
            value: הערך לשמירה
        """
        self.cache[cache_key] = value
        self.cache_timestamps[cache_key] = datetime.now()
        logger.debug(f"נשמר במטמון: {cache_key}")
    
    def _clear_cache(self) -> None:
        """
        ניקוי המטמון
        """
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.debug("המטמון נוקה")
    
    async def get(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        שליחת בקשת GET ל-API עם מטמון
        
        Args:
            endpoint: נקודת הקצה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # יצירת מפתח מטמון
        params_str = json.dumps(params or {}, sort_keys=True)
        cache_key = f"GET:{endpoint}:{params_str}"
        
        # ניסיון לקבל מהמטמון
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # אם לא נמצא במטמון, שליחת בקשה
        status_code, data = await self.api.get(endpoint, params)
        
        # שמירה במטמון רק אם הבקשה הצליחה
        if 200 <= status_code < 300:
            self._set_in_cache(cache_key, (status_code, data))
        
        return status_code, data
    
    async def post(self, endpoint: str, data: dict = None, params: dict = None) -> Tuple[int, Any]:
        """
        שליחת בקשת POST ל-API (ללא מטמון)
        
        Args:
            endpoint: נקודת הקצה
            data: נתוני הבקשה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # בקשות POST משנות נתונים, לכן ניקוי המטמון
        self._clear_cache()
        
        # העברה לשיטה המקורית
        return await self.api.post(endpoint, data, params)
    
    async def put(self, endpoint: str, data: dict = None, params: dict = None) -> Tuple[int, Any]:
        """
        שליחת בקשת PUT ל-API (ללא מטמון)
        
        Args:
            endpoint: נקודת הקצה
            data: נתוני הבקשה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # בקשות PUT משנות נתונים, לכן ניקוי המטמון
        self._clear_cache()
        
        # העברה לשיטה המקורית
        return await self.api.put(endpoint, data, params)
    
    async def delete(self, endpoint: str, params: dict = None) -> Tuple[int, Any]:
        """
        שליחת בקשת DELETE ל-API (ללא מטמון)
        
        Args:
            endpoint: נקודת הקצה
            params: פרמטרים לבקשה
            
        Returns:
            tuple: (קוד תשובה, נתוני תשובה)
        """
        # בקשות DELETE משנות נתונים, לכן ניקוי המטמון
        self._clear_cache()
        
        # העברה לשיטה המקורית
        return await self.api.delete(endpoint, params) 