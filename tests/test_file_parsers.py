"""
בדיקות למודול file_parsers
"""
import os
import unittest
import tempfile
import shutil
from pathlib import Path

# ייבוא המודול לבדיקה
from src.database.file_parsers import FileParser

class TestFileParsers(unittest.TestCase):
    """בדיקות לפרסור קבצים מסוגים שונים"""
    
    def setUp(self):
        """הכנה לפני כל בדיקה"""
        # יצירת תיקייה זמנית לקבצי בדיקה
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """ניקוי אחרי כל בדיקה"""
        # מחיקת התיקייה הזמנית
        shutil.rmtree(self.test_dir)
    
    def create_text_file(self, content, filename="test.txt"):
        """יצירת קובץ טקסט לבדיקה"""
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_parse_text_file(self):
        """בדיקת פרסור קובץ טקסט פשוט"""
        content = "זוהי בדיקה\nשל קובץ טקסט פשוט\nעם מספר שורות."
        file_path = self.create_text_file(content)
        
        # הפעלת הפרסר
        text, metadata = FileParser.parse_text(file_path, {'filename': 'test.txt'})
        
        # בדיקות
        self.assertEqual(text, content)
        self.assertEqual(metadata['line_count'], 3)
        self.assertEqual(metadata['char_count'], len(content))
    
    def test_parse_file_txt(self):
        """בדיקת הפונקציה הראשית עם קובץ טקסט"""
        content = "תוכן לבדיקה"
        file_path = self.create_text_file(content)
        
        # הפעלת הפונקציה הראשית
        text, metadata = FileParser.parse_file(file_path)
        
        # בדיקות
        self.assertEqual(text, content)
        self.assertEqual(metadata['file_extension'], '.txt')
        self.assertIn('line_count', metadata)
    
    def test_parse_file_unsupported(self):
        """בדיקת התנהגות עם סוג קובץ לא נתמך"""
        # יצירת קובץ עם סיומת לא נתמכת
        file_path = self.create_text_file("תוכן כלשהו", "test.xyz")
        
        # בדיקה שהפונקציה מנסה לפרסר כטקסט
        text, metadata = FileParser.parse_file(file_path)
        self.assertEqual(metadata['file_extension'], '.xyz')
        self.assertEqual(text, "תוכן כלשהו")
    
    def test_parse_file_with_unicode(self):
        """בדיקת פרסור קובץ עם תווים מיוחדים"""
        content = "טקסט בעברית עם תווים מיוחדים: ®©™€£¥§¶±"
        file_path = self.create_text_file(content)
        
        # הפעלת הפרסר
        text, metadata = FileParser.parse_file(file_path)
        
        # בדיקות
        self.assertEqual(text, content)
        self.assertEqual(metadata['file_extension'], '.txt')
        self.assertIn('line_count', metadata)
        self.assertEqual(metadata['char_count'], len(content))
    