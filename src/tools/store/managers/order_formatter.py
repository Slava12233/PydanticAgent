"""
מודול לפורמוט והמרת הזמנות
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

from src.core.task_identification.intents.order_intent import extract_order_data

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

def map_status_to_english(status: str) -> str:
    """
    ממפה סטטוס הזמנה בעברית לאנגלית
    
    Args:
        status: סטטוס בעברית
        
    Returns:
        סטטוס באנגלית
    """
    if not status:
        return None
        
    # אם הסטטוס כבר באנגלית
    if status.lower() in ORDER_STATUSES:
        return status.lower()
        
    # חיפוש במיפוי
    return STATUS_MAPPING_HE_TO_EN.get(status.strip(), "processing")

def format_order_for_display(order: Dict[str, Any]) -> str:
    """
    מפרמט הזמנה לתצוגה למשתמש
    
    Args:
        order: נתוני ההזמנה
        
    Returns:
        מחרוזת מפורמטת של ההזמנה
    """
    if not order:
        return "לא נמצאה הזמנה"
    
    try:
        # מידע בסיסי
        order_id = order.get("id", "לא ידוע")
        status = order.get("status", "לא ידוע")
        status_he = ORDER_STATUSES.get(status, status)
        
        # תאריכים
        date_created = order.get("date_created", "")
        if date_created:
            try:
                date_obj = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = date_created
        else:
            date_str = "לא ידוע"
        
        # פרטי לקוח
        billing = order.get("billing", {})
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        if not customer_name:
            customer_name = "לא ידוע"
        
        customer_email = billing.get("email", "לא ידוע")
        customer_phone = billing.get("phone", "לא ידוע")
        
        # כתובת
        address_parts = []
        if billing.get("address_1"):
            address_parts.append(billing.get("address_1"))
        if billing.get("address_2"):
            address_parts.append(billing.get("address_2"))
        if billing.get("city"):
            address_parts.append(billing.get("city"))
        
        address = ", ".join(address_parts) if address_parts else "לא ידוע"
        
        # סכומים
        total = order.get("total", "0")
        currency = order.get("currency", "₪")
        
        # פריטים
        items = order.get("line_items", [])
        items_text = ""
        
        for item in items:
            item_name = item.get("name", "פריט לא ידוע")
            item_quantity = item.get("quantity", 1)
            item_total = item.get("total", "0")
            items_text += f"• {item_name} (כמות: {item_quantity}) - {item_total} {currency}\n"
        
        if not items:
            items_text = "אין פריטים בהזמנה\n"
        
        # הערות
        customer_note = order.get("customer_note", "")
        notes_text = f"הערות לקוח: {customer_note}\n" if customer_note else ""
        
        # בניית הפלט המפורמט
        output = f"""🛒 *הזמנה #{order_id}*
📊 *סטטוס:* {status_he}
📅 *תאריך:* {date_str}
💰 *סכום:* {total} {currency}

👤 *פרטי לקוח:*
   *שם:* {customer_name}
   *טלפון:* {customer_phone}
   *אימייל:* {customer_email}
   *כתובת:* {address}

