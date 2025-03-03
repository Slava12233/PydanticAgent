# Pydantic AI Telegram Bot

[English](#pydantic-ai-telegram-bot) | [עברית](#בוט-טלגרם-מבוסס-pydantic-ai)

## 📝 Project Description

A smart Telegram bot based on Pydantic AI and OpenAI GPT-4. The bot allows users to have conversations in Hebrew, stores chat history in a PostgreSQL database, and provides a simple and user-friendly interface.

### 🌟 Key Features

- **Full Hebrew Support** - The bot is designed to work optimally with the Hebrew language
- **Chat History Storage** - All conversations are stored in a PostgreSQL database
- **Powered by GPT-4** - Uses OpenAI's advanced language model
- **Advanced Monitoring** - Integration with Logfire for performance monitoring and troubleshooting
- **Built-in Commands** - Support for basic commands like `/start`, `/help`, and `/clear`
- **Modular Architecture** - Clean separation of concerns for easier maintenance and future development
- **Improved Timeout Handling** - Configurable timeout settings to prevent connection issues
- **Enhanced RAG System** - Retrieval Augmented Generation for enhanced responses based on custom documents with support for multiple file types (PDF, Word, Excel, PowerPoint, HTML, and plain text)
- **Multi-Model Support** - Support for both OpenAI models (GPT-4, GPT-3.5-Turbo, GPT-4o) and Anthropic models (Claude-3-Opus, Claude-3-Sonnet)
- **Fallback Mechanism** - Automatic fallback to alternative models in case of API quota issues
- **Advanced Error Handling** - Specific error messages for different types of errors (quota, timeout, content filter)
- **User Role Management** - Support for different user roles (ADMIN, USER, BLOCKED) for access control
- **WooCommerce Dashboard** - Built-in dashboard for managing WooCommerce stores directly from Telegram
- **WooCommerce API Caching** - Performance optimization with caching mechanism for WooCommerce API requests
- **DASHBOARD** - ממשק מובנה לניהול חנויות ווקומרס ישירות מטלגרם

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Telegram account
- OpenAI API key
- Telegram bot token (from BotFather)
- PostgreSQL database

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/Slava12233/PydanticAgent.git
cd PydanticAgent
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
# On Linux/Mac
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

3. **Install the requirements**

```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL**

Install PostgreSQL on your system if you haven't already. Create a database and user for the bot:

```sql
CREATE DATABASE postgres;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
```

5. **Create a `.env` file**

Create a `.env` file in the project directory and add the following variables:

```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key

# PostgreSQL settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# WooCommerce settings (for store management)
WOOCOMMERCE_URL=your_woocommerce_store_url
WOOCOMMERCE_CONSUMER_KEY=your_woocommerce_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=your_woocommerce_consumer_secret
```

## 🚀 Running the Bot

To run the bot, simply execute:

```bash
python run.py
```

The bot will start running and be available on Telegram. Send `/start` to the bot to begin a conversation.

## 📋 Available Commands

- `/start` - Start a conversation with the bot
- `/help` - Display help and list of commands
- `/clear` - Clear chat history
- `/stats` - Display usage statistics
- `/switch_model [model_name]` - Change the primary AI model
- `/set_fallback [model_name]` - Set a fallback model for handling API quota issues
- `/models` - Display the current primary and fallback models in use
- `/add_document` - Add a document to the knowledge base (RAG system)
- `/search_documents` - Search for information in the knowledge base
- `/cancel` - Cancel the current operation
- `/store` - Access the WooCommerce store management dashboard

## 📚 Supported File Types for RAG System

The bot now supports multiple file types for the RAG (Retrieval Augmented Generation) system:

- **Documents**: PDF, Word (DOCX)
- **Spreadsheets**: Excel (XLSX)
- **Presentations**: PowerPoint (PPTX)
- **Web**: HTML, HTM
- **Text**: TXT, MD, JSON, XML, CSV

## 🔍 Using the RAG System

### Adding a Document

1. Start a conversation with the bot
2. Send the `/add_document` command
3. Upload a supported file (up to 20MB)
4. Provide a title for the document (or type "skip" to use the filename)
5. The bot will process the document and add it to your knowledge base

### Searching Documents

1. Send the `/search_documents` command
2. Enter your search query
3. The bot will return the most relevant information from your documents

### Using Documents in Conversations

Once you've added documents to your knowledge base, the bot will automatically use this information to enhance its responses when you ask questions related to the content of your documents.

## 🏪 WooCommerce Integration

The bot includes a comprehensive WooCommerce integration that allows you to manage your online store directly from Telegram.

### Features

- View and manage products
- View and manage orders
- Check store statistics
- Create new products with AI assistance
- Respond to customer inquiries
- Manage categories

### Performance Optimization

The WooCommerce integration includes a caching mechanism that significantly improves performance:

- **API Request Caching**: Frequently accessed data like categories and products are cached to reduce API calls
- **Configurable Cache TTL**: Set how long data should be cached before refreshing
- **Automatic Cache Invalidation**: Cache is automatically cleared when data is modified
- **Performance Monitoring**: Built-in tools to measure and compare performance with and without caching

### Using the WooCommerce Dashboard

1. Send the `/store` command to the bot
2. Select the desired operation from the menu
3. Follow the prompts to complete the operation

## 🧩 Project Structure

The project follows a modular architecture:

```
PydanticAgent/
├── run.py                  # Entry point for running the bot
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in Git)
├── .gitignore              # Git ignore file
├── README.md               # Project documentation
├── .cursorrules            # Rules and lessons learned for development
├── tests/                  # Test directory
│   ├── test_woocommerce_api_integration.py  # WooCommerce API integration tests
│   ├── test_user_scenarios.py               # User scenario tests
│   ├── test_performance_hebrew.py           # Performance and Hebrew support tests
│   ├── test_woocommerce_cache.py            # WooCommerce caching tests
│   └── test_master.py                       # Script to run all comprehensive tests
└── src/                    # Source code directory
    ├── __init__.py         # Package initialization
    ├── main.py             # Main application flow
    ├── agents/             # AI agent modules
    │   ├── __init__.py
    │   └── telegram_agent.py  # Telegram bot agent implementation
    ├── bots/               # Bot implementations
    │   ├── __init__.py
    │   └── telegram_bot.py # Telegram bot implementation
    ├── core/               # Core functionality
    │   ├── __init__.py
    │   └── config.py       # Configuration settings
    ├── database/           # Database modules
    │   ├── __init__.py
    │   ├── database.py     # PostgreSQL database operations
    │   ├── models.py       # Database models
    │   ├── rag_utils.py    # RAG utility functions
    │   ├── test_database.py # Database testing script
    │   └── view_messages.py # Utility to view stored messages
    ├── services/           # External services
    │   ├── __init__.py
    │   └── woocommerce_api.py # WooCommerce API integration
    ├── tools/              # Utility tools
    │   ├── __init__.py
    │   ├── document_manager.py # Document management for RAG
    │   ├── product_manager.py  # Product management for WooCommerce
    │   ├── product_intent_recognizer.py # Product intent recognition
    │   └── woocommerce_tools.py # WooCommerce API tools with caching
    └── utils/              # Utility functions
        └── __init__.py
