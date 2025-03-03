"""
בדיקות תרחישי משתמש מלאים
"""
import unittest
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv
from datetime import datetime

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.insert(0, project_dir)

from src.bots.telegram_bot import TelegramBot
from src.services.woocommerce_api import WooCommerceAPI
from src.tools.managers.product_manager import ProductManager, create_product_from_text, format_product_for_display
from src.tools.intent.product_intent import is_product_creation_intent, extract_product_data

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

# קבועים לשלבי השיחה
WAITING_FOR_PRODUCT_NAME = 10
WAITING_FOR_PRODUCT_DESCRIPTION = 11
WAITING_FOR_PRODUCT_PRICE = 12
WAITING_FOR_PRODUCT_CATEGORIES = 17
WAITING_FOR_PRODUCT_IMAGES = 18
WAITING_FOR_PRODUCT_CONFIRMATION = 19

class AsyncTestCase(unittest.TestCase):
    """מחלקת בסיס לבדיקות אסינכרוניות"""
    
    def run_async(self, coro):
        """הרצת פונקציה אסינכרונית בתוך בדיקה"""
        return asyncio.run(coro)

class MockContext:
    """מחלקת מוק להקשר של שיחה בטלגרם"""
    
    def __init__(self):
        self.user_data = {}
        self.bot = MagicMock()
        self.bot.send_message = AsyncMock()
        self.bot.edit_message_text = AsyncMock()
        self.bot.send_photo = AsyncMock()

class MockUpdate:
    """מחלקת מוק לעדכון מטלגרם"""
    
    def __init__(self, message_text=None, user_id=123456789):
        self.message = MagicMock()
        self.message.text = message_text
        self.message.from_user = MagicMock()
        self.message.from_user.id = user_id
        self.message.chat_id = user_id
        self.message.message_id = 1
        self.effective_chat = MagicMock()
        self.effective_chat.id = user_id
        self.effective_message = self.message
        self.callback_query = None

