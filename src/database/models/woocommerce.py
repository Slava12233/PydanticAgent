"""
מודלים הקשורים ל-WooCommerce
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.models.base import Base

class WooCommerceStore(Base):
    """מודל לשמירת פרטי חנות ווקומרס"""
    __tablename__ = 'woocommerce_stores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    store_url = Column(String, nullable=False)
    store_name = Column(String, nullable=True)
    consumer_key = Column(String, nullable=False)
    consumer_secret = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    settings = Column(JSON, default={})
    
    # קשרים
    user = relationship("User", back_populates="stores")
    products = relationship("WooCommerceProduct", back_populates="store")
    orders = relationship("WooCommerceOrder", back_populates="store")
    customers = relationship("WooCommerceCustomer", back_populates="store")
    payments = relationship("WooCommercePayment", back_populates="store")
    shipments = relationship("WooCommerceShipping", back_populates="store")
    notifications = relationship("Notification", back_populates="store")
    scheduled_tasks = relationship("ScheduledTask", back_populates="store")
    categories = relationship("WooCommerceCategory", back_populates="store")

class WooCommerceProduct(Base):
    """מודל לשמירת מוצרים מחנות ווקומרס"""
    __tablename__ = 'woocommerce_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    woo_id = Column(Integer, nullable=False)  # מזהה המוצר בווקומרס
    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    permalink = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    sku = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    regular_price = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    status = Column(String, nullable=True)  # 'publish', 'draft', etc.
    stock_status = Column(String, nullable=True)  # 'instock', 'outofstock', etc.
    stock_quantity = Column(Integer, nullable=True)
    weight = Column(String, nullable=True)
    dimensions = Column(JSON, default={})
    categories = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    images = Column(JSON, default=[])
    attributes = Column(JSON, default=[])
    variations = Column(JSON, default=[])
    product_data = Column(JSON, default={})  # נתונים נוספים על המוצר
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="products")
    order_items = relationship("WooCommerceOrderItem", back_populates="product")
    product_categories = relationship("WooCommerceProductCategory", back_populates="product")

class WooCommerceCategory(Base):
    """מודל לשמירת קטגוריות מחנות ווקומרס"""
    __tablename__ = 'woocommerce_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    woo_id = Column(Integer, nullable=False)  # מזהה הקטגוריה בווקומרס
    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    parent_id = Column(Integer, nullable=True)  # מזהה הקטגוריה האב
    description = Column(Text, nullable=True)
    display = Column(String, nullable=True)
    image = Column(JSON, default={})
    count = Column(Integer, default=0)  # מספר המוצרים בקטגוריה
    category_data = Column(JSON, default={})  # נתונים נוספים על הקטגוריה
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="categories")
    product_categories = relationship("WooCommerceProductCategory", back_populates="category")

class WooCommerceProductCategory(Base):
    """מודל לקשר בין מוצרים לקטגוריות"""
    __tablename__ = 'woocommerce_product_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('woocommerce_products.id'), index=True)
    category_id = Column(Integer, ForeignKey('woocommerce_categories.id'), index=True)
    
    # קשרים
    product = relationship("WooCommerceProduct", back_populates="product_categories")
    category = relationship("WooCommerceCategory", back_populates="product_categories")

class WooCommerceCustomer(Base):
    """מודל לשמירת לקוחות מחנות ווקומרס"""
    __tablename__ = 'woocommerce_customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    woo_id = Column(Integer, nullable=False)  # מזהה הלקוח בווקומרס
    email = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    billing = Column(JSON, default={})
    shipping = Column(JSON, default={})
    is_paying_customer = Column(Boolean, default=False)
    customer_data = Column(JSON, default={})  # נתונים נוספים על הלקוח
    created_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="customers")
    orders = relationship("WooCommerceOrder", back_populates="customer")

class WooCommerceOrderItem(Base):
    """מודל לשמירת פריטים בהזמנה מחנות ווקומרס"""
    __tablename__ = 'woocommerce_order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('woocommerce_orders.id'), index=True)
    product_id = Column(Integer, ForeignKey('woocommerce_products.id'), nullable=True)
    woo_product_id = Column(Integer, nullable=True)  # מזהה המוצר בווקומרס
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    sku = Column(String, nullable=True)
    variation_id = Column(Integer, nullable=True)
    meta_data = Column(JSON, default={})
    
    # קשרים
    order = relationship("WooCommerceOrder", back_populates="items")
    product = relationship("WooCommerceProduct", back_populates="order_items")

class WooCommercePayment(Base):
    """מודל לשמירת תשלומים מחנות ווקומרס"""
    __tablename__ = 'woocommerce_payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    order_id = Column(Integer, ForeignKey('woocommerce_orders.id'), nullable=True)
    woo_id = Column(Integer, nullable=True)  # מזהה התשלום בווקומרס
    method = Column(String, nullable=True)
    method_title = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=True)
    payment_data = Column(JSON, default={})  # נתונים נוספים על התשלום
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="payments")
    order = relationship("WooCommerceOrder", back_populates="payments")

class WooCommerceShipping(Base):
    """מודל לשמירת משלוחים מחנות ווקומרס"""
    __tablename__ = 'woocommerce_shipping'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    order_id = Column(Integer, ForeignKey('woocommerce_orders.id'), nullable=True)
    woo_id = Column(Integer, nullable=True)  # מזהה המשלוח בווקומרס
    method = Column(String, nullable=True)
    method_title = Column(String, nullable=True)
    tracking_number = Column(String, nullable=True)
    tracking_url = Column(String, nullable=True)
    status = Column(String, nullable=True)
    date_shipped = Column(DateTime(timezone=True), nullable=True)
    shipping_data = Column(JSON, default={})  # נתונים נוספים על המשלוח
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="shipments")
    order = relationship("WooCommerceOrder", back_populates="shipments")

class WooCommerceOrder(Base):
    """מודל לשמירת הזמנות מחנות ווקומרס"""
    __tablename__ = 'woocommerce_orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    woo_id = Column(Integer, nullable=False)  # מזהה ההזמנה בווקומרס
    customer_id = Column(Integer, ForeignKey('woocommerce_customers.id'), nullable=True)
    order_number = Column(String, nullable=True)
    status = Column(String, nullable=False)  # 'pending', 'processing', 'completed', etc.
    total = Column(Float, nullable=False)
    currency = Column(String, nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=False)
    date_modified = Column(DateTime(timezone=True), nullable=True)
    order_data = Column(JSON, default={})  # נתונים נוספים על ההזמנה
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="orders")
    customer = relationship("WooCommerceCustomer", back_populates="orders")
    items = relationship("WooCommerceOrderItem", back_populates="order")
    payments = relationship("WooCommercePayment", back_populates="order")
    shipments = relationship("WooCommerceShipping", back_populates="order") 