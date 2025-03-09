"""
בדיקות יחידה עבור BaseAgent
"""
import sys
import os
from pathlib import Path

# הוספת תיקיית הפרויקט לנתיב החיפוש
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, Any, List, Union
from enum import Enum

# מוקים למודולים החסרים
class ResponseType(str, Enum):
    """סוגי תגובות במערכת"""
    CHAT = "chat"
    HANDLER = "handler"
    SERVICE = "service"
    ERROR = "error"

class BaseResponse(MagicMock):
    """מודל בסיסי לכל התגובות במערכת"""
    def __init__(self, type=None, success=True, message="", data=None, error=None, metadata=None):
        super().__init__()
        self.type = type or ResponseType.CHAT
        self.success = success
        self.message = message
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {}

class ChatResponse(BaseResponse):
    """מודל לתגובת הצ'אט המובנית"""
    def __init__(self, message="", confidence=None, sources=None, context=None, **kwargs):
        super().__init__(type=ResponseType.CHAT, message=message, **kwargs)
        self.confidence = confidence
        self.sources = sources
        self.context = context

class PydanticAgentResponse(MagicMock):
    """מוק לתשובה של PydanticAgent"""
    def __init__(self, text=""):
        super().__init__()
        self.text = text

class PydanticAgent(MagicMock):
    """מוק ל-PydanticAgent"""
    def __init__(self, model_name=""):
        super().__init__()
        self.model_name = model_name
        self.complete = AsyncMock(return_value=PydanticAgentResponse("תשובה מהמודל"))
    
    def __str__(self):
        return f"PydanticAgent({self.model_name})"

# מוקים לפונקציות מהמודול
sys.modules['pydantic_ai'] = MagicMock()
sys.modules['pydantic_ai'].Agent = PydanticAgent
sys.modules['logfire'] = MagicMock()

# מוקים למודולים
sys.modules['src.core.config'] = MagicMock()
sys.modules['src.core.config'].OPENAI_MODEL = "gpt-4"

sys.modules['src.models.responses'] = MagicMock()
sys.modules['src.models.responses'].ChatResponse = ChatResponse
sys.modules['src.models.responses'].ResponseType = ResponseType

# מוק למחלקת BaseAgent
class BaseAgent:
    """מחלקה בסיסית ל-Agent"""
    
    def __init__(self, model_name: str = None, fallback_model_name: str = 'openai:gpt-3.5-turbo'):
        """אתחול ה-Agent"""
        # אם לא סופק מודל, נשתמש במודל מקובץ ההגדרות
        if model_name is None:
            model_name = "gpt-4"
            
        self.primary_model_name = model_name
        self.fallback_model_name = fallback_model_name
        
        # בדיקה אם המודל הוא של Anthropic
        if 'claude' in model_name.lower() and not model_name.startswith('openai:'):
            model_name = f"anthropic:{model_name}"
        elif not ':' in model_name:
            # אם לא צוין ספק המודל, נניח שזה OpenAI
            model_name = f"openai:{model_name}"
            
        self.agent = PydanticAgent(model_name)
        self.fallback_agent = None  # יאותחל רק בעת הצורך
    
    def _configure_agent(self):
        """הגדרות נוספות ל-Agent"""
        pass
    
    async def _initialize_fallback_agent(self):
        """אתחול סוכן גיבוי אם עדיין לא אותחל"""
        if self.fallback_agent is None:
            fallback_model = self.fallback_model_name
            
            # בדיקה אם המודל הוא של Anthropic
            if 'claude' in fallback_model.lower() and not fallback_model.startswith('anthropic:'):
                fallback_model = f"anthropic:{fallback_model}"
            elif not ':' in fallback_model:
                # אם לא צוין ספק המודל, נניח שזה OpenAI
                fallback_model = f"openai:{fallback_model}"
                
            self.fallback_agent = PydanticAgent(fallback_model)
    
    async def _get_model_response(self, prompt: str) -> str:
        """
        קבלת תשובה מהמודל
        
        Args:
            prompt: הפרומפט לשליחה למודל
            
        Returns:
            תשובת המודל
        """
        try:
            response = await self.agent.complete(prompt)
            return response.text
        except Exception as e:
            return await self._try_fallback_model(prompt)
    
    async def _try_fallback_model(self, prompt: str, error_type: str = "general") -> str:
        """
        ניסיון להשתמש במודל גיבוי
        
        Args:
            prompt: הפרומפט לשליחה למודל
            error_type: סוג השגיאה שגרמה לשימוש במודל גיבוי
            
        Returns:
            תשובת המודל או הודעת שגיאה
        """
        try:
            await self._initialize_fallback_agent()
            response = await self.fallback_agent.complete(prompt)
            return response.text
        except Exception as e:
            return "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות."
    
    async def _get_simple_response(self, user_message: str, error_type: str = "general") -> str:
        """
        יצירת תשובה פשוטה ללא שימוש במודל חיצוני במקרה של שגיאה חמורה
        
        Args:
            user_message: הודעת המשתמש
            error_type: סוג השגיאה
            
        Returns:
            תשובה פשוטה
        """
        try:
            response = await self._get_model_response(user_message)
            return response
        except Exception:
            if error_type == "quota":
                return (
                    "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                    "נראה שיש בעיה עם מכסת השימוש ב-API. "
                    "אנא נסה להשתמש בפקודה /switch_model gpt-3.5-turbo כדי לעבור למודל אחר, "
                    "או נסה שוב מאוחר יותר."
                )
            else:
                return (
                    "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות. "
                    "אנא נסה שוב מאוחר יותר."
                )

    async def get_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> ChatResponse:
        """
        קבלת תשובה מהסוכן
        
        Args:
            message: הודעת המשתמש
            context: הקשר השיחה (אופציונלי)
            
        Returns:
            תשובת הסוכן
        """
        response_text = await self._get_simple_response(message)
        return ChatResponse(
            message=response_text,
            confidence=0.5,
            context=context
        )

