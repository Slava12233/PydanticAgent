"""
שירות למידה מתמשכת והתאמה אישית
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict

from openai import AsyncOpenAI
from sqlalchemy import text

from src.database.database import db
from src.database.models import (
    User, Message, Conversation, ConversationMemory,
    MemoryType, MemoryPriority, BotSettings
)

logger = logging.getLogger(__name__)

class LearningService:
    """שירות למידה מתמשכת"""
    
    def __init__(self):
        """אתחול השירות"""
        self.openai_client = AsyncOpenAI()
        
        # הגדרות למידה
        self.pattern_confidence_threshold = 0.7  # סף ביטחון לזיהוי דפוסים
        self.min_pattern_occurrences = 3  # מספר מינימלי של הופעות לדפוס
        self.preference_update_weight = 0.2  # משקל עדכון העדפות
        self.max_patterns_per_user = 50  # מספר מקסימלי של דפוסים לשמירה למשתמש
    
    async def analyze_user_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        ניתוח דפוסי התנהגות של משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            דפוסים שזוהו
        """
        try:
            async with db.get_session() as session:
                # קבלת היסטוריית הודעות המשתמש
                result = await session.execute(
                    text("""
                    SELECT m.content, m.role, m.timestamp,
                           c.context, c.summary
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = :user_id
                    ORDER BY m.timestamp DESC
                    LIMIT 100
                    """),
                    {"user_id": user_id}
                )
                messages = result.fetchall()
                
                if not messages:
                    return {}
                
                # ניתוח דפוסים באמצעות GPT-4
                analysis_text = "\n".join([
                    f"[{msg.timestamp.isoformat()}] {msg.role}: {msg.content}"
                    for msg in messages
                ])
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": """
                            נתח את דפוסי ההתנהגות של המשתמש.
                            זהה:
                            1. נושאים מועדפים
                            2. זמני פעילות
                            3. סגנון תקשורת
                            4. העדפות שפה
                            5. תחומי עניין
                            6. דפוסי שאלות חוזרים
                            
                            החזר את התוצאה כ-JSON עם השדות הבאים:
                            - preferred_topics: רשימת נושאים מועדפים עם משקלות (0-1)
                            - active_hours: שעות פעילות מועדפות
                            - communication_style: מאפייני סגנון התקשורת
                            - language_preferences: העדפות שפה ומונחים
                            - interests: תחומי עניין עם משקלות (0-1)
                            - recurring_patterns: דפוסי שאלות חוזרים
                            - greeting_patterns: דפוסי ברכה חוזרים
                            """
                        },
                        {
                            "role": "user",
                            "content": analysis_text
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                
                patterns = json.loads(response.choices[0].message.content)
                
                # שמירת הדפוסים בהגדרות המשתמש
                await self._update_user_preferences(user_id, patterns, session)
                
                return patterns
                
        except Exception as e:
            logger.error(f"שגיאה בניתוח דפוסי משתמש: {str(e)}")
            return {}
    
    async def update_memory_weights(self, user_id: int) -> None:
        """
        עדכון משקלי זיכרונות לפי דפוסי שימוש
        
        Args:
            user_id: מזהה המשתמש
        """
        try:
            async with db.get_session() as session:
                # קבלת העדפות המשתמש
                user_settings = await session.get(BotSettings, user_id)
                if not user_settings or not user_settings.preferences:
                    return
                
                preferences = user_settings.preferences
                
                # עדכון משקלי זיכרונות לפי העדפות
                if "preferred_topics" in preferences:
                    for topic, weight in preferences["preferred_topics"].items():
                        await session.execute(
                            text("""
                            UPDATE conversation_memories
                            SET relevance_score = relevance_score * :weight
                            FROM conversations c
                            WHERE 
                                conversation_memories.conversation_id = c.id
                                AND c.user_id = :user_id
                                AND conversation_memories.metadata->>'topics' ? :topic
                            """),
                            {
                                "user_id": user_id,
                                "topic": topic,
                                "weight": weight
                            }
                        )
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"שגיאה בעדכון משקלי זיכרון: {str(e)}")
    
    async def adapt_response_style(
        self,
        user_id: int,
        original_response: str
    ) -> str:
        """
        התאמת סגנון התשובה להעדפות המשתמש
        
        Args:
            user_id: מזהה המשתמש
            original_response: התשובה המקורית
            
        Returns:
            תשובה מותאמת אישית
        """
        try:
            async with db.get_session() as session:
                # קבלת העדפות המשתמש
                user_settings = await session.get(BotSettings, user_id)
                if not user_settings or not user_settings.preferences:
                    return original_response
                
                preferences = user_settings.preferences
                
                # התאמת התשובה באמצעות GPT
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""
                            התאם את התשובה לסגנון המשתמש:
                            - סגנון תקשורת: {preferences.get('response_style', 'formal')}
                            - שפה: {preferences.get('language', 'he')}
                            - תחומי עניין: {', '.join(preferences.get('interests', []))}
                            
                            שמור על:
                            1. אותו מידע מהתשובה המקורית
                            2. התאמה לסגנון המועדף
                            3. שימוש במונחים מתחומי העניין
                            4. שמירה על טון מתאים
                            """
                        },
                        {
                            "role": "user",
                            "content": f"התאם את התשובה הבאה: {original_response}"
                        }
                    ]
                )
                
                adapted_response = response.choices[0].message.content
                return adapted_response.strip()
                
        except Exception as e:
            logger.error(f"שגיאה בהתאמת סגנון תשובה: {str(e)}")
            return original_response
    
    async def _update_user_preferences(
        self,
        user_id: int,
        new_patterns: Dict[str, Any],
        session
    ) -> None:
        """
        עדכון העדפות המשתמש
        
        Args:
            user_id: מזהה המשתמש
            new_patterns: דפוסים חדשים שזוהו
            session: סשן מסד הנתונים
        """
        try:
            # קבלת או יצירת הגדרות משתמש
            user_settings = await session.get(BotSettings, user_id)
            if not user_settings:
                user_settings = BotSettings(user_id=user_id)
                session.add(user_settings)
            
            current_preferences = user_settings.preferences or {}
            
            # מיזוג העדפות קיימות עם חדשות
            for category, new_values in new_patterns.items():
                if category not in current_preferences:
                    current_preferences[category] = new_values
                elif isinstance(new_values, dict):
                    # עדכון משקלות קיימים
                    for key, value in new_values.items():
                        if key in current_preferences[category]:
                            current_preferences[category][key] = (
                                current_preferences[category][key] * (1 - self.preference_update_weight) +
                                value * self.preference_update_weight
                            )
                        else:
                            current_preferences[category][key] = value
                else:
                    # החלפת ערך פשוט
                    current_preferences[category] = new_values
            
            # הגבלת מספר הדפוסים
            for category in current_preferences:
                if isinstance(current_preferences[category], dict):
                    if len(current_preferences[category]) > self.max_patterns_per_user:
                        # השארת הדפוסים עם המשקלות הגבוהים ביותר
                        sorted_patterns = sorted(
                            current_preferences[category].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        current_preferences[category] = dict(
                            sorted_patterns[:self.max_patterns_per_user]
                        )
            
            # שמירת העדפות מעודכנות
            user_settings.preferences = current_preferences
            user_settings.updated_at = datetime.utcnow()
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון העדפות משתמש: {str(e)}")
            await session.rollback()

# יצירת מופע יחיד של השירות
learning_service = LearningService() 