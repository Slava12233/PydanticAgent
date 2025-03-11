"""
מודלים למסד הנתונים של המערכת
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB
# מבטלים את הייבוא של Vector כרגע כי ההרחבה לא מותקנת
# from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class UserRole(enum.Enum):
    """תפקידי משתמש במערכת"""
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"

class NotificationType(enum.Enum):
    """סוגי התראות במערכת"""
    ORDER = "order"           # התראה על הזמנה חדשה
    PRODUCT = "product"       # התראה על מוצר (מלאי נמוך, שינוי מחיר וכו')
    CUSTOMER = "customer"     # התראה על לקוח (לקוח חדש, עדכון פרטים וכו')
    SYSTEM = "system"         # התראת מערכת (תחזוקה, עדכונים וכו')
    PAYMENT = "payment"       # התראה על תשלום (תשלום חדש, תשלום שנכשל וכו')
    SHIPPING = "shipping"     # התראה על משלוח (משלוח חדש, עדכון סטטוס וכו')
    MARKETING = "marketing"   # התראה על קמפיין שיווקי
    OTHER = "other"           # התראה אחרת

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    conversations = relationship("Conversation", back_populates="user")
    stores = relationship("WooCommerceStore", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    settings = relationship("BotSettings", back_populates="user", uselist=False)
    scheduled_tasks = relationship("ScheduledTask", back_populates="user")
    documents = relationship("Document", back_populates="user")
    user_messages = relationship("Message", back_populates="user")

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

class TaskType(enum.Enum):
    """סוגי משימות מתוזמנות"""
    SYNC_PRODUCTS = "sync_products"
    SYNC_ORDERS = "sync_orders"
    SYNC_CUSTOMERS = "sync_customers"
    BACKUP = "backup"
    REPORT = "report"
    CUSTOM = "custom"

class TaskStatus(enum.Enum):
    """סטטוס משימה מתוזמנת"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScheduledTask(Base):
    """מודל למשימות מתוזמנות"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), nullable=True)
    type = Column(Enum(TaskType), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cron_expression = Column(String, nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    task_data = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="scheduled_tasks")
    store = relationship("WooCommerceStore", back_populates="scheduled_tasks")

class Conversation(Base):
    """מודל לשמירת שיחות"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # קשרים
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """מודל לשמירת הודעות בשיחה"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # תשובת המערכת להודעה
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata = Column(JSON, default={})
    
    # קשרים
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="user_messages")

class Document(Base):
    """מודל לשמירת מסמכים"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """מודל לשמירת חלקי מסמכים"""
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # שינוי מ-Vector ל-ARRAY של Float
    embedding = Column(ARRAY(Float), nullable=True)  # שימוש זמני ב-ARRAY(Float) במקום Vector
    chunk_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('ix_document_chunks_doc_id_chunk_idx', 'document_id', 'chunk_index'),
    )

class Notification(Base):
    """מודל להתראות"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)  # 'order', 'product', 'customer', etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_data = Column(JSON, default={})
    
    # קשרים
    user = relationship("User", back_populates="notifications")
    store = relationship("WooCommerceStore", back_populates="notifications")

class BotSettings(Base):
    """מודל להגדרות הבוט"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), unique=True)
    language = Column(String, default='he')
    timezone = Column(String, default='Asia/Jerusalem')
    notifications_enabled = Column(Boolean, default=True)
    daily_reports_enabled = Column(Boolean, default=False)
    weekly_reports_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    settings_data = Column(JSON, default={})
    
    # קשרים
    user = relationship("User", back_populates="settings")

class Memory(Base):
    """מודל לשמירת זיכרונות המערכת"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    memory_type = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    conversation = relationship("Conversation", back_populates="memories")