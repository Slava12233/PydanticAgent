"""
בדיקות יחידה למודול learning_manager.py
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from src.tools.content.learning_manager import LearningManager
from src.database.database import Database
from src.core.model_manager import ModelManager


@pytest.fixture
def mock_database():
    """יוצר מוק של Database"""
    mock_db = MagicMock(spec=Database)
    mock_db.execute = AsyncMock()
    return mock_db


@pytest.fixture
def mock_model_manager():
    """יוצר מוק של ModelManager"""
    mock_manager = MagicMock(spec=ModelManager)
    mock_manager.generate_response = AsyncMock()
    return mock_manager


@pytest.fixture
def learning_manager(mock_database, mock_model_manager):
    """יוצר מופע של LearningManager עם Database ו-ModelManager מדומים"""
    manager = LearningManager(db=mock_database, model_manager=mock_model_manager)
    return manager


@pytest.mark.asyncio
async def test_init(mock_database, mock_model_manager):
    """בודק שהאתחול של LearningManager מגדיר את הפרמטרים הנכונים"""
    manager = LearningManager(db=mock_database, model_manager=mock_model_manager)
    assert manager.db is mock_database
    assert manager.model_manager is mock_model_manager


@pytest.mark.asyncio
async def test_save_memory(learning_manager, mock_database):
    """בודק שהפונקציה save_memory שומרת זיכרון למשתמש"""
    # הגדרת התנהגות המוק
    mock_database.execute.return_value = None
    
    user_id = 123
    memory = "User likes pizza. User is allergic to nuts."
    
    await learning_manager.save_memory(user_id, memory)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_database.execute.assert_called_once()
    call_args = mock_database.execute.call_args[0]
    assert "INSERT INTO user_memories" in call_args[0]
    assert "ON CONFLICT" in call_args[0]
    assert call_args[1] == (user_id, memory)


@pytest.mark.asyncio
async def test_get_memory(learning_manager, mock_database):
    """בודק שהפונקציה get_memory מחזירה זיכרון של משתמש"""
    # הגדרת התנהגות המוק
    mock_database.execute.return_value = [("User likes pizza. User is allergic to nuts.",)]
    
    user_id = 123
    
    result = await learning_manager.get_memory(user_id)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_database.execute.assert_called_once()
    call_args = mock_database.execute.call_args[0]
    assert "SELECT memory FROM user_memories" in call_args[0]
    assert call_args[1] == (user_id,)
    
    # בדיקת התוצאה
    assert result == "User likes pizza. User is allergic to nuts."


@pytest.mark.asyncio
async def test_get_memory_no_result(learning_manager, mock_database):
    """בודק שהפונקציה get_memory מחזירה None כאשר אין זיכרון"""
    # הגדרת התנהגות המוק
    mock_database.execute.return_value = []
    
    user_id = 123
    
    result = await learning_manager.get_memory(user_id)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_database.execute.assert_called_once()
    
    # בדיקת התוצאה
    assert result is None


@pytest.mark.asyncio
async def test_update_memory(learning_manager, mock_database, mock_model_manager):
    """בודק שהפונקציה update_memory מעדכנת זיכרון של משתמש"""
    # הגדרת התנהגות המוקים
    mock_database.execute.side_effect = [
        [("Existing memory: User likes pizza.",)],  # תוצאת get_memory
        None  # תוצאת save_memory
    ]
    mock_model_manager.generate_response.return_value = "Updated memory: User likes pizza. User is allergic to nuts."
    
    user_id = 123
    new_information = "User is allergic to nuts."
    
    result = await learning_manager.update_memory(user_id, new_information)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    assert mock_database.execute.call_count == 2
    
    # בדיקת הקריאה ל-model_manager.generate_response
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert "Existing memory: User likes pizza." in str(call_args["messages"])
    assert "User is allergic to nuts." in str(call_args["messages"])
    
    # בדיקת התוצאה
    assert result == "Updated memory: User likes pizza. User is allergic to nuts."


@pytest.mark.asyncio
async def test_update_memory_no_existing(learning_manager, mock_database, mock_model_manager):
    """בודק שהפונקציה update_memory יוצרת זיכרון חדש כאשר אין זיכרון קיים"""
    # הגדרת התנהגות המוקים
    mock_database.execute.side_effect = [
        [],  # תוצאת get_memory (אין זיכרון קיים)
        None  # תוצאת save_memory
    ]
    mock_model_manager.generate_response.return_value = "New memory: User is allergic to nuts."
    
    user_id = 123
    new_information = "User is allergic to nuts."
    
    result = await learning_manager.update_memory(user_id, new_information)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    assert mock_database.execute.call_count == 2
    
    # בדיקת הקריאה ל-model_manager.generate_response
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert "User is allergic to nuts." in str(call_args["messages"])
    
    # בדיקת התוצאה
    assert result == "New memory: User is allergic to nuts."


@pytest.mark.asyncio
async def test_extract_information(learning_manager, mock_model_manager):
    """בודק שהפונקציה extract_information מחלצת מידע מטקסט"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = json.dumps({
        "information": [
            "User likes pizza",
            "User is allergic to nuts"
        ]
    })
    
    text = "I really enjoy eating pizza, but I can't have any nuts because of my allergy."
    
    result = await learning_manager.extract_information(text)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert text in str(call_args["messages"])
    
    # בדיקת התוצאה
    assert result == ["User likes pizza", "User is allergic to nuts"]


