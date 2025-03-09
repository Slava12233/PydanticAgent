"""
מודול RAG Core - מכיל את המחלקה הבסיסית ופונקציות הליבה של מערכת ה-RAG
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain.docstore.document import Document

from src.core.config import OPENAI_API_KEY, DATABASE_URL
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class RAGCore:
    """מחלקת הבסיס למערכת ה-RAG"""
    
    def __init__(self):
        """אתחול מערכת ה-RAG"""
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    async def initialize(self) -> None:
        """אתחול המערכת"""
        try:
            self.vectorstore = PGVector(
                connection_string=DATABASE_URL,
                embedding_function=self.embeddings,
                collection_name="documents"
            )
            logger.info("RAG Core initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Core: {str(e)}")
            raise
            
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """הוספת מסמך למאגר
        
        Args:
            content: תוכן המסמך
            metadata: מטא-דאטה נוספת למסמך
            
        Returns:
            מזהה המסמך
        """
        try:
            if metadata is None:
                metadata = {}
                
            # הוספת מטא-דאטה בסיסית
            metadata.update({
                "timestamp": datetime.utcnow().isoformat(),
                "source": "user_upload"
            })
            
            # פיצול המסמך לחלקים
            chunks = self.text_splitter.split_text(content)
            
            # יצירת מסמכים עם מטא-דאטה
            documents = [
                Document(
                    page_content=chunk,
                    metadata=metadata
                ) for chunk in chunks
            ]
            
            # הוספה למאגר הווקטורי
            ids = self.vectorstore.add_documents(documents)
            
            logger.info(f"Added document with {len(chunks)} chunks")
            return ids[0]  # מחזיר את המזהה של החלק הראשון
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise
            
    async def delete_document(self, doc_id: str) -> bool:
        """מחיקת מסמך מהמאגר
        
        Args:
            doc_id: מזהה המסמך למחיקה
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            self.vectorstore.delete([doc_id])
            logger.info(f"Deleted document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False
            
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """קבלת מסמך לפי מזהה
        
        Args:
            doc_id: מזהה המסמך
            
        Returns:
            המסמך אם נמצא, None אחרת
        """
        try:
            doc = self.vectorstore.get(doc_id)
            return doc
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {str(e)}")
            return None
            
    async def update_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """עדכון מסמך קיים
        
        Args:
            doc_id: מזהה המסמך לעדכון
            content: התוכן החדש
            metadata: מטא-דאטה חדשה (אופציונלי)
            
        Returns:
            האם העדכון הצליח
        """
        try:
            # מחיקת המסמך הישן
            if not await self.delete_document(doc_id):
                return False
                
            # הוספת המסמך החדש
            await self.add_document(content, metadata)
            logger.info(f"Updated document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {str(e)}")
            return False 