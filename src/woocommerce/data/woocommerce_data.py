"""
נתונים סטטיים נוספים עבור WooCommerce
"""
from typing import Dict, List, Any, Optional

# מידע על סטטוסי הזמנות ב-WooCommerce
ORDER_STATUSES = {
    "pending": {
        "name": "ממתין לתשלום",
        "description": "ההזמנה התקבלה אך התשלום טרם אושר",
        "next_steps": ["processing", "on-hold", "cancelled"],
        "actions": ["שלח תזכורת תשלום", "בטל הזמנה", "סמן כשולם ידנית"]
    },
    "processing": {
        "name": "בטיפול",
        "description": "התשלום אושר וההזמנה בתהליך הכנה",
        "next_steps": ["completed", "on-hold", "cancelled", "refunded"],
        "actions": ["סמן כהושלם", "עדכן מספר מעקב", "שלח עדכון ללקוח"]
    },
    "on-hold": {
        "name": "בהמתנה",
        "description": "ההזמנה בהמתנה (לרוב בשל בדיקת תשלום או מלאי)",
        "next_steps": ["processing", "cancelled", "refunded"],
        "actions": ["שחרר להמשך טיפול", "בטל הזמנה", "עדכן לקוח"]
    },
    "completed": {
        "name": "הושלם",
        "description": "ההזמנה הושלמה ונשלחה ללקוח",
        "next_steps": ["refunded"],
        "actions": ["החזר כספי", "שלח סקר שביעות רצון", "הצע מוצרים נוספים"]
    },
    "cancelled": {
        "name": "בוטל",
        "description": "ההזמנה בוטלה על ידי המנהל או הלקוח",
        "next_steps": ["processing"],
        "actions": ["שחזר הזמנה", "צור הזמנה חדשה", "שלח קופון פיצוי"]
    },
    "refunded": {
        "name": "הוחזר",
        "description": "הוחזר תשלום מלא עבור ההזמנה",
        "next_steps": [],
        "actions": ["שלח סקר משוב", "הצע מוצרים חלופיים"]
    },
    "failed": {
        "name": "נכשל",
        "description": "תשלום נכשל או נדחה",
        "next_steps": ["pending", "cancelled"],
        "actions": ["שלח אפשרות תשלום חלופית", "בטל הזמנה", "צור קשר עם הלקוח"]
    },
    "trash": {
        "name": "באשפה",
        "description": "ההזמנה הועברה לאשפה",
        "next_steps": [],
        "actions": ["שחזר הזמנה"]
    }
}

# טיפים לשיפור מכירות בחנות
SALES_IMPROVEMENT_TIPS = [
    {
        "category": "general",
        "title": "שיפור חווית משתמש",
        "tips": [
            "פשט את תהליך התשלום",
            "הוסף תמונות איכותיות למוצרים",
            "שפר את זמני טעינת האתר",
            "הוסף חיפוש מתקדם",
            "הוסף סקירות מוצרים"
        ]
    },
    {
        "category": "marketing",
        "title": "שיווק ופרסום",
        "tips": [
            "הפעל קמפיין דיוור אלקטרוני",
            "הצע קופונים והנחות",
            "השתמש ברשתות חברתיות",
            "הפעל תוכנית הפניות",
            "שקול פרסום ממומן"
        ]
    },
    {
        "category": "products",
        "title": "ניהול מוצרים",
        "tips": [
            "הוסף תיאורים מפורטים",
            "עדכן מלאי באופן שוטף",
            "הצע מוצרים משלימים",
            "הוסף תגיות וקטגוריות",
            "בצע מבצעי מכירות תקופתיים"
        ]
    },
    {
        "category": "customers",
        "title": "שירות לקוחות",
        "tips": [
            "הוסף צ'אט חי",
            "ענה במהירות לשאלות",
            "הצע משלוח חינם",
            "פשט את מדיניות ההחזרות",
            "שלח הודעות מעקב אחר הזמנות"
        ]
    },
    {
        "category": "analytics",
        "title": "ניתוח נתונים",
        "tips": [
            "עקוב אחר התנהגות משתמשים",
            "נתח נתוני מכירות",
            "בדוק שיעורי נטישת עגלה",
            "זהה מוצרים פופולריים",
            "בחן את אפקטיביות הקמפיינים"
        ]
    }
]

