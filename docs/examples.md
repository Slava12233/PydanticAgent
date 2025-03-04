# דוגמאות שימוש

מסמך זה מכיל דוגמאות מפורטות לשימוש במערכת.

## ניהול מוצרים

### יצירת מוצר חדש

```python
from src.tools.store_tools.managers.product_manager import ProductManager
from src.tools.store_tools.models import Product, Category

async def create_new_product():
    # יצירת מנהל מוצרים
    product_manager = ProductManager()
    
    # הגדרת נתוני המוצר
    product_data = {
        "name": "חולצת כותנה",
        "description": "חולצת כותנה איכותית 100% כותנה",
        "regular_price": "99.90",
        "categories": ["ביגוד", "חולצות"],
        "attributes": [
            {
                "name": "צבע",
                "options": ["לבן", "שחור", "אפור"]
            },
            {
                "name": "מידה",
                "options": ["S", "M", "L", "XL"]
            }
        ],
        "images": [
            {
                "src": "https://example.com/images/shirt-white.jpg",
                "alt": "חולצה לבנה"
            }
        ],
        "manage_stock": True,
        "stock_quantity": 100,
        "low_stock_amount": 10
    }
    
    try:
        # יצירת המוצר
        product = await product_manager.create_product(product_data)
        print(f"נוצר מוצר חדש: {product.name} (ID: {product.id})")
        
        # עדכון תמונות נוספות
        additional_images = [
            "https://example.com/images/shirt-black.jpg",
            "https://example.com/images/shirt-gray.jpg"
        ]
        await product_manager.add_product_images(product.id, additional_images)
        
        return product
    except Exception as e:
        print(f"שגיאה ביצירת המוצר: {e}")
        return None
```

### עדכון מלאי

```python
from src.tools.store_tools.managers.inventory_manager import InventoryManager

async def update_stock_levels():
    # יצירת מנהל מלאי
    inventory_manager = InventoryManager()
    
    try:
        # עדכון כמות מלאי
        product_id = 123
        new_quantity = 50
        await inventory_manager.update_stock_quantity(product_id, new_quantity)
        
        # קבלת מצב מלאי עדכני
        stock_info = await inventory_manager.get_stock_info(product_id)
        print(f"מצב מלאי עדכני: {stock_info['stock_quantity']} יחידות")
        
        # בדיקת מלאי נמוך
        if stock_info["stock_quantity"] <= stock_info["low_stock_amount"]:
            print("⚠️ אזהרה: מלאי נמוך!")
            
    except Exception as e:
        print(f"שגיאה בעדכון המלאי: {e}")
```

## ניהול הזמנות

### יצירת הזמנה חדשה

```python
from src.tools.store_tools.managers.order_manager import OrderManager
from src.tools.store_tools.models import Order, OrderItem

async def create_new_order():
    # יצירת מנהל הזמנות
    order_manager = OrderManager()
    
    # הגדרת פרטי ההזמנה
    order_data = {
        "customer_id": 456,
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "address_1": "רחוב הרצל 1",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6123001",
            "country": "IL",
            "email": "israel@example.com",
            "phone": "0501234567"
        },
        "shipping": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "address_1": "רחוב הרצל 1",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6123001",
            "country": "IL"
        },
        "line_items": [
            {
                "product_id": 123,
                "quantity": 2
            },
            {
                "product_id": 124,
                "quantity": 1
            }
        ],
        "shipping_lines": [
            {
                "method_id": "flat_rate",
                "method_title": "משלוח רגיל",
                "total": "15.00"
            }
        ]
    }
    
    try:
        # יצירת ההזמנה
        order = await order_manager.create_order(order_data)
        print(f"נוצרה הזמנה חדשה: #{order.id}")
        
        # שליחת אימייל אישור
        await order_manager.send_order_confirmation(order.id)
        
        return order
    except Exception as e:
        print(f"שגיאה ביצירת ההזמנה: {e}")
        return None
```

### מעקב אחר הזמנה

```python
async def track_order(order_id: int):
    # יצירת מנהל הזמנות
    order_manager = OrderManager()
    
    try:
        # קבלת פרטי ההזמנה
        order = await order_manager.get_order(order_id)
        
        # קבלת היסטוריית סטטוסים
        status_history = await order_manager.get_status_history(order_id)
        
        print(f"מצב הזמנה #{order_id}:")
        print(f"סטטוס נוכחי: {order.status}")
        print("\nהיסטוריית סטטוסים:")
        for status in status_history:
            print(f"- {status['date']}: {status['status']}")
            
        # בדיקת מצב משלוח
        if order.status == "completed":
            shipping_info = await order_manager.get_shipping_info(order_id)
            print(f"\nפרטי משלוח:")
            print(f"חברת שילוח: {shipping_info['company']}")
            print(f"מספר מעקב: {shipping_info['tracking_number']}")
            
    except Exception as e:
        print(f"שגיאה בקבלת פרטי ההזמנה: {e}")
```

## ניהול לקוחות

### יצירת לקוח חדש

