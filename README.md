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
- **RAG System** - Retrieval Augmented Generation for enhanced responses based on custom documents

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
- `/add_document` - Add a document to the knowledge base (RAG system)
- `/search_documents` - Search for information in the knowledge base
- `/cancel` - Cancel the current operation

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
    ├── tools/              # Utility tools
    │   ├── __init__.py
    │   └── document_manager.py # Document management for RAG
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

---

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
- **מערכת RAG** - מערכת Retrieval Augmented Generation לשיפור תשובות על בסיס מסמכים מותאמים אישית

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
- `/add_document` - הוסף מסמך למאגר הידע (מערכת RAG)
- `/search_documents` - חפש במסמכים
- `/cancel` - בטל את הפעולה הנוכחית

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
    ├── tools/              # כלי עזר
    │   ├── __init__.py
    │   └── document_manager.py # ניהול מסמכים עבור RAG
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
   - שלח את הפקודה `/add_document` לבוט
   - העלה קובץ טקסט (.txt)
   - ספק כותרת למסמך

2. **באמצעות כלי שורת הפקודה**:
   ```bash
   # הוספת מסמך מקובץ
   python -m src.tools.document_manager add path/to/file.txt --title "כותרת המסמך"
   
   # הוספת תוכן ישירות
   python -m src.tools.document_manager add-content "כותרת המסמך" "זהו תוכן המסמך"
   
   # הוספת תוכן מקובץ
   python -m src.tools.document_manager add-content "כותרת המסמך" path/to/file.txt --from-file
   ```

#### חיפוש במסמכים

1. **באמצעות בוט הטלגרם**:
   - שלח את הפקודה `/search_documents` לבוט
   - הזן את שאילתת החיפוש שלך

2. **באמצעות כלי שורת הפקודה**:
   ```bash
   python -m src.tools.document_manager search "שאילתת החיפוש שלך"
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

### צפייה בהודעות שמורות

כדי לצפות בהודעות השמורות במסד הנתונים, תוכל להשתמש בסקריפט השירות המצורף:

```bash
# הצג הודעות במסוף
python src/database/view_messages.py

# שמור הודעות לקובץ CSV
python src/database/view_messages.py --csv

# הצג מסמכים במסד הנתונים
python src/database/view_messages.py --documents
```

### מבנה מסד הנתונים

מערכת ה-RAG משתמשת בטבלאות הבאות במסד הנתונים:

1. **documents** - מאחסנת מטא-דאטה ותוכן מלא של מסמכים
   - `id` - מזהה ייחודי למסמך
   - `title` - כותרת המסמך
   - `source` - מקור המסמך (למשל, "telegram_upload", "file", "direct")
   - `content` - תוכן מלא של המסמך
   - `doc_metadata` - מטא-דאטה בפורמט JSON על המסמך
   - `upload_date` - מועד הוספת המסמך

2. **document_chunks** - מאחסנת קטעי מסמכים עם embeddings לחיפוש סמנטי
   - `id` - מזהה ייחודי לקטע
   - `document_id` - הפניה למסמך האב
   - `content` - תוכן הקטע
   - `chunk_index` - מיקום במסמך המקורי
   - `embedding` - וקטור embedding לחיפוש סמנטי

### בדיקות

הפרויקט כולל סקריפט בדיקה מקיף למסד הנתונים ולפונקציונליות ה-RAG:

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

</div> 