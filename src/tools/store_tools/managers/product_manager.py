"""
מודול לניהול מוצרים ב-WooCommerce
"""
import logging
import os
import json
import re
import tempfile
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import httpx
import imghdr

from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI
from src.tools.intent.product_intent import extract_product_data, identify_missing_required_fields
from src.tools.store_tools.managers.base_manager import BaseManager
from src.tools.store_tools.managers.product_categories import ProductCategories

logger = logging.getLogger(__name__)

class ProductManager(BaseManager):
    """
    מחלקה לניהול מוצרים ב-WooCommerce
    """
    
    def __init__(self, api: Optional[WooCommerceAPI] = None, use_cache: bool = True):
        """
        אתחול מנהל המוצרים
        
        Args:
            api: אובייקט ה-API של WooCommerce (אופציונלי)
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
        """
        super().__init__(api, use_cache)
        self.categories = ProductCategories(api, use_cache)
        self.categories_cache = None
        self.categories_cache_timestamp = None
        self.cache_ttl = 300  # 5 דקות
    
    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב
        """
        return "products"

    async def _handle_categories(self, api_product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בקטגוריות של מוצר
        
        Args:
            api_product_data: נתוני המוצר
            
        Returns:
            נתוני המוצר מעודכנים
        """
        if "categories" in api_product_data:
            categories = api_product_data["categories"]
            api_categories = []
            
            for category in categories:
                if "name" in category:
                    # חיפוש או יצירת קטגוריה
                    category_id = await self._find_or_create_category(category["name"])
                    if category_id:
                        api_categories.append({"id": category_id})
                    else:
                        # אם לא הצלחנו למצוא או ליצור, נשתמש בשם
                        api_categories.append({"name": category["name"]})
            
            # עדכון הקטגוריות בנתוני המוצר
            if api_categories:
                api_product_data["categories"] = api_categories
        
        return api_product_data

    async def create_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        יצירת מוצר חדש
        
        Args:
            product_data: נתוני המוצר
            
        Returns:
            המוצר שנוצר או None אם היצירה נכשלה
        """
        # וידוא שיש את כל השדות הנדרשים
        missing_fields = identify_missing_required_fields(product_data)
        if missing_fields:
            missing_fields_str = ", ".join(missing_fields)
            logger.error(f"לא ניתן ליצור מוצר: חסרים שדות חובה: {missing_fields_str}")
            return None
        
        # הכנת נתוני המוצר לשליחה ל-API
        api_product_data = self._prepare_product_data_for_api(product_data)
        
        # טיפול בקטגוריות
        api_product_data = await self.categories.handle_product_categories(api_product_data)
        
        # שימוש בפונקציית create של מחלקת הבסיס
        success, message, response = await self.create(api_product_data)
        return response if success else None

    async def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        עדכון מוצר קיים
        
        Args:
            product_id: מזהה המוצר
            product_data: נתוני המוצר לעדכון
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        # הכנת נתוני המוצר לשליחה ל-API
        api_product_data = self._prepare_product_data_for_api(product_data)
        
        # טיפול בקטגוריות
        api_product_data = await self.categories.handle_product_categories(api_product_data)
        
        # שימוש בפונקציית update של מחלקת הבסיס
        success, message, response = await self.update(product_id, api_product_data)
        return response if success else None

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת מוצר לפי מזהה
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            נתוני המוצר או None אם המוצר לא נמצא
        """
        # שימוש בפונקציית get של מחלקת הבסיס
        success, message, response = await self.get(product_id)
        return response if success else None

    async def search_products(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        חיפוש מוצרים לפי מונח חיפוש
        
        Args:
            search_term: מונח החיפוש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימה של מוצרים שתואמים את החיפוש
        """
        params = {
            "search": search_term,
            "per_page": limit
        }
        
        # שימוש בפונקציית list של מחלקת הבסיס
        success, message, response = await self.list(params)
        return response if success else []

    def _is_categories_cache_valid(self):
        """
        בדיקה האם מטמון הקטגוריות תקף
        
        Returns:
            True אם המטמון תקף, False אחרת
        """
        if self.categories_cache is None or self.categories_cache_timestamp is None:
            return False
        
        current_time = time.time()
        return current_time - self.categories_cache_timestamp < self.cache_ttl

    async def _find_or_create_category(self, category_name: str) -> Optional[int]:
        """
        חיפוש קטגוריה קיימת או יצירת קטגוריה חדשה
        
        Args:
            category_name: שם הקטגוריה
            
        Returns:
            מזהה הקטגוריה או None אם לא נמצאה/נוצרה
        """
        try:
            # חיפוש הקטגוריה לפי שם
            success, message, existing_categories = await self.list("products/categories", params={"search": category_name})
            
            if success and existing_categories:
                # חיפוש התאמה מדויקת
                exact_match = next((cat for cat in existing_categories if cat.get("name").lower() == category_name.lower()), None)
                
                if exact_match:
                    # אם נמצאה התאמה מדויקת, נחזיר את ה-ID שלה
                    logger.info(f"נמצאה קטגוריה קיימת: {category_name} (ID: {exact_match['id']})")
                    return exact_match["id"]
            
            # אם לא נמצאה התאמה, ננסה ליצור קטגוריה חדשה
            success, message, new_category = await self.create("products/categories", {"name": category_name})
            
            if success and new_category:
                logger.info(f"נוצרה קטגוריה חדשה: {category_name} (ID: {new_category['id']})")
                return new_category["id"]
            else:
                logger.warning(f"לא ניתן ליצור קטגוריה חדשה: {category_name}")
                return None
        except Exception as e:
            logger.error(f"שגיאה בחיפוש/יצירת קטגוריה: {str(e)}")
            return None

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        קבלת כל הקטגוריות מהחנות
        
        Returns:
            רשימת קטגוריות
        """
        # בדיקה אם יש מטמון תקף
        if self._is_categories_cache_valid():
            return self.categories_cache
        
        try:
            # קבלת כל הקטגוריות
            success, message, categories = await self.list("products/categories", params={"per_page": 100})
            
            if not success:
                raise Exception(f"שגיאה בקבלת קטגוריות: {message}")
            
            # שמירה במטמון
            self.categories_cache = categories
            self.categories_cache_timestamp = time.time()
            
            return categories
        except Exception as e:
            logger.error(f"שגיאה בקבלת קטגוריות: {str(e)}")
            return []

    async def get_products(self, per_page: int = 20, page: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """
        קבלת מוצרים מהחנות
        
        Args:
            per_page: מספר מוצרים בכל עמוד
            page: מספר העמוד
            **kwargs: פרמטרים נוספים לסינון
            
        Returns:
            רשימת מוצרים
        """
        try:
            # הכנת פרמטרים לבקשה
            params = {
                "per_page": per_page,
                "page": page,
                **kwargs
            }
            
            # קבלת מוצרים
            success, message, products = await self.list(params)
            
            if not success:
                logger.error(f"שגיאה בקבלת מוצרים: {message}")
                return []
            
            return products
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים: {str(e)}")
            return []

    def _prepare_product_data_for_api(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        הכנת נתוני המוצר לשליחה ל-API
        
        Args:
            product_data: נתוני המוצר המקוריים
            
        Returns:
            נתוני המוצר מוכנים לשליחה ל-API
        """
        api_data = {}
        
        # העתקת שדות בסיסיים
        basic_fields = ["name", "description", "short_description", "sku", "regular_price", 
                        "sale_price", "status", "featured", "catalog_visibility", 
                        "virtual", "downloadable", "tax_status", "tax_class"]
        
        for field in basic_fields:
            if field in product_data:
                api_data[field] = product_data[field]
        
        # טיפול במחיר אם קיים
        if "price" in product_data and "regular_price" not in product_data:
            api_data["regular_price"] = str(product_data["price"])
        
        # המרת מחירים למחרוזות (נדרש ע"י ה-API)
        price_fields = ["regular_price", "sale_price"]
        for field in price_fields:
            if field in api_data:
                api_data[field] = str(api_data[field])
        
        # טיפול בסוג המוצר
        if "type" in product_data:
            api_data["type"] = product_data["type"]
        else:
            # ברירת מחדל: מוצר פשוט
            api_data["type"] = "simple"
        
        # טיפול בניהול מלאי
        if "stock_quantity" in product_data:
            api_data["manage_stock"] = True
            api_data["stock_quantity"] = product_data["stock_quantity"]
            
            # קביעת סטטוס מלאי אוטומטית
            if product_data["stock_quantity"] > 0:
                api_data["stock_status"] = "instock"
            else:
                api_data["stock_status"] = "outofstock"
        elif "stock_status" in product_data:
            api_data["stock_status"] = product_data["stock_status"]
        
        # טיפול בקטגוריות - נשתמש בשמות בלבד ונטפל בהם בצורה נכונה בפונקציית create_product
        if "categories" in product_data:
            categories = product_data["categories"]
            api_categories = []
            
            # בדיקה אם יש קטגוריות קיימות
            if isinstance(categories, list):
                # אם יש רשימת קטגוריות, נשתמש בהן
                for category_name in categories:
                    api_categories.append({"name": category_name})
            elif isinstance(categories, str):
                # אם זו מחרוזת, נפצל אותה לרשימה
                category_names = [cat.strip() for cat in categories.split(",") if cat.strip()]
                for category_name in category_names:
                    api_categories.append({"name": category_name})
            
            # שמירת הקטגוריות המוכנות
            if api_categories:
                api_data["categories"] = api_categories
        
        return api_data
