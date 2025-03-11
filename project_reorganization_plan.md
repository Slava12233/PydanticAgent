# תוכנית לארגון מחדש של פרויקט PydanticAgent

## רקע

הפרויקט הנוכחי סובל ממספר בעיות ארגוניות:

1. כפילות בקבצי מסד נתונים
2. פיזור קבצים הקשורים לאותו נושא במקומות שונים בפרויקט
3. חוסר עקביות בייבוא מודולים
4. חוסר הפרדה ברורה בין שכבות שונות (מסד נתונים, שירותים, ממשק משתמש)

מסמך זה מפרט תוכנית מסודרת לארגון מחדש של הפרויקט כדי לפתור את הבעיות הללו ולשפר את התחזוקתיות והסקלביליות שלו.

## מבנה חדש מוצע

להלן המבנה החדש המוצע לפרויקט:

```
src/
├── database/                  # כל הקשור למסד נתונים
│   ├── core.py                # התחברות למסד נתונים והגדרת מנוע
│   ├── models/                # מודלים של מסד הנתונים
│   │   ├── base.py            # הגדרת ה-Base והפונקציות הבסיסיות
│   │   ├── users.py           # מודלים הקשורים למשתמשים
│   │   ├── woocommerce.py     # מודלים הקשורים ל-WooCommerce
│   │   ├── conversations.py   # מודלים הקשורים לשיחות
│   │   └── documents.py       # מודלים הקשורים למסמכים
│   ├── managers/              # מנהלים של מסד הנתונים
│   │   ├── user_manager.py    # פונקציות לניהול משתמשים
│   │   ├── document_manager.py # פונקציות לניהול מסמכים
│   │   ├── store_manager.py   # פונקציות לניהול חנויות
│   │   ├── product_manager.py # פונקציות לניהול מוצרים
│   │   └── order_manager.py   # פונקציות לניהול הזמנות
│   └── migrations/            # סקריפטים למיגרציות של מסד הנתונים
│       └── add_woocommerce_tables.py
├── woocommerce/               # כל הקשור ל-WooCommerce
│   ├── api/
│   │   ├── api.py             # מחלקת ה-API הבסיסית
│   │   └── cached_api.py      # גרסה עם מטמון
│   ├── services/
│   │   ├── product_service.py # שירות לניהול מוצרים
│   │   ├── order_service.py   # שירות לניהול הזמנות
│   │   └── customer_service.py # שירות לניהול לקוחות
│   ├── utils/
│   │   ├── product_formatter.py # פורמטים למוצרים
│   │   └── order_formatter.py # פורמטים להזמנות
│   ├── templates/
│   │   └── templates.py       # תבניות ל-WooCommerce
│   ├── data/
│   │   └── product_categories.py # נתוני קטגוריות מוצרים
│   └── tools/
│       └── tools.py           # כלים ל-WooCommerce
├── products/                  # כל הקשור למוצרים
│   ├── intent.py              # זיהוי כוונות הקשורות למוצרים
│   ├── keywords.py            # מילות מפתח למוצרים
│   ├── handler.py             # טיפול בבקשות הקשורות למוצרים
│   └── manager.py             # ניהול מוצרים
├── orders/                    # כל הקשור להזמנות
│   ├── intent.py              # זיהוי כוונות הקשורות להזמנות
│   ├── keywords.py            # מילות מפתח להזמנות
│   ├── handler.py             # טיפול בבקשות הקשורות להזמנות
│   └── manager.py             # ניהול הזמנות
├── stores/                    # כל הקשור לחנויות
│   └── handler.py             # טיפול בבקשות הקשורות לחנויות
├── ui/
│   └── telegram/              # ממשק טלגרם
│       ├── core/
│       │   ├── db.py          # פונקציות ספציפיות לבוט טלגרם
│       │   ├── api.py         # ממשק API של טלגרם
│       │   ├── agent.py       # סוכן טלגרם
│       │   ├── core.py        # ליבת הבוט
│       │   ├── logger/        # לוגר ייעודי לטלגרם
│       │   ├── analytics/     # אנליטיקות לטלגרם
│       │   ├── notifications/ # התראות לטלגרם
│       │   ├── settings/      # הגדרות לטלגרם
│       │   ├── scheduler/     # תזמון משימות בטלגרם
│       │   ├── admin/         # פונקציות אדמין לטלגרם
│       │   ├── documents/     # טיפול במסמכים בטלגרם
│       │   ├── conversations/ # ניהול שיחות בטלגרם
│       │   └── tests/         # בדיקות לבוט טלגרם
│       ├── store/
│       │   ├── products.py    # ממשק טלגרם למוצרים
│       │   ├── orders.py      # ממשק טלגרם להזמנות
│       │   ├── store.py       # ממשק טלגרם לחנויות
│       │   ├── payments.py    # ממשק טלגרם לתשלומים
│       │   ├── shipping.py    # ממשק טלגרם למשלוחים
│       │   └── customers.py   # ממשק טלגרם ללקוחות
│       ├── utils/             # כלי עזר לטלגרם
│       │   ├── utils.py       # פונקציות עזר לבוט
│       │   └── logger/        # לוגר ייעודי לכלי העזר
│       └── handlers/          # מטפלים בפקודות טלגרם
│           └── handlers.py    # מטפלים בפקודות בסיסיות
└── core/                      # פונקציונליות ליבה
    └── config.py              # הגדרות תצורה
```

