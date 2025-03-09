"""
בדיקות יחידה עבור מנהל קטגוריות המוצרים (ProductCategories)
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Optional

from src.tools.store.managers.product_categories import ProductCategories


@pytest_asyncio.fixture
async def product_categories():
    """פיקסצ'ר ליצירת מופע של מנהל קטגוריות המוצרים עם מוקים"""
    # יצירת מוק ל-API של WooCommerce
    mock_api = MagicMock()
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    # יצירת מופע של מנהל קטגוריות המוצרים עם ה-API המוקי
    manager = ProductCategories(woocommerce_api=mock_api, use_cache=False)
    
    # החזרת המנהל והמוק ל-API כדי שנוכל לבדוק קריאות
    yield manager, mock_api


@pytest.mark.asyncio
async def test_get_resource_name(product_categories):
    """בדיקת קבלת שם המשאב"""
    manager, _ = product_categories
    
    # וידוא ששם המשאב הוא 'products/categories'
    assert manager._get_resource_name() == 'products/categories'


@pytest.mark.asyncio
async def test_is_categories_cache_valid(product_categories):
    """בדיקת תקפות המטמון של קטגוריות"""
    manager, _ = product_categories
    
    # כאשר המטמון ריק, הוא אינו תקף
    assert manager._is_categories_cache_valid() is False
    
    # הגדרת מטמון עם זמן פג תוקף עתידי
    manager._categories_cache = {
        "data": [{"id": 1, "name": "קטגוריה לדוגמה"}],
        "timestamp": asyncio.get_event_loop().time() + 3600  # שעה מעכשיו
    }
    
    # כעת המטמון תקף
    assert manager._is_categories_cache_valid() is True
    
    # הגדרת מטמון עם זמן פג תוקף שעבר
    manager._categories_cache = {
        "data": [{"id": 1, "name": "קטגוריה לדוגמה"}],
        "timestamp": asyncio.get_event_loop().time() - 3600  # שעה לפני
    }
    
    # כעת המטמון אינו תקף
    assert manager._is_categories_cache_valid() is False


@pytest.mark.asyncio
async def test_get_categories_from_cache(product_categories):
    """בדיקת קבלת קטגוריות מהמטמון"""
    manager, mock_api = product_categories
    
    # הגדרת מטמון תקף
    mock_categories = [
        {"id": 1, "name": "קטגוריה ראשונה"},
        {"id": 2, "name": "קטגוריה שנייה"}
    ]
    manager._categories_cache = {
        "data": mock_categories,
        "timestamp": asyncio.get_event_loop().time() + 3600  # שעה מעכשיו
    }
    
    # קריאה לפונקציה
    result = await manager.get_categories()
    
    # וידוא שה-API לא נקרא (כי השתמשנו במטמון)
    mock_api.get.assert_not_called()
    
    # וידוא שהוחזרו הקטגוריות הנכונות
    assert result == mock_categories
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_categories_from_api(product_categories):
    """בדיקת קבלת קטגוריות מה-API"""
    manager, mock_api = product_categories
    
    # וידוא שהמטמון ריק
    manager._categories_cache = None
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות
    mock_categories = [
        {"id": 1, "name": "קטגוריה ראשונה"},
        {"id": 2, "name": "קטגוריה שנייה"}
    ]
    mock_api.get.return_value = mock_categories
    
    # קריאה לפונקציה
    result = await manager.get_categories()
    
    # וידוא שה-API נקרא עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('products/categories', params={'per_page': 100})
    
    # וידוא שהוחזרו הקטגוריות הנכונות
    assert result == mock_categories
    assert len(result) == 2
    
    # וידוא שהמטמון עודכן
    assert manager._categories_cache is not None
    assert manager._categories_cache["data"] == mock_categories


@pytest.mark.asyncio
async def test_find_or_create_category_existing(product_categories):
    """בדיקת מציאת קטגוריה קיימת"""
    manager, mock_api = product_categories
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות
    mock_categories = [
        {"id": 1, "name": "קטגוריה קיימת"},
        {"id": 2, "name": "קטגוריה אחרת"}
    ]
    
    # מוק לפונקציית get_categories
    with patch.object(manager, 'get_categories', return_value=mock_categories):
        # קריאה לפונקציה
        result = await manager.find_or_create_category("קטגוריה קיימת")
        
        # וידוא שהוחזר המזהה הנכון
        assert result == 1


