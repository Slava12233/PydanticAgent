"""
מודול לניהול מלאי בחנות WooCommerce.
מאפשר ניהול מלאי מוצרים, התראות על מלאי נמוך, ועדכון כמויות.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta

from src.tools.woocommerce_tools import get_woocommerce_api
from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI

logger = logging.getLogger(__name__)

class InventoryManager:
    """מנהל מלאי המאפשר ביצוע פעולות על מלאי מוצרים בחנות WooCommerce."""

    def __init__(self, woocommerce_api=None, use_cache=True, cache_ttl=300):
        """
        אתחול מנהל המלאי.
        
        Args:
            woocommerce_api: אובייקט API של WooCommerce (אופציונלי)
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        if woocommerce_api is None:
            woocommerce_api = get_woocommerce_api()
        
        # בדיקה האם ה-API כבר עטוף במטמון
        if use_cache and not isinstance(woocommerce_api, CachedWooCommerceAPI):
            self.api = CachedWooCommerceAPI(woocommerce_api, cache_ttl)
            self.using_cache = True
        else:
            self.api = woocommerce_api
            self.using_cache = isinstance(woocommerce_api, CachedWooCommerceAPI)
        
        self.cache_ttl = cache_ttl

    async def get_product_stock(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת מידע על מלאי של מוצר ספציפי.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            מידע על המלאי או None אם המוצר לא נמצא
        """
        try:
            product = await self.api.get(f"products/{product_id}")
            if not product:
                logger.warning(f"מוצר עם מזהה {product_id} לא נמצא")
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
            updated_product = await self.api.put(f"products/{product_id}", data=update_data)
            
            if not updated_product:
                logger.warning(f"עדכון מלאי למוצר {product_id} נכשל")
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

    async def get_low_stock_products(self, threshold: Optional[int] = None, include_alerts: bool = True) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים עם מלאי נמוך.
        
        Args:
            threshold: סף כמות להגדרת מלאי נמוך (אופציונלי)
            include_alerts: האם לכלול התראות מלאי (ברירת מחדל: True)
            
        Returns:
            רשימת מוצרים עם מלאי נמוך
        """
        try:
            # קבלת כל המוצרים
            products = await self.api.get("products", params={"per_page": 100})
            
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
                    elif stock_quantity <= product_threshold * 0.25:
                        alert_level = "high"  # גבוה: פחות מ-25% מהסף
                    elif stock_quantity <= product_threshold * 0.5:
                        alert_level = "medium"  # בינוני: פחות מ-50% מהסף
                    
                    # חישוב אחוז מהסף
                    threshold_percentage = (stock_quantity / product_threshold) * 100 if product_threshold > 0 else 0
                    
                    product_data = {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "sku": product.get("sku", ""),
                        "stock_quantity": stock_quantity,
                        "low_stock_threshold": product_threshold,
                        "threshold_percentage": round(threshold_percentage, 1)
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
                low_stock_products.sort(key=lambda x: alert_priority.get(x.get("alert_level", "low"), 4))
            else:
                # מיון לפי כמות מלאי (מהנמוך לגבוה)
                low_stock_products.sort(key=lambda x: x.get("stock_quantity", 0))
            
            return low_stock_products
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים עם מלאי נמוך: {e}")
            return []
    
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

    async def get_out_of_stock_products(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת מוצרים שאזלו מהמלאי.
        
        Returns:
            רשימת מוצרים שאזלו מהמלאי
        """
        try:
            # קבלת מוצרים שאזלו מהמלאי
            products = await self.api.get("products", params={
                "per_page": 100,
                "stock_status": "outofstock"
            })
            
            out_of_stock_products = []
            for product in products:
                out_of_stock_products.append({
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "sku": product.get("sku", ""),
                    "stock_status": product.get("stock_status", "outofstock")
                })
            
            return out_of_stock_products
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים שאזלו מהמלאי: {e}")
            return []

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
            # וידוא שהערך תקין
            valid_values = ['no', 'notify', 'yes']
            if backorders not in valid_values:
                logger.warning(f"ערך לא תקין למדיניות הזמנות מראש: {backorders}. ערכים תקינים: {', '.join(valid_values)}")
                return None
            
            # עדכון המוצר
            updated_product = await self.api.put(f"products/{product_id}", data={"backorders": backorders})
            
            if not updated_product:
                logger.warning(f"עדכון מדיניות הזמנות מראש למוצר {product_id} נכשל")
                return None
            
            logger.info(f"מדיניות הזמנות מראש למוצר {product_id} עודכנה בהצלחה: {backorders}")
            return updated_product
        except Exception as e:
            logger.error(f"שגיאה בעדכון מדיניות הזמנות מראש למוצר {product_id}: {e}")
            return None

    async def forecast_inventory(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """
        תחזית מלאי למוצר ספציפי.
        
        Args:
            product_id: מזהה המוצר
            days: מספר ימים לתחזית (ברירת מחדל: 30)
            
        Returns:
            תחזית מלאי למוצר
        """
        try:
            # קבלת מידע על המוצר
            product = await self.api.get(f"products/{product_id}")
            if not product:
                logger.warning(f"מוצר עם מזהה {product_id} לא נמצא")
                return {"error": f"מוצר עם מזהה {product_id} לא נמצא"}
            
            # בדיקה אם המוצר מנהל מלאי
            if not product.get("manage_stock", False):
                return {"error": f"המוצר '{product.get('name')}' אינו מנהל מלאי"}
            
            # קבלת הזמנות אחרונות (90 ימים אחורה)
            ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()
            
            # קבלת הזמנות שכוללות את המוצר
            orders_params = {
                "after": ninety_days_ago,
                "per_page": 100
            }
            
            orders = await self.api.get("orders", params=orders_params)
            
            # ניתוח קצב המכירות
            product_sales = []
            for order in orders:
                # בדיקה אם ההזמנה הושלמה או בתהליך
                if order.get("status") not in ["completed", "processing"]:
                    continue
                
                # חיפוש המוצר בפריטי ההזמנה
                line_items = order.get("line_items", [])
                for item in line_items:
                    if item.get("product_id") == product_id:
                        try:
                            order_date = datetime.fromisoformat(order.get("date_created", "").replace('Z', '+00:00'))
                            quantity = item.get("quantity", 0)
                            
                            product_sales.append({
                                "date": order_date,
                                "quantity": quantity
                            })
                        except (ValueError, TypeError):
                            continue
            
            # אם אין מכירות, לא ניתן לחזות
            if not product_sales:
                return {
                    "product_id": product_id,
                    "product_name": product.get("name"),
                    "current_stock": product.get("stock_quantity", 0),
                    "forecast_days": days,
                    "error": "אין מספיק נתוני מכירות לביצוע תחזית"
                }
            
            # חישוב ממוצע מכירות יומי
            total_sold = sum(sale["quantity"] for sale in product_sales)
            days_with_data = min(90, (datetime.now() - min(sale["date"] for sale in product_sales)).days + 1)
            daily_sales_avg = total_sold / days_with_data if days_with_data > 0 else 0
            
            # חישוב תחזית
            current_stock = product.get("stock_quantity", 0) or 0
            days_until_empty = current_stock / daily_sales_avg if daily_sales_avg > 0 else float('inf')
            
            # חישוב מלאי צפוי בסוף התקופה
            forecasted_stock = current_stock - (daily_sales_avg * days)
            
            # תאריך צפוי לאזילת המלאי
            out_of_stock_date = None
            if daily_sales_avg > 0:
                out_of_stock_date = (datetime.now() + timedelta(days=days_until_empty)).isoformat()
            
            # יצירת תחזית יומית
            daily_forecast = []
            for day in range(1, days + 1):
                forecast_date = (datetime.now() + timedelta(days=day)).isoformat()
                forecasted_day_stock = max(0, current_stock - (daily_sales_avg * day))
                
                daily_forecast.append({
                    "date": forecast_date,
                    "forecasted_stock": round(forecasted_day_stock, 1),
                    "daily_sales": round(daily_sales_avg, 2)
                })
            
            # יצירת התחזית
            forecast = {
                "product_id": product_id,
                "product_name": product.get("name"),
                "sku": product.get("sku", ""),
                "current_stock": current_stock,
                "daily_sales_avg": round(daily_sales_avg, 2),
                "days_until_empty": round(days_until_empty, 1) if days_until_empty != float('inf') else None,
                "out_of_stock_date": out_of_stock_date,
                "forecast_days": days,
                "forecasted_end_stock": max(0, round(forecasted_stock, 1)),
                "will_be_out_of_stock": forecasted_stock <= 0,
                "reorder_recommendation": forecasted_stock <= 0,
                "daily_forecast": daily_forecast,
                "historical_data": {
                    "days_analyzed": days_with_data,
                    "total_sold": total_sold
                }
            }
            
            return forecast
        except Exception as e:
            logger.error(f"שגיאה בתחזית מלאי למוצר {product_id}: {e}")
            return {
                "product_id": product_id,
                "error": str(e)
            }
    
    async def get_inventory_report(self) -> Dict[str, Any]:
        """
        הפקת דוח מלאי כללי.
        
        Returns:
            דוח מלאי
        """
        try:
            # קבלת כל המוצרים
            products = await self.api.get("products", params={"per_page": 100})
            
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
                    total_stock_value += stock_value
                    
                    # בדיקת מלאי נמוך
                    low_stock_threshold = product.get("low_stock_amount")
                    if low_stock_threshold is not None and stock_quantity <= low_stock_threshold and stock_quantity > 0:
                        low_stock_count += 1
                        low_stock_products.append({
                            "id": product.get("id"),
                            "name": product.get("name"),
                            "sku": product.get("sku", ""),
                            "stock_quantity": stock_quantity,
                            "low_stock_threshold": low_stock_threshold
                        })
                
                # בדיקת מוצרים שאזלו מהמלאי
                if product.get("stock_status") == "outofstock":
                    out_of_stock_count += 1
                    out_of_stock_products.append({
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "sku": product.get("sku", "")
                    })
            
            # יצירת הדוח
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_products": total_products,
                    "products_with_stock_management": products_with_stock_management,
                    "total_stock_value": round(total_stock_value, 2),
                    "out_of_stock_count": out_of_stock_count,
                    "low_stock_count": low_stock_count
                },
                "out_of_stock_products": out_of_stock_products,
                "low_stock_products": low_stock_products
            }
            
            return report
        except Exception as e:
            logger.error(f"שגיאה בהפקת דוח מלאי: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

# פונקציות עזר לשימוש ישיר

async def update_stock_quantity(store_url: str, consumer_key: str, consumer_secret: str, 
                               product_id: int, quantity: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    עדכון כמות מלאי למוצר.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        product_id: מזהה המוצר
        quantity: הכמות החדשה
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, המוצר המעודכן
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל מלאי
        inventory_manager = InventoryManager(woo_api)
        
        # עדכון המלאי
        updated_product = await inventory_manager.update_product_stock(
            product_id=product_id,
            stock_quantity=quantity,
            manage_stock=True,
            in_stock=quantity > 0
        )
        
        if not updated_product:
            return False, f"עדכון מלאי למוצר {product_id} נכשל", None
        
        return True, f"מלאי מוצר {product_id} עודכן בהצלחה. כמות חדשה: {quantity}", updated_product
    except Exception as e:
        logger.error(f"שגיאה בעדכון מלאי: {e}")
        return False, f"שגיאה בעדכון מלאי: {str(e)}", None

async def add_stock_quantity(store_url: str, consumer_key: str, consumer_secret: str, 
                            product_id: int, quantity_to_add: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    הוספת כמות למלאי קיים.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        product_id: מזהה המוצר
        quantity_to_add: הכמות להוספה
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, המוצר המעודכן
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל מלאי
        inventory_manager = InventoryManager(woo_api)
        
        # הוספה למלאי
        updated_product = await inventory_manager.add_to_stock(
            product_id=product_id,
            quantity_to_add=quantity_to_add
        )
        
        if not updated_product:
            return False, f"הוספת כמות למלאי מוצר {product_id} נכשלה", None
        
        return True, f"נוספו {quantity_to_add} יחידות למלאי מוצר {product_id}", updated_product
    except Exception as e:
        logger.error(f"שגיאה בהוספת כמות למלאי: {e}")
        return False, f"שגיאה בהוספת כמות למלאי: {str(e)}", None

async def get_low_stock_report(store_url: str, consumer_key: str, consumer_secret: str, 
                              threshold: Optional[int] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    קבלת דוח מוצרים עם מלאי נמוך.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        threshold: סף כמות להגדרת מלאי נמוך (אופציונלי)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, רשימת מוצרים עם מלאי נמוך
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל מלאי
        inventory_manager = InventoryManager(woo_api)
        
        # קבלת מוצרים עם מלאי נמוך
        low_stock_products = await inventory_manager.get_low_stock_products(threshold)
        
        if not low_stock_products:
            return True, "לא נמצאו מוצרים עם מלאי נמוך", []
        
        return True, f"נמצאו {len(low_stock_products)} מוצרים עם מלאי נמוך", low_stock_products
    except Exception as e:
        logger.error(f"שגיאה בקבלת דוח מלאי נמוך: {e}")
        return False, f"שגיאה בקבלת דוח מלאי נמוך: {str(e)}", []

async def forecast_product_inventory(store_url: str, consumer_key: str, consumer_secret: str, 
                                    product_id: int, days: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    תחזית מלאי למוצר ספציפי.
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        product_id: מזהה המוצר
        days: מספר ימים לתחזית (ברירת מחדל: 30)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, תחזית המלאי
    """
    try:
        # יצירת מופע של ה-API
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל מלאי
        inventory_manager = InventoryManager(woo_api)
        
        # קבלת תחזית מלאי
        forecast = await inventory_manager.forecast_inventory(product_id, days)
        
        if "error" in forecast:
            return False, f"שגיאה בתחזית מלאי למוצר {product_id}: {forecast['error']}", forecast
        
        # פורמט התחזית להודעה
        formatted_forecast = format_inventory_forecast(forecast)
        
        return True, formatted_forecast, forecast
    except Exception as e:
        logger.error(f"שגיאה בתחזית מלאי: {e}")
        return False, f"שגיאה בתחזית מלאי: {str(e)}", None

def format_inventory_forecast(forecast: Dict[str, Any]) -> str:
    """
    פורמט תחזית מלאי לתצוגה.
    
    Args:
        forecast: תחזית מלאי
        
    Returns:
        תחזית מלאי מפורמטת
    """
    if "error" in forecast:
        return f"🚫 שגיאה בתחזית מלאי: {forecast['error']}"
    
    product_name = forecast["product_name"]
    current_stock = forecast["current_stock"]
    daily_sales_avg = forecast["daily_sales_avg"]
    days_until_empty = forecast.get("days_until_empty")
    out_of_stock_date = forecast.get("out_of_stock_date")
    forecast_days = forecast["forecast_days"]
    forecasted_end_stock = forecast["forecasted_end_stock"]
    will_be_out_of_stock = forecast["will_be_out_of_stock"]
    
    # בחירת אימוג'י מתאים למצב
    status_emoji = "🔴" if will_be_out_of_stock else "🟢"
    if not will_be_out_of_stock and forecasted_end_stock <= current_stock * 0.25:
        status_emoji = "🟡"  # מלאי נמוך בסוף התקופה
    
    formatted_forecast = f"{status_emoji} *תחזית מלאי: {product_name}*\n\n"
    
    # מידע נוכחי
    formatted_forecast += "*מצב נוכחי:*\n"
    formatted_forecast += f"• מלאי נוכחי: {current_stock} יחידות\n"
    formatted_forecast += f"• ממוצע מכירות יומי: {daily_sales_avg} יחידות\n"
    
    # תחזית
    formatted_forecast += "\n*תחזית:*\n"
    formatted_forecast += f"• תקופת תחזית: {forecast_days} ימים\n"
    formatted_forecast += f"• מלאי צפוי בסוף התקופה: {forecasted_end_stock} יחידות\n"
    
    if days_until_empty is not None and days_until_empty != float('inf'):
        formatted_forecast += f"• ימים עד אזילת המלאי: {days_until_empty} ימים\n"
        
        if out_of_stock_date:
            try:
                # המרת התאריך לפורמט קריא
                date_obj = datetime.fromisoformat(out_of_stock_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%d/%m/%Y")
                formatted_forecast += f"• תאריך צפוי לאזילת המלאי: {formatted_date}\n"
            except (ValueError, TypeError):
                formatted_forecast += f"• תאריך צפוי לאזילת המלאי: {out_of_stock_date}\n"
    else:
        formatted_forecast += "• המלאי צפוי להספיק מעבר לתקופת התחזית\n"
    
    # המלצה
    formatted_forecast += "\n*המלצה:*\n"
    if will_be_out_of_stock:
        formatted_forecast += "⚠️ יש להזמין מלאי נוסף בהקדם! המלאי צפוי להיגמר בתקופת התחזית.\n"
    elif forecasted_end_stock <= current_stock * 0.25:
        formatted_forecast += "⚠️ מומלץ להזמין מלאי נוסף. המלאי צפוי להיות נמוך מאוד בסוף תקופת התחזית.\n"
    else:
        formatted_forecast += "✅ אין צורך בהזמנת מלאי נוסף בשלב זה.\n"
    
    # נתונים היסטוריים
    historical_data = forecast.get("historical_data", {})
    if historical_data:
        formatted_forecast += f"\n*נתונים היסטוריים:*\n"
        formatted_forecast += f"• תקופת ניתוח: {historical_data.get('days_analyzed', 0)} ימים\n"
        formatted_forecast += f"• סך הכל נמכרו: {historical_data.get('total_sold', 0)} יחידות\n"
    
    return formatted_forecast

def format_inventory_report(report: Dict[str, Any]) -> str:
    """
    פורמט דוח מלאי לתצוגה.
    
    Args:
        report: דוח מלאי
        
    Returns:
        דוח מלאי מפורמט
    """
    if "error" in report:
        return f"🚫 שגיאה בהפקת דוח מלאי: {report['error']}"
    
    summary = report["summary"]
    
    formatted_report = "📊 *דוח מלאי*\n\n"
    
    # סיכום
    formatted_report += "*סיכום:*\n"
    formatted_report += f"• סך הכל מוצרים: {summary['total_products']}\n"
    formatted_report += f"• מוצרים עם ניהול מלאי: {summary['products_with_stock_management']}\n"
    formatted_report += f"• ערך מלאי כולל: {summary['total_stock_value']} ש\"ח\n"
    formatted_report += f"• מוצרים שאזלו מהמלאי: {summary['out_of_stock_count']}\n"
    formatted_report += f"• מוצרים עם מלאי נמוך: {summary['low_stock_count']}\n\n"
    
    # מוצרים שאזלו מהמלאי
    if report["out_of_stock_products"]:
        formatted_report += "*מוצרים שאזלו מהמלאי:*\n"
        for product in report["out_of_stock_products"][:10]:  # הצגת 10 הראשונים בלבד
            formatted_report += f"• {product['name']} (מק\"ט: {product['sku']})\n"
        
        if len(report["out_of_stock_products"]) > 10:
            formatted_report += f"  _ועוד {len(report['out_of_stock_products']) - 10} מוצרים נוספים..._\n"
        
        formatted_report += "\n"
    
    # מוצרים עם מלאי נמוך
    if report["low_stock_products"]:
        formatted_report += "*מוצרים עם מלאי נמוך:*\n"
        for product in report["low_stock_products"][:10]:  # הצגת 10 הראשונים בלבד
            formatted_report += f"• {product['name']} - נותרו {product['stock_quantity']} יחידות (סף: {product['low_stock_threshold']})\n"
        
        if len(report["low_stock_products"]) > 10:
            formatted_report += f"  _ועוד {len(report['low_stock_products']) - 10} מוצרים נוספים..._\n"
    
    return formatted_report
