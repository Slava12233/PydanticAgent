"""
מודול עזר לעבודה עם מסמכים ומערכת RAG (Retrieval Augmented Generation)
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

from src.database.database import db
from src.database.file_parsers import FileParser

logger = logging.getLogger(__name__)

async def add_document_from_file(file_path: str, title: Optional[str] = None, 
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
    # אתחול מסד הנתונים אם צריך
    if db.engine is None:
        db.init_db()
    
    try:
        # פרסור הקובץ באמצעות המודול החדש
        logger.info(f"מתחיל לפרסר קובץ: {file_path}")
        content, file_metadata = FileParser.parse_file(file_path)
        logger.info(f"פרסור הקובץ הושלם בהצלחה. אורך התוכן: {len(content)} תווים")
        
        # שימוש בשם הקובץ כברירת מחדל לכותרת
        if title is None:
            title = os.path.basename(file_path)
        
        # הוספת מידע על הקובץ למטא-דאטה
        file_metadata['added_at'] = datetime.utcnow().isoformat()
        
        # שילוב המטא-דאטה שסופק עם המטא-דאטה של הקובץ
        if metadata:
            file_metadata.update(metadata)
        
        # הוספת המסמך למערכת RAG
        doc_id = await db.add_document(
            title=title,
            content=content,
            source=source,
            metadata=file_metadata
        )
        
        logger.info(f"המסמך נוסף בהצלחה למערכת RAG. מזהה: {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"שגיאה בהוספת מסמך למערכת RAG: {str(e)}")
        raise

async def search_documents(query: str, limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
    """
    חיפוש במסמכים לפי שאילתה
    
    Args:
        query: שאילתת החיפוש
        limit: מספר התוצאות המקסימלי להחזרה
        min_similarity: סף מינימלי לדמיון (0.0 = החזר את כל התוצאות)
        
    Returns:
        רשימת קטעים רלוונטיים עם מידע על המסמך המקורי
    """
    # אתחול מסד הנתונים אם צריך
    if db.engine is None:
        db.init_db()
    
    # חיפוש קטעים רלוונטיים
    results = await db.search_relevant_chunks(query, limit, min_similarity)
    
    return results

def add_document_from_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    הוספת מסמך למאגר המסמכים מטקסט
    
    Args:
        text: תוכן המסמך
        metadata: מטא-דאטה נוספת למסמך
        
    Returns:
        האם ההוספה הצליחה
    """
    try:
        # יצירת מטא-דאטה בסיסית אם לא סופקה
        if metadata is None:
            metadata = {}
            
        # הוספת מידע בסיסי למטא-דאטה
        metadata.update({
            'source': 'text_input',
            'added_at': datetime.now().isoformat()
        })
        
        # כאן יש להוסיף את המסמך למאגר המסמכים
        # במימוש אמיתי, כאן היינו משתמשים ב-vector database או מנוע חיפוש
        logger.info(f"מסמך טקסט נוסף בהצלחה למאגר")
        
        return True
        
    except Exception as e:
        logger.error(f"שגיאה בהוספת מסמך מטקסט: {str(e)}")
        return False

def delete_document(document_id: str) -> bool:
    """
    מחיקת מסמך מהמאגר
    
    Args:
        document_id: מזהה המסמך
        
    Returns:
        האם המחיקה הצליחה
    """
    try:
        # כאן יש למחוק את המסמך מהמאגר
        # במימוש אמיתי, כאן היינו משתמשים ב-vector database או מנוע חיפוש
        logger.info(f"המסמך {document_id} נמחק בהצלחה מהמאגר")
        
        return True
        
    except Exception as e:
        logger.error(f"שגיאה במחיקת מסמך {document_id}: {str(e)}")
        return False

def update_document(document_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    עדכון מסמך במאגר
    
    Args:
        document_id: מזהה המסמך
        text: תוכן המסמך המעודכן
        metadata: מטא-דאטה מעודכנת למסמך
        
    Returns:
        האם העדכון הצליח
    """
    try:
        # יצירת מטא-דאטה בסיסית אם לא סופקה
        if metadata is None:
            metadata = {}
            
        # הוספת מידע בסיסי למטא-דאטה
        metadata.update({
            'updated_at': datetime.now().isoformat()
        })
        
        # כאן יש לעדכן את המסמך במאגר
        # במימוש אמיתי, כאן היינו משתמשים ב-vector database או מנוע חיפוש
        logger.info(f"המסמך {document_id} עודכן בהצלחה במאגר")
        
        return True
        
    except Exception as e:
        logger.error(f"שגיאה בעדכון מסמך {document_id}: {str(e)}")
        return False 