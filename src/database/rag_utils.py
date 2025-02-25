"""
כלים לעבודה עם מערכת RAG (Retrieval Augmented Generation)
"""
import os
import sys
import asyncio
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime
import json

# הוספת תיקיית הפרויקט לנתיב החיפוש
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.database import db

async def add_document_from_file(file_path: str, title: Optional[str] = None, 
                               source: str = "file", metadata: Optional[Dict[str, Any]] = None,
                               chunk_size: int = 1000) -> int:
    """
    הוספת מסמך למערכת RAG מקובץ טקסט
    
    Args:
        file_path: נתיב לקובץ הטקסט
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
    
    # קריאת תוכן הקובץ
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # שימוש בשם הקובץ כברירת מחדל לכותרת
    if title is None:
        title = os.path.basename(file_path)
    
    # הוספת מידע על הקובץ למטא-דאטה
    file_metadata = {
        'filename': os.path.basename(file_path),
        'path': os.path.abspath(file_path),
        'size_bytes': os.path.getsize(file_path),
        'added_at': datetime.utcnow().isoformat()
    }
    
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
    
    return doc_id

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

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלים לעבודה עם מערכת RAG')
    subparsers = parser.add_subparsers(dest='command', help='פקודה לביצוע')
    
    # פקודה להוספת מסמך
    add_parser = subparsers.add_parser('add', help='הוספת מסמך למערכת RAG')
    add_parser.add_argument('file', help='נתיב לקובץ טקסט להוספה')
    add_parser.add_argument('--title', help='כותרת המסמך (ברירת מחדל: שם הקובץ)')
    add_parser.add_argument('--source', default='file', help='מקור המסמך (ברירת מחדל: file)')
    add_parser.add_argument('--metadata', help='מטא-דאטה בפורמט JSON')
    add_parser.add_argument('--chunk-size', type=int, default=1000, help='גודל כל קטע בתווים')
    
    # פקודה לחיפוש במסמכים
    search_parser = subparsers.add_parser('search', help='חיפוש במסמכים')
    search_parser.add_argument('query', help='שאילתת החיפוש')
    search_parser.add_argument('--limit', type=int, default=5, help='מספר התוצאות המקסימלי')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        # המרת מטא-דאטה מ-JSON אם סופק
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("שגיאה: המטא-דאטה אינו בפורמט JSON תקין")
                return 1
        
        # הוספת המסמך
        doc_id = await add_document_from_file(
            file_path=args.file,
            title=args.title,
            source=args.source,
            metadata=metadata
        )
        
        print(f"המסמך נוסף בהצלחה! מזהה: {doc_id}")
        
    elif args.command == 'search':
        # חיפוש במסמכים
        results = await search_documents(args.query, args.limit)
        
        print(f"נמצאו {len(results)} תוצאות עבור '{args.query}':")
        for i, result in enumerate(results, 1):
            print(f"\n--- תוצאה {i} (התאמה: {result['similarity']:.2f}) ---")
            print(f"מסמך: {result['title']} (מקור: {result['source']})")
            print(f"תוכן: {result['content'][:200]}...")
    
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == '__main__':
    # הפעלת הפונקציה הראשית באופן אסינכרוני
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 