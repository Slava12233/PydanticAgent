"""
בדיקות יחידה למנהל המודל
"""

import pytest
from unittest.mock import Mock, patch
from src.agents.core.model_manager import ModelManager

@pytest.fixture
def model_manager():
    """יצירת מופע של מנהל המודל לבדיקות"""
    return ModelManager()

def test_init_default_model(model_manager):
    """בדיקת אתחול עם מודל ברירת מחדל"""
    assert model_manager.primary_model_name == 'gpt-3.5-turbo'
    assert model_manager.fallback_model_name == 'openai:gpt-3.5-turbo'
    assert model_manager.agent is not None
    assert model_manager.fallback_agent is None

def test_init_custom_model():
    """בדיקת אתחול עם מודל מותאם אישית"""
    manager = ModelManager(model_name='gpt-4')
    assert manager.primary_model_name == 'gpt-4'
    assert manager.agent is not None
    assert manager.fallback_agent is None

def test_init_anthropic_model():
    """בדיקת אתחול עם מודל של Anthropic"""
    manager = ModelManager(model_name='claude-2')
    assert manager.primary_model_name == 'claude-2'
    assert 'anthropic:claude-2' in str(manager.agent)
    assert manager.fallback_agent is None

@pytest.mark.asyncio
async def test_initialize_fallback_agent(model_manager):
    """בדיקת אתחול סוכן גיבוי"""
    assert model_manager.fallback_agent is None
    await model_manager.initialize_fallback_agent()
    assert model_manager.fallback_agent is not None
    assert 'gpt-3.5-turbo' in str(model_manager.fallback_agent)

def test_get_simple_response_quota(model_manager):
    """בדיקת קבלת תשובה פשוטה לשגיאת מכסה"""
    response = model_manager.get_simple_response("מה המחיר?", "quota")
    assert response != ""
    assert "מכסת השימוש" in response
    assert "switch_model" in response

def test_get_simple_response_timeout(model_manager):
    """בדיקת קבלת תשובה פשוטה לשגיאת זמן"""
    response = model_manager.get_simple_response("מה המחיר?", "timeout")
    assert response != ""
    assert "זמן" in response
    assert "פשוטה יותר" in response

def test_get_simple_response_general(model_manager):
    """בדיקת קבלת תשובה פשוטה לשגיאה כללית"""
    response = model_manager.get_simple_response("מה המחיר?", "general")
    assert response != ""
    assert "בעיה טכנית" in response
    assert "נסה שוב" in response

@pytest.mark.asyncio
@patch('pydantic_ai.Agent')
async def test_model_interaction(mock_agent, model_manager):
    """בדיקת אינטראקציה עם המודל"""
    # הגדרת התנהגות מדומה למודל
    mock_agent.complete.return_value = "תשובה מהמודל"
    model_manager.agent = mock_agent
    
    # בדיקת קריאה למודל
    prompt = "מה המחיר של המוצר?"
    response = await model_manager.agent.complete(prompt)
    
    # וידוא שהמודל נקרא עם הפרומפט הנכון
    mock_agent.complete.assert_called_once_with(prompt)
    assert response == "תשובה מהמודל"

@pytest.mark.asyncio
@patch('pydantic_ai.Agent')
async def test_fallback_model_interaction(mock_agent, model_manager):
    """בדיקת אינטראקציה עם מודל הגיבוי"""
    # הגדרת התנהגות מדומה למודל הגיבוי
    mock_agent.complete.return_value = "תשובה ממודל הגיבוי"
    
    # אתחול מודל הגיבוי
    await model_manager.initialize_fallback_agent()
    model_manager.fallback_agent = mock_agent
    
    # בדיקת קריאה למודל הגיבוי
    prompt = "מה המחיר של המוצר?"
    response = await model_manager.fallback_agent.complete(prompt)
    
    # וידוא שמודל הגיבוי נקרא עם הפרומפט הנכון
    mock_agent.complete.assert_called_once_with(prompt)
    assert response == "תשובה ממודל הגיבוי" 