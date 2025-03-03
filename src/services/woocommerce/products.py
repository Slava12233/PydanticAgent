"""
מודול לניהול מוצרים ב-WooCommerce
מייבא פונקציות מ-product_manager ומחשוף אותן לשימוש
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# ייבוא הפונקציות הנדרשות מ-product_manager
from src.tools.managers.product_manager import ProductManager
from src.services.woocommerce.api import WooCommerceAPI, get_cached_woocommerce_api

logger = logging.getLogger(__name__)

# מופע גלובלי של מנהל המוצרים
_product_manager = None

def _get_product_manager():
    """
    קבלת מופע של מנהל המוצרים
    
    Returns:
        מופע של מנהל המוצרים
    """
    global _product_manager
    
    if _product_manager is None:
        # ייבוא כאן כדי למנוע ייבוא מעגלי
        from src.tools.woocommerce_tools import get_woocommerce_api
        
        try:
            api = get_woocommerce_api()
            _product_manager = ProductManager(api)
        except Exception as e:
            logger.error(f"שגיאה ביצירת מנהל מוצרים: {str(e)}")
            return None
    
    return _product_manager

async def get_products(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    קבלת רשימת מוצרים מהחנות
    
    Args:
        filters: פילטרים לסינון המוצרים
        
    Returns:
        רשימת מוצרים
    """
    product_manager = _get_product_manager()
    if not product_manager:
        return []
    
    # המרת פילטרים למבנה המתאים ל-product_manager
    kwargs = {}
    if filters:
        kwargs.update(filters)
    
    try:
        return await product_manager.get_products(**kwargs)
    except Exception as e:
        logger.error(f"שגיאה בקבלת מוצרים: {str(e)}")
        return []

async def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    """
    קבלת מוצר לפי מזהה
    
    Args:
        product_id: מזהה המוצר
        
    Returns:
        פרטי המוצר או None אם המוצר לא נמצא
    """
    product_manager = _get_product_manager()
    if not product_manager:
        return None
    
    try:
        return await product_manager.get_product(product_id)
    except Exception as e:
        logger.error(f"שגיאה בקבלת מוצר {product_id}: {str(e)}")
        return None

async def update_product(product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    עדכון מוצר
    
    Args:
        product_id: מזהה המוצר
        data: נתוני המוצר לעדכון
        
    Returns:
        פרטי המוצר המעודכן או None אם העדכון נכשל
    """
    product_manager = _get_product_manager()
    if not product_manager:
        return None
    
    try:
        return await product_manager.update_product(product_id, data)
    except Exception as e:
        logger.error(f"שגיאה בעדכון מוצר {product_id}: {str(e)}")
        return None

async def delete_product(product_id: int, force: bool = False) -> bool:
    """
    מחיקת מוצר
    
    Args:
        product_id: מזהה המוצר
        force: האם למחוק לצמיתות
        
    Returns:
        האם המחיקה הצליחה
    """
    product_manager = _get_product_manager()
    if not product_manager:
        return False
    
    try:
        return await product_manager.delete_product(product_id, force)
    except Exception as e:
        logger.error(f"שגיאה במחיקת מוצר {product_id}: {str(e)}")
        return False

async def create_product(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    יצירת מוצר חדש
    
    Args:
        data: נתוני המוצר
        
    Returns:
        פרטי המוצר שנוצר או None אם היצירה נכשלה
    """
    product_manager = _get_product_manager()
    if not product_manager:
        return None
    
    try:
        return await product_manager.create_product(data)
    except Exception as e:
        logger.error(f"שגיאה ביצירת מוצר: {str(e)}")
        return None

async def create_product_from_text(store_url: str, consumer_key: str, consumer_secret: str, text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    יצירת מוצר חדש מטקסט
    
    Args:
        store_url: כתובת החנות
        consumer_key: מפתח צרכן
        consumer_secret: סוד צרכן
        text: טקסט המכיל את פרטי המוצר
        
    Returns:
        טאפל עם: האם הפעולה הצליחה, הודעה, פרטי המוצר שנוצר
    """
    try:
        # יצירת מופע של ה-API
        woo_api = WooCommerceAPI(
            store_url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מנהל מוצרים
        product_manager = ProductManager(woo_api)
        
        # חילוץ נתוני המוצר מהטקסט
        product_data = extract_product_data(text)
        
        if not product_data:
            return False, "לא ניתן לחלץ נתוני מוצר מהטקסט", None
        
        # בדיקת שדות חובה
        missing_fields = identify_missing_required_fields(product_data)
        if missing_fields:
            return False, f"חסרים שדות חובה: {', '.join(missing_fields)}", None
        
        # יצירת המוצר
        created_product = await product_manager.create_product(product_data)
        
        if not created_product:
            return False, "יצירת המוצר נכשלה", None
        
        return True, f"המוצר נוצר בהצלחה (מזהה: {created_product.get('id')})", created_product
        
    except Exception as e:
        logger.error(f"שגיאה ביצירת מוצר מטקסט: {str(e)}")
        return False, f"אירעה שגיאה: {str(e)}", None 