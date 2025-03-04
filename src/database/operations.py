from typing import List, Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, time

from src.database.models import User, UserRole, Document, DocumentChunk, Message, WooCommerceStore, WooCommerceProduct, WooCommerceOrder, WooCommerceOrderItem
from src.utils.logger import setup_logger

# Configure logging
logger = setup_logger('database_operations')

async def get_all_users(session: AsyncSession) -> List[User]:
    """
    מחזיר את כל המשתמשים במערכת
    """
    result = await session.execute(select(User))
    return result.scalars().all()

async def get_all_documents(session: AsyncSession) -> List[Document]:
    """
    מחזיר את כל המסמכים במערכת
    """
    result = await session.execute(select(Document))
    return result.scalars().all()

async def update_user_role(user_id: int, role: UserRole, session: AsyncSession) -> Optional[User]:
    """
    עדכון תפקיד משתמש
    """
    user = await get_user_by_id(user_id, session)
    if not user:
        return None
    
    user.role = role
    await session.commit()
    return user

async def delete_document(doc_id: int, session: AsyncSession) -> bool:
    """
    מחיקת מסמך לפי מזהה
    """
    doc = await session.get(Document, doc_id)
    if not doc:
        return False
    
    # מחיקת כל החלקים הקשורים למסמך
    await session.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )
    
    # מחיקת המסמך עצמו
    await session.delete(doc)
    await session.commit()
    return True

async def get_user_documents(user_id: int, session: AsyncSession) -> List[Document]:
    """
    מחזיר את כל המסמכים של משתמש מסוים
    """
    result = await session.execute(
        select(Document).where(Document.user_id == user_id)
    )
    return result.scalars().all()

async def get_system_stats(session: AsyncSession) -> dict:
    """
    מחזיר סטטיסטיקות מערכת
    """
    # מספר משתמשים
    user_count_result = await session.execute(select(func.count()).select_from(User))
    user_count = user_count_result.scalar_one()
    
    # מספר מסמכים
    doc_count_result = await session.execute(select(func.count()).select_from(Document))
    doc_count = doc_count_result.scalar_one()
    
    # מספר הודעות
    message_count_result = await session.execute(select(func.count()).select_from(Message))
    message_count = message_count_result.scalar_one()
    
    # הודעות היום
    today = datetime.now().date()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    today_messages_result = await session.execute(
        select(func.count()).select_from(Message).where(
            Message.timestamp.between(today_start, today_end)
        )
    )
    today_messages = today_messages_result.scalar_one()
    
    return {
        "user_count": user_count,
        "doc_count": doc_count,
        "message_count": message_count,
        "today_messages": today_messages
    }

async def get_user_by_id(user_id: int, session: AsyncSession) -> Optional[User]:
    """
    מחזיר משתמש לפי מזהה
    """
    return await session.get(User, user_id)

async def get_user_by_telegram_id(telegram_id: int, session: AsyncSession) -> Optional[User]:
    """
    מחזיר משתמש לפי מזהה טלגרם
    """
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return await result.scalar()

# פונקציות לניהול חנויות ווקומרס

async def get_store_by_user_id(user_id: int, session: AsyncSession) -> Optional[WooCommerceStore]:
    """
    מחזיר את חנות הווקומרס של המשתמש
    """
    result = await session.execute(
        select(WooCommerceStore).where(
            WooCommerceStore.user_id == user_id,
            WooCommerceStore.is_active == True
        )
    )
    return result.scalars().first()

async def create_store(
    user_id: int, 
    store_url: str, 
    consumer_key: str, 
    consumer_secret: str, 
    session: AsyncSession,
    store_name: str = None
) -> WooCommerceStore:
    """
    יצירת חנות ווקומרס חדשה
    """
    # בדיקה אם כבר קיימת חנות פעילה למשתמש
    existing_store = await get_store_by_user_id(user_id, session)
    
    if existing_store:
        # עדכון החנות הקיימת
        existing_store.store_url = store_url
        existing_store.consumer_key = consumer_key
        existing_store.consumer_secret = consumer_secret
        if store_name:
            existing_store.store_name = store_name
        existing_store.is_active = True
        existing_store.last_sync = None
        
        await session.commit()
        return existing_store
    
    # יצירת חנות חדשה
    new_store = WooCommerceStore(
        user_id=user_id,
        store_url=store_url,
        store_name=store_name,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret
    )
    
    session.add(new_store)
    await session.commit()
    return new_store

