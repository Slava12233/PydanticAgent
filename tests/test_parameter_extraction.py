"""
סקריפט בדיקה לפונקציות חילוץ פרמטרים מהודעות
"""
import sys
import os
from datetime import datetime

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.intent.product_intent import extract_product_data
from src.tools.intent.order_intent import extract_order_data, extract_date_range
from src.tools.intent.customer_intent import extract_customer_data

def test_extract_product_data():
    """בדיקת פונקציית extract_product_data"""
    test_cases = [
        # מקרה פשוט עם כל השדות
        (
            "שם: כיסא משרדי\n"
            "תיאור: כיסא משרדי איכותי עם משענת גב ארגונומית\n"
            "מחיר: 299.90\n"
            "קטגוריות: ריהוט, ריהוט משרדי, כיסאות\n"
            "תמונות: https://example.com/chair.jpg\n"
            "מלאי: 10\n"
            "סוג: simple",
            {
                "name": "כיסא משרדי",
                "description": "כיסא משרדי איכותי עם משענת גב ארגונומית",
                "regular_price": 299.90,
                "categories": ["ריהוט", "ריהוט משרדי", "כיסאות"],
                "images": ["https://example.com/chair.jpg"],
                "stock_quantity": 10,
                "type": "simple"
            }
        ),
        
        # מקרה עם שפה טבעית
        (
            "אני רוצה להוסיף מוצר חדש - שולחן עבודה במחיר 450 שקלים. "
            "יש לי 5 יחידות במלאי והוא שייך לקטגוריה של ריהוט משרדי.",
            {
                "name": "שולחן עבודה",
                "regular_price": 450,
                "stock_quantity": 5,
                "categories": ["ריהוט משרדי"]
            }
        ),
        
        # מקרה עם תיאור מפורט ומידע נוסף
        (
            "צור מוצר חדש בשם מחשב נייד עם תיאור: מחשב נייד חזק עם מעבד i7 ו-16GB RAM. "
            "המחיר הוא 3500 ש\"ח, יש לי 3 יחידות במלאי. "
            "הוא שייך לקטגוריות: אלקטרוניקה, מחשבים. "
            "יש לו גם תכונות נוספות: משקל 1.5 ק\"ג, מסך 15.6 אינץ'.",
            {
                "name": "מחשב נייד",
                "description": "מחשב נייד חזק עם מעבד i7 ו-16GB RAM",
                "regular_price": 3500,
                "stock_quantity": 3,
                "categories": ["אלקטרוניקה", "מחשבים"],
                "attributes": [
                    {"name": "משקל", "options": ["1.5 ק\"ג"]},
                    {"name": "מסך", "options": ["15.6 אינץ'"]}
                ]
            }
        )
    ]
    
    print("=== בדיקת חילוץ נתוני מוצר ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = extract_product_data(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {result}")
        
        # בדיקת השדות שאמורים להיות קיימים
        for field, expected_value in expected_fields.items():
            if field in result:
                if isinstance(expected_value, list) and isinstance(result[field], list):
                    # בדיקת רשימות (כמו קטגוריות או תמונות)
                    if field == "attributes":
                        # בדיקה מיוחדת לאטריביוטים שהם רשימת מילונים
                        expected_attrs = {attr["name"]: attr["options"] for attr in expected_value}
                        result_attrs = {attr["name"]: attr["options"] for attr in result[field]}
                        status = "✅" if expected_attrs == result_attrs else "❌"
                    else:
                        # בדיקה רגילה לרשימות
                        status = "✅" if set(expected_value) == set(result[field]) else "❌"
                else:
                    # בדיקת ערכים רגילים
                    status = "✅" if result[field] == expected_value else "❌"
                print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_extract_order_data():
    """בדיקת פונקציית extract_order_data"""
    test_cases = [
        # מקרה פשוט עם מזהה הזמנה
        (
            "תראה לי את ההזמנה מספר 123",
            {
                "id": "123"
            }
        ),
        
        # מקרה עם סטטוס הזמנה
        (
            "תעדכן את הסטטוס של הזמנה 456 ל'הושלם'",
            {
                "id": "456",
                "status": "completed"
            }
        ),
        
        # מקרה עם פרטי לקוח
        (
            "תראה לי את ההזמנות של הלקוח ישראל ישראלי עם אימייל israel@example.com",
            {
                "customer_name": "ישראל ישראלי",
                "customer_email": "israel@example.com"
            }
        ),
        
        # מקרה עם פרטי תשלום ומשלוח
        (
            "יש הזמנה חדשה ששולמה באמצעות כרטיס אשראי ונשלחה בדואר רשום. מספר המעקב הוא IL123456789",
            {
                "payment_method": "credit_card",
                "shipping_method": "registered_mail",
                "tracking_number": "IL123456789"
            }
        )
    ]
    
    print("=== בדיקת חילוץ נתוני הזמנה ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = extract_order_data(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {result}")
        
        # בדיקת השדות שאמורים להיות קיימים
        for field, expected_value in expected_fields.items():
            if field in result:
                status = "✅" if result[field] == expected_value else "❌"
                print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_extract_customer_data():
    """בדיקת פונקציית extract_customer_data"""
    test_cases = [
        # מקרה פשוט עם שם לקוח
        (
            "תוסיף לקוח חדש בשם ישראל ישראלי",
            {
                "first_name": "ישראל",
                "last_name": "ישראלי"
            }
        ),
        
        # מקרה עם פרטי קשר
        (
            "תעדכן את פרטי הלקוח: שם: ישראל ישראלי, אימייל: israel@example.com, טלפון: 0501234567",
            {
                "first_name": "ישראל",
                "last_name": "ישראלי",
                "email": "israel@example.com",
                "phone": "0501234567"
            }
        ),
        
        # מקרה עם כתובת
        (
            "הלקוח ישראל ישראלי עבר לכתובת חדשה: רחוב הרצל 1, תל אביב, מיקוד 6100000",
            {
                "first_name": "ישראל",
                "last_name": "ישראלי",
                "billing": {
                    "address_1": "רחוב הרצל 1",
                    "city": "תל אביב",
                    "postcode": "6100000"
                }
            }
        )
    ]
    
    print("=== בדיקת חילוץ נתוני לקוח ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = extract_customer_data(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {result}")
        
        # בדיקת השדות שאמורים להיות קיימים
        for field, expected_value in expected_fields.items():
            if field in result:
                if isinstance(expected_value, dict):
                    # בדיקת שדות מקוננים (כמו billing או shipping)
                    for sub_field, sub_value in expected_value.items():
                        if sub_field in result[field]:
                            status = "✅" if result[field][sub_field] == sub_value else "❌"
                            print(f"{status} שדה: {field}.{sub_field}, ערך: {result[field][sub_field]}")
                        else:
                            print(f"❌ שדה: {field}.{sub_field} לא נמצא בתוצאה")
                else:
                    # בדיקת ערכים רגילים
                    status = "✅" if result[field] == expected_value else "❌"
                    print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_extract_date_range():
    """בדיקת פונקציית extract_date_range"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    test_cases = [
        # מקרה עם תאריך מדויק
        (
            "תראה לי את ההזמנות מתאריך 01/01/2023",
            "2023-01-01",
            None
        ),
        
        # מקרה עם טווח תאריכים
        (
            "תראה לי את ההזמנות מתאריך 01/01/2023 עד 31/01/2023",
            "2023-01-01",
            "2023-01-31"
        ),
        
        # מקרה עם תיאור מילולי
        (
            "תראה לי את ההזמנות מהחודש האחרון",
            None,  # תלוי בלוגיקה הפנימית של הפונקציה
            None
        ),
        
        # מקרה עם תאריך בפורמט אחר
        (
            "תראה לי את ההזמנות מ-2023-01-01 עד 2023-01-31",
            "2023-01-01",
            "2023-01-31"
        )
    ]
    
    print("=== בדיקת חילוץ טווח תאריכים ===")
    for text, expected_from, expected_to in test_cases:
        print(f"טקסט: \"{text}\"")
        date_from, date_to = extract_date_range(text)
        
        # הדפסת התוצאה
        print(f"תאריך התחלה: {date_from}")
        print(f"תאריך סיום: {date_to}")
        
        # בדיקת התאריכים (אם צפויים להיות מדויקים)
        if expected_from and date_from:
            # המרת התאריך לפורמט YYYY-MM-DD לצורך השוואה
            date_from_str = date_from.strftime("%Y-%m-%d")
            from_status = "✅" if date_from_str == expected_from else "❌"
            print(f"{from_status} תאריך התחלה: {date_from_str}, ציפייה: {expected_from}")
        
        if expected_to and date_to:
            # המרת התאריך לפורמט YYYY-MM-DD לצורך השוואה
            date_to_str = date_to.strftime("%Y-%m-%d")
            to_status = "✅" if date_to_str == expected_to else "❌"
            print(f"{to_status} תאריך סיום: {date_to_str}, ציפייה: {expected_to}")
        print()

def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות חילוץ פרמטרים מהודעות")
    print("=" * 80)
    
    test_extract_product_data()
    test_extract_order_data()
    test_extract_customer_data()
    test_extract_date_range()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות חילוץ פרמטרים מהודעות הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    main() 