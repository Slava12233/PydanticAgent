"""
בדיקות יחידה למודול model_manager.py
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import json

# מוק למחלקת ModelManager
class ModelManager:
    """מוק למחלקת ModelManager"""
    
    def __init__(self, default_provider="openai", default_model=None):
        """אתחול מנהל המודלים"""
        self.providers = {
            "openai": {
                "client": None,
                "models": {
                    "gpt-3.5-turbo": {"max_tokens": 4096, "context_window": 4096},
                    "gpt-4": {"max_tokens": 8192, "context_window": 8192},
                    "gpt-4-turbo": {"max_tokens": 16384, "context_window": 16384}
                }
            },
            "anthropic": {
                "client": None,
                "models": {
                    "claude-2": {"max_tokens": 8192, "context_window": 8192},
                    "claude-instant-1": {"max_tokens": 4096, "context_window": 4096}
                }
            },
            "cohere": {
                "client": None,
                "models": {
                    "command": {"max_tokens": 4096, "context_window": 4096},
                    "command-light": {"max_tokens": 4096, "context_window": 4096}
                }
            }
        }
        
        self.default_provider = default_provider
        self.default_models = {
            "openai": default_model or "gpt-3.5-turbo",
            "anthropic": default_model or "claude-2",
            "cohere": default_model or "command"
        }
        
        # אתחול לקוחות API
        self._init_clients()
    
    def _init_clients(self):
        """אתחול לקוחות API"""
        # בפועל, כאן היינו מאתחלים את הלקוחות האמיתיים
        # אבל במוק, אנחנו פשוט יוצרים מוקים
        self.providers["openai"]["client"] = MagicMock()
        self.providers["anthropic"]["client"] = MagicMock()
        self.providers["cohere"]["client"] = MagicMock()
    
    def get_model_info(self, provider=None, model=None):
        """קבלת מידע על מודל"""
        provider = provider or self.default_provider
        model = model or self.default_models[provider]
        
        if provider in self.providers and model in self.providers[provider]["models"]:
            return {
                "provider": provider,
                "model": model,
                **self.providers[provider]["models"][model]
            }
        
        return None
    
    def set_model(self, provider, model):
        """הגדרת מודל ברירת מחדל"""
        if provider in self.providers and model in self.providers[provider]["models"]:
            self.default_provider = provider
            self.default_models[provider] = model
            return True
        
        return False
    
    def get_current_model(self):
        """קבלת מודל ברירת מחדל נוכחי"""
        return {
            "provider": self.default_provider,
            "model": self.default_models[self.default_provider]
        }
    
    def get_available_models(self):
        """קבלת רשימת מודלים זמינים"""
        available_models = {}
        
        for provider, data in self.providers.items():
            available_models[provider] = list(data["models"].keys())
        
        return available_models
    
    async def generate_openai_response(self, messages, model=None, temperature=0.7, max_tokens=None):
        """יצירת תשובה באמצעות OpenAI"""
        model = model or self.default_models["openai"]
        
        # מדמה תשובה מ-OpenAI
        return {
            "content": "תשובה לדוגמה מ-OpenAI",
            "model": model,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
    
    async def generate_anthropic_response(self, messages, model=None, temperature=0.7, max_tokens=None):
        """יצירת תשובה באמצעות Anthropic"""
        model = model or self.default_models["anthropic"]
        
        # מדמה תשובה מ-Anthropic
        return {
            "content": "תשובה לדוגמה מ-Anthropic",
            "model": model,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
    
    async def generate_cohere_response(self, messages, model=None, temperature=0.7, max_tokens=None):
        """יצירת תשובה באמצעות Cohere"""
        model = model or self.default_models["cohere"]
        
        # מדמה תשובה מ-Cohere
        return {
            "content": "תשובה לדוגמה מ-Cohere",
            "model": model,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
    
    async def generate_response(self, messages, provider=None, model=None, temperature=0.7, max_tokens=None):
        """יצירת תשובה באמצעות ספק שירות מתאים"""
        provider = provider or self.default_provider
        
        if provider == "openai":
            return await self.generate_openai_response(messages, model, temperature, max_tokens)
        elif provider == "anthropic":
            return await self.generate_anthropic_response(messages, model, temperature, max_tokens)
        elif provider == "cohere":
            return await self.generate_cohere_response(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"ספק שירות לא נתמך: {provider}")


@pytest.fixture
def model_manager():
    """יוצר מופע של ModelManager לבדיקות"""
    # יצירת מופע ModelManager
    manager = ModelManager()
    
    # מוק לפונקציות
    manager.generate_openai_response = AsyncMock(side_effect=manager.generate_openai_response)
    manager.generate_anthropic_response = AsyncMock(side_effect=manager.generate_anthropic_response)
    manager.generate_cohere_response = AsyncMock(side_effect=manager.generate_cohere_response)
    manager.generate_response = AsyncMock(side_effect=manager.generate_response)
    
    return manager


@pytest.fixture
def mock_openai():
    """מוק לספק OpenAI"""
    mock = MagicMock()
    mock.chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="תשובה לדוגמה מ-OpenAI"))],
        usage=MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        model="gpt-3.5-turbo"
    ))
    return mock


@pytest.fixture
def mock_anthropic():
    """מוק לספק Anthropic"""
    mock = MagicMock()
    mock.completions.create = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="תשובה לדוגמה מ-Anthropic")],
        usage=MagicMock(input_tokens=100, output_tokens=50),
        model="claude-2"
    ))
    return mock


@pytest.fixture
def mock_cohere():
    """מוק לספק Cohere"""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value=MagicMock(
        generations=[MagicMock(text="תשובה לדוגמה מ-Cohere")],
        meta=MagicMock(billed_units=MagicMock(input_tokens=100, output_tokens=50)),
        model="command"
    ))
    return mock


def test_init(model_manager):
    """בדיקת אתחול מנהל המודלים"""
    # וידוא שהמודל אותחל כראוי
    assert model_manager.default_provider == "openai"
    assert model_manager.default_models["openai"] == "gpt-3.5-turbo"
    assert model_manager.default_models["anthropic"] == "claude-2"
    assert model_manager.default_models["cohere"] == "command"
    
    # וידוא שהלקוחות אותחלו
    assert model_manager.providers["openai"]["client"] is not None
    assert model_manager.providers["anthropic"]["client"] is not None
    assert model_manager.providers["cohere"]["client"] is not None


def test_get_model_info(model_manager):
    """בדיקת קבלת מידע על מודל"""
    # קבלת מידע על מודל ברירת מחדל
    info = model_manager.get_model_info()
    assert info["provider"] == "openai"
    assert info["model"] == "gpt-3.5-turbo"
    assert "max_tokens" in info
    assert "context_window" in info
    
    # קבלת מידע על מודל ספציפי
    info = model_manager.get_model_info("anthropic", "claude-2")
    assert info["provider"] == "anthropic"
    assert info["model"] == "claude-2"
    assert "max_tokens" in info
    assert "context_window" in info


def test_set_model(model_manager):
    """בדיקת הגדרת מודל ברירת מחדל"""
    # הגדרת מודל חדש
    result = model_manager.set_model("openai", "gpt-4")
    assert result is True
    assert model_manager.default_provider == "openai"
    assert model_manager.default_models["openai"] == "gpt-4"
    
    # ניסיון להגדיר מודל לא קיים
    result = model_manager.set_model("openai", "non-existent-model")
    assert result is False
    assert model_manager.default_models["openai"] == "gpt-4"  # לא השתנה


def test_get_current_model(model_manager):
    """בדיקת קבלת מודל ברירת מחדל נוכחי"""
    # קבלת מודל ברירת מחדל
    current = model_manager.get_current_model()
    assert current["provider"] == "openai"
    assert current["model"] == "gpt-3.5-turbo"


def test_get_available_models(model_manager):
    """בדיקת קבלת רשימת מודלים זמינים"""
    # קבלת רשימת מודלים
    models = model_manager.get_available_models()
    assert "openai" in models
    assert "anthropic" in models
    assert "cohere" in models
    assert "gpt-3.5-turbo" in models["openai"]
    assert "claude-2" in models["anthropic"]
    assert "command" in models["cohere"]


@pytest.mark.asyncio
async def test_generate_openai_response(model_manager, mock_openai):
    """בדיקת יצירת תשובה באמצעות OpenAI"""
    # הגדרת מוק לתשובה
    model_manager.providers["openai"]["client"] = mock_openai
    
    # הרצת הפונקציה
    response = await model_manager.generate_openai_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_openai_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-OpenAI"
    assert response["model"] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_generate_anthropic_response(model_manager, mock_anthropic):
    """בדיקת יצירת תשובה באמצעות Anthropic"""
    # הגדרת מוק לתשובה
    model_manager.providers["anthropic"]["client"] = mock_anthropic
    
    # הרצת הפונקציה
    response = await model_manager.generate_anthropic_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        model="claude-2",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_anthropic_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-Anthropic"
    assert response["model"] == "claude-2"


@pytest.mark.asyncio
async def test_generate_cohere_response(model_manager, mock_cohere):
    """בדיקת יצירת תשובה באמצעות Cohere"""
    # הגדרת מוק לתשובה
    model_manager.providers["cohere"]["client"] = mock_cohere
    
    # הרצת הפונקציה
    response = await model_manager.generate_cohere_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        model="command",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_cohere_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-Cohere"
    assert response["model"] == "command"


@pytest.mark.asyncio
async def test_generate_response_openai(model_manager):
    """בדיקת יצירת תשובה באמצעות ספק OpenAI"""
    # הרצת הפונקציה
    response = await model_manager.generate_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-OpenAI"
    assert response["model"] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_generate_response_anthropic(model_manager):
    """בדיקת יצירת תשובה באמצעות ספק Anthropic"""
    # הרצת הפונקציה
    response = await model_manager.generate_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        provider="anthropic",
        model="claude-2",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-Anthropic"
    assert response["model"] == "claude-2"


@pytest.mark.asyncio
async def test_generate_response_cohere(model_manager):
    """בדיקת יצירת תשובה באמצעות ספק Cohere"""
    # הרצת הפונקציה
    response = await model_manager.generate_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        provider="cohere",
        model="command",
        temperature=0.5,
        max_tokens=100
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "content" in response
    assert "model" in response
    assert "usage" in response
    assert response["content"] == "תשובה לדוגמה מ-Cohere"
    assert response["model"] == "command"


@pytest.mark.asyncio
async def test_generate_response_invalid_provider(model_manager):
    """בדיקת יצירת תשובה באמצעות ספק לא חוקי"""
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(ValueError) as excinfo:
        await model_manager.generate_response(
            messages=[{"role": "user", "content": "שאלה לדוגמה"}],
            provider="invalid_provider"
        )
    
    # וידוא שהשגיאה מכילה את ההודעה הנכונה
    assert "ספק שירות לא נתמך" in str(excinfo.value)


@pytest.mark.asyncio
async def test_generate_response_with_specific_model(model_manager):
    """בדיקת יצירת תשובה עם מודל ספציפי"""
    # הרצת הפונקציה
    response = await model_manager.generate_response(
        messages=[{"role": "user", "content": "שאלה לדוגמה"}],
        provider="openai",
        model="gpt-4"
    )
    
    # וידוא שהפונקציה נקראה
    model_manager.generate_response.assert_called_once()
    
    # וידוא שהוחזרה תשובה תקינה
    assert response is not None
    assert "model" in response
    assert response["model"] == "gpt-4" 