@pytest.mark.asyncio
async def test_find_or_create_category_new(product_categories):
    """בדיקת יצירת קטגוריה חדשה"""
    manager, mock_api = product_categories
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות ללא הקטגוריה המבוקשת
    mock_categories = [
        {"id": 1, "name": "קטגוריה אחרת"},
        {"id": 2, "name": "קטגוריה נוספת"}
    ]
    
    # הגדרת התנהגות המוק ליצירת קטגוריה חדשה
    mock_new_category = {
        "id": 3,
        "name": "קטגוריה חדשה",
        "slug": "new-category"
    }
    mock_api.post.return_value = mock_new_category
    
    # מוק לפונקציית get_categories
    with patch.object(manager, 'get_categories', return_value=mock_categories):
        # קריאה לפונקציה
        result = await manager.find_or_create_category("קטגוריה חדשה")
        
        # וידוא שנקראה הפונקציה ליצירת קטגוריה
        mock_api.post.assert_called_once()
        args, kwargs = mock_api.post.call_args
        assert args[0] == 'products/categories'
        assert kwargs['data']['name'] == "קטגוריה חדשה"
        
        # וידוא שהוחזר המזהה הנכון
        assert result == 3


@pytest.mark.asyncio
async def test_find_or_create_category_error(product_categories):
    """בדיקת טיפול בשגיאה ביצירת קטגוריה"""
    manager, mock_api = product_categories
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות ללא הקטגוריה המבוקשת
    mock_categories = [
        {"id": 1, "name": "קטגוריה אחרת"},
        {"id": 2, "name": "קטגוריה נוספת"}
    ]
    
    # הגדרת התנהגות המוק - החזרת שגיאה ביצירת קטגוריה
    mock_api.post.side_effect = Exception("Failed to create category")
    
    # מוק לפונקציית get_categories
    with patch.object(manager, 'get_categories', return_value=mock_categories):
        # קריאה לפונקציה
        result = await manager.find_or_create_category("קטגוריה חדשה")
        
        # וידוא שנקראה הפונקציה ליצירת קטגוריה
        mock_api.post.assert_called_once()
        
        # וידוא שהוחזר None בגלל השגיאה
        assert result is None


@pytest.mark.asyncio
async def test_handle_product_categories_string(product_categories):
    """בדיקת טיפול בקטגוריות מוצר כמחרוזת"""
    manager, mock_api = product_categories
    
    # נתוני מוצר עם קטגוריה כמחרוזת
    product_data = {
        "name": "מוצר לדוגמה",
        "categories": "קטגוריה לדוגמה"
    }
    
    # מוק לפונקציית find_or_create_category
    with patch.object(manager, 'find_or_create_category', return_value=1) as mock_find:
        # קריאה לפונקציה
        result = await manager.handle_product_categories(product_data)
        
        # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
        mock_find.assert_called_once_with("קטגוריה לדוגמה")
        
        # וידוא שהוחזרו הנתונים הנכונים
        assert "categories" in result
        assert result["categories"] == [{"id": 1}]


@pytest.mark.asyncio
async def test_handle_product_categories_list(product_categories):
    """בדיקת טיפול בקטגוריות מוצר כרשימה"""
    manager, mock_api = product_categories
    
    # נתוני מוצר עם קטגוריות כרשימה
    product_data = {
        "name": "מוצר לדוגמה",
        "categories": ["קטגוריה ראשונה", "קטגוריה שנייה"]
    }
    
    # מוק לפונקציית find_or_create_category
    with patch.object(manager, 'find_or_create_category') as mock_find:
        # הגדרת התנהגות המוק
        mock_find.side_effect = [1, 2]  # מזהי הקטגוריות
        
        # קריאה לפונקציה
        result = await manager.handle_product_categories(product_data)
        
        # וידוא שהפונקציה נקראה פעמיים עם הפרמטרים הנכונים
        assert mock_find.call_count == 2
        mock_find.assert_any_call("קטגוריה ראשונה")
        mock_find.assert_any_call("קטגוריה שנייה")
        
        # וידוא שהוחזרו הנתונים הנכונים
        assert "categories" in result
        assert result["categories"] == [{"id": 1}, {"id": 2}]


@pytest.mark.asyncio
async def test_handle_product_categories_existing_format(product_categories):
    """בדיקת טיפול בקטגוריות מוצר בפורמט קיים"""
    manager, mock_api = product_categories
    
    # נתוני מוצר עם קטגוריות בפורמט קיים
    product_data = {
        "name": "מוצר לדוגמה",
        "categories": [{"id": 1}, {"id": 2}]
    }
    
    # קריאה לפונקציה
    result = await manager.handle_product_categories(product_data)
    
    # וידוא שהנתונים לא השתנו
    assert "categories" in result
    assert result["categories"] == [{"id": 1}, {"id": 2}]


@pytest.mark.asyncio
async def test_handle_product_categories_no_categories(product_categories):
    """בדיקת טיפול במוצר ללא קטגוריות"""
    manager, mock_api = product_categories
    
    # נתוני מוצר ללא קטגוריות
    product_data = {
        "name": "מוצר לדוגמה"
    }
    
    # קריאה לפונקציה
    result = await manager.handle_product_categories(product_data)
    
    # וידוא שהנתונים לא השתנו
    assert result == product_data
    assert "categories" not in result 