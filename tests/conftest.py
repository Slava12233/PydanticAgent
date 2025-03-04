"""
קובץ המכיל fixtures משותפים לכל הבדיקות
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_api():
    """
    יצירת mock ל-API של WooCommerce
    
    Returns:
        AsyncMock: אובייקט mock עם מתודות אסינכרוניות
    """
    api = AsyncMock()
    
    # הגדרת ערכי ברירת מחדל לתשובות ה-API
    async def mock_make_request(method, endpoint, data=None, params=None):
        # מיפוי תשובות לפי סוג הבקשה והנתיב
        responses = {
            ("GET", "products"): (200, []),
            ("GET", "products/categories"): (200, []),
            ("POST", "products"): (201, {}),
            ("POST", "products/categories"): (201, {}),
            ("PUT", "products"): (200, {}),
            ("PUT", "products/categories"): (200, {}),
            ("DELETE", "products"): (200, {}),
            ("DELETE", "products/categories"): (200, {})
        }
        
        # בדיקה אם יש תשובה מותאמת אישית
        if hasattr(api._make_request, "custom_response"):
            return api._make_request.custom_response
        
        # בדיקה אם יש side_effect מוגדר
        if hasattr(api._make_request, "side_effect"):
            if callable(api._make_request.side_effect):
                return await api._make_request.side_effect(method, endpoint, data, params)
            elif isinstance(api._make_request.side_effect, Exception):
                raise api._make_request.side_effect
            else:
                return api._make_request.side_effect
        
        # החזרת תשובת ברירת מחדל
        key = (method, endpoint.split("/")[0])
        return responses.get(key, (200, {}))
    
    api._make_request = AsyncMock(side_effect=mock_make_request)
    
    return api

@pytest.fixture
def mock_product():
    """
    יצירת נתוני מוצר לדוגמה
    
    Returns:
        dict: נתוני מוצר לדוגמה
    """
    return {
        "id": 123,
        "name": "מוצר לדוגמה",
        "sku": "TEST123",
        "regular_price": "100.00",
        "sale_price": "90.00",
        "manage_stock": True,
        "stock_quantity": 50,
        "stock_status": "instock",
        "categories": [
            {"name": "קטגוריה לדוגמה"}
        ]
    }

@pytest.fixture
def mock_category():
    """
    יצירת נתוני קטגוריה לדוגמה
    
    Returns:
        dict: נתוני קטגוריה לדוגמה
    """
    return {
        "id": 1,
        "name": "קטגוריה לדוגמה",
        "slug": "test-category",
        "parent": 0,
        "description": "קטגוריה לבדיקות",
        "count": 5
    }

@pytest.fixture
def mock_order():
    """
    יצירת נתוני הזמנה לדוגמה
    
    Returns:
        dict: נתוני הזמנה לדוגמה
    """
    return {
        "id": 456,
        "status": "completed",
        "date_created": "2024-01-01T00:00:00",
        "line_items": [
            {
                "product_id": 123,
                "quantity": 2,
                "price": "100.00"
            }
        ]
    }

@pytest.fixture
def mock_inventory_data():
    """
    יצירת נתוני מלאי לדוגמה
    
    Returns:
        dict: נתוני מלאי לדוגמה
    """
    return {
        "product_id": 123,
        "stock_quantity": 50,
        "low_stock_amount": 10,
        "manage_stock": True,
        "stock_status": "instock",
        "backorders_allowed": False
    } 