"""
חבילת שירותי המלאי.
מייצאת את כל השירותים הזמינים לשימוש.
"""
from .inventory_service import InventoryService
from .forecasting_service import ForecastingService
from .reporting_service import ReportingService

__all__ = [
    'InventoryService',
    'ForecastingService',
    'ReportingService'
]

class InventoryServices:
    """
    מחלקה המרכזת את כל שירותי המלאי.
    מאפשרת גישה נוחה לכל השירותים ממקום אחד.
    """
    
    def __init__(self, api):
        """
        אתחול כל השירותים.
        
        Args:
            api: מופע של WooCommerceAPI לתקשורת עם החנות
        """
        self.inventory = InventoryService(api)
        self.forecasting = ForecastingService(api)
        self.reporting = ReportingService(api)
    
    async def initialize(self) -> None:
        """אתחול כל השירותים."""
        await self.inventory.initialize()
        await self.forecasting.initialize()
        await self.reporting.initialize()
    
    async def shutdown(self) -> None:
        """סגירת כל השירותים."""
        await self.inventory.shutdown()
        await self.forecasting.shutdown()
        await self.reporting.shutdown() 