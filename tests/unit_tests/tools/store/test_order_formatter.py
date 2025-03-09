"""
בדיקות יחידה עבור מפרמט ההזמנות (order_formatter)
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime

from src.tools.store.formatters.order_formatter import (
    format_order_for_display,
    format_orders_for_display,
    format_order_status,
    format_order_date,
    format_order_items,
    format_order_customer,
    format_order_shipping,
    format_order_billing,
    format_order_payment,
    format_order_totals
)


def test_format_order_status():
    """בדיקת פירמוט סטטוס הזמנה"""
    # מקרה 1: סטטוס מוכר
    order = {"status": "processing"}
    result = format_order_status(order)
    assert result == "סטטוס: בטיפול"
    
    # מקרה 2: סטטוס מוכר אחר
    order = {"status": "completed"}
    result = format_order_status(order)
    assert result == "סטטוס: הושלמה"
    
    # מקרה 3: סטטוס לא מוכר
    order = {"status": "unknown_status"}
    result = format_order_status(order)
    assert result == "סטטוס: unknown_status"
    
    # מקרה 4: ללא סטטוס
    order = {}
    result = format_order_status(order)
    assert result == "סטטוס: לא ידוע"


def test_format_order_date():
    """בדיקת פירמוט תאריך הזמנה"""
    # מקרה 1: תאריך תקין
    order = {"date_created": "2023-05-15T10:30:45"}
    result = format_order_date(order)
    assert "תאריך: 15/05/2023" in result
    assert "10:30" in result
    
    # מקרה 2: תאריך בפורמט אחר
    order = {"date_created": "2023-05-15"}
    result = format_order_date(order)
    assert "תאריך: 15/05/2023" in result
    
    # מקרה 3: ללא תאריך
    order = {}
    result = format_order_date(order)
    assert result == "תאריך: לא ידוע"
    
    # מקרה 4: תאריך לא תקין
    order = {"date_created": "invalid-date"}
    result = format_order_date(order)
    assert result == "תאריך: לא ידוע"


def test_format_order_items():
    """בדיקת פירמוט פריטי הזמנה"""
    # מקרה 1: הזמנה עם מספר פריטים
    order = {
        "line_items": [
            {"name": "מוצר 1", "quantity": 2, "price": 100, "total": "200.00"},
            {"name": "מוצר 2", "quantity": 1, "price": 50, "total": "50.00"}
        ]
    }
    result = format_order_items(order)
    assert "פריטים:" in result
    assert "2 × מוצר 1 - ₪200.00" in result
    assert "1 × מוצר 2 - ₪50.00" in result
    assert "סה\"כ פריטים: 3" in result
    
    # מקרה 2: הזמנה עם פריט אחד
    order = {
        "line_items": [
            {"name": "מוצר 1", "quantity": 1, "price": 100, "total": "100.00"}
        ]
    }
    result = format_order_items(order)
    assert "פריטים:" in result
    assert "1 × מוצר 1 - ₪100.00" in result
    assert "סה\"כ פריטים: 1" in result
    
    # מקרה 3: הזמנה ללא פריטים
    order = {"line_items": []}
    result = format_order_items(order)
    assert result == "פריטים: אין פריטים"
    
    # מקרה 4: הזמנה ללא שדה פריטים
    order = {}
    result = format_order_items(order)
    assert result == "פריטים: אין פריטים"


def test_format_order_customer():
    """בדיקת פירמוט פרטי לקוח"""
    # מקרה 1: לקוח עם כל הפרטים
    order = {
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "email": "israel@example.com",
            "phone": "0501234567"
        }
    }
    result = format_order_customer(order)
    assert "לקוח: ישראל ישראלי" in result
    assert "אימייל: israel@example.com" in result
    assert "טלפון: 0501234567" in result
    
    # מקרה 2: לקוח ללא טלפון
    order = {
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "email": "israel@example.com",
            "phone": ""
        }
    }
    result = format_order_customer(order)
    assert "לקוח: ישראל ישראלי" in result
    assert "אימייל: israel@example.com" in result
    assert "טלפון: לא צוין" in result
    
    # מקרה 3: לקוח ללא פרטי חיוב
    order = {}
    result = format_order_customer(order)
    assert result == "לקוח: לא ידוע"


def test_format_order_shipping():
    """בדיקת פירמוט פרטי משלוח"""
    # מקרה 1: משלוח עם כל הפרטים
    order = {
        "shipping": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "address_1": "רחוב הרצל 1",
            "address_2": "דירה 5",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6120101",
            "country": "IL"
        },
        "shipping_lines": [
            {"method_title": "משלוח רגיל", "total": "20.00"}
        ]
    }
    result = format_order_shipping(order)
    assert "כתובת למשלוח:" in result
    assert "ישראל ישראלי" in result
    assert "רחוב הרצל 1, דירה 5" in result
    assert "תל אביב, TA, 6120101" in result
    assert "IL" in result
    assert "שיטת משלוח: משלוח רגיל (₪20.00)" in result
    
    # מקרה 2: משלוח ללא כתובת 2
    order = {
        "shipping": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "address_1": "רחוב הרצל 1",
            "address_2": "",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6120101",
            "country": "IL"
        },
        "shipping_lines": [
            {"method_title": "משלוח רגיל", "total": "20.00"}
        ]
    }
    result = format_order_shipping(order)
    assert "רחוב הרצל 1" in result
    assert "דירה" not in result
    
    # מקרה 3: ללא פרטי משלוח
    order = {}
    result = format_order_shipping(order)
    assert result == "משלוח: לא צוין"
    
    # מקרה 4: משלוח ללא עלות
    order = {
        "shipping": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "address_1": "רחוב הרצל 1",
            "city": "תל אביב"
        },
        "shipping_lines": [
            {"method_title": "איסוף עצמי", "total": "0.00"}
        ]
    }
    result = format_order_shipping(order)
    assert "שיטת משלוח: איסוף עצמי (ללא עלות)" in result


def test_format_order_billing():
    """בדיקת פירמוט פרטי חיוב"""
    # מקרה 1: חיוב עם כל הפרטים
    order = {
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "company": "חברה בע\"מ",
            "address_1": "רחוב הרצל 1",
            "address_2": "דירה 5",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6120101",
            "country": "IL",
            "email": "israel@example.com",
            "phone": "0501234567"
        }
    }
    result = format_order_billing(order)
    assert "כתובת לחיוב:" in result
    assert "ישראל ישראלי" in result
    assert "חברה בע\"מ" in result
    assert "רחוב הרצל 1, דירה 5" in result
    assert "תל אביב, TA, 6120101" in result
    assert "IL" in result
    assert "israel@example.com" in result
    assert "0501234567" in result
    
    # מקרה 2: חיוב ללא חברה וכתובת 2
    order = {
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "company": "",
            "address_1": "רחוב הרצל 1",
            "address_2": "",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6120101",
            "country": "IL",
            "email": "israel@example.com",
            "phone": "0501234567"
        }
    }
    result = format_order_billing(order)
    assert "חברה" not in result
    assert "דירה" not in result
    
    # מקרה 3: ללא פרטי חיוב
    order = {}
    result = format_order_billing(order)
    assert result == "חיוב: לא צוין"


def test_format_order_payment():
    """בדיקת פירמוט פרטי תשלום"""
    # מקרה 1: תשלום עם כל הפרטים
    order = {
        "payment_method": "credit_card",
        "payment_method_title": "כרטיס אשראי",
        "transaction_id": "txn_123456"
    }
    result = format_order_payment(order)
    assert "אמצעי תשלום: כרטיס אשראי" in result
    assert "מזהה עסקה: txn_123456" in result
    
    # מקרה 2: תשלום ללא מזהה עסקה
    order = {
        "payment_method": "cod",
        "payment_method_title": "תשלום במזומן בעת האספקה",
        "transaction_id": ""
    }
    result = format_order_payment(order)
    assert "אמצעי תשלום: תשלום במזומן בעת האספקה" in result
    assert "מזהה עסקה" not in result
    
    # מקרה 3: ללא פרטי תשלום
    order = {}
    result = format_order_payment(order)
    assert result == "תשלום: לא צוין"


def test_format_order_totals():
    """בדיקת פירמוט סיכום הזמנה"""
    # מקרה 1: הזמנה עם כל הפרטים
    order = {
        "total": "150.00",
        "subtotal": "120.00",
        "total_tax": "10.00",
        "shipping_total": "20.00",
        "discount_total": "0.00"
    }
    result = format_order_totals(order)
    assert "סיכום הזמנה:" in result
    assert "סכום ביניים: ₪120.00" in result
    assert "משלוח: ₪20.00" in result
    assert "מע\"מ: ₪10.00" in result
    assert "הנחה: ₪0.00" in result
    assert "סה\"כ לתשלום: ₪150.00" in result
    
    # מקרה 2: הזמנה עם הנחה
    order = {
        "total": "130.00",
        "subtotal": "120.00",
        "total_tax": "10.00",
        "shipping_total": "20.00",
        "discount_total": "20.00"
    }
    result = format_order_totals(order)
    assert "הנחה: ₪20.00" in result
    assert "סה\"כ לתשלום: ₪130.00" in result
    
    # מקרה 3: ללא פרטי סיכום
    order = {}
    result = format_order_totals(order)
    assert result == "סיכום הזמנה: לא צוין"


def test_format_order_for_display():
    """בדיקת פירמוט הזמנה שלמה להצגה"""
    # יצירת הזמנה לדוגמה
    order = {
        "id": 123,
        "status": "processing",
        "date_created": "2023-05-15T10:30:45",
        "total": "150.00"
    }
    
    # מוק לפונקציות הפירמוט
    with patch('src.tools.store.formatters.order_formatter.format_order_status', return_value="סטטוס: בטיפול") as mock_status, \
         patch('src.tools.store.formatters.order_formatter.format_order_date', return_value="תאריך: 15/05/2023 10:30") as mock_date, \
         patch('src.tools.store.formatters.order_formatter.format_order_items', return_value="פריטים: 2 פריטים") as mock_items, \
         patch('src.tools.store.formatters.order_formatter.format_order_customer', return_value="לקוח: ישראל ישראלי") as mock_customer, \
         patch('src.tools.store.formatters.order_formatter.format_order_shipping', return_value="משלוח: כתובת למשלוח") as mock_shipping, \
         patch('src.tools.store.formatters.order_formatter.format_order_billing', return_value="חיוב: כתובת לחיוב") as mock_billing, \
         patch('src.tools.store.formatters.order_formatter.format_order_payment', return_value="תשלום: כרטיס אשראי") as mock_payment, \
         patch('src.tools.store.formatters.order_formatter.format_order_totals', return_value="סיכום הזמנה: ₪150.00") as mock_totals:
        
        result = format_order_for_display(order)
        
        # וידוא שכל פונקציות הפירמוט נקראו
        mock_status.assert_called_once_with(order)
        mock_date.assert_called_once_with(order)
        mock_items.assert_called_once_with(order)
        mock_customer.assert_called_once_with(order)
        mock_shipping.assert_called_once_with(order)
        mock_billing.assert_called_once_with(order)
        mock_payment.assert_called_once_with(order)
        mock_totals.assert_called_once_with(order)
        
        # וידוא שהפלט מכיל את כל המידע הנדרש
        assert "הזמנה #123" in result
        assert "סטטוס: בטיפול" in result
        assert "תאריך: 15/05/2023 10:30" in result
        assert "פריטים: 2 פריטים" in result
        assert "לקוח: ישראל ישראלי" in result
        assert "משלוח: כתובת למשלוח" in result
        assert "חיוב: כתובת לחיוב" in result
        assert "תשלום: כרטיס אשראי" in result
        assert "סיכום הזמנה: ₪150.00" in result


def test_format_orders_for_display():
    """בדיקת פירמוט רשימת הזמנות להצגה"""
    # יצירת רשימת הזמנות לדוגמה
    orders = [
        {"id": 1, "status": "processing", "total": "100.00"},
        {"id": 2, "status": "completed", "total": "200.00"},
        {"id": 3, "status": "pending", "total": "300.00"}
    ]
    
    # מוק לפונקציית format_order_for_display
    with patch('src.tools.store.formatters.order_formatter.format_order_for_display') as mock_format:
        mock_format.side_effect = [
            "פירמוט הזמנה 1",
            "פירמוט הזמנה 2",
            "פירמוט הזמנה 3"
        ]
        
        result = format_orders_for_display(orders)
        
        # וידוא שהפונקציה נקראה עבור כל הזמנה
        assert mock_format.call_count == 3
        
        # וידוא שהפלט מכיל את כל ההזמנות
        assert "נמצאו 3 הזמנות:" in result
        assert "1. פירמוט הזמנה 1" in result
        assert "2. פירמוט הזמנה 2" in result
        assert "3. פירמוט הזמנה 3" in result


def test_format_orders_for_display_empty():
    """בדיקת פירמוט רשימת הזמנות ריקה"""
    # רשימת הזמנות ריקה
    orders = []
    
    result = format_orders_for_display(orders)
    
    # וידוא שהפלט מציין שלא נמצאו הזמנות
    assert result == "לא נמצאו הזמנות."


def test_format_orders_for_display_single():
    """בדיקת פירמוט רשימה עם הזמנה אחת"""
    # רשימה עם הזמנה אחת
    orders = [{"id": 1, "status": "processing", "total": "100.00"}]
    
    # מוק לפונקציית format_order_for_display
    with patch('src.tools.store.formatters.order_formatter.format_order_for_display', return_value="פירמוט הזמנה יחידה"):
        result = format_orders_for_display(orders)
        
        # וידוא שהפלט מציין שנמצאה הזמנה אחת
        assert "נמצאה הזמנה אחת:" in result
        assert "1. פירמוט הזמנה יחידה" in result 