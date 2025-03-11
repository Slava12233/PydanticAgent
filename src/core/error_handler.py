"""
מודול לטיפול בשגיאות ואי-הבנות

מודול זה מכיל פונקציות לטיפול במקרים של אי-הבנה, שגיאות API, ובקשות הבהרה.
"""
import logging
import re
import random
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools.managers.response_generator import generate_natural_response, get_emoji

logger = logging.getLogger(__name__)

# סוגי שגיאות
class ErrorType:
    """סוגי שגיאות שהמערכת יכולה לטפל בהן"""
    MISUNDERSTANDING = "misunderstanding"  # אי-הבנה של הבקשה
    API_ERROR = "api_error"  # שגיאת API (ווקומרס, OpenAI, וכו')
    QUOTA_ERROR = "quota_error"  # שגיאת מכסה (לדוגמה, מכסת API של OpenAI)
    TIMEOUT_ERROR = "timeout_error"  # שגיאת זמן (לדוגמה, בקשה שלקחה יותר מדי זמן)
    CONTENT_FILTER = "content_filter"  # שגיאת סינון תוכן (לדוגמה, תוכן לא הולם)
    PERMISSION_ERROR = "permission_error"  # שגיאת הרשאות
    CONNECTION_ERROR = "connection_error"  # שגיאת חיבור
    VALIDATION_ERROR = "validation_error"  # שגיאת אימות נתונים
    GENERAL_ERROR = "general_error"  # שגיאה כללית

# תבניות תשובה לסוגי שגיאות שונים
ERROR_TEMPLATES = {
    ErrorType.MISUNDERSTANDING: [
        "לא בטוח שהבנתי את הבקשה שלך. אפשר לנסח אותה בצורה אחרת?",
        "אני מתקשה להבין למה התכוונת. אפשר להסביר בצורה אחרת?",
        "לא הצלחתי לפענח את הבקשה. אפשר לפרט יותר?",
        "אני לא בטוח שהבנתי נכון. האם תוכל להסביר שוב?",
        "אני מתנצל, אבל לא הצלחתי להבין את הבקשה. אפשר לנסח אותה אחרת?"
    ],
    ErrorType.API_ERROR: [
        "אירעה שגיאה בחיבור לשירות החיצוני. אפשר לנסות שוב בעוד מספר דקות.",
        "נתקלתי בבעיה בתקשורת עם השירות החיצוני. אפשר לנסות שוב מאוחר יותר.",
        "יש בעיה זמנית בחיבור לשירות. אנא נסה שוב בעוד מספר דקות.",
        "לא הצלחתי להתחבר לשירות החיצוני. אפשר לנסות שוב בקרוב."
    ],
    ErrorType.QUOTA_ERROR: [
        "הגעת למגבלת השימוש היומית. אנא נסה שוב מחר.",
        "חרגת ממכסת השימוש. המערכת תתאפס בעוד מספר שעות.",
        "הגעת למגבלת השימוש המותרת. אנא המתן מספר שעות ונסה שוב.",
        "מכסת השימוש שלך הסתיימה. המערכת תתאפס בחצות."
    ],
    ErrorType.TIMEOUT_ERROR: [
        "הבקשה לקחה יותר מדי זמן. אפשר לנסות שוב עם בקשה פשוטה יותר?",
        "הפעולה ארכה זמן רב מדי. אפשר לחלק אותה למספר בקשות קטנות יותר?",
        "חל פסק זמן בעיבוד הבקשה. אפשר לנסות שוב עם בקשה קצרה יותר?",
        "הבקשה מורכבת מדי ולקחה יותר מדי זמן. אפשר לפשט אותה?"
    ],
    ErrorType.CONTENT_FILTER: [
        "הבקשה שלך מכילה תוכן שאינו מתאים למדיניות שלנו. אנא נסח אותה מחדש.",
        "לא אוכל לענות על שאלה זו בגלל מדיניות התוכן שלנו. אפשר לשאול משהו אחר?",
        "הבקשה נחסמה על ידי מסנן התוכן שלנו. אנא נסח אותה בצורה אחרת.",
        "אני מתנצל, אך איני יכול לענות על שאלה זו בגלל הגבלות תוכן."
    ],
    ErrorType.PERMISSION_ERROR: [
        "אין לך הרשאות מספיקות לביצוע פעולה זו.",
        "פעולה זו דורשת הרשאות גבוהות יותר.",
        "אינך מורשה לבצע פעולה זו. אנא פנה למנהל המערכת.",
        "אין לך גישה לפעולה זו. נדרשות הרשאות נוספות."
    ],
    ErrorType.CONNECTION_ERROR: [
        "יש בעיה בחיבור לשרת. אנא בדוק את החיבור שלך ונסה שוב.",
        "לא הצלחתי להתחבר לשרת. אפשר לנסות שוב בעוד מספר דקות?",
        "החיבור לשרת נכשל. אנא ודא שיש לך חיבור אינטרנט יציב ונסה שוב.",
        "יש בעיה בתקשורת עם השרת. אנא נסה שוב מאוחר יותר."
    ],
    ErrorType.VALIDATION_ERROR: [
        "הנתונים שהזנת אינם תקינים. אנא בדוק אותם ונסה שוב.",
        "יש שגיאה באחד או יותר מהשדות שהזנת. אנא תקן ונסה שוב.",
        "הפרטים שהזנת אינם עומדים בדרישות המערכת. אנא בדוק ונסה שוב.",
        "לא ניתן לעבד את הבקשה בגלל נתונים לא תקינים. אנא בדוק את הפרטים ונסה שוב."
    ],
    ErrorType.GENERAL_ERROR: [
        "אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב.",
        "משהו השתבש. אפשר לנסות שוב בעוד מספר דקות?",
        "אירעה שגיאה לא צפויה. אנא נסה שוב מאוחר יותר.",
        "המערכת נתקלה בבעיה. אנא נסה שוב בקרוב."
    ]
}

