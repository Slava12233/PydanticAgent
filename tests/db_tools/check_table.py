#!/usr/bin/env python
"""
סקריפט לבדיקת מבנה טבלת users
"""
import psycopg2
import sys

def check_users_table():
    """בדיקת מבנה טבלת users"""
    try:
        # יצירת חיבור למסד הנתונים
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='postgres',
            user='postgres',
            password='SSll456456!!'
        )
        
        # יצירת cursor
        cur = conn.cursor()
        
        # שליפת מידע על העמודות בטבלה
        cur.execute("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        
        print("=== מבנה טבלת users ===")
        for column in columns:
            print(f"שם עמודה: {column[0]}, סוג: {column[1]}, סוג מדויק: {column[2]}")
        
        # בדיקה ספציפית לעמודת role
        role_exists = any(col[0] == 'role' for col in columns)
        if role_exists:
            print("\n✅ עמודת 'role' קיימת בטבלה")
            
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
            print("\n❌ עמודת 'role' לא קיימת בטבלה")
        
        # סגירת החיבור
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"שגיאה בבדיקת מבנה הטבלה: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_users_table()
    if not success:
        sys.exit(1) 