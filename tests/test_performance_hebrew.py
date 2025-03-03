"""
בדיקות ביצועים ותמיכה בעברית
"""
import unittest
import os
import sys
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv
from datetime import datetime
import re

# הוספת תיקיית הפרויקט ל-PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.insert(0, project_dir)

from src.bots.telegram_bot import (
    create_product_start,
    create_product_name,
    create_product_description,
    create_product_price,
    create_product_categories,
    create_product_images_text,
    show_product_confirmation,
    create_product_confirmation,
    safe_edit_message,
    WAITING_FOR_PRODUCT_NAME,
    WAITING_FOR_PRODUCT_DESCRIPTION,
    WAITING_FOR_PRODUCT_PRICE,
    WAITING_FOR_PRODUCT_CATEGORIES,
    WAITING_FOR_PRODUCT_IMAGES,
    WAITING_FOR_PRODUCT_CONFIRMATION
)
from src.tools.product_intent_recognizer import (
    is_product_creation_intent,
    extract_product_data,
    identify_missing_required_fields
)
from src.tools.product_manager import (
    format_product_for_display,
    create_product_from_text
)

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

# הגדרת סף זמן ביצוע מקסימלי (במילישניות)
MAX_EXECUTION_TIME_MS = 1000  # 1 שנייה

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

