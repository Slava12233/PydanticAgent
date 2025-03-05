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

class Base(DeclarativeBase):
    pass

class UserRole(enum.Enum):
    """תפקידי משתמש במערכת"""
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"

class NotificationType(enum.Enum):
    """סוגי התראות במערכת"""
    SYSTEM = "system"  # התראת מערכת
    USER = "user"  # התראת משתמש
    INVENTORY = "inventory"  # התראת מלאי
    ORDER = "order"  # התראת הזמנה
    PAYMENT = "payment"  # התראת תשלום
    SHIPPING = "shipping"  # התראת משלוח

class TaskType(enum.Enum):
    """סוגי משימות מתוזמנות"""
    NOTIFICATION = "notification"  # שליחת התראה
    REPORT = "report"  # הפקת דוח
    BACKUP = "backup"  # גיבוי נתונים
    SYNC = "sync"  # סנכרון נתונים
    CLEANUP = "cleanup"  # ניקוי נתונים
    CUSTOM = "custom"  # משימה מותאמת אישית

class TaskStatus(enum.Enum):
    """סטטוסי משימות מתוזמנות"""
    PENDING = "pending"  # ממתין לביצוע
    RUNNING = "running"  # בביצוע
    COMPLETED = "completed"  # הושלם
    FAILED = "failed"  # נכשל
    CANCELLED = "cancelled"  # בוטל

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
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

