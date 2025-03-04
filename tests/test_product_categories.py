"""
בדיקות יחידה למודול ניהול קטגוריות מוצרים.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.store_tools.managers.product_categories import ProductCategories

@pytest.fixture
def mock_api():
    """יצירת mock ל-API"""
    api = AsyncMock()
    api._make_request = AsyncMock()
    return api

@pytest.fixture
def categories(mock_api):
    """יצירת אובייקט ProductCategories לבדיקות"""
    return ProductCategories(mock_api)

def test_is_categories_cache_valid(categories):
    """בדיקת תקפות מטמון הקטגוריות"""
    # בדיקה כשאין מטמון
    assert categories._is_categories_cache_valid() is False
    
    # בדיקה עם מטמון תקף
    categories.categories_cache = [{"id": 1, "name": "קטגוריה"}]
    categories.categories_cache_timestamp = time.time()
    assert categories._is_categories_cache_valid() is True
    
    # בדיקה עם מטמון לא תקף (ישן)
    categories.categories_cache_timestamp = time.time() - (categories.cache_ttl + 1)
    assert categories._is_categories_cache_valid() is False

@pytest.mark.asyncio
async def test_get_categories_from_cache(categories, mock_api):
    """בדיקת קבלת קטגוריות ממטמון"""
    # הגדרת מטמון תקף
    mock_categories = [{"id": 1, "name": "קטגוריה"}]
    categories.categories_cache = mock_categories
    categories.categories_cache_timestamp = time.time()
    
    # קבלת קטגוריות
    result = await categories.get_categories()
    
    # בדיקה שהתוצאה מגיעה מהמטמון
    assert result == mock_categories
    assert mock_api._make_request.call_count == 0  # לא הייתה קריאה ל-API

@pytest.mark.asyncio
async def test_get_categories_from_api(categories, mock_api):
    """בדיקת קבלת קטגוריות מה-API"""
    # הגדרת תשובת ה-mock
    mock_categories = [{"id": 1, "name": "קטגוריה"}]
    mock_api._make_request.return_value = (200, mock_categories)
    
    # קבלת קטגוריות
    result = await categories.get_categories()
    
    # בדיקות
    assert result == mock_categories
    assert categories.categories_cache == mock_categories
    assert categories.categories_cache_timestamp is not None

@pytest.mark.asyncio
async def test_find_or_create_category_existing(categories, mock_api):
    """בדיקת חיפוש קטגוריה קיימת"""
    # הגדרת קטגוריה קיימת
    existing_category = {
        "id": 1,
        "name": "קטגוריה קיימת"
    }
    mock_api._make_request.return_value = (200, [existing_category])
    
    # חיפוש קטגוריה
    category_id = await categories.find_or_create_category("קטגוריה קיימת")
    
    # בדיקות
    assert category_id == 1
    assert mock_api._make_request.call_count == 1  # רק חיפוש, לא יצירה

@pytest.mark.asyncio
async def test_find_or_create_category_new(categories, mock_api):
    """בדיקת יצירת קטגוריה חדשה"""
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, []),  # אין קטגוריה קיימת
        (201, {"id": 2, "name": "קטגוריה חדשה"})  # יצירת קטגוריה חדשה
    ]
    
    # יצירת קטגוריה חדשה
    category_id = await categories.find_or_create_category("קטגוריה חדשה")
    
    # בדיקות
    assert category_id == 2
    assert mock_api._make_request.call_count == 2  # חיפוש ויצירה

@pytest.mark.asyncio
async def test_handle_product_categories_list(categories, mock_api):
    """בדיקת טיפול בקטגוריות מוצר - רשימת קטגוריות"""
    # הגדרת נתוני מוצר
    product_data = {
        "categories": [
            {"name": "קטגוריה 1"},
            {"name": "קטגוריה 2"}
        ]
    }
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, [{"id": 1, "name": "קטגוריה 1"}]),  # קטגוריה קיימת
        (200, []),  # קטגוריה לא קיימת
        (201, {"id": 2, "name": "קטגוריה 2"})  # יצירת קטגוריה חדשה
    ]
    
    # טיפול בקטגוריות
    result = await categories.handle_product_categories(product_data)
    
    # בדיקות
    assert len(result["categories"]) == 2
    assert {"id": 1} in result["categories"]
    assert {"id": 2} in result["categories"]

@pytest.mark.asyncio
async def test_handle_product_categories_string(categories, mock_api):
    """בדיקת טיפול בקטגוריות מוצר - מחרוזת קטגוריות"""
    # הגדרת נתוני מוצר
    product_data = {
        "categories": "קטגוריה 1, קטגוריה 2"
    }
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, [{"id": 1, "name": "קטגוריה 1"}]),  # קטגוריה קיימת
        (200, []),  # קטגוריה לא קיימת
        (201, {"id": 2, "name": "קטגוריה 2"})  # יצירת קטגוריה חדשה
    ]
    
    # טיפול בקטגוריות
    result = await categories.handle_product_categories(product_data)
    
    # בדיקות
    assert len(result["categories"]) == 2
    assert {"id": 1} in result["categories"]
    assert {"id": 2} in result["categories"]

@pytest.mark.asyncio
async def test_error_handling(categories, mock_api):
    """בדיקת טיפול בשגיאות"""
    # הגדרת שגיאה בקבלת קטגוריות
    mock_api._make_request.side_effect = Exception("API Error")
    
    # בדיקת קבלת קטגוריות
    result = await categories.get_categories()
    assert len(result) == 0
    
    # בדיקת חיפוש/יצירת קטגוריה
    category_id = await categories.find_or_create_category("קטגוריה")
    assert category_id is None
    
    # בדיקת טיפול בקטגוריות מוצר
    product_data = {"categories": ["קטגוריה"]}
    result = await categories.handle_product_categories(product_data)
    assert result["categories"][0]["name"] == "קטגוריה"  # שומר על השם כשיש שגיאה 