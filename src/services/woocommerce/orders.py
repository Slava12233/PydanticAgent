"""
מודול לניהול הזמנות מול WooCommerce API
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.services.woocommerce.api import WooCommerceAPI

logger = logging.getLogger(__name__)

# סטטוסים אפשריים של הזמנות
ORDER_STATUSES = {
    "pending": "ממתין לתשלום",
    "processing": "בטיפול",
    "on-hold": "בהמתנה",
    "completed": "הושלם",
    "cancelled": "בוטל",
    "refunded": "הוחזר",
    "failed": "נכשל",
    "trash": "נמחק"
}

# מיפוי סטטוסים בעברית לאנגלית
STATUS_MAPPING_HE_TO_EN = {
    "ממתין": "pending",
    "ממתין לתשלום": "pending",
    "בהמתנה": "on-hold",
    "בטיפול": "processing",
    "בעיבוד": "processing",
    "בהכנה": "processing",
    "נשלח": "completed",
    "הושלם": "completed",
    "הסתיים": "completed",
    "בוצע": "completed",
    "בוטל": "cancelled",
    "מבוטל": "cancelled",
    "הוחזר": "refunded",
    "זוכה": "refunded",
    "נכשל": "failed",
    "כשל": "failed",
    "נמחק": "trash"
}

async def get_orders(
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    filters: Dict[str, Any] = None
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    קבלת רשימת הזמנות מחנות WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        filters: פילטרים לסינון התוצאות
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, רשימת הזמנות
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # הכנת פרמטרים לבקשה
        params = {
            "per_page": 20,
            "page": 1
        }
        
        if filters:
            # טיפול בסטטוס
            if "status" in filters:
                params["status"] = filters["status"]
            
            # טיפול בטווח תאריכים
            if "after" in filters:
                params["after"] = filters["after"]
            if "before" in filters:
                params["before"] = filters["before"]
            
            # טיפול במספר תוצאות
            if "limit" in filters and filters["limit"] > 0:
                params["per_page"] = min(filters["limit"], 100)  # מגבלה של WooCommerce API
        
        # קבלת הזמנות מה-API
        status_code, orders = await woo_api._make_request("GET", "orders", params=params)
        
        if status_code != 200 or not orders:
            return True, "לא נמצאו הזמנות העונות לקריטריונים", []
        
        return True, f"נמצאו {len(orders)} הזמנות", orders
        
    except Exception as e:
        logger.error(f"שגיאה בקבלת הזמנות: {str(e)}")
        return False, f"אירעה שגיאה בקבלת הזמנות: {str(e)}", []

async def get_order(
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    order_id: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    קבלת פרטי הזמנה ספציפית מחנות WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        order_id: מזהה ההזמנה
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, פרטי ההזמנה
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # קבלת פרטי ההזמנה מה-API
        status_code, order = await woo_api._make_request("GET", f"orders/{int(order_id)}")
        
        if status_code != 200 or not order:
            return False, f"לא נמצאה הזמנה עם מזהה {order_id}", None
        
        return True, f"נמצאה הזמנה {order_id}", order
        
    except ValueError:
        return False, f"מזהה הזמנה לא תקין: {order_id}", None
    except Exception as e:
        logger.error(f"שגיאה בקבלת הזמנה {order_id}: {str(e)}")
        return False, f"אירעה שגיאה בקבלת הזמנה {order_id}: {str(e)}", None

async def update_order_status(
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    order_id: str, 
    status: str,
    note: str = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    עדכון סטטוס הזמנה בחנות WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        order_id: מזהה ההזמנה
        status: הסטטוס החדש
        note: הערה לעדכון (אופציונלי)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, פרטי ההזמנה המעודכנת
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # המרת סטטוס בעברית לאנגלית אם צריך
        if status in STATUS_MAPPING_HE_TO_EN:
            status = STATUS_MAPPING_HE_TO_EN[status]
        
        # בדיקה שהסטטוס תקין
        if status not in ORDER_STATUSES:
            valid_statuses = ", ".join([f"{k} ({v})" for k, v in ORDER_STATUSES.items()])
            return False, f"סטטוס לא תקין. הסטטוסים האפשריים הם: {valid_statuses}", None
        
        # הכנת נתונים לעדכון
        data = {
            "status": status
        }
        
        # הוספת הערה אם יש
        if note:
            data["customer_note"] = note
        
        # עדכון ההזמנה
        status_code, updated_order = await woo_api._make_request("PUT", f"orders/{int(order_id)}", data=data)
        
        if status_code not in [200, 201] or not updated_order:
            return False, f"לא ניתן לעדכן את הזמנה {order_id}", None
        
        status_display = ORDER_STATUSES.get(status, status)
        return True, f"הזמנה {order_id} עודכנה בהצלחה לסטטוס: {status_display}", updated_order
        
    except ValueError:
        return False, f"מזהה הזמנה לא תקין: {order_id}", None
    except Exception as e:
        logger.error(f"שגיאה בעדכון הזמנה {order_id}: {str(e)}")
        return False, f"אירעה שגיאה בעדכון הזמנה {order_id}: {str(e)}", None

async def cancel_order(
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    order_id: str,
    reason: str = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    ביטול הזמנה בחנות WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        order_id: מזהה ההזמנה
        reason: סיבת הביטול (אופציונלי)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, פרטי ההזמנה המעודכנת
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # הכנת נתונים לעדכון
        data = {
            "status": "cancelled"
        }
        
        # הוספת הערה אם יש
        if reason:
            data["customer_note"] = f"סיבת ביטול: {reason}"
        
        # עדכון ההזמנה
        status_code, updated_order = await woo_api._make_request("PUT", f"orders/{int(order_id)}", data=data)
        
        if status_code not in [200, 201] or not updated_order:
            return False, f"לא ניתן לבטל את הזמנה {order_id}", None
        
        return True, f"הזמנה {order_id} בוטלה בהצלחה", updated_order
        
    except ValueError:
        return False, f"מזהה הזמנה לא תקין: {order_id}", None
    except Exception as e:
        logger.error(f"שגיאה בביטול הזמנה {order_id}: {str(e)}")
        return False, f"אירעה שגיאה בביטול הזמנה {order_id}: {str(e)}", None

async def refund_order(
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    order_id: str,
    amount: float = None,
    reason: str = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    ביצוע החזר כספי להזמנה בחנות WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        order_id: מזהה ההזמנה
        amount: סכום ההחזר (אופציונלי, אם לא צוין יבוצע החזר מלא)
        reason: סיבת ההחזר (אופציונלי)
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, פרטי ההחזר
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # קבלת פרטי ההזמנה תחילה
        status_code, order = await woo_api._make_request("GET", f"orders/{int(order_id)}")
        
        if status_code != 200 or not order:
            return False, f"לא נמצאה הזמנה עם מזהה {order_id}", None
        
        # בדיקה שההזמנה במצב שניתן לבצע עבורה החזר
        if order.get("status") not in ["processing", "completed"]:
            return False, f"לא ניתן לבצע החזר להזמנה במצב {order.get('status')}", None
        
        # הכנת נתונים להחזר
        data = {
            "api_refund": True
        }
        
        # הוספת סכום אם צוין
        if amount is not None:
            data["amount"] = str(amount)
        
        # הוספת סיבה אם צוינה
        if reason:
            data["reason"] = reason
        
        # ביצוע ההחזר
        status_code, refund = await woo_api._make_request("POST", f"orders/{int(order_id)}/refunds", data=data)
        
        if status_code not in [200, 201] or not refund:
            # אם לא הצלחנו ליצור החזר, ננסה לעדכן את סטטוס ההזמנה ל-refunded
            status_code, updated_order = await woo_api._make_request("PUT", f"orders/{int(order_id)}", data={"status": "refunded"})
            
            if status_code not in [200, 201] or not updated_order:
                return False, f"לא ניתן לבצע החזר להזמנה {order_id}", None
            
            refund_amount = amount if amount is not None else order.get("total", "0")
            return True, f"בוצע החזר כספי בסך {refund_amount}₪ להזמנה {order_id}", updated_order
        
        return True, f"בוצע החזר כספי להזמנה {order_id}", refund
        
    except ValueError:
        return False, f"מזהה הזמנה לא תקין: {order_id}", None
    except Exception as e:
        logger.error(f"שגיאה בביצוע החזר להזמנה {order_id}: {str(e)}")
        return False, f"אירעה שגיאה בביצוע החזר להזמנה {order_id}: {str(e)}", None 