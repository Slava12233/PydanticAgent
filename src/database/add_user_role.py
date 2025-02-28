"""
סקריפט להוספת עמודת role לטבלת users
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text, Column, Enum, inspect

# הוספת הספרייה הראשית לנתיב החיפוש
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.models import UserRole, User
from src.core.config import DATABASE_URL, ADMIN_USER_ID

# הגדרת לוגר
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_user_role_column():
    """
    הוספת עמודת role לטבלת users
    """
    try:
        # יצירת חיבור למסד הנתונים
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # בדיקה אם העמודה כבר קיימת
        inspector = inspect(engine)
        columns = inspector.get_columns('users')
        column_names = [column['name'] for column in columns]
        
        if 'role' not in column_names:
            logger.info("מוסיף עמודת 'role' לטבלת 'users'...")
            
            # יצירת enum בבסיס הנתונים אם לא קיים
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                        CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'USER', 'BLOCKED');
                    END IF;
                END
                $$;
            """))
            
            # הוספת העמודה עם ערך ברירת מחדל
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role user_role_enum NOT NULL DEFAULT 'USER';
            """))
            
            logger.info("עמודת 'role' נוספה בהצלחה!")
            
            # עדכון המשתמש הראשי להיות מנהל
            if ADMIN_USER_ID:
                conn.execute(text(f"UPDATE users SET role = 'ADMIN' WHERE id = {ADMIN_USER_ID}"))
                logger.info(f"עודכן תפקיד המשתמש עם מזהה {ADMIN_USER_ID} למנהל")
        else:
            logger.info("עמודת 'role' כבר קיימת בטבלת 'users'")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"שגיאה בהוספת עמודת 'role': {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("מתחיל הוספת עמודת role לטבלת users...")
    success = add_user_role_column()
    if success:
        logger.info("התהליך הסתיים בהצלחה!")
    else:
        logger.error("התהליך נכשל!")
        sys.exit(1) 