"""
מודלים הקשורים למסמכים
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.models.base import Base

class Document(Base):
    """מודל לשמירת מסמכים"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # קשרים
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    """מודל לשמירת חלקי מסמכים"""
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # שינוי מ-Vector ל-ARRAY של Float
    embedding = Column(ARRAY(Float), nullable=True)  # שימוש זמני ב-ARRAY(Float) במקום Vector
    chunk_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # קשרים
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('ix_document_chunks_doc_id_chunk_idx', 'document_id', 'chunk_index'),
    ) 