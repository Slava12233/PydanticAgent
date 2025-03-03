"""
מודול לזיהוי כוונות ניהול הזמנות בשפה טבעית
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ביטויים וטריגרים לזיהוי בקשות לניהול הזמנות
ORDER_MANAGEMENT_TRIGGERS = {
    # ביטויים לקבלת מידע על הזמנות
    "get_orders": [
        "הצג הזמנות", "רשימת הזמנות", "הזמנות אחרונות", "כל ההזמנות", "הזמנות שלי",
        "הזמנות היום", "הזמנות השבוע", "הזמנות החודש", "הזמנות ממתינות", "הזמנות בטיפול",
        "show orders", "list orders", "recent orders", "all orders", "my orders",
        "today's orders", "this week's orders", "this month's orders", "pending orders", "processing orders"
    ],
    
    # ביטויים לקבלת מידע על הזמנה ספציפית
    "get_order": [
        "הצג הזמנה", "פרטי הזמנה", "מידע על הזמנה", "סטטוס הזמנה", "מצב הזמנה",
        "הזמנה מספר", "מה קורה עם הזמנה", "איפה הזמנה", "מתי הזמנה", "תאריך הזמנה",
        "show order", "order details", "order info", "order status", "order state",
        "order number", "what's happening with order", "where is order", "when order", "order date"
    ],
    
    # ביטויים לעדכון סטטוס הזמנה
    "update_order_status": [
        "עדכן סטטוס", "שנה סטטוס", "עדכן מצב", "שנה מצב", "סמן כבטיפול", "סמן כנשלח",
        "סמן כהושלם", "סמן כבוטל", "עדכן הזמנה", "שנה הזמנה", "עדכן מצב הזמנה",
        "update status", "change status", "update state", "change state", "mark as processing",
        "mark as shipped", "mark as completed", "mark as cancelled", "update order", "change order"
    ],
    
    # ביטויים לביטול הזמנה
    "cancel_order": [
        "בטל הזמנה", "ביטול הזמנה", "לבטל הזמנה", "לבטל את ההזמנה", "מחק הזמנה",
        "למחוק הזמנה", "למחוק את ההזמנה", "הסר הזמנה", "להסיר הזמנה", "להסיר את ההזמנה",
        "cancel order", "order cancellation", "to cancel order", "to cancel the order", "delete order",
        "to delete order", "to delete the order", "remove order", "to remove order", "to remove the order"
    ],
    
    # ביטויים להחזר כספי
    "refund_order": [
        "החזר כספי", "לבצע החזר", "לעשות החזר", "החזר כסף", "להחזיר כסף", "זיכוי",
        "לבצע זיכוי", "לעשות זיכוי", "החזר תשלום", "להחזיר תשלום", "ביטול תשלום",
        "refund", "make refund", "do refund", "refund money", "return money", "credit",
        "make credit", "do credit", "refund payment", "return payment", "cancel payment"
    ],
    
    # ביטויים לשליחת הודעה ללקוח
    "contact_customer": [
        "צור קשר", "ליצור קשר", "שלח הודעה", "לשלוח הודעה", "שלח אימייל", "לשלוח אימייל",
        "שלח SMS", "לשלוח SMS", "התקשר ללקוח", "להתקשר ללקוח", "עדכן לקוח", "לעדכן לקוח",
        "contact", "to contact", "send message", "to send message", "send email", "to send email",
        "send SMS", "to send SMS", "call customer", "to call customer", "update customer", "to update customer"
    ]
}

# סטטוסים אפשריים של הזמנות
ORDER_STATUSES = {
    "pending": ["ממתין", "ממתין לתשלום", "בהמתנה", "לא שולם", "pending", "awaiting", "not paid"],
    "processing": ["בטיפול", "בעיבוד", "בהכנה", "מכין", "processing", "preparing", "in progress"],
    "on-hold": ["בהמתנה", "מוקפא", "מוחזק", "on hold", "held", "frozen"],
    "completed": ["הושלם", "הסתיים", "נשלם", "בוצע", "completed", "finished", "done"],
    "cancelled": ["בוטל", "מבוטל", "cancelled", "canceled", "aborted"],
    "refunded": ["הוחזר", "זוכה", "refunded", "reimbursed", "credited"],
    "failed": ["נכשל", "כשל", "failed", "unsuccessful"],
    "trash": ["אשפה", "נמחק", "trash", "deleted", "removed"]
}

def is_order_management_intent(text: str) -> Tuple[bool, Optional[str]]:
    """
    בדיקה אם הטקסט מכיל כוונה לניהול הזמנות
    
    Args:
        text: הטקסט לבדיקה
        
    Returns:
        טאפל עם: האם הטקסט מכיל כוונה לניהול הזמנות, וסוג הכוונה (אם יש)
    """
    text_lower = text.lower()
    
    # בדיקת כל סוגי הכוונות
    for intent_type, triggers in ORDER_MANAGEMENT_TRIGGERS.items():
        for trigger in triggers:
            if trigger.lower() in text_lower:
                logger.info(f"זוהתה כוונת ניהול הזמנות: {intent_type} - '{trigger}'")
                return True, intent_type
    
    # בדיקה אם יש מספר הזמנה בטקסט
    order_number_patterns = [
        r'הזמנה\s+(?:מספר\s+)?#?(\d+)',
        r'הזמנה\s+(?:מס[\'"]?\s+)?#?(\d+)',
        r'order\s+(?:number\s+)?#?(\d+)',
        r'order\s+(?:no[.]?\s+)?#?(\d+)',
        r'#(\d+)'
    ]
    
    for pattern in order_number_patterns:
        match = re.search(pattern, text_lower)
        if match:
            logger.info(f"זוהה מספר הזמנה: {match.group(1)}")
            return True, "get_order"
    
    # בדיקה אם יש אזכור של סטטוס הזמנה
    for status, keywords in ORDER_STATUSES.items():
        for keyword in keywords:
            if keyword in text_lower and "הזמנ" in text_lower:
                logger.info(f"זוהה אזכור של סטטוס הזמנה: {status}")
                return True, "update_order_status"
    
    return False, None

def extract_order_id(text: str) -> Optional[str]:
    """
    חילוץ מזהה הזמנה מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מזהה ההזמנה אם נמצא, אחרת None
    """
    # דפוסים אפשריים למספר הזמנה
    order_number_patterns = [
        r'הזמנה\s+(?:מספר\s+)?#?(\d+)',
        r'הזמנה\s+(?:מס[\'"]?\s+)?#?(\d+)',
        r'order\s+(?:number\s+)?#?(\d+)',
        r'order\s+(?:no[.]?\s+)?#?(\d+)',
        r'#(\d+)'
    ]
    
    for pattern in order_number_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_order_status(text: str) -> Optional[str]:
    """
    חילוץ סטטוס הזמנה מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        סטטוס ההזמנה אם נמצא, אחרת None
    """
    text_lower = text.lower()
    
    for status, keywords in ORDER_STATUSES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return status
    
    return None

def extract_date_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    חילוץ טווח תאריכים מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        טאפל עם: תאריך התחלה, תאריך סיום (אם נמצאו, אחרת None)
    """
    text_lower = text.lower()
    now = datetime.now()
    
    # בדיקת ביטויים נפוצים לטווחי זמן
    if any(term in text_lower for term in ["היום", "today"]):
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    elif any(term in text_lower for term in ["אתמול", "yesterday"]):
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    elif any(term in text_lower for term in ["השבוע", "this week"]):
        # מציאת תחילת השבוע (יום ראשון)
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    elif any(term in text_lower for term in ["החודש", "this month", "מהחודש", "from this month"]):
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # חישוב היום האחרון בחודש
        if now.month == 12:
            end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month+1, day=1) - timedelta(days=1)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date
    
    # חיפוש ביטויים של "מתאריך X עד תאריך Y" או "מ-X עד Y" בפורמט YYYY-MM-DD
    from_to_patterns_iso = [
        r'(?:מ|מתאריך|-)\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+(?:עד|ועד|ל|-)\s*(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(?:from|since)\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+(?:to|until)\s*(\d{4})-(\d{1,2})-(\d{1,2})'
    ]
    
    for pattern in from_to_patterns_iso:
        match = re.search(pattern, text)
        if match:
            try:
                year1, month1, day1 = int(match.group(1)), int(match.group(2)), int(match.group(3))
                year2, month2, day2 = int(match.group(4)), int(match.group(5)), int(match.group(6))
                
                start_date = datetime(year1, month1, day1, 0, 0, 0)
                end_date = datetime(year2, month2, day2, 23, 59, 59, 999999)
                return start_date, end_date
            except ValueError:
                continue
    
    # חיפוש תאריך בודד בפורמט YYYY-MM-DD
    iso_date_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    iso_dates = re.findall(iso_date_pattern, text)
    
    if iso_dates:
        try:
            # אם יש יותר מתאריך אחד, נניח שהראשון הוא תאריך התחלה והשני הוא תאריך סיום
            if len(iso_dates) >= 2:
                year1, month1, day1 = int(iso_dates[0][0]), int(iso_dates[0][1]), int(iso_dates[0][2])
                year2, month2, day2 = int(iso_dates[1][0]), int(iso_dates[1][1]), int(iso_dates[1][2])
                
                start_date = datetime(year1, month1, day1, 0, 0, 0)
                end_date = datetime(year2, month2, day2, 23, 59, 59, 999999)
                return start_date, end_date
            else:
                # אם יש רק תאריך אחד, נניח שזה תאריך התחלה
                year, month, day = int(iso_dates[0][0]), int(iso_dates[0][1]), int(iso_dates[0][2])
                
                start_date = datetime(year, month, day, 0, 0, 0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                return start_date, end_date
        except ValueError:
            pass
    
    # חיפוש תאריכים ספציפיים בפורמטים שונים
    date_patterns = [
        # פורמט DD/MM/YYYY או DD-MM-YYYY או DD.MM.YYYY
        r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})',
        # פורמט YYYY/MM/DD או YYYY-MM-DD או YYYY.MM.DD
        r'(\d{4})[\/\.-](\d{1,2})[\/\.-](\d{1,2})'
    ]
    
    for pattern in date_patterns:
        matches = list(re.finditer(pattern, text))
        dates = []
        
        for match in matches:
            if len(match.groups()) == 3:  # תאריך בודד
                if len(match.group(3)) == 4:  # פורמט DD/MM/YYYY
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                elif len(match.group(1)) == 4:  # פורמט YYYY/MM/DD
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                else:  # פורמט DD/MM/YY
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                
                try:
                    date = datetime(year, month, day)
                    dates.append(date)
                except ValueError:
                    continue
        
        if len(dates) == 1:
            # אם נמצא תאריך אחד, נניח שזה תאריך התחלה ונשתמש בתאריך הנוכחי כתאריך סיום
            start_date = dates[0].replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, end_date
        elif len(dates) >= 2:
            # אם נמצאו שני תאריכים או יותר, נניח שהראשון הוא תאריך התחלה והשני הוא תאריך סיום
            dates.sort()  # מיון התאריכים
            start_date = dates[0].replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = dates[1].replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, end_date
    
    # חיפוש ביטויים של "מתאריך X עד תאריך Y"
    from_to_patterns = [
        r'(?:מ|מתאריך)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})\s+(?:עד|ועד|ל)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})',
        r'(?:from|since)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})\s+(?:to|until)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})'
    ]
    
    for pattern in from_to_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                day1, month1, year1 = int(match.group(1)), int(match.group(2)), int(match.group(3))
                day2, month2, year2 = int(match.group(4)), int(match.group(5)), int(match.group(6))
                
                if year1 < 100:
                    year1 += 2000 if year1 < 50 else 1900
                if year2 < 100:
                    year2 += 2000 if year2 < 50 else 1900
                
                start_date = datetime(year1, month1, day1, 0, 0, 0)
                end_date = datetime(year2, month2, day2, 23, 59, 59, 999999)
                return start_date, end_date
            except ValueError:
                continue
    
    # חיפוש ביטויים של "מתאריך X" בלבד
    from_date_patterns = [
        r'(?:מ|מתאריך)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})',
        r'(?:from|since)\s+(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})'
    ]
    
    for pattern in from_date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                
                if year < 100:
                    year += 2000 if year < 50 else 1900
                
                start_date = datetime(year, month, day, 0, 0, 0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                return start_date, end_date
            except ValueError:
                continue
    
    # אם לא נמצאו תאריכים, נחזיר None
    return None, None

def extract_order_filters(text: str) -> Dict[str, Any]:
    """
    חילוץ פילטרים להזמנות מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מילון עם פילטרים להזמנות
    """
    filters = {}
    text_lower = text.lower()
    
    # חיפוש סטטוס הזמנה
    status_patterns = {
        "pending": ["ממתינות", "בהמתנה", "pending", "waiting"],
        "processing": ["בטיפול", "בעיבוד", "processing", "in progress"],
        "completed": ["הושלמו", "שהושלמו", "שהסתיימו", "completed", "finished"],
        "cancelled": ["שבוטלו", "מבוטלות", "cancelled", "canceled"],
        "refunded": ["שהוחזרו", "עם החזר", "refunded", "with refund"],
        "failed": ["שנכשלו", "כושלות", "failed", "unsuccessful"]
    }
    
    for status, keywords in status_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            filters["status"] = status
            break
    
    # חיפוש מזהה לקוח
    customer_id_pattern = r'לקוח\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)'
    customer_id_match = re.search(customer_id_pattern, text)
    if customer_id_match:
        filters["customer_id"] = customer_id_match.group(1)
    
    # חיפוש סכום הזמנה
    amount_patterns = [
        r'(?:בסכום|בעלות|במחיר|שעלו|שמחירן|שעלותן)\s+(?:של|)\s*([\d.,]+)',
        r'(?:יותר מ|מעל|גדול מ)\s*([\d.,]+)',
        r'(?:פחות מ|מתחת ל|קטן מ)\s*([\d.,]+)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1).replace(',', '.')
            try:
                amount = float(amount_str)
                if "מעל" in text or "יותר" in text or "גדול" in text:
                    filters["min_amount"] = amount
                elif "מתחת" in text or "פחות" in text or "קטן" in text:
                    filters["max_amount"] = amount
                else:
                    filters["amount"] = amount
                break
            except ValueError:
                pass
    
    return filters

def extract_order_data(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי הזמנה מטקסט חופשי
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מילון עם פרטי ההזמנה שחולצו
    """
    order_data = {}
    
    # חילוץ מזהה הזמנה
    order_id = extract_order_id(text)
    if order_id:
        order_data["id"] = order_id
    
    # ניסיון נוסף לחלץ מזהה הזמנה
    if "id" not in order_data:
        order_id_patterns = [
            r'הזמנה\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)',
            r'הזמנה\s+(?:id|מזהה)\s*[:]?\s*(\d+)',
            r'(?:מספר|מס[\'"]?|#)\s*(?:הזמנה)?\s*(\d+)',
            r'(?:id|מזהה)\s*(?:הזמנה)?\s*[:]?\s*(\d+)',
            r'(?:order)\s+(?:number|id|#)?\s*(\d+)',
            r'(?:number|id|#)\s*(?:order)?\s*(\d+)',
            r'(?:עדכן|שנה|בטל|החזר)\s+(?:את\s+)?(?:ה)?הזמנה\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)',
            r'(?:update|change|cancel|refund)\s+(?:the\s+)?order\s+(?:number|id|#)?\s*(\d+)'
        ]
        
        for pattern in order_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_data["id"] = match.group(1).strip()
                break
    
    # חילוץ סטטוס הזמנה
    order_status = extract_order_status(text)
    if order_status:
        order_data["status"] = order_status
    
    # חילוץ תאריכים
    date_from, date_to = extract_date_range(text)
    if date_from:
        order_data["date_created_from"] = date_from
    if date_to:
        order_data["date_created_to"] = date_to
    
    # חילוץ פרטי לקוח
    customer_patterns = {
        "customer_id": [
            r'לקוח\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)',
            r'(?:customer|user)\s+(?:id|number|#)?\s*(\d+)',
            r'(?:מזהה|id)\s+(?:לקוח|customer)\s*[:]?\s*(\d+)'
        ],
        "customer_name": [
            r'(?:לקוח|משתמש)\s+(?:בשם|ששמו|:)\s*([^,\.]+)',
            r'(?:customer|user)\s+(?:named|name|:)\s*([^,\.]+)',
            r'(?:שם|name)\s+(?:הלקוח|לקוח|customer)\s*[:]?\s*([^,\.]+)',
            r'(?:של|of)\s+(?:הלקוח|לקוח|customer)\s+([^,\.]+)',
            r'(?:הזמנות של|orders of|הזמנות|orders)\s+(?:הלקוח|לקוח|customer)?\s*([^,\.]+)'
        ],
        "customer_email": [
            r'(?:אימייל|מייל|דוא"ל)\s*(?:של הלקוח|:)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:email)\s*(?:of customer|:)?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ],
        "customer_phone": [
            r'(?:טלפון|נייד|מספר)\s*(?:של הלקוח|:)?\s*(0\d[\d-]{7,})',
            r'(?:phone|mobile|number)\s*(?:of customer|:)?\s*(0\d[\d-]{7,})',
            r'(0\d[\d-]{7,})'
        ]
    }
    
    for field, patterns in customer_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                order_data[field] = match.group(1).strip()
                break
    
    # חילוץ פרטי תשלום
    payment_patterns = {
        "payment_method": [
            r'(?:שולם|תשלום)\s+(?:באמצעות|דרך|ב|ע"י)\s+([^,\.]+)',
            r'(?:paid|payment)\s+(?:via|with|by|using)\s+([^,\.]+)',
            r'(?:אמצעי תשלום|payment method)\s*[:]?\s*([^,\.]+)',
            r'(?:שיטת תשלום|payment type)\s*[:]?\s*([^,\.]+)',
            r'(?:כרטיס אשראי|אשראי|מזומן|העברה בנקאית|פייפאל|credit card|cash|bank transfer|paypal)'
        ],
        "payment_status": [
            r'(?:סטטוס תשלום|מצב תשלום)\s*(?::|הוא|היא)?\s*([^,\.]+)',
            r'(?:payment status|payment state)\s*(?::|is)?\s*([^,\.]+)'
        ],
        "transaction_id": [
            r'(?:מזהה עסקה|מספר עסקה|מזהה תשלום)\s*(?::|הוא|היא)?\s*([^,\.]+)',
            r'(?:transaction id|transaction number|payment id)\s*(?::|is)?\s*([^,\.]+)'
        ]
    }
    
    for field, patterns in payment_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # בדיקה מיוחדת לאמצעי תשלום נפוצים
                if field == "payment_method" and pattern.startswith('(?:כרטיס אשראי'):
                    payment_methods = {
                        "credit_card": ["כרטיס אשראי", "אשראי", "credit card", "visa", "mastercard"],
                        "cash": ["מזומן", "cash"],
                        "bank_transfer": ["העברה בנקאית", "bank transfer"],
                        "paypal": ["פייפאל", "paypal"]
                    }
                    
                    for method, keywords in payment_methods.items():
                        if any(keyword in text.lower() for keyword in keywords):
                            order_data[field] = method
                            break
                else:
                    order_data[field] = match.group(1).strip()
                break
    
    # חילוץ פרטי משלוח
    shipping_patterns = {
        "shipping_method": [
            r'(?:משלוח|שילוח)\s+(?:באמצעות|דרך|ב|ע"י)\s+([^,\.]+)',
            r'(?:shipping|delivery)\s+(?:via|with|by|using)\s+([^,\.]+)',
            r'(?:שיטת משלוח|shipping method)\s*[:]?\s*([^,\.]+)',
            r'(?:אופן משלוח|delivery method)\s*[:]?\s*([^,\.]+)',
            r'(?:דואר רשום|שליח|איסוף עצמי|registered mail|courier|pickup)'
        ],
        "shipping_address": [
            r'(?:כתובת למשלוח|כתובת משלוח)\s*(?::|היא|הוא)?\s*([^,\.]+)',
            r'(?:shipping address|delivery address)\s*(?::|is)?\s*([^,\.]+)'
        ],
        "tracking_number": [
            r'(?:מספר מעקב|מספר משלוח)\s*(?::|הוא|היא)?\s*([^,\.]+)',
            r'(?:tracking number|tracking id|shipping number)\s*(?::|is)?\s*([^,\.]+)',
            r'(?:מספר המעקב|the tracking number)\s*(?:הוא|is)?\s*([^,\.]+)'
        ]
    }
    
    for field, patterns in shipping_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # בדיקה מיוחדת לשיטות משלוח נפוצות
                if field == "shipping_method" and pattern.startswith('(?:דואר רשום'):
                    shipping_methods = {
                        "registered_mail": ["דואר רשום", "registered mail"],
                        "courier": ["שליח", "courier", "שליח עד הבית", "home delivery"],
                        "pickup": ["איסוף עצמי", "pickup", "self pickup", "collection"]
                    }
                    
                    for method, keywords in shipping_methods.items():
                        if any(keyword in text.lower() for keyword in keywords):
                            order_data[field] = method
                            break
                else:
                    order_data[field] = match.group(1).strip()
                break
    
    # חילוץ הערות
    note_patterns = [
        r'(?:הערות|הערה)\s*(?::|הן|היא)?\s*([^,\.]+)',
        r'(?:notes|note)\s*(?::|are|is)?\s*([^,\.]+)'
    ]
    
    for pattern in note_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            order_data["customer_note"] = match.group(1).strip()
            break
    
    # חילוץ פריטים בהזמנה
    items_patterns = [
        r'(?:מוצרים|פריטים|items|products):\s*(.+?)(?:$|\.)',
        r'(?:הזמנה של|order of|ordered):\s*(.+?)(?:$|\.)'
    ]
    
    for pattern in items_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            items_text = match.group(1).strip()
            items = []
            
            # חיפוש פריטים בפורמט "שם מוצר (כמות)"
            item_matches = re.finditer(r'([^,(]+)\s*\((\d+)[^\)]*\)', items_text)
            for item_match in item_matches:
                product_name = item_match.group(1).strip()
                quantity = int(item_match.group(2))
                items.append({"product_name": product_name, "quantity": quantity})
            
            # אם לא נמצאו פריטים בפורמט הקודם, ננסה לפצל לפי פסיקים
            if not items:
                item_parts = items_text.split(',')
                for part in item_parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # ניסיון לחלץ כמות
                    quantity_match = re.search(r'(\d+)\s*(?:יחידות|יח\'|יח"|units|pcs)', part)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        product_name = re.sub(r'\d+\s*(?:יחידות|יח\'|יח"|units|pcs)', '', part).strip()
                    else:
                        quantity = 1
                        product_name = part
                    
                    items.append({"product_name": product_name, "quantity": quantity})
            
            if items:
                order_data["line_items"] = items
            break
    
    return order_data

def generate_order_management_questions(intent_type: str, missing_info: List[str]) -> List[str]:
    """
    יצירת שאלות להשלמת מידע חסר לניהול הזמנות
    
    Args:
        intent_type: סוג הכוונה
        missing_info: רשימת פרטים חסרים
        
    Returns:
        רשימה של שאלות להשלמת המידע
    """
    questions = []
    
    if intent_type == "get_order" and "order_id" in missing_info:
        questions.append("מהו מספר ההזמנה שברצונך לצפות בה?")
    
    elif intent_type == "update_order_status":
        if "order_id" in missing_info:
            questions.append("מהו מספר ההזמנה שברצונך לעדכן?")
        if "status" in missing_info:
            questions.append("מהו הסטטוס החדש שברצונך להגדיר? (לדוגמה: בטיפול, נשלח, הושלם, בוטל)")
    
    elif intent_type == "cancel_order" and "order_id" in missing_info:
        questions.append("מהו מספר ההזמנה שברצונך לבטל?")
    
    elif intent_type == "refund_order":
        if "order_id" in missing_info:
            questions.append("מהו מספר ההזמנה שברצונך לבצע עבורה החזר כספי?")
        if "amount" in missing_info:
            questions.append("מהו הסכום שברצונך להחזיר? (השאר ריק להחזר מלא)")
    
    elif intent_type == "contact_customer":
        if "order_id" in missing_info:
            questions.append("מהו מספר ההזמנה שהלקוח שלה ברצונך ליצור קשר?")
        if "message" in missing_info:
            questions.append("מהי ההודעה שברצונך לשלוח ללקוח?")
    
    elif intent_type == "get_orders":
        if "status" in missing_info:
            questions.append("איזה סטטוס של הזמנות ברצונך לראות? (לדוגמה: ממתין, בטיפול, הושלם, בוטל)")
        if "date_range" in missing_info:
            questions.append("מאיזה טווח זמן ברצונך לראות הזמנות? (לדוגמה: היום, השבוע, החודש)")
    
    return questions
