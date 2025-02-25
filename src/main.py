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

# Configure and initialize Logfire for monitoring
import logfire
logfire.configure()

# Configure logfire to suppress warnings
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'

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
        logfire.error('main_async_error', error=str(e))
    finally:
        # Ensure Logfire flushes all pending logs
        logfire.force_flush()
        # Close database connection
        db.close()

def main():
    """Main entry point for the application."""
    try:
        # Run the async main function
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        logfire.info('bot_stopped_by_user')
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logfire.error('unhandled_exception', error=str(e))
    finally:
        # Ensure Logfire shuts down properly
        logfire.shutdown()
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    main() 