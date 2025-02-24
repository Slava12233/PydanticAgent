import logging
import os
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from config import TELEGRAM_TOKEN, ALLOWED_COMMANDS
from database import db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure and initialize Logfire for monitoring
import logfire
logfire.configure()
logfire.instrument_httpx(capture_all=True)  # Capture all headers, request body, and response body

# Configure logfire to suppress warnings
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'

class ChatBot:
    def __init__(self):
        """Initialize the bot with OpenAI agent."""
        self.agent = Agent('openai:gpt-4')
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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        user_id = update.effective_user.id
        message_text = update.message.text

        # Show typing indicator
        self.typing_status[user_id] = True
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            # Create a Logfire span to track the entire message handling process
            with logfire.span('handle_telegram_message', user_id=user_id, message_length=len(message_text)):
                # Get chat history
                history = db.get_chat_history(user_id)
                
                # Create system prompt with history
                history_text = ""
                if history:
                    history_text = "היסטוריית שיחה:\n" + "\n".join([
                        f"User: {msg}\nAssistant: {resp}" 
                        for msg, resp, _ in reversed(history)
                    ]) + "\n\n"
                
                prompt = (
                    "אתה עוזר ידידותי שעונה בעברית. "
                    "ענה בקצרה ובצורה ממוקדת. "
                    "אל תחזור על המילים של השאלה בתשובה.\n\n"
                    f"{history_text}"
                    f"User: {message_text}\n"
                    "Assistant: "
                )

                logger.info(f"Sending prompt for user {user_id}")
                # Log the prompt being sent to the model
                logfire.info('sending_prompt_to_model', user_id=user_id, prompt_length=len(prompt))
                
                result = await self.agent.run(prompt)
                response = result.data

                logger.info(f"Got response for user {user_id}")
                # Log the response from the model
                logfire.info('received_model_response', user_id=user_id, response_length=len(response))
                
                # Save to database
                db.save_message(user_id, message_text, response)

                # Send response
                await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Log the error in Logfire
            logfire.error('message_handling_error', user_id=user_id, error=str(e))
            await update.message.reply_text(
                "מצטער, אירעה שגיאה בעיבוד ההודעה שלך. אנא נסה שוב מאוחר יותר."
            )
        finally:
            # Clear typing status
            self.typing_status[user_id] = False

def main() -> None:
    """Start the bot."""
    try:
        # Log application startup
        logfire.info('telegram_bot_starting')
        
        # Create the Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Initialize bot
        bot = ChatBot()

        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help))
        application.add_handler(CommandHandler("clear", bot.clear))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

        # Log successful initialization
        logfire.info('telegram_bot_initialized')
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        # Log any startup errors
        logfire.error('telegram_bot_startup_error', error=str(e))
        logger.error(f"Error starting bot: {e}")
    finally:
        # Ensure Logfire flushes all pending logs
        logfire.force_flush()
        # Close database connection
        db.close()

if __name__ == '__main__':
    try:
        main()
    finally:
        # Ensure Logfire shuts down properly
        logfire.shutdown()
