"""
סקריפט להצגת ההודעות השמורות במסד הנתונים
"""
import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv

# הוספת תיקיית הפרויקט לנתיב החיפוש
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# טעינת משתני סביבה
load_dotenv()

# ייבוא מודול מסד הנתונים
from src.database.database import db

def view_messages(save_to_csv=False):
    """הצגת כל ההודעות השמורות במסד הנתונים"""
    try:
        # אתחול מסד הנתונים
        db.init_db()
        
        # קבלת פרטי החיבור
        print(f"מחובר למסד הנתונים: {db.db_url.split('@')[0]}@{db.db_url.split('@')[1]}")
        
        # שליפת כל ההודעות
        with db.Session() as session:
            from sqlalchemy import select
            from src.database.database import Message
            
            # שליפת כל ההודעות מסודרות לפי זמן
            query = select(Message).order_by(Message.timestamp.desc())
            messages = session.execute(query).scalars().all()
            
            if not messages:
                print("אין הודעות שמורות במסד הנתונים.")
                return
            
            print(f"\nנמצאו {len(messages)} הודעות:")
            print("-" * 80)
            
            # שמירה לקובץ CSV אם התבקש
            if save_to_csv:
                csv_file = os.path.join(os.path.dirname(__file__), '..', '..', 'messages.csv')
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'User ID', 'Timestamp', 'Message', 'Response'])
                    
                    for msg in messages:
                        writer.writerow([
                            msg.id,
                            msg.user_id,
                            msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            msg.message,
                            msg.response
                        ])
                
                print(f"ההודעות נשמרו לקובץ: {os.path.abspath(csv_file)}")
            
            # הצגת ההודעות
            for msg in messages:
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"ID: {msg.id}")
                print(f"User ID: {msg.user_id}")
                print(f"זמן: {timestamp}")
                print(f"הודעה: {msg.message}")
                print(f"תשובה: {msg.response}")
                print("-" * 80)
            
            # הצגת סטטיסטיקות
            user_count = db.get_user_count()
            print(f"\nסטטיסטיקות:")
            print(f"סה\"כ הודעות: {len(messages)}")
            print(f"מספר משתמשים ייחודיים: {user_count}")
            
    except Exception as e:
        print(f"שגיאה בהצגת ההודעות: {e}")
    finally:
        # סגירת החיבור
        db.close()

if __name__ == "__main__":
    # בדיקה אם יש פרמטר לשמירה לקובץ
    save_to_csv = len(sys.argv) > 1 and sys.argv[1].lower() in ('--csv', '-c')
    view_messages(save_to_csv) 