"""
שירות RAG (Retrieval Augmented Generation) - מאחד את הפונקציונליות של ניהול מסמכים וחיפוש
"""
import os
import sys
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from datetime import datetime

from src.database.database import db
from src.database.file_parsers import FileParser

# הגדרת לוגר
logger = logging.getLogger(__name__)

class RAGService:
    """שירות לניהול מסמכים במערכת RAG"""
    
    def __init__(self):
        """אתחול שירות ה-RAG"""
        # אתחול מסד הנתונים אם צריך
        if db.engine is None:
            db.init_db()
    
    async def add_document_from_file(self, file_path: str, title: Optional[str] = None, 
                                   source: str = "file", metadata: Optional[Dict[str, Any]] = None,
                                   chunk_size: int = 1000) -> int:
        """
        הוספת מסמך למערכת RAG מקובץ
        
        Args:
            file_path: נתיב לקובץ
            title: כותרת המסמך (ברירת מחדל: שם הקובץ)
            source: מקור המסמך (ברירת מחדל: "file")
            metadata: מטא-דאטה נוסף למסמך
            chunk_size: גודל כל קטע בתווים
            
        Returns:
            מזהה המסמך שנוצר
        """
        try:
            # פרסור הקובץ באמצעות המודול החדש
            logger.info(f"מתחיל לפרסר קובץ: {file_path}")
            content, file_metadata = FileParser.parse_file(file_path)
            logger.info(f"פרסור הקובץ הושלם בהצלחה. אורך התוכן: {len(content)} תווים")
            
            # שימוש בשם הקובץ כברירת מחדל לכותרת
            if title is None:
                title = os.path.basename(file_path)
            
            # שילוב המטא-דאטה מהקובץ עם המטא-דאטה שהתקבל
            combined_metadata = file_metadata.copy() if file_metadata else {}
            if metadata:
                combined_metadata.update(metadata)
            
            # הוספת מידע על זמן ההוספה
            combined_metadata["added_at"] = datetime.now().isoformat()
            combined_metadata["source"] = source
            
            # חלוקת התוכן לקטעים
            chunks = self._split_content_to_chunks(content, chunk_size)
            logger.info(f"התוכן חולק ל-{len(chunks)} קטעים")
            
            # יצירת רשומה עבור המסמך
            session = await db.get_session()
            try:
                from src.database.models import Document, DocumentChunk
                
                # יצירת רשומת מסמך
                document = Document(
                    title=title,
                    source=source,
                    content=content,
                    doc_metadata=combined_metadata
                )
                session.add(document)
                await session.flush()  # לקבלת ה-ID של המסמך
                
                # יצירת רשומות עבור הקטעים
                for i, chunk_text in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=chunk_text,
                        chunk_index=i,
                        metadata={"chunk_index": i}
                    )
                    session.add(chunk)
                
                await session.commit()
                logger.info(f"המסמך נשמר בהצלחה. מזהה: {document.id}")
                return document.id
            except Exception as e:
                await session.rollback()
                logger.error(f"שגיאה בהוספת מסמך: {str(e)}")
                raise
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בהוספת מסמך: {str(e)}")
            raise
    
    async def add_document_from_text(self, content: str, title: str, 
                                   source: str = "text", metadata: Optional[Dict[str, Any]] = None,
                                   chunk_size: int = 1000) -> int:
        """
        הוספת מסמך למערכת RAG מטקסט
        
        Args:
            content: תוכן המסמך
            title: כותרת המסמך
            source: מקור המסמך (ברירת מחדל: "text")
            metadata: מטא-דאטה נוסף למסמך
            chunk_size: גודל כל קטע בתווים
            
        Returns:
            מזהה המסמך שנוצר
        """
        try:
            # הוספת מידע על זמן ההוספה
            combined_metadata = metadata.copy() if metadata else {}
            combined_metadata["added_at"] = datetime.now().isoformat()
            combined_metadata["source"] = source
            
            # חלוקת התוכן לקטעים
            chunks = self._split_content_to_chunks(content, chunk_size)
            logger.info(f"התוכן חולק ל-{len(chunks)} קטעים")
            
            # יצירת רשומה עבור המסמך
            session = await db.get_session()
            try:
                from src.database.models import Document, DocumentChunk
                
                # יצירת רשומת מסמך
                document = Document(
                    title=title,
                    source=source,
                    content=content,
                    doc_metadata=combined_metadata
                )
                session.add(document)
                await session.flush()  # לקבלת ה-ID של המסמך
                
                # יצירת רשומות עבור הקטעים
                for i, chunk_text in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=chunk_text,
                        chunk_index=i,
                        metadata={"chunk_index": i}
                    )
                    session.add(chunk)
                
                await session.commit()
                logger.info(f"המסמך נשמר בהצלחה. מזהה: {document.id}")
                return document.id
            except Exception as e:
                await session.rollback()
                logger.error(f"שגיאה בהוספת מסמך: {str(e)}")
                raise
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בהוספת מסמך: {str(e)}")
            raise
    
    async def search_documents(self, query: str, limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        חיפוש במסמכים לפי שאילתה
        
        Args:
            query: שאילתת החיפוש
            limit: מספר התוצאות המקסימלי להחזרה
            min_similarity: סף מינימלי לדמיון (0.0-1.0)
            
        Returns:
            רשימה של תוצאות חיפוש, כל אחת מכילה את תוכן הקטע, כותרת המסמך, ציון הדמיון ומטא-דאטה
        """
        try:
            from sqlalchemy import text
            import numpy as np
            
            # אתחול מסד הנתונים אם צריך
            if db.engine is None:
                db.init_db()
            
            logger.info(f"מחפש מסמכים עם השאילתה: '{query}'")
            
            # קבלת embedding עבור השאילתה
            query_embedding = await self._get_embedding(query)
            
            # ביצוע החיפוש במסד הנתונים - גישה פשוטה יותר
            session = await db.get_session()
            try:
                # שאילתה פשוטה שמחזירה את כל הקטעים
                sql = text("""
                SELECT 
                    dc.id as chunk_id,
                    dc.content,
                    dc.embedding,
                    d.id as document_id,
                    d.title,
                    d.source,
                    d.doc_metadata as document_metadata,
                    dc.chunk_index as chunk_metadata
                FROM 
                    document_chunks dc
                JOIN 
                    documents d ON dc.document_id = d.id
                WHERE 
                    dc.embedding IS NOT NULL
                """)
                
                # ביצוע השאילתה
                result = await session.execute(sql)
                rows = result.fetchall()
                
                logger.info(f"נמצאו {len(rows)} קטעים במסד הנתונים")
                
                # חישוב דמיון קוסינוס בקוד Python
                chunks_with_similarity = []
                for row in rows:
                    # חישוב דמיון קוסינוס בין וקטורים
                    similarity = 0
                    if row.embedding:
                        try:
                            # המרה לנומפיי
                            v1 = np.array(query_embedding)
                            v2 = np.array(row.embedding)
                            
                            # חישוב דמיון קוסינוס
                            dot_product = np.dot(v1, v2)
                            norm_v1 = np.linalg.norm(v1)
                            norm_v2 = np.linalg.norm(v2)
                            
                            similarity = dot_product / (norm_v1 * norm_v2) if norm_v1 * norm_v2 > 0 else 0
                        except Exception as e:
                            logger.warning(f"שגיאה בחישוב דמיון: {str(e)}")
                    
                    # טיפול במטא-דאטה
                    try:
                        if isinstance(row.document_metadata, dict):
                            doc_metadata = row.document_metadata
                        else:
                            doc_metadata = json.loads(row.document_metadata) if row.document_metadata else {}
                        
                        # שימוש ב-chunk_index במקום metadata
                        chunk_metadata = {"index": row.chunk_metadata} if row.chunk_metadata is not None else {}
                    except Exception as e:
                        logger.warning(f"שגיאה בהמרת מטא-דאטה בחיפוש: {str(e)}")
                        doc_metadata = {}
                        chunk_metadata = {}
                    
                    # דילוג על תוצאות מתחת לסף המינימלי
                    if similarity < min_similarity:
                        continue
                    
                    # הוספת התוצאה לרשימה
                    chunks_with_similarity.append({
                        "content": row.content,
                        "document_id": row.document_id,
                        "chunk_id": row.chunk_id,
                        "title": row.title,
                        "similarity": similarity,
                        "similarity_percentage": round(similarity * 100, 2),
                        "source": row.source or doc_metadata.get("source", "לא ידוע"),
                        "document_metadata": doc_metadata,
                        "chunk_metadata": chunk_metadata
                    })
                
                # מיון לפי דמיון והגבלה למספר התוצאות הרצוי
                search_results = sorted(chunks_with_similarity, key=lambda x: x["similarity"], reverse=True)[:limit]
                
                logger.info(f"נמצאו {len(search_results)} תוצאות חיפוש רלוונטיות")
                return search_results
            except Exception as e:
                logger.error(f"שגיאה בחיפוש מסמכים: {str(e)}")
                raise
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בחיפוש מסמכים: {str(e)}")
            raise
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        קבלת רשימת כל המסמכים במערכת
        
        Returns:
            רשימה של מסמכים, כל אחד מכיל את המזהה, הכותרת, המקור והמטא-דאטה
        """
        try:
            # אתחול מסד הנתונים אם צריך
            if db.engine is None:
                db.init_db()
            
            # קבלת רשימת המסמכים ממסד הנתונים
            session = await db.get_session()
            try:
                from src.database.models import Document
                from sqlalchemy import text
                
                # שליפת כל המסמכים
                result = await session.execute(
                    text("SELECT id, title, source, doc_metadata, upload_date FROM documents ORDER BY upload_date DESC")
                )
                
                # עיבוד התוצאות
                documents = []
                for row in result:
                    # טיפול במטא-דאטה - בדיקה אם זה כבר מילון או צריך להמיר מ-JSON
                    try:
                        if isinstance(row.doc_metadata, dict):
                            metadata = row.doc_metadata
                        else:
                            metadata = json.loads(row.doc_metadata) if row.doc_metadata else {}
                    except Exception as e:
                        logger.warning(f"שגיאה בהמרת מטא-דאטה: {str(e)}")
                        metadata = {}
                    
                    # הוספת המסמך לרשימה
                    documents.append({
                        "id": row.id,
                        "title": row.title,
                        "source": row.source,
                        "metadata": metadata,
                        "created_at": row.upload_date.isoformat() if row.upload_date else None
                    })
                
                return documents
            except Exception as e:
                logger.error(f"שגיאה בקבלת רשימת מסמכים: {str(e)}")
                raise
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת רשימת מסמכים: {str(e)}")
            raise
    
    async def delete_document(self, document_id: int) -> bool:
        """
        מחיקת מסמך מהמערכת
        
        Args:
            document_id: מזהה המסמך למחיקה
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            # אתחול מסד הנתונים אם צריך
            if db.engine is None:
                db.init_db()
            
            # מחיקת המסמך ממסד הנתונים
            session = await db.get_session()
            try:
                from src.database.models import Document, DocumentChunk
                from sqlalchemy import text
                
                # מחיקת כל הקטעים של המסמך
                await session.execute(
                    text(f"DELETE FROM document_chunks WHERE document_id = {document_id}")
                )
                
                # מחיקת המסמך עצמו
                await session.execute(
                    text(f"DELETE FROM documents WHERE id = {document_id}")
                )
                
                await session.commit()
                logger.info(f"המסמך נמחק בהצלחה. מזהה: {document_id}")
                return True
            except Exception as e:
                await session.rollback()
                logger.error(f"שגיאה במחיקת מסמך: {str(e)}")
                return False
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה במחיקת מסמך: {str(e)}")
            return False
    
    async def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        קבלת מסמך לפי מזהה
        
        Args:
            document_id: מזהה המסמך
            
        Returns:
            פרטי המסמך או None אם המסמך לא נמצא
        """
        try:
            # אתחול מסד הנתונים אם צריך
            if db.engine is None:
                db.init_db()
            
            # קבלת המסמך ממסד הנתונים
            session = await db.get_session()
            try:
                from src.database.models import Document
                from sqlalchemy import text
                
                # שליפת המסמך
                result = await session.execute(
                    text(f"SELECT id, title, source, doc_metadata, upload_date FROM documents WHERE id = {document_id}")
                )
                
                # בדיקה אם המסמך נמצא
                row = result.fetchone()
                if not row:
                    return None
                
                # טיפול במטא-דאטה - בדיקה אם זה כבר מילון או צריך להמיר מ-JSON
                try:
                    if isinstance(row.doc_metadata, dict):
                        metadata = row.doc_metadata
                    else:
                        metadata = json.loads(row.doc_metadata) if row.doc_metadata else {}
                except Exception as e:
                    logger.warning(f"שגיאה בהמרת מטא-דאטה: {str(e)}")
                    metadata = {}
                
                # קבלת כל הקטעים של המסמך
                chunks_result = await session.execute(
                    text(f"SELECT id, content, chunk_index, metadata FROM document_chunks WHERE document_id = {document_id} ORDER BY chunk_index")
                )
                
                # עיבוד הקטעים
                chunks = []
                for chunk_row in chunks_result:
                    # טיפול במטא-דאטה של הקטע - בדיקה אם זה כבר מילון או צריך להמיר מ-JSON
                    try:
                        if isinstance(chunk_row.metadata, dict):
                            chunk_metadata = chunk_row.metadata
                        else:
                            chunk_metadata = json.loads(chunk_row.metadata) if chunk_row.metadata else {}
                    except Exception as e:
                        logger.warning(f"שגיאה בהמרת מטא-דאטה של קטע: {str(e)}")
                        chunk_metadata = {}
                    
                    # הוספת הקטע לרשימה
                    chunks.append({
                        "id": chunk_row.id,
                        "content": chunk_row.content,
                        "chunk_index": chunk_row.chunk_index,
                        "metadata": chunk_metadata
                    })
                
                # יצירת מילון עם פרטי המסמך
                document = {
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "metadata": metadata,
                    "created_at": row.upload_date.isoformat() if row.upload_date else None,
                    "chunks": chunks,
                    "chunks_count": len(chunks)
                }
                
                return document
            except Exception as e:
                logger.error(f"שגיאה בקבלת מסמך: {str(e)}")
                return None
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת מסמך: {str(e)}")
            return None
    
    def _split_content_to_chunks(self, content: str, chunk_size: int) -> List[str]:
        """
        חלוקת תוכן לקטעים בגודל קבוע
        
        Args:
            content: התוכן לחלוקה
            chunk_size: גודל כל קטע בתווים
            
        Returns:
            רשימה של קטעי טקסט
        """
        # חלוקה לפסקאות
        paragraphs = content.split("\n\n")
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # אם הפסקה ארוכה מגודל הקטע, חלק אותה
            if len(paragraph) > chunk_size:
                # אם יש תוכן בקטע הנוכחי, הוסף אותו לרשימה
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # חלוקת הפסקה הארוכה למשפטים
                sentences = paragraph.split(". ")
                
                for sentence in sentences:
                    # אם המשפט ארוך מגודל הקטע, חלק אותו
                    if len(sentence) > chunk_size:
                        # חלוקה לחלקים שווים
                        for i in range(0, len(sentence), chunk_size):
                            chunks.append(sentence[i:i+chunk_size].strip())
                    else:
                        # אם הקטע הנוכחי + המשפט ארוכים מגודל הקטע, התחל קטע חדש
                        if len(current_chunk) + len(sentence) + 2 > chunk_size:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence + ". "
                        else:
                            current_chunk += sentence + ". "
            else:
                # אם הקטע הנוכחי + הפסקה ארוכים מגודל הקטע, התחל קטע חדש
                if len(current_chunk) + len(paragraph) + 2 > chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
                else:
                    current_chunk += paragraph + "\n\n"
        
        # הוספת הקטע האחרון אם יש בו תוכן
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    async def _get_embedding(self, text: str) -> List[float]:
        """
        קבלת וקטור embedding עבור טקסט
        
        Args:
            text: הטקסט לקבלת embedding
            
        Returns:
            וקטור embedding
        """
        try:
            # הכנת הטקסט - הסרת רווחים מיותרים ונרמול
            text = text.strip().lower()
            
            # הוספת מילות מפתח לשיפור החיפוש
            # אם הטקסט מכיל מילות מפתח מסוימות, נוסיף מילים נרדפות כדי לשפר את החיפוש
            enhanced_text = text
            
            # שיפור חיפוש לפרויקטים ספציפיים
            if "nexthemes" in text or "נקסט" in text or "תימס" in text:
                enhanced_text += " nexthemes next themes נקסט תימס פרויקט נקסטתימס"
            
            if "נובה" in text or "nova" in text:
                enhanced_text += " nova נובה פרויקט מצגת hebrew nova theme presentation"
            
            # שימוש בטקסט המשופר לקבלת embedding
            from openai import AsyncOpenAI
            
            # יצירת מופע של הלקוח
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # קבלת embedding
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=enhanced_text,
                encoding_format="float"
            )
            
            # החזרת הוקטור
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"שגיאה בקבלת embedding: {str(e)}")
            # החזרת וקטור אפסים במקרה של שגיאה
            return [0.0] * 1536  # גודל וקטור ברירת מחדל של OpenAI

