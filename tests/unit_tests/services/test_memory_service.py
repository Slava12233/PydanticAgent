"""
בדיקות יחידה לשירות הזיכרון
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from src.services.memory_service import MemoryService
from src.database.database import db

@pytest_asyncio.fixture
async def memory_service():
    """פיקסצ'ר ליצירת מופע של Memory Service לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת שירות חדש
    service = MemoryService()
    
    yield service
    
    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute(text("DELETE FROM memories"))
        await session.commit()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_process_message(memory_service):
    """בדיקת שמירת זיכרון חדש"""
    # שמירת הודעה בזיכרון
    message = "זוהי הודעת בדיקה"
    await memory_service.process_message(message, role="user")
    
    # בדיקה שההודעה נשמרה
    async with db.get_session() as session:
        result = await session.execute(text("SELECT * FROM memories"))
        memories = result.fetchall()
        
        assert len(memories) == 1
        assert memories[0].content == message
        assert memories[0].role == "user"
        assert memories[0].embedding is not None

@pytest.mark.asyncio
async def test_get_relevant_memories(memory_service):
    """בדיקת אחזור זיכרונות רלוונטיים"""
    # שמירת מספר הודעות בזיכרון
    messages = [
        ("מה מזג האוויר היום?", "user"),
        ("היום יהיה חם ושמשי", "assistant"),
        ("תודה רבה על המידע", "user"),
        ("מה התחזית למחר?", "user")
    ]
    
    for content, role in messages:
        await memory_service.process_message(content, role)
    
    # חיפוש זיכרונות רלוונטיים
    results = await memory_service.get_relevant_memories("מזג אוויר")
    
    assert len(results) > 0
    assert any("מזג האוויר" in memory["content"] for memory in results)
    assert all(isinstance(memory["similarity"], float) for memory in results)

@pytest.mark.asyncio
async def test_memory_ordering(memory_service):
    """בדיקת סדר הזיכרונות לפי רלוונטיות"""
    # שמירת הודעות עם תוכן דומה בדרגות שונות
    messages = [
        ("משהו לא קשור", "user"),
        ("מזג האוויר היום נעים", "user"),
        ("מזג האוויר מחר יהיה גשום", "assistant"),
        ("איך מזג האוויר אצלכם?", "user")
    ]
    
    for content, role in messages:
        await memory_service.process_message(content, role)
    
    # חיפוש זיכרונות
    results = await memory_service.get_relevant_memories("מזג אוויר")
    
    # בדיקה שהתוצאות מסודרות לפי רלוונטיות
    assert len(results) > 1
    for i in range(len(results) - 1):
        assert results[i]["similarity"] >= results[i + 1]["similarity"]

@pytest.mark.asyncio
async def test_memory_filtering(memory_service):
    """בדיקת סינון זיכרונות לפי סף דמיון"""
    # שמירת הודעות
    messages = [
        ("היום יום שני", "user"),
        ("מחר יום שלישי", "assistant"),
        ("מה השעה עכשיו?", "user"),
        ("השעה שתיים", "assistant")
    ]
    
    for content, role in messages:
        await memory_service.process_message(content, role)
    
    # חיפוש עם סף דמיון גבוה
    results = await memory_service.get_relevant_memories(
        "מה היום?",
        min_similarity=0.8
    )
    
    # בדיקה שרק זיכרונות רלוונטיים מאוד הוחזרו
    assert all(memory["similarity"] >= 0.8 for memory in results)

@pytest.mark.asyncio
async def test_memory_limit(memory_service):
    """בדיקת הגבלת מספר הזיכרונות המוחזרים"""
    # שמירת הרבה הודעות
    messages = [f"הודעה מספר {i}" for i in range(10)]
    for message in messages:
        await memory_service.process_message(message, "user")
    
    # בדיקת הגבלת תוצאות
    limit = 3
    results = await memory_service.get_relevant_memories("הודעה", limit=limit)
    
    assert len(results) <= limit

@pytest.mark.asyncio
async def test_error_handling(memory_service):
    """בדיקת טיפול בשגיאות"""
    # ניסיון לשמור הודעה ריקה
    await memory_service.process_message("", "user")
    
    # בדיקה שלא נשמר כלום
    async with db.get_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM memories"))
        count = result.scalar()
        assert count == 0
    
    # ניסיון לחפש עם שאילתה ריקה
    results = await memory_service.get_relevant_memories("")
    assert len(results) == 0 