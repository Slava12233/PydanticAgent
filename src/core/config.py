"""
קובץ הגדרות המערכת
"""
import os
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env
load_dotenv()

# הגדרות טלגרם
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")  # טוקן לספק תשלומים של טלגרם

# הגדרות OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# הגדרות PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")  # שם מסד הנתונים
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "SSll456456!!")

# URL מלא למסד הנתונים
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# הגדרות Logfire
LOGFIRE_API_KEY = os.getenv("LOGFIRE_API_KEY")
LOGFIRE_DATASET = os.getenv("LOGFIRE_DATASET", "telegram-bot")
LOGFIRE_PROJECT = os.getenv("LOGFIRE_PROJECT", "slavalabovkin1223/newtest")

# הגדרות כלליות
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "5"))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "he")  # ברירת מחדל: עברית

# פקודות מותרות בבוט
ALLOWED_COMMANDS = [
    ("start", "התחלת שיחה עם הבוט"),
    ("help", "הצגת עזרה ורשימת פקודות"),
    ("clear", "ניקוי היסטוריית השיחה"),
    ("stats", "הצגת סטטיסטיקות שימוש"),
    # פקודות למערכת RAG
    ("add_document", "הוספת מסמך למערכת הידע"),
    ("search_documents", "חיפוש במסמכים"),
    ("list_documents", "הצגת רשימת המסמכים שלך"),
    ("cancel", "ביטול פעולה נוכחית"),
    # פקודות לניהול חנות ווקומרס
    ("store", "דאשבורד ניהול חנות ווקומרס"),
    ("connect_store", "חיבור חנות ווקומרס חדשה"),
    ("create_product", "יצירת מוצר חדש בחנות"),
    ("products", "ניהול מוצרים בחנות"),
    ("orders", "ניהול הזמנות בחנות"),
    ("customers", "ניהול לקוחות"),
    ("sales", "דוחות מכירות וסטטיסטיקות"),
    ("inventory", "ניהול מלאי")
]

# פקודות מנהל
ADMIN_COMMANDS = [
    ("admin", "כניסה למצב ניהול (למנהלים בלבד)"),
    ("admin_users", "ניהול משתמשים (רשימה, חסימה, ביטול חסימה)"),
    ("admin_stats", "סטטיסטיקות מערכת מפורטות"),
    ("admin_docs", "ניהול מסמכים (רשימה, מחיקה, עדכון)"),
    ("admin_models", "ניהול מודלים (שינוי ברירות מחדל, הגבלות)"),
    ("admin_config", "ניהול הגדרות מערכת"),
    ("admin_notify", "שליחת התראות למשתמשים")
] 