📦 *פריטים:*
{items_text}
{notes_text}"""
        
        return output
        
    except Exception as e:
        logger.error(f"שגיאה בפירמוט הזמנה: {str(e)}")
        return f"שגיאה בהצגת הזמנה {order.get('id', '')}: {str(e)}"

def format_orders_list_for_display(orders: List[Dict[str, Any]]) -> str:
    """
    מפרמט רשימת הזמנות לתצוגה למשתמש
    
    Args:
        orders: רשימת הזמנות
        
    Returns:
        מחרוזת מפורמטת של רשימת ההזמנות
    """
    if not orders:
        return "לא נמצאו הזמנות"
    
    try:
        output = f"📋 *נמצאו {len(orders)} הזמנות:*\n\n"
        
        for order in orders:
            # מידע בסיסי
            order_id = order.get("id", "לא ידוע")
            status = order.get("status", "לא ידוע")
            status_he = ORDER_STATUSES.get(status, status)
            
            # תאריך
            date_created = order.get("date_created", "")
            if date_created:
                try:
                    date_obj = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%d/%m/%Y")
                except:
                    date_str = date_created
            else:
                date_str = "לא ידוע"
            
            # פרטי לקוח
            billing = order.get("billing", {})
            customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            if not customer_name:
                customer_name = "לא ידוע"
            
            # סכום
            total = order.get("total", "0")
            currency = order.get("currency", "₪")
            
            # מספר פריטים
            items_count = len(order.get("line_items", []))
            
            # הוספה לפלט
            output += f"🛒 *הזמנה #{order_id}*\n"
            output += f"👤 {customer_name}\n"
            output += f"📅 {date_str} | 📊 {status_he}\n"
            output += f"💰 {total} {currency} | 📦 {items_count} פריטים\n\n"
        
        return output
        
    except Exception as e:
        logger.error(f"שגיאה בפירמוט רשימת הזמנות: {str(e)}")
        return f"שגיאה בהצגת רשימת ההזמנות: {str(e)}"

def create_order_from_text(text: str) -> Dict[str, Any]:
    """
    יוצר הזמנה חדשה מטקסט
    
    Args:
        text: טקסט המתאר את ההזמנה
        
    Returns:
        מילון עם נתוני ההזמנה
    """
    # חילוץ נתוני הזמנה מהטקסט
    order_data = extract_order_data(text)
    
    # יצירת מבנה הזמנה
    order = {
        "status": "processing",  # ברירת מחדל
        "billing": {},
        "shipping": {},
        "line_items": [],
        "shipping_lines": [],
        "meta_data": []
    }
    
    # עדכון סטטוס אם צוין
    if "status" in order_data:
        status = map_status_to_english(order_data["status"])
        if status:
            order["status"] = status
    
    # עדכון פרטי לקוח
    if "customer" in order_data:
        customer = order_data["customer"]
        
        if "name" in customer:
            # פיצול שם מלא לשם פרטי ושם משפחה
            name_parts = customer["name"].split(" ", 1)
            order["billing"]["first_name"] = name_parts[0]
            order["billing"]["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
            
            # העתקה לשדות shipping
            order["shipping"] = order["shipping"] or {}
            order["shipping"]["first_name"] = order["billing"]["first_name"]
            order["shipping"]["last_name"] = order["billing"]["last_name"]
        
        if "email" in customer:
            order["billing"]["email"] = customer["email"]
        
        if "phone" in customer:
            order["billing"]["phone"] = customer["phone"]
        
        if "address" in customer:
            order["billing"]["address_1"] = customer["address"]
            
            # העתקה לשדות shipping
            order["shipping"]["address_1"] = customer["address"]
    
    # הוספת פריטים
    if "items" in order_data:
        for item in order_data["items"]:
            line_item = {
                "product_id": item.get("product_id", 0),
                "quantity": item.get("quantity", 1)
            }
            
            # אם אין מזהה מוצר אבל יש שם, נשתמש בשם
            if line_item["product_id"] == 0 and "name" in item:
                line_item["name"] = item["name"]
            
            # אם יש מחיר
            if "price" in item:
                line_item["price"] = item["price"]
            
            order["line_items"].append(line_item)
    
    # הוספת הערות
    if "notes" in order_data:
        order["customer_note"] = order_data["notes"]
    
    return order

def update_order_from_text(text: str, order_id: Optional[int] = None) -> Dict[str, Any]:
    """
    מעדכן הזמנה קיימת מטקסט
    
    Args:
        text: טקסט המתאר את העדכון
        order_id: מזהה ההזמנה לעדכון (אופציונלי)
        
    Returns:
        מילון עם נתוני העדכון
    """
    # חילוץ נתוני הזמנה מהטקסט
    order_data = extract_order_data(text)
    
    # יצירת מבנה עדכון
    update_data = {}
    
    # עדכון מזהה הזמנה אם צוין
    if order_id:
        update_data["id"] = order_id
    elif "order_id" in order_data:
        update_data["id"] = order_data["order_id"]
    
    # עדכון סטטוס אם צוין
    if "status" in order_data:
        status = map_status_to_english(order_data["status"])
        if status:
            update_data["status"] = status
    
    # עדכון פרטי לקוח
    if "customer" in order_data:
        customer = order_data["customer"]
        update_data["billing"] = {}
        
        if "name" in customer:
            # פיצול שם מלא לשם פרטי ושם משפחה
            name_parts = customer["name"].split(" ", 1)
            update_data["billing"]["first_name"] = name_parts[0]
            update_data["billing"]["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
            
            # העתקה לשדות shipping
            update_data["shipping"] = update_data.get("shipping", {})
            update_data["shipping"]["first_name"] = update_data["billing"]["first_name"]
            update_data["shipping"]["last_name"] = update_data["billing"]["last_name"]
        
        if "email" in customer:
            update_data["billing"]["email"] = customer["email"]
        
        if "phone" in customer:
            update_data["billing"]["phone"] = customer["phone"]
        
        if "address" in customer:
            update_data["billing"]["address_1"] = customer["address"]
            
            # העתקה לשדות shipping
            update_data["shipping"] = update_data.get("shipping", {})
            update_data["shipping"]["address_1"] = customer["address"]
    
    # הוספת הערות
    if "notes" in order_data:
        update_data["customer_note"] = order_data["notes"]
    
    return update_data

def get_orders_from_text(text: str) -> Dict[str, Any]:
    """
    מחלץ פרמטרים לחיפוש הזמנות מטקסט
    
    Args:
        text: טקסט המתאר את החיפוש
        
    Returns:
        מילון עם פרמטרים לחיפוש
    """
    # חילוץ נתוני חיפוש מהטקסט
    order_data = extract_order_data(text)
    
    # יצירת מבנה פרמטרים לחיפוש
    params = {}
    
    # חיפוש לפי סטטוס
    if "status" in order_data:
        status = map_status_to_english(order_data["status"])
        if status:
            params["status"] = status
    
    # חיפוש לפי לקוח
    if "customer" in order_data:
        customer = order_data["customer"]
        
        if "email" in customer:
            params["email"] = customer["email"]
        
        if "name" in customer:
            # WooCommerce לא תומך בחיפוש ישיר לפי שם, אבל נשמור את זה לסינון נוסף
            params["customer_name"] = customer["name"]
    
    # חיפוש לפי טווח תאריכים
    if "date_range" in order_data:
        date_range = order_data["date_range"]
        
        if "from" in date_range:
            params["after"] = date_range["from"]
        
        if "to" in date_range:
            params["before"] = date_range["to"]
    
    # חיפוש לפי מוצר
    if "items" in order_data and order_data["items"]:
        # WooCommerce לא תומך בחיפוש ישיר לפי מוצר, אבל נשמור את זה לסינון נוסף
        params["product"] = order_data["items"][0].get("name") or order_data["items"][0].get("product_id")
    
    # מיון
    if "sort" in order_data:
        sort = order_data["sort"]
        
        if sort == "newest" or sort == "latest":
            params["order"] = "desc"
            params["orderby"] = "date"
        elif sort == "oldest":
            params["order"] = "asc"
            params["orderby"] = "date"
        elif sort == "total_high":
            params["order"] = "desc"
            params["orderby"] = "total"
        elif sort == "total_low":
            params["order"] = "asc"
            params["orderby"] = "total"
    
    # הגבלת תוצאות
    if "limit" in order_data:
        params["per_page"] = min(order_data["limit"], 100)  # מקסימום 100 תוצאות
    else:
        params["per_page"] = 10  # ברירת מחדל
    
    return params

def get_order_from_text(text: str) -> Dict[str, Any]:
    """
    מחלץ מזהה הזמנה מטקסט
    
    Args:
        text: טקסט המתאר את ההזמנה
        
    Returns:
        מילון עם מזהה ההזמנה
    """
    # חילוץ נתוני הזמנה מהטקסט
    order_data = extract_order_data(text)
    
    # יצירת מבנה פרמטרים לחיפוש
    params = {}
    
    # חיפוש לפי מזהה
    if "order_id" in order_data:
        params["id"] = order_data["order_id"]
    
    return params 