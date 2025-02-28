"""
מיגרציה להוספת טבלאות ווקומרס למסד הנתונים
"""
import logging
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Table, MetaData
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# הגדרת לוגר
logger = logging.getLogger(__name__)

def upgrade():
    """
    שדרוג: הוספת טבלאות ווקומרס למסד הנתונים
    """
    try:
        # בדיקה אם הטבלאות כבר קיימות
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        tables = inspector.get_table_names()
        
        # יצירת טבלת חנויות ווקומרס
        if 'woocommerce_stores' not in tables:
            op.create_table(
                'woocommerce_stores',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id'), index=True),
                sa.Column('store_url', sa.String, nullable=False),
                sa.Column('store_name', sa.String, nullable=True),
                sa.Column('consumer_key', sa.String, nullable=False),
                sa.Column('consumer_secret', sa.String, nullable=False),
                sa.Column('is_active', sa.Boolean, default=True),
                sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
                sa.Column('last_sync', sa.DateTime, nullable=True),
                sa.Column('settings', sa.JSON, default={})
            )
            logger.info("נוצרה טבלת 'woocommerce_stores'")
        else:
            logger.info("טבלת 'woocommerce_stores' כבר קיימת")
        
        # יצירת טבלת לקוחות ווקומרס
        if 'woocommerce_customers' not in tables:
            op.create_table(
                'woocommerce_customers',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('store_id', sa.Integer, sa.ForeignKey('woocommerce_stores.id'), index=True),
                sa.Column('woo_id', sa.Integer, nullable=False),
                sa.Column('email', sa.String, nullable=True),
                sa.Column('first_name', sa.String, nullable=True),
                sa.Column('last_name', sa.String, nullable=True),
                sa.Column('username', sa.String, nullable=True),
                sa.Column('customer_data', sa.JSON, default={}),
                sa.Column('last_updated', sa.DateTime, default=datetime.utcnow)
            )
            logger.info("נוצרה טבלת 'woocommerce_customers'")
        else:
            logger.info("טבלת 'woocommerce_customers' כבר קיימת")
        
        # יצירת טבלת מוצרים ווקומרס
        if 'woocommerce_products' not in tables:
            op.create_table(
                'woocommerce_products',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('store_id', sa.Integer, sa.ForeignKey('woocommerce_stores.id'), index=True),
                sa.Column('woo_id', sa.Integer, nullable=False),
                sa.Column('name', sa.String, nullable=False),
                sa.Column('sku', sa.String, nullable=True),
                sa.Column('price', sa.Float, nullable=True),
                sa.Column('regular_price', sa.Float, nullable=True),
                sa.Column('sale_price', sa.Float, nullable=True),
                sa.Column('stock_quantity', sa.Integer, nullable=True),
                sa.Column('stock_status', sa.String, nullable=True),
                sa.Column('product_data', sa.JSON, default={}),
                sa.Column('last_updated', sa.DateTime, default=datetime.utcnow)
            )
            logger.info("נוצרה טבלת 'woocommerce_products'")
        else:
            logger.info("טבלת 'woocommerce_products' כבר קיימת")
        
        # יצירת טבלת הזמנות ווקומרס
        if 'woocommerce_orders' not in tables:
            op.create_table(
                'woocommerce_orders',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('store_id', sa.Integer, sa.ForeignKey('woocommerce_stores.id'), index=True),
                sa.Column('woo_id', sa.Integer, nullable=False),
                sa.Column('customer_id', sa.Integer, sa.ForeignKey('woocommerce_customers.id'), nullable=True),
                sa.Column('order_number', sa.String, nullable=True),
                sa.Column('status', sa.String, nullable=False),
                sa.Column('total', sa.Float, nullable=False),
                sa.Column('currency', sa.String, nullable=True),
                sa.Column('date_created', sa.DateTime, nullable=False),
                sa.Column('date_modified', sa.DateTime, nullable=True),
                sa.Column('order_data', sa.JSON, default={}),
                sa.Column('last_updated', sa.DateTime, default=datetime.utcnow)
            )
            logger.info("נוצרה טבלת 'woocommerce_orders'")
        else:
            logger.info("טבלת 'woocommerce_orders' כבר קיימת")
        
        # יצירת טבלת פריטי הזמנה ווקומרס
        if 'woocommerce_order_items' not in tables:
            op.create_table(
                'woocommerce_order_items',
                sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('order_id', sa.Integer, sa.ForeignKey('woocommerce_orders.id'), index=True),
                sa.Column('product_id', sa.Integer, sa.ForeignKey('woocommerce_products.id'), nullable=True),
                sa.Column('name', sa.String, nullable=False),
                sa.Column('quantity', sa.Integer, nullable=False),
                sa.Column('price', sa.Float, nullable=False),
                sa.Column('total', sa.Float, nullable=False),
                sa.Column('item_data', sa.JSON, default={})
            )
            logger.info("נוצרה טבלת 'woocommerce_order_items'")
        else:
            logger.info("טבלת 'woocommerce_order_items' כבר קיימת")
            
    except Exception as e:
        logger.error(f"שגיאה בהוספת טבלאות ווקומרס: {str(e)}")
        raise

def downgrade():
    """
    שחזור: הסרת טבלאות ווקומרס ממסד הנתונים
    """
    try:
        # הסרת הטבלאות בסדר הפוך
        op.drop_table('woocommerce_order_items')
        logger.info("הוסרה טבלת 'woocommerce_order_items'")
        
        op.drop_table('woocommerce_orders')
        logger.info("הוסרה טבלת 'woocommerce_orders'")
        
        op.drop_table('woocommerce_products')
        logger.info("הוסרה טבלת 'woocommerce_products'")
        
        op.drop_table('woocommerce_customers')
        logger.info("הוסרה טבלת 'woocommerce_customers'")
        
        op.drop_table('woocommerce_stores')
        logger.info("הוסרה טבלת 'woocommerce_stores'")
        
    except Exception as e:
        logger.error(f"שגיאה בהסרת טבלאות ווקומרס: {str(e)}")
        raise 