"""
חבילת השירותים של WooCommerce.
מייצאת את כל השירותים הזמינים לשימוש.
"""
from .api.woocommerce_api import (
    WooCommerceAPI,
    CachedWooCommerceAPI,
    get_woocommerce_api,
    get_cached_woocommerce_api
)
from .services.product_service import ProductService
from .services.order_service import OrderService
from .services.customer_service import CustomerService
from .inventory.inventory_service import InventoryService
from .inventory.forecasting_service import ForecastingService
from .inventory.reporting_service import ReportingService
from .data import (
    get_order_status_info,
    get_woocommerce_knowledge_base,
    PRODUCT_TYPES,
    ORDER_STATUSES
)

__all__ = [
    # שירותי API בסיסיים
    'WooCommerceAPI',
    'CachedWooCommerceAPI',
    'get_woocommerce_api',
    'get_cached_woocommerce_api',
    
    # שירותים עיקריים
    'ProductService',
    'OrderService',
    'CustomerService',
    
    # שירותי מלאי
    'InventoryService',
    'ForecastingService',
    'ReportingService',
    
    # פונקציות עזר ונתונים
    'get_order_status_info',
    'get_woocommerce_knowledge_base',
    'PRODUCT_TYPES',
    'ORDER_STATUSES',
    
    # מחלקה המרכזת את כל שירותי WooCommerce
    'WooCommerceServices'
]

class WooCommerceServices:
    """
    מחלקה המרכזת את כל שירותי WooCommerce.
    מאפשרת גישה נוחה לכל השירותים ממקום אחד.
    """
    
    def __init__(
        self,
        url: str,
        consumer_key: str,
        consumer_secret: str
    ):
        """
        אתחול כל השירותים.
        
        Args:
            url: כתובת הבסיס של החנות
            consumer_key: מפתח הצרכן
            consumer_secret: סוד הצרכן
        """
        # יצירת מופע של ה-API
        self.api = WooCommerceAPI(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret
        )
        
        # יצירת מופעים של השירותים העיקריים
        self.products = ProductService(self.api)
        self.orders = OrderService(self.api)
        self.customers = CustomerService(self.api)
        
        # יצירת מופעים של שירותי המלאי
        self.inventory = InventoryService(self.api)
        self.forecasting = ForecastingService(self.api)
        self.reporting = ReportingService(self.api)
    
    async def initialize(self) -> None:
        """אתחול כל השירותים."""
        # אתחול שירותים עיקריים
        await self.products.initialize()
        await self.orders.initialize()
        await self.customers.initialize()
        
        # אתחול שירותי מלאי
        await self.inventory.initialize()
        await self.forecasting.initialize()
        await self.reporting.initialize()
    
    async def shutdown(self) -> None:
        """סגירת כל השירותים."""
        # סגירת שירותים עיקריים
        await self.products.shutdown()
        await self.orders.shutdown()
        await self.customers.shutdown()
        
        # סגירת שירותי מלאי
        await self.inventory.shutdown()
        await self.forecasting.shutdown()
        await self.reporting.shutdown() 