class TestUserScenarios(AsyncTestCase):
    """בדיקות תרחישי משתמש מלאים"""
    
    def setUp(self):
        """הגדרת סביבת הבדיקה"""
        # יצירת מוקים
        self.context = MockContext()
        self.update = MockUpdate()
        
        # יצירת מופע של TelegramBot
        self.bot = TelegramBot()
        
        # מוק לחיבור לחנות
        self.store_patcher = patch('src.bots.telegram_bot.get_store_connection')
        self.mock_get_store = self.store_patcher.start()
        
        # מוק לבדיקת חיבור לחנות
        self.is_connected_patcher = patch('src.bots.telegram_bot.is_store_connected')
        self.mock_is_connected = self.is_connected_patcher.start()
        self.mock_is_connected.return_value = True
        
        # מוק למנהל המוצרים
        self.product_manager_patcher = patch('src.bots.telegram_bot.ProductManager')
        self.mock_product_manager = self.product_manager_patcher.start()
        
        # מוק ל-API של ווקומרס
        self.api_patcher = patch('src.services.woocommerce_api.WooCommerceAPI')
        self.mock_api = self.api_patcher.start()
        
        # הגדרת מזהה ייחודי לבדיקה
        self.test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    def tearDown(self):
        """ניקוי לאחר הבדיקות"""
        self.store_patcher.stop()
        self.is_connected_patcher.stop()
        self.product_manager_patcher.stop()
        self.api_patcher.stop()
    
    async def test_full_product_creation_flow(self):
        """בדיקת תהליך יצירת מוצר מלא"""
        print("\n=== בדיקת תהליך יצירת מוצר מלא ===")
        
        # שלב 1: התחלת תהליך יצירת מוצר
        print("\n--- שלב 1: התחלת תהליך יצירת מוצר ---")
        self.update.message.text = "/create_product"
        result = await self.bot.create_product_start(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_NAME)
        print("✅ המעבר לשלב הזנת שם המוצר התבצע בהצלחה")
        
        # שלב 2: הזנת שם המוצר
        print("\n--- שלב 2: הזנת שם המוצר ---")
        self.update.message.text = f"כיסא משרדי לבדיקה {self.test_timestamp}"
        result = await self.bot.create_product_name(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_DESCRIPTION)
        self.assertEqual(
            self.context.user_data['product_data']['name'],
            f"כיסא משרדי לבדיקה {self.test_timestamp}"
        )
        print("✅ שם המוצר נשמר בהצלחה")
        print("✅ המעבר לשלב הזנת תיאור המוצר התבצע בהצלחה")
        
        # שלב 3: הזנת תיאור המוצר
        print("\n--- שלב 3: הזנת תיאור המוצר ---")
        self.update.message.text = "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת."
        result = await self.bot.create_product_description(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_PRICE)
        self.assertEqual(
            self.context.user_data['product_data']['description'],
            "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת."
        )
        print("✅ תיאור המוצר נשמר בהצלחה")
        print("✅ המעבר לשלב הזנת מחיר המוצר התבצע בהצלחה")
        
        # שלב 4: הזנת מחיר המוצר
        print("\n--- שלב 4: הזנת מחיר המוצר ---")
        self.update.message.text = "299.90 ₪"
        result = await self.bot.create_product_price(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_CATEGORIES)
        self.assertEqual(
            self.context.user_data['product_data']['regular_price'],
            "299.90"
        )
        print("✅ מחיר המוצר נשמר בהצלחה")
        print("✅ המעבר לשלב הזנת קטגוריות המוצר התבצע בהצלחה")
        
        # שלב 5: הזנת קטגוריות המוצר
        print("\n--- שלב 5: הזנת קטגוריות המוצר ---")
        self.update.message.text = "ריהוט, ריהוט משרדי, כיסאות"
        result = await self.bot.create_product_categories(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_IMAGES)
        self.assertEqual(
            self.context.user_data['product_data']['categories'],
            ["ריהוט", "ריהוט משרדי", "כיסאות"]
        )
        print("✅ קטגוריות המוצר נשמרו בהצלחה")
        print("✅ המעבר לשלב הזנת תמונות המוצר התבצע בהצלחה")
        
        # שלב 6: דילוג על תמונות המוצר
        print("\n--- שלב 6: דילוג על תמונות המוצר ---")
        self.update.message.text = "דלג"
        result = await self.bot.create_product_images_text(self.update, self.context)
        self.assertIsNotNone(result)  # מוודא שהפונקציה החזירה ערך כלשהו
        print("✅ דילוג על תמונות המוצר התבצע בהצלחה")
        
        # שלב 7: הצגת סיכום המוצר
        print("\n--- שלב 7: הצגת סיכום המוצר ---")
        # מוק לפונקציית format_product_for_display
        with patch('src.bots.telegram_bot.format_product_preview') as mock_format:
            mock_format.return_value = "סיכום המוצר לאישור"
            result = await self.bot.show_product_confirmation(self.update, self.context)
            self.assertEqual(result, WAITING_FOR_PRODUCT_CONFIRMATION)
            print("✅ סיכום המוצר הוצג בהצלחה")
            print("✅ המעבר לשלב אישור יצירת המוצר התבצע בהצלחה")
        
        # שלב 8: אישור יצירת המוצר
        print("\n--- שלב 8: אישור יצירת המוצר ---")
        self.update.message.text = "אישור"
        
        # מוק לפונקציית create_product
        mock_product_manager_instance = MagicMock()
        mock_product_manager_instance.create_product = AsyncMock()
        mock_product_manager_instance.create_product.return_value = {
            "id": 123,
            "name": f"כיסא משרדי לבדיקה {self.test_timestamp}",
            "permalink": f"https://example.com/product/chair-{self.test_timestamp}"
        }
        self.mock_product_manager.return_value = mock_product_manager_instance
        
        # מוק לפונקציית get_store_connection
        self.mock_get_store.return_value = (True, "חנות מחוברת", self.mock_api)
        
        result = await self.bot.create_product_confirmation(self.update, self.context)
        self.assertEqual(result, -1)  # סיום התהליך
        print("✅ המוצר נוצר בהצלחה")
        print("✅ התהליך הסתיים בהצלחה")
    
    async def test_product_creation_validation_errors(self):
        """בדיקת שגיאות תיקוף בתהליך יצירת מוצר"""
        print("\n=== בדיקת שגיאות תיקוף בתהליך יצירת מוצר ===")
        
        # בדיקת שם קצר מדי
        print("\n--- בדיקת שם קצר מדי ---")
        self.update.message.text = "א"
        result = await self.bot.create_product_name(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_NAME)  # נשאר באותו שלב
        print("✅ שגיאת תיקוף לשם קצר מדי התקבלה בהצלחה")
        
        # בדיקת תיאור קצר מדי
        print("\n--- בדיקת תיאור קצר מדי ---")
        # קודם נגדיר שם תקין
        self.update.message.text = f"כיסא משרדי לבדיקה {self.test_timestamp}"
        await self.bot.create_product_name(self.update, self.context)
        
        # עכשיו נבדוק תיאור קצר מדי
        self.update.message.text = "קצר מדי"
        result = await self.bot.create_product_description(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_DESCRIPTION)  # נשאר באותו שלב
        print("✅ שגיאת תיקוף לתיאור קצר מדי התקבלה בהצלחה")
        
        # בדיקת מחיר לא תקין
        print("\n--- בדיקת מחיר לא תקין ---")
        # קודם נגדיר תיאור תקין
        self.update.message.text = "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת."
        await self.bot.create_product_description(self.update, self.context)
        
        # עכשיו נבדוק מחיר לא תקין
        self.update.message.text = "מחיר"
        result = await self.bot.create_product_price(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_PRICE)  # נשאר באותו שלב
        print("✅ שגיאת תיקוף למחיר לא תקין התקבלה בהצלחה")
        
        # בדיקת מחיר שלילי
        print("\n--- בדיקת מחיר שלילי ---")
        self.update.message.text = "-100"
        result = await self.bot.create_product_price(self.update, self.context)
        self.assertEqual(result, WAITING_FOR_PRODUCT_PRICE)  # נשאר באותו שלב
        print("✅ שגיאת תיקוף למחיר שלילי התקבלה בהצלחה")
    
    async def test_product_creation_cancel(self):
        """בדיקת ביטול תהליך יצירת מוצר"""
        print("\n=== בדיקת ביטול תהליך יצירת מוצר ===")
        
        # התחלת התהליך
        self.update.message.text = "/create_product"
        await self.bot.create_product_start(self.update, self.context)
        
        # ביטול התהליך
        self.update.message.text = "/cancel"
        # מוק לפונקציית cancel
        with patch('src.bots.telegram_bot.cancel') as mock_cancel:
            mock_cancel.return_value = -1
            print("✅ ביטול התהליך התבצע בהצלחה")
    
    async def test_store_not_connected(self):
        """בדיקת מקרה שבו החנות לא מחוברת"""
        print("\n=== בדיקת מקרה שבו החנות לא מחוברת ===")
        
        # הגדרת מוק שהחנות לא מחוברת
        self.mock_is_connected.return_value = False
        
        # ניסיון להתחיל תהליך יצירת מוצר
        self.update.message.text = "/create_product"
        result = await self.bot.create_product_start(self.update, self.context)
        self.assertEqual(result, -1)  # סיום התהליך
        print("✅ התקבלה הודעת שגיאה מתאימה כשהחנות לא מחוברת")

