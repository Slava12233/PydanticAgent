"""
מודול לניהול לקוחות בחנות WooCommerce.
מאפשר יצירה, עדכון, מחיקה וקבלת מידע על לקוחות.
"""

import logging
from typing import Dict, List, Optional, Union, Any

from src.tools.woocommerce_tools import get_woocommerce_api
from src.tools.intent.customer_intent import extract_customer_data

logger = logging.getLogger(__name__)

class CustomerManager:
    """מנהל לקוחות המאפשר ביצוע פעולות על לקוחות בחנות WooCommerce."""

    def __init__(self):
        """אתחול מנהל הלקוחות."""
        self.api = get_woocommerce_api()

    def get_customers(self, **params) -> List[Dict]:
        """
        קבלת רשימת לקוחות מהחנות.

        Args:
            **params: פרמטרים לסינון הלקוחות.

        Returns:
            רשימת לקוחות.
        """
        try:
            return self.api.get("customers", params=params)
        except Exception as e:
            logger.error(f"שגיאה בקבלת רשימת לקוחות: {e}")
            return []

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """
        קבלת מידע על לקוח ספציפי.

        Args:
            customer_id: מזהה הלקוח.

        Returns:
            מידע על הלקוח או None אם הלקוח לא נמצא.
        """
        try:
            return self.api.get(f"customers/{customer_id}")
        except Exception as e:
            logger.error(f"שגיאה בקבלת מידע על לקוח {customer_id}: {e}")
            return None

    def create_customer(self, customer_data: Dict) -> Optional[Dict]:
        """
        יצירת לקוח חדש.

        Args:
            customer_data: נתוני הלקוח.

        Returns:
            הלקוח שנוצר או None אם היצירה נכשלה.
        """
        try:
            return self.api.post("customers", data=customer_data)
        except Exception as e:
            logger.error(f"שגיאה ביצירת לקוח: {e}")
            return None

    def update_customer(self, customer_id: int, customer_data: Dict) -> Optional[Dict]:
        """
        עדכון פרטי לקוח.

        Args:
            customer_id: מזהה הלקוח.
            customer_data: נתוני הלקוח המעודכנים.

        Returns:
            הלקוח המעודכן או None אם העדכון נכשל.
        """
        try:
            return self.api.put(f"customers/{customer_id}", data=customer_data)
        except Exception as e:
            logger.error(f"שגיאה בעדכון לקוח {customer_id}: {e}")
            return None

    def delete_customer(self, customer_id: int, force: bool = False) -> Optional[Dict]:
        """
        מחיקת לקוח.

        Args:
            customer_id: מזהה הלקוח.
            force: האם למחוק את הלקוח לצמיתות.

        Returns:
            תוצאת המחיקה או None אם המחיקה נכשלה.
        """
        try:
            return self.api.delete(f"customers/{customer_id}", params={"force": force})
        except Exception as e:
            logger.error(f"שגיאה במחיקת לקוח {customer_id}: {e}")
            return None

    def search_customers(self, search_term: str) -> List[Dict]:
        """
        חיפוש לקוחות לפי מונח חיפוש.

        Args:
            search_term: מונח החיפוש.

        Returns:
            רשימת לקוחות שתואמים את החיפוש.
        """
        try:
            return self.api.get("customers", params={"search": search_term})
        except Exception as e:
            logger.error(f"שגיאה בחיפוש לקוחות: {e}")
            return []

    def get_customer_orders(self, customer_id: int) -> List[Dict]:
        """
        קבלת רשימת הזמנות של לקוח ספציפי.

        Args:
            customer_id: מזהה הלקוח.

        Returns:
            רשימת הזמנות של הלקוח.
        """
        try:
            return self.api.get("orders", params={"customer": customer_id})
        except Exception as e:
            logger.error(f"שגיאה בקבלת הזמנות של לקוח {customer_id}: {e}")
            return []

def create_customer_from_text(text: str) -> Dict[str, Any]:
    """
    יצירת לקוח חדש מטקסט.

    Args:
        text: טקסט המכיל את פרטי הלקוח.

    Returns:
        תוצאת יצירת הלקוח.
    """
    customer_data = extract_customer_data(text)
    
    if not customer_data:
        return {"success": False, "message": "לא ניתן לחלץ נתוני לקוח מהטקסט."}
    
    required_fields = ["first_name", "last_name"]
    missing_fields = [field for field in required_fields if field not in customer_data]
    
    if missing_fields:
        return {
            "success": False,
            "message": f"חסרים שדות חובה: {', '.join(missing_fields)}",
            "extracted_data": customer_data
        }
    
    try:
        customer_manager = CustomerManager()
        result = customer_manager.create_customer(customer_data)
        
        if result:
            return {
                "success": True,
                "message": f"הלקוח {customer_data.get('first_name')} {customer_data.get('last_name')} נוצר בהצלחה.",
                "customer": result
            }
        else:
            return {
                "success": False,
                "message": "יצירת הלקוח נכשלה.",
                "extracted_data": customer_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה ביצירת הלקוח: {str(e)}",
            "extracted_data": customer_data
        }

