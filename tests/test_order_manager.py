"""
סקריפט בדיקה לפונקציות ניהול הזמנות
"""
import sys
import os
import json
from datetime import datetime

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.managers.order_manager import (
    create_order_from_text,
    update_order_from_text,
    get_orders_from_text,
    get_order_from_text
)

def test_create_order_from_text():
    """בדיקת פונקציית create_order_from_text"""
    test_cases = [
        # מקרה פשוט עם פרטי לקוח בסיסיים
        (
            "צור הזמנה חדשה עבור ישראל ישראלי עם המוצרים: כיסא משרדי (2 יחידות), שולחן עבודה (1 יחידה)",
            {
                "customer": {
                    "first_name": "ישראל",
                    "last_name": "ישראלי"
                },
                "line_items": [
                    {"product_name": "כיסא משרדי", "quantity": 2},
                    {"product_name": "שולחן עבודה", "quantity": 1}
                ]
            }
        ),
        
        # מקרה עם פרטי משלוח ותשלום
        (
            "צור הזמנה חדשה עבור דוד לוי, אימייל: david@example.com, טלפון: 0501234567. "
            "כתובת למשלוח: רחוב הרצל 10, תל אביב. "
            "מוצרים: מחשב נייד (1), עכבר אלחוטי (2). "
            "אמצעי תשלום: כרטיס אשראי.",
            {
                "customer": {
                    "first_name": "דוד",
                    "last_name": "לוי",
                    "email": "david@example.com",
                    "phone": "0501234567"
                },
                "shipping": {
                    "address_1": "רחוב הרצל 10",
                    "city": "תל אביב"
                },
                "line_items": [
                    {"product_name": "מחשב נייד", "quantity": 1},
                    {"product_name": "עכבר אלחוטי", "quantity": 2}
                ],
                "payment_method": "כרטיס אשראי"
            }
        )
    ]
    
    print("=== בדיקת יצירת הזמנה מטקסט ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = create_order_from_text(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # בדיקת השדות שאמורים להיות קיימים
        for field, expected_value in expected_fields.items():
            if field in result:
                if isinstance(expected_value, dict):
                    # בדיקת שדות מקוננים (כמו customer או shipping)
                    for sub_field, sub_value in expected_value.items():
                        if sub_field in result[field]:
                            status = "✅" if result[field][sub_field] == sub_value else "❌"
                            print(f"{status} שדה: {field}.{sub_field}, ערך: {result[field][sub_field]}")
                        else:
                            print(f"❌ שדה: {field}.{sub_field} לא נמצא בתוצאה")
                elif isinstance(expected_value, list):
                    # בדיקת רשימות (כמו line_items)
                    if len(result[field]) == len(expected_value):
                        status = "✅"
                        for i, item in enumerate(expected_value):
                            for item_field, item_value in item.items():
                                if item_field not in result[field][i] or result[field][i][item_field] != item_value:
                                    status = "❌"
                                    break
                    else:
                        status = "❌"
                    print(f"{status} שדה: {field}, אורך: {len(result[field])}")
                else:
                    # בדיקת ערכים רגילים
                    status = "✅" if result[field] == expected_value else "❌"
                    print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_update_order_from_text():
    """בדיקת פונקציית update_order_from_text"""
    test_cases = [
        # עדכון סטטוס הזמנה
        (
            "עדכן את הסטטוס של הזמנה מספר 123 ל'הושלם'",
            {
                "id": 123,
                "status": "completed"
            }
        ),
        
        # עדכון פרטי משלוח
        (
            "עדכן את פרטי המשלוח של הזמנה 456. "
            "כתובת חדשה: רחוב אלנבי 50, תל אביב. "
            "שיטת משלוח: שליח עד הבית.",
            {
                "id": 456,
                "shipping": {
                    "address_1": "רחוב אלנבי 50",
                    "city": "תל אביב"
                },
                "shipping_lines": [
                    {
                        "method_title": "שליח עד הבית"
                    }
                ]
            }
        )
    ]
    
    print("=== בדיקת עדכון הזמנה מטקסט ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = update_order_from_text(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # בדיקת השדות שאמורים להיות קיימים
        for field, expected_value in expected_fields.items():
            if field in result:
                if isinstance(expected_value, dict):
                    # בדיקת שדות מקוננים
                    for sub_field, sub_value in expected_value.items():
                        if sub_field in result[field]:
                            status = "✅" if result[field][sub_field] == sub_value else "❌"
                            print(f"{status} שדה: {field}.{sub_field}, ערך: {result[field][sub_field]}")
                        else:
                            print(f"❌ שדה: {field}.{sub_field} לא נמצא בתוצאה")
                elif isinstance(expected_value, list):
                    # בדיקת רשימות
                    if len(result[field]) == len(expected_value):
                        status = "✅"
                        for i, item in enumerate(expected_value):
                            for item_field, item_value in item.items():
                                if item_field not in result[field][i] or result[field][i][item_field] != item_value:
                                    status = "❌"
                                    break
                    else:
                        status = "❌"
                    print(f"{status} שדה: {field}, אורך: {len(result[field])}")
                else:
                    # בדיקת ערכים רגילים
                    status = "✅" if result[field] == expected_value else "❌"
                    print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_get_orders_from_text():
    """בדיקת פונקציית get_orders_from_text"""
    test_cases = [
        # קבלת כל ההזמנות
        (
            "הצג את כל ההזמנות",
            {}
        ),
        
        # קבלת הזמנות לפי סטטוס
        (
            "הצג את כל ההזמנות בסטטוס 'בטיפול'",
            {
                "status": "processing"
            }
        ),
        
        # קבלת הזמנות לפי תאריך
        (
            "הצג את ההזמנות מהחודש האחרון",
            {
                "after": None  # תלוי בלוגיקה הפנימית של הפונקציה
            }
        ),
        
        # קבלת הזמנות לפי לקוח
        (
            "הצג את ההזמנות של הלקוח ישראל ישראלי",
            {
                "customer": "ישראל ישראלי"
            }
        )
    ]
    
    print("=== בדיקת קבלת הזמנות מטקסט ===")
    for text, expected_params in test_cases:
        print(f"טקסט: \"{text}\"")
        result = get_orders_from_text(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # בדיקת הפרמטרים שאמורים להיות קיימים
        for param, expected_value in expected_params.items():
            if param in result:
                if expected_value is None:
                    # אם הערך הצפוי הוא None, נבדוק רק שהפרמטר קיים
                    print(f"✅ פרמטר: {param} קיים בתוצאה")
                else:
                    status = "✅" if result[param] == expected_value else "❌"
                    print(f"{status} פרמטר: {param}, ערך: {result[param]}")
            else:
                if expected_value is not None:
                    print(f"❌ פרמטר: {param} לא נמצא בתוצאה")
        print()

def test_get_order_from_text():
    """בדיקת פונקציית get_order_from_text"""
    test_cases = [
        # קבלת הזמנה לפי מזהה
        (
            "הצג את הזמנה מספר 123",
            {
                "id": 123
            }
        ),
        
        # קבלת הזמנה לפי מזהה עם תיאור נוסף
        (
            "אני צריך לראות את פרטי ההזמנה 456 כדי לבדוק את הכתובת למשלוח",
            {
                "id": 456
            }
        )
    ]
    
    print("=== בדיקת קבלת הזמנה בודדת מטקסט ===")
    for text, expected_params in test_cases:
        print(f"טקסט: \"{text}\"")
        result = get_order_from_text(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # בדיקת הפרמטרים שאמורים להיות קיימים
        for param, expected_value in expected_params.items():
            if param in result:
                status = "✅" if result[param] == expected_value else "❌"
                print(f"{status} פרמטר: {param}, ערך: {result[param]}")
            else:
                print(f"❌ פרמטר: {param} לא נמצא בתוצאה")
        print()

def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות ניהול הזמנות")
    print("=" * 80)
    
    test_create_order_from_text()
    test_update_order_from_text()
    test_get_orders_from_text()
    test_get_order_from_text()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות ניהול הזמנות הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    main() 