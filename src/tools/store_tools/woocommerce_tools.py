"""
כלים לעבודה עם WooCommerce
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from datetime import datetime, timedelta

# ייבוא נתונים סטטיים ופונקציות מקובץ woocommerce_data.py
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

# ייבוא מחלקות ופונקציות מקובץ woocommerce_api.py
from src.services.woocommerce.api import (
    WooCommerceAPI, 
    CachedWooCommerceAPI, 
    get_cached_woocommerce_api,
    get_woocommerce_api
)

logger = logging.getLogger(__name__)

def get_woocommerce_api(store_url, consumer_key, consumer_secret):
    """
    יצירת חיבור ל-API של WooCommerce
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
    
    Returns:
        אובייקט API של WooCommerce
    """
    try:
        from woocommerce import API
        
        return API(
            url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3",
            timeout=30
        )
    except ImportError:
        raise ImportError("נדרש להתקין את חבילת woocommerce: pip install woocommerce")
    except Exception as e:
        raise Exception(f"שגיאה ביצירת חיבור ל-API של WooCommerce: {str(e)}")

# הערה: מחלקת CachedWooCommerceAPI ופונקציית get_cached_woocommerce_api מיובאות מ-woocommerce_api.py 