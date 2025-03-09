"""
בדיקות יחידה עבור מנהל המוצרים (ProductManager)
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Optional

from src.tools.store.managers.product_manager import ProductManager


@pytest_asyncio.fixture
async def product_manager():
    """פיקסצ'ר ליצירת מופע של מנהל המוצרים עם מוקים"""
    # יצירת מוק ל-API של WooCommerce
    mock_api = MagicMock()
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    # יצירת מופע של מנהל המוצרים עם ה-API המוקי
    manager = ProductManager(api=mock_api, use_cache=False)
    
    # החזרת המנהל והמוק ל-API כדי שנוכל לבדוק קריאות
    yield manager, mock_api


@pytest.mark.asyncio
async def test_get_resource_name(product_manager):
    """בדיקת קבלת שם המשאב"""
    manager, _ = product_manager
    
    # וידוא ששם המשאב הוא 'products'
    assert manager._get_resource_name() == 'products'


@pytest.mark.asyncio
async def test_create_product(product_manager):
    """בדיקת יצירת מוצר חדש"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מוקי
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "price": "100",
        "regular_price": "100",
        "description": "תיאור המוצר",
        "categories": []
    }
    mock_api.post.return_value = mock_product
    
    # נתוני המוצר לשליחה
    product_data = {
        "name": "מוצר לדוגמה",
        "regular_price": "100",
        "description": "תיאור המוצר"
    }
    
    # קריאה לפונקציה
    result = await manager.create_product(product_data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.post.assert_called_once()
    args, kwargs = mock_api.post.call_args
    assert args[0] == 'products'
    
    # וידוא שהוחזר המוצר הנכון
    assert result == mock_product
    assert result["id"] == 123
    assert result["name"] == "מוצר לדוגמה"


@pytest.mark.asyncio
async def test_update_product(product_manager):
    """בדיקת עדכון מוצר קיים"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר מעודכן",
        "price": "150",
        "regular_price": "150",
        "description": "תיאור מעודכן",
        "categories": []
    }
    mock_api.put.return_value = mock_updated_product
    
    # נתוני העדכון
    update_data = {
        "name": "מוצר מעודכן",
        "regular_price": "150",
        "description": "תיאור מעודכן"
    }
    
    # קריאה לפונקציה
    result = await manager.update_product(123, update_data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once()
    args, kwargs = mock_api.put.call_args
    assert args[0] == 'products/123'
    
    # וידוא שהוחזר המוצר המעודכן
    assert result == mock_updated_product
    assert result["name"] == "מוצר מעודכן"
    assert result["regular_price"] == "150"


@pytest.mark.asyncio
async def test_get_product(product_manager):
    """בדיקת קבלת מוצר לפי מזהה"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מוקי
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "price": "100",
        "regular_price": "100",
        "description": "תיאור המוצר",
        "categories": []
    }
    mock_api.get.return_value = mock_product
    
    # קריאה לפונקציה
    result = await manager.get_product(123)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('products/123')
    
    # וידוא שהוחזר המוצר הנכון
    assert result == mock_product
    assert result["id"] == 123


@pytest.mark.asyncio
async def test_get_product_not_found(product_manager):
    """בדיקת קבלת מוצר שאינו קיים"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.get.side_effect = Exception("Product not found")
    
    # קריאה לפונקציה
    result = await manager.get_product(999)
    
    # וידוא שהפונקציה נקראה
    mock_api.get.assert_called_once_with('products/999')
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_search_products(product_manager):
    """בדיקת חיפוש מוצרים"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת מוצרים
    mock_products = [
        {
            "id": 123,
            "name": "מוצר ראשון",
            "price": "100",
            "regular_price": "100"
        },
        {
            "id": 124,
            "name": "מוצר שני",
            "price": "200",
            "regular_price": "200"
        }
    ]
    mock_api.get.return_value = mock_products
    
    # קריאה לפונקציה
    result = await manager.search_products("מוצר", limit=10)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'products'
    assert 'search' in kwargs['params']
    assert kwargs['params']['search'] == "מוצר"
    assert kwargs['params']['per_page'] == 10
    
    # וידוא שהוחזרה רשימת המוצרים
    assert result == mock_products
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_categories(product_manager):
    """בדיקת קבלת קטגוריות"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות
    mock_categories = [
        {
            "id": 15,
            "name": "קטגוריה ראשונה",
            "slug": "category-1"
        },
        {
            "id": 16,
            "name": "קטגוריה שנייה",
            "slug": "category-2"
        }
    ]
    mock_api.get.return_value = mock_categories
    
    # קריאה לפונקציה
    result = await manager.get_categories()
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('products/categories', params={'per_page': 100})
    
    # וידוא שהוחזרה רשימת הקטגוריות
    assert result == mock_categories
    assert len(result) == 2


@pytest.mark.asyncio
async def test_find_or_create_category_existing(product_manager):
    """בדיקת מציאת קטגוריה קיימת"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות
    mock_categories = [
        {
            "id": 15,
            "name": "קטגוריה קיימת",
            "slug": "existing-category"
        }
    ]
    mock_api.get.return_value = mock_categories
    
    # מוק לפונקציית get_categories
    with patch.object(manager, 'get_categories', return_value=mock_categories):
        # קריאה לפונקציה
        result = await manager._find_or_create_category("קטגוריה קיימת")
        
        # וידוא שהוחזר המזהה הנכון
        assert result == 15


@pytest.mark.asyncio
async def test_find_or_create_category_new(product_manager):
    """בדיקת יצירת קטגוריה חדשה"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת קטגוריות ריקה
    mock_api.get.return_value = []
    
    # הגדרת התנהגות המוק ליצירת קטגוריה חדשה
    mock_new_category = {
        "id": 20,
        "name": "קטגוריה חדשה",
        "slug": "new-category"
    }
    mock_api.post.return_value = mock_new_category
    
    # מוק לפונקציית get_categories
    with patch.object(manager, 'get_categories', return_value=[]):
        # קריאה לפונקציה
        result = await manager._find_or_create_category("קטגוריה חדשה")
        
        # וידוא שנקראה הפונקציה ליצירת קטגוריה
        mock_api.post.assert_called_once()
        args, kwargs = mock_api.post.call_args
        assert args[0] == 'products/categories'
        assert kwargs['data']['name'] == "קטגוריה חדשה"
        
        # וידוא שהוחזר המזהה הנכון
        assert result == 20


@pytest.mark.asyncio
async def test_handle_categories(product_manager):
    """בדיקת טיפול בקטגוריות של מוצר"""
    manager, mock_api = product_manager
    
    # נתוני מוצר עם קטגוריות
    product_data = {
        "name": "מוצר עם קטגוריות",
        "categories": ["קטגוריה ראשונה", "קטגוריה שנייה"]
    }
    
    # מוק לפונקציית _find_or_create_category
    with patch.object(manager, '_find_or_create_category') as mock_find_or_create:
        # הגדרת התנהגות המוק
        mock_find_or_create.side_effect = [15, 16]  # מזהי הקטגוריות
        
        # קריאה לפונקציה
        result = await manager._handle_categories(product_data)
        
        # וידוא שהפונקציה נקראה פעמיים עם הפרמטרים הנכונים
        assert mock_find_or_create.call_count == 2
        mock_find_or_create.assert_any_call("קטגוריה ראשונה")
        mock_find_or_create.assert_any_call("קטגוריה שנייה")
        
        # וידוא שהוחזרו הנתונים הנכונים
        assert "categories" in result
        assert result["categories"] == [{"id": 15}, {"id": 16}]


@pytest.mark.asyncio
async def test_get_products(product_manager):
    """בדיקת קבלת רשימת מוצרים"""
    manager, mock_api = product_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת מוצרים
    mock_products = [
        {
            "id": 123,
            "name": "מוצר ראשון",
            "price": "100"
        },
        {
            "id": 124,
            "name": "מוצר שני",
            "price": "200"
        }
    ]
    mock_api.get.return_value = mock_products
    
    # קריאה לפונקציה
    result = await manager.get_products(per_page=20, page=1, status="publish")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'products'
    assert kwargs['params']['per_page'] == 20
    assert kwargs['params']['page'] == 1
    assert kwargs['params']['status'] == "publish"
    
    # וידוא שהוחזרה רשימת המוצרים
    assert result == mock_products
    assert len(result) == 2 