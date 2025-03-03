"""
נתונים סטטיים עבור WooCommerce
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
        "actions": ["שחזר מהאשפה", "מחק לצמיתות"]
    }
}

# מידע על סוגי מוצרים ב-WooCommerce
PRODUCT_TYPES = {
    "simple": {
        "name": "מוצר פשוט",
        "description": "מוצר פיזי או דיגיטלי בודד",
        "features": ["מחיר יחיד", "ניהול מלאי פשוט", "משקל ומידות", "מאפיינים קבועים"],
        "use_cases": ["ספרים", "מוצרי צריכה", "קבצים דיגיטליים", "מוצרים ללא וריאציות"]
    },
    "variable": {
        "name": "מוצר משתנה",
        "description": "מוצר עם וריאציות שונות (צבע, גודל, וכו')",
        "features": ["מחירים שונים לכל וריאציה", "ניהול מלאי לכל וריאציה", "תמונות ייחודיות לכל וריאציה"],
        "use_cases": ["בגדים", "נעליים", "מוצרים עם אפשרויות בחירה"]
    },
    "grouped": {
        "name": "מוצר מקובץ",
        "description": "קבוצה של מוצרים קשורים המוצגים יחד",
        "features": ["מכיל מוצרים פשוטים", "אין מחיר עצמאי", "הלקוח בוחר אילו מוצרים לרכוש"],
        "use_cases": ["סטים", "קולקציות", "מוצרים משלימים"]
    },
    "external": {
        "name": "מוצר חיצוני/מסונף",
        "description": "מוצר המפנה לאתר חיצוני לרכישה",
        "features": ["קישור לאתר חיצוני", "אין ניהול מלאי", "אין עגלת קניות"],
        "use_cases": ["שיווק שותפים", "הפניות לספקים", "מוצרים שאינם נמכרים ישירות"]
    },
    "subscription": {
        "name": "מנוי",
        "description": "מוצר עם תשלום חוזר במרווחי זמן קבועים",
        "features": ["תשלום תקופתי", "תקופת ניסיון", "תאריכי חידוש"],
        "use_cases": ["שירותים מתמשכים", "מועדוני לקוחות", "גישה לתוכן"]
    },
    "bundle": {
        "name": "חבילה",
        "description": "אוסף של מוצרים הנמכרים יחד במחיר מוזל",
        "features": ["מחיר מוזל לעומת רכישה נפרדת", "ניהול מלאי מורכב", "שילוב סוגי מוצרים"],
        "use_cases": ["מבצעים", "ערכות", "סטים מיוחדים"]
    }
}

# טיפים לשיפור מכירות ב-WooCommerce
SALES_IMPROVEMENT_TIPS = [
    {
        "category": "מבצעים והנחות",
        "tips": [
            "הצע קופונים לקונים חוזרים עם קוד הנחה אישי",
            "צור מבצעי 'קנה אחד קבל אחד חינם' למוצרים נבחרים",
            "הגדר הנחות כמות לעידוד רכישות גדולות יותר",
            "צור מבצעים מוגבלי זמן ליצירת תחושת דחיפות",
            "הצע משלוח חינם מעל סכום מסוים"
        ]
    },
    {
        "category": "שיווק ופרסום",
        "tips": [
            "הפעל קמפיין דיוור אלקטרוני לפרסום מוצרים חדשים",
            "השתמש ברשתות חברתיות לפרסום מוצרים פופולריים",
            "צור תוכן שיווקי איכותי סביב המוצרים שלך (בלוג, מדריכים)",
            "הפעל תוכנית שיווק שותפים למינוף משווקים חיצוניים",
            "השתמש בפרסום ממומן בגוגל ופייסבוק למוצרים רווחיים"
        ]
    },
    {
        "category": "חווית משתמש",
        "tips": [
            "שפר את מהירות האתר לצמצום נטישת עגלות קניה",
            "פשט את תהליך התשלום להגדלת אחוזי המרה",
            "הוסף תמונות איכותיות ותיאורים מפורטים למוצרים",
            "הוסף ביקורות לקוחות להגברת אמון",
            "אפשר צ'אט חי לתמיכה מיידית בלקוחות מתעניינים"
        ]
    },
    {
        "category": "ניהול מלאי",
        "tips": [
            "זהה מוצרים שאינם נמכרים והצע עליהם הנחות",
            "הגדל מלאי של מוצרים פופולריים לפני עונות שיא",
            "צור חבילות של מוצרים משלימים",
            "הצע מוצרים חלופיים כאשר מוצר אזל מהמלאי",
            "הגדר התראות מלאי נמוך למניעת מחסור"
        ]
    },
    {
        "category": "שימור לקוחות",
        "tips": [
            "הפעל תוכנית נאמנות עם נקודות ותגמולים",
            "שלח הודעות תודה אישיות לאחר רכישה",
            "הצע הטבות מיוחדות ללקוחות ותיקים",
            "בקש משוב לאחר רכישה ופעל לשיפור בהתאם",
            "שלח תזכורות על מוצרים מתכלים לפני שהם נגמרים"
        ]
    }
]

# מידע על תוספים מומלצים ל-WooCommerce
RECOMMENDED_PLUGINS = [
    {
        "name": "WooCommerce Subscriptions",
        "description": "מאפשר מכירת מוצרים ושירותים עם תשלום חוזר",
        "use_cases": ["מנויים", "שירותים מתמשכים", "תוכן בתשלום"],
        "pros": ["ניהול מלא של מנויים", "חידוש אוטומטי", "גמישות בתמחור"],
        "cons": ["עלות גבוהה יחסית", "מורכבות בהגדרה הראשונית"]
    },
    {
        "name": "YITH WooCommerce Wishlist",
        "description": "מאפשר ללקוחות לשמור מוצרים ברשימת משאלות",
        "use_cases": ["חנויות אופנה", "מתנות", "מוצרים יקרים"],
        "pros": ["קל להגדרה", "מגביר מעורבות לקוחות", "מספק נתוני שיווק"],
        "cons": ["פונקציונליות מוגבלת בגרסה החינמית"]
    },
    {
        "name": "WooCommerce Product Bundles",
        "description": "מאפשר יצירת חבילות מוצרים מותאמות אישית",
        "use_cases": ["מבצעים", "ערכות", "מוצרים משלימים"],
        "pros": ["גמישות בתמחור", "אפשרויות התאמה מתקדמות", "ניהול מלאי חכם"],
        "cons": ["עקומת למידה תלולה", "עלול להאט את האתר בהגדרות מורכבות"]
    },
    {
        "name": "Advanced Coupons for WooCommerce",
        "description": "מרחיב את יכולות הקופונים של WooCommerce",
        "use_cases": ["מבצעים מורכבים", "תוכניות נאמנות", "שיווק ממוקד"],
        "pros": ["כללי הנחה מתקדמים", "קופונים אוטומטיים", "מעקב שימוש"],
        "cons": ["התכונות המתקדמות בתשלום", "עלול להיות מורכב למתחילים"]
    },
    {
        "name": "WooCommerce Automated Email Marketing",
        "description": "אוטומציה של הודעות דוא\"ל שיווקיות",
        "use_cases": ["שימור לקוחות", "שחזור עגלות נטושות", "מכירה נוספת"],
        "pros": ["אוטומציה מלאה", "סגמנטציה מתקדמת", "דוחות ביצועים"],
        "cons": ["עלות חודשית", "דורש הגדרה מדויקת"]
    }
]

# פתרונות לבעיות נפוצות ב-WooCommerce
COMMON_ISSUES_SOLUTIONS = {
    "עגלות נטושות": [
        "הפעל מערכת אוטומטית לשליחת תזכורות על עגלות נטושות",
        "פשט את תהליך התשלום והפחת שדות מיותרים",
        "הצג עלויות משלוח מראש למניעת הפתעות",
        "הוסף אפשרויות תשלום מגוונות",
        "הצע קופון הנחה בהודעת התזכורת"
    ],
    "מהירות אתר נמוכה": [
        "השתמש בתוסף קאשינג כמו WP Rocket או W3 Total Cache",
        "אופטימיזציה של תמונות באמצעות תוסף כמו Smush",
        "שדרג את חבילת האחסון שלך",
        "הפעל CDN להאצת טעינת תוכן",
        "צמצם את מספר התוספים הפעילים"
    ],
    "בעיות תשלום": [
        "ודא שהגדרות ה-SSL תקינות",
        "בדוק את הגדרות שערי התשלום",
        "הוסף הוראות ברורות בדף התשלום",
        "הפעל מספר שערי תשלום חלופיים",
        "בדוק תאימות בין גרסאות WooCommerce ותוספי התשלום"
    ],
    "ניהול מלאי לא יעיל": [
        "הגדר התראות מלאי נמוך",
        "השתמש בתוסף לניהול מלאי מתקדם",
        "אוטומטיזציה של עדכוני מלאי מספקים",
        "הגדר כללים לטיפול במוצרים שאזלו מהמלאי",
        "בצע ספירות מלאי תקופתיות"
    ],
    "דירוג נמוך בחיפוש": [
        "אופטימיזציה של כותרות ותיאורי מוצרים",
        "הוסף תגיות Alt לתמונות",
        "שפר את מבנה ה-URL של המוצרים",
        "הוסף תוכן איכותי סביב המוצרים",
        "השתמש בתוסף SEO ייעודי כמו Yoast WooCommerce SEO"
    ]
}

def get_order_status_info(status: str) -> Dict[str, Any]:
    """
    קבלת מידע על סטטוס הזמנה
    
    Args:
        status: קוד הסטטוס
        
    Returns:
        מילון עם מידע על הסטטוס
    """
    return ORDER_STATUSES.get(status, {
        "name": f"סטטוס לא ידוע ({status})",
        "description": "אין מידע על סטטוס זה",
        "next_steps": [],
        "actions": []
    })

def get_product_type_info(product_type: str) -> Dict[str, Any]:
    """
    קבלת מידע על סוג מוצר
    
    Args:
        product_type: קוד סוג המוצר
        
    Returns:
        מילון עם מידע על סוג המוצר
    """
    return PRODUCT_TYPES.get(product_type, {
        "name": f"סוג מוצר לא ידוע ({product_type})",
        "description": "אין מידע על סוג מוצר זה",
        "features": [],
        "use_cases": []
    })

def get_sales_improvement_tips(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    קבלת טיפים לשיפור מכירות
    
    Args:
        category: קטגוריה ספציפית (אופציונלי)
        
    Returns:
        רשימה של טיפים
    """
    if category:
        for tip_category in SALES_IMPROVEMENT_TIPS:
            if tip_category["category"] == category:
                return [tip_category]
    
    return SALES_IMPROVEMENT_TIPS

