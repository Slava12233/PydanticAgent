"""
בדיקות יחידה עבור מנהל ההזמנות (OrderManager)
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Optional, Union

from src.tools.store.managers.order_manager import OrderManager


@pytest_asyncio.fixture
async def order_manager():
    """פיקסצ'ר ליצירת מופע של מנהל ההזמנות עם מוקים"""
    # יצירת מוק ל-API של WooCommerce
    mock_api = MagicMock()
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    # יצירת מופע של מנהל ההזמנות עם ה-API המוקי
    manager = OrderManager(api=mock_api, use_cache=False)
    
    # החזרת המנהל והמוק ל-API כדי שנוכל לבדוק קריאות
    yield manager, mock_api


@pytest.mark.asyncio
async def test_get_resource_name(order_manager):
    """בדיקת קבלת שם המשאב"""
    manager, _ = order_manager
    
    # וידוא ששם המשאב הוא 'orders'
    assert manager._get_resource_name() == 'orders'


@pytest.mark.asyncio
async def test_get_orders(order_manager):
    """בדיקת קבלת רשימת הזמנות"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת הזמנות
    mock_orders = [
        {
            "id": 123,
            "status": "processing",
            "total": "100.00",
            "customer_id": 1
        },
        {
            "id": 124,
            "status": "completed",
            "total": "200.00",
            "customer_id": 2
        }
    ]
    mock_api.get.return_value = mock_orders
    
    # קריאה לפונקציה ללא פילטרים
    result = await manager.get_orders()
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'orders'
    assert 'params' in kwargs
    
    # וידוא שהוחזרה רשימת ההזמנות
    assert result == mock_orders
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_orders_with_filters(order_manager):
    """בדיקת קבלת רשימת הזמנות עם פילטרים"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת הזמנות מסוננת
    mock_filtered_orders = [
        {
            "id": 123,
            "status": "processing",
            "total": "100.00",
            "customer_id": 1
        }
    ]
    mock_api.get.return_value = mock_filtered_orders
    
    # פילטרים לשאילתה
    filters = {
        "status": "processing",
        "customer_id": 1
    }
    
    # קריאה לפונקציה עם פילטרים
    result = await manager.get_orders(filters)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'orders'
    assert 'params' in kwargs
    assert kwargs['params']['status'] == 'processing'
    assert kwargs['params']['customer'] == 1
    
    # וידוא שהוחזרה רשימת ההזמנות המסוננת
    assert result == mock_filtered_orders
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_order(order_manager):
    """בדיקת קבלת הזמנה לפי מזהה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת הזמנה מוקית
    mock_order = {
        "id": 123,
        "status": "processing",
        "total": "100.00",
        "customer_id": 1,
        "line_items": [
            {
                "id": 1,
                "name": "מוצר לדוגמה",
                "quantity": 2,
                "price": "50.00"
            }
        ]
    }
    mock_api.get.return_value = mock_order
    
    # קריאה לפונקציה
    result = await manager.get_order(123)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('orders/123')
    
    # וידוא שהוחזרה ההזמנה הנכונה
    assert result == mock_order
    assert result["id"] == 123
    assert result["status"] == "processing"


@pytest.mark.asyncio
async def test_get_order_not_found(order_manager):
    """בדיקת קבלת הזמנה שאינה קיימת"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.get.side_effect = Exception("Order not found")
    
    # קריאה לפונקציה
    result = await manager.get_order(999)
    
    # וידוא שהפונקציה נקראה
    mock_api.get.assert_called_once_with('orders/999')
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_update_order_status(order_manager):
    """בדיקת עדכון סטטוס הזמנה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת הזמנה מעודכנת
    mock_updated_order = {
        "id": 123,
        "status": "completed",
        "total": "100.00",
        "customer_id": 1
    }
    mock_api.put.return_value = mock_updated_order
    
    # קריאה לפונקציה
    result = await manager.update_order_status(123, "completed", "ההזמנה הושלמה")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once()
    args, kwargs = mock_api.put.call_args
    assert args[0] == 'orders/123'
    assert kwargs['data']['status'] == 'completed'
    assert 'note' in kwargs['data']
    assert kwargs['data']['note'] == 'ההזמנה הושלמה'
    
    # וידוא שהוחזרה ההזמנה המעודכנת
    assert result == mock_updated_order
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_update_order_status_error(order_manager):
    """בדיקת עדכון סטטוס הזמנה עם שגיאה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.put.side_effect = Exception("Failed to update order")
    
    # קריאה לפונקציה
    result = await manager.update_order_status(123, "completed")
    
    # וידוא שהפונקציה נקראה
    mock_api.put.assert_called_once()
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_cancel_order(order_manager):
    """בדיקת ביטול הזמנה"""
    manager, mock_api = order_manager
    
    # מוק לפונקציית update_order_status
    with patch.object(manager, 'update_order_status') as mock_update:
        # הגדרת התנהגות המוק
        mock_cancelled_order = {
            "id": 123,
            "status": "cancelled",
            "total": "100.00"
        }
        mock_update.return_value = mock_cancelled_order
        
        # קריאה לפונקציה
        result = await manager.cancel_order(123, "ביטול לבקשת הלקוח")
        
        # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
        mock_update.assert_called_once_with(123, "cancelled", "ביטול לבקשת הלקוח")
        
        # וידוא שהוחזרה ההזמנה המבוטלת
        assert result == mock_cancelled_order
        assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_refund_order(order_manager):
    """בדיקת החזר כספי להזמנה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת תשובה מוצלחת
    mock_refund_response = {
        "id": 456,
        "order_id": 123,
        "amount": "100.00",
        "reason": "החזר כספי לבקשת הלקוח"
    }
    mock_api.post.return_value = mock_refund_response
    
    # קריאה לפונקציה
    result = await manager.refund_order(123, 100.00, "החזר כספי לבקשת הלקוח")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.post.assert_called_once()
    args, kwargs = mock_api.post.call_args
    assert args[0] == 'orders/123/refunds'
    assert kwargs['data']['amount'] == '100.00'
    assert kwargs['data']['reason'] == 'החזר כספי לבקשת הלקוח'
    
    # וידוא שהוחזרה תשובת ההחזר הכספי
    assert result == mock_refund_response


@pytest.mark.asyncio
async def test_refund_order_error(order_manager):
    """בדיקת החזר כספי להזמנה עם שגיאה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.post.side_effect = Exception("Failed to refund order")
    
    # קריאה לפונקציה
    result = await manager.refund_order(123, 100.00)
    
    # וידוא שהפונקציה נקראה
    mock_api.post.assert_called_once()
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_refund_order_full_amount(order_manager):
    """בדיקת החזר כספי מלא להזמנה"""
    manager, mock_api = order_manager
    
    # הגדרת התנהגות המוק - החזרת הזמנה
    mock_order = {
        "id": 123,
        "status": "processing",
        "total": "150.00"
    }
    
    # מוק לפונקציית get_order
    with patch.object(manager, 'get_order', return_value=mock_order):
        # הגדרת התנהגות המוק להחזר כספי
        mock_refund_response = {
            "id": 456,
            "order_id": 123,
            "amount": "150.00",
            "reason": "החזר כספי מלא"
        }
        mock_api.post.return_value = mock_refund_response
        
        # קריאה לפונקציה ללא ציון סכום (החזר מלא)
        result = await manager.refund_order(123, reason="החזר כספי מלא")
        
        # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
        mock_api.post.assert_called_once()
        args, kwargs = mock_api.post.call_args
        assert args[0] == 'orders/123/refunds'
        assert kwargs['data']['amount'] == '150.00'
        
        # וידוא שהוחזרה תשובת ההחזר הכספי
        assert result == mock_refund_response 