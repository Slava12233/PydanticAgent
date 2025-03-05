"""
בדיקות יחידה ל-Conversation Agent
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.conversation_agent import ConversationAgent
from src.database.database import db
from src.database.models import User, BotSettings, Message, Conversation
from src.services.conversation_service import ConversationService
from src.services.learning_service import LearningService
from src.services.memory_service import memory_service

@pytest_asyncio.fixture
async def test_user():
    """פיקסצ'ר ליצירת משתמש בדיקה"""
    async with db.get_session() as session:
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        session.add(user)
        await session.commit()
        
        # יצירת הגדרות למשתמש
        settings = BotSettings(
            user_id=user.id,
            preferences={
                "response_style": "formal",
                "language": "he",
                "interests": ["טכנולוגיה", "מדע"]
            }
        )
        session.add(settings)
        await session.commit()
        
        return user

@pytest_asyncio.fixture
async def conversation_agent():
    """פיקסצ'ר ליצירת Agent לבדיקות"""
    # אתחול הדאטהבייס
    db.init_db(recreate_tables=True)
    
    # יצירת מופע של ה-Agent
    agent = ConversationAgent(
        conversation_service=ConversationService(),
        learning_service=LearningService()
    )
    
    yield agent
    
    # ניקוי אחרי כל בדיקה
    async with db.get_session() as session:
        await session.execute("DELETE FROM messages")
        await session.execute("DELETE FROM conversations")
        await session.execute("DELETE FROM bot_settings")
        await session.execute("DELETE FROM users")
        await session.commit()
    await db.close_all_connections()

@pytest.mark.asyncio
async def test_understand_intent(conversation_agent, test_user):
    """בדיקת הבנת כוונת המשתמש"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # בדיקת כוונות שונות
    test_cases = [
        ("מה מזג האוויר היום?", "weather"),
        ("תוסיף מוצר חדש לחנות", "add_product"),
        ("אני רוצה לראות את ההזמנות שלי", "view_orders"),
        ("תודה רבה!", "gratitude")
    ]
    
    for message, expected_intent in test_cases:
        intent = await conversation_agent.understand_intent(message, test_user.id)
        assert intent == expected_intent

@pytest.mark.asyncio
async def test_generate_response(conversation_agent, test_user):
    """בדיקת יצירת תשובה מותאמת אישית"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
        
        # הוספת הודעות קודמות להקשר
        messages = [
            ("אני מתעניין בבינה מלאכותית", "user"),
            ("זה נושא מרתק! במה בדיוק אתה מתעניין?", "assistant")
        ]
        
        for content, role in messages:
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(message)
        await session.commit()
    
    # בדיקת יצירת תשובה
    response = await conversation_agent.generate_response(
        "אני רוצה ללמוד על רשתות נוירונים",
        test_user.id,
        conversation.id
    )
    
    # בדיקות
    assert response is not None
    assert len(response) > 0
    assert any(word in response.lower() for word in ["רשתות", "נוירונים", "למידה"])
    assert response.endswith("?") or response.endswith(".") or response.endswith("!")

