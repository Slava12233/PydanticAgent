import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure logfire to suppress warnings and set project
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'
os.environ['LOGFIRE_PROJECT'] = 'slavalabovkin1223/newtest'

# Configure and initialize Logfire for monitoring
try:
    import logfire
    # נסיון להגדיר את ה-PydanticPlugin אם הוא זמין
    try:
        logfire.configure(
            token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7',
            pydantic_plugin=logfire.PydanticPlugin(record='all')
        )
    except (AttributeError, ImportError):
        # אם ה-PydanticPlugin לא זמין, נגדיר רק את הטוקן
        logfire.configure(token='G9hJ4gBw7tp2XPZ4chQ2HH433NW8S5zrMqDnxb038dQ7')
    
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
    except Exception as e:
        logger.error(f"Error in main_async: {e}")
    finally:
        # Close database connection
        db.close()

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