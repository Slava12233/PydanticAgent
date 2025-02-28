"""
מודלים למסד הנתונים של המערכת
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    """תפקידי משתמש במערכת"""
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    conversations = relationship("Conversation", back_populates="user")
    stores = relationship("WooCommerceStore", back_populates="user")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # קשרים
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    role = Column(String)  # 'user' או 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG (OpenAI embedding)
    
    # קשרים
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    source = Column(String)  # למשל: 'pdf', 'web', 'manual'
    content = Column(Text)
    doc_metadata = Column(JSON, default={})
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), index=True)
    content = Column(Text)
    chunk_index = Column(Integer)  # סדר הקטע במסמך המקורי
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG (OpenAI embedding)
    
    # קשרים
    document = relationship("Document", back_populates="chunks")

# מודלים חדשים לתמיכה בחנויות ווקומרס

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
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime, nullable=True)
    settings = Column(JSON, default={})
    
    # קשרים
    user = relationship("User", back_populates="stores")
    products = relationship("WooCommerceProduct", back_populates="store")
    orders = relationship("WooCommerceOrder", back_populates="store")
    customers = relationship("WooCommerceCustomer", back_populates="store")

class WooCommerceProduct(Base):
    """מודל לשמירת מוצרים מחנות ווקומרס"""
    __tablename__ = 'woocommerce_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    woo_id = Column(Integer, nullable=False)  # מזהה המוצר בווקומרס
    name = Column(String, nullable=False)
    sku = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    regular_price = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    stock_quantity = Column(Integer, nullable=True)
    stock_status = Column(String, nullable=True)  # 'instock', 'outofstock', 'onbackorder'
    product_data = Column(JSON, default={})  # נתונים נוספים על המוצר
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="products")

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
    date_created = Column(DateTime, nullable=False)
    date_modified = Column(DateTime, nullable=True)
    order_data = Column(JSON, default={})  # נתונים נוספים על ההזמנה
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="orders")
    customer = relationship("WooCommerceCustomer", back_populates="orders")
    items = relationship("WooCommerceOrderItem", back_populates="order")

class WooCommerceOrderItem(Base):
    """מודל לשמירת פריטים בהזמנה מחנות ווקומרס"""
    __tablename__ = 'woocommerce_order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('woocommerce_orders.id'), index=True)
    product_id = Column(Integer, ForeignKey('woocommerce_products.id'), nullable=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    item_data = Column(JSON, default={})  # נתונים נוספים על הפריט
    
    # קשרים
    order = relationship("WooCommerceOrder", back_populates="items")
    product = relationship("WooCommerceProduct")

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
    customer_data = Column(JSON, default={})  # נתונים נוספים על הלקוח
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="customers")
    orders = relationship("WooCommerceOrder", back_populates="customer") 