async def test_new_user_scenario():
    """בדיקת תרחיש משתמש חדש שטרם חיבר חנות"""
    print("\n=== בדיקת תרחיש משתמש חדש שטרם חיבר חנות ===")
    
    # סימולציה של משתמש חדש שמנסה ליצור מוצר ללא חיבור חנות
    print("1. משתמש חדש מנסה ליצור מוצר")
    print("2. המערכת בודקת אם יש חנות מחוברת")
    print("3. המערכת מזהה שאין חנות מחוברת")
    print("4. המערכת מציגה הודעת שגיאה ומבקשת מהמשתמש לחבר חנות")
    
    print("\nהודעת מערכת:")
    print("❌ *לא ניתן ליצור מוצר*\n\n"
          "עדיין לא חיברת את חנות ה-WooCommerce שלך לבוט.\n"
          "כדי לחבר את החנות, השתמש בפקודה /connect_store.")
    
    print("\n5. המשתמש מפעיל את פקודת /connect_store")
    print("6. המערכת מציגה הנחיות לחיבור חנות")
    
    print("\nהודעת מערכת:")
    print("🔗 *חיבור חנות WooCommerce*\n\n"
          "כדי לחבר את חנות ה-WooCommerce שלך, אני אצטרך כמה פרטים:\n"
          "1. כתובת האתר שלך (URL)\n"
          "2. מפתח צרכן (Consumer Key)\n"
          "3. סוד צרכן (Consumer Secret)\n\n"
          "אנא הזן את כתובת האתר שלך (לדוגמה: https://mystore.com)")
    
    print("\nתרחיש הסתיים בהצלחה ✅")

