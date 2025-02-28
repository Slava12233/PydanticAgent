#!/usr/bin/env python
"""
סקריפט לבדיקת מסדי הנתונים והסכמות הקיימים
"""
import psycopg2
import sys
from src.core.config import DATABASE_URL

def check_databases():
    """בדיקת מסדי הנתונים והסכמות הקיימים"""
    try:
        # הדפסת ה-DATABASE_URL מהקונפיגורציה
        print(f"DATABASE_URL מהקונפיגורציה: {DATABASE_URL}")
        
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
        
        # שליפת רשימת מסדי הנתונים
        cur.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false;
        """)
        
        databases = cur.fetchall()
        
        print("\n=== מסדי נתונים קיימים ===")
        for db in databases:
            print(f"- {db[0]}")
        
        # שליפת רשימת הסכמות
        cur.execute("""
            SELECT schema_name FROM information_schema.schemata;
        """)
        
        schemas = cur.fetchall()
        
        print("\n=== סכמות קיימות ===")
        for schema in schemas:
            print(f"- {schema[0]}")
        
        # שליפת רשימת הטבלאות בסכמה הציבורית
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        
        tables = cur.fetchall()
        
        print("\n=== טבלאות בסכמה הציבורית ===")
        for table in tables:
            print(f"- {table[0]}")
        
        # סגירת החיבור
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"שגיאה בבדיקת מסדי הנתונים: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_databases()
    if not success:
        sys.exit(1) 