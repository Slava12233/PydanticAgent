"""
מודול לניהול משוב וניתוח
"""
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
import logfire

from src.database import db
from src.database.models import Message, User

class FeedbackManager:
    """מחלקה לניהול משוב וניתוח"""
    
    async def log_interaction(self, user_message: str, response: str, task_type: str, intent_type: str) -> None:
        """
        תיעוד אינטראקציה עם המשתמש
        
        Args:
            user_message: הודעת המשתמש
            response: תשובת הבוט
            task_type: סוג המשימה
            intent_type: סוג הכוונה
        """
        try:
            log_data = {
                "user_message": user_message[:100],  # רק 100 תווים ראשונים
                "response_length": len(response),
                "task_type": task_type,
                "intent_type": intent_type,
                "timestamp": datetime.now().isoformat()
            }
            logfire.info("interaction_logged", **log_data)
        except Exception as e:
            logfire.error("log_interaction_error", error=str(e))
    
    async def handle_feedback(self, user_id: int, message_id: int, feedback: str, original_message: str) -> None:
        """
        טיפול במשוב מהמשתמש
        
        Args:
            user_id: מזהה המשתמש
            message_id: מזהה ההודעה
            feedback: המשוב
            original_message: ההודעה המקורית
        """
        try:
            async with db.get_session() as session:
                # שמירת המשוב במסד הנתונים
                message = Message(
                    user_id=user_id,
                    content=feedback,
                    direction='incoming',
                    metadata={
                        'type': 'feedback',
                        'original_message_id': message_id,
                        'original_message': original_message
                    }
                )
                session.add(message)
                await session.commit()
                
                # תיעוד המשוב
                log_data = {
                    "user_id": user_id,
                    "message_id": message_id,
                    "feedback": feedback[:100],  # רק 100 תווים ראשונים
                    "timestamp": datetime.now().isoformat()
                }
                logfire.info("feedback_received", **log_data)
                
        except Exception as e:
            logfire.error("handle_feedback_error", error=str(e))
    
    async def generate_report(self, report_type: str = "weekly") -> str:
        """
        יצירת דוח סטטיסטי
        
        Args:
            report_type: סוג הדוח ("daily", "weekly", "monthly")
            
        Returns:
            דוח בפורמט מחרוזת
        """
        try:
            # קביעת טווח התאריכים לדוח
            now = datetime.now()
            if report_type == "daily":
                start_date = now - timedelta(days=1)
            elif report_type == "weekly":
                start_date = now - timedelta(weeks=1)
            else:  # monthly
                start_date = now - timedelta(days=30)
            
            async with db.get_session() as session:
                # קבלת סטטיסטיקות בסיסיות
                total_messages = await session.scalar(
                    db.select(db.func.count(Message.id))
                    .where(Message.created_at >= start_date)
                )
                
                total_users = await session.scalar(
                    db.select(db.func.count(User.id))
                    .where(User.created_at >= start_date)
                )
                
                # בניית הדוח
                report = [
                    f"דוח {report_type} - {now.strftime('%Y-%m-%d')}",
                    "=" * 40,
                    f"סה\"כ הודעות: {total_messages}",
                    f"משתמשים חדשים: {total_users}",
                    "=" * 40
                ]
                
                return "\n".join(report)
                
        except Exception as e:
            logfire.error("generate_report_error", error=str(e))
            return "לא ניתן ליצור דוח כרגע. אנא נסה שוב מאוחר יותר."
    
    async def update_keywords(self, min_score: float = 0.5) -> str:
        """
        עדכון מילות מפתח לזיהוי כוונות
        
        Args:
            min_score: ציון מינימלי לכלול מילת מפתח
            
        Returns:
            סיכום העדכון
        """
        try:
            async with db.get_session() as session:
                # קבלת כל ההודעות מהשבוע האחרון
                week_ago = datetime.now() - timedelta(weeks=1)
                messages = await session.execute(
                    db.select(Message)
                    .where(Message.created_at >= week_ago)
                )
                messages = messages.scalars().all()
                
                # ניתוח ההודעות ועדכון מילות המפתח
                from src.tools.intent import update_intent_keywords
                updated = await update_intent_keywords(
                    [msg.content for msg in messages],
                    min_score=min_score
                )
                
                return f"עודכנו {updated} מילות מפתח חדשות"
                
        except Exception as e:
            logfire.error("update_keywords_error", error=str(e))
            return "לא ניתן לעדכן מילות מפתח כרגע. אנא נסה שוב מאוחר יותר." 