def update_customer_from_text(customer_id: int, text: str) -> Dict[str, Any]:
    """
    עדכון פרטי לקוח מטקסט.

    Args:
        customer_id: מזהה הלקוח.
        text: טקסט המכיל את פרטי הלקוח המעודכנים.

    Returns:
        תוצאת עדכון הלקוח.
    """
    customer_data = extract_customer_data(text)
    
    if not customer_data:
        return {"success": False, "message": "לא ניתן לחלץ נתוני לקוח מהטקסט."}
    
    try:
        customer_manager = CustomerManager()
        result = customer_manager.update_customer(customer_id, customer_data)
        
        if result:
            return {
                "success": True,
                "message": f"פרטי הלקוח עודכנו בהצלחה.",
                "customer": result
            }
        else:
            return {
                "success": False,
                "message": f"עדכון פרטי הלקוח נכשל.",
                "extracted_data": customer_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בעדכון פרטי הלקוח: {str(e)}",
            "extracted_data": customer_data
        }

def update_customer_from_text(text: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    עדכון פרטי לקוח מטקסט.

    Args:
        text: טקסט המכיל את פרטי הלקוח המעודכנים.
        customer_id: מזהה הלקוח (אופציונלי). אם לא מסופק, ינסה לחלץ מהטקסט.

    Returns:
        תוצאת עדכון הלקוח.
    """
    customer_data = extract_customer_data(text)
    
    if not customer_data:
        return {"success": False, "message": "לא ניתן לחלץ נתוני לקוח מהטקסט."}
    
    try:
        customer_manager = CustomerManager()
        
        # אם לא סופק מזהה לקוח, ננסה לחלץ אותו מהטקסט
        if customer_id is None:
            # בדיקה אם יש מזהה בנתונים שחולצו
            if "id" in customer_data:
                customer_id = int(customer_data["id"])
                # הסרת המזהה מהנתונים לעדכון
                del customer_data["id"]
            else:
                # חיפוש לקוח לפי אימייל (אם יש)
                if "email" in customer_data:
                    customers = customer_manager.get_customers(email=customer_data["email"])
                    if customers and len(customers) > 0:
                        customer_id = customers[0]["id"]
                
                # אם עדיין אין מזהה, ננסה לחפש לפי שם מלא
                if customer_id is None and "first_name" in customer_data and "last_name" in customer_data:
                    full_name = f"{customer_data['first_name']} {customer_data['last_name']}".strip()
                    customers = customer_manager.search_customers(full_name)
                    if customers and len(customers) == 1:  # רק אם יש תוצאה אחת בדיוק
                        customer_id = customers[0]["id"]
        
        # אם עדיין אין מזהה לקוח, לא ניתן לעדכן
        if customer_id is None:
            return {
                "success": False,
                "message": "לא ניתן לזהות את הלקוח לעדכון. אנא ספק מזהה לקוח.",
                "extracted_data": customer_data
            }
        
        # עדכון הלקוח
        result = customer_manager.update_customer(customer_id, customer_data)
        
        if result:
            return {
                "success": True,
                "message": f"פרטי הלקוח עודכנו בהצלחה.",
                "customer": result
            }
        else:
            return {
                "success": False,
                "message": f"עדכון פרטי הלקוח נכשל.",
                "extracted_data": customer_data
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בעדכון פרטי הלקוח: {str(e)}",
            "extracted_data": customer_data
        }

def get_customer_info(customer_id: Optional[int] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
    """
    קבלת מידע על לקוח לפי מזהה, אימייל או טלפון.

    Args:
        customer_id: מזהה הלקוח.
        email: כתובת אימייל של הלקוח.
        phone: מספר טלפון של הלקוח.

    Returns:
        מידע על הלקוח.
    """
    customer_manager = CustomerManager()
    
    if customer_id:
        customer = customer_manager.get_customer(customer_id)
        if customer:
            return {
                "success": True,
                "message": f"נמצא לקוח עם מזהה {customer_id}.",
                "customer": customer
            }
    
    if email:
        customers = customer_manager.get_customers(email=email)
        if customers:
            return {
                "success": True,
                "message": f"נמצא לקוח עם אימייל {email}.",
                "customer": customers[0]
            }
    
    if phone:
        # חיפוש לפי טלפון דורש חיפוש בכל הלקוחות
        customers = customer_manager.get_customers()
        for customer in customers:
            if customer.get("billing", {}).get("phone") == phone:
                return {
                    "success": True,
                    "message": f"נמצא לקוח עם טלפון {phone}.",
                    "customer": customer
                }
    
    return {
        "success": False,
        "message": "לא נמצא לקוח עם הפרטים שסופקו."
    }

def get_customers_from_text(text: str) -> Dict[str, Any]:
    """
    חיפוש לקוחות לפי טקסט.

    Args:
        text: טקסט המכיל את פרטי החיפוש.

    Returns:
        תוצאת החיפוש.
    """
    customer_data = extract_customer_data(text)
    
    if not customer_data:
        return {"success": False, "message": "לא ניתן לחלץ פרטי חיפוש מהטקסט."}
    
    try:
        customer_manager = CustomerManager()
        
        # חיפוש לפי שם מלא
        if "first_name" in customer_data and "last_name" in customer_data:
            full_name = f"{customer_data['first_name']} {customer_data['last_name']}".strip()
            customers = customer_manager.search_customers(full_name)
            if customers:
                return {
                    "success": True,
                    "message": f"נמצאו {len(customers)} לקוחות עם השם {full_name}.",
                    "customers": customers
                }
        
        # חיפוש לפי אימייל
        if "email" in customer_data:
            customers = customer_manager.get_customers(email=customer_data["email"])
            if customers:
                return {
                    "success": True,
                    "message": f"נמצאו {len(customers)} לקוחות עם האימייל {customer_data['email']}.",
                    "customers": customers
                }
        
        # חיפוש לפי טלפון
        if "phone" in customer_data:
            # חיפוש לפי טלפון דורש חיפוש בכל הלקוחות
            all_customers = customer_manager.get_customers()
            matching_customers = []
            for customer in all_customers:
                if customer.get("billing", {}).get("phone") == customer_data["phone"]:
                    matching_customers.append(customer)
            
            if matching_customers:
                return {
                    "success": True,
                    "message": f"נמצאו {len(matching_customers)} לקוחות עם הטלפון {customer_data['phone']}.",
                    "customers": matching_customers
                }
        
        # חיפוש כללי
        search_term = ""
        if "first_name" in customer_data:
            search_term = customer_data["first_name"]
        elif "last_name" in customer_data:
            search_term = customer_data["last_name"]
        
        if search_term:
            customers = customer_manager.search_customers(search_term)
            if customers:
                return {
                    "success": True,
                    "message": f"נמצאו {len(customers)} לקוחות התואמים את החיפוש '{search_term}'.",
                    "customers": customers
                }
        
        return {
            "success": False,
            "message": "לא נמצאו לקוחות התואמים את החיפוש.",
            "extracted_data": customer_data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בחיפוש לקוחות: {str(e)}",
            "extracted_data": customer_data
        }

def get_customer_from_text(text: str) -> Dict[str, Any]:
    """
    חילוץ פרטי לקוח מטקסט וחיפוש לקוח ספציפי.

    Args:
        text: טקסט המכיל את פרטי הלקוח.

    Returns:
        תוצאת החיפוש.
    """
    customer_data = extract_customer_data(text)
    
    if not customer_data:
        return {"success": False, "message": "לא ניתן לחלץ פרטי לקוח מהטקסט."}
    
    try:
        customer_manager = CustomerManager()
        
        # חיפוש לפי מזהה לקוח
        if "id" in customer_data:
            customer = customer_manager.get_customer(int(customer_data["id"]))
            if customer:
                return {
                    "success": True,
                    "message": f"נמצא לקוח עם מזהה {customer_data['id']}.",
                    "customer": customer
                }
            else:
                return {
                    "success": False,
                    "message": f"לא נמצא לקוח עם מזהה {customer_data['id']}.",
                    "extracted_data": customer_data
                }
        
        # חיפוש לפי אימייל (אימייל הוא ייחודי)
        if "email" in customer_data:
            customers = customer_manager.get_customers(email=customer_data["email"])
            if customers and len(customers) > 0:
                return {
                    "success": True,
                    "message": f"נמצא לקוח עם אימייל {customer_data['email']}.",
                    "customer": customers[0]
                }
        
        # חיפוש לפי טלפון
        if "phone" in customer_data:
            all_customers = customer_manager.get_customers()
            for customer in all_customers:
                if customer.get("billing", {}).get("phone") == customer_data["phone"]:
                    return {
                        "success": True,
                        "message": f"נמצא לקוח עם טלפון {customer_data['phone']}.",
                        "customer": customer
                    }
        
        # חיפוש לפי שם מלא
        if "first_name" in customer_data and "last_name" in customer_data:
            full_name = f"{customer_data['first_name']} {customer_data['last_name']}".strip()
            customers = customer_manager.search_customers(full_name)
            if customers and len(customers) > 0:
                return {
                    "success": True,
                    "message": f"נמצא לקוח עם השם {full_name}.",
                    "customer": customers[0]
                }
        
        # אם לא נמצא לקוח ספציפי, נחזיר את תוצאות החיפוש הכללי
        return get_customers_from_text(text)
        
    except Exception as e:
        return {
            "success": False,
            "message": f"שגיאה בחיפוש לקוח: {str(e)}",
            "extracted_data": customer_data
        } 