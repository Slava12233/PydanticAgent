"""
סקריפט בדיקה לפונקציות ניהול לקוחות
"""
import sys
import os
import json
from datetime import datetime

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.managers.customer_manager import (
    create_customer_from_text,
    update_customer_from_text,
    get_customers_from_text,
    get_customer_from_text
)

def test_create_customer_from_text():
    """בדיקת פונקציית create_customer_from_text"""
    test_cases = [
        # מקרה פשוט עם שם לקוח
        (
            "צור לקוח חדש בשם ישראל ישראלי",
            {
                "first_name": "ישראל",
                "last_name": "ישראלי"
            }
        ),
        
        # מקרה עם פרטי קשר מלאים
        (
            "צור לקוח חדש: שם: דוד לוי, אימייל: david@example.com, טלפון: 0501234567, "
            "כתובת: רחוב הרצל 10, תל אביב, מיקוד: 6100000",
            {
                "first_name": "דוד",
                "last_name": "לוי",
                "email": "david@example.com",
                "phone": "0501234567",
                "billing": {
                    "address_1": "רחוב הרצל 10",
                    "city": "תל אביב",
                    "postcode": "6100000"
                }
            }
        )
    ]
    
    print("=== בדיקת יצירת לקוח מטקסט ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = create_customer_from_text(text)
        
        # הדפסת התוצאה המלאה
        print(f"תוצאה מלאה: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
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

def test_update_customer_from_text():
    """בדיקת פונקציית update_customer_from_text"""
    test_cases = [
        # עדכון אימייל
        (
            "עדכן את האימייל של הלקוח ישראל ישראלי ל-israel.new@example.com",
            {
                "email": "israel.new@example.com",
                "first_name": "ישראל",
                "last_name": "ישראלי"
            }
        ),
        
        # עדכון כתובת
        (
            "עדכן את הכתובת של הלקוח דוד לוי. "
            "כתובת חדשה: רחוב אלנבי 50, תל אביב, מיקוד: 6100001",
            {
                "first_name": "דוד",
                "last_name": "לוי",
                "billing": {
                    "address_1": "רחוב אלנבי 50",
                    "city": "תל אביב",
                    "postcode": "6100001"
                }
            }
        )
    ]
    
    print("=== בדיקת עדכון לקוח מטקסט ===")
    for text, expected_fields in test_cases:
        print(f"טקסט: \"{text}\"")
        result = update_customer_from_text(text)
        
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
                else:
                    # בדיקת ערכים רגילים
                    status = "✅" if result[field] == expected_value else "❌"
                    print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        print()

def test_get_customers_from_text():
    """בדיקת פונקציית get_customers_from_text"""
    test_cases = [
        # קבלת כל הלקוחות
        (
            "הצג את כל הלקוחות",
            {}
        ),
        
        # קבלת לקוחות לפי אימייל
        (
            "הצג את הלקוח עם האימייל israel@example.com",
            {
                "email": "israel@example.com"
            }
        ),
        
        # קבלת לקוחות לפי שם
        (
            "הצג את הלקוח ישראל ישראלי",
            {
                "name": "ישראל ישראלי"
            }
        )
    ]
    
    print("=== בדיקת קבלת לקוחות מטקסט ===")
    for text, expected_params in test_cases:
        print(f"טקסט: \"{text}\"")
        result = get_customers_from_text(text)
        
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

def test_get_customer_from_text():
    """בדיקת פונקציית get_customer_from_text"""
    test_cases = [
        # קבלת לקוח לפי מזהה
        (
            "הצג את הלקוח מספר 123",
            {
                "id": 123
            }
        ),
        
        # קבלת לקוח לפי אימייל
        (
            "אני צריך לראות את פרטי הלקוח עם האימייל israel@example.com",
            {
                "email": "israel@example.com"
            }
        )
    ]
    
    print("=== בדיקת קבלת לקוח בודד מטקסט ===")
    for text, expected_params in test_cases:
        print(f"טקסט: \"{text}\"")
        result = get_customer_from_text(text)
        
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
    print("🧪 בדיקות ניהול לקוחות")
    print("=" * 80)
    
    test_create_customer_from_text()
    test_update_customer_from_text()
    test_get_customers_from_text()
    test_get_customer_from_text()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות ניהול לקוחות הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    main() 