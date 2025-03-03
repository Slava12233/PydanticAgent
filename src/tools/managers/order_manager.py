"""
מודול לניהול הזמנות מול WooCommerce API
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.tools.intent.order_intent import extract_order_data
from src.tools.woocommerce_tools import get_woocommerce_api

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
        from src.services.woocommerce.api import WooCommerceAPI
        
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
        orders = await woo_api.get_orders(params)
        
        if not orders:
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
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # קבלת פרטי ההזמנה מה-API
        order = await woo_api.get_order(int(order_id))
        
        if not order:
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
        from src.services.woocommerce.api import WooCommerceAPI
        
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
        updated_order = await woo_api.update_order(int(order_id), data)
        
        if not updated_order:
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
        from src.services.woocommerce.api import WooCommerceAPI
        
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
        updated_order = await woo_api.update_order(int(order_id), data)
        
        if not updated_order:
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
        from src.services.woocommerce.api import WooCommerceAPI
        
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # קבלת פרטי ההזמנה תחילה
        order = await woo_api.get_order(int(order_id))
        
        if not order:
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
        # TODO: לממש את הפונקציה create_refund ב-WooCommerceAPI
        # refund = await woo_api.create_refund(int(order_id), data)
        
        # כרגע נעדכן רק את סטטוס ההזמנה ל-refunded
        updated_order = await woo_api.update_order(int(order_id), {"status": "refunded"})
        
        if not updated_order:
            return False, f"לא ניתן לבצע החזר להזמנה {order_id}", None
        
        refund_amount = amount if amount is not None else order.get("total", "0")
        return True, f"בוצע החזר כספי בסך {refund_amount}₪ להזמנה {order_id}", updated_order
        
    except ValueError:
        return False, f"מזהה הזמנה לא תקין: {order_id}", None
    except Exception as e:
        logger.error(f"שגיאה בביצוע החזר להזמנה {order_id}: {str(e)}")
        return False, f"אירעה שגיאה בביצוע החזר להזמנה {order_id}: {str(e)}", None

def format_order_for_display(order: Dict[str, Any]) -> str:
    """
    פורמוט הזמנה להצגה למשתמש
    
    Args:
        order: נתוני ההזמנה
        
    Returns:
        מחרוזת מפורמטת להצגה
    """
    if not order:
        return "לא נמצאו פרטי הזמנה"
    
    # מיפוי סטטוסים לעברית
    status_mapping = {
        "pending": "ממתין לתשלום",
        "processing": "בטיפול",
        "on-hold": "בהמתנה",
        "completed": "הושלם",
        "cancelled": "בוטל",
        "refunded": "הוחזר",
        "failed": "נכשל",
        "trash": "נמחק"
    }
    
    # קבלת פרטי הלקוח
    billing = order.get("billing", {})
    customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
    if not customer_name:
        customer_name = "לא צוין"
    
    # קבלת פרטי המשלוח
    shipping = order.get("shipping", {})
    shipping_address = ""
    if shipping.get("address_1"):
        shipping_address = f"{shipping.get('address_1', '')}"
        if shipping.get("address_2"):
            shipping_address += f", {shipping.get('address_2', '')}"
        if shipping.get("city"):
            shipping_address += f", {shipping.get('city', '')}"
        if shipping.get("state"):
            shipping_address += f", {shipping.get('state', '')}"
        if shipping.get("postcode"):
            shipping_address += f" {shipping.get('postcode', '')}"
        if shipping.get("country"):
            shipping_address += f", {shipping.get('country', '')}"
    
    if not shipping_address:
        shipping_address = "לא צוין"
    
    # קבלת פרטי המוצרים
    line_items = order.get("line_items", [])
    products_text = ""
    
    for i, item in enumerate(line_items, 1):
        product_name = item.get("name", "מוצר לא ידוע")
        quantity = item.get("quantity", 1)
        price = item.get("price", "0")
        total = item.get("total", "0")
        
        products_text += f"  {i}. {product_name} x{quantity} - {price}₪ (סה\"כ: {total}₪)\n"
    
    if not products_text:
        products_text = "  לא נמצאו מוצרים בהזמנה\n"
    
    # בניית הטקסט המפורמט
    order_text = (
        f"🛒 *הזמנה #{order.get('id', 'לא ידוע')}*\n\n"
        f"📅 *תאריך:* {order.get('date_created', 'לא ידוע')}\n"
        f"📊 *סטטוס:* {status_mapping.get(order.get('status', ''), order.get('status', 'לא ידוע'))}\n"
        f"💰 *סכום:* {order.get('total', '0')}₪\n\n"
        
        f"👤 *פרטי לקוח:*\n"
        f"  שם: {customer_name}\n"
        f"  טלפון: {billing.get('phone', 'לא צוין')}\n"
        f"  אימייל: {billing.get('email', 'לא צוין')}\n\n"
        
        f"🚚 *פרטי משלוח:*\n"
        f"  כתובת: {shipping_address}\n"
        f"  שיטת משלוח: {order.get('shipping_lines', [{}])[0].get('method_title', 'לא צוין') if order.get('shipping_lines') else 'לא צוין'}\n\n"
        
        f"💳 *פרטי תשלום:*\n"
        f"  שיטת תשלום: {order.get('payment_method_title', 'לא צוין')}\n\n"
        
        f"📦 *מוצרים:*\n"
        f"{products_text}\n"
        
        f"💵 *סיכום:*\n"
        f"  סה\"כ מוצרים: {order.get('total_items', '0')}₪\n"
        f"  משלוח: {order.get('shipping_total', '0')}₪\n"
        f"  מיסים: {order.get('total_tax', '0')}₪\n"
        f"  הנחות: -{order.get('discount_total', '0')}₪\n"
        f"  *סה\"כ לתשלום: {order.get('total', '0')}₪*\n\n"
        
        f"📝 *הערות:*\n"
        f"  {order.get('customer_note', 'אין הערות')}"
    )
    
    return order_text

def format_orders_list_for_display(orders: List[Dict[str, Any]]) -> str:
    """
    פורמוט רשימת הזמנות להצגה למשתמש
    
    Args:
        orders: רשימת הזמנות
        
    Returns:
        מחרוזת מפורמטת להצגה
    """
    if not orders:
        return "לא נמצאו הזמנות"
    
    # מיפוי סטטוסים לעברית
    status_mapping = {
        "pending": "ממתין לתשלום",
        "processing": "בטיפול",
        "on-hold": "בהמתנה",
        "completed": "הושלם",
        "cancelled": "בוטל",
        "refunded": "הוחזר",
        "failed": "נכשל",
        "trash": "נמחק"
    }
    
    # בניית הטקסט המפורמט
    orders_text = f"📋 *רשימת הזמנות ({len(orders)})*\n\n"
    
    for order in orders:
        # קבלת פרטי הלקוח
        billing = order.get("billing", {})
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        if not customer_name:
            customer_name = "לא צוין"
        
        # קבלת מספר פריטים
        items_count = len(order.get("line_items", []))
        
        # הוספת אמוג'י לסטטוס
        status = order.get("status", "")
        status_emoji = "⏳"
        if status == "processing":
            status_emoji = "🔄"
        elif status == "completed":
            status_emoji = "✅"
        elif status == "cancelled":
            status_emoji = "❌"
        elif status == "refunded":
            status_emoji = "💰"
        elif status == "failed":
            status_emoji = "⚠️"
        
        orders_text += (
            f"🛒 *הזמנה #{order.get('id', 'לא ידוע')}* ({order.get('date_created', 'לא ידוע')})\n"
            f"  {status_emoji} סטטוס: {status_mapping.get(status, status)}\n"
            f"  👤 לקוח: {customer_name}\n"
            f"  📱 טלפון: {billing.get('phone', 'לא צוין')}\n"
            f"  📦 פריטים: {items_count}\n"
            f"  💰 סה\"כ: {order.get('total', '0')}₪\n\n"
        )
    
    return orders_text

def create_order_from_text(text: str) -> Dict[str, Any]:
    """
    יצירת הזמנה חדשה מטקסט.

    Args:
        text: טקסט המכיל את פרטי ההזמנה.

    Returns:
        תוצאת יצירת ההזמנה.
    """
    order_data = extract_order_data(text)
    
    if not order_data:
        return {"success": False, "message": "לא ניתן לחלץ נתוני הזמנה מהטקסט."}
    
    # בדיקת שדות חובה
    required_fields = []
    missing_fields = [field for field in required_fields if field not in order_data]
    
    if missing_fields:
        return {
            "success": False,
            "message": f"חסרים שדות חובה: {', '.join(missing_fields)}",
            "extracted_data": order_data
        }
    
    try:
        api = get_woocommerce_api()
        result = api.post("orders", data=order_data)
        
        if result:
            return {
                "success": True,
                "message": f"ההזמנה נוצרה בהצלחה. מזהה הזמנה: {result.get('id')}",
                "order": result
            }
        else:
            return {
                "success": False,
                "message": "יצירת ההזמנה נכשלה.",
                "extracted_data": order_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה ביצירת ההזמנה: {str(e)}",
            "extracted_data": order_data
        }

def update_order_from_text(text: str, order_id: Optional[int] = None) -> Dict[str, Any]:
    """
    עדכון פרטי הזמנה מטקסט.

    Args:
        text: טקסט המכיל את פרטי ההזמנה המעודכנים.
        order_id: מזהה ההזמנה (אופציונלי). אם לא מסופק, ינסה לחלץ מהטקסט.

    Returns:
        תוצאת עדכון ההזמנה.
    """
    order_data = extract_order_data(text)
    
    if not order_data:
        return {"success": False, "message": "לא ניתן לחלץ נתוני הזמנה מהטקסט."}
    
    try:
        # אם לא סופק מזהה הזמנה, ננסה לחלץ אותו מהטקסט
        if order_id is None:
            # בדיקה אם יש מזהה בנתונים שחולצו
            if "id" in order_data:
                order_id = int(order_data["id"])
                # הסרת המזהה מהנתונים לעדכון
                del order_data["id"]
        
        # אם עדיין אין מזהה הזמנה, לא ניתן לעדכן
        if order_id is None:
            return {
                "success": False,
                "message": "לא ניתן לזהות את ההזמנה לעדכון. אנא ספק מזהה הזמנה.",
                "extracted_data": order_data
            }
        
        api = get_woocommerce_api()
        result = api.put(f"orders/{order_id}", data=order_data)
        
        if result:
            return {
                "success": True,
                "message": f"פרטי ההזמנה עודכנו בהצלחה.",
                "order": result
            }
        else:
            return {
                "success": False,
                "message": f"עדכון פרטי ההזמנה נכשל.",
                "extracted_data": order_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בעדכון פרטי ההזמנה: {str(e)}",
            "extracted_data": order_data
        }

def get_orders_from_text(text: str) -> Dict[str, Any]:
    """
    חיפוש הזמנות לפי טקסט.

    Args:
        text: טקסט המכיל את פרטי החיפוש.

    Returns:
        תוצאת החיפוש.
    """
    order_data = extract_order_data(text)
    
    if not order_data:
        return {"success": False, "message": "לא ניתן לחלץ פרטי חיפוש מהטקסט."}
    
    try:
        api = get_woocommerce_api()
        filters = {}
        
        # הוספת פילטרים לפי הנתונים שחולצו
        if "id" in order_data:
            # אם יש מזהה הזמנה, נחפש הזמנה ספציפית
            result = api.get(f"orders/{order_data['id']}")
            if result:
                return {
                    "success": True,
                    "message": f"נמצאה הזמנה עם מזהה {order_data['id']}.",
                    "orders": [result]
                }
            else:
                return {
                    "success": False,
                    "message": f"לא נמצאה הזמנה עם מזהה {order_data['id']}.",
                    "extracted_data": order_data
                }
        
        # פילטרים לפי סטטוס
        if "status" in order_data:
            filters["status"] = order_data["status"]
        
        # פילטרים לפי תאריכים
        if "date_created_from" in order_data:
            filters["after"] = order_data["date_created_from"]
        if "date_created_to" in order_data:
            filters["before"] = order_data["date_created_to"]
        
        # פילטרים לפי לקוח
        if "customer_id" in order_data:
            filters["customer"] = order_data["customer_id"]
        
        # ביצוע החיפוש
        orders = api.get("orders", params=filters)
        
        if orders:
            return {
                "success": True,
                "message": f"נמצאו {len(orders)} הזמנות התואמות את החיפוש.",
                "orders": orders
            }
        else:
            return {
                "success": False,
                "message": "לא נמצאו הזמנות התואמות את החיפוש.",
                "extracted_data": order_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בחיפוש הזמנות: {str(e)}",
            "extracted_data": order_data
        }

def get_order_from_text(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי הזמנה מטקסט וחיפוש הזמנה ספציפית.

    Args:
        text: טקסט המכיל את פרטי ההזמנה.

    Returns:
        תוצאת החיפוש.
    """
    order_data = extract_order_data(text)
    
    if not order_data:
        return {"success": False, "message": "לא ניתן לחלץ פרטי הזמנה מהטקסט."}
    
    try:
        api = get_woocommerce_api()
        
        # חיפוש לפי מזהה הזמנה
        if "id" in order_data:
            result = api.get(f"orders/{order_data['id']}")
            if result:
                return {
                    "success": True,
                    "message": f"נמצאה הזמנה עם מזהה {order_data['id']}.",
                    "order": result
                }
            else:
                return {
                    "success": False,
                    "message": f"לא נמצאה הזמנה עם מזהה {order_data['id']}.",
                    "extracted_data": order_data
                }
        
        # אם אין מזהה הזמנה, ננסה לחפש לפי פרמטרים אחרים
        filters = {}
        
        # פילטרים לפי סטטוס
        if "status" in order_data:
            filters["status"] = order_data["status"]
        
        # פילטרים לפי תאריכים
        if "date_created_from" in order_data:
            filters["after"] = order_data["date_created_from"]
        if "date_created_to" in order_data:
            filters["before"] = order_data["date_created_to"]
        
        # פילטרים לפי לקוח
        if "customer_id" in order_data:
            filters["customer"] = order_data["customer_id"]
        elif "customer_email" in order_data:
            # חיפוש לקוח לפי אימייל
            customers = api.get("customers", params={"email": order_data["customer_email"]})
            if customers and len(customers) > 0:
                filters["customer"] = customers[0]["id"]
        
        # אם יש פילטרים, נחפש הזמנות
        if filters:
            orders = api.get("orders", params=filters)
            
            if orders and len(orders) > 0:
                # נחזיר את ההזמנה הראשונה שנמצאה
                return {
                    "success": True,
                    "message": f"נמצאה הזמנה התואמת את החיפוש.",
                    "order": orders[0]
                }
            else:
                return {
                    "success": False,
                    "message": "לא נמצאה הזמנה התואמת את החיפוש.",
                    "extracted_data": order_data
                }
        
        return {
            "success": False,
            "message": "לא נמצאו פרטים מספיקים לחיפוש הזמנה.",
            "extracted_data": order_data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בחיפוש הזמנה: {str(e)}",
            "extracted_data": order_data
        }
