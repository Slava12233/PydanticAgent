"""
בדיקות יחידה עבור מפרמט המוצרים (product_formatter)
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.tools.store.formatters.product_formatter import (
    format_product_for_display,
    format_products_for_display,
    format_product_attributes,
    format_product_variations,
    format_product_categories,
    format_product_images,
    format_product_price
)


def test_format_product_price():
    """בדיקת פירמוט מחיר מוצר"""
    # מקרה 1: מחיר רגיל ומחיר מבצע
    product = {
        "regular_price": "100.00",
        "sale_price": "80.00"
    }
    result = format_product_price(product)
    assert result == "מחיר: ₪80.00 (במקום ₪100.00)"
    
    # מקרה 2: רק מחיר רגיל
    product = {
        "regular_price": "100.00",
        "sale_price": ""
    }
    result = format_product_price(product)
    assert result == "מחיר: ₪100.00"
    
    # מקרה 3: מחירים חסרים
    product = {}
    result = format_product_price(product)
    assert result == "מחיר: לא צוין"
    
    # מקרה 4: מחיר אפס
    product = {
        "regular_price": "0.00",
        "sale_price": ""
    }
    result = format_product_price(product)
    assert result == "מחיר: ₪0.00"


def test_format_product_images():
    """בדיקת פירמוט תמונות מוצר"""
    # מקרה 1: מוצר עם תמונות
    product = {
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "תמונה 1"},
            {"src": "https://example.com/image2.jpg", "alt": "תמונה 2"}
        ]
    }
    result = format_product_images(product)
    assert result == "תמונות: 2 תמונות"
    
    # מקרה 2: מוצר עם תמונה אחת
    product = {
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "תמונה 1"}
        ]
    }
    result = format_product_images(product)
    assert result == "תמונות: תמונה אחת"
    
    # מקרה 3: מוצר ללא תמונות
    product = {
        "images": []
    }
    result = format_product_images(product)
    assert result == "תמונות: אין תמונות"
    
    # מקרה 4: מוצר ללא שדה תמונות
    product = {}
    result = format_product_images(product)
    assert result == "תמונות: אין תמונות"


def test_format_product_categories():
    """בדיקת פירמוט קטגוריות מוצר"""
    # מקרה 1: מוצר עם קטגוריות
    product = {
        "categories": [
            {"name": "קטגוריה 1"},
            {"name": "קטגוריה 2"}
        ]
    }
    result = format_product_categories(product)
    assert result == "קטגוריות: קטגוריה 1, קטגוריה 2"
    
    # מקרה 2: מוצר עם קטגוריה אחת
    product = {
        "categories": [
            {"name": "קטגוריה 1"}
        ]
    }
    result = format_product_categories(product)
    assert result == "קטגוריות: קטגוריה 1"
    
    # מקרה 3: מוצר ללא קטגוריות
    product = {
        "categories": []
    }
    result = format_product_categories(product)
    assert result == "קטגוריות: לא צוינו"
    
    # מקרה 4: מוצר ללא שדה קטגוריות
    product = {}
    result = format_product_categories(product)
    assert result == "קטגוריות: לא צוינו"


def test_format_product_variations():
    """בדיקת פירמוט וריאציות מוצר"""
    # מקרה 1: מוצר עם וריאציות
    product = {
        "variations": [1, 2, 3]
    }
    result = format_product_variations(product)
    assert result == "וריאציות: 3 וריאציות"
    
    # מקרה 2: מוצר עם וריאציה אחת
    product = {
        "variations": [1]
    }
    result = format_product_variations(product)
    assert result == "וריאציות: וריאציה אחת"
    
    # מקרה 3: מוצר ללא וריאציות
    product = {
        "variations": []
    }
    result = format_product_variations(product)
    assert result == "וריאציות: אין וריאציות"
    
    # מקרה 4: מוצר ללא שדה וריאציות
    product = {}
    result = format_product_variations(product)
    assert result == "וריאציות: אין וריאציות"


def test_format_product_attributes():
    """בדיקת פירמוט תכונות מוצר"""
    # מקרה 1: מוצר עם תכונות
    product = {
        "attributes": [
            {"name": "צבע", "options": ["אדום", "כחול"]},
            {"name": "גודל", "options": ["S", "M", "L"]}
        ]
    }
    result = format_product_attributes(product)
    assert result == "תכונות:\n- צבע: אדום, כחול\n- גודל: S, M, L"
    
    # מקרה 2: מוצר עם תכונה אחת
    product = {
        "attributes": [
            {"name": "צבע", "options": ["אדום", "כחול"]}
        ]
    }
    result = format_product_attributes(product)
    assert result == "תכונות:\n- צבע: אדום, כחול"
    
    # מקרה 3: מוצר ללא תכונות
    product = {
        "attributes": []
    }
    result = format_product_attributes(product)
    assert result == "תכונות: אין תכונות"
    
    # מקרה 4: מוצר ללא שדה תכונות
    product = {}
    result = format_product_attributes(product)
    assert result == "תכונות: אין תכונות"


def test_format_product_for_display():
    """בדיקת פירמוט מוצר שלם להצגה"""
    # יצירת מוצר לדוגמה
    product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "description": "תיאור המוצר",
        "short_description": "תיאור קצר",
        "regular_price": "100.00",
        "sale_price": "80.00",
        "stock_quantity": 10,
        "stock_status": "instock",
        "categories": [
            {"name": "קטגוריה 1"},
            {"name": "קטגוריה 2"}
        ],
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "תמונה 1"}
        ],
        "attributes": [
            {"name": "צבע", "options": ["אדום", "כחול"]}
        ],
        "variations": [1, 2]
    }
    
    # מוק לפונקציות הפירמוט
    with patch('src.tools.store.formatters.product_formatter.format_product_price', return_value="מחיר: ₪80.00 (במקום ₪100.00)") as mock_price, \
         patch('src.tools.store.formatters.product_formatter.format_product_categories', return_value="קטגוריות: קטגוריה 1, קטגוריה 2") as mock_categories, \
         patch('src.tools.store.formatters.product_formatter.format_product_images', return_value="תמונות: תמונה אחת") as mock_images, \
         patch('src.tools.store.formatters.product_formatter.format_product_attributes', return_value="תכונות:\n- צבע: אדום, כחול") as mock_attributes, \
         patch('src.tools.store.formatters.product_formatter.format_product_variations', return_value="וריאציות: 2 וריאציות") as mock_variations:
        
        result = format_product_for_display(product)
        
        # וידוא שכל פונקציות הפירמוט נקראו
        mock_price.assert_called_once_with(product)
        mock_categories.assert_called_once_with(product)
        mock_images.assert_called_once_with(product)
        mock_attributes.assert_called_once_with(product)
        mock_variations.assert_called_once_with(product)
        
        # וידוא שהפלט מכיל את כל המידע הנדרש
        assert "מוצר לדוגמה (מק\"ט: 123)" in result
        assert "תיאור: תיאור המוצר" in result
        assert "מחיר: ₪80.00 (במקום ₪100.00)" in result
        assert "מלאי: 10 יחידות במלאי" in result
        assert "קטגוריות: קטגוריה 1, קטגוריה 2" in result
        assert "תמונות: תמונה אחת" in result
        assert "תכונות:\n- צבע: אדום, כחול" in result
        assert "וריאציות: 2 וריאציות" in result


def test_format_product_for_display_out_of_stock():
    """בדיקת פירמוט מוצר אזל מהמלאי"""
    # יצירת מוצר לדוגמה שאזל מהמלאי
    product = {
        "id": 123,
        "name": "מוצר לדוגמה",
        "description": "תיאור המוצר",
        "regular_price": "100.00",
        "stock_status": "outofstock"
    }
    
    # מוק לפונקציות הפירמוט
    with patch('src.tools.store.formatters.product_formatter.format_product_price') as mock_price, \
         patch('src.tools.store.formatters.product_formatter.format_product_categories') as mock_categories, \
         patch('src.tools.store.formatters.product_formatter.format_product_images') as mock_images, \
         patch('src.tools.store.formatters.product_formatter.format_product_attributes') as mock_attributes, \
         patch('src.tools.store.formatters.product_formatter.format_product_variations') as mock_variations:
        
        result = format_product_for_display(product)
        
        # וידוא שהפלט מציין שהמוצר אזל מהמלאי
        assert "מלאי: אזל מהמלאי" in result


def test_format_products_for_display():
    """בדיקת פירמוט רשימת מוצרים להצגה"""
    # יצירת רשימת מוצרים לדוגמה
    products = [
        {"id": 1, "name": "מוצר 1"},
        {"id": 2, "name": "מוצר 2"},
        {"id": 3, "name": "מוצר 3"}
    ]
    
    # מוק לפונקציית format_product_for_display
    with patch('src.tools.store.formatters.product_formatter.format_product_for_display') as mock_format:
        mock_format.side_effect = [
            "פירמוט מוצר 1",
            "פירמוט מוצר 2",
            "פירמוט מוצר 3"
        ]
        
        result = format_products_for_display(products)
        
        # וידוא שהפונקציה נקראה עבור כל מוצר
        assert mock_format.call_count == 3
        
        # וידוא שהפלט מכיל את כל המוצרים
        assert "נמצאו 3 מוצרים:" in result
        assert "1. פירמוט מוצר 1" in result
        assert "2. פירמוט מוצר 2" in result
        assert "3. פירמוט מוצר 3" in result


def test_format_products_for_display_empty():
    """בדיקת פירמוט רשימת מוצרים ריקה"""
    # רשימת מוצרים ריקה
    products = []
    
    result = format_products_for_display(products)
    
    # וידוא שהפלט מציין שלא נמצאו מוצרים
    assert result == "לא נמצאו מוצרים."


def test_format_products_for_display_single():
    """בדיקת פירמוט רשימה עם מוצר אחד"""
    # רשימה עם מוצר אחד
    products = [{"id": 1, "name": "מוצר יחיד"}]
    
    # מוק לפונקציית format_product_for_display
    with patch('src.tools.store.formatters.product_formatter.format_product_for_display', return_value="פירמוט מוצר יחיד"):
        result = format_products_for_display(products)
        
        # וידוא שהפלט מציין שנמצא מוצר אחד
        assert "נמצא מוצר אחד:" in result
        assert "1. פירמוט מוצר יחיד" in result 