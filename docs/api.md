# תיעוד API פנימי

## מבוא

מסמך זה מתאר את ה-API הפנימי של המערכת. המערכת בנויה ממספר מודולים עיקריים:

1. **מודול הסוכן (Agent)** - אחראי על האינטראקציה עם המשתמש והבנת הכוונות
2. **מודול החנות (Store)** - מטפל בכל הקשור לניהול החנות (מוצרים, הזמנות, לקוחות)
3. **מודול הניטור (Monitoring)** - אחראי על מעקב אחר ביצועי המערכת והתראות
4. **מודול התבניות (Templates)** - מנהל את התבניות לתשובות בשפות שונות

## מודול הסוכן

### `TelegramAgent`

מחלקה המטפלת באינטראקציה עם המשתמש דרך טלגרם.

#### מתודות עיקריות

- `async def handle_message(message: str) -> str`
  - מטפל בהודעת טקסט מהמשתמש
  - מחזיר תשובה מתאימה

- `async def handle_command(command: str, args: List[str]) -> str`
  - מטפל בפקודה מהמשתמש
  - מחזיר תשובה מתאימה

### `IntentRecognizer`

מחלקה לזיהוי כוונות המשתמש.

#### מתודות עיקריות

- `async def recognize_intent(text: str) -> Intent`
  - מזהה את כוונת המשתמש מתוך טקסט
  - מחזיר אובייקט `Intent` עם פרטי הכוונה

## מודול החנות

### `ProductManager`

מחלקה לניהול מוצרים בחנות.

#### מתודות עיקריות

- `async def get_product(id: int) -> Product`
  - מקבל מזהה מוצר
  - מחזיר פרטי מוצר

- `async def create_product(data: Dict[str, Any]) -> Product`
  - מקבל נתוני מוצר
  - יוצר מוצר חדש ומחזיר אותו

### `OrderManager`

מחלקה לניהול הזמנות.

#### מתודות עיקריות

- `async def get_order(id: int) -> Order`
  - מקבל מזהה הזמנה
  - מחזיר פרטי הזמנה

- `async def create_order(data: Dict[str, Any]) -> Order`
  - מקבל נתוני הזמנה
  - יוצר הזמנה חדשה ומחזיר אותה

### `CustomerManager`

מחלקה לניהול לקוחות.

#### מתודות עיקריות

- `async def get_customer(id: int) -> Customer`
  - מקבל מזהה לקוח
  - מחזיר פרטי לקוח

- `async def create_customer(data: Dict[str, Any]) -> Customer`
  - מקבל נתוני לקוח
  - יוצר לקוח חדש ומחזיר אותו

## מודול הניטור

### `MetricsCollector`

מחלקה לאיסוף מטריקות ביצועים.

#### מתודות עיקריות

- `def record_metric(name: str, value: float, labels: Dict[str, str] = None)`
  - מקבל שם מטריקה, ערך ותוויות
  - מתעד את המטריקה

- `def get_metrics(name: str, start_time: datetime = None) -> List[MetricPoint]`
  - מקבל שם מטריקה וזמן התחלה
  - מחזיר רשימת נקודות מדידה

### `AlertManager`

מחלקה לניהול התראות.

#### מתודות עיקריות

- `def add_rule(rule: AlertRule)`
  - מקבל כלל התראה
  - מוסיף אותו למערכת

- `def handle_alert(alert: Alert)`
  - מקבל התראה
  - מטפל בה לפי ההגדרות

## מודול התבניות

### `TemplateManager`

מחלקה לניהול תבניות תשובה.

#### מתודות עיקריות

- `def get_template(name: str, language: str = "he") -> str`
  - מקבל שם תבנית ושפה
  - מחזיר את התבנית בשפה המבוקשת

- `def format_template(template: str, params: Dict[str, Any]) -> str`
  - מקבל תבנית ופרמטרים
  - מחזיר את התבנית המעוצבת עם הפרמטרים

## דוגמאות שימוש

### טיפול בהודעת משתמש

```python
# יצירת סוכן
agent = TelegramAgent()

# טיפול בהודעה
message = "מה המחיר של המוצר הזה?"
response = await agent.handle_message(message)
print(response)
```

### יצירת מוצר חדש

```python
# יצירת מנהל מוצרים
product_manager = ProductManager()

# יצירת מוצר חדש
product_data = {
    "name": "מוצר לדוגמה",
    "price": 99.99,
    "description": "תיאור המוצר"
}
product = await product_manager.create_product(product_data)
print(f"נוצר מוצר חדש: {product.name}")
```

### ניטור ביצועים

```python
# יצירת אוסף מטריקות
metrics = MetricsCollector()

# מדידת זמן פעולה
metrics.start_timer("api_call")
result = await some_api_call()
metrics.stop_timer("api_call")

# קבלת סטטיסטיקות
stats = metrics.get_summary()
print(f"סטטיסטיקות: {stats}")
```

### שימוש בתבניות

```python
# יצירת מנהל תבניות
templates = TemplateManager()

# קבלת תבנית ועיצוב
template = templates.get_template("product_added")
message = templates.format_template(template, {
    "name": "מוצר חדש",
    "price": "99.99"
})
print(message)
```

## טיפול בשגיאות

המערכת משתמשת במספר סוגי שגיאות מותאמים:

### `StoreError`

שגיאות הקשורות לפעולות בחנות:

```python
try:
    product = await product_manager.get_product(999)
except ProductNotFoundError as e:
    print(f"המוצר לא נמצא: {e}")
except StoreError as e:
    print(f"שגיאה בחנות: {e}")
```

### `APIError`

שגיאות בקריאות API:

```python
try:
    result = await api_client.make_request()
except APITimeoutError as e:
    print(f"תם הזמן הקצוב: {e}")
except APIError as e:
    print(f"שגיאת API: {e}")
```

## תצורה

המערכת משתמשת בקובץ תצורה בפורמט YAML:

```yaml
store:
  url: "https://example.com/store"
  api_key: "your-api-key"

monitoring:
  metrics_interval: 60  # שניות
  alert_cooldown: 300  # שניות

templates:
  default_language: "he"
  cache_ttl: 3600  # שניות
```

## מיטוב ביצועים

המערכת כוללת מספר מנגנונים למיטוב ביצועים:

1. **מטמון** - שימוש במטמון לתוצאות API נפוצות
2. **אצווה** - עיבוד מספר בקשות יחד כשאפשר
3. **דחיית עומסים** - האטת קצב הבקשות בזמני עומס
4. **מטמון תבניות** - שמירת תבניות מעובדות בזיכרון

## אבטחה

המערכת מיישמת מספר שכבות אבטחה:

1. **הרשאות** - בדיקת הרשאות לכל פעולה
2. **תיקוף קלט** - בדיקת תקינות כל הקלטים
3. **הצפנה** - שימוש ב-HTTPS לכל התקשורת
4. **רישום** - תיעוד כל הפעולות הרגישות 