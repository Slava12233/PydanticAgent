"""
סקריפט בדיקה לאינטגרציה עם WooCommerce API
"""
import sys
import asyncio
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.woocommerce_api import WooCommerceAPI
from src.tools.managers.product_manager import ProductManager

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

async def test_api_connection():
    """בדיקת חיבור ל-API של WooCommerce"""
    print("\n=== בדיקת חיבור ל-API של WooCommerce ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # בדיקת חיבור לחנות
        start_time = time.time()
        connection_test = await api.test_connection()
        end_time = time.time()
        connection_time_ms = (end_time - start_time) * 1000
        
        if connection_test:
            print(f"✅ החיבור לחנות הצליח!")
            print(f"זמן תגובה: {connection_time_ms:.2f} מילישניות")
            return True
        else:
            print(f"❌ החיבור לחנות נכשל.")
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בבדיקת החיבור: {str(e)}")
        return False

async def test_get_products():
    """בדיקת קבלת מוצרים מהחנות"""
    print("\n=== בדיקת קבלת מוצרים מהחנות ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות.")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # קבלת מוצרים
        start_time = time.time()
        status_code, products = await api._make_request("GET", "products", params={"per_page": 5})
        end_time = time.time()
        request_time_ms = (end_time - start_time) * 1000
        
        if status_code == 200:
            print(f"✅ קבלת מוצרים הצליחה!")
            print(f"זמן תגובה: {request_time_ms:.2f} מילישניות")
            print(f"מספר מוצרים שהתקבלו: {len(products)}")
            
            if products:
                print("\nדוגמה למוצר ראשון:")
                product = products[0]
                print(f"  - ID: {product.get('id')}")
                print(f"  - שם: {product.get('name')}")
                print(f"  - מחיר: {product.get('price')}")
                print(f"  - סטטוס: {product.get('status')}")
            
            return True
        else:
            print(f"❌ קבלת מוצרים נכשלה. קוד תגובה: {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בקבלת מוצרים: {str(e)}")
        return False

async def test_create_product():
    """בדיקת יצירת מוצר חדש"""
    print("\n=== בדיקת יצירת מוצר חדש ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות.")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        # יצירת נתוני מוצר לבדיקה
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product_data = {
            "name": f"מוצר בדיקה - {timestamp}",
            "description": "מוצר שנוצר לצורך בדיקת אינטגרציה עם WooCommerce API",
            "regular_price": "99.90",
            "categories": ["בדיקות"],
            "status": "draft"  # שימוש בסטטוס טיוטה כדי שהמוצר לא יופיע בחנות
        }
        
        # יצירת המוצר
        start_time = time.time()
        created_product = await product_manager.create_product(product_data)
        end_time = time.time()
        create_time_ms = (end_time - start_time) * 1000
        
        if created_product:
            product_id = created_product.get("id")
            print(f"✅ יצירת מוצר הצליחה!")
            print(f"זמן תגובה: {create_time_ms:.2f} מילישניות")
            print(f"מזהה המוצר: {product_id}")
            print(f"שם המוצר: {created_product.get('name')}")
            
            # ניקוי - מחיקת המוצר שנוצר
            print("\nמוחק את מוצר הבדיקה...")
            status_code, _ = await api._make_request("DELETE", f"products/{product_id}", params={"force": True})
            if status_code in (200, 201):
                print(f"✅ מחיקת מוצר הבדיקה הצליחה!")
            else:
                print(f"❌ מחיקת מוצר הבדיקה נכשלה. קוד תגובה: {status_code}")
            
            return True
        else:
            print(f"❌ יצירת מוצר נכשלה.")
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה ביצירת מוצר: {str(e)}")
        return False

async def test_update_product():
    """בדיקת עדכון מוצר קיים"""
    print("\n=== בדיקת עדכון מוצר קיים ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות.")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        # יצירת מוצר לבדיקה
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        product_data = {
            "name": f"מוצר לעדכון - {timestamp}",
            "description": "מוצר שנוצר לצורך בדיקת עדכון",
            "regular_price": "199.90",
            "categories": ["בדיקות"],
            "status": "draft"
        }
        
        # יצירת המוצר
        created_product = await product_manager.create_product(product_data)
        
        if not created_product:
            print(f"❌ יצירת מוצר לבדיקת עדכון נכשלה.")
            return False
        
        product_id = created_product.get("id")
        print(f"✅ נוצר מוצר לבדיקת עדכון. מזהה: {product_id}")
        
        # עדכון המוצר
        update_data = {
            "description": f"תיאור מעודכן - {timestamp}",
            "regular_price": "149.90",
            "sale_price": "129.90"
        }
        
        start_time = time.time()
        updated_product = await product_manager.update_product(product_id, update_data)
        end_time = time.time()
        update_time_ms = (end_time - start_time) * 1000
        
        if updated_product:
            print(f"✅ עדכון מוצר הצליח!")
            print(f"זמן תגובה: {update_time_ms:.2f} מילישניות")
            print(f"מחיר מקורי: {created_product.get('regular_price')}")
            print(f"מחיר מעודכן: {updated_product.get('regular_price')}")
            print(f"מחיר מבצע חדש: {updated_product.get('sale_price')}")
            
            # ניקוי - מחיקת המוצר שנוצר
            print("\nמוחק את מוצר הבדיקה...")
            status_code, _ = await api._make_request("DELETE", f"products/{product_id}", params={"force": True})
            if status_code in (200, 201):
                print(f"✅ מחיקת מוצר הבדיקה הצליחה!")
            else:
                print(f"❌ מחיקת מוצר הבדיקה נכשלה. קוד תגובה: {status_code}")
            
            return True
        else:
            print(f"❌ עדכון מוצר נכשל.")
            
            # ניקוי - מחיקת המוצר שנוצר למרות הכישלון בעדכון
            await api._make_request("DELETE", f"products/{product_id}", params={"force": True})
            
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בעדכון מוצר: {str(e)}")
        return False

async def test_get_categories():
    """בדיקת קבלת קטגוריות מהחנות"""
    print("\n=== בדיקת קבלת קטגוריות מהחנות ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות.")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # קבלת קטגוריות
        start_time = time.time()
        status_code, categories = await api._make_request("GET", "products/categories", params={"per_page": 10})
        end_time = time.time()
        request_time_ms = (end_time - start_time) * 1000
        
        if status_code == 200:
            print(f"✅ קבלת קטגוריות הצליחה!")
            print(f"זמן תגובה: {request_time_ms:.2f} מילישניות")
            print(f"מספר קטגוריות שהתקבלו: {len(categories)}")
            
            if categories:
                print("\nדוגמאות לקטגוריות:")
                for i, category in enumerate(categories[:5], 1):
                    print(f"  {i}. {category.get('name')} (ID: {category.get('id')}, מוצרים: {category.get('count')})")
            
            return True
        else:
            print(f"❌ קבלת קטגוריות נכשלה. קוד תגובה: {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בקבלת קטגוריות: {str(e)}")
        return False

async def test_create_category():
    """בדיקת יצירת קטגוריה חדשה"""
    print("\n=== בדיקת יצירת קטגוריה חדשה ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות.")
        return False
    
    try:
        # יצירת מופע API
        api = WooCommerceAPI(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET
        )
        
        # יצירת נתוני קטגוריה לבדיקה
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        category_data = {
            "name": f"קטגוריית בדיקה - {timestamp}",
            "description": "קטגוריה שנוצרה לצורך בדיקת אינטגרציה עם WooCommerce API"
        }
        
        # יצירת הקטגוריה
        start_time = time.time()
        status_code, created_category = await api._make_request("POST", "products/categories", data=category_data)
        end_time = time.time()
        create_time_ms = (end_time - start_time) * 1000
        
        if status_code in (200, 201):
            category_id = created_category.get("id")
            print(f"✅ יצירת קטגוריה הצליחה!")
            print(f"זמן תגובה: {create_time_ms:.2f} מילישניות")
            print(f"מזהה הקטגוריה: {category_id}")
            print(f"שם הקטגוריה: {created_category.get('name')}")
            
            # ניקוי - מחיקת הקטגוריה שנוצרה
            print("\nמוחק את קטגוריית הבדיקה...")
            status_code, _ = await api._make_request("DELETE", f"products/categories/{category_id}", params={"force": True})
            if status_code in (200, 201):
                print(f"✅ מחיקת קטגוריית הבדיקה הצליחה!")
            else:
                print(f"❌ מחיקת קטגוריית הבדיקה נכשלה. קוד תגובה: {status_code}")
            
            return True
        else:
            print(f"❌ יצירת קטגוריה נכשלה. קוד תגובה: {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ אירעה שגיאה ביצירת קטגוריה: {str(e)}")
        return False

async def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות אינטגרציה עם WooCommerce API")
    print("=" * 80)
    
    # בדיקת חיבור ל-API
    connection_success = await test_api_connection()
    if not connection_success:
        print("\n❌ בדיקת החיבור נכשלה. לא ניתן להמשיך בבדיקות.")
        return
    
    # בדיקות נוספות
    await test_get_products()
    await test_create_product()
    await test_update_product()
    await test_get_categories()
    await test_create_category()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות אינטגרציה עם WooCommerce API הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 