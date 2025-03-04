"""
מודול לניהול הזמנות מול WooCommerce API
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.tools.intent.order_intent import extract_order_data
from src.tools.store_tools.woocommerce_tools import get_woocommerce_api
from src.tools.store_tools.managers.base_manager import BaseManager

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

class OrderManager(BaseManager):
    """
    מחלקה לניהול הזמנות
    """
    
    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב
        """
        return "orders"
    
    def _map_status_to_english(self, status: str) -> str:
        """
        ממיר סטטוס בעברית לאנגלית
        
        Args:
            status: הסטטוס בעברית
            
        Returns:
            הסטטוס באנגלית
        """
        return STATUS_MAPPING_HE_TO_EN.get(status, status)
    
    async def get_orders(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        קבלת רשימת הזמנות
        
        Args:
            filters: פילטרים לסינון התוצאות
            
        Returns:
            רשימת הזמנות
        """
        # הכנת פרמטרים לבקשה
        params = {
            "per_page": 20,
            "page": 1
        }
        
        if filters:
            # טיפול בסטטוס
            if "status" in filters:
                params["status"] = self._map_status_to_english(filters["status"])
            
            # טיפול בטווח תאריכים
            if "after" in filters:
                params["after"] = filters["after"]
            if "before" in filters:
                params["before"] = filters["before"]
            
            # טיפול במספר תוצאות
            if "limit" in filters and filters["limit"] > 0:
                params["per_page"] = min(filters["limit"], 100)  # מגבלה של WooCommerce API
        
        # שימוש בפונקציית list של מחלקת הבסיס
        success, message, response = await self.list(params)
        return response if success else []
    
    async def get_order(self, order_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        קבלת פרטי הזמנה ספציפית
        
        Args:
            order_id: מזהה ההזמנה
            
        Returns:
            פרטי ההזמנה או None אם לא נמצאה
        """
        try:
            order_id = int(order_id)
        except ValueError:
            logger.error(f"מזהה הזמנה לא תקין: {order_id}")
            return None
        
        # שימוש בפונקציית get של מחלקת הבסיס
        success, message, response = await self.get(order_id)
        return response if success else None
    
    async def update_order_status(self, order_id: Union[int, str], status: str, note: str = None) -> Optional[Dict[str, Any]]:
        """
        עדכון סטטוס הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            status: הסטטוס החדש
            note: הערה לעדכון (אופציונלי)
            
        Returns:
            פרטי ההזמנה המעודכנת או None אם העדכון נכשל
        """
        try:
            order_id = int(order_id)
        except ValueError:
            logger.error(f"מזהה הזמנה לא תקין: {order_id}")
            return None
        
        # המרת סטטוס בעברית לאנגלית אם צריך
        status = self._map_status_to_english(status)
        
        # בדיקה שהסטטוס תקין
        if status not in ORDER_STATUSES:
            valid_statuses = ", ".join([f"{k} ({v})" for k, v in ORDER_STATUSES.items()])
            logger.error(f"סטטוס לא תקין. הסטטוסים האפשריים הם: {valid_statuses}")
            return None
        
        # הכנת נתונים לעדכון
        data = {
            "status": status
        }
        
        # הוספת הערה אם יש
        if note:
            data["customer_note"] = note
        
        # שימוש בפונקציית update של מחלקת הבסיס
        success, message, response = await self.update(order_id, data)
        return response if success else None
    
    async def cancel_order(self, order_id: Union[int, str], reason: str = None) -> Optional[Dict[str, Any]]:
        """
        ביטול הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            reason: סיבת הביטול (אופציונלי)
            
        Returns:
            פרטי ההזמנה המעודכנת או None אם הביטול נכשל
        """
        return await self.update_order_status(order_id, "cancelled", reason)
    
    async def refund_order(self, order_id: Union[int, str], amount: float = None, reason: str = None) -> Optional[Dict[str, Any]]:
        """
        החזר כספי להזמנה
        
        Args:
            order_id: מזהה ההזמנה
            amount: סכום ההחזר (אופציונלי, אם לא צוין יוחזר כל הסכום)
            reason: סיבת ההחזר (אופציונלי)
            
        Returns:
            פרטי ההזמנה המעודכנת או None אם ההחזר נכשל
        """
        try:
            order_id = int(order_id)
        except ValueError:
            logger.error(f"מזהה הזמנה לא תקין: {order_id}")
            return None
        
        # קבלת פרטי ההזמנה
        order = await self.get_order(order_id)
        if not order:
            return None
        
        # אם לא צוין סכום, נחזיר את כל הסכום
        if amount is None:
            amount = float(order.get("total", 0))
        
        # הכנת נתונים להחזר
        data = {
            "amount": str(amount)
        }
        
        if reason:
            data["reason"] = reason
        
        # שליחת בקשת החזר
        status_code, response = await self.woocommerce._make_request("POST", f"orders/{order_id}/refunds", data=data)
        
        if status_code in (200, 201):
            # עדכון סטטוס ההזמנה ל-"refunded"
            return await self.update_order_status(order_id, "refunded", reason)
        else:
            logger.error(f"שגיאה בביצוע החזר להזמנה {order_id}: {status_code} - {response}")
            return None

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
