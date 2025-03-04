"""
מודול לניהול קטגוריות מוצרים ב-WooCommerce.
מאפשר חיפוש, יצירה ועדכון של קטגוריות מוצרים.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from src.tools.store_tools.managers.base_manager import BaseManager

logger = logging.getLogger(__name__)

class ProductCategories(BaseManager):
    """מחלקה לניהול קטגוריות מוצרים."""

    def __init__(self, woocommerce_api=None, use_cache: bool = True):
        """
        אתחול מנהל הקטגוריות.
        
        Args:
            woocommerce_api: אובייקט ה-API של WooCommerce (אופציונלי)
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
        """
        super().__init__(woocommerce_api, use_cache)
        self.categories_cache = None
        self.categories_cache_timestamp = None
        self.cache_ttl = 300  # 5 דקות

    def _get_resource_name(self) -> str:
        """מחזיר את שם המשאב"""
        return "products/categories"

    def _is_categories_cache_valid(self) -> bool:
        """
        בדיקה האם מטמון הקטגוריות תקף.
        
        Returns:
            True אם המטמון תקף, False אחרת
        """
        if self.categories_cache is None or self.categories_cache_timestamp is None:
            return False
        
        current_time = time.time()
        return current_time - self.categories_cache_timestamp < self.cache_ttl

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        קבלת כל הקטגוריות מהחנות.
        
        Returns:
            רשימת קטגוריות
        """
        # בדיקה אם יש מטמון תקף
        if self._is_categories_cache_valid():
            return self.categories_cache
        
        try:
            # קבלת כל הקטגוריות
            success, message, categories = await self.list(params={"per_page": 100})
            
            if not success:
                raise Exception(f"שגיאה בקבלת קטגוריות: {message}")
            
            # שמירה במטמון
            self.categories_cache = categories
            self.categories_cache_timestamp = time.time()
            
            return categories
        except Exception as e:
            logger.error(f"שגיאה בקבלת קטגוריות: {str(e)}")
            return []

    async def find_or_create_category(self, category_name: str) -> Optional[int]:
        """
        חיפוש קטגוריה קיימת או יצירת קטגוריה חדשה.
        
        Args:
            category_name: שם הקטגוריה
            
        Returns:
            מזהה הקטגוריה או None אם לא נמצאה/נוצרה
        """
        try:
            # חיפוש הקטגוריה לפי שם
            success, message, existing_categories = await self.list(params={"search": category_name})
            
            if success and existing_categories:
                # חיפוש התאמה מדויקת
                exact_match = next((cat for cat in existing_categories if cat.get("name").lower() == category_name.lower()), None)
                
                if exact_match:
                    # אם נמצאה התאמה מדויקת, נחזיר את ה-ID שלה
                    logger.info(f"נמצאה קטגוריה קיימת: {category_name} (ID: {exact_match['id']})")
                    return exact_match["id"]
            
            # אם לא נמצאה התאמה, ננסה ליצור קטגוריה חדשה
            success, message, new_category = await self.create({"name": category_name})
            
            if success and new_category:
                logger.info(f"נוצרה קטגוריה חדשה: {category_name} (ID: {new_category['id']})")
                return new_category["id"]
            else:
                logger.warning(f"לא ניתן ליצור קטגוריה חדשה: {category_name}")
                return None
        except Exception as e:
            logger.error(f"שגיאה בחיפוש/יצירת קטגוריה: {str(e)}")
            return None

    async def handle_product_categories(self, api_product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        טיפול בקטגוריות של מוצר.
        
        Args:
            api_product_data: נתוני המוצר
            
        Returns:
            נתוני המוצר מעודכנים
        """
        if "categories" in api_product_data:
            categories = api_product_data["categories"]
            api_categories = []
            
            # בדיקה אם יש קטגוריות קיימות
            if isinstance(categories, list):
                # אם יש רשימת קטגוריות, נשתמש בהן
                for category in categories:
                    if isinstance(category, dict) and "name" in category:
                        category_id = await self.find_or_create_category(category["name"])
                        if category_id:
                            api_categories.append({"id": category_id})
                        else:
                            api_categories.append({"name": category["name"]})
                    elif isinstance(category, str):
                        category_id = await self.find_or_create_category(category)
                        if category_id:
                            api_categories.append({"id": category_id})
                        else:
                            api_categories.append({"name": category})
            elif isinstance(categories, str):
                # אם זו מחרוזת, נפצל אותה לרשימה
                category_names = [cat.strip() for cat in categories.split(",") if cat.strip()]
                for category_name in category_names:
                    category_id = await self.find_or_create_category(category_name)
                    if category_id:
                        api_categories.append({"id": category_id})
                    else:
                        api_categories.append({"name": category_name})
            
            # שמירת הקטגוריות המוכנות
            if api_categories:
                api_product_data["categories"] = api_categories
        
        return api_product_data 