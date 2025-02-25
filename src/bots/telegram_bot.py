import logging
import os
from typing import Dict
import datetime
import traceback

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    Defaults
)
import httpx

# Import from our module structure
from src.core.config import TELEGRAM_TOKEN, ALLOWED_COMMANDS
# Import the new database module
from src.database.database import db
from src.agents.telegram_agent import TelegramAgent
# Import the new logger module
from src.utils.logger import setup_logger, log_exception, log_database_operation, log_telegram_message

# Configure logging
logger = setup_logger('telegram_bot')

# Configure and initialize Logfire for monitoring
import logfire
logfire.configure()
# הגבלת ניטור HTTP לכותרות בלבד ללא תוכן הבקשה
logfire.instrument_httpx(capture_headers=True, capture_body=False)

class TelegramBot:
    def __init__(self):
        """Initialize the bot with OpenAI agent."""
        self.agent = TelegramAgent()
        self.typing_status: Dict[int, bool] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        welcome_message = (
            f"שלום {user.first_name}! 👋\n\n"
            "אני בוט AI שיכול לעזור לך בכל נושא.\n"
            "פשוט שלח לי הודעה ואשמח לעזור!\n\n"
            "הקלד /help לרשימת הפקודות."
        )
        # Log the start command
        logfire.info('command_start', user_id=user.id, username=user.username)
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        help_text = "הפקודות הזמינות:\n\n"
        for command, description in ALLOWED_COMMANDS:
            help_text += f"/{command} - {description}\n"
        # Log the help command
        logfire.info('command_help', user_id=update.effective_user.id)
        await update.message.reply_text(help_text)

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /clear command."""
        user_id = update.effective_user.id
        # Log the clear command
        logfire.info('command_clear', user_id=user_id)
        db.clear_chat_history(user_id)
        await update.message.reply_text("היסטוריית השיחה נמחקה! 🗑️")
        
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /stats command - show database statistics."""
        user_id = update.effective_user.id
        
        # Log the stats command
        logfire.info('command_stats', user_id=user_id)
        
        try:
            # Get statistics from database
            message_count = db.get_message_count()
            user_count = db.get_user_count()
            
            # Get user's personal stats
            user_history = db.get_chat_history(user_id)
            user_message_count = len(user_history)
            
            stats_message = (
                "📊 סטטיסטיקות הבוט:\n\n"
                f"סה\"כ הודעות במערכת: {message_count}\n"
                f"מספר משתמשים ייחודיים: {user_count}\n\n"
                f"הסטטיסטיקות שלך:\n"
                f"מספר ההודעות שלך: {user_message_count}\n"
            )
            
            await update.message.reply_text(stats_message)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            logfire.error('stats_error', user_id=user_id, error=str(e))
            await update.message.reply_text("אירעה שגיאה בהצגת הסטטיסטיקות. אנא נסה שוב מאוחר יותר.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user_id = update.effective_user.id
        message_text = update.message.text

        # Show typing indicator
        self.typing_status[user_id] = True
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            # Log the incoming message
            log_telegram_message(logger, user_id, message_text)
            
            # Create a Logfire span to track the entire message handling process
            with logfire.span('handle_telegram_message', user_id=user_id, message_length=len(message_text)):
                # Get chat history
                try:
                    history = db.get_chat_history(user_id)
                    logger.debug(f"Retrieved chat history for user {user_id}: {len(history)} messages")
                except Exception as db_error:
                    log_exception(logger, db_error, {'operation': 'get_chat_history', 'user_id': user_id})
                    history = []  # Use empty history if retrieval fails
                
                # קריאה ל-Agent
                try:
                    response = await self.agent.get_response(message_text, history)
                    logger.info(f"Got response for user {user_id}")
                except Exception as agent_error:
                    log_exception(logger, agent_error, {'operation': 'agent_get_response', 'user_id': user_id})
                    response = "מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר."
                
                # Save to database
                try:
                    # Log the database operation with detailed parameters
                    log_data = {
                        'user_id': user_id,
                        'message_length': len(message_text),
                        'response_length': len(response),
                        'user_id_type': type(user_id).__name__,  # Log the type of user_id
                        'user_id_value': str(user_id)  # Convert to string to ensure it's loggable
                    }
                    logger.debug(f"Saving message with parameters: {log_data}")
                    
                    db.save_message(user_id, message_text, response)
                    log_database_operation(logger, 'save_message', log_data, 'success')
                except Exception as db_error:
                    error_context = {
                        'operation': 'save_message',
                        'user_id': user_id,
                        'user_id_type': type(user_id).__name__,
                        'message_length': len(message_text),
                        'response_length': len(response)
                    }
                    log_exception(logger, db_error, error_context)
                    # Continue to send response even if saving fails

                # Send response
                await update.message.reply_text(response)
                log_telegram_message(logger, user_id, message_text, response)

        except Exception as e:
            error_context = {
                'user_id': user_id,
                'message_length': len(message_text) if message_text else 0
            }
            log_exception(logger, e, error_context)
            # Log the error in Logfire
            with logfire.span('message_handling_error'):
                logfire.error(str(e))
            
            # Send error message to user
            await update.message.reply_text("מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר.")
        finally:
            # Clear typing status
            self.typing_status[user_id] = False

    async def run(self):
        """Start the bot."""
        try:
            # Log application startup
            logfire.info('telegram_bot_starting')
            
            # הגדרת Defaults עם tzinfo בלבד
            defaults = Defaults(
                tzinfo=datetime.timezone.utc
            )
            
            # Create the Application with defaults and increased timeouts
            application = Application.builder()\
                .token(TELEGRAM_TOKEN)\
                .defaults(defaults)\
                .read_timeout(30.0)\
                .write_timeout(30.0)\
                .connect_timeout(30.0)\
                .pool_timeout(30.0)\
                .build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help))
            application.add_handler(CommandHandler("clear", self.clear))
            application.add_handler(CommandHandler("stats", self.stats))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            # Log successful initialization
            logfire.info('telegram_bot_initialized')
            
            # Start the bot with improved settings
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                # הגבלת סוגי העדכונים רק לאלה שאנחנו באמת צריכים
                allowed_updates=["message", "edited_message", "callback_query", "chat_member"],
                # הגדרת זמן ארוך יותר בין בקשות עדכון
                poll_interval=5.0,
                # הגדרת מספר ניסיונות חוזרים
                bootstrap_retries=5
            )
            
            # שומר על הבוט פעיל
            logger.info("Bot is running. Press Ctrl+C to stop")
            # נשאר בלולאה אינסופית עד שיש הפרעה
            import asyncio
            while True:
                await asyncio.sleep(1)
            
        except Exception as e:
            # Log any startup errors
            logfire.error('telegram_bot_startup_error', error=str(e))
            logger.error(f"Error starting bot: {e}")
            raise 