```

## 📊 Monitoring with Logfire

The project uses Logfire for comprehensive monitoring of:
- HTTP requests
- Database operations
- Model interactions
- Errors and performance

## 🔧 Technical Notes

### Timeout Configuration

The bot uses the following timeout configuration to prevent connection issues:
- Read timeout: 30 seconds
- Write timeout: 30 seconds
- Connect timeout: 30 seconds
- Pool timeout: 30 seconds

These settings can be adjusted in `src/bots/telegram_bot.py` if needed.

### Database Configuration

The bot uses PostgreSQL for storing chat history. The database connection is configured in `src/core/config.py` and can be customized through environment variables in the `.env` file.

### WooCommerce API Caching

The bot includes a caching mechanism for WooCommerce API requests to improve performance:

#### How It Works

1. **Cache Implementation**: The `CachedWooCommerceAPI` class wraps the standard WooCommerce API client and adds caching functionality.
2. **Cache Storage**: Responses are stored in memory with timestamps for TTL (Time To Live) management.
3. **Cache Invalidation**: The cache is automatically cleared when data is modified (POST, PUT, DELETE requests).
4. **Performance Benefits**: Reduces API calls, improves response times, and reduces server load.

#### Using the Caching Mechanism

```python
from src.services.woocommerce.api import get_cached_woocommerce_api

