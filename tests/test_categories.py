"""
סקריפט לבדיקת קטגוריות מוצרים בחנות WooCommerce
"""
import sys
import asyncio
import os
from dotenv import load_dotenv

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.woocommerce_api import WooCommerceAPI

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

async def test_get_categories():
    """בדיקת קבלת קטגוריות מהחנות"""
    print("=== בדיקת קטגוריות מוצרים בחנות ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # בדיקת חיבור לחנות
        connection_test = await api.test_connection()
        if not connection_test:
            print("❌ לא ניתן להתחבר לחנות WooCommerce. אנא בדוק את פרטי החיבור.")
            return
        
        print("✅ החיבור לחנות הצליח!")
        
        # קבלת קטגוריות
        status_code, categories = await api._make_request("GET", "products/categories")
        
        if status_code == 200:
            print(f"✅ נמצאו {len(categories)} קטגוריות:")
            for category in categories:
                print(f"  - ID: {category.get('id')}, שם: {category.get('name')}, כמות מוצרים: {category.get('count')}")
        else:
            print(f"❌ שגיאה בקבלת קטגוריות: {status_code}")
            print(f"פרטי השגיאה: {categories}")
    
    except Exception as e:
        print(f"❌ אירעה שגיאה: {str(e)}")

async def test_create_category():
    """בדיקת יצירת קטגוריה חדשה"""
    print("\n=== בדיקת יצירת קטגוריה חדשה ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # יצירת קטגוריה חדשה
        category_data = {
            "name": "ריהוט משרדי",
            "description": "מוצרי ריהוט למשרד - כיסאות, שולחנות ועוד"
        }
        
        status_code, response = await api._make_request("POST", "products/categories", data=category_data)
        
        if status_code in (200, 201):
            print(f"✅ הקטגוריה נוצרה בהצלחה!")
            print(f"  - ID: {response.get('id')}, שם: {response.get('name')}")
        else:
            print(f"❌ שגיאה ביצירת קטגוריה: {status_code}")
            print(f"פרטי השגיאה: {response}")
    
    except Exception as e:
        print(f"❌ אירעה שגיאה: {str(e)}")

async def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות קטגוריות מוצרים")
    print("=" * 80)
    
    await test_get_categories()
    await test_create_category()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות קטגוריות מוצרים הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 