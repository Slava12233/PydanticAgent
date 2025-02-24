import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
import logging
from config import DB_FILE

# Import logfire for monitoring
import logfire
# Configure logfire
logfire.configure()

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize database connection and create tables if they don't exist."""
        logger.info("Initializing database connection")
        with logfire.span('database_init', db_file=DB_FILE):
            self.conn = sqlite3.connect(DB_FILE)
            self.create_tables()

    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        logger.info("Creating/verifying database tables")
        with logfire.span('database_create_tables'):
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, timestamp)
                )
            ''')
            self.conn.commit()
            logger.info("Database tables ready")

    def save_message(self, user_id: int, message: str, response: str) -> None:
        """Save a message and its response to the database."""
        try:
            with logfire.span('database_save_message', user_id=user_id):
                cursor = self.conn.cursor()
                cursor.execute(
                    'INSERT INTO messages (user_id, message, response) VALUES (?, ?, ?)',
                    (user_id, message, response)
                )
                self.conn.commit()
                logger.info(f"Saved message for user {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Error saving message: {e}")
            logfire.error('database_save_message_error', user_id=user_id, error=str(e))
            raise

    def get_chat_history(self, user_id: int, limit: int = 5) -> List[Tuple[str, str, datetime]]:
        """Get the chat history for a specific user."""
        try:
            with logfire.span('database_get_chat_history', user_id=user_id, limit=limit):
                cursor = self.conn.cursor()
                cursor.execute(
                    '''
                    SELECT message, response, timestamp 
                    FROM messages 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    ''',
                    (user_id, limit)
                )
                history = cursor.fetchall()
                logger.info(f"Retrieved {len(history)} messages for user {user_id}")
                logfire.info('database_history_retrieved', user_id=user_id, count=len(history))
                return history
        except sqlite3.Error as e:
            logger.error(f"Error retrieving chat history: {e}")
            logfire.error('database_get_history_error', user_id=user_id, error=str(e))
            return []

    def clear_chat_history(self, user_id: int) -> None:
        """Clear the chat history for a specific user."""
        try:
            with logfire.span('database_clear_chat_history', user_id=user_id):
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
                deleted_count = cursor.rowcount
                self.conn.commit()
                logger.info(f"Cleared chat history for user {user_id}")
                logfire.info('database_history_cleared', user_id=user_id, deleted_count=deleted_count)
        except sqlite3.Error as e:
            logger.error(f"Error clearing chat history: {e}")
            logfire.error('database_clear_history_error', user_id=user_id, error=str(e))
            raise

    def close(self):
        """Close the database connection."""
        logger.info("Closing database connection")
        logfire.info('database_connection_closing')
        self.conn.close()

# Create a global instance
db = Database()
