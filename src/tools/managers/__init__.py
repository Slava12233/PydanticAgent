"""
מודול מנהלי משאבים - מכיל מחלקות ופונקציות לניהול משאבים כמו מוצרים והזמנות
"""

# ייבוא פונקציות ממנהל מוצרים
from src.tools.managers.product_manager import (
    ProductManager,
    create_product_from_text,
    format_product_for_display,
    update_product_from_text,
    search_products_by_text
)

# ייבוא פונקציות ממנהל הזמנות
from src.tools.managers.order_manager import (
    format_order_for_display,
    format_orders_list_for_display,
    get_orders,
    get_order,
    update_order_status,
    cancel_order,
    refund_order
)

from src.tools.managers.context_manager import (
    ConversationContext,
    understand_context,
    resolve_pronouns,
    extract_context_from_history
)

from src.tools.managers.query_parser import (
    parse_complex_query,
    is_comparative_query,
    parse_comparative_query,
    is_hypothetical_query,
    parse_hypothetical_query
)

from src.tools.managers.response_generator import (
    ResponseGenerator,
    generate_natural_response,
    get_emoji,
    format_with_emojis
)

# ייבוא פונקציות ממנהל הלמידה
from src.tools.managers.learning_manager import (
    LearningManager,
    learning_manager
)

from src.tools.managers.sales_analyzer import (
    SalesAnalyzer,
    get_sales_report,
    get_top_selling_products
)

from src.tools.managers.inventory_manager import (
    InventoryManager,
    update_stock_quantity,
    add_stock_quantity,
    get_low_stock_report,
    forecast_product_inventory,
    format_inventory_forecast,
    format_inventory_report
)

__all__ = [
    # ממנהל מוצרים
    'ProductManager',
    'create_product_from_text',
    'format_product_for_display',
    'update_product_from_text',
    'search_products_by_text',
    
    # ממנהל הזמנות
    'format_order_for_display',
    'format_orders_list_for_display',
    'get_orders',
    'get_order',
    'update_order_status',
    'cancel_order',
    'refund_order',

    # ממנהל הקשר
    'ConversationContext',
    'understand_context',
    'resolve_pronouns',
    'extract_context_from_history',
    
    # ממנהל פירוק שאילתות
    'parse_complex_query',
    'is_comparative_query',
    'parse_comparative_query',
    'is_hypothetical_query',
    'parse_hypothetical_query',
    
    # ממחולל התשובות
    'ResponseGenerator',
    'generate_natural_response',
    'get_emoji',
    'format_with_emojis',
    
    # ממנהל הלמידה
    'LearningManager',
    'learning_manager',
    
# ממנהל ניתוח מכירות
    'SalesAnalyzer',
    'get_sales_report',
    'get_top_selling_products',
    
    # ממנהל המלאי
    'InventoryManager',
    'update_stock_quantity',
    'add_stock_quantity',
    'get_low_stock_report',
    'forecast_product_inventory',
    'format_inventory_forecast',
    'format_inventory_report'
]