```python
from src.tools.store_tools.managers.customer_manager import CustomerManager

async def create_new_customer():
    # יצירת מנהל לקוחות
    customer_manager = CustomerManager()
    
    # הגדרת פרטי הלקוח
    customer_data = {
        "email": "israel@example.com",
        "first_name": "ישראל",
        "last_name": "ישראלי",
        "username": "israel123",
        "billing": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "company": "",
            "address_1": "רחוב הרצל 1",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6123001",
            "country": "IL",
            "email": "israel@example.com",
            "phone": "0501234567"
        },
        "shipping": {
            "first_name": "ישראל",
            "last_name": "ישראלי",
            "company": "",
            "address_1": "רחוב הרצל 1",
            "city": "תל אביב",
            "state": "TA",
            "postcode": "6123001",
            "country": "IL"
        }
    }
    
    try:
        # יצירת הלקוח
        customer = await customer_manager.create_customer(customer_data)
        print(f"נוצר לקוח חדש: {customer.first_name} {customer.last_name} (ID: {customer.id})")
        
        # שליחת אימייל ברוכים הבאים
        await customer_manager.send_welcome_email(customer.id)
        
        return customer
    except Exception as e:
        print(f"שגיאה ביצירת הלקוח: {e}")
        return None
```

### ניתוח התנהגות לקוח

```python
async def analyze_customer_behavior(customer_id: int):
    # יצירת מנהל לקוחות
    customer_manager = CustomerManager()
    
    try:
        # קבלת היסטוריית הזמנות
        orders = await customer_manager.get_customer_orders(customer_id)
        
        # ניתוח דפוסי קנייה
        total_spent = sum(order.total for order in orders)
        avg_order_value = total_spent / len(orders) if orders else 0
        favorite_categories = await customer_manager.get_favorite_categories(customer_id)
        last_purchase = max(orders, key=lambda x: x.date_created) if orders else None
        
        print(f"ניתוח התנהגות לקוח {customer_id}:")
        print(f"סה\"כ הזמנות: {len(orders)}")
        print(f"סה\"כ קניות: ₪{total_spent:.2f}")
        print(f"ממוצע להזמנה: ₪{avg_order_value:.2f}")
        print("\nקטגוריות מועדפות:")
        for category in favorite_categories:
            print(f"- {category['name']}: {category['count']} קניות")
        if last_purchase:
            print(f"\nקנייה אחרונה: {last_purchase.date_created}")
            
    except Exception as e:
        print(f"שגיאה בניתוח התנהגות הלקוח: {e}")
```

## ניטור ומטריקות

### מעקב אחר ביצועי API

```python
from src.monitoring.metrics import metrics
from src.monitoring.alerts import alert_manager, AlertRule, AlertSeverity
from datetime import datetime, timedelta

async def monitor_api_performance():
    # הגדרת כלל התראה לזמני תגובה
    alert_manager.add_rule(AlertRule(
        name="high_response_time",
        check_func=lambda: metrics.get_average("api_response_time") > 1000,
        message="זמני תגובה גבוהים מהרגיל",
        severity=AlertSeverity.WARNING
    ))
    
    try:
        # מדידת זמן תגובה
        metrics.start_timer("api_call")
        result = await make_api_call()
        metrics.stop_timer("api_call")
        
        # ניתוח ביצועים
        last_hour = datetime.now() - timedelta(hours=1)
        stats = metrics.get_summary(start_time=last_hour)
        
        print("סטטיסטיקות API בשעה האחרונה:")
        for metric, values in stats.items():
            print(f"\n{metric}:")
            print(f"ממוצע: {values['avg']:.2f}")
            print(f"מינימום: {values['min']:.2f}")
            print(f"מקסימום: {values['max']:.2f}")
            print(f"אחוזון 95: {values['p95']:.2f}")
            
    except Exception as e:
        print(f"שגיאה בניטור ביצועי API: {e}")
```

### ניטור משאבי מערכת

```python
from src.monitoring.performance import SystemMonitor
import asyncio

async def monitor_system_resources():
    # יצירת מנטר מערכת
    system_monitor = SystemMonitor()
    
    try:
        while True:
            # קבלת נתוני מערכת
            stats = system_monitor.get_system_stats()
            
            print("\nמצב משאבי מערכת:")
            print(f"CPU: {stats['cpu_usage']}%")
            print(f"זיכרון: {stats['memory_usage']}%")
            print(f"דיסק: {stats['disk_usage']}%")
            
            # המתנה לסבב הבא
            await asyncio.sleep(60)
            
    except Exception as e:
        print(f"שגיאה בניטור משאבי מערכת: {e}")
```

## שימוש בתבניות

### עיצוב הודעות מותאמות אישית

```python
from src.templates.template_manager import TemplateManager

async def format_custom_messages():
    # יצירת מנהל תבניות
    templates = TemplateManager()
    
    try:
        # הודעת ברוכים הבאים
        welcome_template = templates.get_template("welcome_message")
        welcome_message = templates.format_template(welcome_template, {
            "first_name": "ישראל",
            "store_name": "החנות שלי"
        })
        
        # הודעת אישור הזמנה
        order_template = templates.get_template("order_confirmation")
        order_message = templates.format_template(order_template, {
            "order_id": "12345",
            "total": "199.90",
            "shipping_method": "משלוח רגיל",
            "estimated_delivery": "2-3 ימי עסקים"
        })
        
        # הודעת מלאי נמוך
        stock_template = templates.get_template("low_stock_alert")
        stock_message = templates.format_template(stock_template, {
            "product_name": "חולצת כותנה",
            "current_stock": 5,
            "threshold": 10
        })
        
        print("הודעות מעוצבות:")
        print("\nברוכים הבאים:")
        print(welcome_message)
        print("\nאישור הזמנה:")
        print(order_message)
        print("\nהתראת מלאי:")
        print(stock_message)
        
    except Exception as e:
        print(f"שגיאה בעיצוב ההודעות: {e}")
``` 