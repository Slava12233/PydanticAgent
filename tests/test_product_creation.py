"""
סקריפט בדיקה לפונקציות זיהוי כוונות יצירת מוצר
"""
import sys
import os

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# עדכון הייבואים למיקום החדש
from src.tools.intent.product_intent import (
    is_product_creation_intent,
    extract_product_data,
    identify_missing_required_fields,
    generate_product_creation_questions,
    get_product_type_suggestions
)

def test_product_creation_intent():
    """בדיקת פונקציית is_product_creation_intent"""
    test_cases = [
        # ביטויים ישירים - צריכים להחזיר True
        ("אני רוצה ליצור מוצר חדש", True),
        ("יש לי מוצר חדש למכירה", True),
        ("איך אני מוסיף מוצר לחנות", True),
        ("צור מוצר חדש בשם כיסא", True),
        ("הוסף מוצר לחנות", True),
        
        # ביטויים עקיפים - צריכים להחזיר True
        ("קיבלתי סחורה חדשה שאני רוצה להוסיף", True),
        ("יש לי פריט חדש שהגיע למלאי", True),
        ("הגיע מלאי חדש שצריך להוסיף לחנות", True),
        
        # מקרים נוספים - צריכים להחזיר True
        ("אני צריך להוסיף מוצר חדש לחנות שלי", True),
        ("תעזור לי ליצור מוצר חדש", True),
        ("איך יוצרים מוצר דיגיטלי", True),
        ("רוצה להוסיף פריט חדש למלאי", True),
        
        # ביטויים לא קשורים - צריכים להחזיר False
        ("כמה מוצרים יש בחנות", False),
        ("מה המכירות החודש", False),
        ("תראה לי את ההזמנות האחרונות", False),
        ("מה מצב המלאי", False),
        ("תעדכן את המחיר של המוצר", False),
        
        # מקרים נוספים - צריכים להחזיר False
        ("מתי ההזמנה שלי תגיע", False),
        ("איך אני מבטל הזמנה", False),
        ("תראה לי את הסטטיסטיקות של החנות", False),
        ("איך אני מעדכן את פרטי החנות", False)
    ]
    
    print("=== בדיקת זיהוי כוונות יצירת מוצר ===")
    for text, expected in test_cases:
        result = is_product_creation_intent(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} ביטוי: \"{text}\" - התוצאה: {result}, הציפייה: {expected}")
    print()

def test_extract_product_data():
    """בדיקת פונקציית extract_product_data"""
    test_cases = [
        # מקרה פשוט עם כל השדות
        (
            "שם: כיסא משרדי\n"
            "תיאור: כיסא משרדי איכותי עם משענת גב ארגונומית\n"
            "מחיר: 299.90\n"
            "קטגוריות: ריהוט, ריהוט משרדי, כיסאות\n"
            "תמונות: https://example.com/chair.jpg",
            {
                "name": "כיסא משרדי",
                "description": "כיסא משרדי איכותי עם משענת גב ארגונומית",
                "regular_price": 299.90,
                "categories": ["ריהוט", "ריהוט משרדי", "כיסאות"],
                "images": ["https://example.com/chair.jpg"]
            }
        ),
        
        # מקרה עם חלק מהשדות
        (
            "אני רוצה להוסיף מוצר חדש - שולחן עבודה במחיר 450 שקלים",
            {
                "name": "שולחן עבודה",
                "regular_price": 450
            }
        ),
        
        # מקרים נוספים
        (
            "צור מוצר חדש בשם מחשב נייד עם תיאור: מחשב נייד חזק עם מעבד i7 ו-16GB RAM במחיר 3500 ש\"ח",
            {
                "name": "מחשב נייד",
                "description": "מחשב נייד חזק עם מעבד i7 ו-16GB RAM",
                "regular_price": 3500
            }
        ),
        (
            "אני רוצה להוסיף טלפון חכם חדש לחנות. המחיר הוא 1200 שקלים והוא שייך לקטגוריות: אלקטרוניקה, טלפונים",
            {
                "name": "טלפון חכם",
                "regular_price": 1200,
                "categories": ["אלקטרוניקה", "טלפונים"]
            }
        ),
        (
            "תוסיף בבקשה מוצר חדש - חולצת כותנה, מחיר: 89.90, קטגוריה: ביגוד, צבעים זמינים: שחור, לבן, אדום",
            {
                "name": "חולצת כותנה",
                "regular_price": 89.90,
                "categories": ["ביגוד"]
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
                    status = "✅" if set(expected_value) == set(result[field]) else "❌"
                else:
                    status = "✅" if result[field] == expected_value else "❌"
                print(f"{status} שדה: {field}, ערך: {result[field]}")
            else:
                print(f"❌ שדה: {field} לא נמצא בתוצאה")
        
        # בדיקת שדות חסרים
        missing_fields = identify_missing_required_fields(result)
        print(f"שדות חובה חסרים: {', '.join(missing_fields) if missing_fields else 'אין'}")
        print()

def test_generate_product_creation_questions():
    """בדיקת פונקציית generate_product_creation_questions"""
    test_cases = [
        (["name"], "שאלות לשם המוצר"),
        (["regular_price"], "שאלות למחיר המוצר"),
        (["name", "regular_price"], "שאלות לשם ומחיר המוצר"),
        (["description"], "שאלות לתיאור המוצר"),
        (["categories"], "שאלות לקטגוריות המוצר"),
        (["images"], "שאלות לתמונות המוצר")
    ]
    
    print("=== בדיקת יצירת שאלות למידע חסר ===")
    for missing_fields, description in test_cases:
        print(f"\nבדיקה: {description}")
        questions = generate_product_creation_questions(missing_fields)
        if questions:
            print(f"✅ נוצרו {len(questions)} שאלות:")
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")
        else:
            print("❌ לא נוצרו שאלות")
    print()

def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות זיהוי כוונות יצירת מוצר וחילוץ נתונים")
    print("=" * 80)
    
    test_product_creation_intent()
    test_extract_product_data()
    test_generate_product_creation_questions()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות זיהוי כוונות יצירת מוצר וחילוץ נתונים הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    main() 