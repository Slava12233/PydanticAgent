"""
בדיקות יחידה עבור מנהל המלאי (InventoryManager)
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Optional

from src.tools.store.managers.inventory_manager import InventoryManager


@pytest_asyncio.fixture
async def inventory_manager():
    """פיקסצ'ר ליצירת מופע של מנהל המלאי עם מוקים"""
    # יצירת מוק ל-API של WooCommerce
    mock_api = MagicMock()
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    # יצירת מופע של מנהל המלאי עם ה-API המוקי
    manager = InventoryManager(api=mock_api, use_cache=False)
    
    # החזרת המנהל והמוק ל-API כדי שנוכל לבדוק קריאות
    yield manager, mock_api


@pytest.mark.asyncio
async def test_get_resource_name(inventory_manager):
    """בדיקת קבלת שם המשאב"""
    manager, _ = inventory_manager
    
    # וידוא ששם המשאב הוא 'products'
    assert manager._get_resource_name() == 'products'


@pytest.mark.asyncio
async def test_get_product_stock(inventory_manager):
    """בדיקת קבלת מידע על מלאי מוצר"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מוקי
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 10,
        "manage_stock": True,
        "stock_status": "instock",
        "backorders": "no",
        "low_stock_amount": 2
    }
    mock_api.get.return_value = mock_product
    
    # קריאה לפונקציה
    result = await manager.get_product_stock(123)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('products/123')
    
    # וידוא שהוחזר המידע הנכון
    assert result is not None
    assert result["stock_quantity"] == 10
    assert result["manage_stock"] is True
    assert result["stock_status"] == "instock"


@pytest.mark.asyncio
async def test_get_product_stock_not_found(inventory_manager):
    """בדיקת קבלת מידע על מלאי מוצר שאינו קיים"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.get.side_effect = Exception("Product not found")
    
    # קריאה לפונקציה
    result = await manager.get_product_stock(999)
    
    # וידוא שהפונקציה נקראה
    mock_api.get.assert_called_once_with('products/999')
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_update_product_stock(inventory_manager):
    """בדיקת עדכון מלאי מוצר"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 20,
        "manage_stock": True,
        "stock_status": "instock",
        "low_stock_amount": 5
    }
    mock_api.put.return_value = mock_updated_product
    
    # קריאה לפונקציה
    result = await manager.update_product_stock(123, 20, manage_stock=True, in_stock=True, low_stock_amount=5)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once()
    args, kwargs = mock_api.put.call_args
    assert args[0] == 'products/123'
    assert kwargs['data']['stock_quantity'] == 20
    assert kwargs['data']['manage_stock'] is True
    assert kwargs['data']['stock_status'] == 'instock'
    assert kwargs['data']['low_stock_amount'] == 5
    
    # וידוא שהוחזר המוצר המעודכן
    assert result == mock_updated_product
    assert result["stock_quantity"] == 20
    assert result["low_stock_amount"] == 5


@pytest.mark.asyncio
async def test_update_product_stock_error(inventory_manager):
    """בדיקת עדכון מלאי מוצר עם שגיאה"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.put.side_effect = Exception("Failed to update product stock")
    
    # קריאה לפונקציה
    result = await manager.update_product_stock(123, 20)
    
    # וידוא שהפונקציה נקראה
    mock_api.put.assert_called_once()
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_add_to_stock(inventory_manager):
    """בדיקת הוספת כמות למלאי"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר קיים
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 10,
        "manage_stock": True
    }
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 15,  # 10 + 5
        "manage_stock": True
    }
    
    # מוק לפונקציות get_product_stock ו-update_product_stock
    with patch.object(manager, 'get_product_stock', return_value=mock_product) as mock_get:
        with patch.object(manager, 'update_product_stock', return_value=mock_updated_product) as mock_update:
            # קריאה לפונקציה
            result = await manager.add_to_stock(123, 5)
            
            # וידוא שהפונקציות נקראו עם הפרמטרים הנכונים
            mock_get.assert_called_once_with(123)
            mock_update.assert_called_once_with(123, 15, manage_stock=True)
            
            # וידוא שהוחזר המוצר המעודכן
            assert result == mock_updated_product
            assert result["stock_quantity"] == 15


@pytest.mark.asyncio
async def test_add_to_stock_error_get(inventory_manager):
    """בדיקת הוספת כמות למלאי כאשר המוצר לא נמצא"""
    manager, mock_api = inventory_manager
    
    # מוק לפונקציית get_product_stock שמחזירה None
    with patch.object(manager, 'get_product_stock', return_value=None) as mock_get:
        # קריאה לפונקציה
        result = await manager.add_to_stock(123, 5)
        
        # וידוא שהפונקציה נקראה
        mock_get.assert_called_once_with(123)
        
        # וידוא שהוחזר None
        assert result is None


@pytest.mark.asyncio
async def test_remove_from_stock(inventory_manager):
    """בדיקת הורדת כמות מהמלאי"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר קיים
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 10,
        "manage_stock": True
    }
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 7,  # 10 - 3
        "manage_stock": True
    }
    
    # מוק לפונקציות get_product_stock ו-update_product_stock
    with patch.object(manager, 'get_product_stock', return_value=mock_product) as mock_get:
        with patch.object(manager, 'update_product_stock', return_value=mock_updated_product) as mock_update:
            # קריאה לפונקציה
            result = await manager.remove_from_stock(123, 3)
            
            # וידוא שהפונקציות נקראו עם הפרמטרים הנכונים
            mock_get.assert_called_once_with(123)
            mock_update.assert_called_once_with(123, 7, manage_stock=True)
            
            # וידוא שהוחזר המוצר המעודכן
            assert result == mock_updated_product
            assert result["stock_quantity"] == 7


