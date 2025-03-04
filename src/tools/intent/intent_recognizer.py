"""
מודול לזיהוי כוונות ספציפיות בשפה טבעית

מודול זה מכיל פונקציות לזיהוי כוונות ספציפיות בטקסט חופשי,
כגון יצירת מוצר, עדכון מוצר, מחיקת מוצר, ניהול הזמנות וכו'.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import json
import os
import yaml
import logfire
from difflib import SequenceMatcher

from src.tools.intent.product_intent import (
    is_product_creation_intent,
    PRODUCT_CREATION_TRIGGERS,
    extract_product_data
)
from src.tools.intent.order_intent import (
    is_order_management_intent,
    ORDER_MANAGEMENT_TRIGGERS
)
from src.tools.intent.customer_intent import (
    is_customer_management_intent,
    CUSTOMER_MANAGEMENT_TRIGGERS
)

logger = logging.getLogger(__name__)

# הגדרת כוונות ספציפיות לפי סוגי משימות
SPECIFIC_INTENTS = {
    "product_management": {
        "create_product": {
            "keywords": PRODUCT_CREATION_TRIGGERS["direct_creation"] + 
                        PRODUCT_CREATION_TRIGGERS["indirect_creation"] + 
                        PRODUCT_CREATION_TRIGGERS["product_type_specific"],
            "description": "יצירת מוצר חדש בחנות"
        },
        "update_product": {
            "keywords": [
                # ביטויים לעדכון מוצר
                "עדכן מוצר", "שנה מוצר", "ערוך מוצר", "לעדכן מוצר", "לשנות מוצר", "לערוך מוצר",
                "update product", "edit product", "modify product", "change product",
                "תעדכן מוצר", "תשנה מוצר", "תערוך מוצר", "תעדכן לי מוצר", "תשנה לי מוצר",
                "לשנות את המוצר", "לעדכן את המוצר", "לערוך את המוצר",
                "רוצה לעדכן מוצר", "אני רוצה לשנות מוצר", "אפשר לעדכן מוצר", "אפשר לשנות מוצר",
                "איך אני מעדכן מוצר", "איך משנים מוצר", "איך עורכים מוצר",
                "שינוי מחיר", "עדכון מחיר", "שינוי תיאור", "עדכון תיאור", "שינוי תמונה", "עדכון תמונה",
                "לשנות מחיר", "לעדכן מחיר", "לשנות תיאור", "לעדכן תיאור", "לשנות תמונה", "לעדכן תמונה"
            ],
            "description": "עדכון מוצר קיים בחנות"
        },
        "delete_product": {
            "keywords": [
                # ביטויים למחיקת מוצר
                "מחק מוצר", "הסר מוצר", "למחוק מוצר", "להסיר מוצר", "מחיקת מוצר", "הסרת מוצר",
                "delete product", "remove product", "delete a product", "remove a product",
                "תמחק מוצר", "תסיר מוצר", "תמחק לי מוצר", "תסיר לי מוצר",
                "למחוק את המוצר", "להסיר את המוצר",
                "רוצה למחוק מוצר", "אני רוצה להסיר מוצר", "אפשר למחוק מוצר", "אפשר להסיר מוצר",
                "איך אני מוחק מוצר", "איך מוחקים מוצר", "איך מסירים מוצר"
            ],
            "description": "מחיקת מוצר מהחנות"
        },
        "get_product": {
            "keywords": [
                # ביטויים להצגת מוצר
                "הצג מוצר", "מידע על מוצר", "פרטי מוצר", "להציג מוצר", "לראות מוצר",
                "show product", "product info", "product details", "view product",
                "תציג מוצר", "תראה מוצר", "תציג לי מוצר", "תראה לי מוצר",
                "להציג את המוצר", "לראות את המוצר",
                "רוצה לראות מוצר", "אני רוצה להציג מוצר", "אפשר לראות מוצר", "אפשר להציג מוצר",
                "איך אני רואה מוצר", "איך מציגים מוצר", "איך רואים מוצר"
            ],
            "description": "הצגת פרטי מוצר"
        },
        "list_products": {
            "keywords": [
                # ביטויים להצגת רשימת מוצרים
                "הצג מוצרים", "רשימת מוצרים", "כל המוצרים", "להציג מוצרים", "לראות מוצרים",
                "show products", "list products", "all products", "view products",
                "תציג מוצרים", "תראה מוצרים", "תציג לי מוצרים", "תראה לי מוצרים",
                "להציג את המוצרים", "לראות את המוצרים",
                "רוצה לראות מוצרים", "אני רוצה להציג מוצרים", "אפשר לראות מוצרים", "אפשר להציג מוצרים",
                "איך אני רואה מוצרים", "איך מציגים מוצרים", "איך רואים מוצרים",
                "הצג לי את המוצרים", "תראה לי את המוצרים", "אני רוצה לראות את המוצרים",
                "מה המוצרים שיש", "אילו מוצרים יש", "איזה מוצרים יש"
            ],
            "description": "הצגת רשימת מוצרים"
        }
    },
    "order_management": {
        "get_orders": {
            "keywords": ORDER_MANAGEMENT_TRIGGERS["get_orders"] + [
                "הצג לי את ההזמנות", "תראה לי את ההזמנות", "אני רוצה לראות את ההזמנות",
                "מה ההזמנות שיש", "אילו הזמנות יש", "איזה הזמנות יש"
            ],
            "description": "הצגת רשימת הזמנות"
        },
        "get_order": {
            "keywords": ORDER_MANAGEMENT_TRIGGERS["get_order"],
            "description": "הצגת פרטי הזמנה"
        },
        "update_order_status": {
            "keywords": ORDER_MANAGEMENT_TRIGGERS["update_order_status"] + [
                "עדכן את הסטטוס של הזמנה", "שנה את הסטטוס של הזמנה",
                "עדכן את מצב ההזמנה", "שנה את מצב ההזמנה"
            ],
            "description": "עדכון סטטוס הזמנה"
        },
        "cancel_order": {
            "keywords": ORDER_MANAGEMENT_TRIGGERS["cancel_order"],
            "description": "ביטול הזמנה"
        },
        "refund_order": {
            "keywords": ORDER_MANAGEMENT_TRIGGERS["refund_order"],
            "description": "ביצוע החזר כספי"
        }
    },
    "customer_management": {
        "get_customers": {
            "keywords": CUSTOMER_MANAGEMENT_TRIGGERS["get_customers"] + [
                "הצג לי את הלקוחות", "תראה לי את הלקוחות", "אני רוצה לראות את הלקוחות",
                "מה הלקוחות שיש", "אילו לקוחות יש", "איזה לקוחות יש"
            ],
            "description": "הצגת רשימת לקוחות"
        },
        "get_customer": {
            "keywords": CUSTOMER_MANAGEMENT_TRIGGERS["get_customer"],
            "description": "הצגת פרטי לקוח"
        },
        "create_customer": {
            "keywords": CUSTOMER_MANAGEMENT_TRIGGERS["create_customer"],
            "description": "יצירת לקוח חדש"
        },
        "update_customer": {
            "keywords": CUSTOMER_MANAGEMENT_TRIGGERS["update_customer"],
            "description": "עדכון פרטי לקוח"
        },
        "delete_customer": {
            "keywords": CUSTOMER_MANAGEMENT_TRIGGERS["delete_customer"],
            "description": "מחיקת לקוח"
        }
    },
    "inventory_management": {
        "update_inventory": {
            "keywords": [
                # ביטויים לעדכון מלאי
                "עדכן מלאי", "שנה מלאי", "לעדכן מלאי", "לשנות מלאי", "עדכון מלאי", "שינוי מלאי",
                "update inventory", "change inventory", "update stock", "change stock",
                "תעדכן מלאי", "תשנה מלאי", "תעדכן את המלאי", "תשנה את המלאי",
                "רוצה לעדכן מלאי", "אני רוצה לשנות מלאי", "אפשר לעדכן מלאי", "אפשר לשנות מלאי",
                "איך אני מעדכן מלאי", "איך משנים מלאי", "איך מעדכנים מלאי",
                "הוסף למלאי", "הפחת מהמלאי", "להוסיף למלאי", "להפחית מהמלאי",
                "add to inventory", "reduce from inventory", "add to stock", "reduce from stock"
            ],
            "description": "עדכון מלאי מוצרים"
        },
        "check_inventory": {
            "keywords": [
                # ביטויים לבדיקת מלאי
                "בדוק מלאי", "הצג מלאי", "לבדוק מלאי", "להציג מלאי", "בדיקת מלאי", "הצגת מלאי",
                "check inventory", "show inventory", "check stock", "show stock",
                "תבדוק מלאי", "תציג מלאי", "תבדוק את המלאי", "תציג את המלאי",
                "רוצה לבדוק מלאי", "אני רוצה לראות מלאי", "אפשר לבדוק מלאי", "אפשר לראות מלאי",
                "איך אני בודק מלאי", "איך רואים מלאי", "איך בודקים מלאי",
                "כמה יש במלאי", "כמה נשאר", "כמה יחידות", "כמה פריטים",
                "how much in stock", "how many left", "how many units", "how many items"
            ],
            "description": "בדיקת מלאי מוצרים"
        }
    },
    "document_management": {
        "search_documents": {
            "description": "חיפוש מסמכים",
            "keywords": [
                "חפש מסמך", "חפש מסמכים", "מצא מסמך", "מצא מסמכים", "חיפוש מסמך", "חיפוש מסמכים",
                "אני מחפש מסמך", "אני מחפש מסמכים", "יש לי מסמך", "יש לי מסמכים", "מסמך שקשור ל",
                "מסמכים שקשורים ל", "מסמך על", "מסמכים על", "מסמך בנושא", "מסמכים בנושא",
                "search document", "search documents", "find document", "find documents"
            ],
            "parameters": ["query"]
        },
        "list_documents": {
            "description": "הצגת רשימת מסמכים",
            "keywords": [
                "הצג מסמכים", "רשימת מסמכים", "אילו מסמכים יש", "אילו מסמכים יש לי", "מה המסמכים שיש לי",
                "הראה לי את המסמכים", "הראה את המסמכים", "הצג את המסמכים", "הצג לי את המסמכים",
                "אילו מסמכים יש במאגר", "מה יש במאגר", "מה יש לי במאגר", "מה המסמכים במאגר",
                "איזה מסמכים יש לי", "איזה מסמכים יש", "איזה מסמכים יש במאגר", "איזה מסמכים קיימים",
                "list documents", "show documents", "show me documents", "what documents do i have",
                "מסמכים שלי", "המסמכים שלי", "כל המסמכים", "כל המסמכים שלי"
            ],
            "parameters": []
        },
        "add_document": {
            "description": "הוספת מסמך חדש",
            "keywords": [
                "הוסף מסמך", "הוסף מסמך חדש", "צור מסמך", "צור מסמך חדש", "העלה מסמך", "העלה מסמך חדש",
                "אני רוצה להוסיף מסמך", "אני רוצה להעלות מסמך", "אני רוצה ליצור מסמך",
                "add document", "create document", "upload document", "new document"
            ],
            "parameters": ["title", "content"]
        },
        "delete_document": {
            "description": "מחיקת מסמך",
            "keywords": [
                "מחק מסמך", "הסר מסמך", "מחיקת מסמך", "הסרת מסמך", "אני רוצה למחוק מסמך", "אני רוצה להסיר מסמך",
                "delete document", "remove document"
            ],
            "parameters": ["document_id"]
        }
    }
}

def calculate_intent_score(text: str, keywords: List[str]) -> float:
    """
    חישוב ציון התאמה של טקסט לרשימת מילות מפתח
    
    Args:
        text: הטקסט לבדיקה
        keywords: רשימת מילות מפתח
        
    Returns:
        ציון התאמה (גבוה יותר = התאמה טובה יותר)
    """
    text_lower = text.lower()
    score = 0.0
    
    # מילון לשמירת הציון הגבוה ביותר לכל מילת מפתח שנמצאה
    # זה מונע כפילויות כאשר יש מילות מפתח דומות
    best_keyword_scores = {}
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        if keyword_lower in text_lower:
            # מילות מפתח ארוכות יותר מקבלות ניקוד גבוה יותר
            keyword_score = len(keyword) / 2
            
            # ביטויים בתחילת ההודעה מקבלים ניקוד גבוה יותר
            if text_lower.startswith(keyword_lower) or text_lower.startswith(f"{keyword_lower} "):
                keyword_score *= 1.8  # הגדלת המשקל של ביטויים בתחילת ההודעה
            
            # ביטויים שמופיעים כמילים שלמות מקבלים ניקוד גבוה יותר
            if f" {keyword_lower} " in f" {text_lower} ":
                keyword_score *= 1.3
            
            # ביטויים ארוכים יותר (כמו משפטים) מקבלים ניקוד גבוה יותר
            if len(keyword_lower.split()) > 2:
                keyword_score *= 1.5  # הגדלת המשקל של ביטויים ארוכים
            
            # ביטויים שמופיעים יותר מפעם אחת מקבלים ניקוד גבוה יותר
            occurrences = text_lower.count(keyword_lower)
            if occurrences > 1:
                keyword_score *= 1.0 + (0.2 * min(occurrences, 3))  # מקסימום 60% בונוס
            
            # שמירת הציון הגבוה ביותר לכל מילת מפתח
            if keyword_lower not in best_keyword_scores or keyword_score > best_keyword_scores[keyword_lower]:
                best_keyword_scores[keyword_lower] = keyword_score
    
    # סכימת הציונים הגבוהים ביותר
    score = sum(best_keyword_scores.values())
    
    # בונוס אם נמצאו מספר מילות מפתח שונות
    if len(best_keyword_scores) > 1:
        score *= 1.0 + (0.1 * min(len(best_keyword_scores), 5))  # מקסימום 50% בונוס
    
    return score

def identify_specific_intent(text: str, task_type: str = None) -> Tuple[str, str, float]:
    """
    זיהוי כוונה ספציפית בטקסט
    
    Args:
        text: הטקסט לבדיקה
        task_type: סוג המשימה (אופציונלי, אם ידוע מראש)
        
    Returns:
        טאפל עם: סוג המשימה, הכוונה הספציפית, וציון ההתאמה
    """
    # בדיקה אם הטקסט קצר מדי (כמו "היי", "שלום" וכו')
    if len(text.strip()) <= 5:
        return "general", "greeting", 10.0
        
    text_lower = text.lower()
    
    # בדיקה אם זו ברכה או פתיחת שיחה
    greetings = ["היי", "הי", "שלום", "בוקר טוב", "ערב טוב", "צהריים טובים", "מה שלומך", 
                "מה נשמע", "מה קורה", "hello", "hi", "hey", "good morning", "good evening"]
    
    if any(text_lower.startswith(greeting) for greeting in greetings) or any(greeting in text_lower for greeting in greetings):
        return "general", "greeting", 10.0
    
    # אם לא צוין סוג משימה, ננסה לזהות אותו
    if task_type is None:
        # בדיקת כל סוגי המשימות ומציאת הסוג עם הציון הגבוה ביותר
        task_scores = {}
        
        for task in SPECIFIC_INTENTS.keys():
            task_score = 0
            for intent_type, intent_data in SPECIFIC_INTENTS[task].items():
                intent_score = calculate_intent_score(text, intent_data["keywords"])
                task_score += intent_score
            task_scores[task] = task_score
        
        # בחירת המשימה עם הניקוד הגבוה ביותר
        if any(task_scores.values()):
            best_task = max(task_scores.items(), key=lambda x: x[1])
            if best_task[1] > 0:
                task_type = best_task[0]
        else:
            task_type = "general"
    
    # אם זוהה סוג משימה ספציפי, ננסה לזהות את הכוונה הספציפית
    if task_type in SPECIFIC_INTENTS:
        intent_scores = {}
        for intent_type, intent_data in SPECIFIC_INTENTS[task_type].items():
            intent_score = calculate_intent_score(text, intent_data["keywords"])
            intent_scores[intent_type] = intent_score
        
        # בחירת הכוונה עם הניקוד הגבוה ביותר
        if any(intent_scores.values()):
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return task_type, best_intent[0], best_intent[1]
    
    # אם לא זוהתה כוונה ספציפית, נחזיר כוונה כללית
    return task_type, "general", 0.0

def get_intent_description(task_type: str, intent_type: str) -> str:
    """
    קבלת תיאור של כוונה ספציפית
    
    Args:
        task_type: סוג המשימה
        intent_type: סוג הכוונה
        
    Returns:
        תיאור הכוונה
    """
    if task_type in SPECIFIC_INTENTS and intent_type in SPECIFIC_INTENTS[task_type]:
        return SPECIFIC_INTENTS[task_type][intent_type]["description"]
    return "כוונה כללית"

def extract_parameters_by_intent(text: str, task_type: str, intent_type: str) -> Dict[str, Any]:
    """
    חילוץ פרמטרים מטקסט לפי סוג הכוונה
    
    Args:
        text: הטקסט לחילוץ
        task_type: סוג המשימה
        intent_type: סוג הכוונה הספציפית
        
    Returns:
        מילון עם הפרמטרים שחולצו
    """
    # טיפול בברכות ושיחות כלליות
    if task_type == "general" and intent_type == "greeting":
        return {
            "greeting": True,
            "message": text.strip()
        }
    
    # טיפול בניהול מוצרים
    if task_type == "product_management":
        # יצירת מוצר
        if intent_type == "create_product":
            product_data = extract_product_data(text)
            return {"product_data": product_data}
        
        # עדכון מוצר
        elif intent_type == "update_product":
            product_id = extract_product_id(text)
            product_data = extract_product_data(text)
            
            # חילוץ שם מוצר מהטקסט אם יש
            product_name = None
            product_name_patterns = [
                r'מוצר\s+["\']([^"\']+)["\']',
                r'מוצר\s+בשם\s+["\']?([^"\']+)["\']?',
                r'(?:עדכן|שנה|ערוך)\s+(?:את\s+)?(?:ה)?מוצר\s+["\']?([^"\']+)["\']?',
                r'(?:update|change|edit)\s+(?:the\s+)?product\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in product_name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    product_name = match.group(1)
                    break
            
            params = {"product_data": product_data}
            if product_id:
                params["product_id"] = product_id
            if product_name:
                params["product_name"] = product_name
            return params
        
        # מחיקת מוצר
        elif intent_type == "delete_product":
            product_id = extract_product_id(text)
            
            # חילוץ שם מוצר מהטקסט אם יש
            product_name = None
            product_name_patterns = [
                r'מוצר\s+["\']([^"\']+)["\']',
                r'מוצר\s+בשם\s+["\']?([^"\']+)["\']?',
                r'(?:מחק|הסר)\s+(?:את\s+)?(?:ה)?מוצר\s+["\']?([^"\']+)["\']?',
                r'(?:delete|remove)\s+(?:the\s+)?product\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in product_name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    product_name = match.group(1)
                    break
            
            params = {}
            if product_id:
                params["product_id"] = product_id
            if product_name:
                params["product_name"] = product_name
            return params
        
        # הצגת מוצר ספציפי
        elif intent_type == "get_product":
            product_id = extract_product_id(text)
            
            # חילוץ שם מוצר מהטקסט אם יש
            product_name = None
            product_name_patterns = [
                r'מוצר\s+["\']([^"\']+)["\']',
                r'מוצר\s+בשם\s+["\']?([^"\']+)["\']?',
                r'(?:הצג|תראה)\s+(?:את\s+)?(?:ה)?מוצר\s+["\']?([^"\']+)["\']?',
                r'(?:show|display)\s+(?:the\s+)?product\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in product_name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    product_name = match.group(1)
                    break
            
            params = {}
            if product_id:
                params["product_id"] = product_id
            if product_name:
                params["product_name"] = product_name
            return params
        
        # הצגת רשימת מוצרים
        elif intent_type == "list_products":
            # חילוץ פרמטרים לסינון רשימת המוצרים
            category = None
            category_patterns = [
                r'בקטגוריה\s+["\']?([^"\']+)["\']?',
                r'מהקטגוריה\s+["\']?([^"\']+)["\']?',
                r'(?:in|from)\s+(?:the\s+)?category\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in category_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    category = match.group(1)
                    break
            
            # חילוץ מספר המוצרים להצגה
            limit = None
            limit_patterns = [
                r'(?:הצג|תראה)\s+(\d+)\s+מוצרים',
                r'(\d+)\s+מוצרים',
                r'(?:show|display)\s+(\d+)\s+products',
                r'(\d+)\s+products'
            ]
            
            for pattern in limit_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        limit = int(match.group(1))
                    except ValueError:
                        pass
                    break
            
            params = {}
            if category:
                params["category"] = category
            if limit:
                params["limit"] = limit
            return params
    
    # טיפול בניהול הזמנות
    elif task_type == "order_management":
        # הצגת רשימת הזמנות
        if intent_type == "get_orders":
            # חילוץ פרמטרים לסינון רשימת ההזמנות
            from src.tools.intent.order_intent import extract_date_range, extract_order_filters
            
            date_range = extract_date_range(text)
            filters = extract_order_filters(text)
            
            params = {}
            if date_range:
                params["date_range"] = date_range
            if filters:
                params.update(filters)
            return params
        
        # הצגת הזמנה ספציפית
        elif intent_type == "get_order":
            from src.tools.intent.order_intent import extract_order_id
            
            order_id = extract_order_id(text)
            params = {}
            if order_id:
                params["order_id"] = order_id
            return params
        
        # עדכון סטטוס הזמנה
        elif intent_type == "update_order_status":
            from src.tools.intent.order_intent import extract_order_id, extract_order_status
            
            order_id = extract_order_id(text)
            status = extract_order_status(text)
            
            params = {}
            if order_id:
                params["order_id"] = order_id
            if status:
                params["status"] = status
            return params
        
        # ביטול הזמנה
        elif intent_type == "cancel_order":
            from src.tools.intent.order_intent import extract_order_id
            
            order_id = extract_order_id(text)
            params = {}
            if order_id:
                params["order_id"] = order_id
            return params
        
        # החזר כספי
        elif intent_type == "refund_order":
            from src.tools.intent.order_intent import extract_order_id
            
            order_id = extract_order_id(text)
            
            # חילוץ סכום ההחזר אם צוין
            amount = None
            amount_patterns = [
                r'החזר\s+(?:של\s+)?(\d+(?:\.\d+)?)\s*(?:שקל|ש"ח|\₪)?',
                r'להחזיר\s+(?:סכום\s+של\s+)?(\d+(?:\.\d+)?)\s*(?:שקל|ש"ח|\₪)?',
                r'refund\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:NIS|ILS|\$)?'
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount = float(match.group(1))
                    except ValueError:
                        pass
                    break
            
            params = {}
            if order_id:
                params["order_id"] = order_id
            if amount:
                params["amount"] = amount
            return params
    
    # טיפול בניהול לקוחות
    elif task_type == "customer_management":
        # הצגת לקוח ספציפי
        if intent_type == "get_customer":
            # חילוץ מזהה לקוח
            customer_id = None
            customer_id_patterns = [
                r'לקוח\s+(?:מספר|מס[\'"]?|#)?\s*(\d+)',
                r'customer\s+(?:number|#|id)?\s*(\d+)'
            ]
            
            for pattern in customer_id_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        customer_id = int(match.group(1))
                    except ValueError:
                        pass
                    break
            
            # חילוץ שם לקוח או אימייל
            customer_identifier = None
            identifier_patterns = [
                r'לקוח\s+["\']([^"\']+)["\']',
                r'לקוח\s+בשם\s+["\']?([^"\']+)["\']?',
                r'(?:הצג|תראה)\s+(?:את\s+)?(?:ה)?לקוח\s+["\']?([^"\']+)["\']?',
                r'(?:show|display)\s+(?:the\s+)?customer\s+["\']?([^"\']+)["\']?',
                r'(?:[\w\.-]+@[\w\.-]+\.\w+)'  # תבנית אימייל
            ]
            
            for pattern in identifier_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    customer_identifier = match.group(1)
                    break
            
            params = {}
            if customer_id:
                params["customer_id"] = customer_id
            if customer_identifier:
                # בדיקה אם זה אימייל
                if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', customer_identifier):
                    params["email"] = customer_identifier
                else:
                    params["name"] = customer_identifier
            return params
    
    # טיפול בניהול מלאי
    elif task_type == "inventory_management":
        # עדכון מלאי
        if intent_type == "update_inventory":
            # חילוץ שם מוצר
            product_name = None
            product_name_patterns = [
                r'מוצר\s+["\']([^"\']+)["\']',
                r'מוצר\s+בשם\s+["\']?([^"\']+)["\']?',
                r'(?:עדכן|שנה)\s+(?:את\s+)?(?:ה)?מלאי\s+(?:של\s+)?(?:ה)?מוצר\s+["\']?([^"\']+)["\']?',
                r'(?:update|change)\s+(?:the\s+)?inventory\s+(?:of\s+)?(?:the\s+)?product\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in product_name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    product_name = match.group(1)
                    break
            
            # חילוץ כמות
            quantity = None
            quantity_patterns = [
                r'(?:כמות|מלאי)\s+(?:של\s+)?(\d+)',
                r'(\d+)\s+(?:יחידות|פריטים)',
                r'(?:quantity|stock)\s+(?:of\s+)?(\d+)',
                r'(\d+)\s+(?:units|items)'
            ]
            
            for pattern in quantity_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        quantity = int(match.group(1))
                    except ValueError:
                        pass
                    break
            
            params = {}
            if product_name:
                params["product_name"] = product_name
            if quantity is not None:
                params["quantity"] = quantity
            return params
    
    # טיפול בניתוח מכירות
    elif task_type == "sales_analysis":
        # דוח מכירות
        if intent_type == "get_sales_report":
            # חילוץ טווח תאריכים
            from src.tools.intent.order_intent import extract_date_range
            
            date_range = extract_date_range(text)
            
            # חילוץ סוג הדוח
            report_type = None
            report_type_patterns = [
                r'דוח\s+(?:על\s+)?([^,\.\s]+)',
                r'report\s+(?:on\s+)?([^,\.\s]+)'
            ]
            
            for pattern in report_type_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    report_type = match.group(1)
                    break
            
            params = {}
            if date_range:
                params["date_range"] = date_range
            if report_type:
                params["report_type"] = report_type
            return params
    
    # אם לא זוהו פרמטרים ספציפיים, נחזיר מילון ריק
    return {}

class IntentRecognizer:
    """מזהה כוונות המשתמש"""
    
    def __init__(self):
        """אתחול מזהה הכוונות"""
        self.keywords = {}
        self._load_keywords()
        
    def _load_keywords(self):
        """טעינת מילות המפתח מקובץ ההגדרות"""
        try:
            # קריאת קובץ מילות המפתח
            keywords_path = os.path.join(os.path.dirname(__file__), 'keywords.yaml')
            with open(keywords_path, 'r', encoding='utf-8') as f:
                self.keywords = yaml.safe_load(f)
                
            logfire.info('keywords_loaded', count=len(self.keywords))
        except Exception as e:
            logfire.error('keywords_loading_error', error=str(e))
            raise RuntimeError(f"שגיאה בטעינת מילות המפתח: {e}")
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        חישוב מידת הדמיון בין שתי מחרוזות
        
        Args:
            text1: מחרוזת ראשונה
            text2: מחרוזת שנייה
            
        Returns:
            מידת הדמיון (0-1)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _find_best_match(self, text: str, keywords: List[str]) -> Tuple[str, float]:
        """
        מציאת ההתאמה הטובה ביותר מתוך רשימת מילות מפתח
        
        Args:
            text: הטקסט לחיפוש
            keywords: רשימת מילות מפתח
            
        Returns:
            מילת המפתח המתאימה ביותר וציון ההתאמה
        """
        best_match = ""
        best_score = 0.0
        
        for keyword in keywords:
            score = self._calculate_similarity(text, keyword)
            if score > best_score:
                best_score = score
                best_match = keyword
                
        return best_match, best_score
    
    def _get_task_type_score(self, text: str, task_type: str) -> float:
        """
        חישוב ציון ההתאמה לסוג משימה
        
        Args:
            text: הטקסט לבדיקה
            task_type: סוג המשימה
            
        Returns:
            ציון ההתאמה
        """
        task_keywords = self.keywords['task_types'][task_type]['keywords']
        _, score = self._find_best_match(text, task_keywords)
        return score
    
    def _get_intent_score(self, text: str, task_type: str, intent: str) -> float:
        """
        חישוב ציון ההתאמה לכוונה ספציפית
        
        Args:
            text: הטקסט לבדיקה
            task_type: סוג המשימה
            intent: הכוונה הספציפית
            
        Returns:
            ציון ההתאמה
        """
        intent_keywords = self.keywords['task_types'][task_type]['intents'][intent]['keywords']
        _, score = self._find_best_match(text, intent_keywords)
        return score
    
    def identify_intent(self, text: str) -> Tuple[str, str, float]:
        """
        זיהוי כוונת המשתמש מתוך טקסט
        
        Args:
            text: הטקסט לזיהוי
            
        Returns:
            סוג המשימה, הכוונה הספציפית וציון הביטחון
        """
        best_task_type = "general"
        best_intent = "general"
        best_score = 0.0
        
        # בדיקת כל סוגי המשימות
        for task_type in self.keywords['task_types']:
            # חישוב ציון לסוג המשימה
            task_score = self._get_task_type_score(text, task_type)
            
            # אם נמצאה התאמה טובה, בדיקת כוונות ספציפיות
            if task_score > 0.6:
                for intent in self.keywords['task_types'][task_type].get('intents', {}):
                    intent_score = self._get_intent_score(text, task_type, intent)
                    
                    # שקלול הציונים
                    combined_score = (task_score + intent_score) / 2
                    if combined_score > best_score:
                        best_score = combined_score
                        best_task_type = task_type
                        best_intent = intent
        
        logfire.info('intent_identified', 
                    task_type=best_task_type,
                    intent=best_intent,
                    score=best_score,
                    text=text[:100])
                    
        return best_task_type, best_intent, best_score * 20  # המרה לסקלה של 0-20

    def get_suggested_responses(self, task_type: str, intent: str) -> List[str]:
        """
        קבלת תשובות מוצעות לכוונה ספציפית
        
        Args:
            task_type: סוג המשימה
            intent: הכוונה הספציפית
            
        Returns:
            רשימת תשובות מוצעות
        """
        # TODO: להוסיף תשובות מוצעות לכל כוונה
        return []
    
    def learn_from_interaction(self, text: str, task_type: str, intent: str, success: bool):
        """
        למידה מאינטראקציה עם המשתמש
        
        Args:
            text: הטקסט המקורי
            task_type: סוג המשימה שזוהה
            intent: הכוונה שזוהתה
            success: האם הזיהוי היה מוצלח
        """
        # TODO: להוסיף מנגנון למידה מאינטראקציות
        pass

# יצירת מופע גלובלי של מזהה הכוונות
intent_recognizer = IntentRecognizer()