"""
מודול לניהול לקוחות ב-WooCommerce
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from ..woocommerce.api.api import WooCommerceAPI, CachedWooCommerceAPI
from ..core.base_manager import BaseManager

logger = logging.getLogger(__name__)

class CustomerManager(BaseManager):
    """
    מחלקה לניהול לקוחות
    """

    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב
        """
        return "customers"

    async def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        יצירת לקוח חדש
        
        Args:
            customer_data: נתוני הלקוח
            
        Returns:
            הלקוח שנוצר או None אם היצירה נכשלה
        """
        # שימוש בפונקציית create של מחלקת הבסיס
        success, message, response = await self.create(customer_data)
        return response if success else None

    async def get_customer(self, customer_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        קבלת פרטי לקוח
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            פרטי הלקוח או None אם לא נמצא
        """
        try:
            customer_id = int(customer_id)
        except ValueError:
            logger.error(f"מזהה לקוח לא תקין: {customer_id}")
            return None
        
        # שימוש בפונקציית get של מחלקת הבסיס
        success, message, response = await self.get(customer_id)
        return response if success else None

    async def update_customer(self, customer_id: Union[int, str], customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        עדכון פרטי לקוח
        
        Args:
            customer_id: מזהה הלקוח
            customer_data: נתוני הלקוח לעדכון
            
        Returns:
            הלקוח המעודכן או None אם העדכון נכשל
        """
        try:
            customer_id = int(customer_id)
        except ValueError:
            logger.error(f"מזהה לקוח לא תקין: {customer_id}")
            return None
        
        # שימוש בפונקציית update של מחלקת הבסיס
        success, message, response = await self.update(customer_id, customer_data)
        return response if success else None

    async def delete_customer(self, customer_id: Union[int, str], force: bool = False) -> bool:
        """
        מחיקת לקוח
        
        Args:
            customer_id: מזהה הלקוח
            force: האם למחוק לצמיתות
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            customer_id = int(customer_id)
        except ValueError:
            logger.error(f"מזהה לקוח לא תקין: {customer_id}")
            return False
        
        # שימוש בפונקציית delete של מחלקת הבסיס
        success, message, _ = await self.delete(customer_id, force)
        return success

    async def search_customers(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        חיפוש לקוחות
        
        Args:
            search_term: מונח החיפוש
            limit: מספר התוצאות המקסימלי
            
        Returns:
            רשימת לקוחות שתואמים את החיפוש
        """
        params = {
            "search": search_term,
            "per_page": limit
        }
        
        # שימוש בפונקציית list של מחלקת הבסיס
        success, message, response = await self.list(params)
        return response if success else []

    async def get_customer_orders(self, customer_id: Union[int, str]) -> List[Dict[str, Any]]:
        """
        קבלת רשימת ההזמנות של לקוח
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            רשימת ההזמנות של הלקוח
        """
        try:
            customer_id = int(customer_id)
        except ValueError:
            logger.error(f"מזהה לקוח לא תקין: {customer_id}")
            return []
        
        params = {
            "customer": customer_id
        }
        
        # שימוש בפונקציית list של מחלקת הבסיס עם resource_name="orders"
        success, message, response = await self.list("orders", params=params)
        
        if success:
            return response
        else:
            logger.error(f"שגיאה בקבלת הזמנות לקוח {customer_id}: {message}")
            return []

    async def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        חיפוש לקוח לפי כתובת דוא"ל
        
        Args:
            email: כתובת הדוא"ל לחיפוש
            
        Returns:
            פרטי הלקוח או None אם לא נמצא
        """
        params = {
            "email": email
        }
        
        # שימוש בפונקציית list של מחלקת הבסיס
        success, message, customers = await self.list(params)
        
        if success and customers:
            # מחזירים את הלקוח הראשון שנמצא
            return customers[0]
        else:
            logger.error(f"שגיאה בחיפוש לקוח לפי אימייל {email}: {message}")
            return None