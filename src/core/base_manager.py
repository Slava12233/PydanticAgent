"""
מודול המכיל את מחלקת הבסיס למנהלים
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod

from src.services.woocommerce.api import WooCommerceAPI, CachedWooCommerceAPI

logger = logging.getLogger(__name__)

class BaseManager(ABC):
    """
    מחלקת בסיס למנהלי משאבים
    """
    
    def __init__(self, woocommerce_api: Union[WooCommerceAPI, CachedWooCommerceAPI], use_cache: bool = True, cache_ttl: int = 300):
        """
        אתחול מנהל המשאבים
        
        Args:
            woocommerce_api: אובייקט API של WooCommerce
            use_cache: האם להשתמש במטמון (ברירת מחדל: True)
            cache_ttl: זמן תפוגה של המטמון בשניות (ברירת מחדל: 5 דקות)
        """
        # בדיקה האם ה-API כבר עטוף במטמון
        if use_cache and not isinstance(woocommerce_api, CachedWooCommerceAPI):
            self.woocommerce = CachedWooCommerceAPI(woocommerce_api, cache_ttl)
            self.using_cache = True
        else:
            self.woocommerce = woocommerce_api
            self.using_cache = isinstance(woocommerce_api, CachedWooCommerceAPI)
        
        self.cache_ttl = cache_ttl
        self._resource_name = self._get_resource_name()
    
    @abstractmethod
    def _get_resource_name(self) -> str:
        """
        מחזיר את שם המשאב (למשל: "products", "orders" וכו')
        צריך להיות מיושם בכל מחלקה יורשת
        """
        pass
    
    async def create(self, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        יצירת משאב חדש
        
        Args:
            data: נתוני המשאב
            
        Returns:
            טאפל עם: האם הפעולה הצליחה, הודעה, המשאב שנוצר
        """
        try:
            status_code, response = await self.woocommerce._make_request("POST", self._resource_name, data=data)
            
            if status_code in (200, 201):
                logger.info(f"{self._resource_name} נוצר בהצלחה: {response.get('id', 'לא ידוע')}")
                return True, f"{self._resource_name} נוצר בהצלחה", response
            else:
                logger.error(f"שגיאה ביצירת {self._resource_name}: {status_code} - {response}")
                return False, f"שגיאה ביצירת {self._resource_name}", None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה ביצירת {self._resource_name}: {str(e)}")
            return False, f"שגיאה לא צפויה: {str(e)}", None
    
    async def get(self, resource_id: Union[int, str]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        קבלת משאב לפי מזהה
        
        Args:
            resource_id: מזהה המשאב
            
        Returns:
            טאפל עם: האם הפעולה הצליחה, הודעה, נתוני המשאב
        """
        try:
            status_code, response = await self.woocommerce._make_request("GET", f"{self._resource_name}/{resource_id}")
            
            if status_code == 200:
                return True, f"{self._resource_name} נמצא", response
            else:
                logger.error(f"שגיאה בקבלת {self._resource_name}: {status_code} - {response}")
                return False, f"שגיאה בקבלת {self._resource_name}", None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בקבלת {self._resource_name}: {str(e)}")
            return False, f"שגיאה לא צפויה: {str(e)}", None
    
    async def update(self, resource_id: Union[int, str], data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        עדכון משאב קיים
        
        Args:
            resource_id: מזהה המשאב
            data: נתוני המשאב לעדכון
            
        Returns:
            טאפל עם: האם הפעולה הצליחה, הודעה, המשאב המעודכן
        """
        try:
            status_code, response = await self.woocommerce._make_request("PUT", f"{self._resource_name}/{resource_id}", data=data)
            
            if status_code in (200, 201):
                logger.info(f"{self._resource_name} עודכן בהצלחה: {resource_id}")
                return True, f"{self._resource_name} עודכן בהצלחה", response
            else:
                logger.error(f"שגיאה בעדכון {self._resource_name}: {status_code} - {response}")
                return False, f"שגיאה בעדכון {self._resource_name}", None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בעדכון {self._resource_name}: {str(e)}")
            return False, f"שגיאה לא צפויה: {str(e)}", None
    
    async def delete(self, resource_id: Union[int, str], force: bool = False) -> Tuple[bool, str, None]:
        """
        מחיקת משאב
        
        Args:
            resource_id: מזהה המשאב
            force: האם למחוק לצמיתות
            
        Returns:
            טאפל עם: האם הפעולה הצליחה, הודעה, None
        """
        try:
            params = {"force": force}
            status_code, response = await self.woocommerce._make_request("DELETE", f"{self._resource_name}/{resource_id}", params=params)
            
            if status_code in (200, 201, 204):
                logger.info(f"{self._resource_name} נמחק בהצלחה: {resource_id}")
                return True, f"{self._resource_name} נמחק בהצלחה", None
            else:
                logger.error(f"שגיאה במחיקת {self._resource_name}: {status_code} - {response}")
                return False, f"שגיאה במחיקת {self._resource_name}", None
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה במחיקת {self._resource_name}: {str(e)}")
            return False, f"שגיאה לא צפויה: {str(e)}", None
    
    async def list(self, params: Dict[str, Any] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        קבלת רשימת משאבים
        
        Args:
            params: פרמטרים לסינון ומיון
            
        Returns:
            טאפל עם: האם הפעולה הצליחה, הודעה, רשימת משאבים
        """
        try:
            status_code, response = await self.woocommerce._make_request("GET", self._resource_name, params=params)
            
            if status_code == 200:
                return True, f"נמצאו {len(response)} {self._resource_name}", response
            else:
                logger.error(f"שגיאה בקבלת רשימת {self._resource_name}: {status_code} - {response}")
                return False, f"שגיאה בקבלת רשימת {self._resource_name}", []
                
        except Exception as e:
            logger.error(f"שגיאה לא צפויה בקבלת רשימת {self._resource_name}: {str(e)}")
            return False, f"שגיאה לא צפויה: {str(e)}", [] 