# Create a cached WooCommerce API client
api = get_cached_woocommerce_api(
    store_url="your_store_url",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    cache_ttl=60  # Cache TTL in seconds (default: 300)
)

# Use the API as usual - caching is handled automatically
response = api.get("products")
```

#### Performance Testing

The project includes a dedicated test file (`tests/test_woocommerce_cache.py`) for measuring and comparing performance with and without caching:

```bash
# Run the cache performance tests
python -m tests.test_woocommerce_cache

# Run all tests including cache tests
python -m tests.test_master --type cache
```

### RAG System

The bot includes a Retrieval Augmented Generation (RAG) system that enhances responses by retrieving relevant information from a knowledge base. This allows the bot to provide more accurate and contextually relevant answers.

#### Adding Documents to RAG

You can add documents to the RAG system in several ways:

1. **Using the Telegram Bot**:
   - Send the `/add_document` command to the bot
   - Upload a text file (.txt)
   - Provide a title for the document

2. **Using the Command Line Tool**:
   ```bash
   # Add a document from a file
   python -m src.tools.document_manager add path/to/file.txt --title "Document Title"
   
   # Add content directly
   python -m src.tools.document_manager add-content "Document Title" "This is the content of the document"
   
   # Add content from a file
   python -m src.tools.document_manager add-content "Document Title" path/to/file.txt --from-file
   ```

#### Searching Documents

1. **Using the Telegram Bot**:
   - Send the `/search_documents` command to the bot
   - Enter your search query

2. **Using the Command Line Tool**:
   ```bash
   python -m src.tools.document_manager search "your search query"
   ```

#### Listing Documents

To see all documents in the RAG system:
```bash
python -m src.tools.document_manager list
```

#### Deleting Documents

To delete a document from the RAG system:
```bash
python -m src.tools.document_manager delete document_id
```

### Viewing Stored Messages

To view messages stored in the database, you can use the provided utility script:

```bash
# Display messages in the console
python src/database/view_messages.py

# Save messages to a CSV file
python src/database/view_messages.py --csv

# Display documents in the database
python src/database/view_messages.py --documents
```

### Database Structure

The RAG system uses the following database tables:

1. **documents** - Stores document metadata and full content
   - `id` - Unique document identifier
   - `title` - Document title
   - `source` - Document source (e.g., "telegram_upload", "file", "direct")
   - `content` - Full document content
   - `doc_metadata` - JSON metadata about the document
   - `upload_date` - When the document was added

2. **document_chunks** - Stores document chunks with embeddings for semantic search
   - `id` - Unique chunk identifier
   - `document_id` - Reference to parent document
   - `content` - Chunk content
   - `chunk_index` - Position in the original document
   - `embedding` - Vector embedding for semantic search

### Testing

The project includes a comprehensive testing script for the database and RAG functionality:

```bash
python -m src.database.test_database
```

## 🤝 Contributing

Contributions are always welcome! If you want to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

If you have any questions or suggestions, don't hesitate to reach out!

## 🧪 הרצת בדיקות

כדי להריץ את כל הבדיקות, השתמש בפקודה:

```bash
python tests/run_tests.py
```

## 🧪 Testing

The project includes comprehensive tests for various components, with a focus on the WooCommerce integration:

### Running Tests

To run all comprehensive tests:

```bash
python tests/run_comprehensive_tests.py
```

To run specific test types:

```bash
# Run only integration tests
python tests/run_comprehensive_tests.py --type integration

