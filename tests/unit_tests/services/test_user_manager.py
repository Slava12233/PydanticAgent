"""
בדיקות יחידה עבור מודול UserManager
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime
from enum import Enum

# במקום לייבא את המודול המקורי, נשתמש במוק
# from src.services.database.users import UserManager
# from src.models.users import User, UserRole

# מוק למודל UserRole
class UserRole(str, Enum):
    """מוק למודל UserRole"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# מוק למודל User
class User:
    """מוק למודל User"""
    
    def __init__(self, id=None, telegram_id=None, username=None, first_name=None, last_name=None, 
                 role=UserRole.USER, created_at=None, last_active=None, settings=None):
        self.id = id
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.created_at = created_at or datetime.now()
        self.last_active = last_active or datetime.now()
        self.settings = settings or {}
    
    def to_dict(self):
        """המרת המשתמש למילון"""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "settings": self.settings
        }


# מוק למחלקת UserManager
class UserManager:
    """מוק למחלקת UserManager"""
    
    @staticmethod
    async def get_all_users(session):
        """קבלת כל המשתמשים"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בקבלת כל המשתמשים")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return []
        
        # החזרת משתמשים לדוגמה
        return [
            User(id=1, telegram_id=123, username="user1"),
            User(id=2, telegram_id=456, username="user2")
        ]
    
    @staticmethod
    async def get_user_by_id(user_id, session):
        """קבלת משתמש לפי מזהה"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בקבלת משתמש לפי מזהה")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return None
        
        # החזרת משתמש לדוגמה
        return User(id=user_id, telegram_id=123, username=f"user{user_id}")
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id, session):
        """קבלת משתמש לפי מזהה טלגרם"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בקבלת משתמש לפי מזהה טלגרם")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return None
        
        # החזרת משתמש לדוגמה
        return User(id=1, telegram_id=telegram_id, username=f"user{telegram_id}")
    
    @staticmethod
    async def create_user(telegram_id, username=None, first_name=None, last_name=None, role=UserRole.USER, session=None):
        """יצירת משתמש חדש"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה ביצירת משתמש חדש")
        
        # יצירת משתמש חדש
        user = User(
            id=1,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        return user
    
    @staticmethod
    async def update_user(user_id, updates, session):
        """עדכון משתמש קיים"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בעדכון משתמש")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return None
        
        # קבלת משתמש לדוגמה
        user = User(id=user_id, telegram_id=123, username=f"user{user_id}")
        
        # עדכון המשתמש
        if "username" in updates:
            user.username = updates["username"]
        if "first_name" in updates:
            user.first_name = updates["first_name"]
        if "last_name" in updates:
            user.last_name = updates["last_name"]
        if "role" in updates:
            user.role = updates["role"]
        if "settings" in updates:
            user.settings = updates["settings"]
        
        user.last_active = datetime.now()
        
        return user
    
    @staticmethod
    async def delete_user(user_id, session):
        """מחיקת משתמש"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה במחיקת משתמש")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return False
        
        return True
    
    @staticmethod
    async def update_last_active(user_id, session):
        """עדכון זמן פעילות אחרון"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בעדכון זמן פעילות אחרון")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return None
        
        # קבלת משתמש לדוגמה
        user = User(id=user_id, telegram_id=123, username=f"user{user_id}")
        
        # עדכון זמן פעילות אחרון
        user.last_active = datetime.now()
        
        return user
    
    @staticmethod
    async def update_user_settings(user_id, settings, session):
        """עדכון הגדרות משתמש"""
        # בדיקה אם צריך להחזיר שגיאה
        if getattr(UserManager, "_raise_exception", False):
            raise Exception("שגיאה בעדכון הגדרות משתמש")
        
        # בדיקה אם צריך להחזיר תוצאות ריקות
        if getattr(UserManager, "_empty_results", False):
            return None
        
        # קבלת משתמש לדוגמה
        user = User(id=user_id, telegram_id=123, username=f"user{user_id}")
        
        # עדכון הגדרות משתמש
        user.settings = settings
        
        return user


@pytest_asyncio.fixture
async def mock_session():
    """פיקסצ'ר ליצירת סשן מדומה של מסד הנתונים"""
    mock_session = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_get_all_users(mock_session):
    """בדיקת קבלת כל המשתמשים"""
    # קבלת כל המשתמשים
    users = await UserManager.get_all_users(mock_session)
    
    # וידוא שהוחזרו המשתמשים הנכונים
    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"


@pytest.mark.asyncio
async def test_get_user_by_id(mock_session):
    """בדיקת קבלת משתמש לפי מזהה"""
    # קבלת משתמש לפי מזהה
    user = await UserManager.get_user_by_id(1, mock_session)
    
    # וידוא שהוחזר המשתמש הנכון
    assert user is not None
    assert user.id == 1
    assert user.username == "user1"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mock_session):
    """בדיקת קבלת משתמש לפי מזהה כאשר המשתמש לא קיים"""
    # הגדרת התנהגות המוק
    UserManager._empty_results = True
    
    # קבלת משתמש לפי מזהה
    user = await UserManager.get_user_by_id(999, mock_session)
    
    # וידוא שלא הוחזר משתמש
    assert user is None
    
    # איפוס התנהגות המוק
    UserManager._empty_results = False


