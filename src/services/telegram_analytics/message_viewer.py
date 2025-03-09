"""
כלי לצפייה בהודעות טלגרם השמורות במסד הנתונים
"""

import csv
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from tabulate import tabulate

from src.database.database import Database
from src.models.telegram import User, Conversation, Message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MessageViewer:
    """מחלקה לצפייה בהודעות טלגרם"""
    
    def __init__(self, db: Database):
        """אתחול המחלקה
        
        Args:
            db: מופע של מסד הנתונים
        """
        self.db = db
        
    async def get_messages(self, limit: int = 100) -> List[Dict]:
        """שליפת הודעות מהמסד נתונים
        
        Args:
            limit: מספר ההודעות המקסימלי להחזרה
            
        Returns:
            רשימת הודעות
        """
        async with self.db.session() as session:
            # שליפת הודעות עם מידע על המשתמש והשיחה
            query = """
            SELECT 
                m.id, 
                u.username, 
                u.first_name, 
                u.last_name, 
                c.title as conversation_title,
                m.role, 
                m.content, 
                m.timestamp
            FROM 
                messages m
            JOIN 
                conversations c ON m.conversation_id = c.id
            JOIN 
                users u ON c.user_id = u.id
            ORDER BY 
                m.timestamp DESC
            LIMIT :limit
            """
            
            result = await session.execute(text(query), {"limit": limit})
            
            # המרת התוצאות לרשימה של מילונים
            messages = []
            async for row in result:
                messages.append({
                    'id': row.id,
                    'username': row.username or 'אנונימי',
                    'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or 'לא ידוע',
                    'conversation': row.conversation_title,
                    'role': row.role,
                    'content': row.content[:50] + ('...' if len(row.content) > 50 else ''),
                    'timestamp': row.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return messages
            
    async def get_conversations(self) -> List[Dict]:
        """שליפת שיחות מהמסד נתונים
        
        Returns:
            רשימת שיחות
        """
        async with self.db.session() as session:
            # שליפת שיחות עם מידע על המשתמש ומספר ההודעות
            query = """
            SELECT 
                c.id, 
                u.username, 
                u.first_name, 
                u.last_name, 
                c.title,
                c.created_at,
                c.updated_at,
                c.is_active,
                COUNT(m.id) as message_count
            FROM 
                conversations c
            JOIN 
                users u ON c.user_id = u.id
            LEFT JOIN 
                messages m ON c.id = m.conversation_id
            GROUP BY 
                c.id, u.username, u.first_name, u.last_name
            ORDER BY 
                c.updated_at DESC
            """
            
            result = await session.execute(text(query))
            
            # המרת התוצאות לרשימה של מילונים
            conversations = []
            async for row in result:
                conversations.append({
                    'id': row.id,
                    'username': row.username or 'אנונימי',
                    'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or 'לא ידוע',
                    'title': row.title,
                    'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_active': 'כן' if row.is_active else 'לא',
                    'message_count': row.message_count
                })
            
            return conversations
            
    async def get_statistics(self) -> Dict:
        """קבלת סטטיסטיקות על המערכת
        
        Returns:
            מילון עם הסטטיסטיקות
        """
        async with self.db.session() as session:
            user_count = await session.scalar(text("SELECT COUNT(*) FROM users"))
            conversation_count = await session.scalar(text("SELECT COUNT(*) FROM conversations"))
            message_count = await session.scalar(text("SELECT COUNT(*) FROM messages"))
            
            return {
                'users': user_count,
                'conversations': conversation_count,
                'messages': message_count
            }
            
    async def export_messages_to_csv(self, filename: str, limit: int = 100) -> None:
        """ייצוא הודעות לקובץ CSV
        
        Args:
            filename: שם הקובץ לייצוא
            limit: מספר ההודעות המקסימלי לייצוא
        """
        messages = await self.get_messages(limit)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
            
        logger.info(f"נשמרו {len(messages)} הודעות לקובץ {filename}")
        
    def format_messages_table(self, messages: List[Dict]) -> str:
        """פורמט הודעות כטבלה
        
        Args:
            messages: רשימת הודעות
            
        Returns:
            טבלה מפורמטת
        """
        return tabulate(messages, headers='keys', tablefmt='pretty')
        
    def format_conversations_table(self, conversations: List[Dict]) -> str:
        """פורמט שיחות כטבלה
        
        Args:
            conversations: רשימת שיחות
            
        Returns:
            טבלה מפורמטת
        """
        return tabulate(conversations, headers='keys', tablefmt='pretty')
        
    def format_statistics(self, stats: Dict) -> str:
        """פורמט סטטיסטיקות
        
        Args:
            stats: מילון סטטיסטיקות
            
        Returns:
            טקסט מפורמט
        """
        return f"""סטטיסטיקות:
- מספר משתמשים: {stats['users']}
- מספר שיחות: {stats['conversations']}
- סה"כ הודעות: {stats['messages']}""" 