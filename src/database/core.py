"""
מודול ליבה למסד הנתונים - התחברות למסד הנתונים והגדרת מנוע
"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Initialize logging
logger = logging.getLogger(__name__)

# יבוא הגדרות מקובץ config
from ..core.config import DATABASE_URL, LOGFIRE_API_KEY, LOGFIRE_PROJECT

# הגדרת פרויקט logfire
os.environ['LOGFIRE_PROJECT'] = LOGFIRE_PROJECT

# אתחול logfire
try:
    import logfire
    logfire.configure(
        token=LOGFIRE_API_KEY,
        pydantic_plugin=logfire.PydanticPlugin(record='all')
    )
    logger.info("Logfire initialized successfully")
except (AttributeError, ImportError):
    logger.warning("Logfire not configured properly")

# יצירת מנוע מסד הנתונים
engine = create_async_engine(DATABASE_URL, poolclass=NullPool)

# יצירת פקטורי לסשן
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# ייצוא המשתנים הגלובליים
__all__ = ['engine', 'async_session'] 