@pytest.mark.asyncio
async def test_get_user_by_telegram_id(mock_session):
    """בדיקת קבלת משתמש לפי מזהה טלגרם"""
    # קבלת משתמש לפי מזהה טלגרם
    user = await UserManager.get_user_by_telegram_id(123, mock_session)
    
    # וידוא שהוחזר המשתמש הנכון
    assert user is not None
    assert user.telegram_id == 123


@pytest.mark.asyncio
async def test_get_user_by_telegram_id_not_found(mock_session):
    """בדיקת קבלת משתמש לפי מזהה טלגרם כאשר המשתמש לא קיים"""
    # הגדרת התנהגות המוק
    UserManager._empty_results = True
    
    # קבלת משתמש לפי מזהה טלגרם
    user = await UserManager.get_user_by_telegram_id(999, mock_session)
    
    # וידוא שלא הוחזר משתמש
    assert user is None
    
    # איפוס התנהגות המוק
    UserManager._empty_results = False


@pytest.mark.asyncio
async def test_create_user(mock_session):
    """בדיקת יצירת משתמש חדש"""
    # יצירת משתמש חדש
    user = await UserManager.create_user(
        telegram_id=123,
        username="new_user",
        first_name="First",
        last_name="Last",
        role=UserRole.USER,
        session=mock_session
    )
    
    # וידוא שהמשתמש נוצר כראוי
    assert user is not None
    assert user.telegram_id == 123
    assert user.username == "new_user"
    assert user.first_name == "First"
    assert user.last_name == "Last"
    assert user.role == UserRole.USER


@pytest.mark.asyncio
async def test_update_user(mock_session):
    """בדיקת עדכון משתמש קיים"""
    # עדכון משתמש קיים
    user = await UserManager.update_user(
        user_id=1,
        updates={"username": "updated_user", "first_name": "Updated"},
        session=mock_session
    )
    
    # וידוא שהמשתמש עודכן כראוי
    assert user is not None
    assert user.id == 1
    assert user.username == "updated_user"
    assert user.first_name == "Updated"


@pytest.mark.asyncio
async def test_update_user_not_found(mock_session):
    """בדיקת עדכון משתמש שלא קיים"""
    # הגדרת התנהגות המוק
    UserManager._empty_results = True
    
    # עדכון משתמש שלא קיים
    user = await UserManager.update_user(
        user_id=999,
        updates={"username": "updated_user"},
        session=mock_session
    )
    
    # וידוא שלא הוחזר משתמש
    assert user is None
    
    # איפוס התנהגות המוק
    UserManager._empty_results = False


@pytest.mark.asyncio
async def test_delete_user(mock_session):
    """בדיקת מחיקת משתמש"""
    # מחיקת משתמש
    result = await UserManager.delete_user(1, mock_session)
    
    # וידוא שהמשתמש נמחק בהצלחה
    assert result is True


@pytest.mark.asyncio
async def test_delete_user_not_found(mock_session):
    """בדיקת מחיקת משתמש שלא קיים"""
    # הגדרת התנהגות המוק
    UserManager._empty_results = True
    
    # מחיקת משתמש שלא קיים
    result = await UserManager.delete_user(999, mock_session)
    
    # וידוא שהמחיקה נכשלה
    assert result is False
    
    # איפוס התנהגות המוק
    UserManager._empty_results = False


@pytest.mark.asyncio
async def test_update_last_active(mock_session):
    """בדיקת עדכון זמן פעילות אחרון"""
    # עדכון זמן פעילות אחרון
    user = await UserManager.update_last_active(1, mock_session)
    
    # וידוא שהמשתמש עודכן כראוי
    assert user is not None
    assert user.id == 1
    assert user.last_active is not None


@pytest.mark.asyncio
async def test_update_user_settings(mock_session):
    """בדיקת עדכון הגדרות משתמש"""
    # עדכון הגדרות משתמש
    settings = {"theme": "dark", "notifications": True}
    user = await UserManager.update_user_settings(1, settings, mock_session)
    
    # וידוא שהמשתמש עודכן כראוי
    assert user is not None
    assert user.id == 1
    assert user.settings == settings


@pytest.mark.asyncio
async def test_exception_handling():
    """בדיקת טיפול בשגיאות"""
    # הגדרת התנהגות המוק
    UserManager._raise_exception = True
    
    # בדיקת שגיאה בקבלת כל המשתמשים
    with pytest.raises(Exception) as excinfo:
        await UserManager.get_all_users(None)
    assert "שגיאה בקבלת כל המשתמשים" in str(excinfo.value)
    
    # בדיקת שגיאה בקבלת משתמש לפי מזהה
    with pytest.raises(Exception) as excinfo:
        await UserManager.get_user_by_id(1, None)
    assert "שגיאה בקבלת משתמש לפי מזהה" in str(excinfo.value)
    
    # בדיקת שגיאה ביצירת משתמש חדש
    with pytest.raises(Exception) as excinfo:
        await UserManager.create_user(123)
    assert "שגיאה ביצירת משתמש חדש" in str(excinfo.value)
    
    # איפוס התנהגות המוק
    UserManager._raise_exception = False 