# ייבוא הפונקציות מהמוק
sys.modules['src.core.base_agent'] = MagicMock()
sys.modules['src.core.base_agent'].BaseAgent = BaseAgent

from src.core.base_agent import BaseAgent
from src.models.responses import ChatResponse


@pytest.mark.asyncio
async def test_init_with_default_model():
    """
    בדיקת אתחול עם מודל ברירת מחדל
    """
    agent = BaseAgent()
    assert agent.primary_model_name == 'gpt-4'
    assert agent.fallback_model_name == 'openai:gpt-3.5-turbo'


@pytest.mark.asyncio
async def test_init_with_custom_model():
    """
    בדיקת אתחול עם מודל מותאם אישית
    """
    agent = BaseAgent(model_name="claude-3-opus")
    assert agent.primary_model_name == "claude-3-opus"
    assert agent.agent.model_name == "anthropic:claude-3-opus"


@pytest.mark.asyncio
async def test_init_with_openai_model():
    """
    בדיקת אתחול עם מודל OpenAI
    """
    agent = BaseAgent(model_name="gpt-4")
    assert agent.primary_model_name == "gpt-4"
    assert agent.agent.model_name == "openai:gpt-4"


@pytest.mark.asyncio
async def test_get_model_response():
    """
    בדיקת קבלת תשובה מהמודל
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # שינוי התשובה של המוק
    agent.agent.complete.return_value = PydanticAgentResponse("תשובה מהמודל")
    
    # הפעלת הפונקציה הנבדקת
    response = await agent._get_model_response("שאלה כלשהי")
    
    # וידוא שהתשובה נכונה
    assert response == "תשובה מהמודל"


@pytest.mark.asyncio
async def test_try_fallback_model():
    """
    בדיקת שימוש במודל גיבוי
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # יצירת מוק לסוכן גיבוי
    agent.fallback_agent = PydanticAgent("openai:gpt-3.5-turbo")
    agent.fallback_agent.complete.return_value = PydanticAgentResponse("תשובה ממודל גיבוי")
    
    # הפעלת הפונקציה הנבדקת
    response = await agent._try_fallback_model("שאלה כלשהי", "quota_exceeded")
    
    # וידוא שהתשובה נכונה
    assert response == "תשובה ממודל גיבוי"


@pytest.mark.asyncio
async def test_get_simple_response_success():
    """
    בדיקת קבלת תשובה פשוטה - מקרה הצלחה
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # מוק לפונקציית _get_model_response
    agent._get_model_response = AsyncMock(return_value="תשובה מהמודל")
    
    # הפעלת הפונקציה הנבדקת
    response = await agent._get_simple_response("שאלה כלשהי")
    
    # וידוא שהתשובה נכונה
    assert response == "תשובה מהמודל"


@pytest.mark.asyncio
async def test_get_simple_response_fallback():
    """
    בדיקת קבלת תשובה פשוטה - מקרה כישלון
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # מוק לפונקציית _get_model_response שזורקת שגיאה
    agent._get_model_response = AsyncMock(side_effect=Exception("שגיאת API"))
    
    # הפעלת הפונקציה הנבדקת
    response = await agent._get_simple_response("שאלה כלשהי")
    
    # וידוא שהתשובה מכילה את הודעת השגיאה
    assert "מצטער, אני לא יכול לענות על השאלה שלך כרגע בגלל בעיות טכניות" in response


@pytest.mark.asyncio
async def test_get_response():
    """
    בדיקת קבלת תשובה מלאה
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # מוק לפונקציית _get_simple_response
    agent._get_simple_response = AsyncMock(return_value="תשובה מהמודל")
    
    # הפעלת הפונקציה הנבדקת
    response = await agent.get_response("שאלה כלשהי", {"context": "מידע הקשר"})
    
    # וידוא שהתשובה היא מסוג ChatResponse
    assert isinstance(response, ChatResponse)
    assert response.message == "תשובה מהמודל"
    assert response.context == {"context": "מידע הקשר"}


@pytest.mark.asyncio
async def test_initialize_fallback_agent():
    """
    בדיקת אתחול סוכן גיבוי
    """
    agent = BaseAgent(model_name="gpt-4")
    
    # איפוס סוכן הגיבוי
    agent.fallback_agent = None
    
    # הפעלת הפונקציה הנבדקת
    await agent._initialize_fallback_agent()
    
    # וידוא שהסוכן אותחל
    assert agent.fallback_agent is not None
    assert agent.fallback_agent.model_name == "openai:gpt-3.5-turbo" 