@pytest.mark.asyncio
async def test_extract_information_invalid_json(learning_manager, mock_model_manager):
    """בודק שהפונקציה extract_information מטפלת בתגובה לא תקינה"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "Not a valid JSON"
    
    text = "I really enjoy eating pizza, but I can't have any nuts because of my allergy."
    
    result = await learning_manager.extract_information(text)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות רשימה ריקה במקרה של שגיאה
    assert result == []


@pytest.mark.asyncio
async def test_extract_information_missing_key(learning_manager, mock_model_manager):
    """בודק שהפונקציה extract_information מטפלת ב-JSON חסר"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = json.dumps({
        "other_key": ["Some value"]
    })
    
    text = "I really enjoy eating pizza, but I can't have any nuts because of my allergy."
    
    result = await learning_manager.extract_information(text)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות רשימה ריקה כאשר המפתח חסר
    assert result == []


@pytest.mark.asyncio
async def test_learn_from_conversation(learning_manager, mock_model_manager, mock_database):
    """בודק שהפונקציה learn_from_conversation מחלצת מידע משיחה ומעדכנת את הזיכרון"""
    # הגדרת התנהגות המוקים
    mock_model_manager.generate_response.side_effect = [
        json.dumps({
            "information": [
                "User likes pizza",
                "User is allergic to nuts"
            ]
        }),  # תוצאת extract_information
        "Updated memory: User likes pizza. User is allergic to nuts."  # תוצאת update_memory
    ]
    mock_database.execute.side_effect = [
        [("Existing memory: User likes chocolate.",)],  # תוצאת get_memory
        None  # תוצאת save_memory
    ]
    
    user_id = 123
    conversation = [
        {"role": "user", "content": "I really enjoy eating pizza."},
        {"role": "assistant", "content": "Pizza is great! Any toppings you prefer?"},
        {"role": "user", "content": "I like all toppings except nuts, I'm allergic to them."}
    ]
    
    result = await learning_manager.learn_from_conversation(user_id, conversation)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    assert mock_model_manager.generate_response.call_count == 2
    assert mock_database.execute.call_count == 2
    
    # בדיקת התוצאה
    assert result == "Updated memory: User likes pizza. User is allergic to nuts."


@pytest.mark.asyncio
async def test_learn_from_conversation_empty(learning_manager):
    """בודק שהפונקציה learn_from_conversation מטפלת בשיחה ריקה"""
    user_id = 123
    conversation = []
    
    result = await learning_manager.learn_from_conversation(user_id, conversation)
    
    # בדיקת התוצאה - צריכה להיות None כאשר השיחה ריקה
    assert result is None


