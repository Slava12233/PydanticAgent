"""
מיגרציה להוספת שדה תפקיד לטבלת משתמשים
"""
import logging
from sqlalchemy import Column, Enum, text
from alembic import op
import sqlalchemy as sa

from src.database.models import UserRole

# הגדרת לוגר
logger = logging.getLogger(__name__)

def upgrade():
    """
    שדרוג: הוספת עמודת role לטבלת users
    """
    try:
        # בדיקה אם העמודה כבר קיימת
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = inspector.get_columns('users')
        column_names = [column['name'] for column in columns]
        
        if 'role' not in column_names:
            # הוספת העמודה
            op.add_column('users', 
                Column('role', 
                    Enum(UserRole, name='user_role_enum'),
                    server_default=text("'USER'"),
                    nullable=False
                )
            )
            logger.info("נוספה עמודת 'role' לטבלת 'users'")
        else:
            logger.info("עמודת 'role' כבר קיימת בטבלת 'users'")
            
        # עדכון המשתמש הראשי להיות מנהל
        from src.core.config import ADMIN_USER_ID
        if ADMIN_USER_ID:
            conn.execute(
                text(f"UPDATE users SET role = 'ADMIN' WHERE id = {ADMIN_USER_ID}")
            )
            logger.info(f"עודכן תפקיד המשתמש עם מזהה {ADMIN_USER_ID} למנהל")
            
    except Exception as e:
        logger.error(f"שגיאה בהוספת עמודת 'role': {str(e)}")
        raise

def downgrade():
    """
    שחזור: הסרת עמודת role מטבלת users
    """
    try:
        # בדיקה אם העמודה קיימת
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = inspector.get_columns('users')
        column_names = [column['name'] for column in columns]
        
        if 'role' in column_names:
            # הסרת העמודה
            op.drop_column('users', 'role')
            logger.info("הוסרה עמודת 'role' מטבלת 'users'")
        else:
            logger.info("עמודת 'role' אינה קיימת בטבלת 'users'")
            
    except Exception as e:
        logger.error(f"שגיאה בהסרת עמודת 'role': {str(e)}")
        raise 