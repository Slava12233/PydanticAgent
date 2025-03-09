"""
בדיקות יחידה למודול product_intent.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from src.core.task_identification.intents.product_intent import ProductIntent
from src.core.task_identification.models import IntentType, TaskParameters
from src.tools.content.query_parser import extract_product_details, extract_numbers


@pytest.fixture
def product_intent():
    """יוצר מופע של ProductIntent לבדיקות"""
    return ProductIntent()


def test_init(product_intent):
    """בודק שהאתחול של ProductIntent מגדיר את הפרמטרים הנכונים"""
    assert product_intent.intent_type == IntentType.PRODUCT
    assert product_intent.intent_name == "product"
    assert product_intent.description == "Product related tasks"
    assert product_intent.examples is not None
    assert len(product_intent.examples) > 0


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_product_info(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על מוצר"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": "12345",
        "sku": "SHIRT-BLUE-M"
    }
    
    query = "מצא מידע על המוצר חולצה כחולה עם מזהה 12345"
    task_type = "product_info"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id == "12345"
    assert result.sku == "SHIRT-BLUE-M"


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_product_info_partial(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים חלקיים של מידע על מוצר"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": None,
        "sku": None
    }
    
    query = "מצא מידע על המוצר חולצה כחולה"
    task_type = "product_info"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id is None
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_product_info_id_only(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על מוצר לפי מזהה בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": None,
        "product_id": "12345",
        "sku": None
    }
    
    query = "מצא מידע על המוצר עם מזהה 12345"
    task_type = "product_info"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name is None
    assert result.product_id == "12345"
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_product_info_sku_only(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על מוצר לפי SKU בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": None,
        "product_id": None,
        "sku": "SHIRT-BLUE-M"
    }
    
    query = "מצא מידע על המוצר עם SKU SHIRT-BLUE-M"
    task_type = "product_info"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name is None
    assert result.product_id is None
    assert result.sku == "SHIRT-BLUE-M"


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_product_info_no_details(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחזירה פרמטרים ריקים כאשר אין פרטי מוצר"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": None,
        "product_id": None,
        "sku": None
    }
    
    query = "מצא מידע על מוצר"
    task_type = "product_info"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name is None
    assert result.product_id is None
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
@patch("src.core.task_identification.intents.product_intent.extract_numbers")
def test_extract_parameters_create_product(mock_extract_numbers, mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים ליצירת מוצר"""
    # הגדרת התנהגות המוקים
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": None,
        "sku": "SHIRT-BLUE-M"
    }
    mock_extract_numbers.return_value = ["99.90"]
    
    query = "צור מוצר חדש בשם חולצה כחולה עם SKU SHIRT-BLUE-M במחיר 99.90 ש\"ח"
    task_type = "create_product"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    mock_extract_numbers.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.sku == "SHIRT-BLUE-M"
    assert result.price == "99.90"


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
@patch("src.core.task_identification.intents.product_intent.extract_numbers")
def test_extract_parameters_create_product_no_price(mock_extract_numbers, mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים ליצירת מוצר ללא מחיר"""
    # הגדרת התנהגות המוקים
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": None,
        "sku": "SHIRT-BLUE-M"
    }
    mock_extract_numbers.return_value = []
    
    query = "צור מוצר חדש בשם חולצה כחולה עם SKU SHIRT-BLUE-M"
    task_type = "create_product"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    mock_extract_numbers.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.sku == "SHIRT-BLUE-M"
    assert result.price is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
@patch("src.core.task_identification.intents.product_intent.extract_numbers")
def test_extract_parameters_update_product(mock_extract_numbers, mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לעדכון מוצר"""
    # הגדרת התנהגות המוקים
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": "12345",
        "sku": "SHIRT-BLUE-M"
    }
    mock_extract_numbers.return_value = ["129.90"]
    
    query = "עדכן את המוצר חולצה כחולה עם מזהה 12345 למחיר 129.90 ש\"ח"
    task_type = "update_product"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    mock_extract_numbers.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id == "12345"
    assert result.sku == "SHIRT-BLUE-M"
    assert result.price == "129.90"


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_delete_product(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים למחיקת מוצר"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": "12345",
        "sku": None
    }
    
    query = "מחק את המוצר חולצה כחולה עם מזהה 12345"
    task_type = "delete_product"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id == "12345"
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_list_products(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת מוצרים"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": None,
        "product_id": None,
        "sku": None
    }
    
    query = "הצג את רשימת המוצרים"
    task_type = "list_products"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה - אין פרמטרים ספציפיים לרשימת מוצרים
    assert isinstance(result, TaskParameters)
    assert result.product_name is None
    assert result.product_id is None
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
def test_extract_parameters_list_products_with_category(mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת מוצרים עם קטגוריה"""
    # הגדרת התנהגות המוק
    mock_extract_product_details.return_value = {
        "product_name": "חולצות",
        "product_id": None,
        "sku": None
    }
    
    query = "הצג את רשימת המוצרים בקטגוריה חולצות"
    task_type = "list_products"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    
    # בדיקת התוצאה - שם המוצר משמש כקטגוריה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצות"
    assert result.product_id is None
    assert result.sku is None


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
@patch("src.core.task_identification.intents.product_intent.extract_numbers")
def test_extract_parameters_update_inventory(mock_extract_numbers, mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לעדכון מלאי"""
    # הגדרת התנהגות המוקים
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": "12345",
        "sku": "SHIRT-BLUE-M"
    }
    mock_extract_numbers.return_value = ["50"]
    
    query = "עדכן את המלאי של המוצר חולצה כחולה עם מזהה 12345 ל-50 יחידות"
    task_type = "update_inventory"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    mock_extract_numbers.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id == "12345"
    assert result.sku == "SHIRT-BLUE-M"
    assert result.quantity == "50"


