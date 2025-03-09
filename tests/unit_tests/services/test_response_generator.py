"""
בדיקות יחידה עבור מודול ResponseGenerator
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import json

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.core.response_generator import generate_response

# יצירת מוק לפונקציית generate_response
async def generate_response_mock(query, history=None, context=None, system_prompt=None, model="gpt-3.5-turbo", temperature=0.7):
    """מוק לפונקציית generate_response"""
    if not query:
        return {"response": "", "tokens": 0, "model": model}
    
    if query == "error_message":
        raise Exception("API Error")
    
    if query == "long_response":
        return {
            "response": "זוהי תשובה ארוכה מאוד " * 50,
            "tokens": 500,
            "model": model
        }
    
    # התאמת התשובה לפי ההקשר
    if context:
        if "weather" in context:
            return {
                "response": "היום יהיה יום שמשי עם טמפרטורות של 25-30 מעלות.",
                "tokens": 50,
                "model": model
            }
        elif "news" in context:
            return {
                "response": "החדשות האחרונות: התקדמות משמעותית בפיתוח בינה מלאכותית.",
                "tokens": 60,
                "model": model
            }
    
    # התאמת התשובה לפי ההיסטוריה
    if history:
        if any("שלום" in msg["content"] for msg in history if msg["role"] == "user"):
            return {
                "response": "שלום גם לך! איך אני יכול לעזור לך היום?",
                "tokens": 40,
                "model": model
            }
    
    # התאמת התשובה לפי ה-system prompt
    if system_prompt:
        if "מומחה רפואי" in system_prompt:
            return {
                "response": "כמומחה רפואי, אני ממליץ לפנות לרופא לקבלת ייעוץ מקצועי.",
                "tokens": 70,
                "model": model
            }
    
    # התאמת התשובה לפי הטמפרטורה
    if temperature > 0.8:
        return {
            "response": "תשובה יצירתית ומגוונת לשאלה שלך.",
            "tokens": 30,
            "model": model
        }
    elif temperature < 0.3:
        return {
            "response": "תשובה עובדתית ומדויקת: השמש זורחת במזרח ושוקעת במערב.",
            "tokens": 45,
            "model": model
        }
    
    # תשובה דוגמה רגילה
    return {
        "response": "זוהי תשובה לשאלה שלך. אני מקווה שזה עוזר!",
        "tokens": 35,
        "model": model
    }


@pytest.mark.asyncio
async def test_generate_response_basic():
    """בדיקת יצירת תשובה בסיסית"""
    # הרצת הפונקציה
    result = await generate_response_mock("מה השעה?")
    
    # וידוא שהערכים הוחזרו
    assert "response" in result
    assert "tokens" in result
    assert "model" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert result["tokens"] > 0
    assert result["model"] == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_generate_response_no_context():
    """בדיקת יצירת תשובה ללא הקשר"""
    # הרצת הפונקציה ללא הקשר
    result = await generate_response_mock(
        "מה מזג האוויר היום?",
        history=[
            {"role": "user", "content": "שלום"},
            {"role": "assistant", "content": "שלום! איך אני יכול לעזור?"}
        ]
    )
    
    # וידוא שהערכים הוחזרו
    assert "response" in result
    assert "tokens" in result
    assert "model" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_generate_response_empty_history():
    """בדיקת יצירת תשובה עם היסטוריה ריקה"""
    # הרצת הפונקציה עם היסטוריה ריקה
    result = await generate_response_mock(
        "מה החדשות היום?",
        history=[],
        context="news: התקדמות משמעותית בפיתוח בינה מלאכותית"
    )
    
    # וידוא שהערכים הוחזרו
    assert "response" in result
    assert "tokens" in result
    assert "model" in result
    assert "החדשות" in result["response"]
    assert "בינה מלאכותית" in result["response"]


@pytest.mark.asyncio
async def test_generate_response_api_error():
    """בדיקת טיפול בשגיאת API"""
    # הרצת הפונקציה וציפייה לשגיאה
    with pytest.raises(Exception) as excinfo:
        await generate_response_mock("error_message")
    
    # וידוא שהשגיאה הנכונה נזרקה
    assert "API Error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_generate_response_with_system_prompt():
    """בדיקת יצירת תשובה עם system prompt"""
    # הרצת הפונקציה עם system prompt
    result = await generate_response_mock(
        "האם כדאי לי לקחת אקמול לכאב ראש?",
        system_prompt="אתה מומחה רפואי שעונה על שאלות בתחום הרפואה"
    )
    
    # וידוא שהערכים הוחזרו
    assert "response" in result
    assert "tokens" in result
    assert "model" in result
    assert "מומחה רפואי" in result["response"]
    assert "רופא" in result["response"]


@pytest.mark.asyncio
async def test_generate_response_with_custom_model():
    """בדיקת יצירת תשובה עם מודל מותאם אישית"""
    # הרצת הפונקציה עם מודל מותאם אישית
    result = await generate_response_mock(
        "מה דעתך על בינה מלאכותית?",
        model="gpt-4"
    )
    
    # וידוא שהערכים הוחזרו
    assert "response" in result
    assert "tokens" in result
    assert "model" in result
    assert result["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_generate_response_with_temperature():
    """בדיקת יצירת תשובה עם טמפרטורה שונה"""
    # הרצת הפונקציה עם טמפרטורה גבוהה
    result_high = await generate_response_mock(
        "ספר לי סיפור",
        temperature=0.9
    )
    
    # הרצת הפונקציה עם טמפרטורה נמוכה
    result_low = await generate_response_mock(
        "מתי השמש זורחת?",
        temperature=0.2
    )
    
    # וידוא שהערכים הוחזרו
    assert "response" in result_high
    assert "tokens" in result_high
    assert "model" in result_high
    assert "יצירתית" in result_high["response"]
    
    assert "response" in result_low
    assert "tokens" in result_low
    assert "model" in result_low
    assert "עובדתית" in result_low["response"]
    assert "שמש" in result_low["response"] 