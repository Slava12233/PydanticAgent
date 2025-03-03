"""
בדיקות יחידה למודול error_handler.py

מודול זה מכיל בדיקות יחידה למודול הטיפול בשגיאות ואי-הבנות.
"""
import unittest
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.error_handler import (
    ErrorType,
    handle_misunderstanding,
    handle_api_error,
    generate_clarification_questions,
    suggest_similar_intents,
    get_error_response
)

class AsyncTestCase(unittest.TestCase):
    """מחלקת בסיס לבדיקות אסינכרוניות"""
    
    def run_async(self, coro):
        """מריץ פונקציה אסינכרונית בצורה סינכרונית"""
        return asyncio.run(coro)

class TestErrorHandler(AsyncTestCase):
    """בדיקות יחידה למודול הטיפול בשגיאות"""
    
    def setUp(self):
        """הגדרת משתנים לבדיקות"""
        self.update = MagicMock()
        self.context = MagicMock()
        self.session = MagicMock()
    
    def test_handle_misunderstanding(self):
        """בדיקת טיפול באי-הבנה"""
        # בדיקת טיפול באי-הבנה עם קטגוריה כללית
        response = self.run_async(handle_misunderstanding(
            self.update, self.context, self.session, "מה זה?", "general"
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה הצעות
        self.assertTrue("💡" in response)
        self.assertTrue("הנה כמה הצעות" in response)
        
        # בדיקת טיפול באי-הבנה עם קטגוריית מוצרים
        response = self.run_async(handle_misunderstanding(
            self.update, self.context, self.session, "מוצר", "product_management"
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה הצעות
        self.assertTrue("💡" in response)
        self.assertTrue("הנה כמה הצעות" in response)
    
    def test_handle_api_error(self):
        """בדיקת טיפול בשגיאות API"""
        # בדיקת טיפול בשגיאת API כללית
        error_details = {"message": "שגיאת חיבור"}
        response = self.run_async(handle_api_error(
            self.update, self.context, self.session, error_details
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה את פרטי השגיאה
        self.assertTrue("שגיאת חיבור" in response)
        
        # בדיקת טיפול בשגיאת מכסה
        error_details = {"message": "חריגה ממכסת השימוש"}
        response = self.run_async(handle_api_error(
            self.update, self.context, self.session, error_details, ErrorType.QUOTA_ERROR
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה את פרטי השגיאה
        self.assertTrue("חריגה ממכסת השימוש" in response)
    
    def test_generate_clarification_questions(self):
        """בדיקת יצירת שאלות הבהרה"""
        # בדיקת יצירת שאלות הבהרה למידע חסר
        missing_info = ["product_name", "price"]
        response = self.run_async(generate_clarification_questions(
            self.update, self.context, self.session, "עדכן מוצר", missing_info
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שאלה
        self.assertTrue("❓" in response or "?" in response)
        
        # וידוא שהתשובה מכילה שאלות הבהרה
        self.assertTrue("אני צריך מידע נוסף" in response)
        self.assertTrue("•" in response)
        
        # בדיקת יצירת שאלות הבהרה למידע חסר לא מוכר
        missing_info = ["unknown_field"]
        response = self.run_async(generate_clarification_questions(
            self.update, self.context, self.session, "עדכן מוצר", missing_info
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שאלה
        self.assertTrue("❓" in response or "?" in response)
        
        # וידוא שהתשובה מכילה שאלות הבהרה
        self.assertTrue("אני צריך מידע נוסף" in response)
        self.assertTrue("unknown_field" in response)
    
    def test_suggest_similar_intents(self):
        """בדיקת הצעת כוונות דומות"""
        # בדיקת הצעת כוונות דומות
        similar_intents = [
            ("product_management", "list_products", 80.5),
            ("product_management", "get_product", 60.2)
        ]
        response = self.run_async(suggest_similar_intents(
            self.update, self.context, self.session, "מוצרים", similar_intents
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שאלה
        self.assertTrue("❓" in response or "?" in response)
        
        # וידוא שהתשובה מכילה הצעות לכוונות דומות
        self.assertTrue("לא הצלחתי להבין בדיוק" in response)
        self.assertTrue("הצגת רשימת מוצרים" in response)
        self.assertTrue("הצגת פרטי מוצר" in response)
        self.assertTrue("80%" in response)
        self.assertTrue("60%" in response)
        
        # בדיקת הצעת כוונות דומות עם כוונה לא מוכרת
        similar_intents = [
            ("unknown_task", "unknown_intent", 50.0)
        ]
        response = self.run_async(suggest_similar_intents(
            self.update, self.context, self.session, "לא ידוע", similar_intents
        ))
        
        # וידוא שהתשובה מכילה אימוג'י שאלה
        self.assertTrue("❓" in response or "?" in response)
        
        # וידוא שהתשובה מכילה הודעה מתאימה
        self.assertTrue("לא הצלחתי להבין בדיוק" in response)
    
    def test_get_error_response(self):
        """בדיקת קבלת תשובת שגיאה מוכנה"""
        # בדיקת קבלת תשובת שגיאה מוכנה לסוג שגיאה מוכר
        response = get_error_response(ErrorType.TIMEOUT_ERROR)
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה הודעת שגיאה מתאימה
        self.assertTrue(any(template in response for template in [
            "הבקשה לקחה יותר מדי זמן",
            "הפעולה ארכה זמן רב מדי",
            "חל פסק זמן בעיבוד הבקשה",
            "הבקשה מורכבת מדי ולקחה יותר מדי זמן"
        ]))
        
        # בדיקת קבלת תשובת שגיאה מוכנה לסוג שגיאה לא מוכר
        response = get_error_response("unknown_error_type")
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה הודעת שגיאה כללית
        self.assertTrue(any(template in response for template in [
            "אירעה שגיאה בעיבוד הבקשה",
            "משהו השתבש",
            "אירעה שגיאה לא צפויה",
            "המערכת נתקלה בבעיה"
        ]))
        
        # בדיקת קבלת תשובת שגיאה מוכנה עם פרטי שגיאה
        error_details = {"message": "פרטי שגיאה"}
        response = get_error_response(ErrorType.GENERAL_ERROR, error_details)
        
        # וידוא שהתשובה מכילה אימוג'י שגיאה
        self.assertTrue("❌" in response)
        
        # וידוא שהתשובה מכילה את פרטי השגיאה
        self.assertTrue("פרטי שגיאה" in response)

if __name__ == '__main__':
    unittest.main() 