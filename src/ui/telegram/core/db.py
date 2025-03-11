import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.base import Base
from src.database.models.users import User
from src.database.models.woocommerce import (
    WooCommerceStore as Store,
    WooCommerceProduct as Product,
    WooCommerceOrder as Order,
    WooCommerceOrderItem as OrderItem,
    WooCommerceCustomer as Customer,
    WooCommercePayment as Payment,
    WooCommerceShipping as Shipping
)
from src.database.models.conversations import Notification, ScheduledTask
from src.database.managers.user_manager import UserManager
from src.utils.logger import setup_logger

# הגדרת לוגר
logger = setup_logger('telegram_bot_db')

class TelegramBotDB:
    """
    מחלקה לניהול פעולות בסיס הנתונים
    """
    
    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """
        קבלת משתמש לפי מזהה טלגרם
        
        Args:
            session: סשן בסיס נתונים
            telegram_id: מזהה טלגרם
            
        Returns:
            משתמש אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(User)
                .where(User.telegram_id == telegram_id)
            )
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            return None
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: str,
        language: str = 'he'
    ) -> Optional[User]:
        """
        יצירת משתמש חדש
        
        Args:
            session: סשן בסיס נתונים
            telegram_id: מזהה טלגרם
            username: שם משתמש
            language: שפה (ברירת מחדל: עברית)
            
        Returns:
            משתמש חדש אם נוצר בהצלחה, אחרת None
        """
        try:
            user = User(
                telegram_id=telegram_id,
                username=username,
                language=language
            )
            session.add(user)
            await session.commit()
            return user
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_store(session: AsyncSession, store_id: int) -> Optional[Store]:
        """
        קבלת חנות לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            
        Returns:
            חנות אם נמצאה, אחרת None
        """
        try:
            return await session.scalar(
                select(Store)
                .where(Store.id == store_id)
            )
        except Exception as e:
            logger.error(f"Error getting store {store_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_store(session: AsyncSession, user_id: int) -> Optional[Store]:
        """
        קבלת חנות של משתמש
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה משתמש
            
        Returns:
            חנות אם נמצאה, אחרת None
        """
        try:
            return await session.scalar(
                select(Store)
                .where(Store.user_id == user_id)
            )
        except Exception as e:
            logger.error(f"Error getting store for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def create_store(
        session: AsyncSession,
        user_id: int,
        name: str,
        description: str = None
    ) -> Optional[Store]:
        """
        יצירת חנות חדשה
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה בעל החנות
            name: שם החנות
            description: תיאור החנות (אופציונלי)
            
        Returns:
            חנות חדשה אם נוצרה בהצלחה, אחרת None
        """
        try:
            store = Store(
                user_id=user_id,
                name=name,
                description=description
            )
            session.add(store)
            await session.commit()
            return store
        except Exception as e:
            logger.error(f"Error creating store for user {user_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_product(session: AsyncSession, product_id: int) -> Optional[Product]:
        """
        קבלת מוצר לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            product_id: מזהה מוצר
            
        Returns:
            מוצר אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(Product)
                .where(Product.id == product_id)
            )
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    @staticmethod
    async def get_store_products(
        session: AsyncSession,
        store_id: int,
        active_only: bool = True
    ) -> List[Product]:
        """
        קבלת מוצרי חנות
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            active_only: האם להחזיר רק מוצרים פעילים
            
        Returns:
            רשימת מוצרים
        """
        try:
            query = select(Product).where(Product.store_id == store_id)
            
            if active_only:
                query = query.where(Product.is_active == True)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting products for store {store_id}: {e}")
            return []
    
    @staticmethod
    async def create_product(
        session: AsyncSession,
        store_id: int,
        name: str,
        price: float,
        description: str = None,
        image_url: str = None
    ) -> Optional[Product]:
        """
        יצירת מוצר חדש
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            name: שם המוצר
            price: מחיר
            description: תיאור (אופציונלי)
            image_url: קישור לתמונה (אופציונלי)
            
        Returns:
            מוצר חדש אם נוצר בהצלחה, אחרת None
        """
        try:
            product = Product(
                store_id=store_id,
                name=name,
                price=price,
                description=description,
                image_url=image_url
            )
            session.add(product)
            await session.commit()
            return product
        except Exception as e:
            logger.error(f"Error creating product for store {store_id}: {e}")
            await session.rollback()
            return None
