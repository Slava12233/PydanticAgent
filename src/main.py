import asyncio
import logging
import os
import sys
import signal

# הוספת תיקיית הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# יבוא הגדרות מקובץ config
from .core.config import LOGFIRE_API_KEY, LOGFIRE_PROJECT, LOGFIRE_DATASET

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure logfire to suppress warnings and set project
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'
os.environ['LOGFIRE_PROJECT'] = LOGFIRE_PROJECT

# Configure and initialize Logfire for monitoring
try:
    import logfire
    # נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
    try:
        logfire.configure(
            token=LOGFIRE_API_KEY,
            pydantic_plugin=logfire.PydanticPlugin(record='all')
        )
    except (AttributeError, ImportError):
        # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
        logfire.configure(token=LOGFIRE_API_KEY)
    
    logfire_available = True
    logger.info("Logfire initialized successfully")
except Exception as e:
    logfire_available = False
    logger.warning(f"Logfire initialization failed: {e}. Continuing without Logfire.")

# Import the TelegramBot class
from .ui.telegram.core.core import TelegramBot
# Import the new database module
from .database.core import db

# משתנה גלובלי לשמירת הבוט
bot = None

async def main_async():
    """Async main function to run the bot."""
    global bot
    try:
        # Initialize the database with table creation
        await db.init_db(recreate_tables=True)
        logger.info("Database initialized successfully")
        
        # Initialize and run the Telegram bot
        bot = TelegramBot()
        await bot.run()
        
    except Exception as e:
        logger.error(f"Error in main_async: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Close database connection
        await db.close()
        if bot:
            try:
                await bot.stop()
                logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

def signal_handler(signum, frame):
    """מטפל בסיגנלים לסגירת הבוט"""
    logger.info(f"Received signal {signum}")
    if bot:
        # הפעלת הפונקציה stop בצורה אסינכרונית
        loop = asyncio.get_event_loop()
        loop.create_task(bot.stop())

def main():
    """Main entry point for the application."""
    try:
        # הגדרת מטפלי סיגנלים
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # הרצת הפונקציה הראשית
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    main() 