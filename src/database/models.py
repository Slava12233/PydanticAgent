"""
מודלים למסד הנתונים של המערכת
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # קשרים
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    role = Column(String)  # 'user' או 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG (OpenAI embedding)
    
    # קשרים
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    source = Column(String)  # למשל: 'pdf', 'web', 'manual'
    content = Column(Text)
    doc_metadata = Column(JSON, default={})
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # קשרים
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), index=True)
    content = Column(Text)
    chunk_index = Column(Integer)  # סדר הקטע במסמך המקורי
    embedding = Column(ARRAY(Float), nullable=True)  # וקטור למערכת RAG (OpenAI embedding)
    
    # קשרים
    document = relationship("Document", back_populates="chunks") 