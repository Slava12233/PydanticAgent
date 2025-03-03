"""
מודול לייצור תשובות בשפה טבעית (Response Generation)

מודול זה מכיל פונקציות וכלים לייצור תשובות בשפה טבעית בהתבסס על כוונת המשתמש והנתונים שנאספו.
המודול מאפשר יצירת תשובות מגוונות, טבעיות ומותאמות אישית למשתמש.
"""
import random
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime

# הגדרת לוגר
logger = logging.getLogger(__name__)

class ResponseGenerator:
    """מחלקה לייצור תשובות בשפה טבעית"""
    
    def __init__(self):
        """אתחול מחולל התשובות"""
        # מילון תבניות תשובה לפי סוגי כוונות
        self.templates = {
            # תבניות לשאילתות מוצרים
            "product_query": {
                "search": [
                    "הנה המוצרים שמצאתי עבורך: {products}",
                    "מצאתי את המוצרים הבאים: {products}",
                    "הנה תוצאות החיפוש שלך: {products}",
                    "חיפשתי ומצאתי את המוצרים הבאים: {products}",
                    "אלו המוצרים שמתאימים לחיפוש שלך: {products}"
                ],
                "get": [
                    "הנה המידע על המוצר {product_name}: {product_details}",
                    "מצאתי את המוצר {product_name}. הנה הפרטים: {product_details}",
                    "המוצר {product_name} נמצא במערכת. הנה המידע: {product_details}",
                    "להלן פרטי המוצר {product_name}: {product_details}",
                    "זהו המידע על {product_name}: {product_details}"
                ],
                "not_found": [
                    "לא מצאתי מוצרים שתואמים את החיפוש שלך.",
                    "אין מוצרים שתואמים את הקריטריונים שציינת.",
                    "לא הצלחתי למצוא מוצרים כאלה במערכת.",
                    "החיפוש שלך לא הניב תוצאות. אולי תנסה לחפש במילים אחרות?",
                    "אין לנו מוצרים שתואמים את מה שחיפשת. אפשר לנסות חיפוש אחר?"
                ]
            },
            
            # תבניות להזמנות
            "order_query": {
                "search": [
                    "הנה ההזמנות שמצאתי: {orders}",
                    "מצאתי את ההזמנות הבאות: {orders}",
                    "אלו ההזמנות שתואמות את החיפוש שלך: {orders}",
                    "להלן ההזמנות שביקשת: {orders}",
                    "הנה רשימת ההזמנות שחיפשת: {orders}"
                ],
                "get": [
                    "הנה המידע על הזמנה מספר {order_id}: {order_details}",
                    "מצאתי את ההזמנה {order_id}. הנה הפרטים: {order_details}",
                    "להלן פרטי ההזמנה {order_id}: {order_details}",
                    "זהו המידע על הזמנה {order_id}: {order_details}",
                    "הנה הפרטים של הזמנה מספר {order_id}: {order_details}"
                ],
                "not_found": [
                    "לא מצאתי הזמנות שתואמות את החיפוש שלך.",
                    "אין הזמנות שתואמות את הקריטריונים שציינת.",
                    "לא הצלחתי למצוא הזמנות כאלה במערכת.",
                    "החיפוש שלך לא הניב תוצאות. אולי תנסה לחפש במילים אחרות?",
                    "אין הזמנות שתואמות את מה שחיפשת. אפשר לנסות חיפוש אחר?"
                ]
            },
            
            # תבניות ללקוחות
            "customer_query": {
                "search": [
                    "הנה הלקוחות שמצאתי: {customers}",
                    "מצאתי את הלקוחות הבאים: {customers}",
                    "אלו הלקוחות שתואמים את החיפוש שלך: {customers}",
                    "להלן הלקוחות שביקשת: {customers}",
                    "הנה רשימת הלקוחות שחיפשת: {customers}"
                ],
                "get": [
                    "הנה המידע על הלקוח {customer_name}: {customer_details}",
                    "מצאתי את הלקוח {customer_name}. הנה הפרטים: {customer_details}",
                    "להלן פרטי הלקוח {customer_name}: {customer_details}",
                    "זהו המידע על {customer_name}: {customer_details}",
                    "הנה הפרטים של הלקוח {customer_name}: {customer_details}"
                ],
                "not_found": [
                    "לא מצאתי לקוחות שתואמים את החיפוש שלך.",
                    "אין לקוחות שתואמים את הקריטריונים שציינת.",
                    "לא הצלחתי למצוא לקוחות כאלה במערכת.",
                    "החיפוש שלך לא הניב תוצאות. אולי תנסה לחפש במילים אחרות?",
                    "אין לקוחות שתואמים את מה שחיפשת. אפשר לנסות חיפוש אחר?"
                ]
            },
            
            # תבניות לפעולות יצירה ועדכון
            "action": {
                "create_success": [
                    "יצרתי בהצלחה את {entity_type} {entity_name}.",
                    "{entity_type} {entity_name} נוצר בהצלחה!",
                    "הוספתי את {entity_type} {entity_name} למערכת.",
                    "יצירת {entity_type} {entity_name} הושלמה בהצלחה.",
                    "{entity_type} חדש בשם {entity_name} נוצר במערכת."
                ],
                "update_success": [
                    "עדכנתי בהצלחה את {entity_type} {entity_name}.",
                    "{entity_type} {entity_name} עודכן בהצלחה!",
                    "השינויים ב{entity_type} {entity_name} נשמרו במערכת.",
                    "עדכון {entity_type} {entity_name} הושלם בהצלחה.",
                    "הפרטים של {entity_type} {entity_name} עודכנו כמבוקש."
                ],
                "delete_success": [
                    "מחקתי בהצלחה את {entity_type} {entity_name}.",
                    "{entity_type} {entity_name} נמחק בהצלחה!",
                    "הסרתי את {entity_type} {entity_name} מהמערכת.",
                    "מחיקת {entity_type} {entity_name} הושלמה בהצלחה.",
                    "{entity_type} {entity_name} הוסר לצמיתות מהמערכת."
                ],
                "action_failed": [
                    "לא הצלחתי לבצע את הפעולה על {entity_type} {entity_name}. הסיבה: {reason}",
                    "הפעולה על {entity_type} {entity_name} נכשלה. הסיבה: {reason}",
                    "אירעה שגיאה בעת ביצוע הפעולה על {entity_type} {entity_name}: {reason}",
                    "לא ניתן היה להשלים את הפעולה על {entity_type} {entity_name}. הסיבה: {reason}",
                    "הפעולה נכשלה: {reason}"
                ]
            },
            
            # תבניות לשאלות כלליות
            "general": {
                "greeting": [
                    "שלום! איך אני יכול לעזור לך היום?",
                    "היי! במה אוכל לסייע לך?",
                    "ברוך הבא! איך אוכל לעזור בניהול החנות שלך?",
                    "שלום וברכה! איך אוכל לסייע לך היום?",
                    "היי שם! במה אוכל לעזור לך בחנות?"
                ],
                "farewell": [
                    "להתראות! אשמח לעזור שוב בפעם הבאה.",
                    "ביי! אם תצטרך עוד עזרה, אני כאן.",
                    "תודה ולהתראות! מקווה שהייתי לעזר.",
                    "שיהיה לך יום נפלא! אני זמין כשתצטרך אותי שוב.",
                    "להתראות ובהצלחה! אשמח לסייע שוב בעתיד."
                ],
                "thanks": [
                    "בשמחה! אשמח לעזור בכל דבר נוסף.",
                    "אין בעד מה! יש עוד משהו שאוכל לעזור בו?",
                    "שמחתי לעזור! אם תצטרך עוד משהו, אני כאן.",
                    "בכיף! אני כאן בשבילך.",
                    "זו הייתה הנאה! אשמח לסייע בכל דבר נוסף."
                ],
                "fallback": [
                    "אני לא בטוח שהבנתי. האם תוכל לנסח את השאלה בצורה אחרת?",
                    "סליחה, לא הצלחתי להבין את הבקשה. אפשר לנסות שוב?",
                    "אני מתקשה להבין את הבקשה. אולי תוכל להסביר בצורה אחרת?",
                    "לא הצלחתי לפענח את הבקשה. אפשר לנסות לנסח אותה אחרת?",
                    "אני מצטער, אבל לא הבנתי את הבקשה. אפשר לנסות שוב בצורה אחרת?"
                ]
            }
        }
        
        # מילון אימוג'ים לפי סוגי ישויות
        self.emojis = {
            "product": "🛍️",
            "order": "📦",
            "customer": "👤",
            "category": "📂",
            "price": "💰",
            "date": "📅",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "question": "❓",
            "search": "🔍",
            "create": "➕",
            "update": "🔄",
            "delete": "🗑️",
            "time": "⏱️",
            "store": "🏪",
            "settings": "⚙️",
            "document": "📄"
        }
    
    def generate_natural_response(self, intent_type: str, subtype: str, data: Dict[str, Any]) -> str:
        """
        מייצר תשובה טבעית בהתבסס על סוג הכוונה, תת-הסוג והנתונים
        
        Args:
            intent_type: סוג הכוונה (product_query, order_query, customer_query, action, general)
            subtype: תת-סוג הכוונה (search, get, create_success, וכו')
            data: מילון עם הנתונים להכנסה לתבנית
            
        Returns:
            תשובה טבעית בשפה העברית
        """
        logger.debug(f"מייצר תשובה טבעית עבור כוונה: {intent_type}, תת-סוג: {subtype}")
        
        # בדיקה שהכוונה ותת-הסוג קיימים במילון התבניות
        if intent_type not in self.templates:
            logger.warning(f"סוג כוונה לא מוכר: {intent_type}, משתמש בתבנית כללית")
            intent_type = "general"
            subtype = "fallback"
        
        if subtype not in self.templates[intent_type]:
            logger.warning(f"תת-סוג לא מוכר: {subtype} בכוונה {intent_type}, משתמש בתבנית כללית")
            intent_type = "general"
            subtype = "fallback"
        
        # בחירה אקראית של תבנית מתוך האפשרויות
        templates = self.templates[intent_type][subtype]
        template = random.choice(templates)
        
        try:
            # הוספת אימוג'ים לתשובה
            response = self._add_emojis(template, intent_type, subtype)
            
            # מילוי התבנית עם הנתונים
            response = self._fill_template(response, data)
            
            # הוספת המלצות לפעולות נוספות אם רלוונטי
            response = self._add_suggestions(response, intent_type, subtype, data)
            
            logger.debug(f"תשובה שנוצרה: {response[:50]}...")
            return response
        
        except KeyError as e:
            logger.error(f"שגיאה במילוי התבנית: חסר מפתח {e}")
            return f"{self.emojis['error']} אירעה שגיאה בעת יצירת התשובה. חסר מידע: {e}"
        
        except Exception as e:
            logger.error(f"שגיאה כללית ביצירת תשובה: {e}")
            return f"{self.emojis['error']} אירעה שגיאה בעת יצירת התשובה: {e}"
    
    def _add_emojis(self, template: str, intent_type: str, subtype: str) -> str:
        """
        מוסיף אימוג'ים מתאימים לתבנית התשובה
        
        Args:
            template: תבנית התשובה
            intent_type: סוג הכוונה
            subtype: תת-סוג הכוונה
            
        Returns:
            תבנית עם אימוג'ים
        """
        # בחירת אימוג'י מתאים לפי סוג הכוונה ותת-הסוג
        emoji = ""
        
        if intent_type == "product_query":
            emoji = self.emojis["product"]
        elif intent_type == "order_query":
            emoji = self.emojis["order"]
        elif intent_type == "customer_query":
            emoji = self.emojis["customer"]
        elif intent_type == "action":
            if "success" in subtype:
                emoji = self.emojis["success"]
            elif "failed" in subtype:
                emoji = self.emojis["error"]
            else:
                if "create" in subtype:
                    emoji = self.emojis["create"]
                elif "update" in subtype:
                    emoji = self.emojis["update"]
                elif "delete" in subtype:
                    emoji = self.emojis["delete"]
        elif intent_type == "general":
            if subtype == "greeting":
                emoji = "👋"
            elif subtype == "farewell":
                emoji = "👋"
            elif subtype == "thanks":
                emoji = "😊"
            elif subtype == "fallback":
                emoji = self.emojis["question"]
        
        # הוספת האימוג'י בתחילת התשובה אם עוד אין אימוג'י
        if not any(char in template[:2] for char in "😊👋🛍️📦👤📂💰📅✅❌⚠️ℹ️❓🔍➕🔄🗑️⏱️🏪⚙️📄"):
            return f"{emoji} {template}"
        
        return template
    
    def _fill_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        ממלא את התבנית עם הנתונים
        
        Args:
            template: תבנית התשובה
            data: מילון עם הנתונים להכנסה לתבנית
            
        Returns:
            תשובה מלאה עם הנתונים
        """
        try:
            return template.format(**data)
        except KeyError as e:
            # אם חסר מפתח, מנסה להחליף אותו בטקסט ברירת מחדל
            missing_key = str(e).strip("'")
            logger.warning(f"חסר מפתח בנתונים: {missing_key}, משתמש בברירת מחדל")
            
            # יצירת מילון עם ערכי ברירת מחדל למפתחות חסרים
            default_values = {
                "product_name": "המוצר",
                "product_details": "פרטי המוצר",
                "products": "רשימת המוצרים",
                "order_id": "ההזמנה",
                "order_details": "פרטי ההזמנה",
                "orders": "רשימת ההזמנות",
                "customer_name": "הלקוח",
                "customer_details": "פרטי הלקוח",
                "customers": "רשימת הלקוחות",
                "entity_type": "הפריט",
                "entity_name": "שביקשת",
                "reason": "סיבה לא ידועה"
            }
            
            # הוספת ערך ברירת מחדל למילון הנתונים
            if missing_key in default_values:
                data[missing_key] = default_values[missing_key]
                return template.format(**data)
            else:
                # אם אין ערך ברירת מחדל, מחליף את המקום בתבנית בהודעה
                pattern = r'\{' + missing_key + r'\}'
                return re.sub(pattern, f"[חסר מידע: {missing_key}]", template)
    
    def _add_suggestions(self, response: str, intent_type: str, subtype: str, data: Dict[str, Any]) -> str:
        """
        מוסיף הצעות לפעולות נוספות בסוף התשובה
        
        Args:
            response: התשובה הנוכחית
            intent_type: סוג הכוונה
            subtype: תת-סוג הכוונה
            data: מילון עם הנתונים
            
        Returns:
            תשובה עם הצעות לפעולות נוספות
        """
        # הוספת הצעות רק במקרים מסוימים
        suggestions = []
        
        # הצעות לאחר חיפוש מוצרים
        if intent_type == "product_query" and subtype == "search" and "products" in data:
            suggestions.append("אפשר לקבל מידע מפורט יותר על מוצר ספציפי")
            suggestions.append("אפשר לעדכן את המחיר או המלאי של אחד המוצרים")
        
        # הצעות לאחר הצגת מוצר
        elif intent_type == "product_query" and subtype == "get" and "product_name" in data:
            suggestions.append("אפשר לעדכן את המחיר או המלאי של המוצר")
            suggestions.append("אפשר לראות את ההזמנות שכוללות את המוצר הזה")
        
        # הצעות לאחר חיפוש הזמנות
        elif intent_type == "order_query" and subtype == "search":
            suggestions.append("אפשר לקבל מידע מפורט יותר על הזמנה ספציפית")
            suggestions.append("אפשר לעדכן את הסטטוס של אחת ההזמנות")
        
        # הצעות לאחר הצגת הזמנה
        elif intent_type == "order_query" and subtype == "get":
            suggestions.append("אפשר לעדכן את הסטטוס של ההזמנה")
            suggestions.append("אפשר לראות מידע על הלקוח שביצע את ההזמנה")
        
        # אם יש הצעות, מוסיף אותן לתשובה
        if suggestions:
            # בחירה אקראית של 1-2 הצעות
            selected_suggestions = random.sample(suggestions, min(len(suggestions), random.randint(1, 2)))
            
            # הוספת ההצעות לתשובה
            suggestions_text = "\n\n💡 " + "\n💡 ".join(selected_suggestions) + "."
            return response + suggestions_text
        
        return response

# יצירת מופע גלובלי של מחולל התשובות
response_generator = ResponseGenerator()

def generate_natural_response(intent_type: str, subtype: str, data: Dict[str, Any]) -> str:
    """
    פונקציה גלובלית לייצור תשובה טבעית
    
    Args:
        intent_type: סוג הכוונה (product_query, order_query, customer_query, action, general)
        subtype: תת-סוג הכוונה (search, get, create_success, וכו')
        data: מילון עם הנתונים להכנסה לתבנית
        
    Returns:
        תשובה טבעית בשפה העברית
    """
    return response_generator.generate_natural_response(intent_type, subtype, data)

def get_emoji(emoji_type: str) -> str:
    """
    מחזיר אימוג'י לפי סוג
    
    Args:
        emoji_type: סוג האימוג'י (product, order, customer, וכו')
        
    Returns:
        אימוג'י מתאים
    """
    return response_generator.emojis.get(emoji_type, "")

def format_with_emojis(text: str, entity_types: List[str] = None) -> str:
    """
    מוסיף אימוג'ים לטקסט לפי סוגי ישויות
    
    Args:
        text: הטקסט המקורי
        entity_types: רשימת סוגי ישויות להוספת אימוג'ים
        
    Returns:
        טקסט מעוצב עם אימוג'ים
    """
    if not entity_types:
        return text
    
    # הוספת אימוג'י בתחילת הטקסט
    emoji = get_emoji(entity_types[0])
    if emoji:
        return f"{emoji} {text}"
    
    return text 