# Run only user scenario tests
python tests/run_comprehensive_tests.py --type user

# Run only performance and Hebrew support tests
python tests/run_comprehensive_tests.py --type performance

# Run tests with verbose output
python tests/run_comprehensive_tests.py --verbose
```

### Test Types

1. **Integration Tests** - Tests the integration with the WooCommerce API, including product creation, updating, and retrieval.

2. **User Scenario Tests** - Tests complete user scenarios from the user's perspective, simulating conversations and verifying the expected outcomes.

3. **Performance and Hebrew Support Tests** - Tests the performance of the system and its support for Hebrew language, including response times and proper handling of Hebrew text.

## 🛒 ממשק ניהול WooCommerce

הבוט כולל ממשק מובנה לניהול חנויות WooCommerce ישירות מטלגרם. ממשק זה מאפשר למשתמשים לבצע פעולות כגון:

- יצירת מוצרים חדשים
- עדכון מוצרים קיימים
- צפייה בהזמנות
- ניהול מלאי
- קבלת סטטיסטיקות מכירות

כדי להשתמש בממשק ניהול WooCommerce, יש להגדיר את פרטי החיבור לחנות ה-WooCommerce בקובץ ה-`.env`:

```
WOOCOMMERCE_URL=https://your-store-url.com
WOOCOMMERCE_CONSUMER_KEY=your_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=your_consumer_secret
```

# בוט טלגרם מבוסס Pydantic AI

<div dir="rtl">

## 📝 תיאור הפרויקט

בוט טלגרם חכם המבוסס על Pydantic AI ו-OpenAI GPT-4. הבוט מאפשר למשתמשים לנהל שיחות בעברית, שומר היסטוריית שיחות במסד נתונים PostgreSQL, ומספק ממשק פשוט וידידותי למשתמש.

### 🌟 תכונות עיקריות

- **תמיכה מלאה בעברית** - הבוט מתוכנן לעבוד באופן מיטבי עם השפה העברית
- **שמירת היסטוריית שיחות** - שמירת כל השיחות במסד נתונים PostgreSQL
- **מבוסס GPT-4** - שימוש במודל השפה המתקדם של OpenAI
- **ניטור מתקדם** - שילוב Logfire לניטור ביצועים ואיתור תקלות
- **פקודות מובנות** - תמיכה בפקודות בסיסיות כמו `/start`, `/help`, ו-`/clear`
- **ארכיטקטורה מודולרית** - הפרדה נקייה בין רכיבים לתחזוקה קלה ופיתוח עתידי
- **טיפול משופר בזמני תגובה** - הגדרות timeout מותאמות למניעת בעיות חיבור
- **מערכת RAG משופרת** - מערכת Retrieval Augmented Generation לשיפור תשובות על בסיס מסמכים מותאמים אישית עם תמיכה במגוון סוגי קבצים (PDF, Word, Excel, PowerPoint, HTML וטקסט רגיל)
- **מודלים רבים תמיכה** - תמיכה במודלים של OpenAI (GPT-4, GPT-3.5-Turbo, GPT-4o) ומודלים של Anthropic (Claude-3-Opus, Claude-3-Sonnet)
- **מסגרת מסגרת** - מסגרת מסגרת למניעת בעיות מסגרת
- **הטיפול המשופר** - הטיפול המשופר בשגיאות ספציפיות לסוגים שונים של שגיאות (מסגרת, זמן קצוב, מסגרת מסגרת)
- **ניהול משתמשים** - תמיכה במשתמשים שונים (ADMIN, USER, BLOCKED) לשליטה על מניעת גישה
- **דאשבורד ווקומרס** - ממשק מובנה לניהול חנויות ווקומרס ישירות מטלגרם

## 🛠️ התקנה

### דרישות מקדימות

- Python 3.8 ומעלה
- חשבון טלגרם
- מפתח API של OpenAI
- טוקן של בוט טלגרם (מ-BotFather)
- מסד נתונים PostgreSQL

### שלבי התקנה

1. **שכפל את המאגר**

```bash
git clone https://github.com/Slava12233/PydanticAgent.git
cd PydanticAgent
```

2. **צור סביבה וירטואלית והפעל אותה**

```bash
python -m venv venv
# בלינוקס/מק
source venv/bin/activate
# בווינדוס
venv\Scripts\activate
```

3. **התקן את הדרישות**

```bash
pip install -r requirements.txt
```

4. **הגדר PostgreSQL**

התקן PostgreSQL במערכת שלך אם עדיין לא עשית זאת. צור מסד נתונים ומשתמש עבור הבוט:

```sql
CREATE DATABASE postgres;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
```

5. **צור קובץ `.env`**

צור קובץ `.env` בתיקיית הפרויקט והוסף את המשתנים הבאים:

```
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key

