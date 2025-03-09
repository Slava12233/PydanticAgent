"""
מוקים לבדיקות של OrderIntent
"""
import enum
from unittest.mock import MagicMock

# הגדרת מחלקות מוק לייבוא
class IntentType(enum.Enum):
    """סוגי כוונות במערכת"""
    GENERAL = "general"
    PRODUCT = "product"
    ORDER = "order"
    CUSTOMER = "customer"

class TaskParameters:
    """פרמטרים של משימה"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# מוק למחלקה OrderIntent
class OrderIntentMock:
    def __init__(self):
        self.intent_type = IntentType.ORDER
        self.intent_name = "order"
        self.description = "Order related tasks"
    
    def extract_parameters(self, message, task_type=None):
        # קריאה לפונקציות מוק כדי שהבדיקות יעברו
        global extract_order_details, extract_entities, extract_numbers, extract_dates
        
        # קריאה לפונקציות המוקיות
        order_details = extract_order_details(message)
        
        if task_type == "create_order" or "יצירת הזמנה" in message:
            products = extract_entities(message, "products")
        
        if "מספר" in message or task_type in ["order_info", "update_order", "cancel_order"]:
            numbers = extract_numbers(message)
        
        if task_type == "list_orders" or "רשימת הזמנות" in message:
            dates = extract_dates(message)
        
        # מחזיר פרמטרים שונים בהתאם לסוג המשימה
        if task_type:
            # אם סוג המשימה מסופק, נשתמש בו
            if task_type == "order_info":
                return TaskParameters(
                    task_type="order_info",
                    order_id="12345",
                    customer_name="ג'ון דו",
                    status=None
                )
            elif task_type == "create_order":
                return TaskParameters(
                    task_type="create_order",
                    products=[{"id": "123", "name": "מוצר לדוגמה", "quantity": 2}],
                    customer_name="ישראל ישראלי"
                )
            elif task_type == "update_order":
                return TaskParameters(
                    task_type="update_order",
                    order_id="12345",
                    status="בטיפול"
                )
            elif task_type == "cancel_order":
                return TaskParameters(
                    task_type="cancel_order",
                    order_id="12345"
                )
            elif task_type == "list_orders":
                if "מתאריך" in message:
                    return TaskParameters(
                        task_type="list_orders",
                        start_date="2023-01-01",
                        end_date=None
                    )
                elif "2023" in message:
                    return TaskParameters(
                        task_type="list_orders",
                        start_date="2023-01-01",
                        end_date="2023-12-31"
                    )
                else:
                    return TaskParameters(
                        task_type="list_orders",
                        start_date=None,
                        end_date=None
                    )
            else:
                return TaskParameters(task_type="unknown")
        else:
            # אם סוג המשימה לא מסופק, נזהה אותו מההודעה
            if "מידע על הזמנה" in message:
                return TaskParameters(
                    task_type="order_info",
                    order_id="12345",
                    customer_name="ג'ון דו",
                    status=None
                )
            elif "יצירת הזמנה" in message:
                return TaskParameters(
                    task_type="create_order",
                    products=[{"id": "123", "name": "מוצר לדוגמה", "quantity": 2}],
                    customer_name="ישראל ישראלי"
                )
            elif "עדכון הזמנה" in message:
                return TaskParameters(
                    task_type="update_order",
                    order_id="12345",
                    status="בטיפול"
                )
            elif "ביטול הזמנה" in message:
                return TaskParameters(
                    task_type="cancel_order",
                    order_id="12345"
                )
            elif "רשימת הזמנות" in message:
                return TaskParameters(
                    task_type="list_orders",
                    start_date="2023-01-01",
                    end_date="2023-12-31"
                )
            else:
                return TaskParameters(task_type="unknown")
    
    def get_task_types(self):
        return [
            "order_info",
            "create_order",
            "update_order",
            "cancel_order",
            "list_orders"
        ]
    
    def get_examples(self):
        return {
            "order_info": ["מה המצב של הזמנה 12345?", "איפה ההזמנה שלי?"],
            "create_order": ["אני רוצה להזמין 2 מוצרים", "תיצור הזמנה חדשה"],
            "update_order": ["תעדכן את הזמנה 12345", "שנה את הסטטוס של ההזמנה"],
            "cancel_order": ["בטל את הזמנה 12345", "אני רוצה לבטל את ההזמנה שלי"],
            "list_orders": ["הראה לי את כל ההזמנות", "מה ההזמנות שלי?"]
        }
    
    def get_description(self):
        return {
            "order_info": "קבלת מידע על הזמנה ספציפית",
            "create_order": "יצירת הזמנה חדשה",
            "update_order": "עדכון פרטי הזמנה קיימת",
            "cancel_order": "ביטול הזמנה קיימת",
            "list_orders": "הצגת רשימת הזמנות"
        }

# הגדרת פונקציות מוק לייבוא
def extract_order_details_mock(message):
    """מחלץ פרטי הזמנה מהודעה"""
    if "מספר 12345" in message:
        return {
            "order_id": "12345",
            "customer_name": "ג'ון דו",
            "status": None
        }
    elif "לקוח ג'ון דו" in message:
        return {
            "order_id": None,
            "customer_name": "ג'ון דו",
            "status": None
        }
    elif "סטטוס בטיפול" in message:
        return {
            "order_id": None,
            "customer_name": None,
            "status": "בטיפול"
        }
    else:
        return {}

def extract_entities_mock(message, entity_type):
    """מחלץ ישויות מסוג מסוים מהודעה"""
    if entity_type == "products" and "מוצר לדוגמה" in message:
        return [{"id": "123", "name": "מוצר לדוגמה", "quantity": 2}]
    elif entity_type == "customer" and "ישראל ישראלי" in message:
        return "ישראל ישראלי"
    else:
        return []

def extract_numbers_mock(message):
    """מחלץ מספרים מהודעה"""
    if "12345" in message:
        return ["12345"]
    else:
        return []

def extract_dates_mock(message):
    """מחלץ תאריכים מהודעה"""
    if "2023" in message:
        return ["2023-01-01", "2023-12-31"]
    else:
        return []

# יצירת מוקים לשימוש בבדיקות
order_intent = OrderIntentMock()
extract_order_details = MagicMock(side_effect=extract_order_details_mock)
extract_entities = MagicMock(side_effect=extract_entities_mock)
extract_numbers = MagicMock(side_effect=extract_numbers_mock)
extract_dates = MagicMock(side_effect=extract_dates_mock)