@patch("src.core.task_identification.intents.product_intent.extract_product_details")
@patch("src.core.task_identification.intents.product_intent.extract_numbers")
def test_extract_parameters_update_inventory_no_quantity(mock_extract_numbers, mock_extract_product_details, product_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לעדכון מלאי ללא כמות"""
    # הגדרת התנהגות המוקים
    mock_extract_product_details.return_value = {
        "product_name": "חולצה כחולה",
        "product_id": "12345",
        "sku": "SHIRT-BLUE-M"
    }
    mock_extract_numbers.return_value = []
    
    query = "עדכן את המלאי של המוצר חולצה כחולה עם מזהה 12345"
    task_type = "update_inventory"
    
    result = product_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_product_details.assert_called_once_with(query)
    mock_extract_numbers.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.product_name == "חולצה כחולה"
    assert result.product_id == "12345"
    assert result.sku == "SHIRT-BLUE-M"
    assert result.quantity is None


def test_get_task_types(product_intent):
    """בודק שהפונקציה get_task_types מחזירה את סוגי המשימות הנכונים"""
    task_types = product_intent.get_task_types()
    
    # בדיקת התוצאה
    assert isinstance(task_types, list)
    assert "product_info" in task_types
    assert "create_product" in task_types
    assert "update_product" in task_types
    assert "delete_product" in task_types
    assert "list_products" in task_types
    assert "update_inventory" in task_types


def test_get_examples(product_intent):
    """בודק שהפונקציה get_examples מחזירה דוגמאות לכל סוג משימה"""
    examples = product_intent.get_examples()
    
    # בדיקת התוצאה
    assert isinstance(examples, dict)
    assert "product_info" in examples
    assert "create_product" in examples
    assert "update_product" in examples
    assert "delete_product" in examples
    assert "list_products" in examples
    assert "update_inventory" in examples
    
    # בדיקה שיש דוגמאות לכל סוג משימה
    for task_type, task_examples in examples.items():
        assert isinstance(task_examples, list)
        assert len(task_examples) > 0


def test_get_description(product_intent):
    """בודק שהפונקציה get_description מחזירה תיאור לכל סוג משימה"""
    descriptions = product_intent.get_description()
    
    # בדיקת התוצאה
    assert isinstance(descriptions, dict)
    assert "product_info" in descriptions
    assert "create_product" in descriptions
    assert "update_product" in descriptions
    assert "delete_product" in descriptions
    assert "list_products" in descriptions
    assert "update_inventory" in descriptions
    
    # בדיקה שיש תיאור לכל סוג משימה
    for task_type, description in descriptions.items():
        assert isinstance(description, str)
        assert len(description) > 0 