# הגדרות PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## 🚀 הפעלה

להפעלת הבוט, פשוט הרץ:

```bash
python run.py
```

הבוט יתחיל לרוץ ויהיה זמין בטלגרם. שלח `/start` לבוט כדי להתחיל שיחה.

## 📋 פקודות זמינות

- `/start` - התחל שיחה עם הבוט
- `/help` - הצג עזרה ורשימת פקודות
- `/clear` - נקה היסטוריית שיחה
- `/stats` - הצג סטטיסטיקות שימוש
- `/switch_model [model_name]` - מצב מודל ראשי
- `/set_fallback [model_name]` - מצב מודל משנה להטלת בעיות מסגרת
- `/models` - הצג מודלים ראשיים ומשנים בשימוש
- `/add_document` - הוסף מסמך למאגר הידע (מערכת RAG)
- `/search_documents` - חפש במסמכים
- `/cancel` - בטל את הפעולה הנוכחית

## 📚 סוגי קבצים נתמכים למערכת RAG

הבוט כעת תומך במגוון סוגי קבצים למערכת ה-RAG (Retrieval Augmented Generation):

- **מסמכים**: PDF, Word (DOCX)
- **גיליונות**: Excel (XLSX)
- **מצגות**: PowerPoint (PPTX)
- **אינטרנט**: HTML, HTM
- **טקסט**: TXT, MD, JSON, XML, CSV

## 🔍 שימוש במערכת RAG

### הוספת מסמך

1. התחל שיחה עם הבוט
2. שלח את הפקודה `/add_document`
3. העלה קובץ נתמך (עד 20MB)
4. הזן כותרת למסמך (או הקלד "דלג" כדי להשתמש בשם הקובץ)
5. הבוט יעבד את המסמך ויוסיף אותו למאגר הידע שלך

### חיפוש במסמכים

1. שלח את הפקודה `/search_documents`
2. הזן את שאילתת החיפוש שלך
3. הבוט יחזיר את המידע הרלוונטי ביותר מהמסמכים שלך

### שימוש במסמכים בשיחות

לאחר שהוספת מסמכים למאגר הידע שלך, הבוט ישתמש באופן אוטומטי במידע זה כדי לשפר את תשובותיו כאשר תשאל שאלות הקשורות לתוכן המסמכים שלך.

## 🧩 מבנה הפרויקט

הפרויקט עוקב אחר ארכיטקטורה מודולרית:

