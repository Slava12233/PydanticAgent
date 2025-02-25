# src/database/database.py
import os
from datetime import datetime
from typing import List, Tuple, Optional
import logfire
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, desc, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# הגדרת Base של SQLAlchemy
Base = declarative_base()

# מודל למסרים
class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message(user_id={self.user_id}, timestamp={self.timestamp})>"

class Database:
    def __init__(self, db_url=None):
        """אתחול הקשר למסד הנתונים"""
        if db_url is None:
            # שימוש במשתני סביבה לחיבור למסד הנתונים
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "postgres")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "SSll456456!!")
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.db_url = db_url
        self.engine = None
        self.Session = None
    
    def init_db(self):
        """אתחול מסד הנתונים - יצירת חיבור וטבלאות"""
        with logfire.span('database_init'):
            # יצירת מנוע SQLAlchemy
            self.engine = create_engine(self.db_url)
            
            # יצירת הטבלאות אם הן לא קיימות
            Base.metadata.create_all(self.engine)
            
            # יצירת session factory
            self.Session = sessionmaker(bind=self.engine)
            
            logfire.info('database_connected', engine=str(self.engine.url).split('@')[0])
    
    def save_message(self, user_id: int, message: str, response: str) -> None:
        """שמירת הודעה ותגובה במסד הנתונים"""
        with logfire.span('save_message', user_id=user_id):
            # יצירת אובייקט הודעה חדש
            new_message = Message(
                user_id=user_id,
                message=message,
                response=response
            )
            
            # שמירה במסד הנתונים
            with self.Session() as session:
                session.add(new_message)
                session.commit()
                
                # שמירת ה-ID לפני סגירת הסשן
                message_id = new_message.id
                
            # שימוש ב-ID שנשמר מראש במקום לגשת לאובייקט אחרי סגירת הסשן
            logfire.info('message_saved', user_id=user_id, message_id=message_id)
    
    def get_chat_history(self, user_id: int, limit: int = 10) -> List[dict]:
        """קבלת היסטוריית השיחה למשתמש"""
        with logfire.span('get_chat_history', user_id=user_id):
            with self.Session() as session:
                # שליפת ההודעות האחרונות בסדר כרונולוגי
                messages = session.query(Message)\
                    .filter(Message.user_id == user_id)\
                    .order_by(desc(Message.timestamp))\
                    .limit(limit)\
                    .all()
                
                # הפיכת הרשומות לפורמט המתאים להיסטוריית שיחה
                history = [{
                    'message': msg.message, 
                    'response': msg.response, 
                    'timestamp': msg.timestamp.isoformat()
                } for msg in messages]
                
                logfire.info('chat_history_retrieved', user_id=user_id, message_count=len(history))
                return history
    
    def clear_chat_history(self, user_id: int) -> None:
        """מחיקת היסטוריית השיחה למשתמש"""
        with logfire.span('clear_chat_history', user_id=user_id):
            with self.Session() as session:
                # מחיקת כל ההודעות של המשתמש
                deleted_count = session.query(Message)\
                    .filter(Message.user_id == user_id)\
                    .delete()
                
                session.commit()
                
                logfire.info('chat_history_cleared', user_id=user_id, deleted_count=deleted_count)
    
    def get_message_count(self) -> int:
        """קבלת מספר ההודעות הכולל במערכת - שימושי לסטטיסטיקות"""
        with self.Session() as session:
            count = session.query(Message).count()
            return count
    
    def get_user_count(self) -> int:
        """קבלת מספר המשתמשים הייחודיים - שימושי לסטטיסטיקות"""
        with self.Session() as session:
            # COUNT DISTINCT user_id
            count = session.query(Message.user_id).distinct().count()
            return count
            
    def close(self):
        """סגירת החיבור למסד הנתונים"""
        if self.engine:
            logfire.info('database_connection_closing')
            # אין צורך לסגור את המנוע באופן מפורש ב-SQLAlchemy
            # אבל אפשר לשחרר משאבים
            self.engine.dispose()

# יצירת מופע גלובלי של Database
db = Database() 