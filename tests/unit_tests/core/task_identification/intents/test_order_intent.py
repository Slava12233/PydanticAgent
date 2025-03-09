"""
בדיקות יחידה למודול order_intent.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from src.core.task_identification.intents.order_intent import OrderIntent
from src.core.task_identification.models import IntentType, TaskParameters
from src.tools.content.query_parser import extract_order_details, extract_entities, extract_numbers, extract_dates


@pytest.fixture
def order_intent():
    """יוצר מופע של OrderIntent לבדיקות"""
    return OrderIntent()


def test_init(order_intent):
    """בודק שהאתחול של OrderIntent מגדיר את הפרמטרים הנכונים"""
    assert order_intent.intent_type == IntentType.ORDER
    assert order_intent.intent_name == "order"
    assert order_intent.description == "Order related tasks"
    assert order_intent.examples is not None
    assert len(order_intent.examples) > 0


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_order_info(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על הזמנה"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": "12345",
        "customer_name": "John Doe",
        "status": "processing"
    }
    
    query = "מצא מידע על הזמנה מספר 12345 של הלקוח ג'ון דו"
    task_type = "order_info"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id == "12345"
    assert result.customer_name == "John Doe"
    assert result.order_status == "processing"


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_order_info_partial(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים חלקיים של מידע על הזמנה"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": "12345",
        "customer_name": None,
        "status": None
    }
    
    query = "מצא מידע על הזמנה מספר 12345"
    task_type = "order_info"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id == "12345"
    assert result.customer_name is None
    assert result.order_status is None


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_order_info_customer_only(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על הזמנה לפי לקוח בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": "John Doe",
        "status": None
    }
    
    query = "מצא מידע על ההזמנות של הלקוח ג'ון דו"
    task_type = "order_info"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id is None
    assert result.customer_name == "John Doe"
    assert result.order_status is None


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_order_info_status_only(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על הזמנה לפי סטטוס בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": "processing"
    }
    
    query = "מצא מידע על הזמנות בסטטוס processing"
    task_type = "order_info"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id is None
    assert result.customer_name is None
    assert result.order_status == "processing"


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_order_info_no_details(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחזירה פרמטרים ריקים כאשר אין פרטי הזמנה"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": None
    }
    
    query = "מצא מידע על הזמנות"
    task_type = "order_info"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id is None
    assert result.customer_name is None
    assert result.order_status is None


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_entities")
def test_extract_parameters_create_order(mock_extract_entities, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים ליצירת הזמנה"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": None
    }
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": ["john@example.com"],
        "phones": ["050-1234567"]
    }
    
    query = "צור הזמנה חדשה עבור הלקוח ג'ון דו עם האימייל john@example.com והטלפון 050-1234567"
    task_type = "create_order"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone == "050-1234567"


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_entities")
def test_extract_parameters_create_order_partial(mock_extract_entities, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים חלקיים ליצירת הזמנה"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": None
    }
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": [],
        "phones": []
    }
    
    query = "צור הזמנה חדשה עבור הלקוח ג'ון דו"
    task_type = "create_order"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email is None
    assert result.customer_phone is None


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_update_order(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לעדכון הזמנה"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": "12345",
        "customer_name": "John Doe",
        "status": "completed"
    }
    
    query = "עדכן את הזמנה מספר 12345 של הלקוח ג'ון דו לסטטוס completed"
    task_type = "update_order"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id == "12345"
    assert result.customer_name == "John Doe"
    assert result.order_status == "completed"


@patch("src.tools.content.query_parser.extract_order_details")
def test_extract_parameters_cancel_order(mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לביטול הזמנה"""
    # הגדרת התנהגות המוק
    mock_extract_order_details.return_value = {
        "order_id": "12345",
        "customer_name": "John Doe",
        "status": None
    }
    
    query = "בטל את הזמנה מספר 12345 של הלקוח ג'ון דו"
    task_type = "cancel_order"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.order_id == "12345"
    assert result.customer_name == "John Doe"
    assert result.order_status is None


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_dates")
def test_extract_parameters_list_orders(mock_extract_dates, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת הזמנות"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": "John Doe",
        "status": "processing"
    }
    mock_extract_dates.return_value = ["2023-01-01"]
    
    query = "הצג את רשימת ההזמנות של הלקוח ג'ון דו בסטטוס processing מתאריך 01/01/2023"
    task_type = "list_orders"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_dates.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.order_status == "processing"
    assert result.date == "2023-01-01"


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_dates")
def test_extract_parameters_list_orders_no_date(mock_extract_dates, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת הזמנות ללא תאריך"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": "John Doe",
        "status": "processing"
    }
    mock_extract_dates.return_value = []
    
    query = "הצג את רשימת ההזמנות של הלקוח ג'ון דו בסטטוס processing"
    task_type = "list_orders"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_dates.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.order_status == "processing"
    assert result.date is None


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_dates")
def test_extract_parameters_list_orders_date_only(mock_extract_dates, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת הזמנות לפי תאריך בלבד"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": None
    }
    mock_extract_dates.return_value = ["2023-01-01"]
    
    query = "הצג את רשימת ההזמנות מתאריך 01/01/2023"
    task_type = "list_orders"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_dates.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.order_status is None
    assert result.date == "2023-01-01"


@patch("src.tools.content.query_parser.extract_order_details")
@patch("src.tools.content.query_parser.extract_dates")
def test_extract_parameters_list_orders_empty(mock_extract_dates, mock_extract_order_details, order_intent):
    """בודק שהפונקציה extract_parameters מחזירה פרמטרים ריקים לרשימת הזמנות ללא פרטים"""
    # הגדרת התנהגות המוקים
    mock_extract_order_details.return_value = {
        "order_id": None,
        "customer_name": None,
        "status": None
    }
    mock_extract_dates.return_value = []
    
    query = "הצג את רשימת ההזמנות"
    task_type = "list_orders"
    
    result = order_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_extract_order_details.assert_called_once_with(query)
    mock_extract_dates.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.order_status is None
    assert result.date is None


def test_get_task_types(order_intent):
    """בודק שהפונקציה get_task_types מחזירה את סוגי המשימות הנכונים"""
    task_types = order_intent.get_task_types()
    
    # בדיקת התוצאה
    assert isinstance(task_types, list)
    assert "order_info" in task_types
    assert "create_order" in task_types
    assert "update_order" in task_types
    assert "cancel_order" in task_types
    assert "list_orders" in task_types


def test_get_examples(order_intent):
    """בודק שהפונקציה get_examples מחזירה דוגמאות לכל סוג משימה"""
    examples = order_intent.get_examples()
    
    # בדיקת התוצאה
    assert isinstance(examples, dict)
    assert "order_info" in examples
    assert "create_order" in examples
    assert "update_order" in examples
    assert "cancel_order" in examples
    assert "list_orders" in examples
    
    # בדיקה שיש דוגמאות לכל סוג משימה
    for task_type, task_examples in examples.items():
        assert isinstance(task_examples, list)
        assert len(task_examples) > 0


def test_get_description(order_intent):
    """בודק שהפונקציה get_description מחזירה תיאור לכל סוג משימה"""
    descriptions = order_intent.get_description()
    
    # בדיקת התוצאה
    assert isinstance(descriptions, dict)
    assert "order_info" in descriptions
    assert "create_order" in descriptions
    assert "update_order" in descriptions
    assert "cancel_order" in descriptions
    assert "list_orders" in descriptions
    
    # בדיקה שיש תיאור לכל סוג משימה
    for task_type, description in descriptions.items():
        assert isinstance(description, str)
        assert len(description) > 0 