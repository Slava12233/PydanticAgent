"""
מודול נתונים של WooCommerce
"""

from .product_categories import (
    PRODUCT_CATEGORIES,
    PRODUCT_TYPES,
    get_product_category_info
)

from .woocommerce_data import (
    ORDER_STATUSES,
    SALES_IMPROVEMENT_TIPS,
    RECOMMENDED_PLUGINS,
    COMMON_ISSUE_SOLUTIONS,
    WOOCOMMERCE_KNOWLEDGE_BASE,
    get_order_status_info,
    get_product_type_info,
    get_sales_improvement_tips,
    get_recommended_plugins,
    get_common_issue_solutions,
    get_woocommerce_knowledge_base
)

__all__ = [
    'PRODUCT_CATEGORIES',
    'PRODUCT_TYPES',
    'ORDER_STATUSES',
    'SALES_IMPROVEMENT_TIPS',
    'RECOMMENDED_PLUGINS',
    'COMMON_ISSUE_SOLUTIONS',
    'WOOCOMMERCE_KNOWLEDGE_BASE',
    'get_product_category_info',
    'get_order_status_info',
    'get_product_type_info',
    'get_sales_improvement_tips',
    'get_recommended_plugins',
    'get_common_issue_solutions',
    'get_woocommerce_knowledge_base'
] 