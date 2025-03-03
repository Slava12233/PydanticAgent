"""
סקריפט בדיקה לפונקציות ניהול מוצרים
"""
import sys
import asyncio
import os
from dotenv import load_dotenv

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# עדכון הייבואים למיקום החדש
from src.tools.managers.product_manager import (
    create_product_from_text,
    format_product_for_display,
    update_product_from_text,
    search_products_by_text
)

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

async def test_create_product_from_text():
    """בדיקת פונקציית create_product_from_text"""
    test_cases = [
        # מקרה פשוט עם כל השדות
        (
            "שם: כיסא משרדי לבדיקה\n"
            "תיאור: כיסא משרדי איכותי עם משענת גב ארגונומית - נוצר לצורך בדיקה\n"
            "מחיר: 299.90\n"
            "קטגוריות: ריהוט, ריהוט משרדי\n"
            "מלאי: 10",
            "מוצר פשוט עם כל השדות"
        ),
        
        # מקרה עם שדות מינימליים
        (
            "אני רוצה ליצור מוצר חדש - שולחן עבודה לבדיקה במחיר 450 שקלים",
            "מוצר עם שדות מינימליים"
        ),
        
        # מקרה עם תיאור מפורט
        (
            "צור מוצר חדש בשם מחשב נייד לבדיקה עם תיאור: מחשב נייד חזק עם מעבד i7 ו-16GB RAM במחיר 3500 ש\"ח",
            "מוצר עם תיאור מפורט"
        )
    ]
    
    print("=== בדיקת יצירת מוצרים מטקסט ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return
    
    for text, description in test_cases:
        print(f"\nבדיקה: {description}")
        print(f"טקסט: \"{text}\"")
        
        try:
            success, message, created_product = await create_product_from_text(
                store_url=STORE_URL,
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                text=text
            )
            
            if success and created_product:
                print(f"✅ המוצר נוצר בהצלחה!")
                product_display = format_product_for_display(created_product)
                print(f"פרטי המוצר:\n{product_display}")
            else:
                print(f"❌ יצירת המוצר נכשלה: {message}")
        except Exception as e:
            print(f"❌ אירעה שגיאה: {str(e)}")

async def test_update_product_from_text():
    """בדיקת פונקציית update_product_from_text"""
    # יש צורך במוצר קיים לצורך העדכון
    product_id = os.getenv("TEST_PRODUCT_ID")
    
    if not product_id:
        print("❌ חסר מזהה מוצר לבדיקה. אנא הגדר את משתנה הסביבה TEST_PRODUCT_ID")
        return
    
    test_cases = [
        # עדכון מחיר
        (
            f"עדכן את המוצר {product_id} למחיר 399.90",
            "עדכון מחיר"
        ),
        
        # עדכון תיאור
        (
            f"שנה את התיאור של מוצר {product_id} ל: מוצר איכותי לבדיקה - עודכן",
            "עדכון תיאור"
        ),
        
        # עדכון מספר שדות
        (
            f"עדכן את המוצר {product_id} - שם: מוצר בדיקה מעודכן, מחיר: 499.90, מלאי: 20",
            "עדכון מספר שדות"
        )
    ]
    
    print("=== בדיקת עדכון מוצרים מטקסט ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return
    
    for text, description in test_cases:
        print(f"\nבדיקה: {description}")
        print(f"טקסט: \"{text}\"")
        
        try:
            success, message, updated_product = await update_product_from_text(
                store_url=STORE_URL,
                consumer_key=CONSUMER_KEY,
                consumer_secret=CONSUMER_SECRET,
                text=text
            )
            
            if success and updated_product:
                print(f"✅ המוצר עודכן בהצלחה!")
                product_display = format_product_for_display(updated_product)
                print(f"פרטי המוצר המעודכן:\n{product_display}")
            else:
                print(f"❌ עדכון המוצר נכשל: {message}")
        except Exception as e:
            print(f"❌ אירעה שגיאה: {str(e)}")

async def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות ניהול מוצרים")
    print("=" * 80)
    
    await test_create_product_from_text()
    await test_update_product_from_text()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות ניהול מוצרים הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 