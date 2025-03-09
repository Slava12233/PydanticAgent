"""
בדיקות יחידה עבור מנהל הלקוחות (CustomerManager)
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import Dict, Any, List, Optional, Union

from src.tools.store.managers.customer_manager import CustomerManager


@pytest_asyncio.fixture
async def customer_manager():
    """פיקסצ'ר ליצירת מופע של מנהל הלקוחות עם מוקים"""
    # יצירת מוק ל-API של WooCommerce
    mock_api = MagicMock()
    mock_api.get = AsyncMock()
    mock_api.post = AsyncMock()
    mock_api.put = AsyncMock()
    mock_api.delete = AsyncMock()
    
    # יצירת מופע של מנהל הלקוחות עם ה-API המוקי
    manager = CustomerManager(api=mock_api, use_cache=False)
    
    # החזרת המנהל והמוק ל-API כדי שנוכל לבדוק קריאות
    yield manager, mock_api


@pytest.mark.asyncio
async def test_get_resource_name(customer_manager):
    """בדיקת קבלת שם המשאב"""
    manager, _ = customer_manager
    
    # וידוא ששם המשאב הוא 'customers'
    assert manager._get_resource_name() == 'customers'


@pytest.mark.asyncio
async def test_create_customer(customer_manager):
    """בדיקת יצירת לקוח חדש"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת לקוח מוקי
    mock_customer = {
        "id": 123,
        "email": "test@example.com",
        "first_name": "ישראל",
        "last_name": "ישראלי",
        "username": "israel123",
        "billing": {
            "phone": "0501234567"
        }
    }
    mock_api.post.return_value = mock_customer
    
    # נתוני הלקוח לשליחה
    customer_data = {
        "email": "test@example.com",
        "first_name": "ישראל",
        "last_name": "ישראלי",
        "username": "israel123",
        "billing": {
            "phone": "0501234567"
        }
    }
    
    # קריאה לפונקציה
    result = await manager.create_customer(customer_data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.post.assert_called_once()
    args, kwargs = mock_api.post.call_args
    assert args[0] == 'customers'
    assert kwargs['data'] == customer_data
    
    # וידוא שהוחזר הלקוח הנכון
    assert result == mock_customer
    assert result["id"] == 123
    assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_customer(customer_manager):
    """בדיקת קבלת לקוח לפי מזהה"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת לקוח מוקי
    mock_customer = {
        "id": 123,
        "email": "test@example.com",
        "first_name": "ישראל",
        "last_name": "ישראלי"
    }
    mock_api.get.return_value = mock_customer
    
    # קריאה לפונקציה
    result = await manager.get_customer(123)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once_with('customers/123')
    
    # וידוא שהוחזר הלקוח הנכון
    assert result == mock_customer
    assert result["id"] == 123
    assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_customer_not_found(customer_manager):
    """בדיקת קבלת לקוח שאינו קיים"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.get.side_effect = Exception("Customer not found")
    
    # קריאה לפונקציה
    result = await manager.get_customer(999)
    
    # וידוא שהפונקציה נקראה
    mock_api.get.assert_called_once_with('customers/999')
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_update_customer(customer_manager):
    """בדיקת עדכון לקוח קיים"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת לקוח מעודכן
    mock_updated_customer = {
        "id": 123,
        "email": "updated@example.com",
        "first_name": "ישראל",
        "last_name": "ישראלי מעודכן"
    }
    mock_api.put.return_value = mock_updated_customer
    
    # נתוני העדכון
    update_data = {
        "email": "updated@example.com",
        "last_name": "ישראלי מעודכן"
    }
    
    # קריאה לפונקציה
    result = await manager.update_customer(123, update_data)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.put.assert_called_once()
    args, kwargs = mock_api.put.call_args
    assert args[0] == 'customers/123'
    assert kwargs['data'] == update_data
    
    # וידוא שהוחזר הלקוח המעודכן
    assert result == mock_updated_customer
    assert result["email"] == "updated@example.com"
    assert result["last_name"] == "ישראלי מעודכן"


