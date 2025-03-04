import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import db
from src.database.models import (
    User,
    WooCommerceStore as Store,
    WooCommerceProduct as Product,
    WooCommerceOrder as Order,
    WooCommerceOrderItem as OrderItem,
    WooCommerceCustomer as Customer,
    WooCommercePayment as Payment,
    WooCommerceShipping as Shipping,
    Notification,
    ScheduledTask
)
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
                .where(Store.owner_id == user_id)
            )
        except Exception as e:
            logger.error(f"Error getting store for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def create_store(
        session: AsyncSession,
        owner_id: int,
        name: str,
        description: str = None
    ) -> Optional[Store]:
        """
        יצירת חנות חדשה
        
        Args:
            session: סשן בסיס נתונים
            owner_id: מזהה בעל החנות
            name: שם החנות
            description: תיאור החנות (אופציונלי)
            
        Returns:
            חנות חדשה אם נוצרה בהצלחה, אחרת None
        """
        try:
            store = Store(
                owner_id=owner_id,
                name=name,
                description=description
            )
            session.add(store)
            await session.commit()
            return store
        except Exception as e:
            logger.error(f"Error creating store for user {owner_id}: {e}")
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
    
    @staticmethod
    async def get_order(session: AsyncSession, order_id: int) -> Optional[Order]:
        """
        קבלת הזמנה לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            order_id: מזהה הזמנה
            
        Returns:
            הזמנה אם נמצאה, אחרת None
        """
        try:
            return await session.scalar(
                select(Order)
                .where(Order.id == order_id)
            )
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    @staticmethod
    async def get_store_orders(
        session: AsyncSession,
        store_id: int,
        status: str = None,
        limit: int = None
    ) -> List[Order]:
        """
        קבלת הזמנות של חנות
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            status: סטטוס הזמנה (אופציונלי)
            limit: מספר תוצאות מקסימלי (אופציונלי)
            
        Returns:
            רשימת הזמנות
        """
        try:
            query = select(Order).where(Order.store_id == store_id)
            
            if status:
                query = query.where(Order.status == status)
            
            query = query.order_by(desc(Order.created_at))
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting orders for store {store_id}: {e}")
            return []
    
    @staticmethod
    async def create_order(
        session: AsyncSession,
        store_id: int,
        customer_id: int,
        items: List[Dict[str, Any]]
    ) -> Optional[Order]:
        """
        יצירת הזמנה חדשה
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            customer_id: מזהה לקוח
            items: פריטי ההזמנה
            
        Returns:
            הזמנה חדשה אם נוצרה בהצלחה, אחרת None
        """
        try:
            # חישוב סכום ההזמנה
            total_amount = sum(
                item['price'] * item['quantity']
                for item in items
            )
            
            # יצירת ההזמנה
            order = Order(
                store_id=store_id,
                customer_id=customer_id,
                total_amount=total_amount,
                status='pending'
            )
            session.add(order)
            await session.flush()
            
            # הוספת פריטי ההזמנה
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                session.add(order_item)
            
            await session.commit()
            return order
        except Exception as e:
            logger.error(f"Error creating order for store {store_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_customer(session: AsyncSession, customer_id: int) -> Optional[Customer]:
        """
        קבלת לקוח לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            customer_id: מזהה לקוח
            
        Returns:
            לקוח אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(Customer)
                .where(Customer.id == customer_id)
            )
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return None
    
    @staticmethod
    async def get_store_customers(
        session: AsyncSession,
        store_id: int,
        search_query: str = None,
        limit: int = None
    ) -> List[Customer]:
        """
        קבלת לקוחות של חנות
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            search_query: מחרוזת חיפוש (אופציונלי)
            limit: מספר תוצאות מקסימלי (אופציונלי)
            
        Returns:
            רשימת לקוחות
        """
        try:
            query = select(Customer).where(Customer.store_id == store_id)
            
            if search_query:
                query = query.where(
                    or_(
                        Customer.name.ilike(f"%{search_query}%"),
                        Customer.email.ilike(f"%{search_query}%"),
                        Customer.phone.ilike(f"%{search_query}%")
                    )
                )
            
            query = query.order_by(desc(Customer.created_at))
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting customers for store {store_id}: {e}")
            return []
    
    @staticmethod
    async def create_customer(
        session: AsyncSession,
        store_id: int,
        name: str,
        email: str = None,
        phone: str = None,
        address: str = None
    ) -> Optional[Customer]:
        """
        יצירת לקוח חדש
        
        Args:
            session: סשן בסיס נתונים
            store_id: מזהה חנות
            name: שם הלקוח
            email: אימייל (אופציונלי)
            phone: טלפון (אופציונלי)
            address: כתובת (אופציונלי)
            
        Returns:
            לקוח חדש אם נוצר בהצלחה, אחרת None
        """
        try:
            customer = Customer(
                store_id=store_id,
                name=name,
                email=email,
                phone=phone,
                address=address
            )
            session.add(customer)
            await session.commit()
            return customer
        except Exception as e:
            logger.error(f"Error creating customer for store {store_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_payment(session: AsyncSession, payment_id: int) -> Optional[Payment]:
        """
        קבלת תשלום לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            payment_id: מזהה תשלום
            
        Returns:
            תשלום אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(Payment)
                .where(Payment.id == payment_id)
            )
        except Exception as e:
            logger.error(f"Error getting payment {payment_id}: {e}")
            return None
    
    @staticmethod
    async def get_order_payments(
        session: AsyncSession,
        order_id: int
    ) -> List[Payment]:
        """
        קבלת תשלומים של הזמנה
        
        Args:
            session: סשן בסיס נתונים
            order_id: מזהה הזמנה
            
        Returns:
            רשימת תשלומים
        """
        try:
            result = await session.execute(
                select(Payment)
                .where(Payment.order_id == order_id)
                .order_by(Payment.created_at)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting payments for order {order_id}: {e}")
            return []
    
    @staticmethod
    async def create_payment(
        session: AsyncSession,
        order_id: int,
        amount: float,
        payment_method: str,
        status: str = 'pending'
    ) -> Optional[Payment]:
        """
        יצירת תשלום חדש
        
        Args:
            session: סשן בסיס נתונים
            order_id: מזהה הזמנה
            amount: סכום
            payment_method: שיטת תשלום
            status: סטטוס (ברירת מחדל: ממתין)
            
        Returns:
            תשלום חדש אם נוצר בהצלחה, אחרת None
        """
        try:
            payment = Payment(
                order_id=order_id,
                amount=amount,
                payment_method=payment_method,
                status=status
            )
            session.add(payment)
            await session.commit()
            return payment
        except Exception as e:
            logger.error(f"Error creating payment for order {order_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_shipping(session: AsyncSession, shipping_id: int) -> Optional[Shipping]:
        """
        קבלת משלוח לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            shipping_id: מזהה משלוח
            
        Returns:
            משלוח אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(Shipping)
                .where(Shipping.id == shipping_id)
            )
        except Exception as e:
            logger.error(f"Error getting shipping {shipping_id}: {e}")
            return None
    
    @staticmethod
    async def get_order_shipping(
        session: AsyncSession,
        order_id: int
    ) -> Optional[Shipping]:
        """
        קבלת משלוח של הזמנה
        
        Args:
            session: סשן בסיס נתונים
            order_id: מזהה הזמנה
            
        Returns:
            משלוח אם נמצא, אחרת None
        """
        try:
            return await session.scalar(
                select(Shipping)
                .where(Shipping.order_id == order_id)
            )
        except Exception as e:
            logger.error(f"Error getting shipping for order {order_id}: {e}")
            return None
    
    @staticmethod
    async def create_shipping(
        session: AsyncSession,
        order_id: int,
        address: str,
        shipping_method: str,
        tracking_number: str = None,
        status: str = 'pending'
    ) -> Optional[Shipping]:
        """
        יצירת משלוח חדש
        
        Args:
            session: סשן בסיס נתונים
            order_id: מזהה הזמנה
            address: כתובת
            shipping_method: שיטת משלוח
            tracking_number: מספר מעקב (אופציונלי)
            status: סטטוס (ברירת מחדל: ממתין)
            
        Returns:
            משלוח חדש אם נוצר בהצלחה, אחרת None
        """
        try:
            shipping = Shipping(
                order_id=order_id,
                address=address,
                shipping_method=shipping_method,
                tracking_number=tracking_number,
                status=status
            )
            session.add(shipping)
            await session.commit()
            return shipping
        except Exception as e:
            logger.error(f"Error creating shipping for order {order_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_notification(
        session: AsyncSession,
        notification_id: int
    ) -> Optional[Notification]:
        """
        קבלת התראה לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            notification_id: מזהה התראה
            
        Returns:
            התראה אם נמצאה, אחרת None
        """
        try:
            return await session.scalar(
                select(Notification)
                .where(Notification.id == notification_id)
            )
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_notifications(
        session: AsyncSession,
        user_id: int,
        status: str = None,
        limit: int = None
    ) -> List[Notification]:
        """
        קבלת התראות של משתמש
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה משתמש
            status: סטטוס (אופציונלי)
            limit: מספר תוצאות מקסימלי (אופציונלי)
            
        Returns:
            רשימת התראות
        """
        try:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if status:
                query = query.where(Notification.status == status)
            
            query = query.order_by(desc(Notification.created_at))
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def create_notification(
        session: AsyncSession,
        user_id: int,
        type: str,
        message: str,
        status: str = 'pending'
    ) -> Optional[Notification]:
        """
        יצירת התראה חדשה
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה משתמש
            type: סוג התראה
            message: תוכן ההתראה
            status: סטטוס (ברירת מחדל: ממתין)
            
        Returns:
            התראה חדשה אם נוצרה בהצלחה, אחרת None
        """
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                message=message,
                status=status
            )
            session.add(notification)
            await session.commit()
            return notification
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")
            await session.rollback()
            return None
    
    @staticmethod
    async def get_scheduled_task(
        session: AsyncSession,
        task_id: int
    ) -> Optional[ScheduledTask]:
        """
        קבלת משימה מתוזמנת לפי מזהה
        
        Args:
            session: סשן בסיס נתונים
            task_id: מזהה משימה
            
        Returns:
            משימה אם נמצאה, אחרת None
        """
        try:
            return await session.scalar(
                select(ScheduledTask)
                .where(ScheduledTask.id == task_id)
            )
        except Exception as e:
            logger.error(f"Error getting scheduled task {task_id}: {e}")
            return None
    
    @staticmethod
    async def get_user_scheduled_tasks(
        session: AsyncSession,
        user_id: int,
        status: str = None
    ) -> List[ScheduledTask]:
        """
        קבלת משימות מתוזמנות של משתמש
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה משתמש
            status: סטטוס (אופציונלי)
            
        Returns:
            רשימת משימות
        """
        try:
            query = select(ScheduledTask).where(ScheduledTask.user_id == user_id)
            
            if status:
                query = query.where(ScheduledTask.status == status)
            
            query = query.order_by(ScheduledTask.next_run)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting scheduled tasks for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def create_scheduled_task(
        session: AsyncSession,
        user_id: int,
        type: str,
        name: str,
        schedule: str,
        params: Dict[str, Any] = None,
        status: str = 'active'
    ) -> Optional[ScheduledTask]:
        """
        יצירת משימה מתוזמנת חדשה
        
        Args:
            session: סשן בסיס נתונים
            user_id: מזהה משתמש
            type: סוג משימה
            name: שם המשימה
            schedule: תזמון
            params: פרמטרים (אופציונלי)
            status: סטטוס (ברירת מחדל: פעיל)
            
        Returns:
            משימה חדשה אם נוצרה בהצלחה, אחרת None
        """
        try:
            task = ScheduledTask(
                user_id=user_id,
                type=type,
                name=name,
                schedule=schedule,
                params=params,
                status=status
            )
            session.add(task)
            await session.commit()
            return task
        except Exception as e:
            logger.error(f"Error creating scheduled task for user {user_id}: {e}")
            await session.rollback()
            return None 