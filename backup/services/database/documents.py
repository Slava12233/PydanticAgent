"""
מודול לניהול מסמכים במסד הנתונים
"""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Document, DocumentChunk
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class DocumentManager:
    """מחלקה לניהול מסמכים"""
    
    @staticmethod
    async def get_all_documents(session: AsyncSession) -> List[Document]:
        """קבלת כל המסמכים במערכת
        
        Args:
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת כל המסמכים
        """
        try:
            result = await session.execute(select(Document))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת כל המסמכים: {str(e)}")
            raise
            
    @staticmethod
    async def get_document_by_id(doc_id: int, session: AsyncSession) -> Optional[Document]:
        """קבלת מסמך לפי מזהה
        
        Args:
            doc_id: מזהה המסמך
            session: סשן של מסד הנתונים
            
        Returns:
            המסמך אם נמצא, None אחרת
        """
        try:
            return await session.get(Document, doc_id)
        except Exception as e:
            logger.error(f"שגיאה בקבלת מסמך {doc_id}: {str(e)}")
            return None
            
    @staticmethod
    async def get_user_documents(user_id: int, session: AsyncSession) -> List[Document]:
        """קבלת כל המסמכים של משתמש מסוים
        
        Args:
            user_id: מזהה המשתמש
            session: סשן של מסד הנתונים
            
        Returns:
            רשימת המסמכים של המשתמש
        """
        try:
            result = await session.execute(
                select(Document).where(Document.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"שגיאה בקבלת מסמכים של משתמש {user_id}: {str(e)}")
            raise
            
    @staticmethod
    async def create_document(
        session: AsyncSession,
        user_id: int,
        title: str,
        content: str,
        doc_type: str,
        metadata: Optional[dict] = None
    ) -> Optional[Document]:
        """יצירת מסמך חדש
        
        Args:
            session: סשן של מסד הנתונים
            user_id: מזהה המשתמש
            title: כותרת המסמך
            content: תוכן המסמך
            doc_type: סוג המסמך
            metadata: מטא-דאטה (אופציונלי)
            
        Returns:
            המסמך שנוצר או None אם נכשל
        """
        try:
            # יצירת המסמך
            new_doc = Document(
                user_id=user_id,
                title=title,
                content=content,
                doc_type=doc_type,
                metadata=metadata or {}
            )
            
            session.add(new_doc)
            await session.commit()
            await session.refresh(new_doc)
            
            logger.info(f"נוצר מסמך חדש: {new_doc.id}")
            return new_doc
            
        except Exception as e:
            logger.error(f"שגיאה ביצירת מסמך חדש: {str(e)}")
            await session.rollback()
            return None
            
    @staticmethod
    async def update_document(
        doc_id: int,
        session: AsyncSession,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[Document]:
        """עדכון מסמך קיים
        
        Args:
            doc_id: מזהה המסמך
            session: סשן של מסד הנתונים
            title: כותרת חדשה (אופציונלי)
            content: תוכן חדש (אופציונלי)
            metadata: מטא-דאטה חדשה (אופציונלי)
            
        Returns:
            המסמך המעודכן או None אם נכשל
        """
        try:
            doc = await DocumentManager.get_document_by_id(doc_id, session)
            if not doc:
                return None
                
            if title is not None:
                doc.title = title
            if content is not None:
                doc.content = content
            if metadata is not None:
                doc.metadata.update(metadata)
                
            await session.commit()
            await session.refresh(doc)
            
            logger.info(f"עודכן מסמך {doc_id}")
            return doc
            
        except Exception as e:
            logger.error(f"שגיאה בעדכון מסמך {doc_id}: {str(e)}")
            await session.rollback()
            return None
            
    @staticmethod
    async def delete_document(doc_id: int, session: AsyncSession) -> bool:
        """מחיקת מסמך
        
        Args:
            doc_id: מזהה המסמך
            session: סשן של מסד הנתונים
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            # מחיקת כל החלקים הקשורים למסמך
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
            )
            
            # מחיקת המסמך עצמו
            doc = await DocumentManager.get_document_by_id(doc_id, session)
            if not doc:
                return False
                
            await session.delete(doc)
            await session.commit()
            
            logger.info(f"נמחק מסמך {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה במחיקת מסמך {doc_id}: {str(e)}")
            await session.rollback()
            return False 