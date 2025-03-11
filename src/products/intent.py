"""
מודול לזיהוי כוונות יצירת מוצר בשפה טבעית
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set, TYPE_CHECKING
import json
from src.woocommerce.data.product_categories import PRODUCT_TYPES

if TYPE_CHECKING:
    from src.core.task_identification.models import TaskContext, IntentRecognitionResult

logger = logging.getLogger(__name__)

# ביטויים וטריגרים לזיהוי בקשות ליצירת מוצר
PRODUCT_CREATION_TRIGGERS = {
    # ביטויים ישירים ליצירת מוצר
    "direct_creation": [
        "צור מוצר", "הוסף מוצר", "יצירת מוצר", "הוספת מוצר", "להוסיף מוצר", "ליצור מוצר",
        "רוצה להוסיף מוצר", "אני רוצה ליצור מוצר", "אפשר להוסיף מוצר", "אפשר ליצור מוצר",
        "create product", "add product", "new product", "create a product", "add a product",
        "איך אני מוסיף מוצר", "איך מוסיפים מוצר", "איך יוצרים מוצר", "איך אני יוצר מוצר"
    ],
    
    # ביטויים עקיפים שעשויים להצביע על כוונה ליצור מוצר
    "indirect_creation": [
        "יש לי מוצר חדש", "מוצר חדש למכירה", "להעלות לחנות", "להוסיף לחנות", "להוסיף למלאי",
        "מוצר חדש שהגיע", "קיבלתי סחורה חדשה", "יש לי פריט חדש", "הגיע מלאי חדש",
        "got new merchandise", "new item to sell", "add to store", "add to inventory",
        "סחורה חדשה", "פריט חדש", "מלאי חדש"
    ],
    
    # ביטויים הקשורים לסוגי מוצרים ספציפיים
    "product_type_specific": [
        "מוצר פשוט", "מוצר משתנה", "מוצר דיגיטלי", "מוצר פיזי", "מוצר להורדה", "מנוי",
        "חבילת מוצרים", "מוצר מקובץ", "מוצר חיצוני", "מוצר וירטואלי",
        "simple product", "variable product", "digital product", "physical product", 
        "downloadable product", "subscription", "product bundle", "grouped product",
        "external product", "virtual product"
    ]
}

# שדות מוצר אפשריים שניתן לחלץ מטקסט
PRODUCT_FIELDS = {
    "name": ["שם", "כותרת", "name", "title"],
    "description": ["תיאור", "פירוט", "description", "details"],
    "price": ["מחיר", "עלות", "price", "cost"],
    "regular_price": ["מחיר רגיל", "מחיר מקורי", "regular price", "original price"],
    "sale_price": ["מחיר מבצע", "מחיר הנחה", "sale price", "discount price"],
    "sku": ["מק\"ט", "מקט", "קוד מוצר", "sku", "product code"],
    "stock_quantity": ["מלאי", "כמות במלאי", "stock", "quantity", "inventory"],
    "weight": ["משקל", "weight"],
    "dimensions": ["מידות", "גודל", "dimensions", "size"],
    "categories": ["קטגוריה", "קטגוריות", "category", "categories"],
    "tags": ["תגית", "תגיות", "tag", "tags"],
    "type": ["סוג", "type"],
    "status": ["סטטוס", "מצב", "status", "state"],
    "featured": ["מוצר מומלץ", "מוצר מובחר", "featured", "recommended"],
    "virtual": ["וירטואלי", "virtual"],
    "downloadable": ["להורדה", "downloadable"],
    "tax_status": ["סטטוס מס", "חייב במע\"מ", "פטור ממע\"מ", "tax status", "taxable", "tax exempt"],
    "tax_class": ["קבוצת מס", "tax class"],
    "manage_stock": ["ניהול מלאי", "manage stock"],
    "backorders": ["הזמנות מראש", "backorders"],
    "sold_individually": ["נמכר בודד", "sold individually"],
    "shipping_class": ["קבוצת משלוח", "shipping class"],
    "images": ["תמונה", "תמונות", "image", "images", "photo", "photos"],
    "attributes": ["מאפיין", "מאפיינים", "תכונה", "תכונות", "attribute", "attributes", "feature", "features"]
}

# סוגי מוצרים ב-WooCommerce
PRODUCT_TYPES = {
    "simple": ["פשוט", "רגיל", "simple", "regular", "standard"],
    "variable": ["משתנה", "עם וריאציות", "variable", "with variations"],
    "grouped": ["מקובץ", "קבוצה", "grouped", "group"],
    "external": ["חיצוני", "מסונף", "external", "affiliate"],
    "subscription": ["מנוי", "subscription"],
    "bundle": ["חבילה", "ערכה", "bundle", "kit", "package"]
}

def extract_product_id(text: str) -> Optional[int]:
    """
    חילוץ מזהה מוצר מטקסט חופשי
    
    Args:
        text: טקסט חופשי שעשוי להכיל מזהה מוצר
        
    Returns:
        מזהה המוצר אם נמצא, אחרת None
    """
    # חיפוש מזהה מוצר בפורמטים שונים
    patterns = [
        r'מוצר\s+(?:מספר|#|מס\'?|id|מזהה)?\s*(\d+)',
        r'(?:מוצר|פריט)\s+(?:עם\s+)?(?:מזהה|מספר|#|מס\'?|id)\s*:?\s*(\d+)',
        r'(?:product|item)\s+(?:number|#|id)?\s*:?\s*(\d+)',
        r'(?:id|מזהה|מספר)\s*:?\s*(\d+)',
        r'#(\d+)',
        r'מזהה\s+(?:ה)?מוצר\s*:?\s*(\d+)',
        r'product\s+id\s*:?\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return None

def is_product_creation_intent(text: str) -> bool:
    """
    בדיקה אם הטקסט מכיל כוונה ליצירת מוצר
    
    Args:
        text: הטקסט לבדיקה
        
    Returns:
        האם הטקסט מכיל כוונה ליצירת מוצר
    """
    text_lower = text.lower()
    
    # בדיקת ביטויים ישירים
    for trigger in PRODUCT_CREATION_TRIGGERS["direct_creation"]:
        if trigger.lower() in text_lower:
            logger.info(f"זוהתה כוונת יצירת מוצר ישירה: '{trigger}'")
            return True
    
    # בדיקת ביטויים עקיפים
    for trigger in PRODUCT_CREATION_TRIGGERS["indirect_creation"]:
        if trigger.lower() in text_lower:
            # אם יש ביטוי עקיף, נבדוק אם יש גם אזכור של מוצר, פריט, חנות או מלאי
            if any(word in text_lower for word in ["מוצר", "פריט", "סחורה", "חנות", "מלאי", "product", "item", "merchandise", "store", "inventory"]):
                logger.info(f"זוהתה כוונת יצירת מוצר עקיפה: '{trigger}'")
                return True
    
    # בדיקת ביטויים ספציפיים לסוגי מוצרים
    for trigger in PRODUCT_CREATION_TRIGGERS["product_type_specific"]:
        if trigger.lower() in text_lower:
            # אם יש אזכור של סוג מוצר, נבדוק אם יש גם אזכור של יצירה או הוספה
            creation_words = ["צור", "הוסף", "יצירת", "הוספת", "להוסיף", "ליצור", "create", "add", "new"]
            if any(word in text_lower for word in creation_words):
                logger.info(f"זוהתה כוונת יצירת מוצר מסוג ספציפי: '{trigger}'")
                return True
    
    # בדיקת דפוס של שדות מוצר רבים
    field_count = 0
    for field, keywords in PRODUCT_FIELDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                field_count += 1
                break  # מספיק למצוא מילת מפתח אחת לכל שדה
    
    # אם יש מספר גדול של שדות מוצר, סביר שמדובר ביצירת מוצר
    if field_count >= 3:
        logger.info(f"זוהתה כוונת יצירת מוצר לפי מספר שדות: {field_count}")
        return True
    
    return False

def extract_product_data(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי מוצר מטקסט חופשי
    
    Args:
        text: הטקסט לחילוץ ממנו
        
    Returns:
        מילון עם פרטי המוצר שחולצו
    """
    product_data = {}
    text_lines = text.split('\n')
    
    # חיפוש שדות מוצר בכל שורה
    for line in text_lines:
        line = line.strip()
        if not line:
            continue
        
        # חיפוש שדות מוצר
        for field, keywords in PRODUCT_FIELDS.items():
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
                        if field not in product_data and value:
                            product_data[field] = value
                            break
    
    # חיפוש מתקדם יותר בכל הטקסט (לא רק לפי שורות)
    # חיפוש צבעים
    color_patterns = [
        r'(?:צבע|color)[\s:]+([א-ת\w]+)',
        r'ב(?:צבע|color)\s+([א-ת\w]+)',
        r'(?:available|זמין)\s+(?:in|ב)?\s*(?:colors?|צבעים?)[\s:]+([^,.]+)'
    ]
    
    for pattern in color_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'color' not in product_data:
            product_data['color'] = match.group(1).strip()
            break
    
    # חיפוש מידות
    size_patterns = [
        r'(?:מידה|מידות|size|sizes)[\s:]+([^\n,.]+)',
        r'ב(?:מידה|מידות|size|sizes)\s+([^\n,.]+)',
        r'(?:available|זמין)\s+(?:in|ב)?\s*(?:sizes?|מידות?)[\s:]+([^,.]+)'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'size' not in product_data:
            product_data['size'] = match.group(1).strip()
            break
    
    # חיפוש חומרים
    material_patterns = [
        r'(?:חומר|material)[\s:]+([^\n,.]+)',
        r'(?:עשוי מ|made of|made from)[\s:]+([^\n,.]+)',
        r'(?:מיוצר מ|produced from)[\s:]+([^\n,.]+)'
    ]
    
    for pattern in material_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'material' not in product_data:
            product_data['material'] = match.group(1).strip()
            break
    
    # חיפוש מותג
    brand_patterns = [
        r'(?:מותג|brand)[\s:]+([^\n,.]+)',
        r'(?:של חברת|by company|by brand)[\s:]+([^\n,.]+)',
        r'(?:מבית|from)[\s:]+([^\n,.]+)'
    ]
    
    for pattern in brand_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'brand' not in product_data:
            product_data['brand'] = match.group(1).strip()
            break
    
    return product_data

def identify_missing_required_fields(product_data: Dict[str, Any]) -> List[str]:
    """
    זיהוי שדות חובה חסרים בנתוני מוצר
    
    Args:
        product_data: נתוני המוצר
        
    Returns:
        רשימת שדות חובה חסרים
    """
    required_fields = ["name", "regular_price"]
    missing_fields = []
    
    for field in required_fields:
        if field not in product_data or not product_data[field]:
            missing_fields.append(field)
    
    return missing_fields

def generate_missing_field_questions(product_data: Dict[str, Any]) -> List[str]:
    """
    יצירת שאלות לשדות חסרים
    
    Args:
        product_data: נתוני המוצר
        
    Returns:
        רשימת שאלות לשדות חסרים
    """
    missing_fields = identify_missing_required_fields(product_data)
    return generate_product_creation_questions(missing_fields)

def generate_product_creation_questions(missing_fields: List[str]) -> List[str]:
    """
    יצירת שאלות לשדות חסרים בתהליך יצירת מוצר
    
    Args:
        missing_fields: רשימת שדות חסרים
        
    Returns:
        רשימת שאלות
    """
    questions = []
    
    field_questions = {
        "name": "מה השם של המוצר?",
        "regular_price": "מה המחיר הרגיל של המוצר?",
        "sale_price": "האם יש מחיר מבצע למוצר? אם כן, מהו?",
        "description": "מה התיאור של המוצר?",
        "short_description": "מה התיאור הקצר של המוצר?",
        "categories": "לאיזו קטגוריה שייך המוצר?",
        "sku": "מה המק\"ט (SKU) של המוצר?",
        "stock_quantity": "כמה יחידות יש במלאי?",
        "weight": "מה המשקל של המוצר?",
        "dimensions": "מה המידות של המוצר (אורך, רוחב, גובה)?",
        "images": "האם יש תמונות למוצר? אם כן, אנא ספק קישורים או תיאור.",
        "attributes": "האם יש מאפיינים מיוחדים למוצר (כמו צבע, גודל וכו')?"
    }
    
    for field in missing_fields:
        if field in field_questions:
            questions.append(field_questions[field])
    
    return questions

def get_product_type_suggestions() -> List[Dict[str, str]]:
    """
    קבלת הצעות לסוגי מוצרים
    
    Returns:
        רשימת הצעות לסוגי מוצרים
    """
    suggestions = []
    
    for product_type, keywords in PRODUCT_TYPES.items():
        if keywords and len(keywords) > 0:
            suggestion = {
                "type": product_type,
                "name": keywords[0] if len(keywords) > 0 else product_type
            }
            suggestions.append(suggestion)
    
    return suggestions

async def identify_product_intent(
    message: str,
    context: Optional["TaskContext"] = None
) -> Optional["IntentRecognitionResult"]:
    """
    זיהוי כוונות הקשורות למוצרים
    
    Args:
        message: הודעת המשתמש
        context: הקשר המשימה
        
    Returns:
        תוצאת זיהוי הכוונה
    """
    from src.core.task_identification.models import IntentRecognitionResult
    
    # בדיקה אם יש כוונת יצירת מוצר
    if is_product_creation_intent(message):
        # חילוץ נתוני מוצר
        product_data = extract_product_data(message)
        
        # בדיקת שדות חסרים
        missing_fields = identify_missing_required_fields(product_data)
        
        # יצירת שאלות לשדות חסרים
        questions = generate_product_creation_questions(missing_fields) if missing_fields else []
        
        return IntentRecognitionResult(
            intent="product.create",
            confidence=0.9,
            params={
                "product_data": product_data,
                "missing_fields": missing_fields
            },
            follow_up_questions=questions
        )
    
    # בדיקה אם יש כוונת עדכון מוצר
    product_id = extract_product_id(message)
    if product_id:
        # חילוץ נתוני מוצר
        product_data = extract_product_data(message)
        
        if product_data:
            return IntentRecognitionResult(
                intent="product.update",
                confidence=0.8,
                params={
                    "product_id": product_id,
                    "product_data": product_data
                }
            )
    
    return None 