"""
מודול לניהול חנויות במסד הנתונים
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.woocommerce import WooCommerceStore
from src.database.models.users import User
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class StoreManager:
    """מחלקה לניהול חנויות"""
    
    @staticmethod
    async def get_all_stores(session: AsyncSession) -> List[WooCommerceStore]:
        """קבלת כל החנויות במערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת כל החנויות
        """
        try:
            result = await session.execute(select(WooCommerceStore))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת כל החנויות: {str(e)}")
            raise
            
    @staticmethod
    async def get_store_by_id(store_id: int, session: AsyncSession) -> Optional[WooCommerceStore]:
        """קבלת חנות לפי מזהה
        
        Args:
            store_id: מזהה החנות
            session: סשן של מסד הנתונים
            
        Returns:
            החנות אם נמצאה, None אחרת
        """
        try:
            return await session.get(WooCommerceStore, store_id)
        except Exception as e:
            logger.error(f"שגיאה בקבלת חנות {store_id}: {str(e)}")
            return None
            
    @staticmethod
    async def get_user_stores(user_id: int, session: AsyncSession) -> List[WooCommerceStore]:
        """קבלת כל החנויות של משתמש מסוים
        
        Args:
            user_id: מזהה המשתמש
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת החנויות של המשתמש
        """
        try:
            result = await session.execute(
                select(WooCommerceStore).where(WooCommerceStore.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת חנויות של משתמש {user_id}: {str(e)}")
            return []
            
    @staticmethod
    async def create_store(
        session: AsyncSession,
        user_id: int,
        store_url: str,
        consumer_key: str,
        consumer_secret: str,
        store_name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceStore]:
        """יצירת חנות חדשה
        
        Args:
            session: סשן של מסד הנתונים
            user_id: מזהה המשתמש
            store_url: כתובת החנות
            consumer_key: מפתח צרכן
            consumer_secret: סוד צרכן
            store_name: שם החנות
            settings: הגדרות נוספות לחנות
            
        Returns:
            החנות שנוצרה, None אם נכשל
        """
        try:
            # יצירת חנות חדשה
            store = WooCommerceStore(
                user_id=user_id,
                store_url=store_url,
                store_name=store_name,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                settings=settings or {}
            )
            
            session.add(store)
            await session.commit()
            await session.refresh(store)
            
            logger.info(f"נוצרה חנות חדשה: {store.id} (משתמש: {user_id})")
            return store
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת חנות: {str(e)}")
            return None
            
    @staticmethod
    async def update_store(
        store_id: int,
        session: AsyncSession,
        store_url: Optional[str] = None,
        store_name: Optional[str] = None,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        is_active: Optional[bool] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceStore]:
        """עדכון פרטי חנות
        
        Args:
            store_id: מזהה החנות
            session: סשן של מסד הנתונים
            store_url: כתובת החנות החדשה
            store_name: שם החנות החדש
            consumer_key: מפתח צרכן חדש
            consumer_secret: סוד צרכן חדש
            is_active: האם החנות פעילה
            settings: הגדרות חדשות לחנות
            
        Returns:
            החנות המעודכנת, None אם נכשל
        """
        try:
            store = await StoreManager.get_store_by_id(store_id, session)
            if not store:
                logger.warning(f"לא נמצאה חנות עם מזהה {store_id}")
                return None
                
            if store_url is not None:
                store.store_url = store_url
            if store_name is not None:
                store.store_name = store_name
            if consumer_key is not None:
                store.consumer_key = consumer_key
            if consumer_secret is not None:
                store.consumer_secret = consumer_secret
            if is_active is not None:
                store.is_active = is_active
            if settings is not None:
                store.settings = settings
                
            await session.commit()
            await session.refresh(store)
            
            logger.info(f"עודכנו פרטי חנות {store_id}")
            return store
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה בעדכון פרטי חנות {store_id}: {str(e)}")
            return None
            
    @staticmethod
    async def delete_store(store_id: int, session: AsyncSession) -> bool:
        """מחיקת חנות
        
        Args:
            store_id: מזהה החנות
            session: סשן של מסד הנתונים
            
        Returns:
            True אם המחיקה הצליחה, False אחרת
        """
        try:
            # מחיקת החנות
            result = await session.execute(
                delete(WooCommerceStore).where(WooCommerceStore.id == store_id)
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"נמחקה חנות: {store_id}")
                return True
            else:
                logger.warning(f"לא נמצאה חנות למחיקה: {store_id}")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה במחיקת חנות {store_id}: {str(e)}")
            return False 