async def update_store_settings(store_id: int, settings: dict, session: AsyncSession) -> Optional[WooCommerceStore]:
    """
    עדכון הגדרות חנות ווקומרס
    """
    store = await session.get(WooCommerceStore, store_id)
    if not store:
        return None
    
    # עדכון ההגדרות
    if store.settings:
        # מיזוג ההגדרות החדשות עם הקיימות
        store.settings.update(settings)
    else:
        store.settings = settings
    
    await session.commit()
    return store

async def save_woo_products(store_id: int, products: List[dict], session: AsyncSession) -> List[WooCommerceProduct]:
    """
    שמירת מוצרים מווקומרס במסד הנתונים
    """
    saved_products = []
    
    for product_data in products:
        woo_id = product_data.get('id')
        if not woo_id:
            continue
        
        # בדיקה אם המוצר כבר קיים
        result = await session.execute(
            select(WooCommerceProduct).where(
                WooCommerceProduct.store_id == store_id,
                WooCommerceProduct.woo_id == woo_id
            )
        )
        existing_product = result.scalars().first()
        
        if existing_product:
            # עדכון המוצר הקיים
            existing_product.name = product_data.get('name', '')
            existing_product.sku = product_data.get('sku')
            existing_product.price = float(product_data.get('price', 0))
            existing_product.regular_price = float(product_data.get('regular_price', 0)) if product_data.get('regular_price') else None
            existing_product.sale_price = float(product_data.get('sale_price', 0)) if product_data.get('sale_price') else None
            existing_product.stock_quantity = product_data.get('stock_quantity')
            existing_product.stock_status = product_data.get('stock_status')
            existing_product.product_data = product_data
            existing_product.last_updated = datetime.utcnow()
            
            saved_products.append(existing_product)
        else:
            # יצירת מוצר חדש
            new_product = WooCommerceProduct(
                store_id=store_id,
                woo_id=woo_id,
                name=product_data.get('name', ''),
                sku=product_data.get('sku'),
                price=float(product_data.get('price', 0)),
                regular_price=float(product_data.get('regular_price', 0)) if product_data.get('regular_price') else None,
                sale_price=float(product_data.get('sale_price', 0)) if product_data.get('sale_price') else None,
                stock_quantity=product_data.get('stock_quantity'),
                stock_status=product_data.get('stock_status'),
                product_data=product_data
            )
            
            session.add(new_product)
            saved_products.append(new_product)
    
    await session.commit()
    return saved_products