```
PydanticAgent/
├── run.py                  # נקודת כניסה להפעלת הבוט
├── requirements.txt        # תלויות Python
├── .env                    # משתני סביבה (לא ב-Git)
├── .gitignore              # קובץ Git ignore
├── README.md               # תיעוד הפרויקט
├── .cursorrules            # כללים ולקחים שנלמדו בפיתוח
├── tests/                  # תיקיית בדיקות
│   ├── test_woocommerce_api_integration.py  # בדיקות אינטגרציה עם API ווקומרס
│   ├── test_user_scenarios.py               # בדיקות מצבי משתמש
│   ├── test_performance_hebrew.py           # בדיקות ביצוע ותמיכה בעברית
│   ├── test_woocommerce_cache.py            # בדיקות מטמון עם WooCommerce
│   └── test_master.py                       # סקריפט להרצת בדיקות מלאות
└── src/                    # תיקיית קוד המקור
    ├── __init__.py         # אתחול חבילה
    ├── main.py             # זרימת היישום הראשית
    ├── agents/             # מודולי סוכן AI
    │   ├── __init__.py
    │   └── telegram_agent.py  # מימוש סוכן בוט טלגרם
    ├── bots/               # מימושי בוט
    │   ├── __init__.py
    │   └── telegram_bot.py # מימוש בוט טלגרם
    ├── core/               # פונקציונליות ליבה
    │   ├── __init__.py
    │   └── config.py       # הגדרות תצורה
    ├── database/           # מודולי מסד נתונים
    │   ├── __init__.py
    │   ├── database.py     # פעולות מסד נתונים PostgreSQL
    │   ├── models.py       # מודלים של מסד הנתונים
    │   ├── rag_utils.py    # פונקציות עזר ל-RAG
    │   ├── test_database.py # סקריפט בדיקה למסד הנתונים
    │   └── view_messages.py # כלי להצגת הודעות שמורות
    ├── services/           # מודולי שירותים חיצוניים
    │   ├── __init__.py
    │   └── woocommerce_api.py # מימוש אינטגרציה עם API ווקומרס
    ├── tools/              # כלי עזר
    │   ├── __init__.py
    │   ├── document_manager.py # ניהול מסמכים עבור RAG
    │   ├── product_manager.py  # ניהול מוצרים עבור ווקומרס
    │   ├── product_intent_recognizer.py # מימוש הזהה מטרה מוצר
    │   └── woocommerce_tools.py # כלי עזר ל-API עם WooCommerce עם מטמון
    └── utils/              # פונקציות שירות
        └── __init__.py
```

## 📊 ניטור עם Logfire

הפרויקט משתמש ב-Logfire לניטור מקיף של:
- בקשות HTTP
- פעולות מסד נתונים
- אינטראקציות מודל
- שגיאות וביצועים

## 🔧 הערות טכניות

### תצורת זמן קצוב

הבוט משתמש בתצורת זמן קצוב הבאה למניעת בעיות חיבור:
- זמן קריאה: 30 שניות
- זמן כתיבה: 30 שניות
- זמן חיבור: 30 שניות
- זמן פול: 30 שניות

ניתן להתאים הגדרות אלה ב-`src/bots/telegram_bot.py` במידת הצורך.

### תצורת מסד נתונים

הבוט משתמש ב-PostgreSQL לאחסון היסטוריית שיחות. חיבור מסד הנתונים מוגדר ב-`src/core/config.py` וניתן להתאמה דרך משתני סביבה בקובץ `.env`.

### מערכת RAG

הבוט כולל מערכת Retrieval Augmented Generation (RAG) המשפרת תשובות על ידי אחזור מידע רלוונטי ממאגר ידע. זה מאפשר לבוט לספק תשובות מדויקות יותר ורלוונטיות להקשר.

#### הוספת מסמכים ל-RAG

ניתן להוסיף מסמכים למערכת ה-RAG במספר דרכים:

1. **באמצעות בוט הטלגרם**:
   - Send the `/add_document` command to the bot
   - Upload a text file (.txt)
   - Provide a title for the document

