"""
מודול RAG Utils - מכיל פונקציות עזר למערכת ה-RAG
"""

from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
import json
import hashlib
import re

from langchain.docstore.document import Document

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_document_id(content: str, metadata: Dict[str, Any]) -> str:
    """יצירת מזהה ייחודי למסמך
    
    Args:
        content: תוכן המסמך
        metadata: מטא-דאטה של המסמך
        
    Returns:
        מזהה ייחודי
    """
    # יצירת מחרוזת מהתוכן והמטא-דאטה
    content_str = content
    metadata_str = json.dumps(metadata, sort_keys=True)
    combined = f"{content_str}{metadata_str}"
    
    # יצירת hash
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
def clean_text(text: str) -> str:
    """ניקוי טקסט מתווים מיוחדים
    
    Args:
        text: הטקסט לניקוי
        
    Returns:
        הטקסט המנוקה
    """
    # הסרת תווים מיוחדים
    text = re.sub(r'[^\w\s\u0590-\u05FF]', ' ', text)
    
    # הסרת רווחים מיותרים
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
    
def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """חילוץ מילות מפתח מטקסט
    
    Args:
        text: הטקסט לניתוח
        min_length: אורך מינימלי למילה
        
    Returns:
        רשימת מילות המפתח
    """
    # ניקוי הטקסט
    text = clean_text(text)
    
    # פיצול למילים
    words = text.split()
    
    # סינון מילים קצרות
    keywords = [word for word in words if len(word) >= min_length]
    
    return list(set(keywords))
    
def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 100
) -> List[str]:
    """פיצול טקסט לחלקים
    
    Args:
        text: הטקסט לפיצול
        chunk_size: גודל כל חלק
        overlap: כמות החפיפה בין חלקים
        min_chunk_size: גודל מינימלי לחלק
        
    Returns:
        רשימת החלקים
    """
    # ניקוי הטקסט
    text = clean_text(text)
    
    # פיצול לפסקאות
    paragraphs = text.split('\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # אם הפסקה גדולה מדי, מפצלים אותה
        if para_size > chunk_size:
            words = para.split()
            current_para = []
            current_para_size = 0
            
            for word in words:
                word_size = len(word) + 1  # +1 for space
                if current_para_size + word_size > chunk_size:
                    chunks.append(' '.join(current_para))
                    current_para = []
                    current_para_size = 0
                
                current_para.append(word)
                current_para_size += word_size
                
            if current_para:
                chunks.append(' '.join(current_para))
                
        # אם הפסקה מתאימה לחלק הנוכחי
        elif current_size + para_size <= chunk_size:
            current_chunk.append(para)
            current_size += para_size
            
        # אם צריך ליצור חלק חדש
        else:
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
    
    # הוספת החלק האחרון
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    # הוספת חפיפה
    final_chunks = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            # הוספת טקסט מהחלק הקודם
            prev_chunk = chunks[i-1]
            overlap_text = prev_chunk[-overlap:]
            chunk = overlap_text + chunk
        
        if i < len(chunks) - 1:
            # הוספת טקסט מהחלק הבא
            next_chunk = chunks[i+1]
            overlap_text = next_chunk[:overlap]
            chunk = chunk + overlap_text
            
        final_chunks.append(chunk)
    
    # סינון חלקים קטנים מדי
    return [chunk for chunk in final_chunks if len(chunk) >= min_chunk_size]
    
def merge_metadata(
    base: Dict[str, Any],
    updates: Dict[str, Any],
    merge_lists: bool = True
) -> Dict[str, Any]:
    """מיזוג מטא-דאטה
    
    Args:
        base: המטא-דאטה הבסיסית
        updates: העדכונים למיזוג
        merge_lists: האם למזג רשימות
        
    Returns:
        המטא-דאטה הממוזגת
    """
    result = base.copy()
    
    for key, value in updates.items():
        # אם המפתח לא קיים, מוסיפים אותו
        if key not in result:
            result[key] = value
            continue
            
        # אם שני הערכים הם רשימות
        if merge_lists and isinstance(value, list) and isinstance(result[key], list):
            result[key] = list(set(result[key] + value))
            
        # אם שני הערכים הם מילונים
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = merge_metadata(result[key], value, merge_lists)
            
        # אחרת, מחליפים את הערך
        else:
            result[key] = value
    
    return result 