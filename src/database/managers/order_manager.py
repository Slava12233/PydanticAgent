"""
מודול לניהול הזמנות במסד הנתונים
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.woocommerce import WooCommerceOrder, WooCommerceOrderItem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class OrderManager:
    """מחלקה לניהול הזמנות"""
    
    @staticmethod
    async def get_all_orders(session: AsyncSession) -> List[WooCommerceOrder]:
        """קבלת כל ההזמנות במערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת כל ההזמנות
        """
        try:
            result = await session.execute(select(WooCommerceOrder))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת כל ההזמנות: {str(e)}")
            raise
            
    @staticmethod
    async def get_order_by_id(order_id: int, session: AsyncSession) -> Optional[WooCommerceOrder]:
        """קבלת הזמנה לפי מזהה
        
        Args:
            order_id: מזהה ההזמנה
            session: סשן של מסד הנתונים
            
        Returns:
            ההזמנה אם נמצאה, None אחרת
        """
        try:
            return await session.get(WooCommerceOrder, order_id)
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנה {order_id}: {str(e)}")
            return None
            
    @staticmethod
    async def get_store_orders(store_id: int, session: AsyncSession) -> List[WooCommerceOrder]:
        """קבלת כל ההזמנות של חנות מסוימת
        
        Args:
            store_id: מזהה החנות
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת ההזמנות של החנות
        """
        try:
            result = await session.execute(
                select(WooCommerceOrder).where(WooCommerceOrder.store_id == store_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות של חנות {store_id}: {str(e)}")
            return []
            
    @staticmethod
    async def get_customer_orders(customer_id: int, session: AsyncSession) -> List[WooCommerceOrder]:
        """קבלת כל ההזמנות של לקוח מסוים
        
        Args:
            customer_id: מזהה הלקוח
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת ההזמנות של הלקוח
        """
        try:
            result = await session.execute(
                select(WooCommerceOrder).where(WooCommerceOrder.customer_id == customer_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות של לקוח {customer_id}: {str(e)}")
            return []
            
    @staticmethod
    async def create_order(
        session: AsyncSession,
        store_id: int,
        woo_id: int,
        status: str,
        total: float,
        date_created: datetime,
        customer_id: Optional[int] = None,
        order_number: Optional[str] = None,
        currency: Optional[str] = None,
        date_modified: Optional[datetime] = None,
        order_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceOrder]:
        """יצירת הזמנה חדשה
        
        Args:
            session: סשן של מסד הנתונים
            store_id: מזהה החנות
            woo_id: מזהה ההזמנה בווקומרס
            status: סטטוס ההזמנה
            total: סכום ההזמנה
            date_created: תאריך יצירת ההזמנה
            customer_id: מזהה הלקוח
            order_number: מספר ההזמנה
            currency: מטבע ההזמנה
            date_modified: תאריך עדכון ההזמנה
            order_data: נתונים נוספים על ההזמנה
            
        Returns:
            ההזמנה שנוצרה, None אם נכשל
        """
        try:
            # יצירת הזמנה חדשה
            order = WooCommerceOrder(
                store_id=store_id,
                woo_id=woo_id,
                status=status,
                total=total,
                date_created=date_created,
                customer_id=customer_id,
                order_number=order_number,
                currency=currency,
                date_modified=date_modified,
                order_data=order_data or {}
            )
            
            session.add(order)
            await session.commit()
            await session.refresh(order)
            
            logger.info(f"נוצרה הזמנה חדשה: {order.id} (חנות: {store_id}, woo_id: {woo_id})")
            return order
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת הזמנה: {str(e)}")
            return None
            
    @staticmethod
    async def add_order_item(
        session: AsyncSession,
        order_id: int,
        name: str,
        quantity: int,
        product_id: Optional[int] = None,
        woo_product_id: Optional[int] = None,
        price: Optional[float] = None,
        total: Optional[float] = None,
        tax: Optional[float] = None,
        sku: Optional[str] = None,
        variation_id: Optional[int] = None,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceOrderItem]:
        """הוספת פריט להזמנה
        
        Args:
            session: סשן של מסד הנתונים
            order_id: מזהה ההזמנה
            name: שם הפריט
            quantity: כמות
            product_id: מזהה המוצר
            woo_product_id: מזהה המוצר בווקומרס
            price: מחיר הפריט
            total: סכום כולל
            tax: מס
            sku: מק"ט
            variation_id: מזהה הווריאציה
            meta_data: מטא-דאטה של הפריט
            
        Returns:
            הפריט שנוצר, None אם נכשל
        """
        try:
            # יצירת פריט חדש
            item = WooCommerceOrderItem(
                order_id=order_id,
                name=name,
                quantity=quantity,
                product_id=product_id,
                woo_product_id=woo_product_id,
                price=price,
                total=total,
                tax=tax,
                sku=sku,
                variation_id=variation_id,
                meta_data=meta_data or {}
            )
            
            session.add(item)
            await session.commit()
            await session.refresh(item)
            
            logger.info(f"נוצר פריט חדש בהזמנה: {item.id} (הזמנה: {order_id})")
            return item
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת פריט בהזמנה: {str(e)}")
            return None
            
    @staticmethod
    async def update_order_status(
        order_id: int,
        status: str,
        session: AsyncSession
    ) -> Optional[WooCommerceOrder]:
        """עדכון סטטוס הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            status: הסטטוס החדש
            session: סשן של מסד הנתונים
            
        Returns:
            ההזמנה המעודכנת, None אם נכשל
        """
        try:
            order = await OrderManager.get_order_by_id(order_id, session)
            if not order:
                logger.warning(f"לא נמצאה הזמנה עם מזהה {order_id}")
                return None
                
            order.status = status
            order.date_modified = datetime.now()
            
            await session.commit()
            await session.refresh(order)
            
            logger.info(f"עודכן סטטוס הזמנה {order_id} ל-{status}")
            return order
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה בעדכון סטטוס הזמנה {order_id}: {str(e)}")
            return None
            
    @staticmethod
    async def delete_order(order_id: int, session: AsyncSession) -> bool:
        """מחיקת הזמנה
        
        Args:
            order_id: מזהה ההזמנה
            session: סשן של מסד הנתונים
            
        Returns:
            True אם המחיקה הצליחה, False אחרת
        """
        try:
            # מחיקת כל הפריטים של ההזמנה
            await session.execute(
                delete(WooCommerceOrderItem).where(WooCommerceOrderItem.order_id == order_id)
            )
            
            # מחיקת ההזמנה עצמה
            result = await session.execute(
                delete(WooCommerceOrder).where(WooCommerceOrder.id == order_id)
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"נמחקה הזמנה: {order_id}")
                return True
            else:
                logger.warning(f"לא נמצאה הזמנה למחיקה: {order_id}")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה במחיקת הזמנה {order_id}: {str(e)}")
            return False 