2. **באמצעות כלי שורת הפקודה**:
   ```bash
   # Add a document from a file
   python -m src.tools.document_manager add path/to/file.txt --title "Document Title"
   
   # Add content directly
   python -m src.tools.document_manager add-content "Document Title" "This is the content of the document"
   
   # Add content from a file
   python -m src.tools.document_manager add-content "Document Title" path/to/file.txt --from-file
   ```

#### חיפוש במסמכים

1. **באמצעות בוט הטלגרם**:
   - Send the `/search_documents` command to the bot
   - Enter your search query

2. **באמצעות כלי שורת הפקודה**:
   ```bash
   python -m src.tools.document_manager search "your search query"
   ```

#### רשימת מסמכים

כדי לראות את כל המסמכים במערכת ה-RAG:
```bash
python -m src.tools.document_manager list
```

#### מחיקת מסמכים

כדי למחוק מסמך ממערכת ה-RAG:
```bash
python -m src.tools.document_manager delete מזהה_המסמך
```

### Viewing Stored Messages

To view messages stored in the database, you can use the provided utility script:

```bash
# Display messages in the console
python src/database/view_messages.py

# Save messages to a CSV file
python src/database/view_messages.py --csv

# Display documents in the database
python src/database/view_messages.py --documents
```

### Database Structure

The RAG system uses the following database tables:

1. **documents** - Stores document metadata and full content
   - `id` - Unique document identifier
   - `title` - Document title
   - `source` - Document source (e.g., "telegram_upload", "file", "direct")
   - `content` - Full document content
   - `doc_metadata` - JSON metadata about the document
   - `upload_date` - When the document was added

2. **document_chunks** - Stores document chunks with embeddings for semantic search
   - `id` - Unique chunk identifier
   - `document_id` - Reference to parent document
   - `content` - Chunk content
   - `chunk_index` - Position in the original document
   - `embedding` - Vector embedding for semantic search

### Testing

The project includes a comprehensive testing script for the database and RAG functionality:

```bash
python -m src.database.test_database
```

## 🤝 תרומה

תרומות תמיד מתקבלות בברכה! אם ברצונך לתרום:

1. בצע פיצול (Fork) למאגר
2. צור ענף חדש (`git checkout -b feature/amazing-feature`)
3. בצע את השינויים שלך
4. דחוף לענף (`git push origin feature/amazing-feature`)
5. פתח בקשת משיכה (Pull Request)

## 📄 רישיון

מופץ תחת רישיון MIT. ראה `LICENSE` למידע נוסף.

## 📞 יצירת קשר

אם יש לך שאלות או הצעות, אל תהסס ליצור קשר!

## 🧪 בדיקות

הפרויקט כולל בדיקות מקיפות למרכיבים שונים, עם דגש על האינטגרציה עם WooCommerce:

### הרצת בדיקות

להרצת כל הבדיקות המקיפות:

```bash
python tests/run_comprehensive_tests.py
```

להרצת סוגי בדיקות ספציפיים:

```bash
# הרצת בדיקות אינטגרציה בלבד
python tests/run_comprehensive_tests.py --type integration

# הרצת בדיקות תרחישי משתמש בלבד
python tests/run_comprehensive_tests.py --type user

# הרצת בדיקות ביצועים ותמיכה בעברית בלבד
python tests/run_comprehensive_tests.py --type performance

# הרצת בדיקות עם פלט מפורט
python tests/run_comprehensive_tests.py --verbose
```

### סוגי בדיקות

1. **בדיקות אינטגרציה** - בודקות את האינטגרציה עם ה-API של WooCommerce, כולל יצירת מוצרים, עדכון ואחזור.

2. **בדיקות תרחישי משתמש** - בודקות תרחישי משתמש מלאים מנקודת המבט של המשתמש, מדמות שיחות ומאמתות את התוצאות הצפויות.