# הצעות לניסוח מחדש של שאלות
REPHRASE_SUGGESTIONS = [
    "אפשר לנסות לשאול: \"{suggestion}\"",
    "אולי תנסה לשאול: \"{suggestion}\"",
    "ניתן לנסח את השאלה כך: \"{suggestion}\"",
    "דוגמה לשאלה דומה: \"{suggestion}\""
]

# שאלות דומות נפוצות לפי קטגוריות
SIMILAR_QUESTIONS = {
    "product_management": [
        "הצג לי את כל המוצרים בחנות",
        "איך אני יוצר מוצר חדש?",
        "עדכן את המחיר של המוצר X ל-Y ש\"ח",
        "כמה יחידות נשארו במלאי מהמוצר X?"
    ],
    "order_management": [
        "הצג לי את ההזמנות האחרונות",
        "מה הסטטוס של הזמנה מספר X?",
        "עדכן את הסטטוס של הזמנה X ל-Y",
        "כמה הזמנות התקבלו השבוע?"
    ],
    "customer_management": [
        "הצג לי את רשימת הלקוחות",
        "מי הלקוח שהזמין הכי הרבה החודש?",
        "הוסף לקוח חדש",
        "מה פרטי הקשר של הלקוח X?"
    ],
    "general": [
        "מה אתה יכול לעשות?",
        "איך אני מחבר את החנות שלי?",
        "הצג לי את הסטטיסטיקות של החנות",
        "איך אני משנה את ההגדרות?"
    ]
}

