"""
מודול לניהול לקוחות ב-WooCommerce
מייבא פונקציות מ-customer_manager ומחשוף אותן לשימוש
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# ייבוא הפונקציות הנדרשות מ-customer_manager
from src.tools.managers.customer_manager import CustomerManager
from src.services.woocommerce.api import WooCommerceAPI, get_cached_woocommerce_api

logger = logging.getLogger(__name__)

# מופע גלובלי של מנהל הלקוחות
_customer_manager = None

def _get_customer_manager():
    """
    קבלת מופע של מנהל הלקוחות
    
    Returns:
        מופע של מנהל הלקוחות
    """
    global _customer_manager
    
    if _customer_manager is None:
        # ייבוא כאן כדי למנוע ייבוא מעגלי
        from src.tools.woocommerce_tools import get_woocommerce_api
        
        try:
            api = get_woocommerce_api()
            _customer_manager = CustomerManager()
        except Exception as e:
            logger.error(f"שגיאה ביצירת מנהל לקוחות: {str(e)}")
            return None
    
    return _customer_manager

def get_customers(**params) -> List[Dict[str, Any]]:
    """
    קבלת רשימת לקוחות מהחנות
    
    Args:
        **params: פרמטרים לסינון הלקוחות
        
    Returns:
        רשימת לקוחות
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return []
    
    try:
        return customer_manager.get_customers(**params)
    except Exception as e:
        logger.error(f"שגיאה בקבלת לקוחות: {str(e)}")
        return []

def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    """
    קבלת מידע על לקוח ספציפי
    
    Args:
        customer_id: מזהה הלקוח
        
    Returns:
        פרטי הלקוח או None אם הלקוח לא נמצא
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return None
    
    try:
        return customer_manager.get_customer(customer_id)
    except Exception as e:
        logger.error(f"שגיאה בקבלת לקוח {customer_id}: {str(e)}")
        return None

def create_customer(customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    יצירת לקוח חדש
    
    Args:
        customer_data: נתוני הלקוח
        
    Returns:
        פרטי הלקוח שנוצר או None אם היצירה נכשלה
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return None
    
    try:
        return customer_manager.create_customer(customer_data)
    except Exception as e:
        logger.error(f"שגיאה ביצירת לקוח: {str(e)}")
        return None

def update_customer(customer_id: int, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    עדכון פרטי לקוח
    
    Args:
        customer_id: מזהה הלקוח
        customer_data: נתוני הלקוח המעודכנים
        
    Returns:
        פרטי הלקוח המעודכן או None אם העדכון נכשל
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return None
    
    try:
        return customer_manager.update_customer(customer_id, customer_data)
    except Exception as e:
        logger.error(f"שגיאה בעדכון לקוח {customer_id}: {str(e)}")
        return None

def delete_customer(customer_id: int, force: bool = False) -> bool:
    """
    מחיקת לקוח
    
    Args:
        customer_id: מזהה הלקוח
        force: האם למחוק לצמיתות
        
    Returns:
        האם המחיקה הצליחה
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return False
    
    try:
        result = customer_manager.delete_customer(customer_id, force)
        return result is not None
    except Exception as e:
        logger.error(f"שגיאה במחיקת לקוח {customer_id}: {str(e)}")
        return False

def search_customers(search_term: str) -> List[Dict[str, Any]]:
    """
    חיפוש לקוחות לפי מונח חיפוש
    
    Args:
        search_term: מונח החיפוש
        
    Returns:
        רשימת לקוחות שתואמים את החיפוש
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return []
    
    try:
        return customer_manager.search_customers(search_term)
    except Exception as e:
        logger.error(f"שגיאה בחיפוש לקוחות: {str(e)}")
        return []

def get_customer_orders(customer_id: int) -> List[Dict[str, Any]]:
    """
    קבלת רשימת הזמנות של לקוח ספציפי
    
    Args:
        customer_id: מזהה הלקוח
        
    Returns:
        רשימת הזמנות של הלקוח
    """
    customer_manager = _get_customer_manager()
    if not customer_manager:
        return []
    
    try:
        return customer_manager.get_customer_orders(customer_id)
    except Exception as e:
        logger.error(f"שגיאה בקבלת הזמנות של לקוח {customer_id}: {str(e)}")
        return []

def create_customer_from_text(text: str) -> Dict[str, Any]:
    """
    יצירת לקוח חדש מטקסט
    
    Args:
        text: טקסט המכיל את פרטי הלקוח
        
    Returns:
        תוצאת יצירת הלקוח
    """
    from src.tools.managers.customer_manager import create_customer_from_text as _create_customer_from_text
    return _create_customer_from_text(text)

def update_customer_from_text(text: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    עדכון פרטי לקוח מטקסט
    
    Args:
        text: טקסט המכיל את פרטי הלקוח המעודכנים
        customer_id: מזהה הלקוח (אופציונלי)
        
    Returns:
        תוצאת עדכון הלקוח
    """
    from src.tools.managers.customer_manager import update_customer_from_text as _update_customer_from_text
    return _update_customer_from_text(text, customer_id)

def get_customer_from_text(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי לקוח מטקסט וחיפוש לקוח ספציפי
    
    Args:
        text: טקסט המכיל את פרטי הלקוח
        
    Returns:
        תוצאת החיפוש
    """
    from src.tools.managers.customer_manager import get_customer_from_text as _get_customer_from_text
    return _get_customer_from_text(text)

def get_customers_from_text(text: str) -> Dict[str, Any]:
    """
    חיפוש לקוחות לפי טקסט
    
    Args:
        text: טקסט המכיל את פרטי החיפוש
        
    Returns:
        תוצאת החיפוש
    """
    from src.tools.managers.customer_manager import get_customers_from_text as _get_customers_from_text
    return _get_customers_from_text(text) 