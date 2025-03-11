"""
מנהל מסד הנתונים - מחלקה מרכזית לניהול הקשר עם מסד הנתונים
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import text

# Initialize logging
logger = logging.getLogger(__name__)

# יבוא מנוע מסד הנתונים והסשן מקובץ core
from .core import engine, async_session

class DatabaseManager:
    """מנהל מסד הנתונים - מחלקה מרכזית לניהול הקשר עם מסד הנתונים"""
    
    def __init__(self):
        """Initialize the database"""
        self.engine = engine
        self.async_session = async_session
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get a database session as an async context manager
        
        Yields:
            AsyncSession: Database session
        """
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
    
    @property
    def session(self):
        """
        Get a database session as a context manager
        
        Returns:
            AsyncSession: Database session context manager
        """
        return self.async_session
    
    async def create_all(self):
        """Create all database tables"""
        from src.database.models.base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_all(self):
        """Drop all database tables"""
        from src.database.models.base import Base
        from sqlalchemy import text
        
        # שימוש ב-CASCADE כדי למחוק את כל הטבלאות עם התלויות שלהן
        async with self.engine.begin() as conn:
            # קבלת רשימת כל הטבלאות במסד הנתונים
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = result.scalars().all()
            
            if tables:
                # מחיקת כל הטבלאות עם CASCADE
                await conn.execute(text(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE"))
                logger.info(f"Dropped all tables with CASCADE: {', '.join(tables)}")
            else:
                logger.info("No tables to drop")
    
    async def init_db(self, recreate_tables=False):
        """
        Initialize the database
        
        Args:
            recreate_tables: If True, drop and recreate all tables
        """
        try:
            if recreate_tables:
                await self.drop_all()
            await self.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def select(self, *args, **kwargs):
        """Wrapper for sqlalchemy select"""
        from sqlalchemy import select
        return select(*args, **kwargs)
    
    @property
    def func(self):
        """Wrapper for sqlalchemy func"""
        from sqlalchemy import func
        return func
    
    @property
    def and_(self):
        """Wrapper for sqlalchemy and_"""
        from sqlalchemy import and_
        return and_
    
    @property
    def or_(self):
        """Wrapper for sqlalchemy or_"""
        from sqlalchemy import or_
        return or_
    
    @property
    def desc(self):
        """Wrapper for sqlalchemy desc"""
        from sqlalchemy import desc
        return desc
    
    @property
    def asc(self):
        """Wrapper for sqlalchemy asc"""
        from sqlalchemy import asc
        return asc
    
    async def execute(self, query, params=None):
        """
        Execute a raw SQL query
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            Query result
        """
        async with self.get_session() as session:
            result = await session.execute(query, params)
            return result
    
    async def scalar(self, query, params=None):
        """
        Execute a query and return a scalar result
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            Scalar result
        """
        async with self.get_session() as session:
            result = await session.scalar(query, params)
            return result
    
    async def scalars(self, query, params=None):
        """
        Execute a query and return multiple scalar results
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            List of scalar results
        """
        async with self.get_session() as session:
            result = await session.scalars(query, params)
            return result
    
    async def add(self, obj):
        """
        Add an object to the session
        
        Args:
            obj: Object to add
        """
        async with self.get_session() as session:
            session.add(obj)
            await session.commit()
    
    async def delete(self, obj):
        """
        Delete an object from the session
        
        Args:
            obj: Object to delete
        """
        async with self.get_session() as session:
            await session.delete(obj)
            await session.commit()
    
    async def flush(self):
        """Flush the session"""
        async with self.get_session() as session:
            await session.flush()
    
    async def commit(self):
        """Commit the session"""
        async with self.get_session() as session:
            await session.commit()
    
    async def rollback(self):
        """Rollback the session"""
        async with self.get_session() as session:
            await session.rollback()
    
    async def close(self):
        """Close the session"""
        try:
            # אין צורך לסגור את ה-sessionmaker עצמו
            # רק לרשום הודעת לוג שהחיבור נסגר
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def refresh(self, obj):
        """
        Refresh an object from the database
        
        Args:
            obj: Object to refresh
        """
        async with self.get_session() as session:
            await session.refresh(obj)
    
    async def merge(self, obj):
        """
        Merge an object with the session
        
        Args:
            obj: Object to merge
            
        Returns:
            Merged object
        """
        async with self.get_session() as session:
            result = await session.merge(obj)
            await session.commit()
            return result
    
    async def bulk_save_objects(self, objects):
        """
        Save multiple objects in bulk
        
        Args:
            objects: List of objects to save
        """
        async with self.get_session() as session:
            session.bulk_save_objects(objects)
            await session.commit()
    
    async def bulk_insert_mappings(self, mapper, mappings):
        """
        Insert multiple mappings in bulk
        
        Args:
            mapper: SQLAlchemy mapper
            mappings: List of mappings to insert
        """
        async with self.get_session() as session:
            session.bulk_insert_mappings(mapper, mappings)
            await session.commit()
    
    async def bulk_update_mappings(self, mapper, mappings):
        """
        Update multiple mappings in bulk
        
        Args:
            mapper: SQLAlchemy mapper
            mappings: List of mappings to update
        """
        async with self.get_session() as session:
            session.bulk_update_mappings(mapper, mappings)
            await session.commit()
    
    async def execute_many(self, statement, params_seq):
        """
        Execute multiple statements with different parameters
        
        Args:
            statement: SQL statement to execute
            params_seq: Sequence of parameters
        """
        async with self.get_session() as session:
            await session.execute(statement, params_seq)
            await session.commit()
    
    async def get_or_create(self, model, defaults=None, **kwargs):
        """
        Get an object or create it if it doesn't exist
        
        Args:
            model: SQLAlchemy model
            defaults: Default values for creation
            **kwargs: Lookup parameters
            
        Returns:
            Tuple of (object, created)
        """
        async with self.get_session() as session:
            instance = await session.scalar(
                self.select(model).filter_by(**kwargs)
            )
            if instance:
                return instance, False
            
            params = dict(kwargs)
            if defaults:
                params.update(defaults)
            instance = model(**params)
            session.add(instance)
            await session.commit()
            return instance, True
    
    async def update_or_create(self, model, defaults=None, **kwargs):
        """
        Update an object or create it if it doesn't exist
        
        Args:
            model: SQLAlchemy model
            defaults: Default values for creation/update
            **kwargs: Lookup parameters
            
        Returns:
            Tuple of (object, created)
        """
        async with self.get_session() as session:
            instance = await session.scalar(
                self.select(model).filter_by(**kwargs)
            )
            if instance:
                if defaults:
                    for key, value in defaults.items():
                        setattr(instance, key, value)
                await session.commit()
                return instance, False
            
            params = dict(kwargs)
            if defaults:
                params.update(defaults)
            instance = model(**params)
            session.add(instance)
            await session.commit()
            return instance, True
    
    async def count(self, query):
        """
        Count the number of results for a query
        
        Args:
            query: Query to count
            
        Returns:
            Number of results
        """
        async with self.get_session() as session:
            count_query = query.with_only_columns([self.func.count()]).order_by(None)
            result = await session.scalar(count_query)
            return result
    
    async def exists(self, query):
        """
        Check if any result exists for a query
        
        Args:
            query: Query to check
            
        Returns:
            True if results exist, False otherwise
        """
        async with self.get_session() as session:
            exists_query = query.exists()
            result = await session.scalar(exists_query)
            return result
    
    async def get_or_404(self, model, id):
        """
        Get an object by ID or raise 404
        
        Args:
            model: SQLAlchemy model
            id: Object ID
            
        Returns:
            Object if found
            
        Raises:
            404 error if not found
        """
        async with self.get_session() as session:
            instance = await session.get(model, id)
            if not instance:
                raise Exception(f"{model.__name__} with id {id} not found")
            return instance
    
    async def first_or_404(self, query):
        """
        Get first result or raise 404
        
        Args:
            query: Query to execute
            
        Returns:
            First result if found
            
        Raises:
            404 error if not found
        """
        async with self.get_session() as session:
            instance = await session.scalar(query)
            if not instance:
                raise Exception("No results found")
            return instance
    
    async def paginate(self, query, page=1, per_page=10):
        """
        Paginate query results
        
        Args:
            query: Query to paginate
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with pagination info and results
        """
        async with self.get_session() as session:
            total = await self.count(query)
            
            offset = (page - 1) * per_page
            items = await session.scalars(
                query.offset(offset).limit(per_page)
            )
            
            return {
                'items': list(items),
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }

# Create a database instance
db = DatabaseManager()
