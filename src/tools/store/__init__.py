"""
כלים לניהול חנות
"""

from .managers.product_manager import ProductManager
from .managers.order_manager import OrderManager
from .managers.customer_manager import CustomerManager
from .managers.inventory_manager import InventoryManager
from .managers.inventory_forecasting import InventoryForecasting
from .managers.inventory_reporting import InventoryReporting
from .managers.product_categories import ProductCategories

from .woocommerce_tools import (
    get_woocommerce_api,
    CachedWooCommerceAPI,
    get_cached_woocommerce_api,
    get_order_status_info,
    get_product_type_info,
    get_sales_improvement_tips,
    get_recommended_plugins,
    get_common_issue_solutions,
    get_woocommerce_knowledge_base
)

from .woocommerce_templates import (
    TEMPLATES,
    get_template
)

__all__ = [
    'ProductManager',
    'OrderManager',
    'CustomerManager',
    'InventoryManager',
    'InventoryForecasting',
    'InventoryReporting',
    'ProductCategories',
    'get_woocommerce_api',
    'CachedWooCommerceAPI',
    'get_cached_woocommerce_api',
    'get_order_status_info',
    'get_product_type_info',
    'get_sales_improvement_tips',
    'get_recommended_plugins',
    'get_common_issue_solutions',
    'get_woocommerce_knowledge_base',
    'TEMPLATES',
    'get_template'
] 