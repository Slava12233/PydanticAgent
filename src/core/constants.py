"""
קבועים וערכים משותפים עבור סוכן הטלגרם
"""

# ייבוא קבועים ממודולים אחרים
from src.core.product_keywords import (
    PRODUCT_KEYWORDS,
    INVENTORY_KEYWORDS,
    CATEGORY_KEYWORDS
)

from src.core.order_keywords import (
    ORDER_KEYWORDS,
    SHIPPING_KEYWORDS,
    RETURNS_KEYWORDS
)

from src.core.customer_keywords import (
    CUSTOMER_KEYWORDS,
    CRM_KEYWORDS,
    LOYALTY_KEYWORDS
)

from src.core.general_constants import (
    GREETINGS,
    DOCUMENT_KEYWORDS,
    SALES_ANALYSIS_KEYWORDS,
    MARKETING_KEYWORDS,
    HELP_KEYWORDS
)

# מילות מפתח לזיהוי סוגי משימות
KEYWORDS = {
    'product_management': PRODUCT_KEYWORDS,
    'document_management': DOCUMENT_KEYWORDS,
    'order_management': ORDER_KEYWORDS,
    'customer_management': CUSTOMER_KEYWORDS,
    'inventory_management': INVENTORY_KEYWORDS,
    'sales_analysis': SALES_ANALYSIS_KEYWORDS,
    'marketing': MARKETING_KEYWORDS,
    'shipping': SHIPPING_KEYWORDS,
    'returns': RETURNS_KEYWORDS,
    'crm': CRM_KEYWORDS,
    'loyalty': LOYALTY_KEYWORDS,
    'help': HELP_KEYWORDS
}
