"""
בדיקות יחידה למודול inventory_reporting
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.store_tools.managers.inventory_reporting import InventoryReporting

@pytest.fixture
def mock_api():
    """יצירת mock ל-API"""
    api = AsyncMock()
    return api

@pytest.fixture
def reporting(mock_api):
    """יצירת אובייקט InventoryReporting לבדיקות"""
    return InventoryReporting(woocommerce_api=mock_api)

def test_get_alert_emoji(reporting):
    """בדיקת קבלת אימוג'י התראה"""
    assert reporting._get_alert_emoji("critical") == "🚨"
    assert reporting._get_alert_emoji("high") == "⚠️"
    assert reporting._get_alert_emoji("medium") == "⚠️"
    assert reporting._get_alert_emoji("low") == "📉"
    assert reporting._get_alert_emoji("unknown") == "📊"  # ברירת מחדל

def test_get_alert_message(reporting):
    """בדיקת יצירת הודעת התראה"""
    product_name = "מוצר לדוגמה"
    stock_quantity = 5
    threshold = 20
    
    # בדיקת הודעות לכל רמת חומרה
    critical_msg = reporting._get_alert_message("critical", product_name, 0, threshold)
    assert "אזל מהמלאי" in critical_msg
    assert product_name in critical_msg
    
    high_msg = reporting._get_alert_message("high", product_name, stock_quantity, threshold)
    assert "מלאי נמוך מאוד" in high_msg
    assert str(stock_quantity) in high_msg
    
    medium_msg = reporting._get_alert_message("medium", product_name, stock_quantity, threshold)
    assert "מלאי נמוך" in medium_msg
    assert str(stock_quantity) in medium_msg
    
    low_msg = reporting._get_alert_message("low", product_name, stock_quantity, threshold)
    assert "מתקרב לסף" in low_msg
    assert str(threshold) in low_msg

@pytest.mark.asyncio
async def test_get_low_stock_products(reporting, mock_api):
    """בדיקת קבלת מוצרים עם מלאי נמוך"""
    # הגדרת מוצרים לדוגמה
    mock_products = [
        {
            "id": 1,
            "name": "מוצר 1",
            "sku": "SKU1",
            "manage_stock": True,
            "stock_quantity": 5,
            "low_stock_amount": 20,
            "price": "100.00",
            "date_modified": "2024-01-01T00:00:00"
        },
        {
            "id": 2,
            "name": "מוצר 2",
            "sku": "SKU2",
            "manage_stock": True,
            "stock_quantity": 0,
            "low_stock_amount": 10,
            "price": "50.00",
            "date_modified": "2024-01-02T00:00:00"
        }
    ]
    
    # הגדרת תשובת ה-mock
    mock_api._make_request.return_value = (200, mock_products)
    
    # בדיקת מוצרים עם מלאי נמוך
    result = await reporting.get_low_stock_products(include_alerts=True)
    
    # בדיקות
    assert len(result) == 2
    
    # בדיקת מוצר עם מלאי נמוך
    low_stock_product = next(p for p in result if p["id"] == 1)
    assert low_stock_product["stock_quantity"] == 5
    assert low_stock_product["threshold_percentage"] == pytest.approx(25.0)
    assert "alert_level" in low_stock_product
    assert "alert_emoji" in low_stock_product
    assert "alert_message" in low_stock_product
    
    # בדיקת מוצר שאזל מהמלאי
    out_of_stock_product = next(p for p in result if p["id"] == 2)
    assert out_of_stock_product["stock_quantity"] == 0
    assert out_of_stock_product["alert_level"] == "critical"

