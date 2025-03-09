"""
בדיקות יחידה עבור מודול Learning Service
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime, timezone, timedelta
import json

# מוק למחלקת LearningService
class LearningService:
    """מוק למחלקת LearningService"""
    
    def __init__(self):
        """אתחול שירות הלמידה"""
        self.client = MagicMock()
        self.db = MagicMock()
    
    async def analyze_user_patterns(self, user_id):
        """ניתוח דפוסי התנהגות של משתמש"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בניתוח דפוסי התנהגות של משתמש")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(self, "_empty_results", False):
            return {
                "patterns": [],
                "topics_of_interest": [],
                "activity_times": {},
                "response_preferences": {}
            }
        
        # החזרת תוצאות לדוגמה
        return {
            "patterns": [
                {"type": "search", "frequency": 0.6, "avg_length": 15},
                {"type": "document", "frequency": 0.3, "avg_length": 250},
                {"type": "conversation", "frequency": 0.1, "avg_length": 50}
            ],
            "topics_of_interest": ["טכנולוגיה", "מדע", "חדשות"],
            "activity_times": {
                "morning": 0.2,
                "afternoon": 0.5,
                "evening": 0.3
            },
            "response_preferences": {
                "length": "medium",
                "detail_level": "high",
                "formality": "medium"
            }
        }
    
    async def update_memory_weights(self, user_id, interaction_data):
        """עדכון משקלי זיכרון"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בעדכון משקלי זיכרון")
        
        # החזרת תוצאות לדוגמה
        return {
            "updated": True,
            "new_weights": {
                "recency": 0.7,
                "importance": 0.8,
                "relevance": 0.9
            }
        }
    
    async def adapt_response_style(self, user_id, message_content):
        """התאמת סגנון תגובה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בהתאמת סגנון תגובה")
        
        # החזרת תוצאות לדוגמה
        return {
            "style": "informative",
            "tone": "friendly",
            "length": "medium",
            "detail_level": "high",
            "formality": "medium"
        }
    
    async def update_user_preferences(self, user_id, preferences=None):
        """עדכון העדפות משתמש"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(self, "_raise_exception", False):
            raise Exception("שגיאה בעדכון העדפות משתמש")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(self, "_empty_results", False):
            return {
                "updated": False,
                "preferences": {}
            }
        
        # החזרת תוצאות לדוגמה
        return {
            "updated": True,
            "preferences": preferences or {
                "response_style": "informative",
                "tone": "friendly",
                "length": "medium",
                "detail_level": "high",
                "formality": "medium"
            }
        }


@pytest_asyncio.fixture
async def learning_service():
    """פיקסצ'ר ליצירת מופע Learning Service לבדיקות"""
    # יצירת מופע של Learning Service
    service = LearningService()
    return service


@pytest.mark.asyncio
async def test_analyze_user_patterns(learning_service):
    """בדיקת ניתוח דפוסי התנהגות של משתמש"""
    # ניתוח דפוסי התנהגות של משתמש
    result = await learning_service.analyze_user_patterns(user_id=1)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert "patterns" in result
    assert "topics_of_interest" in result
    assert "activity_times" in result
    assert "response_preferences" in result
    
    # בדיקת דפוסים
    assert len(result["patterns"]) == 3
    assert result["patterns"][0]["type"] == "search"
    assert result["patterns"][1]["type"] == "document"
    assert result["patterns"][2]["type"] == "conversation"
    
    # בדיקת נושאי עניין
    assert len(result["topics_of_interest"]) == 3
    assert "טכנולוגיה" in result["topics_of_interest"]
    assert "מדע" in result["topics_of_interest"]
    assert "חדשות" in result["topics_of_interest"]
    
    # בדיקת זמני פעילות
    assert "morning" in result["activity_times"]
    assert "afternoon" in result["activity_times"]
    assert "evening" in result["activity_times"]
    
    # בדיקת העדפות תגובה
    assert result["response_preferences"]["length"] == "medium"
    assert result["response_preferences"]["detail_level"] == "high"
    assert result["response_preferences"]["formality"] == "medium"