# יצירת מופע יחיד של השירות (Singleton)
rag_service = RAGService()

# פונקציות עוטפות לנוחות השימוש
async def add_document_from_file(file_path: str, title: str = None, source: str = None, metadata: Dict = None) -> str:
    """
    הוספת מסמך מקובץ למאגר
    
    Args:
        file_path: נתיב לקובץ
        title: כותרת המסמך (אופציונלי)
        source: מקור המסמך (אופציונלי)
        metadata: מטא-דאטה נוספת (אופציונלי)
        
    Returns:
        מזהה המסמך שנוצר
    """
    return await rag_service.add_document_from_file(file_path, title, source, metadata)

async def add_document_from_text(text: str, title: str, source: str = None, metadata: Dict = None) -> str:
    """
    הוספת מסמך מטקסט למאגר
    
    Args:
        text: תוכן המסמך
        title: כותרת המסמך
        source: מקור המסמך (אופציונלי)
        metadata: מטא-דאטה נוספת (אופציונלי)
        
    Returns:
        מזהה המסמך שנוצר
    """
    return await rag_service.add_document_from_text(text, title, source, metadata)

async def search_documents(query: str, limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
    """
    חיפוש במסמכים לפי שאילתה
    
    Args:
        query: שאילתת החיפוש
        limit: מספר התוצאות המקסימלי להחזרה
        min_similarity: סף מינימלי לדמיון (0.0-1.0)
        
    Returns:
        רשימה של תוצאות חיפוש, כל אחת מכילה את תוכן הקטע, כותרת המסמך, ציון הדמיון ומטא-דאטה
    """
    return await rag_service.search_documents(query, limit, min_similarity)

async def list_documents() -> List[Dict[str, Any]]:
    """
    קבלת רשימת כל המסמכים במערכת
    
    Returns:
        רשימה של מסמכים, כל אחד מכיל את המזהה, הכותרת, המקור והמטא-דאטה
    """
    return await rag_service.list_documents()

async def delete_document(document_id: str) -> bool:
    """
    מחיקת מסמך מהמאגר
    
    Args:
        document_id: מזהה המסמך למחיקה
        
    Returns:
        האם המחיקה הצליחה
    """
    return await rag_service.delete_document(document_id)

async def get_document_by_id(document_id: str) -> Dict[str, Any]:
    """
    קבלת מסמך לפי מזהה
    
    Args:
        document_id: מזהה המסמך
        
    Returns:
        מילון המכיל את פרטי המסמך
    """
    return await rag_service.get_document_by_id(document_id) 