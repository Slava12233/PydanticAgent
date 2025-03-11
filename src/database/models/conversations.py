"""
מודלים הקשורים לשיחות
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.models.base import Base

class Conversation(Base):
    """מודל לשמירת שיחות"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # קשרים
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """מודל לשמירת הודעות בשיחה"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # תשובת המערכת להודעה
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata = Column(JSON, default={})
    
    # קשרים
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="user_messages")

class Memory(Base):
    """מודל לשמירת זיכרונות המערכת"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    memory_type = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    conversation = relationship("Conversation", back_populates="memories") 