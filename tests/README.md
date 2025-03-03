# מערכת בדיקות PydanticAgent

מסמך זה מתאר את מערכת הבדיקות של PydanticAgent ומסביר כיצד להריץ את הבדיקות השונות.

## סוגי בדיקות

המערכת כוללת מספר סוגי בדיקות:

1. **בדיקות אינטגרציה** - בדיקות המתקשרות ל-API של WooCommerce ובודקות את האינטגרציה עם המערכת.
2. **בדיקות תרחישי משתמש** - בדיקות המדמות תרחישי שימוש מלאים של משתמשים במערכת.
3. **בדיקות ביצועים** - בדיקות הבודקות את ביצועי המערכת ואת התמיכה בעברית.
4. **בדיקות זיהוי כוונות** - בדיקות הבודקות את יכולת המערכת לזהות כוונות משתמש מטקסט בשפה טבעית.
5. **בדיקות מנהלים** - בדיקות הבודקות את פונקציות הניהול של מוצרים, הזמנות ולקוחות.

## הרצת בדיקות

ניתן להריץ את הבדיקות באמצעות הסקריפט `run_tests.py`:

```bash
# הרצת כל הבדיקות
python tests/run_tests.py

# הרצת בדיקות מסוג מסוים
python tests/run_tests.py --type integration
python tests/run_tests.py --type user
python tests/run_tests.py --type performance
python tests/run_tests.py --type intent
python tests/run_tests.py --type manager

# הרצת קובץ בדיקה ספציפי
python tests/run_tests.py --file test_product_creation.py
```

ניתן גם להריץ את הבדיקות המקיפות באמצעות הסקריפט `run_comprehensive_tests.py`:

```bash
python tests/run_comprehensive_tests.py --type all
```

## פרמטרים נוספים

- `--verbose` - הצגת פלט מפורט יותר בזמן הרצת הבדיקות.
- `--file` - הרצת קובץ בדיקה ספציפי.

## קבצי בדיקה

להלן רשימת קבצי הבדיקה העיקריים:

### בדיקות אינטגרציה
- `test_woocommerce_api_integration.py` - בדיקות אינטגרציה עם WooCommerce API.
- `test_product_creation_integration.py` - בדיקות אינטגרציה לתהליך יצירת מוצר.

### בדיקות תרחישי משתמש
- `test_user_scenarios.py` - בדיקות תרחישי שימוש מלאים.

### בדיקות ביצועים
- `test_performance_hebrew.py` - בדיקות ביצועים ותמיכה בעברית.

### בדיקות זיהוי כוונות
- `test_product_creation.py` - בדיקות זיהוי כוונות ליצירת מוצרים.
- `test_intent_recognizer.py` - בדיקות זיהוי כוונות ספציפיות.
- `test_parameter_extraction.py` - בדיקות חילוץ פרמטרים מהודעות.

### בדיקות מנהלים
- `test_product_manager.py` - בדיקות מנהל מוצרים.
- `test_order_manager.py` - בדיקות מנהל הזמנות.
- `test_customer_manager.py` - בדיקות מנהל לקוחות.

## הוספת בדיקות חדשות

כדי להוסיף בדיקות חדשות:

1. צור קובץ בדיקה חדש בתיקיית `tests` עם שם המתחיל ב-`test_`.
2. ודא שהקובץ מכיל פונקציית `main()` שמריצה את הבדיקות.
3. הוסף את הבדיקה החדשה לקובץ `run_comprehensive_tests.py` בקטגוריה המתאימה.

## דרישות מקדימות

לפני הרצת הבדיקות, ודא שהגדרת את משתני הסביבה הנדרשים:

- `WOOCOMMERCE_URL` - כתובת ה-URL של חנות WooCommerce.
- `WOOCOMMERCE_KEY` - מפתח API של WooCommerce.
- `WOOCOMMERCE_SECRET` - סוד API של WooCommerce.

ניתן להגדיר את המשתנים הללו בקובץ `.env` בתיקיית הפרויקט הראשית. 