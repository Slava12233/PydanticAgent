#!/usr/bin/env python
"""
סקריפט לניהול תפקידי משתמשים במערכת
"""

import asyncio
import argparse
from typing import Optional

from src.database.database import Database
from src.services.auth.role_manager import RoleManager
from src.models.users import UserRole
from src.core.config import ADMIN_USER_ID

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלי לניהול תפקידי משתמשים במערכת')
    parser.add_argument('--init', action='store_true', help='יצירת עמודת role בטבלת users')
    parser.add_argument('--set-role', type=int, help='עדכון תפקיד למשתמש (נדרש מזהה משתמש)')
    parser.add_argument('--role', choices=['ADMIN', 'USER', 'BLOCKED'], help='התפקיד החדש')
    parser.add_argument('--get-role', type=int, help='קבלת תפקיד משתמש (נדרש מזהה משתמש)')
    parser.add_argument('--list-users', choices=['ADMIN', 'USER', 'BLOCKED'], help='הצגת משתמשים לפי תפקיד')
    
    args = parser.parse_args()
    
    # יצירת מופע של מסד הנתונים
    db = Database()
    await db.initialize()
    
    # יצירת מופע של מנהל התפקידים
    role_manager = RoleManager(db)
    
    try:
        if args.init:
            # יצירת עמודת role
            success = await role_manager.ensure_role_column_exists()
            if success:
                print("עמודת role נוצרה או קיימת בהצלחה")
                
                # עדכון המשתמש הראשי להיות מנהל
                if ADMIN_USER_ID:
                    success = await role_manager.set_user_role(ADMIN_USER_ID, UserRole.ADMIN)
                    if success:
                        print(f"עודכן תפקיד המשתמש {ADMIN_USER_ID} למנהל")
            else:
                print("שגיאה ביצירת עמודת role")
                
        elif args.set_role:
            if not args.role:
                print("חובה לציין את התפקיד החדש עם הפרמטר --role")
                return
                
            # עדכון תפקיד משתמש
            success = await role_manager.set_user_role(args.set_role, UserRole[args.role])
            if success:
                print(f"עודכן תפקיד המשתמש {args.set_role} ל-{args.role}")
            else:
                print(f"שגיאה בעדכון תפקיד המשתמש {args.set_role}")
                
        elif args.get_role:
            # קבלת תפקיד משתמש
            role = await role_manager.get_user_role(args.get_role)
            if role:
                print(f"תפקיד המשתמש {args.get_role}: {role.value}")
            else:
                print(f"לא נמצא תפקיד למשתמש {args.get_role}")
                
        elif args.list_users:
            # הצגת משתמשים לפי תפקיד
            users = await role_manager.get_users_by_role(UserRole[args.list_users])
            if users:
                print(f"משתמשים עם תפקיד {args.list_users}:")
                for user in users:
                    print(f"- מזהה: {user.id}, שם משתמש: {user.username or 'אנונימי'}")
            else:
                print(f"לא נמצאו משתמשים עם תפקיד {args.list_users}")
                
        else:
            parser.print_help()
    
    finally:
        await db.close()

if __name__ == '__main__':
    asyncio.run(main()) 