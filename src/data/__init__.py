"""
מודול נתונים סטטיים
"""

from src.services.woocommerce.data import (
    # קבועים
    ORDER_STATUSES,
    PRODUCT_TYPES,
    SALES_IMPROVEMENT_TIPS,
    RECOMMENDED_PLUGINS,
    COMMON_ISSUES_SOLUTIONS,
    
    # פונקציות
    get_order_status_info,
    get_product_type_info,
    get_sales_improvement_tips,
    get_recommended_plugins,
    get_common_issue_solutions,
    get_woocommerce_knowledge_base
)

__all__ = [
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