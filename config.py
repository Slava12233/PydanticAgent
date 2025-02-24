import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Database settings
DB_FILE = "chat_history.db"

# Bot settings
ALLOWED_COMMANDS = [
    ("start", "התחל שיחה עם הבוט"),
    ("help", "הצג עזרה ורשימת פקודות"),
    ("clear", "נקה היסטוריית שיחה")
]
