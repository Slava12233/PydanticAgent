"""
מודול לפורמוט והמרת מוצרים
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from src.core.task_identification.intents.product_intent import extract_product_data, identify_missing_required_fields

logger = logging.getLogger(__name__)

def format_product_for_display(product: Dict[str, Any]) -> str:
    """
    מפרמט מוצר לתצוגה למשתמש
    
    Args:
        product: נתוני המוצר
        
    Returns:
        מחרוזת מפורמטת של המוצר
    """
    if not product:
        return "לא נמצא מוצר"
    
    try:
        # מידע בסיסי
        product_id = product.get("id", "לא ידוע")
        name = product.get("name", "לא ידוע")
        status = product.get("status", "draft")
        status_he = {
            "publish": "פורסם",
            "draft": "טיוטה",
            "pending": "ממתין לאישור",
            "private": "פרטי",
            "trash": "נמחק"
        }.get(status, status)
        
        # מחירים
        regular_price = product.get("regular_price", "")
        sale_price = product.get("sale_price", "")
        price_html = product.get("price_html", "")
        
        # אם יש מחיר מבצע, נציג אותו
        price_display = ""
        currency = "₪"
        
        if sale_price:
            price_display = f"{sale_price} {currency} (במקום {regular_price} {currency})"
        elif regular_price:
            price_display = f"{regular_price} {currency}"
        else:
            price_display = "לא צוין מחיר"
        
        # מלאי
        stock_status = product.get("stock_status", "")
        stock_status_he = {
            "instock": "במלאי",
            "outofstock": "אזל מהמלאי",
            "onbackorder": "בהזמנה מראש"
        }.get(stock_status, stock_status)
        
        stock_quantity = product.get("stock_quantity", "")
        stock_display = f"{stock_status_he}"
        if stock_quantity:
            stock_display += f" ({stock_quantity} יחידות)"
        
        # קטגוריות
        categories = product.get("categories", [])
        categories_display = ", ".join([cat.get("name", "") for cat in categories]) if categories else "ללא קטגוריה"
        
        # תיאור
        short_description = product.get("short_description", "").strip()
        description = product.get("description", "").strip()
        
        # תמונות
        images = product.get("images", [])
        image_url = images[0].get("src", "") if images else ""
        
        # בניית הפלט המפורמט
        output = f"""🛍️ *{name}* (#{product_id})
💰 *מחיר:* {price_display}
📦 *מלאי:* {stock_display}
🏷️ *קטגוריות:* {categories_display}
📊 *סטטוס:* {status_he}
"""
        
        # הוספת תיאור קצר אם יש
        if short_description:
            output += f"\n📝 *תיאור קצר:*\n{short_description}\n"
        
        # הוספת תיאור מלא אם יש ואין תיאור קצר
        elif description:
            # קיצור התיאור אם הוא ארוך מדי
            if len(description) > 200:
                description = description[:197] + "..."
            output += f"\n📝 *תיאור:*\n{description}\n"
        
        # הוספת קישור לתמונה אם יש
        if image_url:
            output += f"\n🖼️ [תמונת המוצר]({image_url})\n"
        
        return output
        
    except Exception as e:
        logger.error(f"שגיאה בפירמוט מוצר: {str(e)}")
        return f"שגיאה בהצגת מוצר {product.get('id', '')}: {str(e)}"

def format_products_list_for_display(products: List[Dict[str, Any]]) -> str:
    """
    מפרמט רשימת מוצרים לתצוגה למשתמש
    
    Args:
        products: רשימת מוצרים
        
    Returns:
        מחרוזת מפורמטת של רשימת המוצרים
    """
    if not products:
        return "לא נמצאו מוצרים"
    
    try:
        output = f"📋 *נמצאו {len(products)} מוצרים:*\n\n"
        
        for product in products:
            # מידע בסיסי
            product_id = product.get("id", "לא ידוע")
            name = product.get("name", "לא ידוע")
            
            # מחירים
            regular_price = product.get("regular_price", "")
            sale_price = product.get("sale_price", "")
            
            # הצגת מחיר
            price_display = ""
            currency = "₪"
            
            if sale_price:
                price_display = f"{sale_price} {currency}"
            elif regular_price:
                price_display = f"{regular_price} {currency}"
            else:
                price_display = "לא צוין מחיר"
            
            # מלאי
            stock_status = product.get("stock_status", "")
            stock_status_he = {
                "instock": "במלאי",
                "outofstock": "אזל מהמלאי",
                "onbackorder": "בהזמנה מראש"
            }.get(stock_status, stock_status)
            
            # הוספה לפלט
            output += f"🛍️ *{name}* (#{product_id})\n"
            output += f"💰 {price_display} | 📦 {stock_status_he}\n\n"
        
        return output
        
    except Exception as e:
        logger.error(f"שגיאה בפירמוט רשימת מוצרים: {str(e)}")
        return f"שגיאה בהצגת רשימת המוצרים: {str(e)}"

def create_product_from_text(text: str) -> Dict[str, Any]:
    """
    יוצר מוצר חדש מטקסט
    
    Args:
        text: טקסט המתאר את המוצר
        
    Returns:
        מילון עם נתוני המוצר
    """
    # חילוץ נתוני מוצר מהטקסט
    product_data = extract_product_data(text)
    
    # בדיקה שיש את כל השדות הנדרשים
    missing_fields = identify_missing_required_fields(product_data)
    if missing_fields:
        logger.warning(f"חסרים שדות חובה: {', '.join(missing_fields)}")
    
    return product_data

def prepare_product_data_for_api(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    הכנת נתוני המוצר לשליחה ל-API
    
    Args:
        product_data: נתוני המוצר המקוריים
        
    Returns:
        נתוני המוצר מוכנים לשליחה ל-API
    """
    api_data = {}
    
    # העתקת שדות בסיסיים
    basic_fields = ["name", "description", "short_description", "sku", "regular_price", 
                    "sale_price", "status", "featured", "catalog_visibility", 
                    "virtual", "downloadable", "tax_status", "tax_class"]
    
    for field in basic_fields:
        if field in product_data:
            api_data[field] = product_data[field]
    
    # טיפול במחיר אם קיים
    if "price" in product_data and "regular_price" not in product_data:
        api_data["regular_price"] = str(product_data["price"])
    
    # המרת מחירים למחרוזות (נדרש ע"י ה-API)
    price_fields = ["regular_price", "sale_price"]
    for field in price_fields:
        if field in api_data:
            api_data[field] = str(api_data[field])
    
    # טיפול בסוג המוצר
    if "type" in product_data:
        api_data["type"] = product_data["type"]
    else:
        # ברירת מחדל: מוצר פשוט
        api_data["type"] = "simple"
    
    # טיפול בניהול מלאי
    if "stock_quantity" in product_data:
        api_data["manage_stock"] = True
        api_data["stock_quantity"] = product_data["stock_quantity"]
        
        # קביעת סטטוס מלאי אוטומטית
        if product_data["stock_quantity"] > 0:
            api_data["stock_status"] = "instock"
        else:
            api_data["stock_status"] = "outofstock"
    elif "stock_status" in product_data:
        api_data["stock_status"] = product_data["stock_status"]
    
    # טיפול בקטגוריות - נשתמש בשמות בלבד ונטפל בהם בצורה נכונה בפונקציית create_product
    if "categories" in product_data:
        categories = product_data["categories"]
        api_categories = []
        
        # בדיקה אם יש קטגוריות קיימות
        if isinstance(categories, list):
            # אם יש רשימת קטגוריות, נשתמש בהן
            for category_name in categories:
                api_categories.append({"name": category_name})
        elif isinstance(categories, str):
            # אם זו מחרוזת, נפצל אותה לרשימה
            category_names = [cat.strip() for cat in categories.split(",") if cat.strip()]
            for category_name in category_names:
                api_categories.append({"name": category_name})
        
        # שמירת הקטגוריות המוכנות
        if api_categories:
            api_data["categories"] = api_categories
    
    return api_data

def get_products_from_text(text: str) -> Dict[str, Any]:
    """
    מחלץ פרמטרים לחיפוש מוצרים מטקסט
    
    Args:
        text: טקסט המתאר את החיפוש
        
    Returns:
        מילון עם פרמטרים לחיפוש
    """
    # חילוץ נתוני חיפוש מהטקסט
    product_data = extract_product_data(text)
    
    # יצירת מבנה פרמטרים לחיפוש
    params = {}
    
    # חיפוש לפי שם
    if "name" in product_data:
        params["search"] = product_data["name"]
    
    # חיפוש לפי קטגוריה
    if "categories" in product_data:
        categories = product_data["categories"]
        if isinstance(categories, list) and categories:
            params["category"] = categories[0]
        elif isinstance(categories, str):
            params["category"] = categories
    
    # חיפוש לפי סטטוס
    if "status" in product_data:
        params["status"] = product_data["status"]
    
    # חיפוש לפי מלאי
    if "stock_status" in product_data:
        params["stock_status"] = product_data["stock_status"]
    
    # חיפוש לפי טווח מחירים
    if "min_price" in product_data:
        params["min_price"] = product_data["min_price"]
    if "max_price" in product_data:
        params["max_price"] = product_data["max_price"]
    
    # הגבלת תוצאות
    if "limit" in product_data:
        params["per_page"] = min(product_data["limit"], 100)  # מקסימום 100 תוצאות
    else:
        params["per_page"] = 10  # ברירת מחדל
    
    return params 