"""
מודול זיהוי כוונות - מכיל פונקציות לזיהוי כוונות המשתמש מטקסט חופשי
"""

# ייבוא פונקציות מזיהוי כוונות יצירת מוצר
from src.tools.intent.product_intent import (
    extract_product_data,
    is_product_creation_intent,
    identify_missing_required_fields,
    generate_product_creation_questions,
    get_product_type_suggestions
)

# ייבוא פונקציות מזיהוי כוונות ניהול הזמנות
from src.tools.intent.order_intent import (
    is_order_management_intent,
    extract_order_id,
    extract_order_status,
    extract_date_range,
    extract_order_filters,
    generate_order_management_questions
)

# ייבוא פונקציות מזיהוי כוונות ספציפיות
from src.tools.intent.intent_recognizer import (
    identify_specific_intent,
    get_intent_description,
    extract_parameters_by_intent,
    calculate_intent_score,
    SPECIFIC_INTENTS
)

from .recognizers.base_recognizer import BaseIntentRecognizer
from .learning.intent_learner import IntentLearner
from .config.intent_config import (
    GENERAL_SETTINGS,
    INTENT_KEYWORDS,
    INTENT_PATTERNS,
    get_all_keywords,
    save_custom_keywords
)

# יצירת מופע יחיד של המזהה ומנהל הלמידה
intent_recognizer = BaseIntentRecognizer()
intent_learner = IntentLearner()

def identify_intent(text: str) -> tuple[str, str, float]:
    """
    זיהוי כוונה מתוך טקסט
    
    Args:
        text: הטקסט לזיהוי
        
    Returns:
        סוג הכוונה, הפעולה הספציפית, וציון הביטחון
    """
    return intent_recognizer.identify_intent(text)

def learn_from_feedback(text: str, predicted: tuple[str, str], correct: tuple[str, str]) -> None:
    """
    למידה מפידבק משתמש
    
    Args:
        text: הטקסט המקורי
        predicted: הכוונה והפעולה שזוהו (כוונה, פעולה)
        correct: הכוונה והפעולה הנכונות (כוונה, פעולה)
    """
    intent_learner.learn_from_feedback(text, predicted, correct)

def learn_from_examples(examples: list[tuple[str, str, str]]) -> None:
    """
    למידה מדוגמאות מתויגות
    
    Args:
        examples: רשימה של טאפלים (טקסט, כוונה, פעולה)
    """
    intent_learner.learn_from_examples(examples)

def analyze_learning_history(days: int = 7) -> dict:
    """
    ניתוח היסטוריית הלמידה
    
    Args:
        days: מספר הימים לניתוח
        
    Returns:
        סטטיסטיקות על הלמידה
    """
    return intent_learner.analyze_learning_history(days)

__all__ = [
    # מזיהוי כוונות יצירת מוצר
    'extract_product_data',
    'is_product_creation_intent',
    'identify_missing_required_fields',
    'generate_product_creation_questions',
    'get_product_type_suggestions',
    
    # מזיהוי כוונות ניהול הזמנות
    'is_order_management_intent',
    'extract_order_id',
    'extract_order_status',
    'extract_date_range',
    'extract_order_filters',
    'generate_order_management_questions',
    
    # מזיהוי כוונות ספציפיות
    'identify_specific_intent',
    'get_intent_description',
    'extract_parameters_by_intent',
    'calculate_intent_score',
    'SPECIFIC_INTENTS',

    'BaseIntentRecognizer',
    'IntentLearner',
    'GENERAL_SETTINGS',
    'INTENT_KEYWORDS',
    'INTENT_PATTERNS',
    'get_all_keywords',
    'save_custom_keywords',
    'identify_intent',
    'learn_from_feedback',
    'learn_from_examples',
    'analyze_learning_history'
] 