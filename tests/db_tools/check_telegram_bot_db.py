#!/usr/bin/env python
"""
סקריפט לבדיקת מבנה הטבלאות במסד הנתונים telegram_bot
"""
import psycopg2
import sys

def check_telegram_bot_db():
    """בדיקת מבנה הטבלאות במסד הנתונים telegram_bot"""
    try:
        # יצירת חיבור למסד הנתונים telegram_bot
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='telegram_bot',
            user='postgres',
            password='SSll456456!!'
        )
        
        # יצירת cursor
        cur = conn.cursor()
        
        # שליפת רשימת הטבלאות
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        
        tables = cur.fetchall()
        
        print("=== טבלאות במסד הנתונים telegram_bot ===")
        for table in tables:
            print(f"- {table[0]}")
        
        # בדיקה אם טבלת users קיימת
        users_exists = any(table[0] == 'users' for table in tables)
        if users_exists:
            # שליפת מידע על העמודות בטבלת users
            cur.execute("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            
            print("\n=== מבנה טבלת users במסד הנתונים telegram_bot ===")
            for column in columns:
                print(f"שם עמודה: {column[0]}, סוג: {column[1]}, סוג מדויק: {column[2]}")
            
            # בדיקה ספציפית לעמודת role
            role_exists = any(col[0] == 'role' for col in columns)
            if role_exists:
                print("\n✅ עמודת 'role' קיימת בטבלת users במסד הנתונים telegram_bot")
                
                # בדיקת סוג ה-enum
                cur.execute("""
                    SELECT pg_enum.enumlabel
                    FROM pg_type JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid
                    WHERE pg_type.typname = 'user_role_enum'
                    ORDER BY pg_enum.enumsortorder;
                """)
                
                enum_values = cur.fetchall()
                if enum_values:
                    print("ערכי ה-enum האפשריים:")
                    for value in enum_values:
                        print(f"- {value[0]}")
                else:
                    print("❌ לא נמצאו ערכים ל-enum")
            else:
                print("\n❌ עמודת 'role' לא קיימת בטבלת users במסד הנתונים telegram_bot")
        else:
            print("\n❌ טבלת users לא קיימת במסד הנתונים telegram_bot")
        
        # סגירת החיבור
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"שגיאה בבדיקת מסד הנתונים telegram_bot: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_telegram_bot_db()
    if not success:
        sys.exit(1) 