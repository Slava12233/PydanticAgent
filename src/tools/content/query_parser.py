"""
מודול לפירוק שאילתות מורכבות (Query Parsing)

מודול זה מכיל פונקציות וכלים לפירוק שאילתות מורכבות למשימות פשוטות יותר,
זיהוי מחברים לוגיים, וטיפול בשאלות השוואתיות והיפותטיות.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union

from src.core.task_identification.intents.customer_intent import identify_specific_intent

# הגדרת לוגר
logger = logging.getLogger(__name__)

# רשימת מחברים לוגיים בעברית
LOGICAL_CONNECTORS = [
    # מחברים פשוטים
    "ו", "וגם", "או", "אבל", "אך",
    
    # מחברים מורכבים
    "ואז", "אחר כך", "לאחר מכן", "בנוסף", "כמו כן",
    "יחד עם זאת", "למרות זאת", "עם זאת", "לעומת זאת",
    
    # מחברים באנגלית
    "and", "or", "but", "however", "then", "also", "additionally"
]

# רשימת ביטויים המרמזים על שאלה השוואתית
COMPARATIVE_PHRASES = [
    # ביטויים בעברית
    "מה ההבדל בין", "השוואה בין", "להשוות בין", "תשווה בין",
    "איזה יותר", "מה יותר", "מה עדיף", "איזה עדיף",
    "מה הכי", "איזה הכי", "מי הכי",
    
    # ביטויים באנגלית
    "what is the difference between", "compare between", "which is better",
    "which is more", "what is the best", "which is the best"
]

# רשימת ביטויים המרמזים על שאלה היפותטית
HYPOTHETICAL_PHRASES = [
    # ביטויים בעברית
    "מה יקרה אם", "מה יהיה אם", "אם אני", "במידה ו", "בהנחה ש",
    "נניח ש", "בהינתן ש", "אילו", "לו", "אם הייתי",
    
    # ביטויים באנגלית
    "what if", "what would happen if", "if i", "assuming that", "given that",
    "suppose that", "hypothetically"
]


def parse_complex_query(text: str) -> List[Dict[str, Any]]:
    """
    ניתוח שאילתה מורכבת לתת-משימות
    
    Args:
        text: טקסט השאילתה
        
    Returns:
        רשימת תת-משימות
    """
    tasks = []
    
    # פיצול לפי מחברים לוגיים
    sub_queries = split_by_logical_connectors(text)
    
    # אם יש יותר מתת-שאילתה אחת, זו שאילתה מורכבת
    if len(sub_queries) > 1:
        for i, sub_query in enumerate(sub_queries):
            # זיהוי סוג המשימה של תת-השאילתה
            task_type, intent_type, score = identify_specific_intent(sub_query)
            
            # הוספת המשימה לרשימה
            tasks.append({
                "query": sub_query,
                "task_type": task_type,
                "intent_type": intent_type,
                "confidence": score,
                "order": i
            })
    else:
        # אם יש רק תת-שאילתה אחת, זו לא שאילתה מורכבת
        task_type, intent_type, score = identify_specific_intent(text)
        
        tasks.append({
            "query": text,
            "task_type": task_type,
            "intent_type": intent_type,
            "confidence": score,
            "order": 0
        })
    
    return tasks


def split_by_logical_connectors(text: str) -> List[str]:
    """
    פיצול טקסט לפי מחברים לוגיים
    
    Args:
        text: הטקסט לפיצול
        
    Returns:
        רשימת תת-שאילתות
    """
    # יצירת תבנית חיפוש למחברים לוגיים
    pattern = r'\b(' + '|'.join(LOGICAL_CONNECTORS) + r')\b'
    
    # מציאת כל המחברים הלוגיים בטקסט
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    
    # אם אין מחברים לוגיים, מחזירים את הטקסט המקורי
    if not matches:
        return [text]
    
    # פיצול הטקסט לפי המחברים הלוגיים
    sub_queries = []
    start_pos = 0
    
    for match in matches:
        # הוספת הטקסט עד המחבר הלוגי
        if match.start() > start_pos:
            sub_query = text[start_pos:match.start()].strip()
            if sub_query:
                sub_queries.append(sub_query)
        
        # עדכון מיקום ההתחלה
        start_pos = match.end()
    
    # הוספת הטקסט אחרי המחבר הלוגי האחרון
    if start_pos < len(text):
        sub_query = text[start_pos:].strip()
        if sub_query:
            sub_queries.append(sub_query)
    
    # סינון תת-שאילתות ריקות
    sub_queries = [q for q in sub_queries if q]
    
    # אם אין תת-שאילתות, מחזירים את הטקסט המקורי
    if not sub_queries:
        return [text]
    
    return sub_queries


def is_comparative_query(text: str) -> bool:
    """
    בדיקה אם השאילתה היא שאלה השוואתית
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        האם השאילתה היא שאלה השוואתית
    """
    # בדיקה אם הטקסט מכיל ביטוי השוואתי
    for phrase in COMPARATIVE_PHRASES:
        if phrase in text.lower():
            return True
    
    # בדיקה אם הטקסט מכיל את המילה "או" בין שני אובייקטים
    or_pattern = r'(?:[\w\s]+)\s+או\s+(?:[\w\s]+)'
    if re.search(or_pattern, text):
        return True
    
    # בדיקה אם הטקסט מכיל את המילה "לעומת"
    if "לעומת" in text:
        return True
    
    return False


def parse_comparative_query(text: str) -> List[Dict[str, Any]]:
    """
    פירוק שאלה השוואתית למשימות
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        רשימה של משימות לביצוע
    """
    # זיהוי האובייקטים להשוואה
    objects = extract_comparison_objects(text)
    
    # יצירת משימות להשוואה
    tasks = []
    
    # משימה ראשונה: קבלת מידע על האובייקט הראשון
    if objects and len(objects) >= 1:
        tasks.append({
            "query": f"מידע על {objects[0]}",
            "task_type": "comparison",
            "intent_type": "get_info",
            "object": objects[0],
            "confidence": 1.0,
            "order": 0
        })
    
    # משימה שנייה: קבלת מידע על האובייקט השני
    if objects and len(objects) >= 2:
        tasks.append({
            "query": f"מידע על {objects[1]}",
            "task_type": "comparison",
            "intent_type": "get_info",
            "object": objects[1],
            "confidence": 1.0,
            "order": 1
        })
    
    # משימה שלישית: השוואה בין האובייקטים
    if objects and len(objects) >= 2:
        tasks.append({
            "query": f"השוואה בין {objects[0]} ל{objects[1]}",
            "task_type": "comparison",
            "intent_type": "compare",
            "objects": objects,
            "confidence": 1.0,
            "order": 2
        })
    
    return tasks


def extract_comparison_objects(text: str) -> List[str]:
    """
    חילוץ האובייקטים להשוואה מהטקסט
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        רשימת האובייקטים להשוואה
    """
    objects = []
    
    # חיפוש דפוס "מה ההבדל בין X ל-Y"
    pattern1 = r'(?:מה ההבדל בין|השוואה בין|להשוות בין|תשווה בין)\s+([^,\s]+(?:\s+[^,\s]+)*)\s+(?:ל|ובין|ו)\s*([^,\s?\.]+(?:\s+[^,\s?\.]+)*)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        objects.append(match.group(1).strip())
        objects.append(match.group(2).strip())
        return objects
    
    # חיפוש דפוס "X או Y"
    pattern2 = r'([^,\s]+(?:\s+[^,\s]+)*)\s+או\s+([^,\s?\.]+(?:\s+[^,\s?\.]+)*)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        objects.append(match.group(1).strip())
        objects.append(match.group(2).strip())
        return objects
    
    # חיפוש דפוס "X לעומת Y"
    pattern3 = r'([^,\s]+(?:\s+[^,\s]+)*)\s+לעומת\s+([^,\s?\.]+(?:\s+[^,\s?\.]+)*)'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        objects.append(match.group(1).strip())
        objects.append(match.group(2).strip())
        return objects
    
    return objects


def is_hypothetical_query(text: str) -> bool:
    """
    בדיקה אם השאילתה היא שאלה היפותטית
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        האם השאילתה היא שאלה היפותטית
    """
    # בדיקה אם הטקסט מכיל ביטוי היפותטי
    for phrase in HYPOTHETICAL_PHRASES:
        if phrase in text.lower():
            return True
    
    return False


def parse_hypothetical_query(text: str) -> List[Dict[str, Any]]:
    """
    פירוק שאלה היפותטית למשימות
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        רשימה של משימות לביצוע
    """
    # חילוץ התנאי והתוצאה מהשאלה ההיפותטית
    condition, action = extract_hypothetical_parts(text)
    
    # יצירת משימות לטיפול בשאלה היפותטית
    tasks = []
    
    # משימה ראשונה: בדיקת התנאי
    if condition:
        tasks.append({
            "query": f"בדיקת התנאי: {condition}",
            "task_type": "hypothetical",
            "intent_type": "check_condition",
            "condition": condition,
            "confidence": 1.0,
            "order": 0
        })
    
    # משימה שנייה: סימולציית התוצאה
    if action:
        tasks.append({
            "query": f"סימולציית התוצאה: {action}",
            "task_type": "hypothetical",
            "intent_type": "simulate_result",
            "action": action,
            "confidence": 1.0,
            "order": 1
        })
    
    # משימה שלישית: ניתוח התוצאה
    if condition and action:
        tasks.append({
            "query": f"ניתוח התוצאה של {action} בהינתן {condition}",
            "task_type": "hypothetical",
            "intent_type": "analyze_result",
            "condition": condition,
            "action": action,
            "confidence": 1.0,
            "order": 2
        })
    
    return tasks


def extract_hypothetical_parts(text: str) -> Tuple[str, str]:
    """
    חילוץ התנאי והתוצאה מהשאלה ההיפותטית
    
    Args:
        text: הטקסט של השאילתה
        
    Returns:
        טאפל עם התנאי והתוצאה
    """
    # חיפוש דפוס "מה יקרה אם X"
    pattern1 = r'(?:מה יקרה אם|מה יהיה אם)\s+(.+)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        condition = match.group(1).strip()
        action = "התוצאה של " + condition
        return condition, action
    
    # חיפוש דפוס "אם X אז Y"
    pattern2 = r'(?:אם|במידה ו|בהנחה ש|נניח ש|בהינתן ש)\s+(.+?)\s+(?:אז|יקרה|יהיה|יתרחש|תהיה התוצאה)\s+(.+)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        condition = match.group(1).strip()
        action = match.group(2).strip()
        return condition, action
    
    # אם לא נמצא דפוס מתאים, מחזירים את כל הטקסט כתנאי
    return text, "" 