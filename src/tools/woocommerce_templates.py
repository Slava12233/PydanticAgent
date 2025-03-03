"""
תבניות תשובה לשאלות נפוצות על WooCommerce
"""

# מילון של תבניות תשובה לשאלות נפוצות
TEMPLATES = {
    "setup": {
        "question": "איך מתקינים ומגדירים חנות WooCommerce?",
        "answer": """
🔧 **התקנה והגדרה של חנות WooCommerce**

להתקנת והגדרת חנות WooCommerce, עקוב אחר השלבים הבאים:

1️⃣ **התקנת WordPress**:
   - התקן WordPress על השרת שלך
   - הגדר את האתר הבסיסי (שם, כתובת מייל, וכו')

2️⃣ **התקנת תוסף WooCommerce**:
   - בלוח הבקרה של WordPress, לך ל"תוספים" > "הוסף חדש"
   - חפש "WooCommerce" והתקן את התוסף
   - הפעל את התוסף

3️⃣ **אשף ההגדרות**:
   - אשף ההגדרות יופעל אוטומטית
   - הגדר את פרטי החנות (מיקום, מטבע, יחידות מידה)
   - הגדר אפשרויות תשלום ומשלוח בסיסיות
   - הגדר הגדרות מס אם נדרש

4️⃣ **הוספת מוצרים**:
   - לך ל"מוצרים" > "הוסף חדש"
   - הוסף את המוצר הראשון שלך עם תמונות, מחיר ותיאור

5️⃣ **בחירת ערכת עיצוב**:
   - בחר ערכת עיצוב תואמת לחנות מסחר אלקטרוני
   - התאם את העיצוב לפי המותג שלך

6️⃣ **הגדרות נוספות**:
   - הגדר דפי חשבון, עגלת קניות וקופה
   - הגדר אימיילים אוטומטיים ללקוחות

אם יש לך שאלות ספציפיות לגבי אחד מהשלבים, אשמח לעזור!
"""
    },
    
    "payment_gateways": {
        "question": "אילו שערי תשלום מומלצים ב-WooCommerce?",
        "answer": """
💳 **שערי תשלום מומלצים ב-WooCommerce**

WooCommerce תומך במגוון רחב של שערי תשלום. הנה כמה מהאפשרויות המומלצות:

1️⃣ **שערי תשלום מובנים**:
   - **העברה בנקאית ישירה** - לתשלומים ידניים
   - **תשלום בהמחאה** - לעסקים מסורתיים
   - **תשלום במזומן בעת האספקה** - למשלוחים מקומיים

2️⃣ **שערי תשלום פופולריים בישראל**:
   - **PayPal** - פתרון בינלאומי נפוץ
   - **כרטיסי אשראי (דרך Isracard, Cal, Max)** - באמצעות תוספים ייעודיים
   - **Bit** - לתשלומים מקומיים
   - **PayBox** - לתשלומים מקומיים

3️⃣ **תוספי תשלום מומלצים**:
   - **WooCommerce Payments** - פתרון רשמי של WooCommerce
   - **Stripe** - לתשלומי כרטיסי אשראי בינלאומיים
   - **PayPal Checkout** - לתשלומי PayPal מתקדמים
   - **iCredit** - לסליקת כרטיסי אשראי ישראליים

4️⃣ **שיקולים בבחירת שער תשלום**:
   - עמלות עסקה
   - תמיכה במטבעות
   - אבטחה ותאימות ל-PCI DSS
   - חווית משתמש וקלות השימוש
   - תמיכה בתשלומים חוזרים (אם רלוונטי)

אשמח לתת המלצות ספציפיות יותר בהתאם לצרכים המדויקים של העסק שלך!
"""
    },
    
    "shipping": {
        "question": "איך מגדירים אפשרויות משלוח ב-WooCommerce?",
        "answer": """
🚚 **הגדרת אפשרויות משלוח ב-WooCommerce**

הגדרת מערכת משלוחים יעילה היא קריטית להצלחת החנות שלך. הנה מדריך מקיף:

1️⃣ **הגדרות בסיסיות**:
   - לך ל-WooCommerce > הגדרות > משלוח
   - הגדר את אזורי המשלוח (ישראל, בינלאומי, וכו')
   - הגדר את כתובת המוצא של המשלוחים

2️⃣ **שיטות משלוח פופולריות בישראל**:
   - **משלוח רגיל** - משלוח בדואר ישראל
   - **משלוח מהיר** - שליח עד הבית
   - **איסוף עצמי** - מנקודות איסוף או מהחנות
   - **חברות שליחויות** - שירותי משלוחים כמו UPS, DHL, וכו'

3️⃣ **תוספים מומלצים למשלוח**:
   - **WooCommerce Shipping** - לחישוב עלויות משלוח בזמן אמת
   - **Table Rate Shipping** - לחישוב עלויות לפי משקל, מחיר, כמות או יעד
   - **Distance Rate Shipping** - לחישוב עלויות לפי מרחק

4️⃣ **טיפים להגדרת מדיניות משלוח**:
   - הצע משלוח חינם מעל סכום מסוים
   - הגדר עלויות משלוח ברורות ושקופות
   - אפשר ללקוחות לבחור בין מספר אפשרויות משלוח
   - הגדר זמני אספקה מדויקים לכל שיטת משלוח

5️⃣ **מעקב משלוחים**:
   - הפעל אפשרות למעקב אחר משלוחים
   - שלח הודעות עדכון אוטומטיות על סטטוס המשלוח

אשמח לעזור בהגדרת אפשרויות המשלוח המתאימות ביותר לעסק שלך!
"""
    },
    
    "tax": {
        "question": "איך מגדירים מיסים ומע\"מ ב-WooCommerce?",
        "answer": """
💰 **הגדרת מיסים ומע\"מ ב-WooCommerce**

הגדרת מיסים נכונה חשובה לעמידה בדרישות החוק ולחישוב מחירים מדויק:

1️⃣ **הגדרות בסיסיות**:
   - לך ל-WooCommerce > הגדרות > מיסים
   - הפעל חישוב מיסים
   - בחר אם המחירים כוללים מע\"מ או לא
   - הגדר את כתובת העסק שלך

2️⃣ **הגדרות מע\"מ בישראל**:
   - צור שיעור מס עבור ישראל (כרגע 17%)
   - הגדר את קוד המס (לדוגמה: "מע\"מ")
   - הגדר את המס כאחוז מהמחיר

3️⃣ **מקרים מיוחדים**:
   - מוצרים פטורים ממע\"מ
   - שיעורי מס שונים למוצרים שונים
   - מיסוי בינלאומי למשלוחים לחו\"ל

4️⃣ **תוספים מומלצים למיסוי**:
   - **WooCommerce Tax** - לחישוב אוטומטי של מיסים
   - **Avalara AvaTax** - לאוטומציה מלאה של חישובי מס

5️⃣ **טיפים להגדרת מיסים**:
   - ודא שהחשבוניות כוללות את כל פרטי המס הנדרשים
   - עדכן את שיעורי המס בהתאם לשינויים בחוק
   - שמור על תיעוד מסודר של כל העסקאות והמיסים

אשמח לעזור בהגדרת מערכת המיסים המתאימה לעסק שלך בהתאם לדרישות החוק בישראל!
"""
    },
    
    "seo": {
        "question": "איך מקדמים חנות WooCommerce בגוגל?",
        "answer": """
🔍 **קידום חנות WooCommerce בגוגל (SEO)**

קידום אורגני של חנות WooCommerce יכול להגדיל משמעותית את התנועה והמכירות:

1️⃣ **יסודות ה-SEO לחנויות WooCommerce**:
   - התקן תוסף SEO כמו Yoast SEO או Rank Math
   - הגדר כותרות ותיאורים מתאימים לכל דף ומוצר
   - צור מבנה URL ידידותי למנועי חיפוש
   - הגדר מפת אתר XML והגש אותה לגוגל

2️⃣ **אופטימיזציה למוצרים**:
   - כתוב תיאורי מוצר ייחודיים ומפורטים
   - השתמש במילות מפתח רלוונטיות בכותרות ובתיאורים
   - הוסף תגיות Alt לתמונות המוצרים
   - ארגן מוצרים בקטגוריות הגיוניות עם תיאורים מפורטים

3️⃣ **שיפור מהירות האתר**:
   - השתמש בתוסף קאשינג כמו WP Rocket או W3 Total Cache
   - אופטימיזציה של תמונות באמצעות תוסף כמו Smush
   - בחר אחסון אתרים איכותי ומהיר
   - הפעל CDN להאצת טעינת תוכן

4️⃣ **בניית קישורים וסמכות**:
   - צור תוכן איכותי בבלוג החנות
   - השתתף בפורומים ורשתות חברתיות רלוונטיות
   - צור שותפויות עם אתרים משלימים
   - עודד ביקורות וחוות דעת של לקוחות

5️⃣ **מעקב וניתוח**:
   - חבר את האתר ל-Google Search Console
   - הגדר מעקב באמצעות Google Analytics
   - עקוב אחר דירוגים במילות מפתח חשובות
   - נתח את התנועה והמרות באופן קבוע

אשמח לעזור בבניית אסטרטגיית SEO מותאמת אישית לחנות WooCommerce שלך!
"""
    },
    
    "marketing": {
        "question": "אילו אסטרטגיות שיווק מומלצות לחנות WooCommerce?",
        "answer": """
📣 **אסטרטגיות שיווק מומלצות לחנות WooCommerce**

שיווק אפקטיבי הוא המפתח להצלחת חנות מקוונת. הנה האסטרטגיות המובילות:

1️⃣ **שיווק בדואר אלקטרוני**:
   - בנה רשימת תפוצה באמצעות טפסים באתר
   - שלח ניוזלטר שבועי עם מבצעים ותוכן מעניין
   - הגדר אימיילים אוטומטיים לעגלות נטושות
   - צור קמפיינים לחגים ואירועים מיוחדים
   - תוספים מומלצים: MailChimp for WooCommerce, Newsletter

2️⃣ **שיווק ברשתות חברתיות**:
   - פתח דפי עסק בפייסבוק, אינסטגרם וטיקטוק
   - פרסם תמונות ווידאו איכותיים של המוצרים
   - הפעל חנות בפייסבוק ואינסטגרם
   - עבוד עם משפיענים רלוונטיים לקהל היעד שלך
   - תוספים מומלצים: Social Media Share Buttons, Facebook for WooCommerce

3️⃣ **פרסום ממומן**:
   - הפעל קמפיינים בגוגל (Google Ads)
   - פרסם בפייסבוק ואינסטגרם
   - השתמש בפרסום ריטרגטינג למבקרים קודמים
   - נסה פרסום בערוצים נישתיים רלוונטיים לתחום שלך
   - תוספים מומלצים: Pixel Manager for WooCommerce, Google Ads & Marketing

4️⃣ **תוכניות נאמנות ושיווק שותפים**:
   - הפעל תוכנית נקודות ותגמולים ללקוחות חוזרים
   - צור תוכנית שיווק שותפים למינוף משווקים חיצוניים
   - הצע קופונים אישיים ללקוחות ותיקים
   - תוספים מומלצים: YITH WooCommerce Points and Rewards, AffiliateWP

5️⃣ **אופטימיזציה להמרות**:
   - פשט את תהליך התשלום
   - הוסף עדויות לקוחות ודירוגי מוצרים
   - הצג מוצרים קשורים והצעות למכירה נוספת
   - הפעל צ'אט חי לתמיכה בלקוחות
   - תוספים מומלצים: WooCommerce Checkout Field Editor, TrustPulse

אשמח לעזור בבניית תוכנית שיווק מותאמת אישית לחנות WooCommerce שלך!
"""
    }
}

def get_template(template_key: str) -> dict:
    """
    מחזיר תבנית תשובה לפי מפתח
    
    Args:
        template_key: מפתח התבנית
        
    Returns:
        מילון עם השאלה והתשובה, או None אם המפתח לא קיים
    """
    return TEMPLATES.get(template_key)

def get_all_template_keys() -> list:
    """
    מחזיר רשימה של כל מפתחות התבניות הזמינות
    
    Returns:
        רשימת מפתחות
    """
    return list(TEMPLATES.keys()) 