class TestPerformanceHebrew(AsyncTestCase):
    """בדיקות ביצועים ותמיכה בעברית"""
    
    def setUp(self):
        """הגדרת סביבת הבדיקה"""
        # יצירת מוקים
        self.context = MockContext()
        self.update = MockUpdate()
        
        # מוק לחיבור לחנות
        self.store_patcher = patch('src.bots.telegram_bot.get_store_connection')
        self.mock_get_store = self.store_patcher.start()
        self.mock_get_store.return_value = (True, "חנות מחוברת", MagicMock())
        
        # מוק לבדיקת חיבור לחנות
        self.is_connected_patcher = patch('src.bots.telegram_bot.is_store_connected')
        self.mock_is_connected = self.is_connected_patcher.start()
        self.mock_is_connected.return_value = True
        
        # מוק למנהל המוצרים
        self.product_manager_patcher = patch('src.bots.telegram_bot.ProductManager')
        self.mock_product_manager = self.product_manager_patcher.start()
        
        # הגדרת מזהה ייחודי לבדיקה
        self.test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # רשימת זמני ביצוע
        self.execution_times = {}
    
    def tearDown(self):
        """ניקוי לאחר הבדיקות"""
        self.store_patcher.stop()
        self.is_connected_patcher.stop()
        self.product_manager_patcher.stop()
        
        # הצגת סיכום זמני ביצוע
        if self.execution_times:
            print("\n=== סיכום זמני ביצוע ===")
            for name, time_ms in self.execution_times.items():
                print(f"{name}: {time_ms:.2f} מילישניות")
    
    async def measure_execution_time(self, func, *args, **kwargs):
        """מדידת זמן ביצוע של פונקציה"""
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # המרה למילישניות
        self.execution_times[func.__name__] = execution_time
        return result
    
    async def test_performance_product_creation_flow(self):
        """בדיקת ביצועים של תהליך יצירת מוצר"""
        print("\n=== בדיקת ביצועים של תהליך יצירת מוצר ===")
        
        # שלב 1: התחלת תהליך יצירת מוצר
        self.update.message.text = "/create_product"
        await self.measure_execution_time(create_product_start, self.update, self.context)
        print("✅ נמדד זמן ביצוע של התחלת תהליך יצירת מוצר")
        
        # שלב 2: הזנת שם המוצר
        self.update.message.text = f"כיסא משרדי לבדיקה {self.test_timestamp}"
        await self.measure_execution_time(create_product_name, self.update, self.context)
        print("✅ נמדד זמן ביצוע של הזנת שם המוצר")
        
        # שלב 3: הזנת תיאור המוצר
        self.update.message.text = "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת."
        await self.measure_execution_time(create_product_description, self.update, self.context)
        print("✅ נמדד זמן ביצוע של הזנת תיאור המוצר")
        
        # שלב 4: הזנת מחיר המוצר
        self.update.message.text = "299.90 ₪"
        await self.measure_execution_time(create_product_price, self.update, self.context)
        print("✅ נמדד זמן ביצוע של הזנת מחיר המוצר")
        
        # שלב 5: הזנת קטגוריות המוצר
        self.update.message.text = "ריהוט, ריהוט משרדי, כיסאות"
        await self.measure_execution_time(create_product_categories, self.update, self.context)
        print("✅ נמדד זמן ביצוע של הזנת קטגוריות המוצר")
        
        # שלב 6: דילוג על תמונות המוצר
        self.update.message.text = "דלג"
        await self.measure_execution_time(create_product_images_text, self.update, self.context)
        print("✅ נמדד זמן ביצוע של דילוג על תמונות המוצר")
        
        # שלב 7: הצגת סיכום המוצר
        with patch('src.bots.telegram_bot.format_product_preview') as mock_format:
            mock_format.return_value = "סיכום המוצר לאישור"
            await self.measure_execution_time(show_product_confirmation, self.update, self.context)
            print("✅ נמדד זמן ביצוע של הצגת סיכום המוצר")
        
        # שלב 8: אישור יצירת המוצר
        self.update.message.text = "אישור"
        mock_product_manager_instance = MagicMock()
        mock_product_manager_instance.create_product = AsyncMock()
        mock_product_manager_instance.create_product.return_value = {
            "id": 123,
            "name": f"כיסא משרדי לבדיקה {self.test_timestamp}",
            "permalink": f"https://example.com/product/chair-{self.test_timestamp}"
        }
        self.mock_product_manager.return_value = mock_product_manager_instance
        
        await self.measure_execution_time(create_product_confirmation, self.update, self.context)
        print("✅ נמדד זמן ביצוע של אישור יצירת המוצר")
        
        # בדיקת זמני ביצוע
        for name, time_ms in self.execution_times.items():
            self.assertLess(time_ms, 1000, f"זמן הביצוע של {name} ({time_ms:.2f} מילישניות) ארוך מדי")
        
        print("✅ כל זמני הביצוע סבירים (פחות מ-1000 מילישניות)")
    
    async def test_hebrew_support_product_intent(self):
        """בדיקת תמיכה בעברית בזיהוי כוונת יצירת מוצר"""
        print("\n=== בדיקת תמיכה בעברית בזיהוי כוונת יצירת מוצר ===")
        
        # מקרי בדיקה בעברית
        hebrew_test_cases = [
            "אני רוצה ליצור מוצר חדש - כיסא משרדי",
            "תוסיף בבקשה מוצר חדש לחנות - שולחן עבודה",
            "צריך להוסיף מוצר - מחשב נייד",
            "אפשר להוסיף לחנות כיסא גיימינג חדש?",
            "בוא נוסיף מוצר חדש לחנות - מקלדת מכנית"
        ]
        
        for i, text in enumerate(hebrew_test_cases, 1):
            start_time = time.time()
            intent_result = is_product_creation_intent(text)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # המרה למילישניות
            
            self.assertTrue(intent_result, f"לא זוהתה כוונת יצירת מוצר בטקסט העברי: '{text}'")
            print(f"✅ מקרה {i}: זוהתה כוונת יצירת מוצר בטקסט העברי ({execution_time:.2f} מילישניות)")
            
            # חילוץ נתונים
            start_time = time.time()
            product_data = extract_product_data(text)
            end_time = time.time()
            extraction_time = (end_time - start_time) * 1000  # המרה למילישניות
            
            self.assertIn("name", product_data, f"לא חולץ שם מוצר מהטקסט העברי: '{text}'")
            print(f"✅ מקרה {i}: חולץ שם מוצר מהטקסט העברי ({extraction_time:.2f} מילישניות)")
    
    async def test_hebrew_markdown_parsing(self):
        """בדיקת פרסור תגי Markdown בטקסט עברי"""
        print("\n=== בדיקת פרסור תגי Markdown בטקסט עברי ===")
        
        # מקרי בדיקה עם תגי Markdown בעברית
        markdown_test_cases = [
            "*כיסא משרדי*: מוצר איכותי לבדיקה",
            "**שולחן עבודה**: מוצר _איכותי_ לבדיקה",
            "מוצר חדש: `מחשב נייד` לבדיקה",
            "[קישור למוצר](https://example.com/product)",
            "מוצר *מודגש* עם _הטיה_ ו`קוד`"
        ]
        
        for i, text in enumerate(markdown_test_cases, 1):
            # יצירת מוק לעדכון הודעה
            mock_message = MagicMock()
            mock_message.text = text
            mock_message.chat_id = 123456789
            mock_message.message_id = 1
            
            # בדיקת פרסור Markdown
            try:
                await safe_edit_message(
                    self.context.bot,
                    chat_id=mock_message.chat_id,
                    message_id=mock_message.message_id,
                    text=text
                )
                print(f"✅ מקרה {i}: פרסור תגי Markdown בטקסט עברי הצליח")
            except Exception as e:
                self.fail(f"פרסור תגי Markdown בטקסט עברי נכשל: {str(e)}")
    
    async def test_hebrew_special_characters(self):
        """בדיקת תמיכה בתווים מיוחדים בעברית"""
        # יצירת אובייקטים מדומים
        update = MockUpdate(message_text="מוצר עם תווים מיוחדים: ״׳–—")
        context = MockContext()
        
        # מדידת זמן ביצוע
        start_time = time.time()
        
        # הרצת הפונקציה
        with patch('src.bots.telegram_bot.safe_edit_message') as mock_edit:
            await create_product_name(update, context)
            
            # בדיקה שהפונקציה נקראה עם הפרמטרים הנכונים
            mock_edit.assert_called_once()
            
            # בדיקה שהטקסט בעברית עם תווים מיוחדים מטופל כראוי
            call_args = mock_edit.call_args[0]
            self.assertIn("מוצר עם תווים מיוחדים", call_args[2])
        
        # חישוב זמן ביצוע
        execution_time = time.time() - start_time
        print(f"זמן ביצוע test_hebrew_special_characters: {execution_time:.2f} שניות")
        
        # בדיקה שזמן הביצוע סביר
        self.assertLess(execution_time, 1.0, "זמן הביצוע ארוך מדי")
    
    async def test_product_display_hebrew(self):
        """בדיקת הצגת מוצר בעברית"""
        # יצירת אובייקטים מדומים
        update = MockUpdate()
        context = MockContext()
        
        # הגדרת נתוני מוצר בעברית
        context.user_data = {
            'product_name': 'מוצר לבדיקה',
            'product_description': 'תיאור מוצר בעברית עם פסקאות\nשורה שנייה\nשורה שלישית',
            'product_price': '99.90',
            'product_categories': ['קטגוריה 1', 'קטגוריה 2'],
            'product_images': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
        }
        
        # מדידת זמן ביצוע
        start_time = time.time()
        
        # הרצת הפונקציה
        with patch('src.bots.telegram_bot.safe_edit_message') as mock_edit:
            await show_product_confirmation(update, context)
            
            # בדיקה שהפונקציה נקראה עם הפרמטרים הנכונים
            mock_edit.assert_called_once()
            
            # בדיקה שהטקסט בעברית מוצג כראוי
            call_args = mock_edit.call_args[0]
            self.assertIn('מוצר לבדיקה', call_args[2])
            self.assertIn('תיאור מוצר בעברית', call_args[2])
            self.assertIn('99.90', call_args[2])
            self.assertIn('קטגוריה 1', call_args[2])
            self.assertIn('קטגוריה 2', call_args[2])
        
        # חישוב זמן ביצוע
        execution_time = time.time() - start_time
        print(f"זמן ביצוע test_product_display_hebrew: {execution_time:.2f} שניות")
        
        # בדיקה שזמן הביצוע סביר
        self.assertLess(execution_time, 1.0, "זמן הביצוע ארוך מדי")
    
    async def test_woocommerce_api_performance(self):
        """בדיקת ביצועים של ה-API של WooCommerce"""
        from src.tools.product_manager import ProductManager
        from src.tools.woocommerce_tools import get_woocommerce_api
        
        # יצירת חיבור ל-API של WooCommerce
        woocommerce = get_woocommerce_api(
            store_url=os.getenv("TEST_STORE_URL"),
            consumer_key=os.getenv("TEST_CONSUMER_KEY"),
            consumer_secret=os.getenv("TEST_CONSUMER_SECRET")
        )
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(woocommerce)
        
        # מדידת זמן ביצוע לקבלת קטגוריות
        start_time = time.time()
        categories = await product_manager.get_categories()
        categories_time = time.time() - start_time
        print(f"זמן ביצוע קבלת קטגוריות: {categories_time:.2f} שניות")
        
        # מדידת זמן ביצוע לקבלת מוצרים
        start_time = time.time()
        products = await product_manager.get_products(per_page=5)
        products_time = time.time() - start_time
        print(f"זמן ביצוע קבלת מוצרים: {products_time:.2f} שניות")
        
        print(f"מספר קטגוריות שהתקבלו: {len(categories)}")
        print(f"מספר מוצרים שהתקבלו: {len(products)}")
        
        return categories_time, products_time
    
    async def test_hebrew_rtl_formatting(self):
        """בדיקת פורמט RTL בעברית"""
        # יצירת אובייקטים מדומים
        update = MockUpdate()
        context = MockContext()
        
        # טקסט מעורב עברית ואנגלית
        mixed_text = "מוצר חדש - New Product עם תכונות מיוחדות"
        update.message.text = mixed_text
        
        # מדידת זמן ביצוע
        start_time = time.time()
        
        # הרצת הפונקציה
        with patch('src.bots.telegram_bot.safe_edit_message') as mock_edit:
            await create_product_name(update, context)
            
            # בדיקה שהפונקציה נקראה עם הפרמטרים הנכונים
            mock_edit.assert_called_once()
            
            # בדיקה שהטקסט המעורב מטופל כראוי
            call_args = mock_edit.call_args[0]
            self.assertIn(mixed_text, call_args[2])
        
        # חישוב זמן ביצוע
        execution_time = time.time() - start_time
        print(f"זמן ביצוע test_hebrew_rtl_formatting: {execution_time:.2f} שניות")
        
        # בדיקה שזמן הביצוע סביר
        self.assertLess(execution_time, 1.0, "זמן הביצוע ארוך מדי")
    
    async def test_caching_performance(self):
        """בדיקת ביצועים עם מנגנון מטמון"""
        from src.tools.product_manager import ProductManager
        from src.tools.woocommerce_tools import get_woocommerce_api
        
        # יצירת חיבור ל-API של WooCommerce
        woocommerce = get_woocommerce_api(
            store_url=os.getenv("TEST_STORE_URL"),
            consumer_key=os.getenv("TEST_CONSUMER_KEY"),
            consumer_secret=os.getenv("TEST_CONSUMER_SECRET")
        )
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(woocommerce)
        
        # קריאה ראשונה - ללא מטמון
        start_time = time.time()
        categories1 = await product_manager.get_categories()
        first_call_time = time.time() - start_time
        print(f"זמן ביצוע קריאה ראשונה לקטגוריות: {first_call_time:.2f} שניות")
        
        # קריאה שנייה - עם מטמון (אם קיים)
        start_time = time.time()
        categories2 = await product_manager.get_categories()
        second_call_time = time.time() - start_time
        print(f"זמן ביצוע קריאה שנייה לקטגוריות: {second_call_time:.2f} שניות")
        
        # בדיקה שהקריאה השנייה מהירה יותר (אם יש מטמון)
        # אם אין מטמון, נדלג על הבדיקה הזו
        if hasattr(product_manager, 'cache_categories') and product_manager.cache_categories:
            self.assertLess(second_call_time, first_call_time, 
                           "הקריאה השנייה אמורה להיות מהירה יותר בגלל המטמון")

