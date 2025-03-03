"""
בדיקות יחידה למודול response_generator.py

מודול זה מכיל בדיקות יחידה למחולל התשובות הטבעיות.
"""
import unittest
import re
import sys
import os

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.managers.response_generator import (
    ResponseGenerator,
    generate_natural_response,
    get_emoji,
    format_with_emojis
)

class TestResponseGenerator(unittest.TestCase):
    """בדיקות יחידה למחולל התשובות"""
    
    def setUp(self):
        """הגדרת משתנים לבדיקות"""
        self.response_generator = ResponseGenerator()
    
    def test_generate_natural_response_product_query(self):
        """בדיקת יצירת תשובה לשאילתת מוצרים"""
        # בדיקת תשובה לחיפוש מוצרים
        data = {"products": "מוצר 1, מוצר 2, מוצר 3"}
        response = generate_natural_response("product_query", "search", data)
        
        # וידוא שהתשובה מכילה את המוצרים
        self.assertIn("מוצר 1", response)
        self.assertIn("מוצר 2", response)
        self.assertIn("מוצר 3", response)
        
        # וידוא שהתשובה מכילה אימוג'י מתאים
        self.assertTrue(any(emoji in response[:2] for emoji in ["🛍️"]))
    
    def test_generate_natural_response_order_query(self):
        """בדיקת יצירת תשובה לשאילתת הזמנות"""
        # בדיקת תשובה להצגת הזמנה
        data = {"order_id": "12345", "order_details": "פרטי ההזמנה כאן"}
        response = generate_natural_response("order_query", "get", data)
        
        # וידוא שהתשובה מכילה את מספר ההזמנה והפרטים
        self.assertIn("12345", response)
        self.assertIn("פרטי ההזמנה כאן", response)
        
        # וידוא שהתשובה מכילה אימוג'י מתאים
        self.assertTrue(any(emoji in response[:2] for emoji in ["📦"]))
    
    def test_generate_natural_response_action_success(self):
        """בדיקת יצירת תשובה לפעולה מוצלחת"""
        # בדיקת תשובה ליצירת מוצר
        data = {"entity_type": "מוצר", "entity_name": "חולצה כחולה"}
        response = generate_natural_response("action", "create_success", data)
        
        # וידוא שהתשובה מכילה את סוג הישות ושם הישות
        self.assertIn("מוצר", response)
        self.assertIn("חולצה כחולה", response)
        
        # וידוא שהתשובה מכילה אימוג'י מתאים
        self.assertTrue(any(emoji in response[:2] for emoji in ["✅", "➕"]))
    
    def test_generate_natural_response_action_failed(self):
        """בדיקת יצירת תשובה לפעולה שנכשלה"""
        # בדיקת תשובה לפעולה שנכשלה
        data = {"entity_type": "מוצר", "entity_name": "חולצה כחולה", "reason": "המוצר כבר קיים"}
        response = generate_natural_response("action", "action_failed", data)
        
        # וידוא שהתשובה מכילה את סוג הישות, שם הישות והסיבה
        self.assertIn("מוצר", response)
        self.assertIn("חולצה כחולה", response)
        self.assertIn("המוצר כבר קיים", response)
        
        # וידוא שהתשובה מכילה אימוג'י מתאים
        self.assertTrue(any(emoji in response[:2] for emoji in ["❌"]))
    
    def test_generate_natural_response_general(self):
        """בדיקת יצירת תשובה כללית"""
        # בדיקת תשובת ברכה
        response = generate_natural_response("general", "greeting", {})
        
        # וידוא שהתשובה מכילה מילות ברכה
        self.assertTrue(any(word in response for word in ["שלום", "היי", "ברוך"]))
        
        # וידוא שהתשובה מכילה אימוג'י מתאים
        self.assertTrue(any(emoji in response[:2] for emoji in ["👋"]))
    
    def test_generate_natural_response_with_missing_data(self):
        """בדיקת יצירת תשובה עם נתונים חסרים"""
        # בדיקת תשובה עם נתונים חסרים
        data = {"product_name": "חולצה כחולה"}  # חסר product_details
        response = generate_natural_response("product_query", "get", data)
        
        # וידוא שהתשובה מכילה את שם המוצר
        self.assertIn("חולצה כחולה", response)
        
        # וידוא שהתשובה מכילה ערך ברירת מחדל או הודעת שגיאה
        self.assertTrue(
            "פרטי המוצר" in response or 
            "חסר מידע" in response or 
            "שגיאה" in response
        )
    
    def test_generate_natural_response_with_unknown_intent(self):
        """בדיקת יצירת תשובה עם כוונה לא מוכרת"""
        # בדיקת תשובה עם כוונה לא מוכרת
        response = generate_natural_response("unknown_intent", "unknown_subtype", {})
        
        # וידוא שהתשובה היא תשובת ברירת מחדל
        # בדיקה שהתשובה מכילה אחד מהביטויים המצופים בתשובת ברירת מחדל
        fallback_phrases = [
            "לא בטוח שהבנתי",
            "לא הצלחתי להבין",
            "מתקשה להבין",
            "לא הצלחתי לפענח",
            "לא הבנתי",
            "אפשר לנסות שוב"
        ]
        
        # בדיקה שלפחות אחד מהביטויים נמצא בתשובה
        self.assertTrue(
            any(phrase in response for phrase in fallback_phrases),
            f"התשובה '{response}' אינה מכילה אף אחד מהביטויים המצופים בתשובת ברירת מחדל"
        )
    
    def test_add_suggestions(self):
        """בדיקת הוספת הצעות לפעולות נוספות"""
        # בדיקת הוספת הצעות לאחר חיפוש מוצרים
        data = {"products": "מוצר 1, מוצר 2, מוצר 3"}
        response = generate_natural_response("product_query", "search", data)
        
        # וידוא שהתשובה מכילה הצעות
        self.assertTrue("💡" in response)
    
    def test_get_emoji(self):
        """בדיקת פונקציית get_emoji"""
        # בדיקת אימוג'ים שונים
        self.assertEqual(get_emoji("product"), "🛍️")
        self.assertEqual(get_emoji("order"), "📦")
        self.assertEqual(get_emoji("customer"), "👤")
        self.assertEqual(get_emoji("success"), "✅")
        self.assertEqual(get_emoji("error"), "❌")
        
        # בדיקת אימוג'י לא קיים
        self.assertEqual(get_emoji("non_existent"), "")
    
    def test_format_with_emojis(self):
        """בדיקת פונקציית format_with_emojis"""
        # בדיקת הוספת אימוג'י למוצר
        text = "חולצה כחולה"
        formatted_text = format_with_emojis(text, ["product"])
        self.assertEqual(formatted_text, "🛍️ חולצה כחולה")
        
        # בדיקת הוספת אימוג'י להזמנה
        text = "הזמנה מספר 12345"
        formatted_text = format_with_emojis(text, ["order"])
        self.assertEqual(formatted_text, "📦 הזמנה מספר 12345")
        
        # בדיקה ללא סוגי ישויות
        text = "טקסט רגיל"
        formatted_text = format_with_emojis(text)
        self.assertEqual(formatted_text, "טקסט רגיל")
        
        # בדיקה עם סוג ישות לא קיים
        text = "טקסט רגיל"
        formatted_text = format_with_emojis(text, ["non_existent"])
        self.assertEqual(formatted_text, "טקסט רגיל")
    
    def test_response_variability(self):
        """בדיקת גיוון בתשובות"""
        # יצירת מספר תשובות לאותה שאילתה
        data = {"products": "מוצר 1, מוצר 2, מוצר 3"}
        responses = set()
        
        # יצירת 10 תשובות ובדיקה שיש לפחות 2 תשובות שונות
        for _ in range(10):
            response = generate_natural_response("product_query", "search", data)
            # הסרת אימוג'ים והצעות לפעולות נוספות לצורך השוואה פשוטה יותר
            clean_response = re.sub(r'[\U00010000-\U0010ffff]', '', response)
            clean_response = re.sub(r'💡.*', '', clean_response, flags=re.DOTALL)
            responses.add(clean_response.strip())
        
        # וידוא שיש לפחות 2 תשובות שונות
        self.assertGreaterEqual(len(responses), 2)

if __name__ == '__main__':
    unittest.main() 