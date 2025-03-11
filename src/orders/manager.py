"""
מודול לניהול הזמנות מול WooCommerce API
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.woocommerce.api.api import WooCommerceAPI, CachedWooCommerceAPI
from src.orders.intent import extract_order_data
from src.tools.store.managers.base_manager import BaseManager
from src.woocommerce.utils.order_formatter import (
    ORDER_STATUSES,
    STATUS_MAPPING_HE_TO_EN,
    map_status_to_english,
    format_order_for_display,
    format_orders_list_for_display,
    create_order_from_text,
    update_order_from_text,
    get_orders_from_text,
    get_order_from_text
)

logger = logging.getLogger(__name__)

class OrderManager(BaseManager):
    """
    מחלקה לניהול הזמנות
    """
    
    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב
        """
        return "orders"
    
    async def get_orders(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        מקבל רשימת הזמנות לפי פילטרים
        
        Args:
            filters: פילטרים לחיפוש
            
        Returns:
            רשימת הזמנות
        """
        try:
            # הכנת פרמטרים לחיפוש
            params = filters or {}
            
            # ביצוע החיפוש
            success, message, orders = await self.list(params)
            
            if not success:
                logger.error(f"שגיאה בקבלת הזמנות: {message}")
                return []
            
            return orders
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות: {str(e)}")
            return []

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        מקבל הזמנה לפי מזהה
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            נתוני ההזמנה או None אם לא נמצאה
        """
        try:
            success, message, order = await self.get(order_id)
            
            if not success:
                logger.error(f"שגיאה בקבלת הזמנה {order_id}: {message}")
                return None
            
            return order
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנה {order_id}: {str(e)}")
            return None

    async def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        יצירת הזמנה חדשה
        
        Args:
            order_data: נתוני ההזמנה
            
        Returns:
            ההזמנה שנוצרה או None אם היצירה נכשלה
        """
        try:
            # הכנת נתוני ההזמנה לשליחה ל-API
            api_order_data = order_data
            
            # שימוש בפונקציית create של מחלקת הבסיס
            success, message, response = await self.create(api_order_data)
            return response if success else None
            
        except Exception as e:
            logger.error(f"שגיאה ביצירת הזמנה: {str(e)}")
            return None

    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        עדכון הזמנה קיימת
        
        Args:
            order_id: מזהה ההזמנה
            order_data: נתוני ההזמנה לעדכון
            
        Returns:
            ההזמנה המעודכנת או None אם העדכון נכשל
        """
        try:
            # הכנת נתוני ההזמנה לשליחה ל-API
            api_order_data = order_data
            
            # שימוש בפונקציית update של מחלקת הבסיס
            success, message, response = await self.update(order_id, api_order_data)
            return response if success else None
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון הזמנה {order_id}: {str(e)}")
            return None

    async def update_order_status(self, order_id: str, status: str) -> Optional[Dict[str, Any]]:
        """
        עדכון סטטוס הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            status: הסטטוס החדש
            
        Returns:
            ההזמנה המעודכנת או None אם העדכון נכשל
        """
        try:
            # המרת הסטטוס לאנגלית אם צריך
            english_status = map_status_to_english(status)
            
            # הכנת נתוני העדכון
            update_data = {
                "status": english_status
            }
            
            # עדכון ההזמנה
            return await self.update_order(order_id, update_data)
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון סטטוס הזמנה {order_id}: {str(e)}")
            return None

    async def cancel_order(self, order_id: str, reason: str = None) -> Optional[Dict[str, Any]]:
        """
        ביטול הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            reason: סיבת הביטול (אופציונלי)
            
        Returns:
            ההזמנה המבוטלת או None אם הביטול נכשל
        """
        try:
            # הכנת נתוני העדכון
            update_data = {
                "status": "cancelled"
            }
            
            # הוספת הערה אם יש סיבת ביטול
            if reason:
                update_data["customer_note"] = f"סיבת ביטול: {reason}"
            
            # עדכון ההזמנה
            return await self.update_order(order_id, update_data)
            
        except Exception as e:
            logger.error(f"שגיאה בביטול הזמנה {order_id}: {str(e)}")
            return None

    async def refund_order(self, order_id: str, amount: float = None, reason: str = None) -> Optional[Dict[str, Any]]:
        """
        ביצוע החזר כספי להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            amount: סכום ההחזר (אופציונלי, ברירת מחדל: החזר מלא)
            reason: סיבת ההחזר (אופציונלי)
            
        Returns:
            פרטי ההחזר או None אם ההחזר נכשל
        """
        try:
            # קבלת פרטי ההזמנה
            order = await self.get_order(order_id)
            if not order:
                logger.error(f"לא נמצאה הזמנה עם מזהה {order_id}")
                return None
            
            # חישוב סכום ההחזר אם לא צוין
            if amount is None:
                amount = float(order.get("total", 0))
            
            # הכנת נתוני ההחזר
            refund_data = {
                "amount": str(amount)
            }
            
            # הוספת סיבת ההחזר אם צוינה
            if reason:
                refund_data["reason"] = reason
            
            # ביצוע ההחזר
            endpoint = f"orders/{order_id}/refunds"
            success, message, response = await self.api.post(endpoint, refund_data)
            
            if not success:
                logger.error(f"שגיאה בביצוע החזר כספי להזמנה {order_id}: {message}")
                return None
            
            return response
            
        except Exception as e:
            logger.error(f"שגיאה בביצוע החזר כספי להזמנה {order_id}: {str(e)}")
            return None

    async def get_order_notes(self, order_id: str) -> List[Dict[str, Any]]:
        """
        קבלת הערות להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            רשימת הערות
        """
        try:
            endpoint = f"orders/{order_id}/notes"
            success, message, response = await self.api.get(endpoint)
            
            if not success:
                logger.error(f"שגיאה בקבלת הערות להזמנה {order_id}: {message}")
                return []
            
            return response
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הערות להזמנה {order_id}: {str(e)}")
            return []

    async def add_order_note(self, order_id: str, note: str, is_customer_note: bool = False) -> Optional[Dict[str, Any]]:
        """
        הוספת הערה להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            note: תוכן ההערה
            is_customer_note: האם ההערה מיועדת ללקוח
            
        Returns:
            פרטי ההערה שנוספה או None אם ההוספה נכשלה
        """
        try:
            # הכנת נתוני ההערה
            note_data = {
                "note": note,
                "customer_note": is_customer_note
            }
            
            # הוספת ההערה
            endpoint = f"orders/{order_id}/notes"
            success, message, response = await self.api.post(endpoint, note_data)
            
            if not success:
                logger.error(f"שגיאה בהוספת הערה להזמנה {order_id}: {message}")
                return None
            
            return response
            
        except Exception as e:
            logger.error(f"שגיאה בהוספת הערה להזמנה {order_id}: {str(e)}")
            return None

    async def get_order_shipping_methods(self, order_id: str) -> List[Dict[str, Any]]:
        """
        קבלת שיטות משלוח להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            רשימת שיטות משלוח
        """
        try:
            # קבלת פרטי ההזמנה
            order = await self.get_order(order_id)
            if not order:
                logger.error(f"לא נמצאה הזמנה עם מזהה {order_id}")
                return []
            
            # חילוץ שיטות המשלוח מההזמנה
            shipping_lines = order.get("shipping_lines", [])
            return shipping_lines
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת שיטות משלוח להזמנה {order_id}: {str(e)}")
            return []

    async def update_order_shipping(self, order_id: str, tracking_id: str, carrier: str = None) -> Optional[Dict[str, Any]]:
        """
        עדכון פרטי משלוח להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            tracking_id: מספר מעקב
            carrier: חברת השילוח (אופציונלי)
            
        Returns:
            ההזמנה המעודכנת או None אם העדכון נכשל
        """
        try:
            # הכנת הערה עם פרטי המשלוח
            note = f"מספר מעקב: {tracking_id}"
            if carrier:
                note += f", חברת שילוח: {carrier}"
            
            # הוספת הערה עם פרטי המשלוח
            await self.add_order_note(order_id, note, True)
            
            # עדכון סטטוס ההזמנה ל"נשלח"
            return await self.update_order_status(order_id, "shipped")
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון פרטי משלוח להזמנה {order_id}: {str(e)}")
            return None

    async def search_orders(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        חיפוש הזמנות לפי מילת חיפוש
        
        Args:
            search_term: מילת החיפוש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת הזמנות שתואמות את החיפוש
        """
        try:
            # הכנת פרמטרים לחיפוש
            params = {
                "search": search_term,
                "per_page": min(limit, 100)  # מגבלה של WooCommerce API
            }
            
            # ביצוע החיפוש
            return await self.get_orders(params)
            
        except Exception as e:
            logger.error(f"שגיאה בחיפוש הזמנות: {str(e)}")
            return []

    async def get_orders_by_status(self, status: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        קבלת הזמנות לפי סטטוס
        
        Args:
            status: הסטטוס המבוקש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת הזמנות בסטטוס המבוקש
        """
        try:
            # המרת הסטטוס לאנגלית אם צריך
            english_status = map_status_to_english(status)
            
            # הכנת פרמטרים לחיפוש
            params = {
                "status": english_status,
                "per_page": min(limit, 100)  # מגבלה של WooCommerce API
            }
            
            # ביצוע החיפוש
            return await self.get_orders(params)
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות לפי סטטוס: {str(e)}")
            return []

    async def get_orders_by_date_range(self, start_date: datetime = None, end_date: datetime = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        קבלת הזמנות לפי טווח תאריכים
        
        Args:
            start_date: תאריך התחלה (אופציונלי)
            end_date: תאריך סיום (אופציונלי)
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת הזמנות בטווח התאריכים
        """
        try:
            # הכנת פרמטרים לחיפוש
            params = {
                "per_page": min(limit, 100)  # מגבלה של WooCommerce API
            }
            
            # הוספת תאריך התחלה אם צוין
            if start_date:
                params["after"] = start_date.isoformat()
            
            # הוספת תאריך סיום אם צוין
            if end_date:
                params["before"] = end_date.isoformat()
            
            # ביצוע החיפוש
            return await self.get_orders(params)
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות לפי טווח תאריכים: {str(e)}")
            return []

    async def get_orders_by_customer(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        קבלת הזמנות של לקוח מסוים
        
        Args:
            customer_id: מזהה הלקוח
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת הזמנות של הלקוח
        """
        try:
            # הכנת פרמטרים לחיפוש
            params = {
                "customer": customer_id,
                "per_page": min(limit, 100)  # מגבלה של WooCommerce API
            }
            
            # ביצוע החיפוש
            return await self.get_orders(params)
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות של לקוח {customer_id}: {str(e)}")
            return [] 