def get_recommended_plugins(use_case: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    קבלת תוספים מומלצים
    
    Args:
        use_case: מקרה שימוש ספציפי (אופציונלי)
        
    Returns:
        רשימה של תוספים מומלצים
    """
    if use_case:
        return [
            plugin for plugin in RECOMMENDED_PLUGINS 
            if any(uc.lower() in use_case.lower() for uc in plugin["use_cases"])
        ]
    
    return RECOMMENDED_PLUGINS

def get_common_issue_solutions(issue: Optional[str] = None) -> Dict[str, List[str]]:
    """
    קבלת פתרונות לבעיות נפוצות
    
    Args:
        issue: בעיה ספציפית (אופציונלי)
        
    Returns:
        מילון עם פתרונות לבעיות
    """
    if issue:
        for problem, solutions in COMMON_ISSUES_SOLUTIONS.items():
            if issue.lower() in problem.lower():
                return {problem: solutions}
    
    return COMMON_ISSUES_SOLUTIONS

def get_woocommerce_knowledge_base() -> Dict[str, Any]:
    """
    קבלת מאגר ידע מלא על WooCommerce
    
    Returns:
        מילון עם כל המידע על WooCommerce
    """
    return {
        "order_statuses": ORDER_STATUSES,
        "product_types": PRODUCT_TYPES,
        "sales_improvement_tips": SALES_IMPROVEMENT_TIPS,
        "recommended_plugins": RECOMMENDED_PLUGINS,
        "common_issues_solutions": COMMON_ISSUES_SOLUTIONS
    } 
