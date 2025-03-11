"""
מודלים הקשורים למשתמשים
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from src.database.models.base import Base

class UserRole(enum.Enum):
    """תפקידי משתמש במערכת"""
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"

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