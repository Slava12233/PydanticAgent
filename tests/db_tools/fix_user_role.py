#!/usr/bin/env python
"""
סקריפט להוספת עמודת role לטבלת users במסד הנתונים postgres
"""
import psycopg2
import sys
import logging
from src.core.config import ADMIN_USER_ID

# הגדרת לוגר
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_user_role():
    """הוספת עמודת role לטבלת users במסד הנתונים postgres"""
    try:
        # יצירת חיבור למסד הנתונים postgres
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='postgres',
            user='postgres',
            password='SSll456456!!'
        )
        
        # הגדרת autocommit כדי שהפקודות יבוצעו מיד
        conn.autocommit = True
        
        # יצירת cursor
        cur = conn.cursor()
        
        # בדיקה אם העמודה כבר קיימת
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role';
        """)
        
        role_exists = cur.fetchone() is not None
        
        if not role_exists:
            logger.info("מוסיף עמודת 'role' לטבלת 'users'...")
            
            # יצירת enum בבסיס הנתונים אם לא קיים
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                        CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'USER', 'BLOCKED');
                    END IF;
                END
                $$;
            """)
            
            # הוספת העמודה עם ערך ברירת מחדל
            cur.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role user_role_enum NOT NULL DEFAULT 'USER';
            """)
            
            logger.info("עמודת 'role' נוספה בהצלחה!")
            
            # עדכון המשתמש הראשי להיות מנהל
            if ADMIN_USER_ID:
                cur.execute(f"UPDATE users SET role = 'ADMIN' WHERE id = {ADMIN_USER_ID}")
                logger.info(f"עודכן תפקיד המשתמש עם מזהה {ADMIN_USER_ID} למנהל")
        else:
            logger.info("עמודת 'role' כבר קיימת בטבלת 'users'")
        
        # סגירת החיבור
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"שגיאה בהוספת עמודת 'role': {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("מתחיל הוספת עמודת role לטבלת users במסד הנתונים postgres...")
    success = fix_user_role()
    if success:
        logger.info("התהליך הסתיים בהצלחה!")
    else:
        logger.error("התהליך נכשל!")
        sys.exit(1) 