# תוספים מומלצים ל-WooCommerce
RECOMMENDED_PLUGINS = [
    {
        "use_case": "shipping",
        "plugins": [
            {"name": "WooCommerce Shipping", "description": "חישוב עלויות משלוח מדויקות"},
            {"name": "Table Rate Shipping", "description": "הגדרת תעריפי משלוח מותאמים אישית"},
            {"name": "Shipment Tracking", "description": "מעקב אחר משלוחים"}
        ]
    },
    {
        "use_case": "payment",
        "plugins": [
            {"name": "WooCommerce Payments", "description": "עיבוד תשלומים מובנה"},
            {"name": "PayPal Checkout", "description": "תשלום באמצעות PayPal"},
            {"name": "Stripe Gateway", "description": "עיבוד כרטיסי אשראי"}
        ]
    },
    {
        "use_case": "marketing",
        "plugins": [
            {"name": "MailChimp for WooCommerce", "description": "אינטגרציה עם MailChimp לשיווק באימייל"},
            {"name": "Yoast SEO", "description": "אופטימיזציה למנועי חיפוש"},
            {"name": "Facebook for WooCommerce", "description": "מכירה ישירה בפייסבוק ואינסטגרם"}
        ]
    },
    {
        "use_case": "analytics",
        "plugins": [
            {"name": "Google Analytics", "description": "מעקב אחר התנהגות משתמשים"},
            {"name": "WooCommerce Admin", "description": "דוחות וניתוחים מתקדמים"},
            {"name": "Enhanced Ecommerce Google Analytics", "description": "ניתוח מתקדם של חנות"}
        ]
    },
    {
        "use_case": "customer_service",
        "plugins": [
            {"name": "Live Chat", "description": "צ'אט חי עם לקוחות"},
            {"name": "Customer Reviews", "description": "ניהול ביקורות לקוחות"},
            {"name": "Advanced Notifications", "description": "התראות מותאמות אישית"}
        ]
    }
]

# פתרונות לבעיות נפוצות ב-WooCommerce
COMMON_ISSUE_SOLUTIONS = {
    "payment_issues": [
        "ודא שמפתחות ה-API של שער התשלום נכונים",
        "בדוק אם יש הגבלות גיאוגרפיות על שער התשלום",
        "ודא שהתוסף של שער התשלום מעודכן",
        "בדוק את הגדרות ה-SSL של האתר",
        "נסה לבטל זמנית תוספים אחרים שעלולים להפריע"
    ],
    "shipping_issues": [
        "ודא שהגדרת נכון את אזורי המשלוח",
        "בדוק אם המוצרים כוללים מידות ומשקל",
        "ודא שהגדרת את שיטות המשלוח הנכונות",
        "בדוק אם יש הגבלות משלוח למדינות מסוימות",
        "ודא שחישובי המס נכונים"
    ],
    "product_display": [
        "נקה את המטמון של האתר",
        "ודא שהתמונות בגודל המתאים",
        "בדוק אם יש בעיות בערכת העיצוב",
        "ודא שהתוספים מעודכנים",
        "בדוק אם יש קונפליקטים בין תוספים"
    ],
    "checkout_issues": [
        "פשט את תהליך התשלום",
        "ודא שטפסי התשלום תקינים",
        "בדוק אם יש שדות מיותרים",
        "ודא שהודעות השגיאה ברורות",
        "בדוק את תאימות הדפדפן"
    ],
    "performance": [
        "השתמש בתוסף מטמון",
        "אופטימיזציה של תמונות",
        "שדרג את האחסון",
        "הפעל דחיסת GZIP",
        "הגבל את מספר התוספים"
    ]
}

