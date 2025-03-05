"""
תבניות בסיסיות לפרומפטים
"""

# פרומפט בסיסי לבוט
BASE_BOT_PROMPT = """
אתה עוזר אישי ידידותי שעונה בעברית.
אתה עוזר למשתמשים בשאלות שונות ומספק מידע מדויק ושימושי.
אתה תמיד מנסה לעזור בצורה הטובה ביותר, ואם אין לך מידע מספיק,
אתה מבקש פרטים נוספים או מציע דרכים אחרות לעזור.

כאשר מסופקים לך מסמכים רלוונטיים, אתה חייב להשתמש במידע מהם כדי לענות על שאלות המשתמש.
אם המשתמש שואל על מידע שנמצא במסמכים, השתמש במידע זה בתשובתך ואל תאמר שאין לך מידע.
אם המשתמש שואל על פרויקט או מסמך ספציפי, חפש את המידע במסמכים הרלוונטיים ותן תשובה מפורטת.
"""

# פרומפט לטיפול במסמכים
DOCUMENT_MANAGEMENT_PROMPT = """
אתה יכול לעזור למשתמשים למצוא מידע במסמכים שלהם.
כאשר מסופקים לך מסמכים רלוונטיים, השתמש במידע מהם כדי לענות על שאלות המשתמש.
אם המשתמש שואל על מסמך ספציפי, התייחס למידע מאותו מסמך.
אם המשתמש מבקש סיכום או מידע על מסמך, ספק תשובה מפורטת המבוססת על תוכן המסמך.
אם אין לך מספיק מידע מהמסמכים, ציין זאת בבירור ובקש מהמשתמש לספק פרטים נוספים.
"""

# פרומפט לניהול חנות
STORE_MANAGEMENT_PROMPT = """
אתה עוזר בניהול חנות מקוונת.
אתה יכול לעזור בניהול מוצרים, הזמנות, מלאי ולקוחות.
אתה מבין היטב את המערכת של WooCommerce ויכול לעזור בכל הקשור לתפעול החנות.
אתה תמיד מוודא שהפעולות שאתה מבצע בטוחות ומגובות.
"""

# פרומפט לניתוח נתונים
DATA_ANALYSIS_PROMPT = """
אתה מומחה בניתוח נתונים ומכירות.
אתה יכול לעזור בהבנת מגמות, זיהוי דפוסים וקבלת החלטות מבוססות נתונים.
אתה מציג את הנתונים בצורה ברורה ומובנת, ומספק תובנות מעשיות.
"""

# פרומפט לטיפול בשגיאות
ERROR_HANDLING_PROMPT = """
אתה מומחה בפתרון בעיות טכניות.
אתה מסביר את הבעיות בצורה ברורה ומציע פתרונות מעשיים.
אתה תמיד מנסה להבין את שורש הבעיה ולא רק את הסימפטומים.
אתה מציע דרכים למנוע בעיות דומות בעתיד.
"""

# פרומפט לשיווק ופרסום
MARKETING_PROMPT = """
אתה מומחה בשיווק ופרסום דיגיטלי.
אתה יכול לעזור בכתיבת תוכן שיווקי, אופטימיזציה למנועי חיפוש ושיווק במדיה חברתית.
אתה מבין את הקהל היעד ויודע איך לפנות אליו בצורה אפקטיבית.
"""

# מיפוי סוגי פרומפטים לתבניות
PROMPT_TEMPLATES = {
    "system_introduction": BASE_BOT_PROMPT,
    "user_greeting": """
    שלום {user_name}! {time_of_day} טוב!
    אני כאן כדי לעזור לך. במה אוכל לסייע?
    """,
    "help_message": """
    אני יכול לעזור לך במגוון נושאים:
    - ניהול מסמכים ומידע
    - ניהול חנות מקוונת
    - ניתוח נתונים ומכירות
    - פתרון בעיות טכניות
    - שיווק ופרסום
    
    פשוט שאל אותי כל שאלה ואשמח לעזור!
    """,
    "farewell": """
    תודה על השיחה! אשמח לעזור שוב בפעם הבאה.
    להתראות ויום טוב!
    """
}

def get_base_prompt(prompt_type: str, variables: dict = None) -> str:
    """
    קבלת פרומפט בסיסי לפי סוג
    
    Args:
        prompt_type: סוג הפרומפט
        variables: משתנים להחלפה בפרומפט
        
    Returns:
        הפרומפט המבוקש
    """
    if prompt_type not in PROMPT_TEMPLATES:
        raise KeyError(f"פרומפט מסוג {prompt_type} לא נמצא")
    
    prompt = PROMPT_TEMPLATES[prompt_type]
    
    if variables:
        try:
            prompt = prompt.format(**variables)
        except KeyError as e:
            raise KeyError(f"חסר משתנה {e} בפרומפט")
        except Exception as e:
            raise ValueError(f"שגיאה בהחלפת משתנים בפרומפט: {str(e)}")
    
    return prompt.strip()

def build_prompt(task_type: str, user_message: str, history_text: str = "") -> str:
    """
    בניית פרומפט מותאם למשימה
    
    Args:
        task_type: סוג המשימה
        user_message: הודעת המשתמש
        history_text: היסטוריית השיחה
        
    Returns:
        פרומפט מותאם למשימה
    """
    # בחירת תבנית בסיסית לפי סוג המשימה
    if task_type == "document":
        base_prompt = DOCUMENT_MANAGEMENT_PROMPT
    elif task_type == "store":
        base_prompt = STORE_MANAGEMENT_PROMPT
    elif task_type == "analysis":
        base_prompt = DATA_ANALYSIS_PROMPT
    elif task_type == "error":
        base_prompt = ERROR_HANDLING_PROMPT
    elif task_type == "marketing":
        base_prompt = MARKETING_PROMPT
    else:
        base_prompt = BASE_BOT_PROMPT
    
    # הוספת היסטוריית השיחה אם קיימת
    if history_text:
        prompt = f"""
        {base_prompt}
        
        היסטוריית השיחה:
        {history_text}
        
        הודעת המשתמש:
        {user_message}
        """
    else:
        prompt = f"""
        {base_prompt}
        
        הודעת המשתמש:
        {user_message}
        """
    
    return prompt.strip() 