import asyncio
import logging
import os
import sys
import signal

# הוספת תיקיית הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# יבוא הגדרות מקובץ config
from src.core.config import LOGFIRE_API_KEY, LOGFIRE_PROJECT, LOGFIRE_DATASET

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
from src.bots.telegram_bot import TelegramBot
# Import the new database module
from src.database.database import db

async def main_async():
    """Async main function to run the bot."""
    try:
        # Initialize the database
        db.init_db()
        
        # Initialize and run the Telegram bot
        bot = TelegramBot()
        await bot.run()
        
        # הוספת אירוע שימתין לסיום הבוט
        stop_event = asyncio.Event()
        
        # הוספת מטפל לסיגנלים כדי לאפשר סגירה מסודרת
        def signal_handler():
            logger.info("Received stop signal")
            stop_event.set()
        
        # רישום מטפל לסיגנלים
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows לא תומך ב-add_signal_handler
            pass
        
        # המתנה לסיגנל סיום
        await stop_event.wait()
        
        # סגירת הבוט בצורה מסודרת
        if hasattr(bot, 'application'):
            await bot.application.stop()
            await bot.application.shutdown()
    except Exception as e:
        logger.error(f"Error in main_async: {e}")
    finally:
        # Close database connection
        await db.close()

def main():
    """Main entry point for the application."""
    try:
        # Run the async main function
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    main() 