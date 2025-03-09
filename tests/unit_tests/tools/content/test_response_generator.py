"""
בדיקות יחידה למודול response_generator.py
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from src.tools.content.response_generator import ResponseGenerator
from src.core.model_manager import ModelManager


@pytest.fixture
def mock_model_manager():
    """יוצר מוק של ModelManager"""
    mock_manager = MagicMock(spec=ModelManager)
    mock_manager.generate_response = AsyncMock()
    return mock_manager


@pytest.fixture
def response_generator(mock_model_manager):
    """יוצר מופע של ResponseGenerator עם ModelManager מדומה"""
    generator = ResponseGenerator(model_manager=mock_model_manager)
    return generator


@pytest.mark.asyncio
async def test_init(mock_model_manager):
    """בודק שהאתחול של ResponseGenerator מגדיר את הפרמטרים הנכונים"""
    generator = ResponseGenerator(model_manager=mock_model_manager)
    assert generator.model_manager is mock_model_manager


@pytest.mark.asyncio
async def test_generate_response(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response קוראת ל-ModelManager עם הפרמטרים הנכונים"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    result = await response_generator.generate_response(
        prompt="Hello",
        system_message="You are a helpful assistant",
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == "You are a helpful assistant"
    assert call_args["messages"][1]["role"] == "user"
    assert call_args["messages"][1]["content"] == "Hello"
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_conversation(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מעבירה את השיחה הקודמת"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    result = await response_generator.generate_response(
        prompt=None,
        system_message="You are a helpful assistant",
        conversation=conversation,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert len(call_args["messages"]) == 4  # system + 3 conversation messages
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == "You are a helpful assistant"
    assert call_args["messages"][1:] == conversation
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_prompt_and_conversation(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מעדיפה את ה-prompt על פני השיחה האחרונה"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    result = await response_generator.generate_response(
        prompt="New question",
        system_message="You are a helpful assistant",
        conversation=conversation,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert len(call_args["messages"]) == 4  # system + 2 conversation messages + new prompt
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == "You are a helpful assistant"
    assert call_args["messages"][1:3] == conversation[:2]  # רק 2 הודעות ראשונות מהשיחה
    assert call_args["messages"][3]["role"] == "user"
    assert call_args["messages"][3]["content"] == "New question"
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_context(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מוסיפה הקשר לפרומפט"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    context = "This is some relevant context information."
    
    result = await response_generator.generate_response(
        prompt="Hello",
        system_message="You are a helpful assistant",
        context=context,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == "You are a helpful assistant"
    assert call_args["messages"][1]["role"] == "user"
    assert context in call_args["messages"][1]["content"]
    assert "Hello" in call_args["messages"][1]["content"]
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_memory(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מוסיפה זיכרון לפרומפט"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    memory = "User likes pizza. User is allergic to nuts."
    
    result = await response_generator.generate_response(
        prompt="Hello",
        system_message="You are a helpful assistant",
        memory=memory,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert memory in call_args["messages"][0]["content"]
    assert "You are a helpful assistant" in call_args["messages"][0]["content"]
    assert call_args["messages"][1]["role"] == "user"
    assert call_args["messages"][1]["content"] == "Hello"
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_specific_model(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מעבירה מודל ספציפי"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    result = await response_generator.generate_response(
        prompt="Hello",
        system_message="You are a helpful assistant",
        model="gpt-4o",
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert call_args["model"] == "gpt-4o"
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_max_tokens(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מעבירה מגבלת טוקנים"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    result = await response_generator.generate_response(
        prompt="Hello",
        system_message="You are a helpful assistant",
        max_tokens=100,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    assert call_args["max_tokens"] == 100
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_generate_response_with_all_parameters(response_generator, mock_model_manager):
    """בודק שהפונקציה generate_response מעבירה את כל הפרמטרים יחד"""
    # הגדרת התנהגות המוק
    mock_model_manager.generate_response.return_value = "This is a test response"
    
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    context = "This is some relevant context information."
    memory = "User likes pizza. User is allergic to nuts."
    
    result = await response_generator.generate_response(
        prompt="How can you help me?",
        system_message="You are a helpful assistant",
        conversation=conversation,
        context=context,
        memory=memory,
        model="gpt-4o",
        max_tokens=100,
        temperature=0.7
    )
    
    # וידוא שהפונקציה הנכונה נקראה עם הפרמטרים הנכונים
    mock_model_manager.generate_response.assert_called_once()
    call_args = mock_model_manager.generate_response.call_args[1]
    
    # בדיקת הודעת המערכת עם זיכרון
    assert call_args["messages"][0]["role"] == "system"
    assert memory in call_args["messages"][0]["content"]
    assert "You are a helpful assistant" in call_args["messages"][0]["content"]
    
    # בדיקת השיחה הקודמת
    assert call_args["messages"][1]["role"] == "user"
    assert call_args["messages"][1]["content"] == "Hello"
    assert call_args["messages"][2]["role"] == "assistant"
    assert call_args["messages"][2]["content"] == "Hi there!"
    
    # בדיקת הפרומפט החדש עם הקשר
    assert call_args["messages"][3]["role"] == "user"
    assert context in call_args["messages"][3]["content"]
    assert "How can you help me?" in call_args["messages"][3]["content"]
    
    # בדיקת פרמטרים נוספים
    assert call_args["model"] == "gpt-4o"
    assert call_args["max_tokens"] == 100
    assert call_args["temperature"] == 0.7
    
    # בדיקת התוצאה
    assert result == "This is a test response"


@pytest.mark.asyncio
async def test_format_prompt_with_context(response_generator):
    """בודק שהפונקציה _format_prompt_with_context מוסיפה הקשר לפרומפט"""
    prompt = "What is the capital of France?"
    context = "France is a country in Western Europe."
    
    formatted_prompt = response_generator._format_prompt_with_context(prompt, context)
    
    assert context in formatted_prompt
    assert prompt in formatted_prompt
    assert "Context:" in formatted_prompt
    assert "Question:" in formatted_prompt


@pytest.mark.asyncio
async def test_format_prompt_with_context_empty_context(response_generator):
    """בודק שהפונקציה _format_prompt_with_context מחזירה את הפרומפט המקורי כאשר אין הקשר"""
    prompt = "What is the capital of France?"
    
    formatted_prompt = response_generator._format_prompt_with_context(prompt, None)
    assert formatted_prompt == prompt
    
    formatted_prompt = response_generator._format_prompt_with_context(prompt, "")
    assert formatted_prompt == prompt


@pytest.mark.asyncio
async def test_format_system_message_with_memory(response_generator):
    """בודק שהפונקציה _format_system_message_with_memory מוסיפה זיכרון להודעת המערכת"""
    system_message = "You are a helpful assistant."
    memory = "User likes pizza. User is allergic to nuts."
    
    formatted_message = response_generator._format_system_message_with_memory(system_message, memory)
    
    assert system_message in formatted_message
    assert memory in formatted_message
    assert "User Information:" in formatted_message


@pytest.mark.asyncio
async def test_format_system_message_with_memory_empty_memory(response_generator):
    """בודק שהפונקציה _format_system_message_with_memory מחזירה את הודעת המערכת המקורית כאשר אין זיכרון"""
    system_message = "You are a helpful assistant."
    
    formatted_message = response_generator._format_system_message_with_memory(system_message, None)
    assert formatted_message == system_message
    
    formatted_message = response_generator._format_system_message_with_memory(system_message, "")
    assert formatted_message == system_message


@pytest.mark.asyncio
async def test_prepare_messages_with_prompt_only(response_generator):
    """בודק שהפונקציה _prepare_messages מכינה הודעות עם פרומפט בלבד"""
    system_message = "You are a helpful assistant."
    prompt = "What is the capital of France?"
    
    messages = response_generator._prepare_messages(
        system_message=system_message,
        prompt=prompt,
        conversation=None,
        context=None,
        memory=None
    )
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_message
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == prompt


@pytest.mark.asyncio
async def test_prepare_messages_with_conversation(response_generator):
    """בודק שהפונקציה _prepare_messages מכינה הודעות עם שיחה"""
    system_message = "You are a helpful assistant."
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    messages = response_generator._prepare_messages(
        system_message=system_message,
        prompt=None,
        conversation=conversation,
        context=None,
        memory=None
    )
    
    assert len(messages) == 4  # system + 3 conversation messages
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_message
    assert messages[1:] == conversation


@pytest.mark.asyncio
async def test_prepare_messages_with_prompt_and_conversation(response_generator):
    """בודק שהפונקציה _prepare_messages מכינה הודעות עם פרומפט ושיחה"""
    system_message = "You are a helpful assistant."
    prompt = "New question"
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    messages = response_generator._prepare_messages(
        system_message=system_message,
        prompt=prompt,
        conversation=conversation,
        context=None,
        memory=None
    )
    
    assert len(messages) == 4  # system + 2 conversation messages + new prompt
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_message
    assert messages[1:3] == conversation[:2]  # רק 2 הודעות ראשונות מהשיחה
    assert messages[3]["role"] == "user"
    assert messages[3]["content"] == prompt 