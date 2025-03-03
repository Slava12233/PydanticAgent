"""
בדיקות למודול learning_manager

קובץ זה מכיל בדיקות יחידה למודול learning_manager שאחראי על תיעוד אינטראקציות,
זיהוי אינטראקציות בעייתיות, ויצירת דוחות תקופתיים.
"""
import unittest
import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# הוספת תיקיית הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.managers.learning_manager import LearningManager

class TestLearningManager(unittest.TestCase):
    """בדיקות למודול learning_manager"""
    
    def setUp(self):
        """הגדרת סביבת הבדיקה"""
        # יצירת תיקיית זמנית לבדיקות
        self.test_dir = tempfile.mkdtemp()
        
        # שינוי הנתיב של קובץ מסד הנתונים לתיקייה הזמנית
        self.original_learning_db = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'learning.db')))
        self.test_db_path = Path(self.test_dir) / "test_learning.db"
        
        # יצירת מופע של מנהל הלמידה לבדיקות
        self.learning_manager = LearningManager()
        
        # שינוי הנתיב של מסד הנתונים למסד נתונים זמני
        self.learning_manager.LEARNING_DB = self.test_db_path
        
        # אתחול מסד הנתונים
        self.learning_manager._init_db()
    
    def tearDown(self):
        """ניקוי לאחר הבדיקה"""
        # מחיקת התיקייה הזמנית
        shutil.rmtree(self.test_dir)
    
    def test_init_db(self):
        """בדיקת אתחול מסד הנתונים"""
        # וידוא שמסד הנתונים נוצר
        self.assertTrue(self.test_db_path.exists())
        
        # בדיקה שהטבלאות נוצרו
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        # בדיקת טבלת אינטראקציות
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")
        self.assertIsNotNone(cursor.fetchone())
        
        # בדיקת טבלת הצעות מילות מפתח
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keyword_suggestions'")
        self.assertIsNotNone(cursor.fetchone())
        
        # בדיקת טבלת דוחות
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_log_interaction(self):
        """בדיקת תיעוד אינטראקציה"""
        # תיעוד אינטראקציה
        user_id = 123456
        message = "מה המוצר הכי נמכר?"
        intent_type = "product_query"
        confidence = 0.85
        response = "המוצר הכי נמכר הוא חולצת כותנה בצבע כחול."
        
        interaction_id = self.learning_manager.log_interaction(
            user_id=user_id,
            message=message,
            intent_type=intent_type,
            confidence=confidence,
            response=response
        )
        
        # בדיקה שהאינטראקציה נשמרה במסד הנתונים
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM interactions WHERE id = ?", (interaction_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], user_id)
        self.assertEqual(result[2], message)
        self.assertEqual(result[3], intent_type)
        self.assertEqual(result[4], confidence)
        self.assertEqual(result[5], response)
        self.assertEqual(result[7], 1)  # success = True
        
        conn.close()
        
        # בדיקה שהאינטראקציה נשמרה ברשימה המקומית
        self.assertEqual(len(self.learning_manager.interactions), 1)
        self.assertEqual(self.learning_manager.interactions[0]["user_id"], user_id)
        self.assertEqual(self.learning_manager.interactions[0]["message"], message)
        self.assertEqual(self.learning_manager.interactions[0]["intent_type"], intent_type)
        self.assertEqual(self.learning_manager.interactions[0]["confidence"], confidence)
        self.assertEqual(self.learning_manager.interactions[0]["response"], response)
        self.assertEqual(self.learning_manager.interactions[0]["success"], True)
    
    def test_analyze_successful_interaction(self):
        """בדיקת ניתוח אינטראקציה מוצלחת"""
        # יצירת אינטראקציה מוצלחת
        interaction = {
            "id": 1,
            "user_id": 123456,
            "message": "תעדכן את המחיר של חולצת כותנה ל-99 ש\"ח",
            "intent_type": "update_product",
            "confidence": 0.95,
            "response": "המחיר של חולצת כותנה עודכן ל-99 ש\"ח",
            "timestamp": datetime.now(),
            "success": True
        }
        
        # ניתוח האינטראקציה
        self.learning_manager._analyze_successful_interaction(interaction)
        
        # בדיקה שנוצרו הצעות מילות מפתח
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM keyword_suggestions WHERE intent_type = ?", ("update_product",))
        count = cursor.fetchone()[0]
        
        self.assertGreater(count, 0)
        
        # בדיקה שנוצרו הצעות מילות מפתח ספציפיות
        cursor.execute("SELECT * FROM keyword_suggestions WHERE keyword LIKE ?", ("%תעדכן את המחיר%",))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "update_product")
        
        conn.close()
    
    def test_identify_problematic_interactions(self):
        """בדיקת זיהוי אינטראקציות בעייתיות"""
        # תיעוד אינטראקציה בעייתית
        user_id = 123456
        message = "מה המוצר הכי נמכר?"
        intent_type = "product_query"
        confidence = 0.5  # נמוך מהסף
        response = "לא הצלחתי להבין את השאלה."
        
        self.learning_manager.log_interaction(
            user_id=user_id,
            message=message,
            intent_type=intent_type,
            confidence=confidence,
            response=response,
            success=False
        )
        
        # זיהוי אינטראקציות בעייתיות
        problematic = self.learning_manager.identify_problematic_interactions()
        
        # בדיקה שהאינטראקציה זוהתה כבעייתית
        self.assertEqual(len(problematic), 1)
        self.assertEqual(problematic[0]["user_id"], user_id)
        self.assertEqual(problematic[0]["message"], message)
        self.assertEqual(problematic[0]["intent_type"], intent_type)
        self.assertEqual(problematic[0]["confidence"], confidence)
        self.assertEqual(problematic[0]["success"], 0)
    
    def test_generate_periodic_report(self):
        """בדיקת יצירת דוח תקופתי"""
        # תיעוד כמה אינטראקציות
        self.learning_manager.log_interaction(
            user_id=123456,
            message="מה המוצר הכי נמכר?",
            intent_type="product_query",
            confidence=0.85,
            response="המוצר הכי נמכר הוא חולצת כותנה בצבע כחול."
        )
        
        self.learning_manager.log_interaction(
            user_id=123456,
            message="תעדכן את המחיר של חולצת כותנה ל-99 ש\"ח",
            intent_type="update_product",
            confidence=0.95,
            response="המחיר של חולצת כותנה עודכן ל-99 ש\"ח"
        )
        
        self.learning_manager.log_interaction(
            user_id=123456,
            message="מה המחיר של חולצת כותנה?",
            intent_type="product_query",
            confidence=0.9,
            response="המחיר של חולצת כותנה הוא 99 ש\"ח"
        )
        
        # יצירת דוח
        report = self.learning_manager.generate_periodic_report()
        
        # בדיקת תוכן הדוח
        self.assertIn("title", report)
        self.assertIn("statistics", report)
        self.assertIn("intent_distribution", report)
        
        # בדיקת הסטטיסטיקות
        stats = report["statistics"]
        self.assertEqual(stats["total_interactions"], 3)
        self.assertEqual(stats["successful_interactions"], 3)
        self.assertEqual(stats["problematic_interactions"], 0)
        
        # בדיקת התפלגות הכוונות
        intent_dist = report["intent_distribution"]
        self.assertEqual(len(intent_dist), 2)  # product_query, update_product
        
        # בדיקה שהדוח נשמר במסד הנתונים
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reports")
        count = cursor.fetchone()[0]
        
        self.assertEqual(count, 1)
        
        conn.close()
    
    def test_update_keywords_automatically(self):
        """בדיקת עדכון אוטומטי של מילות מפתח"""
        # יצירת כמה הצעות מילות מפתח
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # הוספת כמה הצעות מילות מפתח
        cursor.execute('''
        INSERT INTO keyword_suggestions 
        (intent_type, keyword, score, source_message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', ("update_product", "עדכן את המחיר", 0.6, "תעדכן את המחיר של חולצת כותנה", now))
        
        cursor.execute('''
        INSERT INTO keyword_suggestions 
        (intent_type, keyword, score, source_message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', ("update_product", "שנה מחיר", 0.4, "תשנה את המחיר של חולצת כותנה", now))
        
        cursor.execute('''
        INSERT INTO keyword_suggestions 
        (intent_type, keyword, score, source_message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', ("product_query", "מה המחיר של", 0.7, "מה המחיר של חולצת כותנה?", now))
        
        conn.commit()
        conn.close()
        
        # עדכון מילות מפתח
        new_keywords = self.learning_manager.update_keywords_automatically(min_score=0.5)
        
        # בדיקת התוצאה
        self.assertIn("update_product", new_keywords)
        self.assertIn("product_query", new_keywords)
        
        self.assertIn("עדכן את המחיר", new_keywords["update_product"])
        self.assertIn("מה המחיר של", new_keywords["product_query"])
        
        # בדיקה שמילות מפתח עם ציון נמוך לא נכללו
        self.assertNotIn("שנה מחיר", new_keywords["update_product"])
    
    def test_get_learning_statistics(self):
        """בדיקת קבלת סטטיסטיקות למידה"""
        # תיעוד כמה אינטראקציות
        self.learning_manager.log_interaction(
            user_id=123456,
            message="מה המוצר הכי נמכר?",
            intent_type="product_query",
            confidence=0.85,
            response="המוצר הכי נמכר הוא חולצת כותנה בצבע כחול."
        )
        
        self.learning_manager.log_interaction(
            user_id=123456,
            message="לא הבנתי את התשובה",
            intent_type="unknown",
            confidence=0.3,
            response="אני מצטער, אנסה להסביר טוב יותר.",
            success=False
        )
        
        # יצירת כמה הצעות מילות מפתח
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO keyword_suggestions 
        (intent_type, keyword, score, source_message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', ("product_query", "מה המוצר הכי", 0.5, "מה המוצר הכי נמכר?", now))
        
        conn.commit()
        conn.close()
        
        # יצירת דוח
        self.learning_manager.generate_periodic_report()
        
        # קבלת סטטיסטיקות
        stats = self.learning_manager.get_learning_statistics()
        
        # בדיקת הסטטיסטיקות
        self.assertEqual(stats["total_interactions"], 2)
        self.assertEqual(stats["successful_interactions"], 1)
        self.assertEqual(stats["failed_interactions"], 1)
        self.assertEqual(stats["total_keyword_suggestions"], 1)
        self.assertEqual(stats["total_reports"], 1)

if __name__ == '__main__':
    unittest.main() 