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
    'SPECIFIC_INTENTS'
] 