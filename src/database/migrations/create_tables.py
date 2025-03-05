"""
מיגרציה ליצירת הטבלאות הבסיסיות במסד הנתונים
"""
import logging
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Table, MetaData
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from src.database.models import UserRole

# הגדרת לוגר
logger = logging.getLogger(__name__)

def upgrade():
    """
    שדרוג: יצירת הטבלאות הבסיסיות במסד הנתונים
    """
    try:
        # בדיקה אם הטבלאות כבר קיימות
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        tables = inspector.get_table_names()
        
        # יצירת טבלת משתמשים
        if 'users' not in tables:
            op.create_table(
                'users',
                sa.Column('id', sa.BigInteger, primary_key=True),
                sa.Column('telegram_id', sa.BigInteger, unique=True),
                sa.Column('username', sa.String, nullable=True),
                sa.Column('first_name', sa.String, nullable=True),
                sa.Column('last_name', sa.String, nullable=True),
                sa.Column('role', sa.Enum(UserRole), default=UserRole.USER),
                sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('last_active', sa.DateTime, default=datetime.utcnow)
            )
            logger.info("נוצרה טבלת 'users'")
        else:
            logger.info("טבלת 'users' כבר קיימת")
        
        # יצירת טבלת שיחות
        if 'conversations' not in tables:
            op.create_table(
                'conversations',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id'), index=True),
                sa.Column('title', sa.String, nullable=True),
                sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('updated_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('is_active', sa.Boolean, default=True),
                sa.Column('context', sa.JSON, default={}),
                sa.Column('summary', sa.Text, nullable=True)
            )
            logger.info("נוצרה טבלת 'conversations'")
        else:
            logger.info("טבלת 'conversations' כבר קיימת")
        
        # יצירת טבלת הודעות
        if 'messages' not in tables:
            op.create_table(
                'messages',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('conversation_id', sa.Integer, sa.ForeignKey('conversations.id'), index=True),
                sa.Column('role', sa.String),
                sa.Column('content', sa.Text),
                sa.Column('timestamp', sa.DateTime, default=datetime.utcnow),
                sa.Column('embedding', sa.ARRAY(sa.Float), nullable=True),
                sa.Column('message_metadata', sa.JSON, default={}),
                sa.Column('is_memory_processed', sa.Boolean, default=False)
            )
            logger.info("נוצרה טבלת 'messages'")
        else:
            logger.info("טבלת 'messages' כבר קיימת")
        
        # יצירת טבלת הגדרות בוט
        if 'bot_settings' not in tables:
            op.create_table(
                'bot_settings',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id'), unique=True),
                sa.Column('language', sa.String, default='he'),
                sa.Column('timezone', sa.String, default='Asia/Jerusalem'),
                sa.Column('currency', sa.String, default='ILS'),
                sa.Column('theme', sa.String, default='light'),
                sa.Column('privacy_level', sa.String, default='medium'),
                sa.Column('notification_level', sa.String, default='all'),
                sa.Column('api_keys', sa.JSON, default={}),
                sa.Column('preferences', sa.JSON, default={}),
                sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('updated_at', sa.DateTime, default=datetime.utcnow)
            )
            logger.info("נוצרה טבלת 'bot_settings'")
        else:
            logger.info("טבלת 'bot_settings' כבר קיימת")
            
    except Exception as e:
        logger.error(f"שגיאה ביצירת טבלאות בסיסיות: {str(e)}")
        raise 