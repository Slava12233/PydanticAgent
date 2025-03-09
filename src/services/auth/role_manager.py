"""
מודול לניהול תפקידי משתמשים במערכת
"""

from typing import Optional, List
import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import Database
from src.models.users import User, UserRole
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class RoleManager:
    """מחלקה לניהול תפקידי משתמשים"""
    
    def __init__(self, db: Database):
        """אתחול המחלקה
        
        Args:
            db: מופע של מסד הנתונים
        """
        self.db = db
        
    async def ensure_role_column_exists(self) -> bool:
        """וידוא שעמודת role קיימת בטבלת users
        
        Returns:
            האם העמודה קיימת או נוצרה בהצלחה
        """
        try:
            async with self.db.session() as session:
                # בדיקה אם העמודה כבר קיימת
                inspector = inspect(self.db.engine)
                columns = inspector.get_columns('users')
                column_names = [column['name'] for column in columns]
                
                if 'role' not in column_names:
                    logger.info("מוסיף עמודת 'role' לטבלת 'users'...")
                    
                    # יצירת enum בבסיס הנתונים אם לא קיים
                    await session.execute(text("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                                CREATE TYPE user_role_enum AS ENUM ('ADMIN', 'USER', 'BLOCKED');
                            END IF;
                        END
                        $$;
                    """))
                    
                    # הוספת העמודה עם ערך ברירת מחדל
                    await session.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS role user_role_enum NOT NULL DEFAULT 'USER';
                    """))
                    
                    await session.commit()
                    logger.info("עמודת 'role' נוספה בהצלחה!")
                else:
                    logger.info("עמודת 'role' כבר קיימת בטבלת 'users'")
                
                return True
                
        except Exception as e:
            logger.error(f"שגיאה בוידוא קיום עמודת 'role': {str(e)}")
            return False
            
    async def set_user_role(self, user_id: int, role: UserRole) -> bool:
        """עדכון תפקיד משתמש
        
        Args:
            user_id: מזהה המשתמש
            role: התפקיד החדש
            
        Returns:
            האם העדכון הצליח
        """
        try:
            async with self.db.session() as session:
                # עדכון תפקיד המשתמש
                await session.execute(
                    text("UPDATE users SET role = :role WHERE id = :user_id"),
                    {"role": role.value, "user_id": user_id}
                )
                await session.commit()
                
                logger.info(f"עודכן תפקיד המשתמש {user_id} ל-{role.value}")
                return True
                
        except Exception as e:
            logger.error(f"שגיאה בעדכון תפקיד משתמש {user_id}: {str(e)}")
            return False
            
    async def get_user_role(self, user_id: int) -> Optional[UserRole]:
        """קבלת תפקיד משתמש
        
        Args:
            user_id: מזהה המשתמש
            
        Returns:
            תפקיד המשתמש או None אם לא נמצא
        """
        try:
            async with self.db.session() as session:
                result = await session.execute(
                    text("SELECT role FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                role = result.scalar()
                return UserRole(role) if role else None
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת תפקיד משתמש {user_id}: {str(e)}")
            return None
            
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """קבלת כל המשתמשים עם תפקיד מסוים
        
        Args:
            role: התפקיד לחיפוש
            
        Returns:
            רשימת המשתמשים
        """
        try:
            async with self.db.session() as session:
                result = await session.execute(
                    text("SELECT * FROM users WHERE role = :role"),
                    {"role": role.value}
                )
                return [User(**row) for row in result]
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת משתמשים עם תפקיד {role.value}: {str(e)}")
            return [] 