# מאגר ידע WooCommerce
WOOCOMMERCE_KNOWLEDGE_BASE = {
    "setup": {
        "title": "הקמת חנות",
        "articles": [
            "התקנת WooCommerce",
            "הגדרת מטבע ומיסים",
            "הגדרת שיטות תשלום",
            "הגדרת שיטות משלוח",
            "יצירת דפי חנות"
        ]
    },
    "products": {
        "title": "ניהול מוצרים",
        "articles": [
            "הוספת מוצרים",
            "ניהול מלאי",
            "הגדרת קטגוריות ותגיות",
            "יצירת מוצרים עם וריאציות",
            "ייבוא וייצוא מוצרים"
        ]
    },
    "orders": {
        "title": "ניהול הזמנות",
        "articles": [
            "עיבוד הזמנות",
            "ניהול החזרות",
            "הדפסת תוויות משלוח",
            "שליחת חשבוניות",
            "מעקב אחר הזמנות"
        ]
    },
    "marketing": {
        "title": "שיווק",
        "articles": [
            "יצירת קופונים",
            "הגדרת מבצעים",
            "שיווק באימייל",
            "אינטגרציה עם רשתות חברתיות",
            "אופטימיזציה למנועי חיפוש"
        ]
    },
    "customization": {
        "title": "התאמה אישית",
        "articles": [
            "שינוי ערכת עיצוב",
            "התאמת דפי מוצר",
            "שינוי תהליך התשלום",
            "הוספת שדות מותאמים אישית",
            "יצירת דפי נחיתה"
        ]
    }
}

def get_order_status_info(status: str) -> Dict[str, Any]:
    """
    מחזיר מידע על סטטוס הזמנה
    
    Args:
        status: מזהה הסטטוס
        
    Returns:
        מילון עם מידע על הסטטוס או מילון ריק אם לא נמצא
    """
    return ORDER_STATUSES.get(status, {})

def get_product_type_info(product_type: str) -> Dict[str, Any]:
    """
    מחזיר מידע על סוג מוצר
    
    Args:
        product_type: מזהה סוג המוצר
        
    Returns:
        מילון עם מידע על סוג המוצר או מילון ריק אם לא נמצא
    """
    from .product_categories import PRODUCT_TYPES
    return PRODUCT_TYPES.get(product_type, {})

def get_sales_improvement_tips(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    מחזיר טיפים לשיפור מכירות
    
    Args:
        category: קטגוריה ספציפית (אופציונלי)
        
    Returns:
        רשימה של טיפים לשיפור מכירות
    """
    if category:
        return [tip for tip in SALES_IMPROVEMENT_TIPS if tip["category"] == category]
    return SALES_IMPROVEMENT_TIPS

def get_recommended_plugins(use_case: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    מחזיר תוספים מומלצים
    
    Args:
        use_case: מקרה שימוש ספציפי (אופציונלי)
        
    Returns:
        רשימה של תוספים מומלצים
    """
    if use_case:
        for case in RECOMMENDED_PLUGINS:
            if case["use_case"] == use_case:
                return case["plugins"]
        return []
    return RECOMMENDED_PLUGINS

def get_common_issue_solutions(issue: Optional[str] = None) -> Dict[str, List[str]]:
    """
    מחזיר פתרונות לבעיות נפוצות
    
    Args:
        issue: סוג הבעיה (אופציונלי)
        
    Returns:
        מילון עם פתרונות לבעיות נפוצות
    """
    if issue and issue in COMMON_ISSUE_SOLUTIONS:
        return {issue: COMMON_ISSUE_SOLUTIONS[issue]}
    return COMMON_ISSUE_SOLUTIONS

def get_woocommerce_knowledge_base() -> Dict[str, Any]:
    """
    מחזיר את מאגר הידע של WooCommerce
    
    Returns:
        מילון עם מאגר הידע
    """
    return WOOCOMMERCE_KNOWLEDGE_BASE 