"""
מודול לניהול משתמשים במסד הנתונים
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import User, UserRole
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class UserManager:
    """מחלקה לניהול משתמשים"""
    
    @staticmethod
    async def get_all_users(session: AsyncSession) -> List[User]:
        """קבלת כל המשתמשים במערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת כל המשתמשים
        """
        try:
            result = await session.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת כל המשתמשים: {str(e)}")
            raise
            
    @staticmethod
    async def get_user_by_id(user_id: int, session: AsyncSession) -> Optional[User]:
        """קבלת משתמש לפי מזהה
        
        Args:
            user_id: מזהה המשתמש
            session: סשן של מסד הנתונים
            
        Returns:
            המשתמש אם נמצא, None אחרת
        """
        try:
            return await session.get(User, user_id)
        except Exception as e:
            logger.error(f"שגיאה בקבלת משתמש {user_id}: {str(e)}")
            return None
            
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int, session: AsyncSession) -> Optional[User]:
        """קבלת משתמש לפי מזהה טלגרם
        
        Args:
            telegram_id: מזהה הטלגרם
            session: סשן של מסד הנתונים
            
        Returns:
            המשתמש אם נמצא, None אחרת
        """
        try:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"שגיאה בקבלת משתמש לפי telegram_id {telegram_id}: {str(e)}")
            return None
            
    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> Optional[User]:
        """יצירת משתמש חדש
        
        Args:
            session: סשן של מסד הנתונים
            telegram_id: מזהה הטלגרם
            username: שם המשתמש (אופציונלי)
            first_name: שם פרטי (אופציונלי)
            last_name: שם משפחה (אופציונלי)
            role: תפקיד המשתמש (ברירת מחדל: USER)
            
        Returns:
            המשתמש שנוצר או None אם נכשל
        """
        try:
            # בדיקה אם המשתמש כבר קיים
            existing_user = await UserManager.get_user_by_telegram_id(telegram_id, session)
            if existing_user:
                return existing_user
                
            # יצירת משתמש חדש
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            logger.info(f"נוצר משתמש חדש: {new_user.id} (telegram_id: {telegram_id})")
            return new_user
            
        except Exception as e:
            logger.error(f"שגיאה ביצירת משתמש חדש: {str(e)}")
            await session.rollback()
            return None
            
    @staticmethod
    async def update_user_role(user_id: int, role: UserRole, session: AsyncSession) -> Optional[User]:
        """עדכון תפקיד משתמש
        
        Args:
            user_id: מזהה המשתמש
            role: התפקיד החדש
            session: סשן של מסד הנתונים
            
        Returns:
            המשתמש המעודכן או None אם נכשל
        """
        try:
            user = await UserManager.get_user_by_id(user_id, session)
            if not user:
                return None
                
            user.role = role
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"עודכן תפקיד משתמש {user_id} ל-{role.value}")
            return user
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון תפקיד משתמש {user_id}: {str(e)}")
            await session.rollback()
            return None
            
    @staticmethod
    async def update_user(
        user: User,
        session: AsyncSession,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Optional[User]:
        """עדכון פרטי משתמש
        
        Args:
            user: המשתמש לעדכון
            session: סשן של מסד הנתונים
            username: שם משתמש חדש (אופציונלי)
            first_name: שם פרטי חדש (אופציונלי)
            last_name: שם משפחה חדש (אופציונלי)
            
        Returns:
            המשתמש המעודכן או None אם נכשל
        """
        try:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
                
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"עודכנו פרטי משתמש {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון פרטי משתמש {user.id}: {str(e)}")
            await session.rollback()
            return None 