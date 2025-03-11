"""
מודול המכיל את השירות לניהול לקוחות.
"""
from typing import Dict, Any, List, Optional
from src.services.base.base_service import BaseService, ServiceResponse
from src.woocommerce.api.api import WooCommerceAPI

class CustomerService(BaseService):
    """
    שירות לניהול לקוחות בחנות.
    מספק פעולות ליצירה, עדכון, מחיקה וחיפוש של לקוחות.
    """
    
    def __init__(self, api: WooCommerceAPI):
        """
        אתחול השירות.
        
        Args:
            api: מופע של WooCommerceAPI לתקשורת עם החנות
        """
        super().__init__()
        self.api = api
    
    async def initialize(self) -> None:
        """אתחול השירות."""
        # אין צורך באתחול מיוחד כרגע
        pass
    
    async def shutdown(self) -> None:
        """סגירת השירות."""
        # אין צורך בסגירה מיוחדת כרגע
        pass
    
    async def get_customer(self, customer_id: int) -> ServiceResponse:
        """
        מקבל מידע על לקוח.
        
        Args:
            customer_id: מזהה הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            status_code, response = await self.api.get(f"customers/{customer_id}")
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה בקבלת הלקוח: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת הלקוח: {str(e)}"
            )
    
    async def list_customers(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מקבל רשימת לקוחות.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_customers',
            self._list_customers,
            params or {}
        )
    
    async def create_customer(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יוצר לקוח חדש.
        
        Args:
            data: נתוני הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        required_params = ['email']
        return await self._handle_request(
            'create_customer',
            self._create_customer,
            data,
            required_params
        )
    
    async def update_customer(self, customer_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        מעדכן לקוח קיים.
        
        Args:
            customer_id: מזהה הלקוח
            data: נתוני העדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            status_code, response = await self.api.put(f"customers/{customer_id}", data)
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response,
                    message="הלקוח עודכן בהצלחה"
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה בעדכון הלקוח: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בעדכון הלקוח: {str(e)}"
            )
    
    async def delete_customer(self, customer_id: int, force: bool = False) -> ServiceResponse:
        """
        מוחק לקוח.
        
        Args:
            customer_id: מזהה הלקוח
            force: האם למחוק לצמיתות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            params = {"force": "true"} if force else {}
            status_code, response = await self.api.delete(f"customers/{customer_id}", params)
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response,
                    message="הלקוח נמחק בהצלחה"
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה במחיקת הלקוח: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה במחיקת הלקוח: {str(e)}"
            )
    
    async def search_customers(self, query: str) -> ServiceResponse:
        """
        חיפוש לקוחות לפי מחרוזת חיפוש.
        
        Args:
            query: מחרוזת החיפוש
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'search': query,
            'per_page': 20
        }
        
        return await self._handle_request(
            'search_customers',
            self._list_customers,
            params
        )
    
    async def get_customer_by_email(self, email: str) -> ServiceResponse:
        """
        קבלת לקוח לפי כתובת אימייל.
        
        Args:
            email: כתובת האימייל
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        params = {
            'email': email
        }
        
        try:
            status_code, response = await self.api.get("customers", params)
            
            if 200 <= status_code < 300:
                if response and len(response) > 0:
                    return ServiceResponse(
                        success=True,
                        data=response[0]
                    )
                else:
                    return ServiceResponse(
                        success=False,
                        error=f"לא נמצא לקוח עם האימייל: {email}"
                    )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה בחיפוש לקוח לפי אימייל: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בחיפוש לקוח לפי אימייל: {str(e)}"
            )
    
    async def _list_customers(self, params: Dict[str, Any]) -> ServiceResponse:
        """
        קבלת רשימת לקוחות - מימוש פנימי.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            status_code, response = await self.api.get("customers", params)
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה בקבלת רשימת הלקוחות: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת רשימת הלקוחות: {str(e)}"
            )
    
    async def _create_customer(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יצירת לקוח - מימוש פנימי.
        
        Args:
            data: נתוני הלקוח
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            status_code, response = await self.api.post("customers", data)
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response,
                    message="הלקוח נוצר בהצלחה"
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה ביצירת הלקוח: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה ביצירת הלקוח: {str(e)}"
            ) 