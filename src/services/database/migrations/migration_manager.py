"""
מודול לניהול מיגרציות של מסד הנתונים
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import Database
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MigrationManager:
    """מחלקה לניהול מיגרציות של מסד הנתונים"""
    
    def __init__(self, db: Database):
        """אתחול המחלקה
        
        Args:
            db: מופע של מסד הנתונים
        """
        self.db = db
        self.migrations_dir = Path(__file__).parent / "versions"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
    async def get_current_version(self) -> int:
        """קבלת הגרסה הנוכחית של מסד הנתונים
        
        Returns:
            מספר הגרסה הנוכחית
        """
        try:
            async with self.db.session() as session:
                # בדיקה אם טבלת המיגרציות קיימת
                inspector = inspect(self.db.engine)
                if not inspector.has_table("migrations"):
                    await self._create_migrations_table(session)
                    return 0
                    
                # קבלת הגרסה האחרונה
                result = await session.execute(
                    text("SELECT version FROM migrations ORDER BY version DESC LIMIT 1")
                )
                version = result.scalar()
                return version or 0
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת גרסת מסד הנתונים: {str(e)}")
            raise
            
    async def _create_migrations_table(self, session: AsyncSession) -> None:
        """יצירת טבלת המיגרציות
        
        Args:
            session: סשן של מסד הנתונים
        """
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    version INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await session.commit()
            logger.info("טבלת migrations נוצרה בהצלחה")
            
        except Exception as e:
            logger.error(f"שגיאה ביצירת טבלת migrations: {str(e)}")
            raise
            
    async def apply_migrations(self, target_version: Optional[int] = None) -> None:
        """הרצת מיגרציות
        
        Args:
            target_version: הגרסה הרצויה (אופציונלי, ברירת מחדל: הגרסה האחרונה)
        """
        try:
            current_version = await self.get_current_version()
            
            # קבלת כל קבצי המיגרציה
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            
            if not migration_files:
                logger.info("לא נמצאו קבצי מיגרציה")
                return
                
            # חישוב הגרסה האחרונה אם לא צוינה גרסה
            if target_version is None:
                target_version = len(migration_files)
                
            # הרצת המיגרציות הנדרשות
            async with self.db.session() as session:
                for migration_file in migration_files:
                    version = int(migration_file.stem.split("_")[0])
                    
                    # דילוג על מיגרציות שכבר הורצו או שלא צריך להריץ
                    if version <= current_version or version > target_version:
                        continue
                        
                    # קריאת קובץ המיגרציה
                    sql = migration_file.read_text(encoding='utf-8')
                    
                    try:
                        # הרצת המיגרציה
                        await session.execute(text(sql))
                        
                        # עדכון טבלת המיגרציות
                        await session.execute(
                            text("""
                                INSERT INTO migrations (version, name)
                                VALUES (:version, :name)
                            """),
                            {
                                "version": version,
                                "name": migration_file.stem
                            }
                        )
                        
                        await session.commit()
                        logger.info(f"מיגרציה {migration_file.name} הורצה בהצלחה")
                        
                    except Exception as e:
                        logger.error(f"שגיאה בהרצת מיגרציה {migration_file.name}: {str(e)}")
                        await session.rollback()
                        raise
                        
        except Exception as e:
            logger.error(f"שגיאה בהרצת מיגרציות: {str(e)}")
            raise
            
    async def create_migration(self, name: str, sql: str) -> Path:
        """יצירת קובץ מיגרציה חדש
        
        Args:
            name: שם המיגרציה
            sql: תוכן המיגרציה
            
        Returns:
            נתיב לקובץ המיגרציה שנוצר
        """
        try:
            # קבלת המספר הבא בתור
            current_version = await self.get_current_version()
            next_version = current_version + 1
            
            # יצירת שם הקובץ
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{next_version:03d}_{timestamp}_{name}.sql"
            
            # יצירת הקובץ
            file_path = self.migrations_dir / filename
            file_path.write_text(sql, encoding='utf-8')
            
            logger.info(f"נוצר קובץ מיגרציה חדש: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"שגיאה ביצירת קובץ מיגרציה: {str(e)}")
            raise
            
    async def rollback(self, steps: int = 1) -> None:
        """ביטול מיגרציות
        
        Args:
            steps: מספר המיגרציות לביטול
        """
        try:
            current_version = await self.get_current_version()
            target_version = max(0, current_version - steps)
            
            # הרצת המיגרציות עד לגרסה הרצויה
            await self.apply_migrations(target_version)
            
        except Exception as e:
            logger.error(f"שגיאה בביטול מיגרציות: {str(e)}")
            raise 