async def handle_misunderstanding(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    session: AsyncSession,
    original_text: str,
    category: str = "general"
) -> str:
    """
    טיפול במקרים של אי-הבנה
    
    Args:
        update: אובייקט העדכון מטלגרם
        context: אובייקט הקונטקסט מטלגרם
        session: מושב מסד הנתונים
        original_text: הטקסט המקורי שלא הובן
        category: קטגוריה לשאלות דומות (product_management, order_management, וכו')
        
    Returns:
        תשובה טבעית למקרה של אי-הבנה
    """
    logger.info(f"טיפול באי-הבנה: '{original_text}'")
    
    # בחירת תבנית תשובה אקראית
    response_template = random.choice(ERROR_TEMPLATES[ErrorType.MISUNDERSTANDING])
    
    # בחירת שאלות דומות מהקטגוריה המתאימה
    similar_questions = SIMILAR_QUESTIONS.get(category, SIMILAR_QUESTIONS["general"])
    selected_questions = random.sample(similar_questions, min(2, len(similar_questions)))
    
    # הוספת הצעות לניסוח מחדש
    suggestions = []
    for question in selected_questions:
        suggestion_template = random.choice(REPHRASE_SUGGESTIONS)
        suggestions.append(suggestion_template.format(suggestion=question))
    
    # בניית התשובה המלאה
    response = f"{get_emoji('error')} {response_template}\n\n"
    response += "💡 הנה כמה הצעות:\n"
    response += "\n".join(suggestions)
    
    return response

async def handle_api_error(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    session: AsyncSession,
    error_details: Dict[str, Any],
    error_type: str = ErrorType.API_ERROR
) -> str:
    """
    טיפול בשגיאות API
    
    Args:
        update: אובייקט העדכון מטלגרם
        context: אובייקט הקונטקסט מטלגרם
        session: מושב מסד הנתונים
        error_details: פרטי השגיאה
        error_type: סוג השגיאה
        
    Returns:
        תשובה טבעית למקרה של שגיאת API
    """
    logger.error(f"שגיאת API: {error_details}")
    
    # בחירת תבנית תשובה מתאימה לסוג השגיאה
    if error_type in ERROR_TEMPLATES:
        response_template = random.choice(ERROR_TEMPLATES[error_type])
    else:
        response_template = random.choice(ERROR_TEMPLATES[ErrorType.GENERAL_ERROR])
    
    # הוספת פרטי שגיאה אם יש
    error_message = error_details.get("message", "")
    if error_message:
        response = f"{get_emoji('error')} {response_template}\n\nפרטי השגיאה: {error_message}"
    else:
        response = f"{get_emoji('error')} {response_template}"
    
    return response

async def generate_clarification_questions(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    session: AsyncSession,
    original_text: str,
    missing_info: List[str]
) -> str:
    """
    יצירת שאלות הבהרה כאשר חסר מידע
    
    Args:
        update: אובייקט העדכון מטלגרם
        context: אובייקט הקונטקסט מטלגרם
        session: מושב מסד הנתונים
        original_text: הטקסט המקורי
        missing_info: רשימת פרטי מידע חסרים
        
    Returns:
        תשובה עם שאלות הבהרה
    """
    logger.info(f"יצירת שאלות הבהרה. טקסט מקורי: '{original_text}', מידע חסר: {missing_info}")
    
    # תבניות לשאלות הבהרה
    clarification_templates = {
        "product_name": [
            "מה שם המוצר?",
            "איך קוראים למוצר?",
            "מהו שם המוצר שאתה מחפש?"
        ],
        "product_id": [
            "מה המזהה של המוצר?",
            "מהו מספר המוצר?",
            "איזה מזהה יש למוצר?"
        ],
        "order_id": [
            "מה מספר ההזמנה?",
            "מהו מזהה ההזמנה?",
            "איזו הזמנה אתה מחפש?"
        ],
        "customer_id": [
            "מי הלקוח?",
            "מהו מזהה הלקוח?",
            "לאיזה לקוח אתה מתכוון?"
        ],
        "date_range": [
            "לאיזה טווח תאריכים?",
            "מאיזה תאריך עד איזה תאריך?",
            "לאיזו תקופה אתה מתכוון?"
        ],
        "price": [
            "מה המחיר?",
            "כמה זה עולה?",
            "מהו המחיר שאתה רוצה להגדיר?"
        ],
        "quantity": [
            "מה הכמות?",
            "כמה יחידות?",
            "איזו כמות אתה רוצה?"
        ],
        "status": [
            "מה הסטטוס?",
            "לאיזה סטטוס לשנות?",
            "מהו הסטטוס הרצוי?"
        ]
    }
    
    # יצירת שאלות הבהרה לכל פריט מידע חסר
    questions = []
    for info in missing_info:
        if info in clarification_templates:
            questions.append(random.choice(clarification_templates[info]))
        else:
            questions.append(f"אנא ספק מידע נוסף על {info}")
    
    # בניית התשובה המלאה
    response = f"{get_emoji('question')} אני צריך מידע נוסף כדי לענות על השאלה שלך:\n\n"
    response += "\n".join([f"• {q}" for q in questions])
    
    return response

