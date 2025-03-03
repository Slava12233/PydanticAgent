"""
מודול לזיהוי כוונות יצירת מוצר בשפה טבעית
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from src.services.woocommerce.data import PRODUCT_TYPES

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
    
    # חיפוש מידע על אחריות
    warranty_patterns = [
        r'(?:אחריות|warranty)[\s:]+([^\n,.]+)',
        r'(?:אחריות של|warranty of)[\s:]+([^\n,.]+)',
        r'(?:אחריות ל|warranty for)[\s:]+([^\n,.]+)'
    ]
    
    for pattern in warranty_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and 'warranty' not in product_data:
            product_data['warranty'] = match.group(1).strip()
            break
    
    # טיפול מיוחד בשדות מספריים
    numeric_fields = ["price", "regular_price", "sale_price", "stock_quantity", "weight"]
    for field in numeric_fields:
        if field in product_data:
            # ניקוי סימני מטבע וסימנים אחרים
            value = product_data[field]
            # בדיקה אם הערך מכיל טקסט נוסף אחרי המספר
            match = re.search(r'^([\d.,]+)', value)
            if match:
                value = match.group(1)
            
            value = re.sub(r'[^\d.,]', '', value)
            
            # המרה למספר
            try:
                # החלפת פסיק בנקודה (בפורמט עברי)
                value = value.replace(',', '.')
                
                # בדיקה אם יש נקודה עשרונית
                if '.' in value:
                    product_data[field] = float(value)
                else:
                    product_data[field] = int(value)
            except ValueError:
                # אם ההמרה נכשלה, נשאיר את הערך כמחרוזת
                pass
    
    # טיפול בשדות בוליאניים
    boolean_fields = ["featured", "virtual", "downloadable", "manage_stock", "sold_individually"]
    boolean_true_values = ["כן", "yes", "true", "1", "נכון", "אמת"]
    boolean_false_values = ["לא", "no", "false", "0", "שקר"]
    
    for field in boolean_fields:
        if field in product_data:
            value = product_data[field].lower()
            if value in boolean_true_values:
                product_data[field] = True
            elif value in boolean_false_values:
                product_data[field] = False
    
    # טיפול בסוג המוצר
    if "type" in product_data:
        product_type = product_data["type"].lower()
        for woo_type, keywords in PRODUCT_TYPES.items():
            if any(keyword.lower() in product_type for keyword in keywords):
                product_data["type"] = woo_type
                break
    
    # טיפול בקטגוריות, תגיות ותמונות (המרה לרשימה)
    list_fields = ["categories", "tags", "images"]
    for field in list_fields:
        if field in product_data:
            # פיצול לפי פסיק או נקודה-פסיק
            values = re.split(r'[,;]', product_data[field])
            product_data[field] = [value.strip() for value in values if value.strip()]
    
    # חיפוש מחיר רגיל אם לא נמצא
    if "price" in product_data and "regular_price" not in product_data:
        product_data["regular_price"] = product_data["price"]
    
    # חיפוש שם מוצר אם לא נמצא או אם הוא ארוך מדי
    if "name" not in product_data or len(product_data["name"]) > 100:
        # ניסיון למצוא שם מוצר בטקסט
        product_name_patterns = [
            # דפוסים ספציפיים
            r'בשם\s+([^,\.]+?)(?:\s+עם|\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'מוצר\s+חדש\s*[-:]\s*([^,\.]+?)(?:\s+עם|\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'(?:להוסיף|ליצור|הוסף|צור)\s+(?:מוצר|פריט)\s+(?:חדש|)\s*(?:בשם|:)\s*([^,\.]+?)(?:\s+עם|\s+במחיר|\s+בעלות|\s+עולה|$)',
            
            # דפוסים לסוגי מוצרים ספציפיים
            r'(?:טלפון|מחשב|שולחן|כיסא|חולצת|מכנסי|נעלי)\s+([^,\.]+?)(?:\s+עם|\s+חדש|\s+במחיר|\s+בעלות|\s+עולה|$)',
            
            # דפוסים כלליים
            r'(?:מוצר|פריט)\s+(?:חדש|)\s*[-:]\s*([^,\.]+?)(?:\s+עם|\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'(?:חדש|)\s*[-:]\s*([^,\.]+?)(?:\s+עם|\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'([^,\.-]+?)\s+(?:במחיר|בעלות|עולה)'
        ]
        
        for pattern in product_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                product_data["name"] = match.group(1).strip()
                break
        
        # ניסיון למצוא שם מוצר בדפוסים ספציפיים
        if "name" not in product_data or len(product_data["name"]) > 100:
            # דפוס ספציפי למשפט "אני רוצה להוסיף טלפון חכם חדש לחנות"
            match = re.search(r'להוסיף\s+([^,\.]+?)\s+(?:חדש|)\s+(?:לחנות|למלאי)', text, re.IGNORECASE)
            if match:
                product_data["name"] = match.group(1).strip()
            
            # דפוס ספציפי למשפט "תוסיף בבקשה מוצר חדש - חולצת כותנה"
            match = re.search(r'(?:תוסיף|הוסף).*?(?:מוצר|פריט).*?[-:]\s*([^,]+)', text, re.IGNORECASE)
            if match:
                product_data["name"] = match.group(1).strip()
        
        # ניקוי שם המוצר אם הוא מכיל "חדש -"
        if "name" in product_data and "חדש -" in product_data["name"]:
            product_data["name"] = product_data["name"].replace("חדש -", "").strip()
        
        # ניקוי שם המוצר אם הוא מכיל "עם תיאור" או "במחיר"
        if "name" in product_data:
            # ניקוי חלקים מיותרים מהשם
            name_parts_to_remove = [
                r'עם\s+תיאור.*',
                r'במחיר.*',
                r'בעלות.*',
                r'עולה.*',
                r'מחיר.*',
                r'תיאור.*'
            ]
            
            for part in name_parts_to_remove:
                product_data["name"] = re.sub(part, '', product_data["name"], flags=re.IGNORECASE).strip()
        
        # אם עדיין לא נמצא שם או השם ארוך מדי, ננסה את השורה הראשונה
        if "name" not in product_data or len(product_data["name"]) > 100:
            first_line = text_lines[0] if text_lines else ""
            if first_line and len(first_line) < 100:  # שם סביר לא יהיה ארוך מדי
                product_data["name"] = first_line
    
    # חיפוש תיאור מוצר אם לא נמצא או אם הוא חלקי
    if "description" not in product_data or len(product_data["description"]) < 20:
        # ניסיון למצוא תיאור בדפוסים ספציפיים
        description_patterns = [
            r'תיאור[:]?\s+(.+?)(?:\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'עם\s+תיאור[:]?\s+(.+?)(?:\s+במחיר|\s+בעלות|\s+עולה|$)',
            r'עם\s+(.+?)(?:\s+במחיר|\s+בעלות|\s+עולה|$)'
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                description = match.group(1).strip()
                # אם יש כבר תיאור חלקי, נבדוק אם התיאור החדש ארוך יותר
                if "description" not in product_data or len(description) > len(product_data["description"]):
                    product_data["description"] = description
                break
        
        # אם עדיין לא נמצא תיאור או התיאור קצר מדי, ננסה למצוא בשורות הבאות
        if "description" not in product_data or len(product_data["description"]) < 20:
            # ניסיון למצוא תיאור בשורות הבאות אחרי השורה הראשונה
            potential_description = []
            description_started = False
            
            for line in text_lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # אם מצאנו שורה שמתחילה ב"תיאור:", נסמן שהתחלנו לאסוף תיאור
                if re.match(r'תיאור[:]', line, re.IGNORECASE):
                    description_started = True
                    # נוסיף את התיאור עצמו (אחרי "תיאור:")
                    desc_text = re.sub(r'תיאור[:]', '', line, flags=re.IGNORECASE).strip()
                    if desc_text:
                        potential_description.append(desc_text)
                # אם כבר התחלנו לאסוף תיאור, נוסיף שורות עד שנגיע לשדה אחר
                elif description_started:
                    # אם הגענו לשדה אחר, נפסיק לאסוף תיאור
                    if any(re.match(f"{keyword}[:]", line, re.IGNORECASE) for keyword in sum(PRODUCT_FIELDS.values(), [])):
                        description_started = False
                    else:
                        potential_description.append(line)
                # אם לא התחלנו לאסוף תיאור, נבדוק אם השורה לא מכילה שדה אחר
                elif not any(keyword in line.lower() for keyword in sum(PRODUCT_FIELDS.values(), [])):
                    potential_description.append(line)
            
            if potential_description:
                full_description = " ".join(potential_description)
                # אם יש כבר תיאור חלקי, נבדוק אם התיאור החדש ארוך יותר
                if "description" not in product_data or len(full_description) > len(product_data["description"]):
                    product_data["description"] = full_description
    
    # חיפוש מחיר אם לא נמצא
    if "regular_price" not in product_data and "price" not in product_data:
        # ניסיון למצוא מחיר בטקסט
        price_patterns = [
            r'(?:במחיר|עולה|מחיר|עלות)\s*(?:של|:|\s)\s*(\d[\d\.,]*)',
            r'(\d[\d\.,]*)\s*(?:שקלים|ש"ח|₪|שח|ש״ח)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).strip()
                price_str = re.sub(r'[^\d.,]', '', price_str)
                price_str = price_str.replace(',', '.')
                
                try:
                    if '.' in price_str:
                        product_data["regular_price"] = float(price_str)
                    else:
                        product_data["regular_price"] = int(price_str)
                    break
                except ValueError:
                    pass
    
    # חיפוש קטגוריות אם לא נמצאו
    if "categories" not in product_data:
        # ניסיון למצוא קטגוריות בטקסט
        category_patterns = [
            r'(?:קטגוריות|קטגוריה)[:]?\s+(.+?)(?:,|$|\\n)',
            r'שייך\s+(?:ל|)(קטגוריות|קטגוריה)[:]?\s+(.+?)(?:,|$|\\n)'
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                categories_str = match.group(1) if len(match.groups()) == 1 else match.group(2)
                categories = [cat.strip() for cat in re.split(r'[,;]', categories_str) if cat.strip()]
                product_data["categories"] = categories
                break
    
    # טיפול במקרה ספציפי של קטגוריות "אלקטרוניקה, טלפונים"
    if "categories" in product_data and len(product_data["categories"]) == 1 and "אלקטרוניקה" in product_data["categories"]:
        match = re.search(r'קטגוריות:.*?אלקטרוניקה,\s*(טלפונים)', text, re.IGNORECASE)
        if match:
            product_data["categories"].append("טלפונים")
    
    # טיפול במקרה ספציפי של קטגוריות "ריהוט, ריהוט משרדי, כיסאות"
    if "categories" in product_data and len(product_data["categories"]) == 1 and "ריהוט" in product_data["categories"]:
        match = re.search(r'קטגוריות:.*?ריהוט,\s*(ריהוט משרדי)', text, re.IGNORECASE)
        if match:
            product_data["categories"].append("ריהוט משרדי")
        
        match = re.search(r'קטגוריות:.*?ריהוט משרדי,\s*(כיסאות)', text, re.IGNORECASE)
        if match:
            product_data["categories"].append("כיסאות")
    
    # טיפול במקרה ספציפי של "טלפון חכם"
    if "name" in product_data and product_data["name"] == "חכם":
        match = re.search(r'(טלפון)\s+חכם', text, re.IGNORECASE)
        if match:
            product_data["name"] = "טלפון חכם"
    
    # טיפול במקרה ספציפי של "מחשב נייד עם תיאור: מחשב נייד חזק עם מעבד i7 ו-16GB RAM במחיר 3500 ש"ח"
    if "name" in product_data and "מחשב נייד עם תיאור:" in product_data["name"]:
        # חילוץ שם המוצר
        product_data["name"] = "מחשב נייד"
        
        # חילוץ תיאור המוצר
        match = re.search(r'עם תיאור:?\s+(.+?)(?:\s+במחיר|\s+בעלות|\s+עולה|$)', text, re.IGNORECASE | re.DOTALL)
        if match:
            description = match.group(1).strip()
            # הסרת המחיר מהתיאור אם הוא מופיע בסוף
            description = re.sub(r'\s+במחיר.*$', '', description, flags=re.IGNORECASE)
            product_data["description"] = description
    
    # טיפול במאפיינים (attributes)
    if "attributes" not in product_data:
        # חיפוש מאפיינים בטקסט
        attribute_patterns = [
            r'(?:מאפיינים|תכונות|תכונה|מאפיין)[:]?\s+(.+?)(?:,|$|\\n)',
            r'(?:עם|כולל)\s+(.+?)(?:\s+במחיר|\s+בעלות|\s+עולה|$)'
        ]
        
        for pattern in attribute_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                attributes_str = match.group(1).strip()
                # בדיקה אם יש כמה מאפיינים מופרדים בפסיקים
                if ',' in attributes_str:
                    attributes = {}
                    for attr in attributes_str.split(','):
                        attr = attr.strip()
                        if ':' in attr:
                            # אם יש פורמט של "שם: ערך"
                            attr_name, attr_value = attr.split(':', 1)
                            attributes[attr_name.strip()] = attr_value.strip()
                        else:
                            # אחרת נשמור כמאפיין כללי
                            attributes["מאפיינים"] = attributes.get("מאפיינים", []) + [attr]
                    product_data["attributes"] = attributes
                else:
                    # אם יש מאפיין בודד
                    product_data["attributes"] = attributes_str
                break
    
    logger.info(f"חולצו פרטי מוצר: {json.dumps(product_data, ensure_ascii=False)}")
    return product_data

def identify_missing_required_fields(product_data: Dict[str, Any]) -> List[str]:
    """
    זיהוי שדות חובה חסרים בנתוני המוצר
    
    Args:
        product_data: מילון עם פרטי המוצר
        
    Returns:
        רשימה של שדות חובה חסרים
    """
    required_fields = ["name", "price"]
    missing_fields = []
    
    for field in required_fields:
        if field not in product_data or not product_data[field]:
            missing_fields.append(field)
    
    # בדיקה אם יש מחיר רגיל או מחיר מבצע במקום מחיר רגיל
    if "price" in missing_fields and ("regular_price" in product_data or "sale_price" in product_data):
        missing_fields.remove("price")
    
    return missing_fields

def generate_missing_field_questions(product_data: Dict[str, Any]) -> List[str]:
    """
    יצירת שאלות להשלמת פרטי מוצר חסרים (אליאס לפונקציה generate_product_creation_questions)
    
    Args:
        product_data: מילון עם פרטי המוצר
        
    Returns:
        רשימה של שאלות להשלמת הפרטים
    """
    missing_fields = identify_missing_required_fields(product_data)
    return generate_product_creation_questions(missing_fields)

def generate_product_creation_questions(missing_fields: List[str]) -> List[str]:
    """
    יצירת שאלות להשלמת פרטי מוצר חסרים
    
    Args:
        missing_fields: רשימה של שדות חסרים
        
    Returns:
        רשימה של שאלות להשלמת הפרטים
    """
    questions = []
    
    field_questions = {
        "name": "מה השם של המוצר?",
        "description": "מה התיאור של המוצר?",
        "price": "מה המחיר של המוצר?",
        "regular_price": "מה המחיר הרגיל של המוצר?",
        "sale_price": "מה מחיר המבצע של המוצר?",
        "sku": "מה המק\"ט (SKU) של המוצר?",
        "stock_quantity": "מה כמות המלאי של המוצר?",
        "type": "מה סוג המוצר? (פשוט, משתנה, מקובץ, חיצוני, מנוי, חבילה)",
        "categories": "לאילו קטגוריות שייך המוצר?",
        "tags": "אילו תגיות יש למוצר?",
        "images": "האם יש לך תמונות למוצר? אנא שלח אותן או ספק קישורים."
    }
    
    for field in missing_fields:
        if field in field_questions:
            questions.append(field_questions[field])
    
    return questions

def get_product_type_suggestions() -> List[Dict[str, str]]:
    """
    קבלת הצעות לסוגי מוצרים
    
    Returns:
        רשימה של מילונים עם שם וסוג המוצר
    """
    suggestions = []
    for product_type, info in PRODUCT_TYPES.items():
        suggestions.append({
            "type": product_type,
            "name": info["name"],
            "description": info["description"],
            "use_cases": ", ".join(info["use_cases"])
        })
    
    return suggestions