class BotSettings(Base):
    """מודל להגדרות הבוט"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), unique=True)
    language = Column(String, default='he')  # קוד שפה (he, en, ru, ar)
    timezone = Column(String, default='Asia/Jerusalem')  # אזור זמן
    currency = Column(String, default='ILS')  # קוד מטבע
    theme = Column(String, default='light')  # עיצוב (light, dark, colorful, minimal)
    privacy_level = Column(String, default='medium')  # רמת פרטיות (max, medium, min, custom)
    notification_level = Column(String, default='all')  # רמת התראות (all, none, important, custom)
    api_keys = Column(JSON, default={})  # מפתחות API
    preferences = Column(JSON, default={})  # העדפות נוספות
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="settings")

class MemoryType(enum.Enum):
    """סוגי זיכרון"""
    SHORT_TERM = "short_term"  # זיכרון קצר טווח - רלוונטי לשיחה הנוכחית
    LONG_TERM = "long_term"    # זיכרון ארוך טווח - תובנות ומידע חשוב לשמירה
    WORKING = "working"        # זיכרון עבודה - מידע זמני לעיבוד

class MemoryPriority(enum.Enum):
    """רמות עדיפות לזיכרון"""
    LOW = "low"        # מידע שולי
    MEDIUM = "medium"  # מידע חשוב
    HIGH = "high"      # מידע קריטי
    URGENT = "urgent"  # מידע דחוף

class ConversationMemory(Base):
    """מודל לשמירת זיכרון שיחה מתקדם"""
    __tablename__ = 'conversation_memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    memory_type = Column(Enum(MemoryType), nullable=False)
    priority = Column(Enum(MemoryPriority), default=MemoryPriority.MEDIUM)
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG
    context = Column(Text, nullable=True)  # הקשר בו נוצר הזיכרון
    source_message_ids = Column(ARRAY(Integer))  # מזהי ההודעות שיצרו את הזיכרון
    memory_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())  # מעקב אחר שימוש בזיכרון
    access_count = Column(Integer, default=0)  # מונה שימושים
    relevance_score = Column(Float, default=1.0)  # ציון רלוונטיות (יורד עם הזמן)
    is_active = Column(Boolean, default=True)  # האם הזיכרון פעיל
    
    # קשרים
    conversation = relationship("Conversation", back_populates="memories")
    
    # אינדקסים
    __table_args__ = (
        Index('ix_memories_type_priority', memory_type, priority),
        Index('ix_memories_relevance', relevance_score.desc()),
    )

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    context = Column(JSON, default={})  # הקשר כללי של השיחה
    summary = Column(Text, nullable=True)  # תקציר השיחה המתעדכן
    
    # קשרים
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    memories = relationship("ConversationMemory", back_populates="conversation")  # קשר חדש

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    role = Column(String)  # 'user' או 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG
    message_metadata = Column(JSON, default={})  # מטא-דאטה נוסף (רגשות, כוונות, וכו')
    is_memory_processed = Column(Boolean, default=False)  # האם ההודעה עובדה לזיכרונות
    
    # קשרים
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    source = Column(String)  # למשל: 'pdf', 'web', 'manual'
    content = Column(Text)
    doc_metadata = Column(JSON, default={})
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), index=True)
    content = Column(Text)
    chunk_index = Column(Integer)  # סדר הקטע במסמך המקורי
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG
    chunk_metadata = Column(JSON, default={})
    
    # קשרים
    document = relationship("Document", back_populates="chunks")
    
    # אינדקסים לביצועים
    __table_args__ = (
        # אינדקס משולב לחיפוש לפי מסמך וסדר הקטעים
        Index('ix_document_chunks_doc_idx', document_id, chunk_index),
    )

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
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
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
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="customers")
    orders = relationship("WooCommerceOrder", back_populates="customer")

class WooCommercePayment(Base):
    """מודל לשמירת תשלומים מחנות ווקומרס"""
    __tablename__ = 'woocommerce_payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), index=True)
    order_id = Column(Integer, ForeignKey('woocommerce_orders.id'), nullable=True)
    woo_id = Column(Integer, nullable=False)  # מזהה התשלום בווקומרס
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True)
    method = Column(String, nullable=False)  # 'credit_card', 'bit', 'paypal', 'bank_transfer', 'cash'
    status = Column(String, nullable=False)  # 'pending', 'completed', 'failed', 'refunded'
    transaction_id = Column(String, nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=False)
    date_modified = Column(DateTime(timezone=True), nullable=True)
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
    woo_id = Column(Integer, nullable=False)  # מזהה המשלוח בווקומרס
    method = Column(String, nullable=False)  # 'self_pickup', 'store_delivery', 'courier', 'post_office', 'express'
    status = Column(String, nullable=False)  # 'pending', 'processing', 'shipped', 'delivered', 'failed', 'returned'
    tracking_number = Column(String, nullable=True)
    shipping_address = Column(String, nullable=True)
    shipping_notes = Column(Text, nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=False)
    date_modified = Column(DateTime(timezone=True), nullable=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    actual_delivery = Column(DateTime(timezone=True), nullable=True)
    shipping_data = Column(JSON, default={})  # נתונים נוספים על המשלוח
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    store = relationship("WooCommerceStore", back_populates="shipments")
    order = relationship("WooCommerceOrder", back_populates="shipments")

class Notification(Base):
    """מודל לשמירת התראות"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    send_time = Column(DateTime(timezone=True), nullable=False)
    sent_time = Column(DateTime(timezone=True), nullable=True)
    read_time = Column(DateTime(timezone=True), nullable=True)
    notification_data = Column(JSON, default={})  # נתונים נוספים על ההתראה
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="notifications")
    store = relationship("WooCommerceStore", back_populates="notifications")

class ScheduledTask(Base):
    """מודל למשימות מתוזמנות"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)  # משתמש שיצר את המשימה
    store_id = Column(Integer, ForeignKey('woocommerce_stores.id'), nullable=True)  # חנות רלוונטית
    type = Column(Enum(TaskType), nullable=False)  # סוג המשימה
    name = Column(String, nullable=False)  # שם המשימה
    description = Column(Text, nullable=True)  # תיאור המשימה
    cron_expression = Column(String, nullable=True)  # ביטוי CRON לתזמון
    interval_seconds = Column(Integer, nullable=True)  # מרווח זמן בשניות
    next_run = Column(DateTime(timezone=True), nullable=True)  # מועד הריצה הבא
    last_run = Column(DateTime(timezone=True), nullable=True)  # מועד הריצה האחרון
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)  # סטטוס המשימה
    task_data = Column(JSON, default={})  # נתונים נוספים למשימה
    error_message = Column(Text, nullable=True)  # הודעת שגיאה אחרונה
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="scheduled_tasks")
    store = relationship("WooCommerceStore", back_populates="scheduled_tasks")

class Memory(Base):
    """מודל לשמירת זיכרונות בסיסיים"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user' או 'assistant'
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # אינדקסים
    __table_args__ = (
        Index('ix_memories_timestamp', timestamp.desc()),
    ) 