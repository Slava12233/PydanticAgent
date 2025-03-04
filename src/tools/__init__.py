"""
כלים לניהול מוצרים והזמנות ב-WooCommerce
"""

# ייבוא פונקציות מזיהוי כוונות
from src.tools.intent import (
    # מזיהוי כוונות יצירת מוצר
    extract_product_data,
    is_product_creation_intent,
    identify_missing_required_fields,
    generate_product_creation_questions,
    get_product_type_suggestions,
    
    # מזיהוי כוונות ניהול הזמנות
    is_order_management_intent,
    extract_order_id,
    extract_order_status,
    extract_date_range,
    extract_order_filters,
    generate_order_management_questions,
    
    # מזיהוי כוונות ספציפיות
    identify_specific_intent,
    get_intent_description,
    extract_parameters_by_intent,
    calculate_intent_score,
    SPECIFIC_INTENTS
)

# ייבוא מנהלים מ-store_tools
from src.tools.store_tools.managers.product_manager import ProductManager
from src.tools.store_tools.managers.order_manager import OrderManager
from src.tools.store_tools.managers.customer_manager import CustomerManager
from src.tools.store_tools.managers.inventory_manager import InventoryManager
from src.tools.store_tools.managers.inventory_forecasting import InventoryForecasting
from src.tools.store_tools.managers.inventory_reporting import InventoryReporting
from src.tools.store_tools.managers.product_categories import ProductCategories

# ייבוא פונקציות מכלי WooCommerce
from src.tools.store_tools.woocommerce_tools import (
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

# ייבוא תבניות WooCommerce
from src.tools.store_tools.woocommerce_templates import (
    TEMPLATES,
    get_template
)

# ייבוא שירותי RAG (מועבר ל-services)
from src.services.rag_service import (
    RAGService,
    add_document_from_file,
    add_document_from_text,
    search_documents,
    list_documents,
    delete_document,
    get_document_by_id
)

__all__ = [
    # מזיהוי כוונות יצירת מוצר
    'extract_product_data',
    'is_product_creation_intent',
    'identify_missing_required_fields',
    'generate_product_creation_questions',
    'get_product_type_suggestions',
    
    # מזיהוי כוונות ספציפיות
    'identify_specific_intent',
    'get_intent_description',
    'extract_parameters_by_intent',
    'calculate_intent_score',
    'SPECIFIC_INTENTS',
    
    # ממנהלי store_tools
    'ProductManager',
    'OrderManager',
    'CustomerManager',
    'InventoryManager',
    'InventoryForecasting',
    'InventoryReporting',
    'ProductCategories',
    
    # מזיהוי כוונות ניהול הזמנות
    'is_order_management_intent',
    'extract_order_id',
    'extract_order_status',
    'extract_date_range',
    'extract_order_filters',
    'generate_order_management_questions',
    
    # מכלי WooCommerce
    'get_woocommerce_api',
    'CachedWooCommerceAPI',
    'get_cached_woocommerce_api',
    'get_order_status_info',
    'get_product_type_info',
    'get_sales_improvement_tips',
    'get_recommended_plugins',
    'get_common_issue_solutions',
    'get_woocommerce_knowledge_base',
    
    # מתבניות WooCommerce
    'TEMPLATES',
    'get_template',
    
    # משירותי RAG
    'RAGService',
    'add_document_from_file',
    'add_document_from_text',
    'search_documents',
    'list_documents',
    'delete_document',
    'get_document_by_id'
]