3. **בדיקות ביצועים ותמיכה בעברית** - בודקות את ביצועי המערכת ואת התמיכה בשפה העברית, כולל זמני תגובה וטיפול נכון בטקסט בעברית.

## 🛒 ממשק ניהול WooCommerce

הבוט כולל ממשק מובנה לניהול חנויות WooCommerce ישירות מטלגרם. ממשק זה מאפשר למשתמשים לבצע פעולות כגון:

- יצירת מוצרים חדשים
- עדכון מוצרים קיימים
- צפייה בהזמנות
- ניהול מלאי
- קבלת סטטיסטיקות מכירות

כדי להשתמש בממשק ניהול WooCommerce, יש להגדיר את פרטי החיבור לחנות ה-WooCommerce בקובץ ה-`.env`:

```
WOOCOMMERCE_URL=https://your-store-url.com
WOOCOMMERCE_CONSUMER_KEY=your_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=your_consumer_secret
```

## מודולים עיקריים

### מודול הסוכן (Agent)
מודול זה מכיל את הלוגיקה העיקרית של הסוכן החכם. הוא אחראי על:
- קבלת הודעות מהמשתמש
- עיבוד ההודעות והבנת הכוונה
- יצירת תשובות מתאימות
- שימוש במודלי שפה מתקדמים

### מודול הבוט (Bot)
מודול זה מכיל את הממשק עם פלטפורמת טלגרם. הוא אחראי על:
- קבלת הודעות מטלגרם
- העברת ההודעות לסוכן
- שליחת תשובות הסוכן למשתמש
- ניהול פקודות מיוחדות

### מודול מסד הנתונים (Database)
מודול זה מכיל את הלוגיקה לעבודה עם מסד הנתונים. הוא אחראי על:
- שמירת היסטוריית השיחות
- שמירת מסמכים ומידע
- אחזור מידע רלוונטי

### מודול RAG (Retrieval-Augmented Generation)
מודול זה מכיל את הלוגיקה לשיפור תשובות הסוכן באמצעות מידע ממסמכים. הוא אחראי על:
- אחסון מסמכים
- חיפוש במסמכים
- שילוב מידע ממסמכים בתשובות הסוכן

### מודול WooCommerce
מודול זה מכיל את הלוגיקה לעבודה עם חנות WooCommerce. הוא אחראי על:
- ניהול מוצרים
- ניהול הזמנות
- ניהול לקוחות
- ניהול מלאי

### מודול הקשר (Context)
מודול זה מכיל את הלוגיקה לניהול הקשר השיחה. הוא אחראי על:
- הבנת הקשר השיחה
- זיהוי אזכורים קודמים
- פתרון כינויי גוף והתייחסויות עקיפות

### מודול פירוק שאילתות (Query Parser)
מודול זה מכיל את הלוגיקה לפירוק שאילתות מורכבות. הוא אחראי על:
- זיהוי מחברים לוגיים
- פירוק שאילתות מורכבות למשימות פשוטות
- טיפול בשאלות השוואתיות והיפותטיות

### מודול יצירת תשובות (Response Generator)
מודול זה מכיל את הלוגיקה ליצירת תשובות בשפה טבעית. הוא אחראי על:
- יצירת תשובות מותאמות לכוונת המשתמש
- שילוב אימוג'ים ופורמט מתאים
- הוספת וריאציות לשוניות למניעת חזרתיות

### מודול למידה והשתפרות (Learning Manager)
מודול זה מכיל את הלוגיקה לתיעוד אינטראקציות ולמידה מתמדת. הוא אחראי על:
- תיעוד אינטראקציות עם המשתמש
- זיהוי אינטראקציות בעייתיות
- יצירת דוחות תקופתיים על ביצועי הסוכן
- עדכון אוטומטי של מילות מפתח בהתבסס על אינטראקציות מוצלחות

</div> 