@pytest.mark.asyncio
async def test_remove_from_stock_insufficient(inventory_manager):
    """בדיקת הורדת כמות מהמלאי כאשר אין מספיק מלאי"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר קיים
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 5,
        "manage_stock": True
    }
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 0,  # מינימום 0
        "manage_stock": True
    }
    
    # מוק לפונקציות get_product_stock ו-update_product_stock
    with patch.object(manager, 'get_product_stock', return_value=mock_product) as mock_get:
        with patch.object(manager, 'update_product_stock', return_value=mock_updated_product) as mock_update:
            # קריאה לפונקציה עם כמות גדולה יותר מהמלאי
            result = await manager.remove_from_stock(123, 10)
            
            # וידוא שהפונקציות נקראו עם הפרמטרים הנכונים
            mock_get.assert_called_once_with(123)
            mock_update.assert_called_once_with(123, 0, manage_stock=True)  # מינימום 0
            
            # וידוא שהוחזר המוצר המעודכן
            assert result == mock_updated_product
            assert result["stock_quantity"] == 0


@pytest.mark.asyncio
async def test_set_backorders_policy(inventory_manager):
    """בדיקת הגדרת מדיניות הזמנות מראש"""
    manager, mock_api = inventory_manager
    
    # הגדרת התנהגות המוק - החזרת מוצר מעודכן
    mock_updated_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "backorders": "yes",
        "backorders_allowed": True
    }
    mock_api.put.return_value = mock_updated_product
    
    # קריאה לפונקציה
    result = await manager.set_backorders_policy(123, "yes")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once()
    args, kwargs = mock_api.put.call_args
    assert args[0] == 'products/123'
    assert kwargs['data']['backorders'] == 'yes'
    
    # וידוא שהוחזר המוצר המעודכן
    assert result == mock_updated_product
    assert result["backorders"] == "yes"
    assert result["backorders_allowed"] is True


@pytest.mark.asyncio
async def test_forecast_inventory(inventory_manager):
    """בדיקת תחזית מלאי"""
    manager, mock_api = inventory_manager
    
    # מוק לפונקציית forecast_inventory של InventoryForecasting
    with patch('src.tools.store.managers.inventory_forecasting.InventoryForecasting.forecast_inventory') as mock_forecast:
        # הגדרת התנהגות המוק
        mock_forecast_result = {
            "product_id": 123,
            "current_stock": 10,
            "forecast": [
                {"period": 7, "predicted_stock": 5},
                {"period": 14, "predicted_stock": 0},
                {"period": 30, "predicted_stock": -10}
            ],
            "restock_recommendation": True,
            "recommended_quantity": 20
        }
        mock_forecast.return_value = mock_forecast_result
        
        # קריאה לפונקציה
        result = await manager.forecast_inventory(123, days=30, forecast_periods=[7, 14, 30])
        
        # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
        mock_forecast.assert_called_once_with(123, days=30, forecast_periods=[7, 14, 30])
        
        # וידוא שהוחזרה התחזית הנכונה
        assert result == mock_forecast_result
        assert result["product_id"] == 123
        assert result["restock_recommendation"] is True


@pytest.mark.asyncio
async def test_get_low_stock_products(inventory_manager):
    """בדיקת קבלת מוצרים במלאי נמוך"""
    manager, mock_api = inventory_manager
    
    # מוק לפונקציית get_low_stock_products של InventoryReporting
    with patch('src.tools.store.managers.inventory_reporting.InventoryReporting.get_low_stock_products') as mock_get_low:
        # הגדרת התנהגות המוק
        mock_low_stock_products = [
            {
                "id": 123,
                "name": "מוצר ראשון",
                "stock_quantity": 2,
                "low_stock_amount": 5,
                "alert_level": "high"
            },
            {
                "id": 124,
                "name": "מוצר שני",
                "stock_quantity": 3,
                "low_stock_amount": 5,
                "alert_level": "medium"
            }
        ]
        mock_get_low.return_value = mock_low_stock_products
        
        # קריאה לפונקציה
        result = await manager.get_low_stock_products(threshold=5, include_alerts=True)
        
        # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
        mock_get_low.assert_called_once_with(threshold=5, include_alerts=True, 
                                            high_threshold_percentage=0.25, 
                                            medium_threshold_percentage=0.5, 
                                            per_page=100, category_id=None)
        
        # וידוא שהוחזרה רשימת המוצרים הנכונה
        assert result == mock_low_stock_products
        assert len(result) == 2
        assert result[0]["alert_level"] == "high"


@pytest.mark.asyncio
async def test_get_out_of_stock_products(inventory_manager):
    """בדיקת קבלת מוצרים שאזלו מהמלאי"""
    manager, mock_api = inventory_manager
    
    # מוק לפונקציית get_out_of_stock_products של InventoryReporting
    with patch('src.tools.store.managers.inventory_reporting.InventoryReporting.get_out_of_stock_products') as mock_get_out:
        # הגדרת התנהגות המוק
        mock_out_of_stock_products = [
            {
                "id": 123,
                "name": "מוצר ראשון",
                "stock_quantity": 0,
                "stock_status": "outofstock"
            },
            {
                "id": 124,
                "name": "מוצר שני",
                "stock_quantity": 0,
                "stock_status": "outofstock"
            }
        ]
        mock_get_out.return_value = mock_out_of_stock_products
        
        # קריאה לפונקציה
        result = await manager.get_out_of_stock_products()
        
        # וידוא שהפונקציה נקראה
        mock_get_out.assert_called_once()
        
        # וידוא שהוחזרה רשימת המוצרים הנכונה
        assert result == mock_out_of_stock_products
        assert len(result) == 2
        assert result[0]["stock_status"] == "outofstock"


@pytest.mark.asyncio
async def test_get_inventory_report(inventory_manager):
    """בדיקת קבלת דוח מלאי"""
    manager, mock_api = inventory_manager
    
    # מוק לפונקציית get_inventory_report של InventoryReporting
    with patch('src.tools.store.managers.inventory_reporting.InventoryReporting.get_inventory_report') as mock_get_report:
        # הגדרת התנהגות המוק
        mock_inventory_report = {
            "total_products": 10,
            "in_stock": 8,
            "out_of_stock": 2,
            "low_stock": 3,
            "total_stock_value": 5000,
            "products": [
                {
                    "id": 123,
                    "name": "מוצר ראשון",
                    "stock_quantity": 5,
                    "stock_value": 500
                },
                {
                    "id": 124,
                    "name": "מוצר שני",
                    "stock_quantity": 10,
                    "stock_value": 1000
                }
            ]
        }
        mock_get_report.return_value = mock_inventory_report
        
        # קריאה לפונקציה
        result = await manager.get_inventory_report(per_page=100)
        
        # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
        mock_get_report.assert_called_once_with(per_page=100, category_id=None)
        
        # וידוא שהוחזר הדוח הנכון
        assert result == mock_inventory_report
        assert result["total_products"] == 10
        assert result["in_stock"] == 8
        assert result["out_of_stock"] == 2 