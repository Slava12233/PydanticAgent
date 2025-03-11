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
import random
from urllib.parse import urlencode

from src.woocommerce.api.api import WooCommerceAPI, CachedWooCommerceAPI
from src.services.ai.learning_service import get_product_improvement_suggestions

# ייבוא פונקציות מזיהוי כוונות מוצרים
from src.products.intent import extract_product_data, identify_missing_required_fields
from src.tools.store.managers.base_manager import BaseManager
from src.woocommerce.data.product_categories import ProductCategories
from src.woocommerce.utils.product_formatter import (
    format_product_for_display,
    format_products_list_for_display,
    create_product_from_text,
    prepare_product_data_for_api,
    get_products_from_text
)

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
            נתוני המוצר עם קטגוריות מעודכנות
        """
        # אם אין קטגוריות, נחזיר את הנתונים כמו שהם
        if "categories" not in api_product_data:
            return api_product_data
        
        # קבלת הקטגוריות מהנתונים
        categories = api_product_data["categories"]
        
        # אם אין קטגוריות, נחזיר את הנתונים כמו שהם
        if not categories:
            return api_product_data
        
        # יצירת רשימת קטגוריות חדשה
        new_categories = []
        
        # עבור כל קטגוריה
        for category in categories:
            # אם יש מזהה, נשתמש בו
            if "id" in category and category["id"]:
                new_categories.append({"id": category["id"]})
            # אחרת, ננסה למצוא או ליצור את הקטגוריה
            elif "name" in category and category["name"]:
                category_id = await self.categories.find_or_create_category(category["name"])
                if category_id:
                    new_categories.append({"id": category_id})
        
        # עדכון הקטגוריות בנתוני המוצר
        api_product_data["categories"] = new_categories
        
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
        api_product_data = prepare_product_data_for_api(product_data)
        
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
        api_product_data = prepare_product_data_for_api(product_data)
        
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
            נתוני המוצר או None אם לא נמצא
        """
        try:
            success, message, product = await self.get(product_id)
            
            if not success:
                logger.error(f"שגיאה בקבלת מוצר {product_id}: {message}")
                return None
            
            return product
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצר {product_id}: {str(e)}")
            return None

    async def search_products(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        חיפוש מוצרים לפי מילת חיפוש
        
        Args:
            search_term: מילת החיפוש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת מוצרים שתואמים את החיפוש
        """
        try:
            # הכנת פרמטרים לחיפוש
            params = {
                "search": search_term,
                "per_page": min(limit, 100)  # מגבלה של WooCommerce API
            }
            
            # ביצוע החיפוש
            success, message, products = await self.list(params)
            
            if not success:
                logger.error(f"שגיאה בחיפוש מוצרים: {message}")
                return []
            
            return products
            
        except Exception as e:
            logger.error(f"שגיאה בחיפוש מוצרים: {str(e)}")
            return []

    def _is_categories_cache_valid(self):
        """
        בדיקה אם המטמון של הקטגוריות תקף
        
        Returns:
            True אם המטמון תקף, False אחרת
        """
        if self.categories_cache is None or self.categories_cache_timestamp is None:
            return False
        
        # בדיקה אם עברו יותר מ-5 דקות מאז העדכון האחרון
        current_time = time.time()
        return (current_time - self.categories_cache_timestamp) < self.cache_ttl

    async def _find_or_create_category(self, category_name: str) -> Optional[int]:
        """
        מציאה או יצירה של קטגוריה
        
        Args:
            category_name: שם הקטגוריה
            
        Returns:
            מזהה הקטגוריה או None אם לא נמצאה/נוצרה
        """
        # בדיקה אם יש מטמון תקף
        if self._is_categories_cache_valid():
            # חיפוש בקטגוריות הקיימות
            for category in self.categories_cache:
                if category["name"].lower() == category_name.lower():
                    return category["id"]
        else:
            # טעינת הקטגוריות מחדש
            self.categories_cache = await self.get_categories()
            self.categories_cache_timestamp = time.time()
            
            # חיפוש בקטגוריות הקיימות
            for category in self.categories_cache:
                if category["name"].lower() == category_name.lower():
                    return category["id"]
        
        # אם לא נמצאה קטגוריה, ננסה ליצור אותה
        try:
            # הכנת נתוני הקטגוריה
            category_data = {
                "name": category_name
            }
            
            # יצירת הקטגוריה
            success, message, response = await self.categories.create(category_data)
            
            if success and response and "id" in response:
                # עדכון המטמון
                if self.categories_cache is not None:
                    self.categories_cache.append(response)
                
                return response["id"]
            else:
                logger.error(f"שגיאה ביצירת קטגוריה '{category_name}': {message}")
                return None
                
        except Exception as e:
            logger.error(f"שגיאה ביצירת קטגוריה '{category_name}': {str(e)}")
            return None

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        קבלת כל הקטגוריות
        
        Returns:
            רשימת כל הקטגוריות
        """
        try:
            # קבלת כל הקטגוריות
            success, message, categories = await self.categories.list({"per_page": 100})
            
            if not success:
                logger.error(f"שגיאה בקבלת קטגוריות: {message}")
                return []
            
            return categories
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת קטגוריות: {str(e)}")
            return []

    async def get_products(self, per_page: int = 20, page: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים
        
        Args:
            per_page: מספר מוצרים בכל עמוד
            page: מספר העמוד
            **kwargs: פרמטרים נוספים לסינון
            
        Returns:
            רשימת מוצרים
        """
        try:
            # הכנת פרמטרים
            params = {
                "per_page": per_page,
                "page": page,
                **kwargs
            }
            
            # קבלת המוצרים
            success, message, products = await self.list(params)
            
            if not success:
                logger.error(f"שגיאה בקבלת מוצרים: {message}")
                return []
            
            return products
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים: {str(e)}")
            return []

    async def delete_product(self, product_id: int, force: bool = False) -> bool:
        """
        מחיקת מוצר
        
        Args:
            product_id: מזהה המוצר
            force: האם למחוק לצמיתות (ברירת מחדל: False)
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            # הכנת פרמטרים
            params = {"force": force}
            
            # מחיקת המוצר
            success, message, _ = await self.delete(product_id, params)
            
            if not success:
                logger.error(f"שגיאה במחיקת מוצר {product_id}: {message}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"שגיאה במחיקת מוצר {product_id}: {str(e)}")
            return False

    async def upload_product_image(self, product_id: int, image_url: str) -> Optional[Dict[str, Any]]:
        """
        העלאת תמונת מוצר
        
        Args:
            product_id: מזהה המוצר
            image_url: כתובת התמונה
            
        Returns:
            פרטי התמונה שהועלתה או None אם ההעלאה נכשלה
        """
        try:
            # קבלת המוצר הנוכחי
            product = await self.get_product(product_id)
            if not product:
                logger.error(f"לא נמצא מוצר עם מזהה {product_id}")
                return None
            
            # הכנת נתוני התמונה
            image_data = {
                "src": image_url
            }
            
            # אם יש כבר תמונות למוצר, נוסיף את התמונה החדשה
            if "images" in product and product["images"]:
                images = product["images"]
                images.append(image_data)
                update_data = {"images": images}
            else:
                # אם אין תמונות, ניצור רשימה חדשה
                update_data = {"images": [image_data]}
            
            # עדכון המוצר
            updated_product = await self.update_product(product_id, update_data)
            if not updated_product:
                logger.error(f"שגיאה בעדכון תמונת מוצר {product_id}")
                return None
            
            # החזרת התמונה האחרונה שהועלתה
            if "images" in updated_product and updated_product["images"]:
                return updated_product["images"][-1]
            
            return None
            
        except Exception as e:
            logger.error(f"שגיאה בהעלאת תמונת מוצר {product_id}: {str(e)}")
            return None 