"""
מודול לניהול מסמכים במסד הנתונים
"""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.documents import Document, DocumentChunk
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
            return []
            
    @staticmethod
    async def create_document(
        session: AsyncSession,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        source: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Optional[Document]:
        """יצירת מסמך חדש
        
        Args:
            session: סשן של מסד הנתונים
            user_id: מזהה המשתמש
            title: כותרת המסמך
            description: תיאור המסמך
            source: מקור המסמך
            content_type: סוג התוכן של המסמך
            
        Returns:
            המסמך שנוצר, None אם נכשל
        """
        try:
            # יצירת מסמך חדש
            document = Document(
                user_id=user_id,
                title=title,
                description=description,
                source=source,
                content_type=content_type
            )
            
            session.add(document)
            await session.commit()
            await session.refresh(document)
            
            logger.info(f"נוצר מסמך חדש: {document.id} (משתמש: {user_id})")
            return document
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת מסמך: {str(e)}")
            return None
            
    @staticmethod
    async def add_chunk(
        session: AsyncSession,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding=None,
        chunk_metadata=None
    ) -> Optional[DocumentChunk]:
        """הוספת חלק למסמך
        
        Args:
            session: סשן של מסד הנתונים
            document_id: מזהה המסמך
            chunk_index: אינדקס החלק
            content: תוכן החלק
            embedding: וקטור המייצג את החלק
            chunk_metadata: מטא-דאטה של החלק
            
        Returns:
            החלק שנוצר, None אם נכשל
        """
        try:
            # יצירת חלק חדש
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                content=content,
                embedding=embedding,
                chunk_metadata=chunk_metadata or {}
            )
            
            session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
            
            logger.info(f"נוצר חלק חדש: {chunk.id} (מסמך: {document_id}, אינדקס: {chunk_index})")
            return chunk
            
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה ביצירת חלק: {str(e)}")
            return None
            
    @staticmethod
    async def delete_document(doc_id: int, session: AsyncSession) -> bool:
        """מחיקת מסמך
        
        Args:
            doc_id: מזהה המסמך
            session: סשן של מסד הנתונים
            
        Returns:
            True אם המחיקה הצליחה, False אחרת
        """
        try:
            # מחיקת כל החלקים של המסמך
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
            )
            
            # מחיקת המסמך עצמו
            result = await session.execute(
                delete(Document).where(Document.id == doc_id)
            )
            
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"נמחק מסמך: {doc_id}")
                return True
            else:
                logger.warning(f"לא נמצא מסמך למחיקה: {doc_id}")
                return False
                
        except Exception as e:
            await session.rollback()
            logger.error(f"שגיאה במחיקת מסמך {doc_id}: {str(e)}")
            return False 