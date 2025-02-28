#!/usr/bin/env python
"""
סקריפט להעברת נתונים מהמבנה הישן של מסד הנתונים למבנה החדש
"""
import os
import sys
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# הוספת תיקיית הפרויקט לנתיב החיפוש
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
from src.database.models import Base, User, Conversation, Message
from src.database.database import db

def get_db_connection():
    """יצירת חיבור למסד הנתונים"""
    db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

def check_old_table_exists():
    """בדיקה אם הטבלה הישנה קיימת"""
    session = get_db_connection()
    try:
        # בדיקה אם הטבלה הישנה קיימת
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'messages'
                AND column_name = 'user_id'
                AND column_name = 'message'
                AND column_name = 'response'
            )
        """))
        exists = result.scalar()
        return exists
    except Exception as e:
        print(f"שגיאה בבדיקת קיום הטבלה הישנה: {e}")
        return False
    finally:
        session.close()

def migrate_data():
    """העברת נתונים מהמבנה הישן למבנה החדש"""
    if not check_old_table_exists():
        print("הטבלה הישנה לא נמצאה. אין צורך בהעברת נתונים.")
        return
    
    # אתחול מסד הנתונים החדש
    db.init_db()
    
    session = get_db_connection()
    try:
        # שליפת ההודעות מהטבלה הישנה
        old_messages = session.execute(text("""
            SELECT id, user_id, message, response, timestamp
            FROM messages
            ORDER BY timestamp ASC
        """)).fetchall()
        
        print(f"נמצאו {len(old_messages)} הודעות בטבלה הישנה.")
        
        # העברת הנתונים למבנה החדש
        migrated_count = 0
        for old_msg in old_messages:
            user_id = old_msg.user_id
            message = old_msg.message
            response = old_msg.response
            
            # שמירת ההודעה במבנה החדש
            db.save_message(user_id, message, response)
            migrated_count += 1
            
            # הצגת התקדמות
            if migrated_count % 10 == 0:
                print(f"הועברו {migrated_count} הודעות...")
        
        print(f"הועברו בהצלחה {migrated_count} הודעות למבנה החדש.")
        
        # שינוי שם הטבלה הישנה (גיבוי)
        session.execute(text("""
            ALTER TABLE messages RENAME TO messages_old;
        """))
        session.commit()
        
        print("הטבלה הישנה שונתה ל-messages_old לגיבוי.")
        
    except Exception as e:
        print(f"שגיאה בהעברת הנתונים: {e}")
    finally:
        session.close()
        db.close()

def run_migrations():
    """
    הפעלת כל המיגרציות הנדרשות
    """
    # יבוא מיגרציות
    from src.database.migrations.create_tables import upgrade as create_tables
    from src.database.migrations.add_user_role import upgrade as add_user_role
    from src.database.migrations.add_woocommerce_tables import upgrade as add_woocommerce_tables
    
    # הפעלת המיגרציות לפי הסדר
    try:
        # יצירת טבלאות בסיסיות
        create_tables()
        
        # הוספת שדה תפקיד למשתמשים
        add_user_role()
        
        # הוספת טבלאות ווקומרס
        add_woocommerce_tables()
        
        logger.info("כל המיגרציות הושלמו בהצלחה")
    except Exception as e:
        logger.error(f"שגיאה בהפעלת מיגרציות: {str(e)}")
        raise

def print_db_info():
    """
    הצגת מידע על מסד הנתונים
    """
    try:
        with db.Session() as session:
            # ספירת משתמשים
            from src.database.models import User, UserRole
            user_count = session.query(User).count()
            admin_count = session.query(User).filter(User.role == UserRole.ADMIN).count()
            
            # ספירת מסמכים
            from src.database.models import Document
            doc_count = session.query(Document).count()
            
            # ספירת הודעות
            from src.database.models import Message
            message_count = session.query(Message).count()
            
            print("\n===== מידע על מסד הנתונים =====")
            print(f"סה\"כ משתמשים: {user_count}")
            print(f"מנהלים: {admin_count}")
            print(f"סה\"כ מסמכים: {doc_count}")
            print(f"סה\"כ הודעות: {message_count}")
            print("================================\n")
            
    except Exception as e:
        logger.error(f"שגיאה בהצגת מידע על מסד הנתונים: {str(e)}")

def main():
    """פונקציה ראשית"""
    try:
        # אתחול מסד הנתונים
        db.init_db()
        
        # הפעלת מיגרציות
        run_migrations()
        
        # הצגת מידע על מסד הנתונים
        print_db_info()
        
    except Exception as e:
        logger.error(f"שגיאה: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 