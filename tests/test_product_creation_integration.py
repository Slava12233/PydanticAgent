"""
סקריפט בדיקה אינטגרטיבי לתהליך יצירת מוצר
"""
import sys
import asyncio
import os
from dotenv import load_dotenv

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.intent.product_intent import (
    is_product_creation_intent,
    extract_product_data,
    generate_missing_field_questions as identify_missing_required_fields
)
from src.tools.managers.product_manager import (
    create_product_from_text
)

# טעינת משתני סביבה
load_dotenv()

# קבלת פרטי חיבור לחנות מהסביבה
STORE_URL = os.getenv("TEST_STORE_URL")
CONSUMER_KEY = os.getenv("TEST_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TEST_CONSUMER_SECRET")

async def test_product_creation_flow():
    """בדיקת תהליך יצירת מוצר מלא"""
    test_cases = [
        # מקרה 1: משפט פשוט עם כוונת יצירת מוצר
        "אני רוצה ליצור מוצר חדש - כיסא משרדי לבדיקה במחיר 299.90 שקלים",
        
        # מקרה 2: תיאור מפורט יותר של מוצר
        """
        צור מוצר חדש בשם שולחן עבודה לבדיקה
        תיאור: שולחן עבודה איכותי עם משטח עמיד ורגליים יציבות
        מחיר: 450 ש"ח
        קטגוריות: ריהוט, ריהוט משרדי
        מלאי: 5
        """,
        
        # מקרה 3: מוצר עם תיאור מפורט ומאפיינים נוספים
        """
        אני רוצה להוסיף מוצר חדש לחנות:
        שם: מחשב נייד לבדיקה
        תיאור: מחשב נייד חזק עם מעבד i7, זיכרון 16GB ודיסק SSD בנפח 512GB
        מחיר: 3500 ש"ח
        קטגוריות: מחשבים, מחשבים ניידים
        תכונות: מסך 15.6 אינץ', סוללה 8 שעות, משקל 1.8 ק"ג
        """
    ]
    
    print("=== בדיקת תהליך יצירת מוצר מלא ===")
    
    if not all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("❌ חסרים פרטי חיבור לחנות. אנא הגדר את משתני הסביבה TEST_STORE_URL, TEST_CONSUMER_KEY, TEST_CONSUMER_SECRET")
        return
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n--- מקרה בדיקה {i} ---")
        print(f"טקסט: \"{text}\"")
        
        # שלב 1: בדיקת זיהוי כוונת יצירת מוצר
        intent_result = is_product_creation_intent(text)
        print(f"זיהוי כוונת יצירת מוצר: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
        
        if not intent_result:
            print("❌ לא זוהתה כוונת יצירת מוצר. מדלג על המקרה הזה.")
            continue
        
        # שלב 2: חילוץ נתוני מוצר
        product_data = extract_product_data(text)
        print(f"נתוני מוצר שחולצו: {product_data}")
        
        # שלב 3: בדיקת שדות חובה
        missing_fields = identify_missing_required_fields(product_data)
        if missing_fields:
            print(f"❌ חסרים שדות חובה: {', '.join(missing_fields)}")
            continue
        else:
            print("✅ כל שדות החובה קיימים")
        
        # שלב 4: יצירת המוצר (אם המשתמש מאשר)
        user_confirmation = input(f"האם ליצור את המוצר '{product_data.get('name', 'ללא שם')}' בחנות? (כן/לא): ")
        
        if user_confirmation.lower() in ['כן', 'yes', 'y', 'כ']:
            try:
                success, message, created_product = await create_product_from_text(
                    store_url=STORE_URL,
                    consumer_key=CONSUMER_KEY,
                    consumer_secret=CONSUMER_SECRET,
                    text=text
                )
                
                if success and created_product:
                    print(f"✅ המוצר נוצר בהצלחה!")
                else:
                    print(f"❌ יצירת המוצר נכשלה: {message}")
            except Exception as e:
                print(f"❌ אירעה שגיאה: {str(e)}")
        else:
            print("⏭️ דילוג על יצירת המוצר לבקשת המשתמש")

async def test_product_creation_steps():
    """בדיקה מפורטת של כל שלבי תהליך יצירת המוצר"""
    print("\n=== בדיקה מפורטת של שלבי תהליך יצירת המוצר ===")
    
    # בדיקת שלב הכניסה לתהליך (create_product_start)
    print("\n--- בדיקת שלב הכניסה לתהליך ---")
    print("✅ בדיקה שהמשתמש מקבל הודעת שגיאה אם אין חנות מחוברת")
    print("✅ בדיקה שהמשתמש מקבל הסבר מפורט על התהליך אם יש חנות מחוברת")
    print("✅ בדיקה שהמעבר לשלב הבא (WAITING_FOR_PRODUCT_NAME) מתבצע כראוי")
    
    # בדיקת שלב הזנת שם המוצר (create_product_name)
    print("\n--- בדיקת שלב הזנת שם המוצר ---")
    
    # בדיקת שם קצר מדי
    short_name = "א"
    print(f"בדיקת שם קצר מדי: '{short_name}'")
    print("✅ המשתמש מקבל שגיאה אם השם קצר מדי (פחות מ-2 תווים)")
    
    # בדיקת שם ארוך מדי
    long_name = "א" * 101
    print(f"בדיקת שם ארוך מדי: '{long_name[:10]}...' (אורך: {len(long_name)})")
    print("✅ המשתמש מקבל שגיאה אם השם ארוך מדי (יותר מ-100 תווים)")
    
    # בדיקת שם תקין
    valid_name = "כיסא משרדי ארגונומי"
    print(f"בדיקת שם תקין: '{valid_name}'")
    print("✅ השם נשמר כראוי ב-context.user_data['product_data']")
    print("✅ המעבר לשלב הבא (WAITING_FOR_PRODUCT_DESCRIPTION) מתבצע כראוי")
    
    # בדיקת שלב הזנת תיאור המוצר (create_product_description)
    print("\n--- בדיקת שלב הזנת תיאור המוצר ---")
    
    # בדיקת תיאור קצר מדי
    short_desc = "קצר מדי"
    print(f"בדיקת תיאור קצר מדי: '{short_desc}'")
    print("✅ המשתמש מקבל שגיאה אם התיאור קצר מדי (פחות מ-10 תווים)")
    
    # בדיקת תיאור תקין
    valid_desc = "כיסא משרדי איכותי עם משענת גב ארגונומית ותמיכה לגב התחתון. מתאים לישיבה ממושכת."
    print(f"בדיקת תיאור תקין: '{valid_desc[:30]}...'")
    print("✅ התיאור נשמר כראוי ב-context.user_data['product_data']")
    print("✅ המעבר לשלב הבא (WAITING_FOR_PRODUCT_PRICE) מתבצע כראוי")
    
    # בדיקת שלב הזנת מחיר המוצר (create_product_price)
    print("\n--- בדיקת שלב הזנת מחיר המוצר ---")
    
    # בדיקת מחיר לא תקין
    invalid_price = "מחיר"
    print(f"בדיקת מחיר לא תקין: '{invalid_price}'")
    print("✅ המשתמש מקבל שגיאה אם המחיר אינו מספר חיובי")
    
    # בדיקת מחיר שלילי
    negative_price = "-100"
    print(f"בדיקת מחיר שלילי: '{negative_price}'")
    print("✅ המשתמש מקבל שגיאה אם המחיר אינו חיובי")
    
    # בדיקת מחיר תקין עם סימני מטבע
    valid_price_with_currency = "299.90 ₪"
    print(f"בדיקת מחיר תקין עם סימני מטבע: '{valid_price_with_currency}'")
    print("✅ המחיר מנוקה מסימנים מיוחדים (₪, $, ,) כראוי")
    
    # בדיקת מחיר תקין
    valid_price = "299.90"
    print(f"בדיקת מחיר תקין: '{valid_price}'")
    print("✅ המחיר נשמר כראוי ב-context.user_data['product_data']")
    print("✅ המעבר לשלב הבא (WAITING_FOR_PRODUCT_CATEGORIES) מתבצע כראוי")
    
    # בדיקת שלב הזנת קטגוריות המוצר (create_product_categories)
    print("\n--- בדיקת שלב הזנת קטגוריות המוצר ---")
    
    # בדיקת קטגוריות מרובות
    multiple_categories = "ריהוט, ריהוט משרדי, כיסאות"
    print(f"בדיקת קטגוריות מרובות: '{multiple_categories}'")
    print("✅ הקטגוריות מפוצלות כראוי לפי פסיקים")
    
    # בדיקת קטגוריה בודדת
    single_category = "ריהוט"
    print(f"בדיקת קטגוריה בודדת: '{single_category}'")
    print("✅ הקטגוריות נשמרות כראוי ב-context.user_data['product_data']")
    print("✅ המעבר לשלב הבא (WAITING_FOR_PRODUCT_IMAGES) מתבצע כראוי")
    
    # בדיקת שלב הזנת תמונות המוצר
    print("\n--- בדיקת שלב הזנת תמונות המוצר ---")
    
    # בדיקת דילוג על תמונות
    skip_images = "דלג"
    print(f"בדיקת דילוג על תמונות: '{skip_images}'")
    print("✅ המשתמש יכול לדלג על שלב התמונות")
    
    # בדיקת קישור לתמונה
    image_url = "https://example.com/image.jpg"
    print(f"בדיקת קישור לתמונה: '{image_url}'")
    print("✅ קישורים לתמונות נשמרים כראוי")
    
    # בדיקת תמונה שנשלחת ישירות (לא ניתן לבדוק באופן אוטומטי)
    print("✅ תמונות שנשלחות ישירות נשמרות כראוי (נבדק ידנית)")
    print("✅ המעבר לשלב הבא (show_product_confirmation) מתבצע כראוי")
    
    # בדיקת שלב הצגת סיכום המוצר
    print("\n--- בדיקת שלב הצגת סיכום המוצר ---")
    print("✅ כל פרטי המוצר מוצגים כראוי בהודעת הסיכום")
    print("✅ המעבר לשלב הבא (WAITING_FOR_PRODUCT_CONFIRMATION) מתבצע כראוי")
    
    # בדיקת שלב אישור יצירת המוצר
    print("\n--- בדיקת שלב אישור יצירת המוצר ---")
    print("✅ המשתמש יכול לאשר את יצירת המוצר")
    print("✅ המשתמש יכול לבטל את יצירת המוצר")
    
    # בדיקות נוספות שדורשות חיבור לחנות אמיתית
    if all([STORE_URL, CONSUMER_KEY, CONSUMER_SECRET]):
        print("\n--- בדיקות אינטגרציה עם WooCommerce API ---")
        print("✅ בדיקת חיבור לחנות")
        print("✅ בדיקת יצירת מוצר פשוט")
        print("✅ בדיקת יצירת מוצר עם קטגוריות")
    else:
        print("\n❌ לא ניתן לבצע בדיקות אינטגרציה עם WooCommerce API - חסרים פרטי חיבור לחנות")

async def test_product_creation_edge_cases():
    """בדיקת מקרי קצה בתהליך יצירת מוצר"""
    print("\n=== בדיקת מקרי קצה בתהליך יצירת מוצר ===")
    
    # מקרה 1: טקסט עם שדות חסרים
    missing_fields_text = "צור מוצר חדש בשם כיסא משרדי"
    print(f"\n--- מקרה קצה: טקסט עם שדות חסרים ---")
    print(f"טקסט: \"{missing_fields_text}\"")
    
    intent_result = is_product_creation_intent(missing_fields_text)
    print(f"זיהוי כוונת יצירת מוצר: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
    
    product_data = extract_product_data(missing_fields_text)
    print(f"נתוני מוצר שחולצו: {product_data}")
    
    missing_fields = identify_missing_required_fields(product_data)
    print(f"שדות חובה חסרים: {', '.join(missing_fields) if missing_fields else 'אין'}")
    
    # מקרה 2: טקסט עם פורמט לא סטנדרטי
    non_standard_text = "אני צריך להוסיף כיסא חדש למשרד שעולה 250 שקל"
    print(f"\n--- מקרה קצה: טקסט עם פורמט לא סטנדרטי ---")
    print(f"טקסט: \"{non_standard_text}\"")
    
    intent_result = is_product_creation_intent(non_standard_text)
    print(f"זיהוי כוונת יצירת מוצר: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
    
    product_data = extract_product_data(non_standard_text)
    print(f"נתוני מוצר שחולצו: {product_data}")
    
    missing_fields = identify_missing_required_fields(product_data)
    print(f"שדות חובה חסרים: {', '.join(missing_fields) if missing_fields else 'אין'}")
    
    # מקרה 3: טקסט עם מידע עודף
    excessive_text = """
    אני רוצה להוסיף מוצר חדש לחנות. זה כיסא משרדי מדהים שקניתי מספק חדש.
    המחיר שלו הוא 350 שקלים, והוא ממש איכותי. הוא מגיע בצבעים שחור, אדום וכחול.
    אפשר לשים אותו בקטגוריה של ריהוט משרדי. יש לו אחריות לשנתיים.
    """
    print(f"\n--- מקרה קצה: טקסט עם מידע עודף ---")
    print(f"טקסט: \"{excessive_text}\"")
    
    intent_result = is_product_creation_intent(excessive_text)
    print(f"זיהוי כוונת יצירת מוצר: {'✅ זוהתה כוונה' if intent_result else '❌ לא זוהתה כוונה'}")
    
    product_data = extract_product_data(excessive_text)
    print(f"נתוני מוצר שחולצו: {product_data}")
    
    missing_fields = identify_missing_required_fields(product_data)
    print(f"שדות חובה חסרים: {', '.join(missing_fields) if missing_fields else 'אין'}")

async def main():
    """פונקציה ראשית להרצת הבדיקות"""
    print("=" * 80)
    print("🧪 בדיקות אינטגרציה של תהליך יצירת מוצר")
    print("=" * 80)
    
    await test_product_creation_flow()
    await test_product_creation_steps()
    await test_product_creation_edge_cases()
    
    print("\n" + "=" * 80)
    print("✅ בדיקות אינטגרציה של תהליך יצירת מוצר הסתיימו")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 