## תוכנית עבודה

### שלב 1: ארגון מחדש של מודול מסד הנתונים

#### משימה 1.1: יצירת מבנה תיקיות חדש למסד הנתונים ✅
- יצירת תיקיות `src/database/models` ו-`src/database/managers`
- יצירת תיקיית `src/database/migrations`
### משימה 1.2: העברת קוד מסד הנתונים הבסיסי
- [x] יצירת src/database/database_manager.py מתוך src/database/database.py
- [x] יצירת src/database/core.py עם קוד להתחברות למסד הנתונים והגדרת מנוע
- [x] יצירת src/database/models/base.py עם המודל הבסיסי
- [x] עדכון קבצי __init__.py בתיקיות המתאימות
- [x] מחיקת src/database/database.py 

#### משימה 1.3: פיצול מודלים ✅
- [x] יצירת `src/database/models/base.py` עם ה-Base והפונקציות הבסיסיות
- [x] יצירת `src/database/models/users.py` עם מודלים הקשורים למשתמשים
- [x] יצירת `src/database/models/woocommerce.py` עם מודלים הקשורים ל-WooCommerce
- [x] יצירת `src/database/models/conversations.py` עם מודלים הקשורים לשיחות
- [x] יצירת `src/database/models/documents.py` עם מודלים הקשורים למסמכים

#### משימה 1.4: העברת מנהלי מסד הנתונים ✅
- [x] העברת `src/services/database/users.py` ל-`src/database/managers/user_manager.py`
- [x] העברת `src/services/database/documents.py` ל-`src/database/managers/document_manager.py`
- [x] יצירת `src/database/managers/store_manager.py`, `product_manager.py`, ו-`order_manager.py`

#### משימה 1.5: העברת מיגרציות ✅
- [x] העברת `src/database/add_woocommerce_tables.py` ל-`src/database/migrations/add_woocommerce_tables.py`

### שלב 2: ארגון מחדש של מודול WooCommerce

#### משימה 2.1: יצירת מבנה תיקיות חדש ל-WooCommerce ✅
- [x] יצירת תיקיית `src/woocommerce` עם תתי-תיקיות `api`, `services`, `utils`, `templates`, `data`, ו-`tools`

#### משימה 2.2: העברת קוד ה-API ✅
- [x] העברת `src/services/store/woocommerce/api/woocommerce_api.py` ל-`src/woocommerce/api/api.py`
- [x] פיצול הקוד ל-`api.py` ו-`cached_api.py` אם רלוונטי

#### משימה 2.3: העברת שירותים ✅
- [x] העברת `src/services/store/woocommerce/services/product_service.py` ל-`src/woocommerce/services/product_service.py`
- [x] העברת `src/services/store/woocommerce/services/order_service.py` ל-`src/woocommerce/services/order_service.py`
- [x] יצירת `src/woocommerce/services/customer_service.py` אם קיים

#### משימה 2.4: העברת כלים ותבניות ✅
- [x] העברת `src/services/store/woocommerce/utils/product_formatter.py` ל-`src/woocommerce/utils/product_formatter.py`
- [x] העברת `src/services/store/woocommerce/utils/order_formatter.py` ל-`src/woocommerce/utils/order_formatter.py`
- [x] העברת `src/services/store/woocommerce/templates/woocommerce_templates.py` ל-`src/woocommerce/templates/templates.py`
- [x] העברת `src/services/store/woocommerce/data/product_categories.py` ל-`src/woocommerce/data/product_categories.py`
- [x] העברת `src/services/store/woocommerce/tools/woocommerce_tools.py` ל-`src/woocommerce/tools/tools.py`

### שלב 3: ארגון מחדש של מודולי מוצרים, הזמנות וחנויות

#### משימה 3.1: יצירת מודול מוצרים ✅
- [x] יצירת תיקיית `src/products`
- [x] העברת `src/core/task_identification/intents/product_intent.py` ל-`src/products/intent.py`
- [x] העברת `src/core/product_keywords.py` ל-`src/products/keywords.py`
- [x] העברת `src/handlers/product/product_handler.py` ל-`src/products/handler.py`
- [x] העברת `src/tools/store/managers/product_manager.py` ל-`src/products/manager.py`
- [x] עדכון קובץ `__init__.py` בתיקיית `products`
- [x] מחיקת הקבצים המקוריים

#### משימה 3.2: יצירת מודול הזמנות ✅
- [x] יצירת תיקיית `src/orders`
- [x] העברת `src/core/task_identification/intents/order_intent.py` ל-`src/orders/intent.py`
- [x] העברת `src/core/order_keywords.py` ל-`src/orders/keywords.py`
- [x] העברת `src/handlers/order/order_handler.py` ל-`src/orders/handler.py`
- [x] העברת `src/tools/store/managers/order_manager.py` ל-`src/orders/manager.py`
- [x] עדכון קובץ `__init__.py` בתיקיית `orders`
- [x] מחיקת הקבצים המקוריים

