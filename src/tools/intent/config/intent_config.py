"""
קובץ קונפיגורציה למערכת זיהוי כוונות
"""
from typing import Dict, List, Any
import json
import os
from pathlib import Path

# נתיב לקבצי קונפיגורציה
CONFIG_DIR = Path(__file__).parent

# הגדרות כלליות
GENERAL_SETTINGS = {
    "min_confidence_score": 0.5,
    "max_keywords_per_intent": 20,
    "min_keyword_length": 2,
    "max_keyword_length": 30,
    "learning_rate": 0.1,
    "update_threshold": 0.3
}

# מילות מפתח לפי סוגי כוונות
INTENT_KEYWORDS = {
    "product": {
        "create": [
            "צור", "הוסף", "חדש", "יצירת", "הוספת",
            "מוצר", "פריט", "מוצרים", "פריטים"
        ],
        "update": [
            "עדכן", "שנה", "ערוך", "עדכון", "שינוי",
            "עריכת", "מוצר", "פריט"
        ],
        "delete": [
            "מחק", "הסר", "מחיקת", "הסרת",
            "מוצר", "פריט"
        ],
        "view": [
            "הצג", "ראה", "מצא", "חפש", "הראה",
            "מוצר", "פריט", "מוצרים", "פריטים"
        ]
    },
    "order": {
        "create": [
            "צור", "הוסף", "חדש", "יצירת", "הוספת",
            "הזמנה", "הזמנות"
        ],
        "update": [
            "עדכן", "שנה", "ערוך", "עדכון", "שינוי",
            "עריכת", "הזמנה", "סטטוס"
        ],
        "cancel": [
            "בטל", "מחק", "ביטול", "מחיקת",
            "הזמנה", "הזמנות"
        ],
        "view": [
            "הצג", "ראה", "מצא", "חפש", "הראה",
            "הזמנה", "הזמנות", "סטטוס"
        ]
    },
    "customer": {
        "create": [
            "צור", "הוסף", "חדש", "יצירת", "הוספת",
            "לקוח", "משתמש"
        ],
        "update": [
            "עדכן", "שנה", "ערוך", "עדכון", "שינוי",
            "עריכת", "לקוח", "משתמש", "פרטים"
        ],
        "delete": [
            "מחק", "הסר", "מחיקת", "הסרת",
            "לקוח", "משתמש"
        ],
        "view": [
            "הצג", "ראה", "מצא", "חפש", "הראה",
            "לקוח", "משתמש", "לקוחות", "משתמשים"
        ]
    }
}

# תבניות לזיהוי כוונות
INTENT_PATTERNS = {
    "product": {
        "create": r"(?:צור|הוסף|חדש)\s+(?:מוצר|פריט)",
        "update": r"(?:עדכן|שנה|ערוך)\s+(?:מוצר|פריט)",
        "delete": r"(?:מחק|הסר)\s+(?:מוצר|פריט)",
        "view": r"(?:הצג|ראה|מצא|חפש)\s+(?:מוצר|פריט)"
    },
    "order": {
        "create": r"(?:צור|הוסף|חדש)\s+(?:הזמנה)",
        "update": r"(?:עדכן|שנה|ערוך)\s+(?:הזמנה|סטטוס)",
        "cancel": r"(?:בטל|מחק)\s+(?:הזמנה)",
        "view": r"(?:הצג|ראה|מצא|חפש)\s+(?:הזמנה|סטטוס)"
    },
    "customer": {
        "create": r"(?:צור|הוסף|חדש)\s+(?:לקוח|משתמש)",
        "update": r"(?:עדכן|שנה|ערוך)\s+(?:לקוח|משתמש)",
        "delete": r"(?:מחק|הסר)\s+(?:לקוח|משתמש)",
        "view": r"(?:הצג|ראה|מצא|חפש)\s+(?:לקוח|משתמש)"
    }
}

def load_custom_keywords() -> Dict[str, Dict[str, List[str]]]:
    """
    טעינת מילות מפתח מותאמות אישית מקובץ JSON
    
    Returns:
        מילון של מילות מפתח מותאמות אישית
    """
    custom_keywords_path = CONFIG_DIR / "custom_keywords.json"
    if custom_keywords_path.exists():
        with open(custom_keywords_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_custom_keywords(keywords: Dict[str, Dict[str, List[str]]]) -> None:
    """
    שמירת מילות מפתח מותאמות אישית לקובץ JSON
    
    Args:
        keywords: מילון של מילות מפתח מותאמות אישית
    """
    custom_keywords_path = CONFIG_DIR / "custom_keywords.json"
    with open(custom_keywords_path, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)

def get_all_keywords() -> Dict[str, Dict[str, List[str]]]:
    """
    קבלת כל מילות המפתח (מובנות + מותאמות אישית)
    
    Returns:
        מילון משולב של כל מילות המפתח
    """
    custom_keywords = load_custom_keywords()
    all_keywords = INTENT_KEYWORDS.copy()
    
    # מיזוג מילות מפתח מותאמות אישית
    for intent_type, actions in custom_keywords.items():
        if intent_type not in all_keywords:
            all_keywords[intent_type] = {}
        for action, keywords in actions.items():
            if action not in all_keywords[intent_type]:
                all_keywords[intent_type][action] = []
            all_keywords[intent_type][action].extend(keywords)
    
    return all_keywords 