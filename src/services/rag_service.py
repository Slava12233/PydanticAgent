"""
שירות RAG (Retrieval Augmented Generation) - מאחד את הפונקציונליות של ניהול מסמכים וחיפוש
"""
import os
import sys
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import db
from src.database.file_parsers import FileParser
from src.database.models import Document, DocumentChunk
from src.database.database import Database

# הגדרת לוגר
logger = logging.getLogger(__name__)

class RAGService:
    """שירות לניהול מסמכים וחיפוש סמנטי"""
    
    def __init__(self):
        """אתחול השירות"""
        self.db = Database()
        self.db.init_db()
    
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
            async with self.db.AsyncSession() as session:
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
            logger.error(f"שגיאה בהוספת מסמך: {str(e)}")
            raise
    
    async def add_document_from_text(
        self,
        content: str,
        title: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[int]:
        """הוספת מסמך חדש מטקסט"""
        try:
            # בדיקה שהמסמך לא ריק
            if not content.strip() or not title.strip() or not source.strip():
                logger.warning("לא ניתן להוסיף מסמך ריק")
                return None
            
            # יצירת מטא-דאטה בסיסי
            doc_metadata = {
                "source": source,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # חלוקת התוכן לקטעים
            chunks = self._split_content_to_chunks(content, chunk_size=100)
            
            async with self.db.AsyncSession() as session:
                # יצירת מסמך חדש
                document = Document(
                    title=title,
                    source=source,
                    content=content,
                    doc_metadata=doc_metadata
                )
                session.add(document)
                await session.flush()  # לקבלת ה-ID של המסמך
                
                # יצירת קטעים
                for i, chunk_text in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=document.id,
                        content=chunk_text,
                        chunk_index=i,
                        chunk_metadata={"chunk_index": i}
                    )
                    session.add(chunk)
                
                await session.commit()
                
                logger.info(f"מסמך חדש נוסף: {document.id}")
                return document.id
                
        except Exception as e:
            logger.error(f"שגיאה בהוספת מסמך: {e}")
            return None
    
    async def search_documents(self, query: str, limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """חיפוש מסמכים לפי שאילתה"""
        try:
            async with self.db.AsyncSession() as session:
                # חיפוש מסמכים שמכילים את מילות החיפוש
                query_words = query.lower().split()
                
                # מילון מילים דומות
                semantic_words = {
                    "מזג": ["אוויר", "טמפרטורה", "חם", "קר", "שמש", "גשם"],
                    "אוויר": ["מזג", "טמפרטורה", "חם", "קר", "שמש", "גשם"],
                    "טמפרטורה": ["מזג", "אוויר", "חם", "קר"],
                    "חם": ["מזג", "אוויר", "טמפרטורה", "שמש"],
                    "קר": ["מזג", "אוויר", "טמפרטורה"],
                    "שמש": ["מזג", "אוויר", "חם"],
                    "גשם": ["מזג", "אוויר"],
                    "מה": ["איך", "איפה", "מתי", "כמה"],
                    "היום": ["עכשיו", "כרגע", "השבוע", "החודש"],
                    "תחזית": ["מזג", "אוויר", "טמפרטורה", "חם", "קר", "שמש", "גשם"]
                }
                
                # יצירת תנאי חיפוש מורכב
                conditions = []
                for word in query_words:
                    # הוספת תנאי חיפוש למילה עצמה
                    word_condition = Document.content.ilike(f"%{word}%") | Document.title.ilike(f"%{word}%")
                    
                    # הוספת תנאי חיפוש למילים דומות
                    if word in semantic_words:
                        for related_word in semantic_words[word]:
                            word_condition = word_condition | Document.content.ilike(f"%{related_word}%") | Document.title.ilike(f"%{related_word}%")
                    
                    conditions.append(word_condition)
                
                # חיפוש מסמכים שמכילים לפחות מילה אחת מהשאילתה או מילה דומה
                stmt = select(Document).where(
                    conditions[0] if len(conditions) == 1 else conditions[0] | conditions[1]
                )
                
                result = await session.execute(stmt)
                documents = result.scalars().all()
                
                # מיון התוצאות לפי רלוונטיות
                results = []
                for doc in documents:
                    # חישוב דמיון פשוט - כמה מילות חיפוש נמצאות במסמך
                    content_words = doc.content.lower().split()
                    title_words = doc.title.lower().split()
                    
                    # חישוב דמיון מילולי
                    word_matches = sum(1 for word in query_words if word in content_words or word in title_words)
                    word_similarity = word_matches / len(query_words) if query_words else 0.0
                    
                    # חישוב דמיון סמנטי פשוט - האם יש מילים דומות
                    semantic_matches = 0
                    for word in query_words:
                        if word in semantic_words:
                            semantic_matches += sum(1 for related_word in semantic_words[word]
                                                if related_word in content_words or related_word in title_words)
                        else:
                            # אם המילה לא במילון הסמנטי, נחפש אותה כמו שהיא
                            if word in content_words or word in title_words:
                                semantic_matches += 1
                    
                    semantic_similarity = semantic_matches / (len(query_words) * 3) if query_words else 0.0
                    
                    # חישוב דמיון כולל
                    similarity = max(word_similarity, semantic_similarity)
                    
                    if similarity >= min_similarity:
                        results.append({
                            "id": doc.id,
                            "title": doc.title,
                            "content": doc.content,
                            "source": doc.source,
                            "document_metadata": doc.doc_metadata,
                            "similarity": similarity
                        })
                
                # מיון לפי דמיון
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
                
        except Exception as e:
            logger.error(f"שגיאה בחיפוש מסמכים: {e}")
            return []
    
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
            async with db.get_session() as session:
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
    
    async def delete_document(self, doc_id: int) -> bool:
        """מחיקת מסמך לפי ID"""
        try:
            async with self.db.AsyncSession() as session:
                document = await session.get(Document, doc_id)
                if document:
                    # מחיקת כל הקטעים של המסמך
                    await session.execute(
                        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
                    )
                    # מחיקת המסמך עצמו
                    await session.delete(document)
                    await session.commit()
                    logger.info(f"מסמך {doc_id} נמחק בהצלחה")
                    return True
                logger.warning(f"מסמך {doc_id} לא נמצא")
                return False
        except Exception as e:
            logger.error(f"שגיאה במחיקת מסמך: {e}")
            return False

    async def delete_all_documents(self) -> bool:
        """מחיקת כל המסמכים מהדאטהבייס"""
        try:
            async with self.db.AsyncSession() as session:
                # מחיקת כל הקטעים
                await session.execute(delete(DocumentChunk))
                # מחיקת כל המסמכים
                await session.execute(delete(Document))
                await session.commit()
                logger.info("כל המסמכים נמחקו בהצלחה")
                return True
        except Exception as e:
            logger.error(f"שגיאה במחיקת כל המסמכים: {e}")
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
            async with self.db.AsyncSession() as session:
                # שליפת המסמך
                document = await session.get(Document, document_id)
                if not document:
                    return None
                
                # שליפת הקטעים של המסמך
                stmt = select(DocumentChunk).where(
                    DocumentChunk.document_id == document_id
                ).order_by(DocumentChunk.chunk_index)
                
                result = await session.execute(stmt)
                chunks = result.scalars().all()
                
                # המרת הקטעים למילונים
                chunks_data = []
                for chunk in chunks:
                    chunks_data.append({
                        "id": chunk.id,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "metadata": chunk.chunk_metadata
                    })
                
                # יצירת מילון עם פרטי המסמך
                return {
                    "id": document.id,
                    "title": document.title,
                    "content": document.content,
                    "source": document.source,
                    "metadata": document.doc_metadata,
                    "created_at": document.upload_date.isoformat() if document.upload_date else None,
                    "chunks": chunks_data,
                    "chunks_count": len(chunks_data)
                }
                
        except Exception as e:
            logger.error(f"שגיאה בקבלת מסמך: {e}")
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
        # הסרת רווחים מיותרים מהתחלה ומהסוף
        content = content.strip()
        
        # אם התוכן קצר מגודל הקטע, להחזיר אותו כקטע אחד
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        # חלוקה לקטעים בגודל קבוע
        for i in range(0, len(content), chunk_size):
            # חיפוש נקודת סיום טבעית (סוף משפט או פסקה)
            end = min(i + chunk_size, len(content))
            
            # אם לא הגענו לסוף הטקסט, לחפש נקודת סיום טבעית
            if end < len(content):
                # חיפוש סוף פסקה
                paragraph_end = content.rfind('\n\n', i, end)
                if paragraph_end > i:
                    end = paragraph_end
                else:
                    # חיפוש סוף משפט
                    sentence_end = content.rfind('. ', i, end)
                    if sentence_end > i:
                        end = sentence_end + 2  # כולל את הנקודה והרווח
            
            # הוספת הקטע לרשימה
            chunk = content[i:end].strip()
            if chunk:  # רק אם הקטע לא ריק
                chunks.append(chunk)
        
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

    async def update_document(
        self,
        doc_id: int,
        content: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """עדכון מסמך קיים"""
        try:
            async with self.db.AsyncSession() as session:
                document = await session.get(Document, doc_id)
                if not document:
                    logger.warning(f"מסמך {doc_id} לא נמצא")
                    return False
                
                if content is not None:
                    document.content = content
                    # עדכון הקטעים
                    chunks = self._split_content_to_chunks(content, chunk_size=100)
                    
                    # מחיקת הקטעים הישנים
                    await session.execute(
                        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
                    )
                    
                    # יצירת קטעים חדשים
                    for i, chunk_text in enumerate(chunks):
                        chunk = DocumentChunk(
                            document_id=doc_id,
                            content=chunk_text,
                            chunk_index=i,
                            chunk_metadata={"chunk_index": i}
                        )
                        session.add(chunk)
                
                if title is not None:
                    document.title = title
                
                if metadata is not None:
                    # עדכון המטא-דאטה הקיים
                    if document.doc_metadata is None:
                        document.doc_metadata = {}
                    document.doc_metadata = {**document.doc_metadata, **metadata}  # שימוש ב-dictionary unpacking
                
                await session.commit()
                logger.info(f"מסמך {doc_id} עודכן בהצלחה")
                return True
        except Exception as e:
            logger.error(f"שגיאה בעדכון מסמך: {e}")
            return False

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

async def update_document(
    doc_id: int,
    content: Optional[str] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    עדכון מסמך קיים
    
    Args:
        doc_id: מזהה המסמך
        content: תוכן חדש (אופציונלי)
        title: כותרת חדשה (אופציונלי)
        metadata: מטא-דאטה חדשה (אופציונלי)
        
    Returns:
        האם העדכון הצליח
    """
    return await rag_service.update_document(doc_id, content, title, metadata) 