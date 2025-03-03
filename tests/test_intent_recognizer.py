"""
סקריפט בדיקה לפונקציות זיהוי כוונות ספציפיות
"""
import sys
import os

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.intent.intent_recognizer import (
    identify_specific_intent,
    get_intent_description,
    extract_parameters_by_intent,
    calculate_intent_score,
    SPECIFIC_INTENTS
)

def test_identify_specific_intent():
    """בדיקת פונקציית identify_specific_intent"""
    test_cases = [
        # בדיקות יצירת מוצר
        ("אני רוצה ליצור מוצר חדש", "product_management", "create_product"),
        ("תוסיף מוצר חדש בשם כיסא משרדי", "product_management", "create_product"),
        
        # בדיקות עדכון מוצר
        ("תעדכן את המוצר מספר 123", "product_management", "update_product"),
        ("שנה את המחיר של המוצר כיסא משרדי ל-299", "product_management", "update_product"),
        
        # בדיקות ניהול הזמנות
        ("תראה לי את ההזמנות האחרונות", "order_management", "get_orders"),
        ("מה הסטטוס של הזמנה מספר 456", "order_management", "get_order"),
        ("תעדכן את הסטטוס של הזמנה 456 ל'הושלם'", "order_management", "update_order_status"),
        
        # בדיקות ניהול לקוחות
        ("תראה לי את רשימת הלקוחות", "customer_management", "get_customers"),
        ("מי הלקוח עם מזהה 789", "customer_management", "get_customer"),
        ("תוסיף לקוח חדש בשם ישראל ישראלי", "customer_management", "create_customer"),
        
        # בדיקות כלליות
        ("מה שלומך", "general", "general"),
        ("תודה רבה", "general", "general")
    ]
    
    print("=== בדיקת זיהוי כוונות ספציפיות ===")
    for text, expected_task_type, expected_intent_type in test_cases:
        task_type, intent_type, score = identify_specific_intent(text)
        
        task_status = "✅" if task_type == expected_task_type else "❌"
        intent_status = "✅" if intent_type == expected_intent_type else "❌"
        
        print(f"טקסט: \"{text}\"")
        print(f"{task_status} סוג משימה: {task_type}, ציפייה: {expected_task_type}")
        print(f"{intent_status} סוג כוונה: {intent_type}, ציפייה: {expected_intent_type}")
        print(f"ציון: {score:.2f}")
        print()

def test_extract_parameters_by_intent():
    """בדיקת פונקציית extract_parameters_by_intent"""
    test_cases = [
        # בדיקת חילוץ פרמטרים ליצירת מוצר
        (
            "תוסיף מוצר חדש בשם כיסא משרדי במחיר 299.90",
            "product_management",
            "create_product",
            ["product_data"]
        ),
        
        # בדיקת חילוץ פרמטרים לעדכון מוצר
        (
            "תעדכן את המוצר מספר 123 למחיר 399.90",
            "product_management",
            "update_product",
            ["product_id", "product_data"]
        ),
        
        # בדיקת חילוץ פרמטרים לקבלת הזמנה
        (
            "תראה לי את ההזמנה מספר 456",
            "order_management",
            "get_order",
            ["order_id"]
        ),
        
        # בדיקת חילוץ פרמטרים לעדכון סטטוס הזמנה
        (
            "תעדכן את הסטטוס של הזמנה 456 ל'הושלם'",
            "order_management",
            "update_order_status",
            ["order_id", "status"]
        ),
        
        # בדיקת חילוץ פרמטרים לקבלת לקוח
        (
            "תראה לי את הלקוח עם מזהה 789",
            "customer_management",
            "get_customer",
            ["customer_id"]
        )
    ]
    
    print("=== בדיקת חילוץ פרמטרים לפי כוונה ===")
    for text, task_type, intent_type, expected_params in test_cases:
        params = extract_parameters_by_intent(text, task_type, intent_type)
        
        print(f"טקסט: \"{text}\"")
        print(f"סוג משימה: {task_type}, סוג כוונה: {intent_type}")
        print(f"פרמטרים שחולצו: {list(params.keys())}")
        
        # בדיקה שכל הפרמטרים הצפויים קיימים
        all_params_found = all(param in params for param in expected_params)
        status = "✅" if all_params_found else "❌"
        print(f"{status} נמצאו כל הפרמטרים הצפויים: {expected_params}")
        
        # הדפסת הפרמטרים שחולצו
        for param, value in params.items():
            if param not in ["intent_type", "intent_score", "intent_description"]:
                print(f"  - {param}: {value}")
        print()

def test_get_intent_description():
    """בדיקת פונקציית get_intent_description"""
    test_cases = [
        ("product_management", "create_product"),
        ("product_management", "update_product"),
        ("order_management", "get_orders"),
        ("order_management", "get_order"),
        ("customer_management", "get_customers"),
        ("general", "general")
    ]
    
    print("=== בדיקת קבלת תיאור כוונה ===")
    for task_type, intent_type in test_cases:
        description = get_intent_description(task_type, intent_type)
        
        status = "✅" if description else "❌"
        print(f"{status} סוג משימה: {task_type}, סוג כוונה: {intent_type}")
        print(f"  תיאור: {description}")
    print()

def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות זיהוי כוונות ספציפיות")
    print("=" * 80)
    
    test_identify_specific_intent()
    test_extract_parameters_by_intent()
    test_get_intent_description()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות זיהוי כוונות ספציפיות הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    main() 