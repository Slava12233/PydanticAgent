"""
בדיקות אינטגרציה למערכת RAG
"""
import os
import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path

# ייבוא המודולים לבדיקה
from src.database.rag_utils import add_document_from_file, search_documents
from src.database.database import db

class TestRAGIntegration(unittest.TestCase):
    """בדיקות אינטגרציה למערכת RAG"""
    
    @classmethod
    def setUpClass(cls):
        """הכנה לפני כל הבדיקות"""
        # אתחול מסד הנתונים
        if db.engine is None:
            db.init_db()
        
        # יצירת תיקייה זמנית לקבצי בדיקה
        cls.test_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        """ניקוי אחרי כל הבדיקות"""
        # מחיקת התיקייה הזמנית
        shutil.rmtree(cls.test_dir)
    
    def create_text_file(self, content, filename="test.txt"):
        """יצירת קובץ טקסט לבדיקה"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_add_and_search_document(self):
        """בדיקת הוספת מסמך וחיפוש בו"""
        # יצירת קובץ טקסט לבדיקה
        content = """
        זהו מסמך בדיקה למערכת RAG.
        המסמך מכיל מידע על מערכת הבדיקות.
        ניתן לחפש מידע במסמך זה.
        המערכת תומכת במגוון סוגי קבצים כולל PDF, Word, Excel ועוד.
        """
        file_path = self.create_text_file(content, "test_rag.txt")
        
        # הפעלת הפונקציות באופן אסינכרוני
        async def run_test():
            # הוספת המסמך
            doc_id = await add_document_from_file(
                file_path=file_path,
                title="מסמך בדיקה",
                source="test",
                metadata={"test": True, "user_id": 12345}
            )
            
            # וידוא שהמסמך נוסף בהצלחה
            self.assertIsNotNone(doc_id)
            
            # חיפוש במסמך
            results = await search_documents("מערכת בדיקות", limit=5)
            
            # בדיקות על תוצאות החיפוש
            self.assertTrue(len(results) > 0)
            self.assertIn("מערכת", results[0]["content"])
            self.assertIn("מסמך בדיקה", results[0]["title"])
            
            return doc_id
        
        # הרצת הבדיקה האסינכרונית
        doc_id = asyncio.run(run_test())
        
        # ניקוי - מחיקת המסמך מהמסד נתונים
        with db.Session() as session:
            from src.database.models import Document, DocumentChunk
            # מחיקת הקטעים
            session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
            # מחיקת המסמך
            session.query(Document).filter(Document.id == doc_id).delete()
            session.commit()

# בדיקות נוספות למערכת הטלגרם 