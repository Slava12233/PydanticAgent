"""
מודול לניהול סטטיסטיקות מערכת
"""

from typing import Dict
from datetime import datetime, time
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User
from src.models.documents import Document
from src.models.messages import Message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class StatsManager:
    """מחלקה לניהול סטטיסטיקות מערכת"""
    
    @staticmethod
    async def get_system_stats(session: AsyncSession) -> Dict:
        """קבלת סטטיסטיקות מערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            מילון עם הסטטיסטיקות
        """
        try:
            # מספר משתמשים
            user_count_result = await session.execute(select(func.count()).select_from(User))
            user_count = user_count_result.scalar_one()
            
            # מספר מסמכים
            doc_count_result = await session.execute(select(func.count()).select_from(Document))
            doc_count = doc_count_result.scalar_one()
            
            # מספר הודעות
            message_count_result = await session.execute(select(func.count()).select_from(Message))
            message_count = message_count_result.scalar_one()
            
            # הודעות היום
            today = datetime.now().date()
            today_start = datetime.combine(today, time.min)
            today_end = datetime.combine(today, time.max)
            
            today_messages_result = await session.execute(
                select(func.count()).select_from(Message).where(
                    Message.timestamp.between(today_start, today_end)
                )
            )
            today_messages = today_messages_result.scalar_one()
            
            # משתמשים פעילים היום
            active_users_result = await session.execute(
                select(func.count(func.distinct(Message.user_id))).select_from(Message).where(
                    Message.timestamp.between(today_start, today_end)
                )
            )
            active_users = active_users_result.scalar_one()
            
            # מסמכים שנוספו היום
            new_docs_result = await session.execute(
                select(func.count()).select_from(Document).where(
                    Document.created_at.between(today_start, today_end)
                )
            )
            new_docs = new_docs_result.scalar_one()
            
            return {
                "total_stats": {
                    "users": user_count,
                    "documents": doc_count,
                    "messages": message_count
                },
                "today_stats": {
                    "messages": today_messages,
                    "active_users": active_users,
                    "new_documents": new_docs
                }
            }
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת סטטיסטיקות מערכת: {str(e)}")
            raise
            
    @staticmethod
    async def get_user_stats(user_id: int, session: AsyncSession) -> Dict:
        """קבלת סטטיסטיקות משתמש
        
        Args:
            user_id: מזהה המשתמש
            session: סשן של מסד הנתונים
            
        Returns:
            מילון עם הסטטיסטיקות
        """
        try:
            # מספר הודעות
            message_count_result = await session.execute(
                select(func.count()).select_from(Message).where(Message.user_id == user_id)
            )
            message_count = message_count_result.scalar_one()
            
            # מספר מסמכים
            doc_count_result = await session.execute(
                select(func.count()).select_from(Document).where(Document.user_id == user_id)
            )
            doc_count = doc_count_result.scalar_one()
            
            # הודעות היום
            today = datetime.now().date()
            today_start = datetime.combine(today, time.min)
            today_end = datetime.combine(today, time.max)
            
            today_messages_result = await session.execute(
                select(func.count()).select_from(Message).where(
                    Message.user_id == user_id,
                    Message.timestamp.between(today_start, today_end)
                )
            )
            today_messages = today_messages_result.scalar_one()
            
            # מסמכים שנוספו היום
            new_docs_result = await session.execute(
                select(func.count()).select_from(Document).where(
                    Document.user_id == user_id,
                    Document.created_at.between(today_start, today_end)
                )
            )
            new_docs = new_docs_result.scalar_one()
            
            return {
                "total_stats": {
                    "messages": message_count,
                    "documents": doc_count
                },
                "today_stats": {
                    "messages": today_messages,
                    "new_documents": new_docs
                }
            }
            
        except Exception as e:
            logger.error(f"שגיאה בקבלת סטטיסטיקות משתמש {user_id}: {str(e)}")
            raise 