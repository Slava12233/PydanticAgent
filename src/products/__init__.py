"""
מודול מוצרים - מכיל את כל הפונקציונליות הקשורה לניהול מוצרים
"""

from .intent import (
    extract_product_data, 
    identify_missing_required_fields, 
    is_product_creation_intent,
    extract_product_id,
    generate_missing_field_questions,
    generate_product_creation_questions,
    get_product_type_suggestions,
    identify_product_intent
)

from .keywords import (
    PRODUCT_KEYWORDS,
    INVENTORY_KEYWORDS,
    CATEGORY_KEYWORDS
)

from .handler import ProductHandler
from .manager import ProductManager

# ייבוא יתבצע כאשר הקבצים יועברו 