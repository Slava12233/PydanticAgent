"""
מודול לניהול מוצרים במסד הנתונים
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.woocommerce import WooCommerceProduct, WooCommerceStore
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ProductManager:
    """מחלקה לניהול מוצרים"""
    
    @staticmethod
    async def get_all_products(session: AsyncSession) -> List[WooCommerceProduct]:
        """קבלת כל המוצרים במערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת כל המוצרים
        """
        try:
            result = await session.execute(select(WooCommerceProduct))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת כל המוצרים: {str(e)}")
            raise
            
    @staticmethod
    async def get_product_by_id(product_id: int, session: AsyncSession) -> Optional[WooCommerceProduct]:
        """קבלת מוצר לפי מזהה
        
        Args:
            product_id: מזהה המוצר
            session: סשן של מסד הנתונים
            
        Returns:
            המוצר אם נמצא, None אחרת
        """
        try:
            return await session.get(WooCommerceProduct, product_id)
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצר {product_id}: {str(e)}")
            return None
            
    @staticmethod
    async def get_store_products(store_id: int, session: AsyncSession) -> List[WooCommerceProduct]:
        """קבלת כל המוצרים של חנות מסוימת
        
        Args:
            store_id: מזהה החנות
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת המוצרים של החנות
        """
        try:
            result = await session.execute(
                select(WooCommerceProduct).where(WooCommerceProduct.store_id == store_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת מוצרים של חנות {store_id}: {str(e)}")
            return []
            
    @staticmethod
    async def create_product(
        session: AsyncSession,
        store_id: int,
        woo_id: int,
        name: str,
        price: Optional[float] = None,
        description: Optional[str] = None,
        short_description: Optional[str] = None,
        sku: Optional[str] = None,
        status: Optional[str] = None,
        stock_status: Optional[str] = None,
        stock_quantity: Optional[int] = None,
        product_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceProduct]:
        """יצירת מוצר חדש
        
        Args:
            session: סשן של מסד הנתונים
            store_id: מזהה החנות
            woo_id: מזהה המוצר בווקומרס
            name: שם המוצר
            price: מחיר המוצר
            description: תיאור המוצר
            short_description: תיאור קצר של המוצר
            sku: מק"ט המוצר
            status: סטטוס המוצר
            stock_status: סטטוס המלאי
            stock_quantity: כמות במלאי
            product_data: נתונים נוספים על המוצר
            
        Returns:
            המוצר שנוצר, None אם נכשל
        """
        try:
            # יצירת מוצר חדש
            product = WooCommerceProduct(
                store_id=store_id,
                woo_id=woo_id,
                name=name,
                price=price,
                description=description,
                short_description=short_description,
                sku=sku,
                status=status,
                stock_status=stock_status,
                stock_quantity=stock_quantity,
                product_data=product_data or {}
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            logger.info(f"נוצר מוצר חדש: {product.id} (חנות: {store_id}, woo_id: {woo_id})")
            return product
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת מוצר: {str(e)}")
            return None
            
    @staticmethod
    async def update_product(
        product_id: int,
        session: AsyncSession,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
        short_description: Optional[str] = None,
        sku: Optional[str] = None,
        status: Optional[str] = None,
        stock_status: Optional[str] = None,
        stock_quantity: Optional[int] = None,
        product_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WooCommerceProduct]:
        """עדכון פרטי מוצר
        
        Args:
            product_id: מזהה המוצר
            session: סשן של מסד הנתונים
            name: שם המוצר החדש
            price: מחיר המוצר החדש
            description: תיאור המוצר החדש
            short_description: תיאור קצר חדש של המוצר
            sku: מק"ט המוצר החדש
            status: סטטוס המוצר החדש
            stock_status: סטטוס המלאי החדש
            stock_quantity: כמות במלאי החדשה
            product_data: נתונים נוספים חדשים על המוצר
            
        Returns:
            המוצר המעודכן, None אם נכשל
        """
        try:
            product = await ProductManager.get_product_by_id(product_id, session)
            if not product:
                logger.warning(f"לא נמצא מוצר עם מזהה {product_id}")
                return None
                
            if name is not None:
                product.name = name
            if price is not None:
                product.price = price
            if description is not None:
                product.description = description
            if short_description is not None:
                product.short_description = short_description
            if sku is not None:
                product.sku = sku
            if status is not None:
                product.status = status
            if stock_status is not None:
                product.stock_status = stock_status
            if stock_quantity is not None:
                product.stock_quantity = stock_quantity
            if product_data is not None:
                product.product_data = product_data
                
            await session.commit()
            await session.refresh(product)
            
            logger.info(f"עודכנו פרטי מוצר {product_id}")
            return product
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה בעדכון פרטי מוצר {product_id}: {str(e)}")
            return None
            
    @staticmethod
    async def delete_product(product_id: int, session: AsyncSession) -> bool:
        """מחיקת מוצר
        
        Args:
            product_id: מזהה המוצר
            session: סשן של מסד הנתונים
            
        Returns:
            True אם המחיקה הצליחה, False אחרת
        """
        try:
            # מחיקת המוצר
            result = await session.execute(
                delete(WooCommerceProduct).where(WooCommerceProduct.id == product_id)
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"נמחק מוצר: {product_id}")
                return True
            else:
                logger.warning(f"לא נמצא מוצר למחיקה: {product_id}")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה במחיקת מוצר {product_id}: {str(e)}")
            return False 