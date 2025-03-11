"""
מודול RAG Document - מכיל את פונקציות ניהול המסמכים במערכת ה-RAG
"""

from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
import json

from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma

from src.utils.logger import setup_logger
from .rag_core import RAGCore

logger = setup_logger(__name__)

class RAGDocument(RAGCore):
    """מחלקה לניהול מסמכים במערכת ה-RAG"""
    
    async def create_document(
        self,
        content: Union[str, Dict[str, Any]],
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """יצירת מסמך חדש
        
        Args:
            content: תוכן המסמך (טקסט או JSON)
            doc_type: סוג המסמך
            metadata: מטא-דאטה נוספת
            tags: תגיות למסמך
            
        Returns:
            מזהה המסמך
        """
        try:
            if metadata is None:
                metadata = {}
            if tags is None:
                tags = []
                
            # המרת תוכן ל-JSON אם צריך
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
                
            # הוספת מטא-דאטה בסיסית
            metadata.update({
                "doc_type": doc_type,
                "tags": tags,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": 1
            })
            
            # הוספת המסמך
            doc_id = await self.add_document(content, metadata)
            logger.info(f"Created new document of type {doc_type} with ID {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            raise
            
    async def update_document_metadata(
        self,
        doc_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """עדכון מטא-דאטה של מסמך
        
        Args:
            doc_id: מזהה המסמך
            metadata_updates: המטא-דאטה לעדכון
            
        Returns:
            האם העדכון הצליח
        """
        try:
            # קבלת המסמך הנוכחי
            doc = await self.get_document(doc_id)
            if doc is None:
                return False
                
            # עדכון המטא-דאטה
            new_metadata = doc.metadata.copy()
            new_metadata.update(metadata_updates)
            new_metadata["updated_at"] = datetime.utcnow().isoformat()
            new_metadata["version"] += 1
            
            # עדכון המסמך
            success = await self.update_document(
                doc_id,
                doc.page_content,
                new_metadata
            )
            
            if success:
                logger.info(f"Updated metadata for document {doc_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update document metadata: {str(e)}")
            return False
            
    async def add_tags(self, doc_id: str, tags: List[str]) -> bool:
        """הוספת תגיות למסמך
        
        Args:
            doc_id: מזהה המסמך
            tags: התגיות להוספה
            
        Returns:
            האם ההוספה הצליחה
        """
        try:
            # קבלת המסמך הנוכחי
            doc = await self.get_document(doc_id)
            if doc is None:
                return False
                
            # הוספת התגיות
            current_tags = set(doc.metadata.get("tags", []))
            current_tags.update(tags)
            
            # עדכון המטא-דאטה
            return await self.update_document_metadata(doc_id, {
                "tags": list(current_tags)
            })
            
        except Exception as e:
            logger.error(f"Failed to add tags to document {doc_id}: {str(e)}")
            return False
            
    async def remove_tags(self, doc_id: str, tags: List[str]) -> bool:
        """הסרת תגיות ממסמך
        
        Args:
            doc_id: מזהה המסמך
            tags: התגיות להסרה
            
        Returns:
            האם ההסרה הצליחה
        """
        try:
            # קבלת המסמך הנוכחי
            doc = await self.get_document(doc_id)
            if doc is None:
                return False
                
            # הסרת התגיות
            current_tags = set(doc.metadata.get("tags", []))
            current_tags.difference_update(tags)
            
            # עדכון המטא-דאטה
            return await self.update_document_metadata(doc_id, {
                "tags": list(current_tags)
            })
            
        except Exception as e:
            logger.error(f"Failed to remove tags from document {doc_id}: {str(e)}")
            return False
            
    async def get_document_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """קבלת היסטוריית השינויים של מסמך
        
        Args:
            doc_id: מזהה המסמך
            
        Returns:
            רשימת השינויים
        """
        try:
            # קבלת המסמך הנוכחי
            doc = await self.get_document(doc_id)
            if doc is None:
                return []
                
            # החזרת ההיסטוריה מהמטא-דאטה
            history = doc.metadata.get("history", [])
            history.append({
                "version": doc.metadata.get("version", 1),
                "updated_at": doc.metadata.get("updated_at"),
                "metadata": doc.metadata
            })
            
            return sorted(history, key=lambda x: x["version"])
            
        except Exception as e:
            logger.error(f"Failed to get document history for {doc_id}: {str(e)}")
            return [] 