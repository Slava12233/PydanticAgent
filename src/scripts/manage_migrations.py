#!/usr/bin/env python
"""
סקריפט לניהול מיגרציות של מסד הנתונים
"""

import asyncio
import argparse
from pathlib import Path

from src.database.database import Database
from src.services.database.migrations.migration_manager import MigrationManager

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלי לניהול מיגרציות של מסד הנתונים')
    parser.add_argument('--create', help='יצירת מיגרציה חדשה (נדרש שם המיגרציה)')
    parser.add_argument('--file', help='קובץ SQL למיגרציה החדשה')
    parser.add_argument('--apply', action='store_true', help='הרצת כל המיגרציות שטרם הורצו')
    parser.add_argument('--rollback', type=int, help='ביטול מספר מיגרציות')
    parser.add_argument('--version', action='store_true', help='הצגת הגרסה הנוכחית')
    
    args = parser.parse_args()
    
    # יצירת מופע של מסד הנתונים
    db = Database()
    await db.initialize()
    
    # יצירת מופע של מנהל המיגרציות
    migration_manager = MigrationManager(db)
    
    try:
        if args.create:
            if not args.file:
                print("חובה לציין קובץ SQL למיגרציה החדשה עם הפרמטר --file")
                return
                
            # קריאת קובץ ה-SQL
            sql_file = Path(args.file)
            if not sql_file.exists():
                print(f"הקובץ {args.file} לא קיים")
                return
                
            sql = sql_file.read_text(encoding='utf-8')
            
            # יצירת המיגרציה
            migration_file = await migration_manager.create_migration(args.create, sql)
            print(f"נוצרה מיגרציה חדשה: {migration_file.name}")
            
        elif args.apply:
            # הרצת כל המיגרציות
            await migration_manager.apply_migrations()
            current_version = await migration_manager.get_current_version()
            print(f"כל המיגרציות הורצו בהצלחה. גרסה נוכחית: {current_version}")
            
        elif args.rollback:
            # ביטול מיגרציות
            await migration_manager.rollback(args.rollback)
            current_version = await migration_manager.get_current_version()
            print(f"בוטלו {args.rollback} מיגרציות. גרסה נוכחית: {current_version}")
            
        elif args.version:
            # הצגת הגרסה הנוכחית
            current_version = await migration_manager.get_current_version()
            print(f"גרסה נוכחית של מסד הנתונים: {current_version}")
            
        else:
            parser.print_help()
    
    finally:
        await db.close()

if __name__ == '__main__':
    asyncio.run(main()) 