#### משימה 3.3: יצירת מודול חנויות ✅
- [x] יצירת תיקיית `src/stores`
- [x] העברת `src/handlers/store_handler.py` ל-`src/stores/handler.py`
- [x] עדכון קובץ `__init__.py` בתיקיית `stores`
- [x] מחיקת הקבצים המקוריים

### שלב 4: ארגון מחדש של ממשק טלגרם

#### משימה 4.1: ארגון מחדש של קבצי הליבה של טלגרם ✅
- [x] העברת `src/ui/telegram/core/db/telegram_bot_db.py` ל-`src/ui/telegram/core/db.py`
- [x] מחיקת הקובץ המקורי

#### משימה 4.2: ארגון מחדש של קבצי החנות של טלגרם ✅
- [x] העברת `src/ui/telegram/store/telegram_bot_products.py` ל-`src/ui/telegram/store/products.py`
- [x] העברת `src/ui/telegram/store/telegram_bot_orders.py` ל-`src/ui/telegram/store/orders.py`
- [x] העברת `src/ui/telegram/store/telegram_bot_store.py` ל-`src/ui/telegram/store/store.py`
- [x] מחיקת הקבצים המקוריים

#### משימה 4.3: ארגון מחדש של קבצי טלגרם נוספים ✅
- [x] העברת `src/ui/telegram/store/telegram_bot_payments.py` ל-`src/ui/telegram/store/payments.py`
- [x] העברת `src/ui/telegram/store/telegram_bot_shipping.py` ל-`src/ui/telegram/store/shipping.py`
- [x] העברת `src/ui/telegram/store/telegram_bot_customers.py` ל-`src/ui/telegram/store/customers.py`
- [x] מחיקת הקבצים המקוריים

#### משימה 4.4: ארגון מחדש של קבצי הליבה הנוספים של טלגרם ✅
- [x] העברת `src/ui/telegram/core/telegram_bot_api.py` ל-`src/ui/telegram/core/api.py`
- [x] העברת `src/ui/telegram/core/telegram_bot_core.py` ל-`src/ui/telegram/core/core.py`
- [x] העברת `src/ui/telegram/core/telegram_agent.py` ל-`src/ui/telegram/core/agent.py`
- [x] מחיקת הקבצים המקוריים

#### משימה 4.5: טיפול בקבצי utils של טלגרם ✅
- [x] העברת `src/ui/telegram/utils/telegram_bot_utils.py` ל-`src/ui/telegram/utils/utils.py`
- [x] עדכון ייבואים בהתאם
- [x] מחיקת הקובץ המקורי

#### משימה 4.6: טיפול בקבצי handlers של טלגרם ✅
- [x] העברת `src/ui/telegram/handlers/telegram_bot_handlers.py` ל-`src/ui/telegram/handlers/handlers.py`
- [x] עדכון ייבואים בהתאם
- [x] מחיקת הקובץ המקורי

### שלב 5: עדכון ייבואים ובדיקות

#### משימה 5.1: עדכון ייבואים ✅
- [x] עדכון הייבואים בקבצי הליבה של טלגרם
- [x] עדכון הייבואים בקבצי החנות של טלגרם
- [x] עדכון הייבואים בקבצי הבדיקות
- [x] טיפול בייבואים מעגליים אם קיימים

#### משימה 5.2: בדיקות
- [ ] בדיקת הקוד החדש לוודא שהכל עובד כמצופה
- [ ] תיקון בעיות שנוצרו במהלך הארגון מחדש

## יתרונות המבנה החדש

1. **ארגון לפי נושאים** - כל הקוד הקשור לנושא מסוים (מוצרים, הזמנות, חנויות) מרוכז במקום אחד.
2. **הפרדה ברורה** - הפרדה ברורה בין שכבות שונות (מסד נתונים, שירותים, ממשק משתמש).
3. **הפחתת כפילויות** - כל פונקציונליות תהיה במקום אחד בלבד.
4. **קלות תחזוקה** - קל יותר לתחזק קבצים קטנים וממוקדים.
5. **מניעת ייבואים מעגליים** - מבנה היררכי ברור מונע בעיות ייבוא מעגלי.
6. **סקלביליות** - קל יותר להוסיף פונקציונליות חדשה כשהמבנה מאורגן היטב.

## סיכום

ארגון מחדש של הפרויקט לפי התוכנית המוצעת יביא לשיפור משמעותי בתחזוקתיות, קריאות, וסקלביליות של הקוד. המבנה החדש יקל על פיתוח תכונות חדשות ועל איתור ותיקון באגים.

התוכנית מחולקת למשימות קטנות וברורות שניתן לבצע בהדרגה, מה שמאפשר לבדוק את הקוד אחרי כל שלב ולוודא שהכל עובד כמצופה.