@pytest.mark.asyncio
async def test_update_customer_error(customer_manager):
    """בדיקת עדכון לקוח עם שגיאה"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.put.side_effect = Exception("Failed to update customer")
    
    # קריאה לפונקציה
    result = await manager.update_customer(123, {"email": "new@example.com"})
    
    # וידוא שהפונקציה נקראה
    mock_api.put.assert_called_once()
    
    # וידוא שהוחזר None
    assert result is None


@pytest.mark.asyncio
async def test_delete_customer(customer_manager):
    """בדיקת מחיקת לקוח"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת תשובה מוצלחת
    mock_api.delete.return_value = {"deleted": True, "previous": {"id": 123}}
    
    # קריאה לפונקציה
    result = await manager.delete_customer(123, force=True)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.delete.assert_called_once()
    args, kwargs = mock_api.delete.call_args
    assert args[0] == 'customers/123'
    assert kwargs['params']['force'] is True
    
    # וידוא שהוחזרה תשובה חיובית
    assert result is True


@pytest.mark.asyncio
async def test_delete_customer_error(customer_manager):
    """בדיקת מחיקת לקוח עם שגיאה"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת שגיאה
    mock_api.delete.side_effect = Exception("Failed to delete customer")
    
    # קריאה לפונקציה
    result = await manager.delete_customer(123)
    
    # וידוא שהפונקציה נקראה
    mock_api.delete.assert_called_once()
    
    # וידוא שהוחזרה תשובה שלילית
    assert result is False


@pytest.mark.asyncio
async def test_search_customers(customer_manager):
    """בדיקת חיפוש לקוחות"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת לקוחות
    mock_customers = [
        {
            "id": 123,
            "email": "test1@example.com",
            "first_name": "ישראל",
            "last_name": "ישראלי"
        },
        {
            "id": 124,
            "email": "test2@example.com",
            "first_name": "שרה",
            "last_name": "ישראלי"
        }
    ]
    mock_api.get.return_value = mock_customers
    
    # קריאה לפונקציה
    result = await manager.search_customers("ישראלי", limit=10)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'customers'
    assert 'search' in kwargs['params']
    assert kwargs['params']['search'] == "ישראלי"
    assert kwargs['params']['per_page'] == 10
    
    # וידוא שהוחזרה רשימת הלקוחות
    assert result == mock_customers
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_customer_orders(customer_manager):
    """בדיקת קבלת הזמנות של לקוח"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת הזמנות
    mock_orders = [
        {
            "id": 456,
            "customer_id": 123,
            "status": "processing",
            "total": "100.00"
        },
        {
            "id": 457,
            "customer_id": 123,
            "status": "completed",
            "total": "200.00"
        }
    ]
    mock_api.get.return_value = mock_orders
    
    # קריאה לפונקציה
    result = await manager.get_customer_orders(123)
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'orders'
    assert kwargs['params']['customer'] == 123
    
    # וידוא שהוחזרה רשימת ההזמנות
    assert result == mock_orders
    assert len(result) == 2
    assert result[0]["customer_id"] == 123


@pytest.mark.asyncio
async def test_get_customer_by_email(customer_manager):
    """בדיקת קבלת לקוח לפי כתובת אימייל"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת רשימת לקוחות
    mock_customers = [
        {
            "id": 123,
            "email": "test@example.com",
            "first_name": "ישראל",
            "last_name": "ישראלי"
        }
    ]
    mock_api.get.return_value = mock_customers
    
    # קריאה לפונקציה
    result = await manager.get_customer_by_email("test@example.com")
    
    # וידוא שהפונקציה נקראה עם הפרמטרים הנכונים
    mock_api.get.assert_called_once()
    args, kwargs = mock_api.get.call_args
    assert args[0] == 'customers'
    assert kwargs['params']['email'] == "test@example.com"
    
    # וידוא שהוחזר הלקוח הנכון
    assert result == mock_customers[0]
    assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_customer_by_email_not_found(customer_manager):
    """בדיקת קבלת לקוח לפי כתובת אימייל שאינה קיימת"""
    manager, mock_api = customer_manager
    
    # הגדרת התנהגות המוק - החזרת רשימה ריקה
    mock_api.get.return_value = []
    
    # קריאה לפונקציה
    result = await manager.get_customer_by_email("nonexistent@example.com")
    
    # וידוא שהפונקציה נקראה
    mock_api.get.assert_called_once()
    
    # וידוא שהוחזר None
    assert result is None 