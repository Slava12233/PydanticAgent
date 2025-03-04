"""
מיגרציה להוספת טבלאות זיכרון למסד הנתונים
"""
import logging
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Table, MetaData
from alembic import op
import sqlalchemy as sa
from datetime import datetime

from src.database.models import MemoryType, MemoryPriority

# הגדרת לוגר
logger = logging.getLogger(__name__)

def upgrade():
    """
    שדרוג: הוספת טבלאות זיכרון למסד הנתונים
    """
    try:
        # בדיקה אם הטבלאות כבר קיימות
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        tables = inspector.get_table_names()
        
        # הוספת שדות חדשים לטבלת conversations
        if 'conversations' in tables:
            columns = [c["name"] for c in inspector.get_columns('conversations')]
            
            if 'context' not in columns:
                op.add_column('conversations', sa.Column('context', sa.JSON, default={}))
                logger.info("נוסף שדה 'context' לטבלת 'conversations'")
            
            if 'summary' not in columns:
                op.add_column('conversations', sa.Column('summary', sa.Text, nullable=True))
                logger.info("נוסף שדה 'summary' לטבלת 'conversations'")
        
        # הוספת שדות חדשים לטבלת messages
        if 'messages' in tables:
            columns = [c["name"] for c in inspector.get_columns('messages')]
            
            if 'metadata' not in columns:
                op.add_column('messages', sa.Column('metadata', sa.JSON, default={}))
                logger.info("נוסף שדה 'metadata' לטבלת 'messages'")
            
            if 'is_memory_processed' not in columns:
                op.add_column('messages', sa.Column('is_memory_processed', sa.Boolean, default=False))
                logger.info("נוסף שדה 'is_memory_processed' לטבלת 'messages'")
        
        # יצירת טבלת זיכרונות
        if 'conversation_memories' not in tables:
            op.create_table(
                'conversation_memories',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('conversation_id', sa.Integer, sa.ForeignKey('conversations.id'), index=True),
                sa.Column('memory_type', sa.Enum(MemoryType), nullable=False),
                sa.Column('priority', sa.Enum(MemoryPriority), default=MemoryPriority.MEDIUM),
                sa.Column('content', sa.Text, nullable=False),
                sa.Column('embedding', sa.ARRAY(sa.Float), nullable=True),
                sa.Column('context', sa.Text, nullable=True),
                sa.Column('source_message_ids', sa.ARRAY(sa.Integer)),
                sa.Column('metadata', sa.JSON, default={}),
                sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('last_accessed', sa.DateTime, default=datetime.utcnow),
                sa.Column('access_count', sa.Integer, default=0),
                sa.Column('relevance_score', sa.Float, default=1.0),
                sa.Column('is_active', sa.Boolean, default=True)
            )
            
            # הוספת אינדקסים
            op.create_index(
                'ix_memories_type_priority',
                'conversation_memories',
                ['memory_type', 'priority']
            )
            op.create_index(
                'ix_memories_relevance',
                'conversation_memories',
                [sa.text('relevance_score DESC')]
            )
            
            logger.info("נוצרה טבלת 'conversation_memories' עם האינדקסים שלה")
            
    except Exception as e:
        logger.error(f"שגיאה בהוספת טבלאות זיכרון: {str(e)}")
        raise

def downgrade():
    """
    שחזור: הסרת טבלאות זיכרון ממסד הנתונים
    """
    try:
        # הסרת טבלת הזיכרונות
        op.drop_table('conversation_memories')
        logger.info("הוסרה טבלת 'conversation_memories'")
        
        # הסרת שדות מטבלת messages
        op.drop_column('messages', 'metadata')
        op.drop_column('messages', 'is_memory_processed')
        logger.info("הוסרו שדות חדשים מטבלת 'messages'")
        
        # הסרת שדות מטבלת conversations
        op.drop_column('conversations', 'context')
        op.drop_column('conversations', 'summary')
        logger.info("הוסרו שדות חדשים מטבלת 'conversations'")
        
    except Exception as e:
        logger.error(f"שגיאה בהסרת טבלאות זיכרון: {str(e)}")
        raise 