@pytest.mark.asyncio
async def test_get_out_of_stock_products(reporting, mock_api):
    """בדיקת קבלת מוצרים שאזלו מהמלאי"""
    # הגדרת מוצרים לדוגמה
    mock_products = [
        {
            "id": 1,
            "name": "מוצר אזל 1",
            "sku": "SKU1",
            "manage_stock": True,
            "stock_quantity": 0,
            "date_modified": "2024-01-01T00:00:00",
            "backorders_allowed": False
        },
        {
            "id": 2,
            "name": "מוצר אזל 2",
            "sku": "SKU2",
            "manage_stock": True,
            "stock_quantity": 0,
            "date_modified": "2024-01-02T00:00:00",
            "backorders_allowed": True
        }
    ]
    
    # הגדרת תשובת ה-mock
    mock_api._make_request.return_value = (200, mock_products)
    
    # בדיקת מוצרים שאזלו מהמלאי
    result = await reporting.get_out_of_stock_products()
    
    # בדיקות
    assert len(result) == 2
    for product in result:
        assert "id" in product
        assert "name" in product
        assert "sku" in product
        assert "last_modified" in product
        assert "manage_stock" in product
        assert "stock_quantity" in product
        assert "backorders_allowed" in product

@pytest.mark.asyncio
async def test_get_inventory_report(reporting, mock_api):
    """בדיקת הפקת דוח מלאי"""
    # הגדרת מוצרים לדוגמה
    mock_products = [
        {
            "id": 1,
            "name": "מוצר 1",
            "manage_stock": True,
            "stock_quantity": 100,
            "price": "50.00",
            "stock_status": "instock"
        },
        {
            "id": 2,
            "name": "מוצר 2",
            "manage_stock": True,
            "stock_quantity": 5,
            "low_stock_amount": 20,
            "price": "100.00",
            "stock_status": "instock"
        },
        {
            "id": 3,
            "name": "מוצר 3",
            "manage_stock": True,
            "stock_quantity": 0,
            "price": "75.00",
            "stock_status": "outofstock"
        }
    ]
    
    # הגדרת תשובת ה-mock
    mock_api._make_request.return_value = (200, mock_products)
    
    # הפקת דוח מלאי
    result = await reporting.get_inventory_report()
    
    # בדיקות
    assert "generated_at" in result
    assert "summary" in result
    
    summary = result["summary"]
    assert summary["total_products"] == 3
    assert summary["products_with_stock_management"] == 3
    assert summary["total_stock_value"] == pytest.approx(5500.00)  # (100 * 50) + (5 * 100) + (0 * 75)
    assert summary["out_of_stock_count"] == 1
    assert summary["low_stock_count"] == 1
    assert summary["average_product_value"] == pytest.approx(5500.00 / 3)
    
    # בדיקת רשימות מוצרים
    assert "out_of_stock_products" in result
    assert "low_stock_products" in result
    assert len(result["out_of_stock_products"]) == 1
    assert len(result["low_stock_products"]) == 1

@pytest.mark.asyncio
async def test_get_inventory_report_with_category(reporting, mock_api):
    """בדיקת הפקת דוח מלאי עם סינון לפי קטגוריה"""
    # הגדרת קטגוריה לדוגמה
    mock_category = {
        "id": 1,
        "name": "קטגוריה לדוגמה",
        "slug": "test-category"
    }
    
    # הגדרת מוצרים לדוגמה
    mock_products = [
        {
            "id": 1,
            "name": "מוצר בקטגוריה",
            "manage_stock": True,
            "stock_quantity": 100,
            "price": "50.00"
        }
    ]
    
    # הגדרת תשובות ה-mock
    mock_api._make_request.side_effect = [
        (200, mock_category),  # תשובה לקבלת הקטגוריה
        (200, mock_products)  # תשובה לקבלת המוצרים
    ]
    
    # הפקת דוח מלאי עם קטגוריה
    result = await reporting.get_inventory_report(category_id=1)
    
    # בדיקות
    assert "category" in result
    category_info = result["category"]
    assert category_info["id"] == 1
    assert category_info["name"] == "קטגוריה לדוגמה"
    assert category_info["slug"] == "test-category"

@pytest.mark.asyncio
async def test_error_handling(reporting, mock_api):
    """בדיקת טיפול בשגיאות"""
    # הגדרת שגיאה בקבלת מוצרים
    mock_api._make_request.side_effect = Exception("API Error")
    
    # בדיקת טיפול בשגיאות בפונקציות שונות
    low_stock_result = await reporting.get_low_stock_products()
    assert len(low_stock_result) == 0
    
    out_of_stock_result = await reporting.get_out_of_stock_products()
    assert len(out_of_stock_result) == 0
    
    report_result = await reporting.get_inventory_report()
    assert "error" in report_result
    assert "generated_at" in report_result 