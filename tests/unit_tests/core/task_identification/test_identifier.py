"""
בדיקות יחידה למודול identifier.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from src.core.task_identification.identifier import TaskIdentifier
from src.core.task_identification.models import IntentType, TaskParameters, IdentifiedTask
from src.core.model_manager import ModelManager
from src.core.task_identification.intents.customer_intent import CustomerIntent
from src.core.task_identification.intents.product_intent import ProductIntent
from src.core.task_identification.intents.order_intent import OrderIntent


@pytest.fixture
def mock_model_manager():
    """יוצר מוק של ModelManager"""
    mock_manager = MagicMock(spec=ModelManager)
    mock_manager.generate_response = AsyncMock()
    return mock_manager


@pytest.fixture
def task_identifier(mock_model_manager):
    """יוצר מופע של TaskIdentifier עם ModelManager מדומה"""
    identifier = TaskIdentifier(model_manager=mock_manager)
    return identifier


def test_init(mock_model_manager):
    """בודק שהאתחול של TaskIdentifier מגדיר את הפרמטרים הנכונים"""
    identifier = TaskIdentifier(model_manager=mock_model_manager)
    assert identifier.model_manager is mock_model_manager
    assert len(identifier.intents) > 0
    
    # בדיקה שכל סוגי ה-intents נטענו
    intent_types = [intent.intent_type for intent in identifier.intents]
    assert IntentType.CUSTOMER in intent_types
    assert IntentType.PRODUCT in intent_types
    assert IntentType.ORDER in intent_types


def test_get_intent_by_type(task_identifier):
    """בודק שהפונקציה _get_intent_by_type מחזירה את ה-intent הנכון לפי סוג"""
    customer_intent = task_identifier._get_intent_by_type(IntentType.CUSTOMER)
    assert isinstance(customer_intent, CustomerIntent)
    
    product_intent = task_identifier._get_intent_by_type(IntentType.PRODUCT)
    assert isinstance(product_intent, ProductIntent)
    
    order_intent = task_identifier._get_intent_by_type(IntentType.ORDER)
    assert isinstance(order_intent, OrderIntent)


def test_get_intent_by_type_not_found(task_identifier):
    """בודק שהפונקציה _get_intent_by_type מחזירה None כאשר סוג ה-intent לא נמצא"""
    # יצירת סוג intent שלא קיים
    non_existent_type = MagicMock()
    non_existent_type.name = "NON_EXISTENT"
    
    result = task_identifier._get_intent_by_type(non_existent_type)
    assert result is None


def test_get_intent_by_name(task_identifier):
    """בודק שהפונקציה _get_intent_by_name מחזירה את ה-intent הנכון לפי שם"""
    customer_intent = task_identifier._get_intent_by_name("customer")
    assert isinstance(customer_intent, CustomerIntent)
    
    product_intent = task_identifier._get_intent_by_name("product")
    assert isinstance(product_intent, ProductIntent)
    
    order_intent = task_identifier._get_intent_by_name("order")
    assert isinstance(order_intent, OrderIntent)


def test_get_intent_by_name_not_found(task_identifier):
    """בודק שהפונקציה _get_intent_by_name מחזירה None כאשר שם ה-intent לא נמצא"""
    result = task_identifier._get_intent_by_name("non_existent_intent")
    assert result is None


def test_get_all_task_types(task_identifier):
    """בודק שהפונקציה _get_all_task_types מחזירה את כל סוגי המשימות מכל ה-intents"""
    task_types = task_identifier._get_all_task_types()
    
    # בדיקה שהפונקציה מחזירה מילון
    assert isinstance(task_types, dict)
    
    # בדיקה שהמילון מכיל את כל סוגי ה-intents
    assert "customer" in task_types
    assert "product" in task_types
    assert "order" in task_types
    
    # בדיקה שכל intent מכיל את סוגי המשימות שלו
    assert "customer_info" in task_types["customer"]
    assert "product_info" in task_types["product"]
    assert "order_info" in task_types["order"]


def test_get_all_examples(task_identifier):
    """בודק שהפונקציה _get_all_examples מחזירה את כל הדוגמאות מכל ה-intents"""
    examples = task_identifier._get_all_examples()
    
    # בדיקה שהפונקציה מחזירה מילון
    assert isinstance(examples, dict)
    
    # בדיקה שהמילון מכיל את כל סוגי ה-intents
    assert "customer" in examples
    assert "product" in examples
    assert "order" in examples
    
    # בדיקה שכל intent מכיל את הדוגמאות שלו
    assert "customer_info" in examples["customer"]
    assert "product_info" in examples["product"]
    assert "order_info" in examples["order"]
    
    # בדיקה שהדוגמאות הן רשימות לא ריקות
    assert isinstance(examples["customer"]["customer_info"], list)
    assert len(examples["customer"]["customer_info"]) > 0


def test_get_all_descriptions(task_identifier):
    """בודק שהפונקציה _get_all_descriptions מחזירה את כל התיאורים מכל ה-intents"""
    descriptions = task_identifier._get_all_descriptions()
    
    # בדיקה שהפונקציה מחזירה מילון
    assert isinstance(descriptions, dict)
    
    # בדיקה שהמילון מכיל את כל סוגי ה-intents
    assert "customer" in descriptions
    assert "product" in descriptions
    assert "order" in descriptions
    
    # בדיקה שכל intent מכיל את התיאורים שלו
    assert "customer_info" in descriptions["customer"]
    assert "product_info" in descriptions["product"]
    assert "order_info" in descriptions["order"]
    
    # בדיקה שהתיאורים הם מחרוזות לא ריקות
    assert isinstance(descriptions["customer"]["customer_info"], str)
    assert len(descriptions["customer"]["customer_info"]) > 0


def test_prepare_prompt(task_identifier):
    """בודק שהפונקציה _prepare_prompt מכינה את הפרומפט הנכון לזיהוי משימה"""
    query = "מצא מידע על הלקוח ג'ון דו"
    
    prompt = task_identifier._prepare_prompt(query)
    
    # בדיקה שהפרומפט מכיל את השאילתה
    assert query in prompt
    
    # בדיקה שהפרומפט מכיל את המבנה הנדרש
    assert "intent" in prompt
    assert "task_type" in prompt
    assert "JSON" in prompt


@patch.object(TaskIdentifier, "_prepare_prompt")
@pytest.mark.asyncio
async def test_identify_task(mock_prepare_prompt, task_identifier, mock_model_manager):
    """בודק שהפונקציה identify_task מזהה משימה בצורה נכונה"""
    # הגדרת התנהגות המוקים
    mock_prepare_prompt.return_value = "מוק פרומפט"
    mock_model_manager.generate_response.return_value = json.dumps({
        "intent": "customer",
        "task_type": "customer_info"
    })
    
    query = "מצא מידע על הלקוח ג'ון דו"
    
    result = await task_identifier.identify_task(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_prepare_prompt.assert_called_once_with(query)
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה
    assert isinstance(result, IdentifiedTask)
    assert result.intent_name == "customer"
    assert result.task_type == "customer_info"


@patch.object(TaskIdentifier, "_prepare_prompt")
@pytest.mark.asyncio
async def test_identify_task_invalid_json(mock_prepare_prompt, task_identifier, mock_model_manager):
    """בודק שהפונקציה identify_task מטפלת ב-JSON לא תקין"""
    # הגדרת התנהגות המוקים
    mock_prepare_prompt.return_value = "מוק פרומפט"
    mock_model_manager.generate_response.return_value = "לא JSON תקין"
    
    query = "מצא מידע על הלקוח ג'ון דו"
    
    result = await task_identifier.identify_task(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_prepare_prompt.assert_called_once_with(query)
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות None במקרה של שגיאה
    assert result is None


@patch.object(TaskIdentifier, "_prepare_prompt")
@pytest.mark.asyncio
async def test_identify_task_missing_fields(mock_prepare_prompt, task_identifier, mock_model_manager):
    """בודק שהפונקציה identify_task מטפלת ב-JSON חסר שדות"""
    # הגדרת התנהגות המוקים
    mock_prepare_prompt.return_value = "מוק פרומפט"
    mock_model_manager.generate_response.return_value = json.dumps({
        "intent": "customer"
        # חסר שדה task_type
    })
    
    query = "מצא מידע על הלקוח ג'ון דו"
    
    result = await task_identifier.identify_task(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_prepare_prompt.assert_called_once_with(query)
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות None במקרה של שדות חסרים
    assert result is None


@patch.object(TaskIdentifier, "_prepare_prompt")
@pytest.mark.asyncio
async def test_identify_task_invalid_intent(mock_prepare_prompt, task_identifier, mock_model_manager):
    """בודק שהפונקציה identify_task מטפלת ב-intent לא תקין"""
    # הגדרת התנהגות המוקים
    mock_prepare_prompt.return_value = "מוק פרומפט"
    mock_model_manager.generate_response.return_value = json.dumps({
        "intent": "non_existent_intent",
        "task_type": "some_task"
    })
    
    query = "מצא מידע על הלקוח ג'ון דו"
    
    result = await task_identifier.identify_task(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_prepare_prompt.assert_called_once_with(query)
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות None במקרה של intent לא תקין
    assert result is None


@patch.object(TaskIdentifier, "identify_task")
@pytest.mark.asyncio
async def test_extract_task_parameters(mock_identify_task, task_identifier):
    """בודק שהפונקציה extract_task_parameters מחלצת פרמטרים בצורה נכונה"""
    # הגדרת התנהגות המוק
    identified_task = IdentifiedTask(intent_name="customer", task_type="customer_info")
    mock_identify_task.return_value = identified_task
    
    # מוק לפונקציית extract_parameters של CustomerIntent
    customer_intent = task_identifier._get_intent_by_name("customer")
    original_extract_parameters = customer_intent.extract_parameters
    customer_intent.extract_parameters = MagicMock()
    customer_intent.extract_parameters.return_value = TaskParameters(customer_name="John Doe")
    
    query = "מצא מידע על הלקוח ג'ון דו"
    
    result = await task_identifier.extract_task_parameters(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_identify_task.assert_called_once_with(query)
    customer_intent.extract_parameters.assert_called_once_with(query, "customer_info")
    
    # בדיקת התוצאה
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == identified_task
    assert isinstance(result[1], TaskParameters)
    assert result[1].customer_name == "John Doe"
    
    # החזרת הפונקציה המקורית
    customer_intent.extract_parameters = original_extract_parameters


@patch.object(TaskIdentifier, "identify_task")
@pytest.mark.asyncio
async def test_extract_task_parameters_identification_failed(mock_identify_task, task_identifier):
    """בודק שהפונקציה extract_task_parameters מטפלת במקרה שזיהוי המשימה נכשל"""
    # הגדרת התנהגות המוק
    mock_identify_task.return_value = None
    
    query = "שאילתה לא ברורה"
    
    result = await task_identifier.extract_task_parameters(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_identify_task.assert_called_once_with(query)
    
    # בדיקת התוצאה - צריכה להיות None במקרה של כישלון בזיהוי
    assert result is None


@patch.object(TaskIdentifier, "identify_task")
@pytest.mark.asyncio
async def test_extract_task_parameters_intent_not_found(mock_identify_task, task_identifier):
    """בודק שהפונקציה extract_task_parameters מטפלת במקרה שה-intent לא נמצא"""
    # הגדרת התנהגות המוק
    identified_task = IdentifiedTask(intent_name="non_existent_intent", task_type="some_task")
    mock_identify_task.return_value = identified_task
    
    query = "שאילתה עם intent לא קיים"
    
    result = await task_identifier.extract_task_parameters(query)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_identify_task.assert_called_once_with(query)
    
    # בדיקת התוצאה - צריכה להיות None במקרה של intent לא קיים
    assert result is None 