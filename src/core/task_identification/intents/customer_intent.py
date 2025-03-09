"""
מודול לזיהוי כוונות ניהול לקוחות בשפה טבעית
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set, TYPE_CHECKING
import json
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from ..models import TaskContext, IntentRecognitionResult

logger = logging.getLogger(__name__)

# ביטויים וטריגרים לזיהוי בקשות לניהול לקוחות
CUSTOMER_MANAGEMENT_TRIGGERS = {
    # ביטויים לקבלת מידע על לקוחות
    "get_customers": [
        "הצג לקוחות", "רשימת לקוחות", "לקוחות אחרונים", "כל הלקוחות", "לקוחות שלי",
        "לקוחות חדשים", "לקוחות פעילים", "לקוחות לא פעילים", "לקוחות מועדפים",
        "show customers", "list customers", "recent customers", "all customers", "my customers",
        "new customers", "active customers", "inactive customers", "preferred customers"
    ],
    
    # ביטויים לקבלת מידע על לקוח ספציפי
    "get_customer": [
        "הצג לקוח", "פרטי לקוח", "מידע על לקוח", "סטטוס לקוח", "מצב לקוח",
        "לקוח מספר", "מה קורה עם לקוח", "איפה לקוח", "מתי לקוח", "תאריך לקוח",
        "show customer", "customer details", "customer info", "customer status", "customer state",
        "customer number", "what's happening with customer", "where is customer", "when customer", "customer date"
    ],
    
    # ביטויים ליצירת לקוח חדש
    "create_customer": [
        "צור לקוח", "הוסף לקוח", "יצירת לקוח", "הוספת לקוח", "להוסיף לקוח", "ליצור לקוח",
        "רוצה להוסיף לקוח", "אני רוצה ליצור לקוח", "אפשר להוסיף לקוח", "אפשר ליצור לקוח",
        "create customer", "add customer", "new customer", "create a customer", "add a customer",
        "איך אני מוסיף לקוח", "איך מוסיפים לקוח", "איך יוצרים לקוח", "איך אני יוצר לקוח"
    ],
    
    # ביטויים לעדכון לקוח
    "update_customer": [
        "עדכן לקוח", "שנה לקוח", "עדכון לקוח", "שינוי לקוח", "לעדכן לקוח", "לשנות לקוח",
        "רוצה לעדכן לקוח", "אני רוצה לשנות לקוח", "אפשר לעדכן לקוח", "אפשר לשנות לקוח",
        "update customer", "change customer", "modify customer", "edit customer", "update a customer",
        "איך אני מעדכן לקוח", "איך מעדכנים לקוח", "איך משנים לקוח", "איך אני משנה לקוח"
    ],
    
    # ביטויים למחיקת לקוח
    "delete_customer": [
        "מחק לקוח", "הסר לקוח", "מחיקת לקוח", "הסרת לקוח", "למחוק לקוח", "להסיר לקוח",
        "רוצה למחוק לקוח", "אני רוצה להסיר לקוח", "אפשר למחוק לקוח", "אפשר להסיר לקוח",
        "delete customer", "remove customer", "delete a customer", "remove a customer",
        "איך אני מוחק לקוח", "איך מוחקים לקוח", "איך מסירים לקוח", "איך אני מסיר לקוח"
    ]
}

# שדות לקוח אפשריים שניתן לחלץ מטקסט
CUSTOMER_FIELDS = {
    "first_name": ["שם פרטי", "שם", "first name", "name"],
    "last_name": ["שם משפחה", "משפחה", "last name", "surname", "family name"],
    "email": ["אימייל", "מייל", "דוא\"ל", "email", "e-mail"],
    "phone": ["טלפון", "נייד", "מספר טלפון", "phone", "mobile", "phone number"],
    "address": ["כתובת", "מען", "address", "location"],
    "city": ["עיר", "ישוב", "city", "town"],
    "state": ["מדינה", "מחוז", "state", "province", "region"],
    "postcode": ["מיקוד", "zip", "postal code", "postcode"],
    "country": ["ארץ", "מדינה", "country", "nation"]
}

def is_customer_management_intent(text: str) -> Tuple[bool, Optional[str]]:
    """
    בדיקה אם הטקסט מכיל כוונת ניהול לקוחות
    
    Args:
        text: הטקסט לבדיקה
        
    Returns:
        טאפל עם: האם זוהתה כוונת ניהול לקוחות, וסוג הכוונה הספציפית (אם זוהתה)
    """
    text_lower = text.lower()
    
    # בדיקת כל סוגי הכוונות
    for intent_type, triggers in CUSTOMER_MANAGEMENT_TRIGGERS.items():
        for trigger in triggers:
            if trigger.lower() in text_lower:
                return True, intent_type
    
    return False, None

def extract_customer_id(text: str) -> Optional[str]:
    """
    חילוץ מזהה לקוח מטקסט
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מזהה הלקוח אם נמצא, אחרת None
    """
    # דפוסים אפשריים למזהה לקוח
    patterns = [
        r'לקוח\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)',
        r'(?:customer|user)\s+(?:id|number|#)?\s*(\d+)',
        r'(?:id|מספר)\s+(?:לקוח|customer)?\s*[:#]?\s*(\d+)',
        r'#(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_customer_data(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי לקוח מטקסט חופשי
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מילון עם פרטי הלקוח שחולצו
    """
    customer_data = {}
    text_lines = text.split('\n')
    
    # חילוץ מזהה לקוח
    customer_id = extract_customer_id(text)
    if customer_id:
        customer_data["id"] = customer_id
    
    # חיפוש שדות לקוח בכל שורה
    for line in text_lines:
        line = line.strip()
        if not line:
            continue
        
        # חיפוש שדות לקוח
        for field, keywords in CUSTOMER_FIELDS.items():
            for keyword in keywords:
                # חיפוש דפוס של "מילת_מפתח: ערך" או "מילת_מפתח - ערך"
                patterns = [
                    f"{keyword}[:]\\s*(.+?)(?:,|$|\\n)",
                    f"{keyword}\\s*[-]\\s*(.+?)(?:,|$|\\n)",
                    f"{keyword}\\s+(.+?)(?:,|$|\\n)"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if field not in customer_data and value:
                            customer_data[field] = value
                            break
    
    # חיפוש מתקדם יותר בכל הטקסט (לא רק לפי שורות)
    
    # חיפוש שם מלא ופיצול לשם פרטי ושם משפחה
    if "first_name" not in customer_data or "last_name" not in customer_data:
        # חיפוש שם מלא בפורמטים שונים
        full_name_patterns = [
            r'(?:שם מלא|שם הלקוח|full name|customer name|שם|name)[\s:]+([^\n,.]+)',
            r'(?:לקוח בשם|customer named|בשם|named)[\s:]+([^\n,.]+)',
            r'(?:לקוח חדש בשם|new customer named|לקוח חדש|new customer)[\s:]+([^\n,.]+)',
            r'(?:עבור|for)\s+([^\n,.]+)',
            r'(?:של|of)\s+([^\n,.]+)',
            r'(?:ל|to)\s+([^\n,.]+)'
        ]
        
        for pattern in full_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_name = match.group(1).strip()
                # בדיקה אם השם מכיל מילים שאינן חלק מהשם
                ignore_words = ['לקוח', 'customer', 'חדש', 'new', 'את', 'the', 'עבור', 'for', 'של', 'of']
                for word in ignore_words:
                    full_name = re.sub(r'\b' + word + r'\b', '', full_name, flags=re.IGNORECASE).strip()
                
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    customer_data["first_name"] = name_parts[0]
                    customer_data["last_name"] = " ".join(name_parts[1:])
                elif len(name_parts) == 1:
                    customer_data["first_name"] = name_parts[0]
                break
    
    # חיפוש ישיר של שם פרטי ושם משפחה
    if "first_name" not in customer_data:
        first_name_patterns = [
            r'(?:שם פרטי|first name)[\s:]+([^\n,.]+)',
            r'(?:פרטי|first)[\s:]+([^\n,.]+)'
        ]
        
        for pattern in first_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                customer_data["first_name"] = match.group(1).strip()
                break
    
    if "last_name" not in customer_data:
        last_name_patterns = [
            r'(?:שם משפחה|last name|surname|family name)[\s:]+([^\n,.]+)',
            r'(?:משפחה|last|surname|family)[\s:]+([^\n,.]+)'
        ]
        
        for pattern in last_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                customer_data["last_name"] = match.group(1).strip()
                break
    
    # חיפוש שם לקוח בפורמט "שם פרטי שם משפחה"
    if "first_name" not in customer_data and "last_name" not in customer_data:
        name_patterns = [
            r'(?:לקוח|customer)\s+(?:חדש|new)?\s*(?:בשם|named)?\s*([א-ת\w]+)\s+([א-ת\w]+)',
            r'(?:צור|הוסף|create|add)\s+(?:לקוח|customer)\s+(?:חדש|new)?\s+(?:בשם|named)?\s*([א-ת\w]+)\s+([א-ת\w]+)',
            r'(?:עדכן|שנה|update|change)\s+(?:את\s+)?(?:ה)?(?:לקוח|customer)\s+([א-ת\w]+)\s+([א-ת\w]+)',
            r'(?:הלקוח|the customer)\s+([א-ת\w]+)\s+([א-ת\w]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                customer_data["first_name"] = match.group(1).strip()
                customer_data["last_name"] = match.group(2).strip()
                break
    
    # חיפוש אימייל
    if "email" not in customer_data:
        email_patterns = [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:אימייל|מייל|דוא"ל|email|e-mail)[\s:]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                customer_data["email"] = match.group(1).strip()
                break
    
    # חיפוש מספר טלפון
    if "phone" not in customer_data:
        phone_patterns = [
            r'(?:טלפון|נייד|מספר טלפון|phone|mobile|phone number)[\s:]+(\+?[\d\s\-\(\)]{7,})',
            r'(\+?[\d\s\-\(\)]{7,})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phone = match.group(1).strip()
                # ניקוי מספר הטלפון מתווים מיותרים
                phone = re.sub(r'[\s\-\(\)]', '', phone)
                customer_data["phone"] = phone
                break
    
    # חיפוש כתובת
    address_fields = ["address_1", "city", "state", "postcode", "country"]
    if not any(field in customer_data for field in address_fields):
        # חיפוש כתובת מלאה
        address_patterns = [
            r'(?:כתובת|מען|address|location)[\s:]+(.+?)(?:,|$|\n)',
            r'(?:רחוב|street)[\s:]+(.+?)(?:,|$|\n)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                customer_data["address_1"] = address
                break
        
        # חיפוש עיר
        city_patterns = [
            r'(?:עיר|ישוב|city|town)[\s:]+([^\d,]+?)(?:,|$|\n)',
            r',\s*([^\d,]+?)(?:,|$|\n)'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                customer_data["city"] = city
                break
        
        # חיפוש מיקוד
        postcode_patterns = [
            r'(?:מיקוד|zip|postal code|postcode)[\s:]+(\d{5,7})',
            r'(\d{5,7})'
        ]
        
        for pattern in postcode_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                postcode = match.group(1).strip()
                customer_data["postcode"] = postcode
                break
    
    # ארגון נתוני כתובת במבנה המתאים ל-WooCommerce
    address_fields = ["address_1", "city", "state", "postcode", "country"]
    if any(field in customer_data for field in address_fields):
        billing = {}
        shipping = {}
        
        for field in address_fields:
            if field in customer_data:
                billing[field] = customer_data[field]
                shipping[field] = customer_data[field]
                del customer_data[field]
        
        if billing:
            customer_data["billing"] = billing
        if shipping:
            customer_data["shipping"] = shipping
    
    return customer_data

def generate_customer_management_questions(intent_type: str, missing_info: List[str]) -> List[str]:
    """
    יצירת שאלות המשך בהתאם לסוג הכוונה ולמידע החסר
    
    Args:
        intent_type: סוג הכוונה
        missing_info: רשימת שדות חסרים
        
    Returns:
        רשימת שאלות המשך
    """
    questions = []
    
    if intent_type in ["create_customer", "update_customer"]:
        field_questions = {
            "first_name": ["מה השם הפרטי של הלקוח?", "What is the customer's first name?"],
            "last_name": ["מה שם המשפחה של הלקוח?", "What is the customer's last name?"],
            "email": ["מה כתובת האימייל של הלקוח?", "What is the customer's email address?"],
            "phone": ["מה מספר הטלפון של הלקוח?", "What is the customer's phone number?"],
            "address": ["מה הכתובת של הלקוח?", "What is the customer's address?"],
            "city": ["באיזו עיר גר הלקוח?", "In which city does the customer live?"],
            "postcode": ["מה המיקוד של הלקוח?", "What is the customer's postal code?"]
        }
        
        for field in missing_info:
            if field in field_questions:
                questions.extend(field_questions[field])
    
    elif intent_type in ["get_customer", "delete_customer"]:
        if "id" in missing_info:
            questions.append("מה מספר הלקוח שאתה מחפש?")
            questions.append("What is the customer ID you are looking for?")
        elif "email" in missing_info:
            questions.append("מה כתובת האימייל של הלקוח?")
            questions.append("What is the customer's email address?")
    
    return questions 

async def identify_customer_intent(
    message: str,
    context: Optional["TaskContext"] = None
) -> Optional["IntentRecognitionResult"]:
    """
    זיהוי כוונות הקשורות ללקוחות בהודעת המשתמש
    
    Args:
        message: הודעת המשתמש
        context: הקשר המשימה (אופציונלי)
        
    Returns:
        תוצאות זיהוי הכוונה, או None אם לא זוהתה כוונה
    """
    from ..models import IntentRecognitionResult
    
    # בדיקה אם יש כוונת ניהול לקוחות
    is_intent, intent_type = is_customer_management_intent(message)
    
    if not is_intent:
        return None
    
    # טיפול בכוונות שונות
    if intent_type == "get_customer":
        # חילוץ מזהה לקוח
        customer_id = extract_customer_id(message)
        customer_data = extract_customer_data(message)
        
        missing_info = []
        if not customer_id and not any(key in customer_data for key in ["email", "phone", "name"]):
            missing_info.append("customer_id")
        
        return IntentRecognitionResult(
            intent_type=intent_type,
            confidence=0.85,
            params={
                "customer_id": customer_id,
                "customer_data": customer_data,
                "missing_info": missing_info,
                "questions": generate_customer_management_questions(intent_type, missing_info)
            },
            source="customer_intent"
        )
    
    elif intent_type == "get_customers":
        # אין צורך במידע נוסף לרוב
        return IntentRecognitionResult(
            intent_type=intent_type,
            confidence=0.8,
            params={
                "filters": {},
                "missing_info": [],
                "questions": []
            },
            source="customer_intent"
        )
    
    elif intent_type == "create_customer":
        # חילוץ נתוני לקוח
        customer_data = extract_customer_data(message)
        
        # בדיקת שדות חובה
        required_fields = ["name", "email", "phone"]
        missing_info = [field for field in required_fields if field not in customer_data]
        
        return IntentRecognitionResult(
            intent_type=intent_type,
            confidence=0.9,
            params={
                "customer_data": customer_data,
                "missing_info": missing_info,
                "questions": generate_customer_management_questions(intent_type, missing_info)
            },
            source="customer_intent"
        )
    
    elif intent_type == "update_customer":
        # חילוץ מזהה לקוח ונתונים לעדכון
        customer_id = extract_customer_id(message)
        customer_data = extract_customer_data(message)
        
        missing_info = []
        if not customer_id:
            missing_info.append("customer_id")
        if not customer_data:
            missing_info.append("update_data")
        
        return IntentRecognitionResult(
            intent_type=intent_type,
            confidence=0.85,
            params={
                "customer_id": customer_id,
                "customer_data": customer_data,
                "missing_info": missing_info,
                "questions": generate_customer_management_questions(intent_type, missing_info)
            },
            source="customer_intent"
        )
    
    elif intent_type == "delete_customer":
        # חילוץ מזהה לקוח
        customer_id = extract_customer_id(message)
        missing_info = [] if customer_id else ["customer_id"]
        
        return IntentRecognitionResult(
            intent_type=intent_type,
            confidence=0.85,
            params={
                "customer_id": customer_id,
                "missing_info": missing_info,
                "questions": generate_customer_management_questions(intent_type, missing_info)
            },
            source="customer_intent"
        )
    
    # אם הגענו לכאן, זוהתה כוונה אבל לא טופלה בצורה ספציפית
    return IntentRecognitionResult(
        intent_type="customer_management",
        confidence=0.6,
        params={},
        source="customer_intent"
    )