@pytest.mark.asyncio
async def test_learn_from_text(learning_manager, mock_model_manager, mock_database):
    """בודק שהפונקציה learn_from_text מחלצת מידע מטקסט ומעדכנת את הזיכרון"""
    # הגדרת התנהגות המוקים
    mock_model_manager.generate_response.side_effect = [
        json.dumps({
            "information": [
                "User likes pizza",
                "User is allergic to nuts"
            ]
        }),  # תוצאת extract_information
        "Updated memory: User likes pizza. User is allergic to nuts."  # תוצאת update_memory
    ]
    mock_database.execute.side_effect = [
        [("Existing memory: User likes chocolate.",)],  # תוצאת get_memory
        None  # תוצאת save_memory
    ]
    
    user_id = 123
    text = "I really enjoy eating pizza, but I can't have any nuts because of my allergy."
    
    result = await learning_manager.learn_from_text(user_id, text)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    assert mock_model_manager.generate_response.call_count == 2
    assert mock_database.execute.call_count == 2
    
    # בדיקת התוצאה
    assert result == "Updated memory: User likes pizza. User is allergic to nuts."


@pytest.mark.asyncio
async def test_learn_from_text_empty(learning_manager):
    """בודק שהפונקציה learn_from_text מטפלת בטקסט ריק"""
    user_id = 123
    text = ""
    
    result = await learning_manager.learn_from_text(user_id, text)
    
    # בדיקת התוצאה - צריכה להיות None כאשר הטקסט ריק
    assert result is None


@pytest.mark.asyncio
async def test_summarize_memory(learning_manager, mock_model_manager):
    """בודק שהפונקציה summarize_memory מסכמת זיכרון"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "User likes pizza and is allergic to nuts."
    
    memory = "User likes pizza. User enjoys watching movies. User has a dog. User is allergic to nuts. User lives in Tel Aviv."
    
    result = await learning_manager.summarize_memory(memory)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert memory in str(call_args["messages"])
    
    # בדיקת התוצאה
    assert result == "User likes pizza and is allergic to nuts."


@pytest.mark.asyncio
async def test_summarize_memory_empty(learning_manager):
    """בודק שהפונקציה summarize_memory מטפלת בזיכרון ריק"""
    memory = ""
    
    result = await learning_manager.summarize_memory(memory)
    
    # בדיקת התוצאה - צריכה להיות זהה לקלט כאשר הזיכרון ריק
    assert result == ""


@pytest.mark.asyncio
async def test_get_user_memory_summary(learning_manager, mock_database, mock_model_manager):
    """בודק שהפונקציה get_user_memory_summary מחזירה סיכום זיכרון של משתמש"""
    # הגדרת התנהגות המוקים
    mock_database.execute.return_value = [("User likes pizza. User enjoys watching movies. User has a dog. User is allergic to nuts. User lives in Tel Aviv.",)]
    mock_model_manager.generate_response.return_value = "User likes pizza and is allergic to nuts."
    
    user_id = 123
    
    result = await learning_manager.get_user_memory_summary(user_id)
    
    # וידוא שהפונקציות הנכונות נקראו עם הפרמטרים הנכונים
    mock_database.execute.assert_called_once()
    mock_model_manager.generate_response.assert_called_once()
    
    # בדיקת התוצאה
    assert result == "User likes pizza and is allergic to nuts."


@pytest.mark.asyncio
async def test_get_user_memory_summary_no_memory(learning_manager, mock_database):
    """בודק שהפונקציה get_user_memory_summary מטפלת במקרה שאין זיכרון"""
    # הגדרת התנהגות המוק
    mock_database.execute.return_value = []
    
    user_id = 123
    
    result = await learning_manager.get_user_memory_summary(user_id)
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_database.execute.assert_called_once()
    
    # בדיקת התוצאה - צריכה להיות None כאשר אין זיכרון
    assert result is None 