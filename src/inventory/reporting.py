"""
מודול לדוחות מלאי ב-WooCommerce
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI
from src.tools.store.managers.base_manager import BaseManager

logger = logging.getLogger(__name__)

class InventoryReporting(BaseManager):
    """מחלקה להפקת דוחות מלאי מפורטים."""

    def _get_resource_name(self) -> str:
        """מחזיר את שם המשאב"""
        return "products"

    def _get_alert_emoji(self, alert_level: str) -> str:
        """
        קבלת אימוג'י מתאים לרמת התראה.
        
        Args:
            alert_level: רמת ההתראה
            
        Returns:
            אימוג'י מתאים
        """
        alert_emojis = {
            "critical": "🚨",  # קריטי
            "high": "⚠️",      # גבוה
            "medium": "⚠️",    # בינוני
            "low": "📉"        # נמוך
        }
        
        return alert_emojis.get(alert_level, "📊")
    
    def _get_alert_message(self, alert_level: str, product_name: str, stock_quantity: int, threshold: int) -> str:
        """
        יצירת הודעת התראה מותאמת.
        
        Args:
            alert_level: רמת ההתראה
            product_name: שם המוצר
            stock_quantity: כמות המלאי
            threshold: סף המלאי הנמוך
            
        Returns:
            הודעת התראה מותאמת
        """
        if alert_level == "critical":
            return f"המוצר '{product_name}' אזל מהמלאי! יש להזמין מלאי חדש בדחיפות."
        elif alert_level == "high":
            return f"מלאי נמוך מאוד למוצר '{product_name}'. נותרו {stock_quantity} יחידות בלבד (פחות מ-25% מהסף)."
        elif alert_level == "medium":
            return f"מלאי נמוך למוצר '{product_name}'. נותרו {stock_quantity} יחידות (פחות מ-50% מהסף)."
        else:
            return f"מלאי המוצר '{product_name}' מתקרב לסף. נותרו {stock_quantity} יחידות (סף: {threshold})."

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
        try:
            # הכנת פרמטרים לבקשה
            params = {"per_page": per_page}
            if category_id is not None:
                params["category"] = category_id
            
            # קבלת כל המוצרים
            success, message, products = await self.list(params)
            if not success:
                logger.error(f"שגיאה בקבלת רשימת מוצרים: {message}")
                return []
            
            low_stock_products = []
            for product in products:
                # בדיקה אם המוצר מנהל מלאי
                if not product.get("manage_stock", False):
                    continue
                
                # קבלת כמות המלאי וסף המלאי הנמוך
                stock_quantity = product.get("stock_quantity", 0) or 0
                product_threshold = product.get("low_stock_amount") or threshold
                
                # אם לא הוגדר סף, נמשיך למוצר הבא
                if product_threshold is None:
                    continue
                
                # בדיקה אם המלאי נמוך מהסף
                if stock_quantity <= product_threshold:
                    # חישוב רמת חומרה של ההתראה
                    alert_level = "low"  # ברירת מחדל: נמוך
                    
                    if stock_quantity == 0:
                        alert_level = "critical"  # קריטי: אזל מהמלאי
                    elif stock_quantity <= product_threshold * high_threshold_percentage:
                        alert_level = "high"  # גבוה: פחות מהאחוז שהוגדר מהסף
                    elif stock_quantity <= product_threshold * medium_threshold_percentage:
                        alert_level = "medium"  # בינוני: פחות מהאחוז שהוגדר מהסף
                    
                    # חישוב אחוז מהסף
                    threshold_percentage = (stock_quantity / product_threshold) * 100 if product_threshold > 0 else 0
                    
                    # הכנת נתוני המוצר
                    product_data = {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "sku": product.get("sku", ""),
                        "stock_quantity": stock_quantity,
                        "low_stock_threshold": product_threshold,
                        "threshold_percentage": round(threshold_percentage, 1),
                        "price": float(product.get("price", 0) or 0),
                        "stock_value": round(stock_quantity * float(product.get("price", 0) or 0), 2),
                        "last_modified": product.get("date_modified")
                    }
                    
                    # הוספת נתוני התראה אם נדרש
                    if include_alerts:
                        product_data.update({
                            "alert_level": alert_level,
                            "alert_emoji": self._get_alert_emoji(alert_level),
                            "alert_message": self._get_alert_message(alert_level, product.get("name"), stock_quantity, product_threshold)
                        })
                    
                    low_stock_products.append(product_data)
            
            # מיון לפי רמת חומרה (קריטי -> גבוה -> בינוני -> נמוך)
            if include_alerts:
                alert_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                low_stock_products.sort(key=lambda x: (alert_priority.get(x.get("alert_level", "low"), 4), x.get("threshold_percentage", 0)))
            else:
                # מיון לפי כמות מלאי (מהנמוך לגבוה)
                low_stock_products.sort(key=lambda x: x.get("stock_quantity", 0))
            
            return low_stock_products
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים עם מלאי נמוך: {e}")
            return []

    async def get_out_of_stock_products(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים שאזלו מהמלאי.
        
        Returns:
            רשימת מוצרים שאזלו מהמלאי
        """
        try:
            # קבלת מוצרים שאזלו מהמלאי
            success, message, products = await self.list({"stock_status": "outofstock"})
            if not success:
                logger.error(f"שגיאה בקבלת רשימת מוצרים שאזלו מהמלאי: {message}")
                return []
            
            out_of_stock_products = []
            for product in products:
                product_data = {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "sku": product.get("sku", ""),
                    "last_modified": product.get("date_modified"),
                    "manage_stock": product.get("manage_stock", False),
                    "stock_quantity": product.get("stock_quantity", 0),
                    "backorders_allowed": product.get("backorders_allowed", False)
                }
                out_of_stock_products.append(product_data)
            
            return out_of_stock_products
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים שאזלו מהמלאי: {e}")
            return []

    async def get_inventory_report(self, per_page: int = 100, category_id: Optional[int] = None) -> Dict[str, Any]:
        """
        הפקת דוח מלאי כללי.
        
        Args:
            per_page: מספר מוצרים לעמוד (ברירת מחדל: 100)
            category_id: מזהה קטגוריה לסינון (אופציונלי)
            
        Returns:
            דוח מלאי
        """
        try:
            # הכנת פרמטרים לבקשה
            params = {"per_page": per_page}
            if category_id is not None:
                params["category"] = category_id
            
            # מידע על קטגוריות
            category_info = None
            if category_id is not None:
                success, message, category = await self.get(f"products/categories/{category_id}")
                if success and isinstance(category, dict):
                    category_info = {
                        "id": category.get("id"),
                        "name": category.get("name"),
                        "slug": category.get("slug")
                    }
            
            # קבלת כל המוצרים
            success, message, products = await self.list(params)
            if not success:
                logger.error(f"שגיאה בקבלת רשימת מוצרים: {message}")
                return {
                    "error": "שגיאה בקבלת רשימת מוצרים",
                    "generated_at": datetime.now().isoformat()
                }
            
            # מידע כללי
            total_products = len(products)
            products_with_stock_management = 0
            total_stock_value = 0
            out_of_stock_count = 0
            low_stock_count = 0
            
            # רשימות מוצרים לפי קטגוריות
            out_of_stock_products = []
            low_stock_products = []
            
            for product in products:
                # בדיקה אם המוצר מנהל מלאי
                if product.get("manage_stock", False):
                    products_with_stock_management += 1
                    
                    # חישוב ערך המלאי
                    stock_quantity = product.get("stock_quantity", 0) or 0
                    price = float(product.get("price", 0) or 0)
                    stock_value = stock_quantity * price
                    total_stock_value = round(total_stock_value + stock_value, 2)
                    
                    # בדיקת מלאי נמוך
                    low_stock_threshold = product.get("low_stock_amount")
                    if low_stock_threshold is not None and stock_quantity <= low_stock_threshold and stock_quantity > 0:
                        low_stock_count += 1
                        
                    # בדיקת מלאי אפס
                    if stock_quantity == 0 or product.get("stock_status") == "outofstock":
                        out_of_stock_count += 1
                        out_of_stock_products.append({
                            "id": product.get("id"),
                            "name": product.get("name"),
                            "sku": product.get("sku", ""),
                            "last_modified": product.get("date_modified")
                        })
                    
                    # הוספה לרשימת מלאי נמוך
                    if low_stock_threshold is not None and stock_quantity <= low_stock_threshold and stock_quantity > 0:
                        low_stock_products.append({
                            "id": product.get("id"),
                            "name": product.get("name"),
                            "sku": product.get("sku", ""),
                            "stock_quantity": stock_quantity,
                            "low_stock_threshold": low_stock_threshold,
                            "last_modified": product.get("date_modified")
                        })
            
            # חישוב ממוצע ערך מוצר
            average_product_value = round(total_stock_value / total_products, 4) if total_products > 0 else 0
            
            # הכנת הדוח
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_products": total_products,
                    "products_with_stock_management": products_with_stock_management,
                    "total_stock_value": total_stock_value,
                    "average_product_value": average_product_value,
                    "out_of_stock_count": out_of_stock_count,
                    "low_stock_count": low_stock_count
                },
                "out_of_stock_products": out_of_stock_products,
                "low_stock_products": low_stock_products
            }
            
            # הוספת מידע על הקטגוריה אם נבחרה
            if category_info:
                report["category"] = category_info
            
            return report
        except Exception as e:
            logger.error(f"שגיאה בהפקת דוח מלאי: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            } 