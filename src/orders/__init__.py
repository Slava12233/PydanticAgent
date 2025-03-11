"""
מודול הזמנות - מכיל את כל הפונקציונליות הקשורה לניהול הזמנות
"""

from .intent import (
    extract_order_data,
    extract_order_id,
    extract_order_status,
    extract_date_range,
    extract_order_filters,
    is_order_management_intent,
    generate_order_management_questions,
    identify_order_intent
)

from .keywords import (
    ORDER_KEYWORDS,
    SHIPPING_KEYWORDS,
    RETURNS_KEYWORDS
)

from .handler import OrderHandler
from .manager import OrderManager 