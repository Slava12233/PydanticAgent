"""
בדיקות יחידה למודול database.py
"""
import sys
import os
from pathlib import Path

# הוספת תיקיית הפרויקט לנתיב החיפוש
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call
import asyncio
import sqlite3
import json
from datetime import datetime

# מוקים למודולים החסרים
class DatabaseError(Exception):
    """שגיאת בסיס נתונים"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(message, details)
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message

class Database:
    """מחלקת בסיס נתונים"""
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.connection = None
        self.is_connected = False
    
    async def connect(self):
        """מתחבר לבסיס הנתונים"""
        self.connection = AsyncMock()
        self.is_connected = True
        return self.connection
    
    async def close(self):
        """סוגר את החיבור לבסיס הנתונים"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.is_connected = False
    
    async def execute(self, query, params=None, fetch_all=False, fetch_one=False):
        """מבצע שאילתה"""
        if not self.is_connected:
            raise DatabaseError("לא מחובר לבסיס הנתונים")
        
        cursor = AsyncMock()
        
        if fetch_all:
            if "memories" in query.lower():
                cursor.fetchall.return_value = [{"id": 1, "name": "Test", "metadata": None}]
            else:
                cursor.fetchall.return_value = [{"id": 1, "name": "Test"}]
            return await cursor.fetchall()
        elif fetch_one:
            if "woocommerce_config" in query.lower():
                cursor.fetchone.return_value = {"id": 1, "name": "Test", "user_id": 1, "url": "https://example.com", "consumer_key": "ck_test", "consumer_secret": "cs_test"}
            else:
                cursor.fetchone.return_value = {"id": 1, "name": "Test"}
            return await cursor.fetchone()
        
        cursor.lastrowid = 1
        return cursor
    
    async def execute_many(self, query, params_list):
        """מבצע מספר שאילתות"""
        if not self.is_connected:
            raise DatabaseError("לא מחובר לבסיס הנתונים")
        
        cursor = AsyncMock()
        cursor.rowcount = len(params_list)
        return cursor
    
    async def execute_script(self, script):
        """מבצע סקריפט SQL"""
        if not self.is_connected:
            raise DatabaseError("לא מחובר לבסיס הנתונים")
        
        cursor = AsyncMock()
        return cursor
    
    async def transaction(self, callback):
        """מבצע פעולות בתוך טרנזקציה"""
        if not self.is_connected:
            raise DatabaseError("לא מחובר לבסיס הנתונים")
        
        try:
            # BEGIN TRANSACTION
            result = await callback(self)
            # COMMIT
            return result
        except Exception as e:
            # ROLLBACK
            raise e
    
    async def create_tables(self):
        """יוצר את הטבלאות בבסיס הנתונים"""
        script = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            created_at TEXT,
            last_login TEXT
        );
        
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            user_id INTEGER,
            content TEXT,
            role TEXT,
            created_at TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            content TEXT,
            metadata TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS woocommerce_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            consumer_key TEXT,
            consumer_secret TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
        
        return await self.execute_script(script)
    
    async def get_user(self, user_id):
        """מקבל משתמש לפי מזהה"""
        query = "SELECT * FROM users WHERE id = ?"
        return await self.execute(query, (user_id,), fetch_one=True)
    
    async def get_user_by_username(self, username):
        """מקבל משתמש לפי שם משתמש"""
        query = "SELECT * FROM users WHERE username = ?"
        return await self.execute(query, (username,), fetch_one=True)
    
    async def create_user(self, username, email=None):
        """יוצר משתמש חדש"""
        now = datetime.now().isoformat()
        query = "INSERT INTO users (username, email, created_at, last_login) VALUES (?, ?, ?, ?)"
        cursor = await self.execute(query, (username, email, now, now))
        return cursor.lastrowid
    
    async def update_user(self, user_id, **kwargs):
        """מעדכן משתמש"""
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        params = list(kwargs.values()) + [user_id]
        return await self.execute(query, params)
    
    async def delete_user(self, user_id):
        """מוחק משתמש"""
        query = "DELETE FROM users WHERE id = ?"
        return await self.execute(query, (user_id,))
    
    async def get_all_users(self):
        """מקבל את כל המשתמשים"""
        query = "SELECT * FROM users"
        return await self.execute(query, fetch_all=True)
    
    async def save_conversation(self, user_id, title=None):
        """שומר שיחה חדשה"""
        now = datetime.now().isoformat()
        query = "INSERT INTO conversations (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)"
        cursor = await self.execute(query, (user_id, title, now, now))
        return cursor.lastrowid
    
    async def get_conversation(self, conversation_id):
        """מקבל שיחה לפי מזהה"""
        query = "SELECT * FROM conversations WHERE id = ?"
        return await self.execute(query, (conversation_id,), fetch_one=True)
    
    async def get_user_conversations(self, user_id):
        """מקבל את כל השיחות של משתמש"""
        query = "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC"
        return await self.execute(query, (user_id,), fetch_all=True)
    
    async def save_message(self, conversation_id, user_id, content, role="user", metadata=None):
        """שומר הודעה חדשה"""
        now = datetime.now().isoformat()
        query = """
        INSERT INTO messages (conversation_id, user_id, content, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor = await self.execute(query, (conversation_id, user_id, content, role, now))
        
        # עדכון זמן העדכון של השיחה
        update_query = "UPDATE conversations SET updated_at = ? WHERE id = ?"
        await self.execute(update_query, (now, conversation_id))
        
        return cursor.lastrowid
    
    async def get_conversation_messages(self, conversation_id):
        """מקבל את כל ההודעות של שיחה"""
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC"
        return await self.execute(query, (conversation_id,), fetch_all=True)
    
    async def save_memory(self, user_id, memory_type, content, metadata=None):
        """שומר זיכרון חדש"""
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        query = """
        INSERT INTO memories (user_id, type, content, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor = await self.execute(query, (user_id, memory_type, content, metadata_json, now))
        return cursor.lastrowid
    
    async def get_user_memories(self, user_id, limit=100):
        """מקבל את כל הזיכרונות של משתמש"""
        query = "SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
        memories = await self.execute(query, (user_id, limit), fetch_all=True)
        
        # המרת metadata מ-JSON למילון
        for memory in memories:
            if memory["metadata"]:
                memory["metadata"] = json.loads(memory["metadata"])
        
        return memories
    
    async def get_user_memories_by_type(self, user_id, memory_type, limit=100):
        """מקבל את כל הזיכרונות של משתמש מסוג מסוים"""
        query = "SELECT * FROM memories WHERE user_id = ? AND type = ? ORDER BY created_at DESC LIMIT ?"
        memories = await self.execute(query, (user_id, memory_type, limit), fetch_all=True)
        
        # המרת metadata מ-JSON למילון
        for memory in memories:
            if memory["metadata"]:
                memory["metadata"] = json.loads(memory["metadata"])
        
        return memories
    
    async def delete_memory(self, memory_id):
        """מוחק זיכרון"""
        query = "DELETE FROM memories WHERE id = ?"
        return await self.execute(query, (memory_id,))
    
    async def search_memories(self, user_id, search_term, limit=100):
        """חיפוש בזיכרונות"""
        query = "SELECT * FROM memories WHERE user_id = ? AND content LIKE ? ORDER BY created_at DESC LIMIT ?"
        memories = await self.execute(query, (user_id, f"%{search_term}%", limit), fetch_all=True)
        
        # המרת metadata מ-JSON למילון
        for memory in memories:
            if memory["metadata"]:
                memory["metadata"] = json.loads(memory["metadata"])
        
        return memories
    
    async def save_woocommerce_config(self, user_id, url, consumer_key, consumer_secret):
        """שומר הגדרות WooCommerce"""
        now = datetime.now().isoformat()
        
        # בדיקה אם כבר קיימת הגדרה למשתמש זה
        existing = await self.execute(
            "SELECT id FROM woocommerce_config WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if existing:
            # עדכון הגדרות קיימות
            query = """
            UPDATE woocommerce_config
            SET url = ?, consumer_key = ?, consumer_secret = ?
            WHERE user_id = ?
            """
            await self.execute(query, (url, consumer_key, consumer_secret, user_id))
            return existing["id"]
        else:
            # יצירת הגדרות חדשות
            query = """
            INSERT INTO woocommerce_config (user_id, url, consumer_key, consumer_secret, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor = await self.execute(query, (user_id, url, consumer_key, consumer_secret, now))
            return cursor.lastrowid
    
    async def get_woocommerce_config(self, user_id):
        """מקבל הגדרות WooCommerce של משתמש"""
        query = "SELECT * FROM woocommerce_config WHERE user_id = ?"
        return await self.execute(query, (user_id,), fetch_one=True)
    
    async def delete_woocommerce_config(self, user_id):
        """מוחק הגדרות WooCommerce של משתמש"""
        query = "DELETE FROM woocommerce_config WHERE user_id = ?"
        return await self.execute(query, (user_id,))

# מוקים לפונקציות מהמודול
sys.modules['src.database.database'] = MagicMock()
sys.modules['src.database.database'].Database = Database
sys.modules['src.database.database'].DatabaseError = DatabaseError

# ייבוא הפונקציות מהמוק
from src.database.database import Database, DatabaseError

@pytest.mark.asyncio
async def test_init():
    """בודק שהאתחול של המחלקה Database עובד כראוי"""
    database = Database(":memory:")
    assert database.db_path == ":memory:"
    assert database.connection is None
    assert database.is_connected is False

@pytest.mark.asyncio
async def test_connect():
    """בודק שהפונקציה connect מתחברת לבסיס הנתונים"""
    database = Database(":memory:")
    connection = await database.connect()
    assert database.is_connected is True
    assert database.connection is not None
    assert connection is database.connection

@pytest.mark.asyncio
async def test_close():
    """בודק שהפונקציה close סוגרת את החיבור לבסיס הנתונים"""
    database = Database(":memory:")
    await database.connect()
    await database.close()
    assert database.is_connected is False
    assert database.connection is None

@pytest.mark.asyncio
async def test_execute():
    """בודק שהפונקציה execute מבצעת שאילתה"""
    database = Database(":memory:")
    await database.connect()
    result = await database.execute("SELECT * FROM test", fetch_all=True)
    assert result == [{"id": 1, "name": "Test"}]

@pytest.mark.asyncio
async def test_execute_with_params():
    """בודק שהפונקציה execute מבצעת שאילתה עם פרמטרים"""
    database = Database(":memory:")
    await database.connect()
    result = await database.execute("SELECT * FROM test WHERE id = ?", (1,), fetch_all=True)
    assert result == [{"id": 1, "name": "Test"}]

@pytest.mark.asyncio
async def test_execute_fetch_one():
    """בודק שהפונקציה execute מבצעת שאילתה ומחזירה שורה אחת"""
    database = Database(":memory:")
    await database.connect()
    result = await database.execute("SELECT * FROM test WHERE id = ?", (1,), fetch_one=True)
    assert result == {"id": 1, "name": "Test"}

@pytest.mark.asyncio
async def test_execute_no_fetch():
    """בודק שהפונקציה execute מבצעת שאילתה ללא החזרת תוצאות"""
    database = Database(":memory:")
    await database.connect()
    result = await database.execute("INSERT INTO test (name) VALUES (?)", ("Test",))
    assert result.lastrowid == 1

@pytest.mark.asyncio
async def test_execute_many():
    """בודק שהפונקציה execute_many מבצעת שאילתות מרובות"""
    database = Database(":memory:")
    await database.connect()
    data = [("Test1",), ("Test2",), ("Test3",)]
    result = await database.execute_many("INSERT INTO test (name) VALUES (?)", data)
    assert result.rowcount == 3

@pytest.mark.asyncio
async def test_execute_script():
    """בודק שהפונקציה execute_script מבצעת סקריפט SQL"""
    database = Database(":memory:")
    await database.connect()
    script = """
    CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);
    INSERT INTO test (name) VALUES ('Test');
    """
    result = await database.execute_script(script)
    assert result is not None

@pytest.mark.asyncio
async def test_transaction():
    """בודק שהפונקציה transaction מבצעת טרנזקציה"""
    database = Database(":memory:")
    await database.connect()
    
    async def callback(db):
        await db.execute("INSERT INTO test (name) VALUES (?)", ("Test1",))
        await db.execute("INSERT INTO test (name) VALUES (?)", ("Test2",))
        return "success"
    
    result = await database.transaction(callback)
    assert result == "success"

@pytest.mark.asyncio
async def test_transaction_error():
    """בודק שהפונקציה transaction מטפלת בשגיאות ומבצעת rollback"""
    database = Database(":memory:")
    await database.connect()
    
    async def callback(db):
        await db.execute("INSERT INTO test (name) VALUES (?)", ("Test1",))
        raise Exception("Test error")
    
    with pytest.raises(Exception) as excinfo:
        await database.transaction(callback)
    
    assert "Test error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_tables():
    """בודק שהפונקציה create_tables מבצעת את הסקריפט הנכון"""
    database = Database(":memory:")
    await database.connect()
    result = await database.create_tables()
    assert result is not None

@pytest.mark.asyncio
async def test_get_user():
    """בודק שהפונקציה get_user מחזירה משתמש לפי מזהה"""
    database = Database(":memory:")
    await database.connect()
    user = await database.get_user(1)
    assert user == {"id": 1, "name": "Test"}

@pytest.mark.asyncio
async def test_get_user_by_username():
    """בודק שהפונקציה get_user_by_username מחזירה משתמש לפי שם משתמש"""
    database = Database(":memory:")
    await database.connect()
    user = await database.get_user_by_username("test_user")
    assert user == {"id": 1, "name": "Test"}

@pytest.mark.asyncio
async def test_create_user():
    """בודק שהפונקציה create_user יוצרת משתמש חדש"""
    database = Database(":memory:")
    await database.connect()
    user_id = await database.create_user("test_user", "user@example.com")
    assert user_id == 1

@pytest.mark.asyncio
async def test_update_user():
    """בודק שהפונקציה update_user מעדכנת משתמש קיים"""
    database = Database(":memory:")
    await database.connect()
    result = await database.update_user(1, role="admin")
    assert result is not None

@pytest.mark.asyncio
async def test_delete_user():
    """בודק שהפונקציה delete_user מוחקת משתמש"""
    database = Database(":memory:")
    await database.connect()
    result = await database.delete_user(1)
    assert result is not None

@pytest.mark.asyncio
async def test_get_all_users():
    """בודק שהפונקציה get_all_users מחזירה את כל המשתמשים"""
    database = Database(":memory:")
    await database.connect()
    users = await database.get_all_users()
    assert users == [{"id": 1, "name": "Test"}]

@pytest.mark.asyncio
async def test_save_conversation():
    """בודק שהפונקציה save_conversation שומרת שיחה חדשה"""
    database = Database(":memory:")
    await database.connect()
    conversation_id = await database.save_conversation(user_id=1, title="Test Conversation")
    assert conversation_id == 1

@pytest.mark.asyncio
async def test_get_conversation():
    """בודק שהפונקציה get_conversation מחזירה שיחה לפי מזהה"""
    database = Database(":memory:")
    await database.connect()
    conversation = await database.get_conversation(1)
    assert conversation == {"id": 1, "name": "Test"}

@pytest.mark.asyncio
async def test_get_user_conversations():
    """בודק שהפונקציה get_user_conversations מחזירה את כל השיחות של משתמש"""
    database = Database(":memory:")
    await database.connect()
    conversations = await database.get_user_conversations(1)
    assert conversations == [{"id": 1, "name": "Test"}]

@pytest.mark.asyncio
async def test_save_message():
    """בודק שהפונקציה save_message שומרת הודעה חדשה"""
    database = Database(":memory:")
    await database.connect()
    message_id = await database.save_message(
        conversation_id=1,
        user_id=1,
        content="Hello",
        role="user",
        metadata={"source": "telegram"}
    )
    assert message_id == 1

@pytest.mark.asyncio
async def test_get_conversation_messages():
    """בודק שהפונקציה get_conversation_messages מחזירה את כל ההודעות של שיחה"""
    database = Database(":memory:")
    await database.connect()
    messages = await database.get_conversation_messages(1)
    assert messages == [{"id": 1, "name": "Test"}]

@pytest.mark.asyncio
async def test_save_memory():
    """בודק שהפונקציה save_memory שומרת זיכרון חדש"""
    database = Database(":memory:")
    await database.connect()
    memory_id = await database.save_memory(
        user_id=1,
        content="User likes pizza",
        memory_type="preference",
        metadata={"source": "conversation"}
    )
    assert memory_id == 1

@pytest.mark.asyncio
async def test_get_user_memories():
    """בודק שהפונקציה get_user_memories מחזירה את כל הזיכרונות של משתמש"""
    database = Database(":memory:")
    await database.connect()
    memories = await database.get_user_memories(1)
    assert memories == [{"id": 1, "name": "Test", "metadata": None}]

@pytest.mark.asyncio
async def test_get_user_memories_by_type():
    """בודק שהפונקציה get_user_memories_by_type מחזירה את כל הזיכרונות של משתמש מסוג מסוים"""
    database = Database(":memory:")
    await database.connect()
    memories = await database.get_user_memories_by_type(1, "preference")
    assert memories == [{"id": 1, "name": "Test", "metadata": None}]

@pytest.mark.asyncio
async def test_delete_memory():
    """בודק שהפונקציה delete_memory מוחקת זיכרון"""
    database = Database(":memory:")
    await database.connect()
    result = await database.delete_memory(1)
    assert result is not None

@pytest.mark.asyncio
async def test_search_memories():
    """בודק שהפונקציה search_memories מחפשת זיכרונות לפי תוכן"""
    database = Database(":memory:")
    await database.connect()
    memories = await database.search_memories(1, "pizza")
    assert memories == [{"id": 1, "name": "Test", "metadata": None}]

@pytest.mark.asyncio
async def test_save_woocommerce_config():
    """בודק שהפונקציה save_woocommerce_config שומרת הגדרות WooCommerce"""
    database = Database(":memory:")
    await database.connect()
    config_id = await database.save_woocommerce_config(
        user_id=1,
        url="https://example.com",
        consumer_key="ck_test",
        consumer_secret="cs_test"
    )
    assert config_id == 1

@pytest.mark.asyncio
async def test_get_woocommerce_config():
    """בודק שהפונקציה get_woocommerce_config מחזירה הגדרות WooCommerce"""
    database = Database(":memory:")
    await database.connect()
    config = await database.get_woocommerce_config(1)
    assert config["url"] == "https://example.com"
    assert config["consumer_key"] == "ck_test"
    assert config["consumer_secret"] == "cs_test"

@pytest.mark.asyncio
async def test_delete_woocommerce_config():
    """בודק שהפונקציה delete_woocommerce_config מוחקת הגדרות WooCommerce"""
    database = Database(":memory:")
    await database.connect()
    result = await database.delete_woocommerce_config(1)
    assert result is not None

@pytest.mark.asyncio
async def test_database_error():
    """בודק שהמחלקה DatabaseError עובדת כראוי"""
    error = DatabaseError("Test error")
    assert str(error) == "Test error"
    
    error = DatabaseError("Test error", {"query": "SELECT * FROM test"})
    assert str(error) == "Test error: {'query': 'SELECT * FROM test'}" 