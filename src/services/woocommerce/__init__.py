"""
מודול שירותי WooCommerce - מכיל שירותים לתקשורת עם API של WooCommerce
"""

from src.services.woocommerce.api import (
    WooCommerceAPI, 
    CachedWooCommerceAPI, 
    get_cached_woocommerce_api,
    get_woocommerce_api
)

from src.services.woocommerce.data import (
    ORDER_STATUSES,
    PRODUCT_TYPES,
    SALES_IMPROVEMENT_TIPS,
    RECOMMENDED_PLUGINS,
    COMMON_ISSUES_SOLUTIONS,
    get_order_status_info,
    get_product_type_info,
    get_sales_improvement_tips,
    get_recommended_plugins,
    get_common_issue_solutions,
    get_woocommerce_knowledge_base
)

__all__ = [
    # מ-API
    'WooCommerceAPI',
    'CachedWooCommerceAPI',
    'get_cached_woocommerce_api',
    'get_woocommerce_api',
    
    # מנתונים סטטיים
    'ORDER_STATUSES',
    'PRODUCT_TYPES',
    'SALES_IMPROVEMENT_TIPS',
    'RECOMMENDED_PLUGINS',
    'COMMON_ISSUES_SOLUTIONS',
    'get_order_status_info',
    'get_product_type_info',
    'get_sales_improvement_tips',
    'get_recommended_plugins',
    'get_common_issue_solutions',
    'get_woocommerce_knowledge_base'
] 