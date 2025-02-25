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

def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='העברת נתונים מהמבנה הישן למבנה החדש')
    parser.add_argument('--force', action='store_true', help='כפיית העברת נתונים גם אם הטבלה הישנה לא נמצאה')
    
    args = parser.parse_args()
    
    if args.force:
        print("מעביר נתונים בכפייה...")
        migrate_data()
    else:
        # בדיקה אם הטבלה הישנה קיימת
        if check_old_table_exists():
            print("נמצאה טבלה ישנה. מעביר נתונים...")
            migrate_data()
        else:
            print("הטבלה הישנה לא נמצאה. אין צורך בהעברת נתונים.")

if __name__ == '__main__':
    main() 