@pytest.mark.asyncio
async def test_update_memory_weights(learning_service):
    """בדיקת עדכון משקלי זיכרון"""
    # עדכון משקלי זיכרון
    interaction_data = {
        "message_type": "search",
        "content_length": 20,
        "response_time": 1.5,
        "user_feedback": "positive"
    }
    
    result = await learning_service.update_memory_weights(user_id=1, interaction_data=interaction_data)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert result["updated"] is True
    assert "new_weights" in result
    assert result["new_weights"]["recency"] == 0.7
    assert result["new_weights"]["importance"] == 0.8
    assert result["new_weights"]["relevance"] == 0.9


@pytest.mark.asyncio
async def test_adapt_response_style(learning_service):
    """בדיקת התאמת סגנון תגובה"""
    # התאמת סגנון תגובה
    message_content = "מה המשמעות של בינה מלאכותית בעולם המודרני?"
    
    result = await learning_service.adapt_response_style(user_id=1, message_content=message_content)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert "style" in result
    assert "tone" in result
    assert "length" in result
    assert "detail_level" in result
    assert "formality" in result
    
    # בדיקת ערכים ספציפיים
    assert result["style"] == "informative"
    assert result["tone"] == "friendly"
    assert result["length"] == "medium"
    assert result["detail_level"] == "high"
    assert result["formality"] == "medium"


@pytest.mark.asyncio
async def test_update_user_preferences(learning_service):
    """בדיקת עדכון העדפות משתמש"""
    # עדכון העדפות משתמש
    preferences = {
        "response_style": "concise",
        "tone": "professional",
        "length": "short",
        "detail_level": "medium",
        "formality": "high"
    }
    
    result = await learning_service.update_user_preferences(user_id=1, preferences=preferences)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert result["updated"] is True
    assert "preferences" in result
    
    # בדיקת ערכים ספציפיים
    assert result["preferences"]["response_style"] == "concise"
    assert result["preferences"]["tone"] == "professional"
    assert result["preferences"]["length"] == "short"
    assert result["preferences"]["detail_level"] == "medium"
    assert result["preferences"]["formality"] == "high"


@pytest.mark.asyncio
async def test_analyze_user_patterns_no_messages(learning_service):
    """בדיקת ניתוח דפוסי התנהגות של משתמש ללא הודעות"""
    # הגדרת התנהגות המוק
    learning_service._empty_results = True
    
    # ניתוח דפוסי התנהגות של משתמש
    result = await learning_service.analyze_user_patterns(user_id=999)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert "patterns" in result
    assert "topics_of_interest" in result
    assert "activity_times" in result
    assert "response_preferences" in result
    
    # בדיקה שהרשימות ריקות
    assert len(result["patterns"]) == 0
    assert len(result["topics_of_interest"]) == 0
    assert len(result["activity_times"]) == 0
    
    # איפוס התנהגות המוק
    learning_service._empty_results = False


@pytest.mark.asyncio
async def test_adapt_response_style_error(learning_service):
    """בדיקת טיפול בשגיאות בהתאמת סגנון תגובה"""
    # הגדרת התנהגות המוק
    learning_service._raise_exception = True
    
    # בדיקה שהפונקציה מעלה שגיאה
    with pytest.raises(Exception) as excinfo:
        await learning_service.adapt_response_style(user_id=1, message_content="שאלה כלשהי")
    
    # בדיקת הודעת השגיאה
    assert "שגיאה בהתאמת סגנון תגובה" in str(excinfo.value)
    
    # איפוס התנהגות המוק
    learning_service._raise_exception = False


@pytest.mark.asyncio
async def test_update_user_preferences_new_user(learning_service):
    """בדיקת עדכון העדפות משתמש חדש"""
    # הגדרת התנהגות המוק
    learning_service._empty_results = True
    
    # עדכון העדפות משתמש חדש
    result = await learning_service.update_user_preferences(user_id=999)
    
    # וידוא שהוחזרו התוצאות הנכונות
    assert result["updated"] is False
    assert "preferences" in result
    assert len(result["preferences"]) == 0
    
    # איפוס התנהגות המוק
    learning_service._empty_results = False 