"""
מודול לתקשורת עם ה-API של ווקומרס עם מטמון
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from src.woocommerce.api.api import WooCommerceAPI

logger = logging.getLogger(__name__)

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