async def save_woo_orders(store_id: int, orders: List[dict], session: AsyncSession) -> List[WooCommerceOrder]:
    """
    שמירת הזמנות מווקומרס במסד הנתונים
    """
    saved_orders = []
    
    for order_data in orders:
        woo_id = order_data.get('id')
        if not woo_id:
            continue
        
        # בדיקה אם ההזמנה כבר קיימת
        result = await session.execute(
            select(WooCommerceOrder).where(
                WooCommerceOrder.store_id == store_id,
                WooCommerceOrder.woo_id == woo_id
            )
        )
        existing_order = result.scalars().first()
        
        # המרת תאריכים
        date_created = datetime.fromisoformat(order_data.get('date_created').replace('Z', '+00:00')) if order_data.get('date_created') else datetime.utcnow()
        date_modified = datetime.fromisoformat(order_data.get('date_modified').replace('Z', '+00:00')) if order_data.get('date_modified') else None
        
        if existing_order:
            # עדכון ההזמנה הקיימת
            existing_order.order_number = order_data.get('number')
            existing_order.status = order_data.get('status', '')
            existing_order.total = float(order_data.get('total', 0))
            existing_order.currency = order_data.get('currency')
            existing_order.date_created = date_created
            existing_order.date_modified = date_modified
            existing_order.order_data = order_data
            existing_order.last_updated = datetime.utcnow()
            
            saved_orders.append(existing_order)
        else:
            # יצירת הזמנה חדשה
            new_order = WooCommerceOrder(
                store_id=store_id,
                woo_id=woo_id,
                order_number=order_data.get('number'),
                status=order_data.get('status', ''),
                total=float(order_data.get('total', 0)),
                currency=order_data.get('currency'),
                date_created=date_created,
                date_modified=date_modified,
                order_data=order_data
            )
            
            session.add(new_order)
            await session.flush()  # כדי לקבל את ה-ID של ההזמנה החדשה
            
            # שמירת פריטי ההזמנה
            if 'line_items' in order_data:
                for item_data in order_data['line_items']:
                    new_item = WooCommerceOrderItem(
                        order_id=new_order.id,
                        name=item_data.get('name', ''),
                        quantity=item_data.get('quantity', 1),
                        price=float(item_data.get('price', 0)),
                        total=float(item_data.get('total', 0)),
                        item_data=item_data
                    )
                    
                    # קישור למוצר אם קיים
                    product_id = item_data.get('product_id')
                    if product_id:
                        product_result = await session.execute(
                            select(WooCommerceProduct).where(
                                WooCommerceProduct.store_id == store_id,
                                WooCommerceProduct.woo_id == product_id
                            )
                        )
                        product = product_result.scalars().first()
                        if product:
                            new_item.product_id = product.id
                    
                    session.add(new_item)
            
            saved_orders.append(new_order)
    
    await session.commit()
    return saved_orders

async def get_store_products(store_id: int, session: AsyncSession, limit: int = 10) -> List[WooCommerceProduct]:
    """
    קבלת מוצרים של חנות ווקומרס
    """
    result = await session.execute(
        select(WooCommerceProduct)
        .where(WooCommerceProduct.store_id == store_id)
        .order_by(WooCommerceProduct.last_updated.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_store_orders(store_id: int, session: AsyncSession, limit: int = 10) -> List[WooCommerceOrder]:
    """
    קבלת הזמנות של חנות ווקומרס
    """
    result = await session.execute(
        select(WooCommerceOrder)
        .where(WooCommerceOrder.store_id == store_id)
        .order_by(WooCommerceOrder.date_created.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_low_stock_products(store_id: int, session: AsyncSession, threshold: int = 5) -> List[WooCommerceProduct]:
    """
    קבלת מוצרים במלאי נמוך
    """
    result = await session.execute(
        select(WooCommerceProduct)
        .where(
            WooCommerceProduct.store_id == store_id,
            WooCommerceProduct.stock_quantity <= threshold,
            WooCommerceProduct.stock_quantity > 0
        )
        .order_by(WooCommerceProduct.stock_quantity)
    )
    return result.scalars().all()

async def get_out_of_stock_products(store_id: int, session: AsyncSession) -> List[WooCommerceProduct]:
    """
    קבלת מוצרים שאזל המלאי שלהם
    """
    result = await session.execute(
        select(WooCommerceProduct)
        .where(
            WooCommerceProduct.store_id == store_id,
            (WooCommerceProduct.stock_quantity == 0) | (WooCommerceProduct.stock_status == 'outofstock')
        )
    )
    return result.scalars().all()

async def update_user(user: User, session: AsyncSession) -> User:
    """
    עדכון פרטי משתמש
    """
    session.add(user)
    await session.commit()
    return user

async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None
) -> Optional[User]:
    """
    יצירת משתמש חדש
    
    Args:
        session: סשן בסיס נתונים
        telegram_id: מזהה טלגרם
        username: שם משתמש (אופציונלי)
        first_name: שם פרטי (אופציונלי)
        last_name: שם משפחה (אופציונלי)
        
    Returns:
        משתמש חדש אם נוצר בהצלחה, אחרת None
    """
    try:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        await session.commit()
        return user
    except Exception as e:
        logger.error(f"Error creating user {telegram_id}: {e}")
        await session.rollback()
        return None 