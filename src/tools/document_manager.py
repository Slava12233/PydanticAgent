"""
כלי לניהול מסמכים במערכת RAG (Retrieval Augmented Generation)
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
from src.database.rag_utils import add_document_from_file, search_documents

class DocumentManager:
    """כלי לניהול מסמכים במערכת RAG"""
    
    def __init__(self):
        """אתחול מנהל המסמכים"""
        # אתחול מסד הנתונים אם צריך
        if db.engine is None:
            db.init_db()
    
    async def add_text_document(self, title: str, file_path: str, source: str = "file", 
                               metadata: Dict[str, Any] = None) -> int:
        """
        הוספת מסמך טקסט למערכת RAG
        
        Args:
            title: כותרת המסמך
            file_path: נתיב לקובץ הטקסט
            source: מקור המסמך (ברירת מחדל: "file")
            metadata: מטא-דאטה נוסף למסמך
            
        Returns:
            מזהה המסמך שנוצר
        """
        doc_id = await add_document_from_file(
            file_path=file_path,
            title=title,
            source=source,
            metadata=metadata
        )
        
        print(f"נוסף מסמך חדש למערכת RAG. מזהה: {doc_id}, כותרת: {title}")
        return doc_id
    
    async def add_text_content(self, title: str, content: str, source: str = "manual", 
                              metadata: Dict[str, Any] = None) -> int:
        """
        הוספת תוכן טקסט ישירות למערכת RAG
        
        Args:
            title: כותרת המסמך
            content: תוכן הטקסט
            source: מקור המסמך (ברירת מחדל: "manual")
            metadata: מטא-דאטה נוסף למסמך
            
        Returns:
            מזהה המסמך שנוצר
        """
        # הוספת מידע על זמן ההוספה למטא-דאטה
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'added_at': datetime.utcnow().isoformat(),
            'source_type': 'direct_input'
        })
        
        # הוספת המסמך למערכת RAG
        doc_id = await db.add_document(
            title=title,
            content=content,
            source=source,
            metadata=metadata
        )
        
        print(f"נוסף מסמך חדש למערכת RAG. מזהה: {doc_id}, כותרת: {title}")
        return doc_id
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        חיפוש במסמכים לפי שאילתה
        
        Args:
            query: שאילתת החיפוש
            limit: מספר התוצאות המקסימלי להחזרה
            
        Returns:
            רשימת קטעים רלוונטיים עם מידע על המסמך המקורי
        """
        results = await search_documents(query, limit)
        
        # הדפסת תוצאות החיפוש
        print(f"\nתוצאות חיפוש עבור: '{query}'")
        print("-" * 50)
        
        for i, chunk in enumerate(results, 1):
            print(f"{i}. {chunk['title']} (התאמה: {chunk['similarity']:.4f})")
            print(f"   מקור: {chunk['source']}")
            print(f"   תוכן: {chunk['content'][:150]}...")
            print()
        
        return results
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        רשימת כל המסמכים במערכת RAG
        
        Returns:
            רשימת מסמכים
        """
        # שליפת כל המסמכים ממסד הנתונים
        with db.Session() as session:
            from src.database.models import Document
            documents = session.query(Document).all()
            
            # המרה לרשימת מילונים
            docs_list = []
            for doc in documents:
                docs_list.append({
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "upload_date": doc.upload_date.isoformat(),
                    "metadata": doc.metadata
                })
        
        # הדפסת רשימת המסמכים
        print("רשימת מסמכים במערכת RAG:")
        print("-" * 50)
        
        for i, doc in enumerate(docs_list, 1):
            print(f"{i}. {doc['title']} (מזהה: {doc['id']})")
            print(f"   מקור: {doc['source']}")
            print(f"   תאריך העלאה: {doc['upload_date']}")
            print()
        
        return docs_list
    
    async def delete_document(self, doc_id: int) -> bool:
        """
        מחיקת מסמך ממערכת RAG
        
        Args:
            doc_id: מזהה המסמך למחיקה
            
        Returns:
            האם המחיקה הצליחה
        """
        try:
            with db.Session() as session:
                from src.database.models import Document, DocumentChunk
                
                # מחיקת כל הקטעים של המסמך
                session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
                
                # מחיקת המסמך עצמו
                result = session.query(Document).filter(Document.id == doc_id).delete()
                
                session.commit()
                
                if result:
                    print(f"מסמך עם מזהה {doc_id} נמחק בהצלחה.")
                    return True
                else:
                    print(f"לא נמצא מסמך עם מזהה {doc_id}.")
                    return False
                
        except Exception as e:
            print(f"שגיאה במחיקת מסמך: {e}")
            return False

async def main():
    """פונקציה ראשית"""
    parser = argparse.ArgumentParser(description='כלי לניהול מסמכים במערכת RAG')
    subparsers = parser.add_subparsers(dest='command', help='פקודה לביצוע')
    
    # פקודה להוספת מסמך מקובץ
    add_parser = subparsers.add_parser('add', help='הוספת מסמך מקובץ למערכת RAG')
    add_parser.add_argument('file', help='נתיב לקובץ טקסט להוספה')
    add_parser.add_argument('--title', help='כותרת המסמך (ברירת מחדל: שם הקובץ)')
    add_parser.add_argument('--source', default='file', help='מקור המסמך (ברירת מחדל: file)')
    add_parser.add_argument('--metadata', help='מטא-דאטה בפורמט JSON')
    
    # פקודה להוספת תוכן טקסט ישירות
    add_content_parser = subparsers.add_parser('add-content', help='הוספת תוכן טקסט ישירות למערכת RAG')
    add_content_parser.add_argument('title', help='כותרת המסמך')
    add_content_parser.add_argument('content', help='תוכן הטקסט או נתיב לקובץ עם התוכן')
    add_content_parser.add_argument('--source', default='manual', help='מקור המסמך (ברירת מחדל: manual)')
    add_content_parser.add_argument('--from-file', action='store_true', help='האם לקרוא את התוכן מקובץ')
    add_content_parser.add_argument('--metadata', help='מטא-דאטה בפורמט JSON')
    
    # פקודה לחיפוש במסמכים
    search_parser = subparsers.add_parser('search', help='חיפוש במסמכים')
    search_parser.add_argument('query', help='שאילתת החיפוש')
    search_parser.add_argument('--limit', type=int, default=5, help='מספר התוצאות המקסימלי')
    
    # פקודה להצגת רשימת מסמכים
    list_parser = subparsers.add_parser('list', help='הצגת רשימת מסמכים')
    
    # פקודה למחיקת מסמך
    delete_parser = subparsers.add_parser('delete', help='מחיקת מסמך')
    delete_parser.add_argument('doc_id', type=int, help='מזהה המסמך למחיקה')
    
    args = parser.parse_args()
    
    # אתחול מנהל המסמכים
    manager = DocumentManager()
    
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
        await manager.add_text_document(
            title=args.title or os.path.basename(args.file),
            file_path=args.file,
            source=args.source,
            metadata=metadata
        )
    
    elif args.command == 'add-content':
        # המרת מטא-דאטה מ-JSON אם סופק
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("שגיאה: המטא-דאטה אינו בפורמט JSON תקין")
                return 1
        
        # קריאת התוכן מקובץ אם צריך
        content = args.content
        if args.from_file:
            try:
                with open(args.content, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"שגיאה בקריאת הקובץ: {e}")
                return 1
        
        # הוספת התוכן
        await manager.add_text_content(
            title=args.title,
            content=content,
            source=args.source,
            metadata=metadata
        )
    
    elif args.command == 'search':
        # חיפוש במסמכים
        await manager.search(args.query, args.limit)
    
    elif args.command == 'list':
        # הצגת רשימת מסמכים
        await manager.list_documents()
    
    elif args.command == 'delete':
        # מחיקת מסמך
        await manager.delete_document(args.doc_id)
    
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    # הפעלת הפונקציה הראשית באופן אסינכרוני
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 