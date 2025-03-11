"""
מודול המכיל את השירות לניהול מוצרים.
"""
from typing import Dict, Any, List, Optional
from src.services.base.base_service import BaseService, ServiceResponse
from src.woocommerce.api.api import WooCommerceAPI

class ProductService(BaseService):
    """
    שירות לניהול מוצרים בחנות.
    מספק פעולות ליצירה, עדכון, מחיקה וחיפוש של מוצרים.
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
    
    async def create_product(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יוצר מוצר חדש.
        
        Args:
            data: נתוני המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        required_params = ['name', 'regular_price']
        return await self._handle_request(
            'create_product',
            self._create_product,
            data,
            required_params
        )
    
    async def update_product(self, product_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        מעדכן מוצר קיים.
        
        Args:
            product_id: מזהה המוצר
            data: נתוני העדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'update_product',
            self._update_product,
            product_id,
            data
        )
    
    async def delete_product(self, product_id: int) -> ServiceResponse:
        """
        מוחק מוצר.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'delete_product',
            self._delete_product,
            product_id
        )
    
    async def get_product(self, product_id: int) -> ServiceResponse:
        """
        מקבל מידע על מוצר.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'get_product',
            self._get_product,
            product_id
        )
    
    async def list_products(self, params: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        מקבל רשימת מוצרים.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        return await self._handle_request(
            'list_products',
            self._list_products,
            params or {}
        )
    
    async def search_products(self, query: str) -> ServiceResponse:
        """
        חיפוש מוצרים לפי מחרוזת חיפוש.
        
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
            'search_products',
            self._list_products,
            params
        )
    
    async def update_product_image(self, product_id: int, image_url: str) -> ServiceResponse:
        """
        עדכון תמונת מוצר.
        
        Args:
            product_id: מזהה המוצר
            image_url: כתובת התמונה
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        try:
            status_code, response = await self.api.update_product_image(product_id, image_url)
            
            if 200 <= status_code < 300:
                return ServiceResponse(
                    success=True,
                    data=response,
                    message="תמונת המוצר עודכנה בהצלחה"
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"שגיאה בעדכון תמונת המוצר: {status_code}",
                    data=response
                )
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בעדכון תמונת המוצר: {str(e)}"
            )
    
    async def _create_product(self, data: Dict[str, Any]) -> ServiceResponse:
        """
        יצירת מוצר - מימוש פנימי.
        
        Args:
            data: נתוני המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.create_product(data)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response,
                message="המוצר נוצר בהצלחה"
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה ביצירת המוצר: {status_code}",
                data=response
            )
    
    async def _update_product(self, product_id: int, data: Dict[str, Any]) -> ServiceResponse:
        """
        עדכון מוצר - מימוש פנימי.
        
        Args:
            product_id: מזהה המוצר
            data: נתוני העדכון
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.update_product(product_id, data)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response,
                message="המוצר עודכן בהצלחה"
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בעדכון המוצר: {status_code}",
                data=response
            )
    
    async def _delete_product(self, product_id: int) -> ServiceResponse:
        """
        מחיקת מוצר - מימוש פנימי.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.delete_product(product_id, force=True)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response,
                message="המוצר נמחק בהצלחה"
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה במחיקת המוצר: {status_code}",
                data=response
            )
    
    async def _get_product(self, product_id: int) -> ServiceResponse:
        """
        קבלת מידע על מוצר - מימוש פנימי.
        
        Args:
            product_id: מזהה המוצר
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.get_product(product_id)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת המוצר: {status_code}",
                data=response
            )
    
    async def _list_products(self, params: Dict[str, Any]) -> ServiceResponse:
        """
        קבלת רשימת מוצרים - מימוש פנימי.
        
        Args:
            params: פרמטרים לסינון התוצאות
            
        Returns:
            ServiceResponse עם תוצאת הפעולה
        """
        status_code, response = await self.api.get_products(params)
        
        if 200 <= status_code < 300:
            return ServiceResponse(
                success=True,
                data=response
            )
        else:
            return ServiceResponse(
                success=False,
                error=f"שגיאה בקבלת רשימת המוצרים: {status_code}",
                data=response
            ) 