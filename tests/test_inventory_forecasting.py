"""
בדיקות יחידה למודול inventory_forecasting
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.store_tools.managers.inventory_forecasting import InventoryForecasting

@pytest.fixture
def mock_api():
    """יצירת mock ל-API"""
    api = AsyncMock()
    return api

@pytest.fixture
def forecasting(mock_api):
    """יצירת אובייקט InventoryForecasting לבדיקות"""
    return InventoryForecasting(woocommerce_api=mock_api)

@pytest.mark.asyncio
async def test_forecast_inventory_success(forecasting, mock_api):
    """בדיקת חיזוי מלאי מוצלח"""
    # הגדרת נתוני מוצר לדוגמה
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 100,
        "manage_stock": True
    }
    
    # הגדרת הזמנות לדוגמה
    mock_orders = [
        {
            "status": "completed",
            "line_items": [
                {"product_id": 123, "quantity": 5}
            ]
        },
        {
            "status": "processing",
            "line_items": [
                {"product_id": 123, "quantity": 3}
            ]
        }
    ]
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, mock_product),  # תשובה לקבלת המוצר
        (200, mock_orders)  # תשובה לקבלת ההזמנות
    ]
    
    # הרצת הפונקציה
    result = await forecasting.forecast_inventory(123, days=30, forecast_periods=[7, 14])
    
    # בדיקות
    assert result["success"] is True
    assert "forecast" in result
    forecast_data = result["forecast"]
    
    # בדיקת שדות חובה
    assert forecast_data["product_id"] == 123
    assert forecast_data["product_name"] == "מוצר לדוגמה"
    assert forecast_data["current_stock"] == 100
    assert forecast_data["total_sold_last_30_days"] == 8  # 5 + 3
    assert forecast_data["daily_sales_avg"] == pytest.approx(8/30, 0.01)
    
    # בדיקת תחזיות
    assert "7_days" in forecast_data["forecast"]
    assert "14_days" in forecast_data["forecast"]
    
    # בדיקת המלצות
    assert isinstance(forecast_data["will_be_out_of_stock"], bool)
    assert isinstance(forecast_data["reorder_recommendation"], bool)

@pytest.mark.asyncio
async def test_forecast_inventory_product_not_found(forecasting, mock_api):
    """בדיקת חיזוי מלאי כאשר המוצר לא נמצא"""
    # הגדרת תשובת ה-mock
    mock_api._make_request.return_value = (404, {"message": "Product not found"})
    
    # הרצת הפונקציה
    result = await forecasting.forecast_inventory(999)
    
    # בדיקות
    assert result["success"] is False
    assert "מוצר לא נמצא" in result["message"]
    assert result["forecast"] is None

@pytest.mark.asyncio
async def test_forecast_inventory_no_orders(forecasting, mock_api):
    """בדיקת חיזוי מלאי כאשר אין הזמנות"""
    # הגדרת נתוני מוצר לדוגמה
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 100,
        "manage_stock": True
    }
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, mock_product),  # תשובה לקבלת המוצר
        (200, [])  # אין הזמנות
    ]
    
    # הרצת הפונקציה
    result = await forecasting.forecast_inventory(123)
    
    # בדיקות
    assert result["success"] is True
    forecast_data = result["forecast"]
    assert forecast_data["daily_sales_avg"] == 0
    assert forecast_data["total_sold_last_30_days"] == 0
    assert forecast_data["days_until_stockout"] is None  # אין מכירות, אז אין תאריך אזילת מלאי

@pytest.mark.asyncio
async def test_forecast_inventory_with_custom_periods(forecasting, mock_api):
    """בדיקת חיזוי מלאי עם תקופות מותאמות אישית"""
    # הגדרת נתוני מוצר לדוגמה
    mock_product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "stock_quantity": 100,
        "manage_stock": True
    }
    
    # הגדרת הזמנות לדוגמה
    mock_orders = [
        {
            "status": "completed",
            "line_items": [
                {"product_id": 123, "quantity": 10}
            ]
        }
    ]
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, mock_product),  # תשובה לקבלת המוצר
        (200, mock_orders)  # תשובה לקבלת ההזמנות
    ]
    
    # הגדרת תקופות חיזוי מותאמות
    custom_periods = [15, 45, 75]
    
    # הרצת הפונקציה
    result = await forecasting.forecast_inventory(123, forecast_periods=custom_periods)
    
    # בדיקות
    assert result["success"] is True
    forecast_data = result["forecast"]
    
    # בדיקת קיום כל התקופות המותאמות
    for period in custom_periods:
        assert f"{period}_days" in forecast_data["forecast"]

@pytest.mark.asyncio
async def test_forecast_inventory_error_handling(forecasting, mock_api):
    """בדיקת טיפול בשגיאות בחיזוי מלאי"""
    # הגדרת שגיאה בקבלת המוצר
    mock_api._make_request.side_effect = Exception("API Error")
    
    # הרצת הפונקציה
    result = await forecasting.forecast_inventory(123)
    
    # בדיקות
    assert result["success"] is False
    assert "שגיאה בחיזוי מלאי" in result["message"]
    assert result["forecast"] is None 