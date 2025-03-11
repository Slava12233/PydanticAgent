"""
מודל בסיסי למסד הנתונים
"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    """
    מחלקת בסיס למודלים של מסד הנתונים
    כל המודלים יורשים ממחלקה זו
    """
    pass
