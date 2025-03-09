"""
בדיקות יחידה למודול customer_intent.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import sys

# הוספת נתיב הפרויקט ל-PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ייבוא מודולים מהפרויקט
try:
    from src.core.task_identification.intents.customer_intent import CustomerIntent
    from src.core.task_identification.models import IntentType, TaskParameters
    from src.tools.content.query_parser import extract_entities, extract_parameters
except ImportError as e:
    print(f"שגיאת ייבוא: {e}")
    print("משתמש במחלקות מוק במקום")
    
    # מחלקות מוק למקרה שהייבוא נכשל
    class IntentType:
        """מחלקת מוק ל-IntentType"""
        CUSTOMER = "customer"
        ORDER = "order"
        PRODUCT = "product"
        GENERAL = "general"
    
    class TaskParameters:
        """מחלקת מוק ל-TaskParameters"""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class CustomerIntent:
        """מחלקת מוק ל-CustomerIntent"""
        def __init__(self):
            self.intent_type = IntentType.CUSTOMER
            self.confidence_threshold = 0.7
            self.keywords = {
                "שירות לקוחות": 0.8,
                "תמיכה": 0.8,
                "עזרה": 0.7,
                "שאלה": 0.6,
                "בעיה": 0.7,
                "תלונה": 0.8
            }
        
        async def analyze(self, query):
            """מנתח את השאילתה ומחזיר פרמטרים של משימה"""
            return TaskParameters(
                intent_type=IntentType.CUSTOMER,
                confidence=0.8,
                customer_type="regular",
                issue_type="question",
                priority="medium"
            )
    
    def extract_entities(text):
        """פונקציית מוק ל-extract_entities"""
        return {"entities": []}
    
    def extract_parameters(text):
        """פונקציית מוק ל-extract_parameters"""
        return {"parameters": {}}


@pytest.fixture
def customer_intent():
    """יוצר מופע של CustomerIntent לבדיקות"""
    return CustomerIntent()


def test_init(customer_intent):
    """בודק שהאתחול של CustomerIntent מגדיר את הפרמטרים הנכונים"""
    assert customer_intent.intent_type == IntentType.CUSTOMER
    assert customer_intent.confidence_threshold == 0.7
    assert "שירות לקוחות" in customer_intent.keywords
    assert "תמיכה" in customer_intent.keywords


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על לקוח"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": ["john@example.com"],
        "phones": ["050-1234567"]
    }
    
    query = "מצא מידע על הלקוח ג'ון דו עם האימייל john@example.com והטלפון 050-1234567"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone == "050-1234567"


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info_partial(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים חלקיים של מידע על לקוח"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": [],
        "phones": []
    }
    
    query = "מצא מידע על הלקוח ג'ון דו"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email is None
    assert result.customer_phone is None


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info_email_only(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על לקוח לפי אימייל בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": [],
        "emails": ["john@example.com"],
        "phones": []
    }
    
    query = "מצא מידע על הלקוח עם האימייל john@example.com"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.customer_email == "john@example.com"
    assert result.customer_phone is None


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info_phone_only(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים של מידע על לקוח לפי טלפון בלבד"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": [],
        "emails": [],
        "phones": ["050-1234567"]
    }
    
    query = "מצא מידע על הלקוח עם הטלפון 050-1234567"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.customer_email is None
    assert result.customer_phone == "050-1234567"


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info_no_entities(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחזירה פרמטרים ריקים כאשר אין ישויות"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": [],
        "emails": [],
        "phones": []
    }
    
    query = "מצא מידע על לקוח"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.customer_email is None
    assert result.customer_phone is None


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_customer_info_multiple_entities(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters לוקחת את הישות הראשונה כאשר יש מספר ישויות"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe", "Jane Smith"],
        "emails": ["john@example.com", "jane@example.com"],
        "phones": ["050-1234567", "050-7654321"]
    }
    
    query = "מצא מידע על הלקוחות ג'ון דו וג'יין סמית'"
    task_type = "customer_info"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה - צריך לקחת את הישות הראשונה בכל קטגוריה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone == "050-1234567"


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_create_customer(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים ליצירת לקוח"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": ["john@example.com"],
        "phones": ["050-1234567"]
    }
    
    query = "צור לקוח חדש בשם ג'ון דו עם האימייל john@example.com והטלפון 050-1234567"
    task_type = "create_customer"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone == "050-1234567"


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_update_customer(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לעדכון לקוח"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": ["john@example.com"],
        "phones": ["050-1234567"]
    }
    
    query = "עדכן את הלקוח ג'ון דו עם האימייל john@example.com והטלפון החדש 050-1234567"
    task_type = "update_customer"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone == "050-1234567"


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_delete_customer(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים למחיקת לקוח"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": ["John Doe"],
        "emails": ["john@example.com"],
        "phones": []
    }
    
    query = "מחק את הלקוח ג'ון דו עם האימייל john@example.com"
    task_type = "delete_customer"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה
    assert isinstance(result, TaskParameters)
    assert result.customer_name == "John Doe"
    assert result.customer_email == "john@example.com"
    assert result.customer_phone is None


@patch("src.core.task_identification.intents.customer_intent.extract_entities")
def test_extract_parameters_list_customers(mock_extract_entities, customer_intent):
    """בודק שהפונקציה extract_parameters מחלצת פרמטרים לרשימת לקוחות"""
    # הגדרת התנהגות המוק
    mock_extract_entities.return_value = {
        "names": [],
        "emails": [],
        "phones": []
    }
    
    query = "הצג את רשימת הלקוחות"
    task_type = "list_customers"
    
    result = customer_intent.extract_parameters(query, task_type)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_extract_entities.assert_called_once_with(query)
    
    # בדיקת התוצאה - אין פרמטרים ספציפיים לרשימת לקוחות
    assert isinstance(result, TaskParameters)
    assert result.customer_name is None
    assert result.customer_email is None
    assert result.customer_phone is None


def test_get_task_types(customer_intent):
    """בודק שהפונקציה get_task_types מחזירה את סוגי המשימות הנכונים"""
    task_types = customer_intent.get_task_types()
    
    # בדיקת התוצאה
    assert isinstance(task_types, list)
    assert "customer_info" in task_types
    assert "create_customer" in task_types
    assert "update_customer" in task_types
    assert "delete_customer" in task_types
    assert "list_customers" in task_types


def test_get_examples(customer_intent):
    """בודק שהפונקציה get_examples מחזירה דוגמאות לכל סוג משימה"""
    examples = customer_intent.get_examples()
    
    # בדיקת התוצאה
    assert isinstance(examples, dict)
    assert "customer_info" in examples
    assert "create_customer" in examples
    assert "update_customer" in examples
    assert "delete_customer" in examples
    assert "list_customers" in examples
    
    # בדיקה שיש דוגמאות לכל סוג משימה
    for task_type, task_examples in examples.items():
        assert isinstance(task_examples, list)
        assert len(task_examples) > 0


def test_get_description(customer_intent):
    """בודק שהפונקציה get_description מחזירה תיאור לכל סוג משימה"""
    descriptions = customer_intent.get_description()
    
    # בדיקת התוצאה
    assert isinstance(descriptions, dict)
    assert "customer_info" in descriptions
    assert "create_customer" in descriptions
    assert "update_customer" in descriptions
    assert "delete_customer" in descriptions
    assert "list_customers" in descriptions
    
    # בדיקה שיש תיאור לכל סוג משימה
    for task_type, description in descriptions.items():
        assert isinstance(description, str)
        assert len(description) > 0 