async def test_performance_product_creation_flow():
    """בדיקת ביצועים של תהליך יצירת מוצר"""
    print("\n=== בדיקת ביצועים של תהליך יצירת מוצר ===")
    
    # טקסט בדיקה בעברית
    hebrew_text = """
    אני רוצה ליצור מוצר חדש בשם כיסא משרדי ארגונומי
    תיאור: כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת ומונע כאבי גב.
    מחיר: 599.90 ש"ח
    מחיר מבצע: 499.90 ש"ח
    קטגוריות: ריהוט, ריהוט משרדי, כיסאות
    מלאי: 15 יחידות
    משקל: 12 ק"ג
    מידות: אורך 60 ס"מ, רוחב 60 ס"מ, גובה 120 ס"מ
    """
    
    # מדידת זמן ביצוע לזיהוי כוונת יצירת מוצר
    start_time = time.time()
    intent_result = is_product_creation_intent(hebrew_text)
    end_time = time.time()
    intent_time_ms = (end_time - start_time) * 1000
    
    print(f"זיהוי כוונת יצירת מוצר: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
    print(f"זמן ביצוע: {intent_time_ms:.2f} מילישניות")
    print(f"סף זמן: {MAX_EXECUTION_TIME_MS} מילישניות")
    print(f"תוצאה: {'✅ עומד בדרישות' if intent_time_ms < MAX_EXECUTION_TIME_MS else '❌ חורג מהסף'}")
    
    # מדידת זמן ביצוע לחילוץ נתוני מוצר
    start_time = time.time()
    product_data = extract_product_data(hebrew_text)
    end_time = time.time()
    extract_time_ms = (end_time - start_time) * 1000
    
    print(f"\nחילוץ נתוני מוצר:")
    print(f"זמן ביצוע: {extract_time_ms:.2f} מילישניות")
    print(f"סף זמן: {MAX_EXECUTION_TIME_MS} מילישניות")
    print(f"תוצאה: {'✅ עומד בדרישות' if extract_time_ms < MAX_EXECUTION_TIME_MS else '❌ חורג מהסף'}")
    
    # בדיקת שדות חובה
    missing_fields = identify_missing_required_fields(product_data)
    print(f"שדות חובה חסרים: {', '.join(missing_fields) if missing_fields else 'אין'}")
    
    # הצגת הנתונים שחולצו
    print(f"נתוני מוצר שחולצו:")
    for key, value in product_data.items():
        print(f"  - {key}: {value}")
    
    # אם יש פרטי חיבור לחנות, בדיקת זמן יצירת מוצר
    if all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("\nבדיקת זמן יצירת מוצר בחנות:")
        
        # הוספת תוספת לשם המוצר כדי למנוע התנגשויות
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hebrew_text_with_timestamp = hebrew_text.replace("כיסא משרדי ארגונומי", f"כיסא משרדי ארגונומי - בדיקת ביצועים {timestamp}")
        
        start_time = time.time()
        success, message, created_product = await create_product_from_text(
            store_url=STORE_URL,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            text=hebrew_text_with_timestamp
        )
        end_time = time.time()
        create_time_ms = (end_time - start_time) * 1000
        
        print(f"זמן ביצוע: {create_time_ms:.2f} מילישניות")
        print(f"תוצאה: {'✅ המוצר נוצר בהצלחה' if success else '❌ יצירת המוצר נכשלה'}")
        if success:
            print(f"מזהה המוצר: {created_product.get('id', 'לא ידוע')}")
    else:
        print("\n❌ לא ניתן לבדוק זמן יצירת מוצר - חסרים פרטי חיבור לחנות")

async def test_hebrew_support_product_intent():
    """בדיקת תמיכה בעברית בזיהוי כוונת יצירת מוצר"""
    print("\n=== בדיקת תמיכה בעברית בזיהוי כוונת יצירת מוצר ===")
    
    hebrew_test_cases = [
        # ביטויים ישירים בעברית
        "אני רוצה ליצור מוצר חדש",
        "תוסיף בבקשה מוצר חדש לחנות",
        "איך אני מוסיף פריט חדש למלאי",
        "צריך להוסיף מוצר חדש שהגיע",
        "אפשר להוסיף כיסא חדש לחנות",
        
        # ביטויים עם ניקוד ותווים מיוחדים
        "אֲנִי רוֹצֶה לְהוֹסִיף מוּצָר חָדָשׁ",
        "תּוֹסִיף בְּבַקָּשָׁה פָּרִיט חָדָשׁ",
        
        # ביטויים עם סימני פיסוק
        "מוצר חדש! אפשר להוסיף?",
        "הגיע מלאי חדש - צריך להוסיף לחנות",
        
        # ביטויים עם מילים לועזיות
        "אני רוצה לאפלוד פרודקט חדש לסטור",
        "תעשה אדד של איטם חדש לחנות"
    ]
    
    for text in hebrew_test_cases:
        start_time = time.time()
        intent_result = is_product_creation_intent(text)
        end_time = time.time()
        intent_time_ms = (end_time - start_time) * 1000
        
        print(f"טקסט: \"{text}\"")
        print(f"זיהוי כוונה: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
        print(f"זמן ביצוע: {intent_time_ms:.2f} מילישניות")
        print()

async def test_hebrew_markdown_parsing():
    """בדיקת פרסור Markdown בטקסט עברי"""
    print("\n=== בדיקת פרסור Markdown בטקסט עברי ===")
    
    # מקרי בדיקה עם תגי Markdown בעברית
    markdown_test_cases = [
        "*כיסא משרדי*: מוצר איכותי לבדיקה",
        "**שולחן עבודה**: מוצר _איכותי_ לבדיקה",
        "מוצר חדש: `מחשב נייד` לבדיקה",
        "[קישור למוצר](https://example.com/product)",
        "מוצר *מודגש* עם _הטיה_ ו`קוד`"
    ]
    
    for i, text in enumerate(markdown_test_cases, 1):
        # יצירת מוק לעדכון הודעה
        mock_message = MagicMock()
        mock_message.text = text
        mock_message.chat_id = 123456789
        mock_message.message_id = 1
        
        # בדיקת פרסור Markdown
        try:
            await safe_edit_message(
                self.context.bot,
                chat_id=mock_message.chat_id,
                message_id=mock_message.message_id,
                text=text
            )
            print(f"✅ מקרה {i}: פרסור תגי Markdown בטקסט עברי הצליח")
        except Exception as e:
            self.fail(f"פרסור תגי Markdown בטקסט עברי נכשל: {str(e)}")

async def test_hebrew_special_characters():
    """בדיקת תמיכה בתווים מיוחדים בעברית"""
    print("\n=== בדיקת תמיכה בתווים מיוחדים בעברית ===")
    
    # מקרי בדיקה עם תווים מיוחדים בעברית
    special_chars_test_cases = [
        "מוצר במחיר 299.90 ₪",
        "מוצר עם % הנחה",
        "מוצר ב-50% הנחה!",
        "מוצר (חדש) בחנות",
        "מוצר - \"מיוחד\" לבדיקה",
        "מוצר: א', ב', ג'"
    ]
    
    for i, text in enumerate(special_chars_test_cases, 1):
        # בדיקת טיפול בתווים מיוחדים במחיר
        if "₪" in text or "%" in text:
            self.update.message.text = text
            try:
                await create_product_price(self.update, self.context)
                print(f"✅ מקרה {i}: טיפול בתווים מיוחדים במחיר הצליח")
            except Exception as e:
                self.fail(f"טיפול בתווים מיוחדים במחיר נכשל: {str(e)}")
        
        # בדיקת טיפול בתווים מיוחדים בתיאור
        else:
            self.update.message.text = text
            try:
                await create_product_description(self.update, self.context)
                print(f"✅ מקרה {i}: טיפול בתווים מיוחדים בתיאור הצליח")
            except Exception as e:
                self.fail(f"טיפול בתווים מיוחדים בתיאור נכשל: {str(e)}")

async def test_product_display_hebrew():
    """בדיקת הצגת מוצר בעברית"""
    print("\n=== בדיקת הצגת מוצר בעברית ===")
    
    # יצירת מוצר לדוגמה בעברית
    product = {
        "id": 123,
        "name": "כיסא משרדי ארגונומי",
        "description": "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת.",
        "regular_price": "299.90",
        "categories": [
            {"name": "ריהוט"},
            {"name": "ריהוט משרדי"}
        ],
        "images": [
            {"src": "https://example.com/image1.jpg"},
            {"src": "https://example.com/image2.jpg"}
        ],
        "permalink": "https://example.com/product/chair"
    }
    
    # פורמט תצוגת המוצר
    display_text = format_product_for_display(product)
    
    # בדיקת תמיכה בעברית בתצוגת המוצר
    self.assertIn("כיסא משרדי ארגונומי", display_text, "שם המוצר בעברית חסר בתצוגה")
    self.assertIn("כיסא משרדי איכותי", display_text, "תיאור המוצר בעברית חסר בתצוגה")
    self.assertIn("ריהוט", display_text, "קטגוריות המוצר בעברית חסרות בתצוגה")
    
    # בדיקת תמיכה בתגי Markdown בתצוגת המוצר
    self.assertTrue(re.search(r"\*.*\*", display_text), "חסרים תגי Markdown בתצוגת המוצר")
    
    print("✅ תצוגת המוצר בעברית תקינה")
    print("✅ תגי Markdown בתצוגת המוצר תקינים")

async def test_woocommerce_api_performance():
    """בדיקת ביצועים של ה-API של WooCommerce"""
    from src.tools.product_manager import ProductManager
    from src.tools.woocommerce_tools import get_woocommerce_api
    
    print("\n--- בדיקת ביצועים של ה-API של WooCommerce ---")
    
    # יצירת חיבור ל-API של WooCommerce
    woocommerce = get_woocommerce_api(
        store_url=os.getenv("TEST_STORE_URL"),
        consumer_key=os.getenv("TEST_CONSUMER_KEY"),
        consumer_secret=os.getenv("TEST_CONSUMER_SECRET")
    )
    
    # יצירת מנהל מוצרים
    product_manager = ProductManager(woocommerce)
    
    # מדידת זמן ביצוע לקבלת קטגוריות
    start_time = time.time()
    categories = await product_manager.get_categories()
    categories_time = time.time() - start_time
    print(f"זמן ביצוע קבלת קטגוריות: {categories_time:.2f} שניות")
    
    # מדידת זמן ביצוע לקבלת מוצרים
    start_time = time.time()
    products = await product_manager.get_products(per_page=5)
    products_time = time.time() - start_time
    print(f"זמן ביצוע קבלת מוצרים: {products_time:.2f} שניות")
    
    print(f"מספר קטגוריות שהתקבלו: {len(categories)}")
    print(f"מספר מוצרים שהתקבלו: {len(products)}")
    
    return categories_time, products_time

async def test_hebrew_rtl_formatting():
    """בדיקת פורמט RTL בעברית"""
    print("\n--- בדיקת פורמט RTL בעברית ---")
    
    # טקסט מעורב עברית ואנגלית
    mixed_text = "מוצר חדש - New Product עם תכונות מיוחדות"
    
    # יצירת אובייקטים מדומים
    update = MockUpdate(message_text=mixed_text)
    context = MockContext()
    
    # מדידת זמן ביצוע
    start_time = time.time()
    
    # הרצת הפונקציה
    with patch('src.bots.telegram_bot.safe_edit_message') as mock_edit:
        await create_product_name(update, context)
        
        # בדיקה שהפונקציה נקראה
        if mock_edit.called:
            print("✅ הפונקציה safe_edit_message נקראה בהצלחה")
            
            # בדיקה שהטקסט המעורב מטופל כראוי
            call_args = mock_edit.call_args[0]
            if mixed_text in call_args[2]:
                print("✅ הטקסט המעורב טופל כראוי")
            else:
                print("❌ הטקסט המעורב לא טופל כראוי")
        else:
            print("❌ הפונקציה safe_edit_message לא נקראה")
    
    # חישוב זמן ביצוע
    execution_time = time.time() - start_time
    print(f"זמן ביצוע: {execution_time:.2f} שניות")
    
    return execution_time

async def test_caching_performance():
    """בדיקת ביצועים עם מנגנון מטמון"""
    print("\n--- בדיקת ביצועים עם מנגנון מטמון ---")
    
    from src.tools.product_manager import ProductManager
    from src.tools.woocommerce_tools import get_woocommerce_api
    
    # יצירת חיבור ל-API של WooCommerce
    woocommerce = get_woocommerce_api(
        store_url=os.getenv("TEST_STORE_URL"),
        consumer_key=os.getenv("TEST_CONSUMER_KEY"),
        consumer_secret=os.getenv("TEST_CONSUMER_SECRET")
    )
    
    # יצירת מנהל מוצרים
    product_manager = ProductManager(woocommerce)
    
    # קריאה ראשונה - ללא מטמון
    start_time = time.time()
    categories1 = await product_manager.get_categories()
    first_call_time = time.time() - start_time
    print(f"זמן ביצוע קריאה ראשונה לקטגוריות: {first_call_time:.2f} שניות")
    
    # קריאה שנייה - עם מטמון (אם קיים)
    start_time = time.time()
    categories2 = await product_manager.get_categories()
    second_call_time = time.time() - start_time
    print(f"זמן ביצוע קריאה שנייה לקטגוריות: {second_call_time:.2f} שניות")
    
    # בדיקה שהקריאה השנייה מהירה יותר (אם יש מטמון)
    if hasattr(product_manager, 'cache_categories') and product_manager.cache_categories:
        if second_call_time < first_call_time:
            print("✅ הקריאה השנייה מהירה יותר בגלל המטמון")
        else:
            print("❌ הקריאה השנייה לא מהירה יותר למרות המטמון")
    else:
        print("⚠️ לא נמצא מנגנון מטמון במנהל המוצרים")
    
    return first_call_time, second_call_time

async def main():
    """פונקציה ראשית להרצת כל הבדיקות"""
    print("=" * 80)
    print("בדיקות ביצועים ותמיכה בעברית")
    print("=" * 80)
    
    # הרצת בדיקות ביצועים של תהליך יצירת מוצר
    print("\n" + "=" * 80)
    print("בדיקת ביצועים של תהליך יצירת מוצר")
    print("=" * 80)
    await test_performance_product_creation_flow()
    
    # הרצת בדיקות תמיכה בעברית בזיהוי כוונות יצירת מוצר
    print("\n" + "=" * 80)
    print("בדיקת תמיכה בעברית בזיהוי כוונות יצירת מוצר")
    print("=" * 80)
    await test_hebrew_support_product_intent()
    
    # הרצת בדיקות פרסור Markdown בעברית
    print("\n" + "=" * 80)
    print("בדיקת פרסור Markdown בעברית")
    print("=" * 80)
    await test_hebrew_markdown_parsing()
    
    # הרצת בדיקות תווים מיוחדים בעברית
    print("\n" + "=" * 80)
    print("בדיקת תווים מיוחדים בעברית")
    print("=" * 80)
    await test_hebrew_special_characters()
    
    # הרצת בדיקות הצגת מוצר בעברית
    print("\n" + "=" * 80)
    print("בדיקת הצגת מוצר בעברית")
    print("=" * 80)
    await test_product_display_hebrew()
    
    # הרצת בדיקות ביצועים של ה-API של WooCommerce
    print("\n" + "=" * 80)
    print("בדיקת ביצועים של ה-API של WooCommerce")
    print("=" * 80)
    await test_woocommerce_api_performance()
    
    # הרצת בדיקות פורמט RTL בעברית
    print("\n" + "=" * 80)
    print("בדיקת פורמט RTL בעברית")
    print("=" * 80)
    await test_hebrew_rtl_formatting()
    
    # הרצת בדיקות ביצועים עם מנגנון מטמון
    print("\n" + "=" * 80)
    print("בדיקת ביצועים עם מנגנון מטמון")
    print("=" * 80)
    await test_caching_performance()
    
    print("\n" + "=" * 80)
    print("סיום בדיקות ביצועים ותמיכה בעברית")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 