@pytest.mark.asyncio
async def test_maintain_context(conversation_agent, test_user):
    """בדיקת שמירת הקשר השיחה"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # סימולציה של שיחה
    messages = [
        "שלום, אני מחפש מידע על מכוניות חשמליות",
        "איזה דגמים מעניינים אותך?",
        "טסלה מודל 3",
        "מה הטווח נסיעה שלה?"
    ]
    
    responses = []
    for message in messages:
        response = await conversation_agent.generate_response(
            message,
            test_user.id,
            conversation.id
        )
        responses.append(response)
    
    # בדיקה שהתשובות מתייחסות להקשר
    assert any("טסלה" in response for response in responses)
    assert any("חשמלי" in response for response in responses)
    assert any("טווח" in response for response in responses)

@pytest.mark.asyncio
async def test_learn_from_interaction(conversation_agent, test_user):
    """בדיקת למידה מאינטראקציות"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # סימולציה של כמה אינטראקציות
    interactions = [
        ("אני אוהב לקרוא ספרי מדע בדיוני", "user"),
        ("איזה סופרים אתה אוהב?", "assistant"),
        ("אייזק אסימוב ופיליפ דיק", "user"),
        ("אלו סופרים מעולים! איזה ספר שלהם אהבת במיוחד?", "assistant")
    ]
    
    for content, role in interactions:
        await conversation_agent.process_message(
            content,
            role,
            test_user.id,
            conversation.id
        )
    
    # בדיקת העדפות שנלמדו
    async with db.get_session() as session:
        settings = await session.get(BotSettings, test_user.id)
        assert settings is not None
        assert "interests" in settings.preferences
        assert any("ספרות" in interest or "מדע בדיוני" in interest 
                  for interest in settings.preferences["interests"])

@pytest.mark.asyncio
async def test_handle_complex_queries(conversation_agent, test_user):
    """בדיקת טיפול בשאילתות מורכבות"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # בדיקת שאילתות מורכבות
    complex_queries = [
        "מה ההבדל בין למידת מכונה עמוקה ולמידת מכונה רגילה, ואיך זה קשור לבינה מלאכותית?",
        "האם תוכל להסביר לי את התהליך של רכישת מוצר מההתחלה ועד הסוף, כולל תשלום ומשלוח?",
        "אני מחפש המלצות לספרים על היסטוריה של המדע, במיוחד בתחום הפיזיקה והמתמטיקה"
    ]
    
    for query in complex_queries:
        response = await conversation_agent.generate_response(
            query,
            test_user.id,
            conversation.id
        )
        
        # בדיקות
        assert response is not None
        assert len(response) > 100  # תשובה מפורטת
        assert response.count(".") > 1  # מספר משפטים
        assert not response.startswith(("כן", "לא"))  # לא תשובה פשוטה

@pytest.mark.asyncio
async def test_handle_emotional_responses(conversation_agent, test_user):
    """בדיקת טיפול בתגובות רגשיות"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # בדיקת תגובות רגשיות
    emotional_messages = [
        "אני ממש מתוסכל מהמצב",
        "אני כל כך שמח שהצלחתי!",
        "אני מרגיש לחוץ מאוד לקראת המבחן",
        "אני מאוכזב מהתוצאות"
    ]
    
    for message in emotional_messages:
        response = await conversation_agent.generate_response(
            message,
            test_user.id,
            conversation.id
        )
        
        # בדיקות
        assert response is not None
        assert any(word in response for word in ["מבין", "מרגיש", "שמח", "מצטער", "תקווה"])
        assert "😊" in response or "❤️" in response or "🤗" in response  # שימוש באימוג'ים

@pytest.mark.asyncio
async def test_handle_task_management(conversation_agent, test_user):
    """בדיקת ניהול משימות"""
    # יצירת שיחה
    async with db.get_session() as session:
        conversation = Conversation(
            user_id=test_user.id,
            title="שיחת בדיקה"
        )
        session.add(conversation)
        await session.commit()
    
    # בדיקת משימות שונות
    tasks = [
        "תזכיר לי מחר בבוקר להתקשר לרופא",
        "תוסיף לרשימת הקניות חלב ולחם",
        "תקבע לי פגישה עם יוסי ביום ראשון",
        "תבדוק מה סטטוס ההזמנה שלי"
    ]
    
    for task in tasks:
        response = await conversation_agent.generate_response(
            task,
            test_user.id,
            conversation.id
        )
        
        # בדיקות
        assert response is not None
        assert any(word in response for word in ["בסדר", "אוסיף", "אזכיר", "אבדוק"])
        assert "✅" in response or "📝" in response or "⏰" in response  # שימוש באימוג'ים מתאימים 