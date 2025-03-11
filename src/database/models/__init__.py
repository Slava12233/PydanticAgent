"""
מודלים של מסד הנתונים
"""
from src.database.models.base import Base
from src.database.models.users import (
    User, UserRole, BotSettings, Notification, NotificationType,
    ScheduledTask, TaskType, TaskStatus
)
from src.database.models.woocommerce import (
    WooCommerceStore, WooCommerceProduct, WooCommerceCategory,
    WooCommerceProductCategory, WooCommerceCustomer, WooCommerceOrderItem,
    WooCommercePayment, WooCommerceShipping, WooCommerceOrder
)
from src.database.models.conversations import (
    Conversation, Message, Memory
)
from src.database.models.documents import (
    Document, DocumentChunk
)

# ייצוא כל המודלים
__all__ = [
    'Base',
    # Users
    'User', 'UserRole', 'BotSettings', 'Notification', 'NotificationType',
    'ScheduledTask', 'TaskType', 'TaskStatus',
    # WooCommerce
    'WooCommerceStore', 'WooCommerceProduct', 'WooCommerceCategory',
    'WooCommerceProductCategory', 'WooCommerceCustomer', 'WooCommerceOrderItem',
    'WooCommercePayment', 'WooCommerceShipping', 'WooCommerceOrder',
    # Conversations
    'Conversation', 'Message', 'Memory',
    # Documents
    'Document', 'DocumentChunk'
]