async def suggest_similar_intents(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    session: AsyncSession,
    original_text: str,
    similar_intents: List[Tuple[str, str, float]]
) -> str:
    """
    הצעת כוונות דומות כאשר הכוונה לא ברורה
    
    Args:
        update: אובייקט העדכון מטלגרם
        context: אובייקט הקונטקסט מטלגרם
        session: מושב מסד הנתונים
        original_text: הטקסט המקורי
        similar_intents: רשימת כוונות דומות (טאפלים של סוג משימה, סוג כוונה, ציון)
        
    Returns:
        תשובה עם הצעות לכוונות דומות
    """
    logger.info(f"הצעת כוונות דומות. טקסט מקורי: '{original_text}', כוונות דומות: {similar_intents}")
    
    # מילון תיאורים לכוונות
    intent_descriptions = {
        ("product_management", "list_products"): "הצגת רשימת מוצרים",
        ("product_management", "get_product"): "הצגת פרטי מוצר",
        ("product_management", "create_product"): "יצירת מוצר חדש",
        ("product_management", "update_product"): "עדכון מוצר קיים",
        ("product_management", "delete_product"): "מחיקת מוצר",
        
        ("order_management", "get_orders"): "הצגת רשימת הזמנות",
        ("order_management", "get_order"): "הצגת פרטי הזמנה",
        ("order_management", "update_order_status"): "עדכון סטטוס הזמנה",
        ("order_management", "cancel_order"): "ביטול הזמנה",
        ("order_management", "refund_order"): "ביצוע החזר כספי",
        
        ("customer_management", "get_customers"): "הצגת רשימת לקוחות",
        ("customer_management", "get_customer"): "הצגת פרטי לקוח",
        ("customer_management", "create_customer"): "יצירת לקוח חדש",
        ("customer_management", "update_customer"): "עדכון פרטי לקוח",
        ("customer_management", "delete_customer"): "מחיקת לקוח"
    }
    
    # יצירת הצעות לכוונות דומות
    suggestions = []
    for task_type, intent_type, score in similar_intents:
        key = (task_type, intent_type)
        if key in intent_descriptions:
            suggestions.append(f"• {intent_descriptions[key]} (התאמה: {int(score)}%)")
    
    # בניית התשובה המלאה
    response = f"{get_emoji('question')} לא הצלחתי להבין בדיוק למה התכוונת. האם התכוונת לאחת מהאפשרויות הבאות?\n\n"
    response += "\n".join(suggestions)
    response += "\n\nאנא נסה לנסח את הבקשה שלך בצורה ברורה יותר."
    
    return response

def get_error_response(error_type: str, error_details: Dict[str, Any] = None) -> str:
    """
    קבלת תשובת שגיאה מוכנה לפי סוג השגיאה
    
    Args:
        error_type: סוג השגיאה
        error_details: פרטי השגיאה (אופציונלי)
        
    Returns:
        תשובת שגיאה מוכנה
    """
    if error_details is None:
        error_details = {}
    
    # בחירת תבנית תשובה מתאימה לסוג השגיאה
    if error_type in ERROR_TEMPLATES:
        response_template = random.choice(ERROR_TEMPLATES[error_type])
    else:
        response_template = random.choice(ERROR_TEMPLATES[ErrorType.GENERAL_ERROR])
    
    # הוספת פרטי שגיאה אם יש
    error_message = error_details.get("message", "")
    if error_message:
        response = f"{get_emoji('error')} {response_template}\n\nפרטי השגיאה: {error_message}"
    else:
        response = f"{get_emoji('error')} {response_template}"
    
    return response 