"""
מודול לניהול מלאי ב-WooCommerce
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from ..woocommerce.api.api import WooCommerceAPI, CachedWooCommerceAPI
from ..core.base_manager import BaseManager
from .forecasting import InventoryForecasting
from .reporting import InventoryReporting

logger = logging.getLogger(__name__)

class InventoryManager(BaseManager):
    """מנהל מלאי המאפשר ביצוע פעולות על מלאי מוצרים בחנות WooCommerce."""

    def __init__(self, api=None, use_cache: bool = True):
        """
        אתחול מנהל המלאי.
        
        Args:
            api: אובייקט ה-API של WooCommerce (אופציונלי)
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
        """
        super().__init__(api, use_cache)
        self.forecasting = InventoryForecasting(api, use_cache)
        self.reporting = InventoryReporting(api, use_cache)

    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב
        """
        return "products"

    async def get_product_stock(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת מידע על מלאי של מוצר ספציפי.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            מידע על המלאי או None אם המוצר לא נמצא
        """
        try:
            success, message, product = await self.get(product_id)
            if not success:
                logger.warning(f"מוצר עם מזהה {product_id} לא נמצא: {message}")
                return None
            
            # חילוץ מידע על המלאי
            stock_info = {
                "product_id": product_id,
                "product_name": product.get("name", ""),
                "sku": product.get("sku", ""),
                "manage_stock": product.get("manage_stock", False),
                "in_stock": product.get("in_stock", False),
                "stock_quantity": product.get("stock_quantity", 0),
                "stock_status": product.get("stock_status", ""),
                "backorders_allowed": product.get("backorders_allowed", False),
                "backorders": product.get("backorders", "no"),
                "low_stock_amount": product.get("low_stock_amount", None)
            }
            
            return stock_info
        except Exception as e:
            logger.error(f"שגיאה בקבלת מידע על מלאי מוצר {product_id}: {e}")
            return None

    async def update_product_stock(self, product_id: int, stock_quantity: int, manage_stock: bool = True, 
                                  in_stock: bool = True, low_stock_amount: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        עדכון מלאי של מוצר.
        
        Args:
            product_id: מזהה המוצר
            stock_quantity: כמות המלאי החדשה
            manage_stock: האם לנהל מלאי (ברירת מחדל: True)
            in_stock: האם המוצר במלאי (ברירת מחדל: True)
            low_stock_amount: כמות מלאי נמוכה להתראה (אופציונלי)
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        try:
            # הכנת נתוני העדכון
            update_data = {
                "manage_stock": manage_stock,
                "stock_quantity": stock_quantity,
                "in_stock": in_stock
            }
            
            # הוספת כמות מלאי נמוכה אם סופקה
            if low_stock_amount is not None:
                update_data["low_stock_amount"] = low_stock_amount
            
            # עדכון המוצר
            success, message, updated_product = await self.update(product_id, update_data)
            
            if not success:
                logger.warning(f"עדכון מלאי למוצר {product_id} נכשל: {message}")
                return None
            
            logger.info(f"מלאי מוצר {product_id} עודכן בהצלחה. כמות חדשה: {stock_quantity}")
            return updated_product
        except Exception as e:
            logger.error(f"שגיאה בעדכון מלאי מוצר {product_id}: {e}")
            return None

    async def add_to_stock(self, product_id: int, quantity_to_add: int) -> Optional[Dict[str, Any]]:
        """
        הוספת כמות למלאי קיים.
        
        Args:
            product_id: מזהה המוצר
            quantity_to_add: הכמות להוספה
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        try:
            # קבלת מידע נוכחי על המלאי
            current_stock = await self.get_product_stock(product_id)
            if not current_stock:
                logger.warning(f"לא ניתן להוסיף למלאי: מוצר {product_id} לא נמצא")
                return None
            
            # חישוב הכמות החדשה
            current_quantity = current_stock.get("stock_quantity", 0) or 0
            new_quantity = current_quantity + quantity_to_add
            
            # עדכון המלאי
            return await self.update_product_stock(
                product_id=product_id,
                stock_quantity=new_quantity,
                manage_stock=True,
                in_stock=new_quantity > 0
            )
        except Exception as e:
            logger.error(f"שגיאה בהוספת כמות למלאי מוצר {product_id}: {e}")
            return None

    async def remove_from_stock(self, product_id: int, quantity_to_remove: int) -> Optional[Dict[str, Any]]:
        """
        הורדת כמות מהמלאי הקיים.
        
        Args:
            product_id: מזהה המוצר
            quantity_to_remove: הכמות להורדה
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        try:
            # קבלת מידע נוכחי על המלאי
            current_stock = await self.get_product_stock(product_id)
            if not current_stock:
                logger.warning(f"לא ניתן להוריד מהמלאי: מוצר {product_id} לא נמצא")
                return None
            
            # חישוב הכמות החדשה
            current_quantity = current_stock.get("stock_quantity", 0) or 0
            new_quantity = max(0, current_quantity - quantity_to_remove)
            
            # עדכון המלאי
            return await self.update_product_stock(
                product_id=product_id,
                stock_quantity=new_quantity,
                manage_stock=True,
                in_stock=new_quantity > 0
            )
        except Exception as e:
            logger.error(f"שגיאה בהורדת כמות ממלאי מוצר {product_id}: {e}")
            return None

    async def set_backorders_policy(self, product_id: int, backorders: str) -> Optional[Dict[str, Any]]:
        """
        הגדרת מדיניות הזמנות מראש למוצר.
        
        Args:
            product_id: מזהה המוצר
            backorders: מדיניות הזמנות מראש ('no', 'notify', 'yes')
            
        Returns:
            המוצר המעודכן או None אם העדכון נכשל
        """
        try:
            # בדיקת תקינות הערך
            valid_backorders = ['no', 'notify', 'yes']
            if backorders not in valid_backorders:
                logger.error(f"ערך לא תקין להזמנות מראש: {backorders}. ערכים תקינים: {', '.join(valid_backorders)}")
                return None
            
            # עדכון המוצר
            success, message, updated_product = await self.update(product_id, {"backorders": backorders})
            
            if not success:
                logger.warning(f"עדכון מדיניות הזמנות מראש למוצר {product_id} נכשל: {message}")
                return None
            
            logger.info(f"מדיניות הזמנות מראש למוצר {product_id} עודכנה ל-{backorders}")
            return updated_product
        except Exception as e:
            logger.error(f"שגיאה בעדכון מדיניות הזמנות מראש למוצר {product_id}: {e}")
            return None

    # פונקציות מועברות למחלקות חדשות
    async def forecast_inventory(self, product_id: int, days: int = 30, forecast_periods: List[int] = None) -> Dict[str, Any]:
        """
        חיזוי מלאי למוצר.
        
        Args:
            product_id: מזהה המוצר
            days: מספר ימים לחיזוי (ברירת מחדל: 30)
            forecast_periods: רשימת תקופות לחיזוי בימים (ברירת מחדל: [7, 14, 30, 60, 90])
            
        Returns:
            תחזית המלאי
        """
        return await self.forecasting.forecast_inventory(product_id, days, forecast_periods)

    async def get_low_stock_products(self, threshold: Optional[int] = None, include_alerts: bool = True,
                                  high_threshold_percentage: float = 0.25, medium_threshold_percentage: float = 0.5,
                                  per_page: int = 100, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים עם מלאי נמוך.
        
        Args:
            threshold: סף כמות להגדרת מלאי נמוך (אופציונלי)
            include_alerts: האם לכלול התראות מלאי (ברירת מחדל: True)
            high_threshold_percentage: אחוז מהסף להגדרת רמת חומרה גבוהה (ברירת מחדל: 0.25)
            medium_threshold_percentage: אחוז מהסף להגדרת רמת חומרה בינונית (ברירת מחדל: 0.5)
            per_page: מספר מוצרים לעמוד (ברירת מחדל: 100)
            category_id: מזהה קטגוריה לסינון (אופציונלי)
            
        Returns:
            רשימת מוצרים עם מלאי נמוך
        """
        return await self.reporting.get_low_stock_products(threshold, include_alerts, high_threshold_percentage,
                                                        medium_threshold_percentage, per_page, category_id)

    async def get_out_of_stock_products(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים שאזלו מהמלאי.
        
        Returns:
            רשימת מוצרים שאזלו מהמלאי
        """
        return await self.reporting.get_out_of_stock_products()

    async def get_inventory_report(self, per_page: int = 100, category_id: Optional[int] = None) -> Dict[str, Any]:
        """
        הפקת דוח מלאי כללי.
        
        Args:
            per_page: מספר מוצרים לעמוד (ברירת מחדל: 100)
            category_id: מזהה קטגוריה לסינון (אופציונלי)
            
        Returns:
            דוח מלאי
        """
        return await self.reporting.get_inventory_report(per_page, category_id)