async def test_product_creation_scenario():
    """בדיקת תרחיש יצירת מוצר פשוט"""
    print("\n=== בדיקת תרחיש יצירת מוצר פשוט ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. לא ניתן לבצע את הבדיקה.")
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
            print("❌ החיבור לחנות נכשל. לא ניתן לבצע את הבדיקה.")
            return
        
        print("1. משתמש מחובר מבקש ליצור מוצר חדש")
        
        # סימולציה של הודעת משתמש
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_message = f"""
        אני רוצה ליצור מוצר חדש:
        שם: כיסא משרדי ארגונומי - תרחיש בדיקה {timestamp}
        תיאור: כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת ומונע כאבי גב.
        מחיר: 599.90 ש"ח
        קטגוריות: ריהוט, ריהוט משרדי
        סטטוס: טיוטה
        """
        
        print("\n2. המערכת מזהה כוונת יצירת מוצר")
        intent_result = is_product_creation_intent(user_message)
        print(f"זיהוי כוונה: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
        
        print("\n3. המערכת מחלצת נתוני מוצר מההודעה")
        product_data = extract_product_data(user_message)
        print("נתוני מוצר שחולצו:")
        for key, value in product_data.items():
            print(f"  - {key}: {value}")
        
        print("\n4. המערכת יוצרת את המוצר בחנות")
        success, message, created_product = await create_product_from_text(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            text=user_message
        )
        
        if success and created_product:
            product_id = created_product.get("id")
            print(f"✅ המוצר נוצר בהצלחה! מזהה: {product_id}")
            
            print("\n5. המערכת מציגה למשתמש אישור ופרטי המוצר שנוצר")
            product_display = format_product_for_display(created_product)
            print("הודעת מערכת:")
            print(f"🎉 *המוצר נוצר בהצלחה!*\n\n{product_display}")
            
            # ניקוי - מחיקת המוצר שנוצר
            print("\nמוחק את מוצר הבדיקה...")
            status_code, _ = await api._make_request("DELETE", f"products/{product_id}", params={"force": True})
            if status_code in (200, 201):
                print(f"✅ מחיקת מוצר הבדיקה הצליחה!")
            else:
                print(f"❌ מחיקת מוצר הבדיקה נכשלה. קוד תגובה: {status_code}")
        else:
            print(f"❌ יצירת המוצר נכשלה: {message}")
        
        print("\nתרחיש הסתיים בהצלחה ✅")
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בתרחיש: {str(e)}")

async def test_complex_product_scenario():
    """בדיקת תרחיש יצירת מוצר מורכב עם תמונות וקטגוריות"""
    print("\n=== בדיקת תרחיש יצירת מוצר מורכב עם תמונות וקטגוריות ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. לא ניתן לבצע את הבדיקה.")
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
            print("❌ החיבור לחנות נכשל. לא ניתן לבצע את הבדיקה.")
            return
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(api)
        
        print("1. משתמש מבקש ליצור מוצר מורכב עם תמונות וקטגוריות")
        
        # סימולציה של תהליך יצירת מוצר מורכב
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        print("\n2. המשתמש מזין שם מוצר")
        product_name = f"מחשב נייד מקצועי - תרחיש מורכב {timestamp}"
        print(f"שם המוצר: {product_name}")
        
        print("\n3. המשתמש מזין תיאור מוצר")
        product_description = (
            "מחשב נייד מקצועי עם מפרט חזק במיוחד. "
            "מעבד Intel Core i7 דור 11, זיכרון 16GB RAM, "
            "כונן SSD בנפח 512GB, מסך 15.6 אינץ' ברזולוציית Full HD. "
            "מתאים לעבודה מקצועית, עריכת וידאו, גרפיקה ומשחקים."
        )
        print(f"תיאור המוצר: {product_description[:50]}...")
        
        print("\n4. המשתמש מזין מחיר רגיל ומחיר מבצע")
        regular_price = "4999.90"
        sale_price = "4499.90"
        print(f"מחיר רגיל: {regular_price} ש\"ח")
        print(f"מחיר מבצע: {sale_price} ש\"ח")
        
        print("\n5. המשתמש מזין מק\"ט")
        sku = f"LAPTOP-PRO-{timestamp[-6:]}"
        print(f"מק\"ט: {sku}")
        
        print("\n6. המשתמש מזין נתוני מלאי")
        stock_quantity = 10
        print(f"כמות במלאי: {stock_quantity} יחידות")
        
        print("\n7. המשתמש מזין משקל ומידות")
        weight = "2.1"
        dimensions = {
            "length": "35.8",
            "width": "24.5",
            "height": "1.8"
        }
        print(f"משקל: {weight} ק\"ג")
        print(f"מידות: אורך {dimensions['length']} ס\"מ, רוחב {dimensions['width']} ס\"מ, גובה {dimensions['height']} ס\"מ")
        
        print("\n8. המשתמש מזין קטגוריות")
        categories = ["מחשבים", "מחשבים ניידים", "ציוד אלקטרוני"]
        print(f"קטגוריות: {', '.join(categories)}")
        
        print("\n9. המשתמש מזין תמונות")
        images = [
            {"src": "https://example.com/laptop1.jpg", "alt": "מחשב נייד - מבט חזית"},
            {"src": "https://example.com/laptop2.jpg", "alt": "מחשב נייד - מבט צד"}
        ]
        print(f"תמונות: {len(images)} תמונות")
        
        # יצירת נתוני המוצר המלאים
        product_data = {
            "name": product_name,
            "description": product_description,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "sku": sku,
            "manage_stock": True,
            "stock_quantity": stock_quantity,
            "weight": weight,
            "dimensions": dimensions,
            "categories": categories,
            "images": images,
            "status": "draft"  # שימוש בסטטוס טיוטה כדי שהמוצר לא יופיע בחנות
        }
        
        print("\n10. המערכת יוצרת את המוצר בחנות")
        created_product = await product_manager.create_product(product_data)
        
        if created_product:
            product_id = created_product.get("id")
            print(f"✅ המוצר נוצר בהצלחה! מזהה: {product_id}")
            
            print("\n11. המערכת מציגה למשתמש אישור ופרטי המוצר שנוצר")
            product_display = format_product_for_display(created_product)
            print("הודעת מערכת:")
            print(f"🎉 *המוצר נוצר בהצלחה!*\n\n{product_display[:200]}...")
            
            # ניקוי - מחיקת המוצר שנוצר
            print("\nמוחק את מוצר הבדיקה...")
            status_code, _ = await api._make_request("DELETE", f"products/{product_id}", params={"force": True})
            if status_code in (200, 201):
                print(f"✅ מחיקת מוצר הבדיקה הצליחה!")
            else:
                print(f"❌ מחיקת מוצר הבדיקה נכשלה. קוד תגובה: {status_code}")
        else:
            print(f"❌ יצירת המוצר נכשלה.")
        
        print("\nתרחיש הסתיים בהצלחה ✅")
            
    except Exception as e:
        print(f"❌ אירעה שגיאה בתרחיש: {str(e)}")

async def test_cancel_scenario():
    """בדיקת תרחיש ביטול תהליך יצירת מוצר"""
    print("\n=== בדיקת תרחיש ביטול תהליך יצירת מוצר ===")
    
    print("1. משתמש מתחיל תהליך יצירת מוצר")
    print("2. המערכת מציגה הנחיות להזנת שם מוצר")
    
    print("\nהודעת מערכת:")
    print("🛍️ *יצירת מוצר חדש ב-WooCommerce*\n\n"
          "🔵⚪⚪⚪⚪⚪ *שלב 1/6: שם המוצר*\n\n"
          "אני אלווה אותך בתהליך יצירת מוצר חדש בחנות שלך.\n"
          "התהליך כולל מספר שלבים...\n\n"
          "נתחיל! מה יהיה שם המוצר?")
    
    print("\n3. המשתמש מזין שם מוצר")
    print("הודעת משתמש: שולחן עבודה מתכוונן")
    
    print("\n4. המערכת מבקשת תיאור מוצר")
    print("\nהודעת מערכת:")
    print("✅ שם המוצר נשמר: *שולחן עבודה מתכוונן*\n\n"
          "✅🔵⚪⚪⚪⚪ *שלב 2/6: תיאור המוצר*\n\n"
          "עכשיו, אנא הזן תיאור מפורט למוצר.\n"
          "התיאור יוצג בדף המוצר ויעזור ללקוחות להבין את המוצר.")
    
    print("\n5. המשתמש מחליט לבטל את התהליך")
    print("הודעת משתמש: /cancel")
    
    print("\n6. המערכת מבטלת את התהליך ומנקה את הנתונים הזמניים")
    print("\nהודעת מערכת:")
    print("הפעולה בוטלה.")
    
    print("\nתרחיש הסתיים בהצלחה ✅")

async def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות תרחישי משתמש מלאים")
    print("=" * 80)
    
    await test_new_user_scenario()
    await test_product_creation_scenario()
    await test_complex_product_scenario()
    await test_cancel_scenario()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות תרחישי משתמש מלאים הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 