"""
בדיקות יחידה למודול ניהול הקשר
"""
import unittest
from datetime import datetime, timedelta

from src.tools.managers.context_manager import (
    ConversationContext,
    understand_context,
    resolve_pronouns,
    extract_context_from_history
)

class TestConversationContext(unittest.TestCase):
    """בדיקות למחלקת ConversationContext"""
    
    def setUp(self):
        """הכנה לפני כל בדיקה"""
        self.context = ConversationContext()
    
    def test_init(self):
        """בדיקת אתחול המחלקה"""
        self.assertEqual(len(self.context.entities["products"]), 0)
        self.assertEqual(len(self.context.entities["orders"]), 0)
        self.assertEqual(len(self.context.entities["customers"]), 0)
        self.assertIsNone(self.context.last_mentioned["product"])
        self.assertIsNone(self.context.last_mentioned["order"])
        self.assertIsNone(self.context.last_mentioned["customer"])
        self.assertEqual(len(self.context.intent_history), 0)
    
    def test_update_context(self):
        """בדיקת עדכון הקשר"""
        # עדכון הקשר עם מוצר
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        # בדיקה שהמוצר נוסף לרשימת המוצרים
        self.assertEqual(len(self.context.entities["products"]), 1)
        self.assertEqual(self.context.entities["products"][0], "חולצה כחולה")
        
        # בדיקה שהמוצר נשמר כמוצר האחרון שהוזכר
        self.assertEqual(self.context.last_mentioned["product"], "חולצה כחולה")
        
        # בדיקה שהכוונה נוספה להיסטוריה
        self.assertEqual(len(self.context.intent_history), 1)
        self.assertEqual(self.context.intent_history[0]["intent"], "update_product")
        
        # עדכון הקשר עם הזמנה
        self.context.update_context(
            "תבדוק את הסטטוס של הזמנה 12345",
            "get_order",
            {"order_id": "12345"}
        )
        
        # בדיקה שההזמנה נוספה לרשימת ההזמנות
        self.assertEqual(len(self.context.entities["orders"]), 1)
        self.assertEqual(self.context.entities["orders"][0], "12345")
        
        # בדיקה שההזמנה נשמרה כהזמנה האחרונה שהוזכרה
        self.assertEqual(self.context.last_mentioned["order"], "12345")
        
        # בדיקה שהכוונה נוספה להיסטוריה
        self.assertEqual(len(self.context.intent_history), 2)
        self.assertEqual(self.context.intent_history[1]["intent"], "get_order")
    
    def test_get_last_entity(self):
        """בדיקת קבלת הישות האחרונה"""
        # עדכון הקשר עם מוצר
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        # בדיקה שאפשר לקבל את המוצר האחרון
        self.assertEqual(self.context.get_last_entity("product"), "חולצה כחולה")
        
        # בדיקה שאין הזמנה אחרונה
        self.assertIsNone(self.context.get_last_entity("order"))
    
    def test_get_entities_by_type(self):
        """בדיקת קבלת ישויות לפי סוג"""
        # עדכון הקשר עם כמה מוצרים
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        self.context.update_context(
            "תעדכן את המחיר של מכנסיים שחורים ל-149 ש\"ח",
            "update_product",
            {"product_name": "מכנסיים שחורים", "price": 149}
        )
        
        # בדיקה שאפשר לקבל את כל המוצרים
        products = self.context.get_entities_by_type("product")
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0], "מכנסיים שחורים")  # המוצר האחרון בהתחלה
        self.assertEqual(products[1], "חולצה כחולה")
    
    def test_get_last_intent(self):
        """בדיקת קבלת הכוונה האחרונה"""
        # עדכון הקשר עם כמה כוונות
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        self.context.update_context(
            "תבדוק את הסטטוס של הזמנה 12345",
            "get_order",
            {"order_id": "12345"}
        )
        
        # בדיקה שאפשר לקבל את הכוונה האחרונה
        last_intent = self.context.get_last_intent()
        self.assertEqual(last_intent["intent"], "get_order")
        self.assertEqual(last_intent["message"], "תבדוק את הסטטוס של הזמנה 12345")
    
    def test_is_context_fresh(self):
        """בדיקת טריות ההקשר"""
        # עדכון הקשר
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        # בדיקה שההקשר טרי
        self.assertTrue(self.context.is_context_fresh())
        
        # שינוי הזמן האחרון לפני 31 דקות
        self.context.last_update = datetime.now() - timedelta(minutes=31)
        
        # בדיקה שההקשר כבר לא טרי (ברירת המחדל היא 30 דקות)
        self.assertFalse(self.context.is_context_fresh())
        
        # בדיקה עם פרמטר מותאם
        self.assertTrue(self.context.is_context_fresh(max_age_minutes=60))
    
    def test_clear_context(self):
        """בדיקת איפוס ההקשר"""
        # עדכון הקשר
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        # בדיקה שיש מידע בהקשר
        self.assertEqual(len(self.context.entities["products"]), 1)
        self.assertEqual(len(self.context.intent_history), 1)
        
        # איפוס ההקשר
        self.context.clear_context()
        
        # בדיקה שההקשר אופס
        self.assertEqual(len(self.context.entities["products"]), 0)
        self.assertEqual(len(self.context.intent_history), 0)
        self.assertIsNone(self.context.last_mentioned["product"])


class TestContextFunctions(unittest.TestCase):
    """בדיקות לפונקציות הקשר"""
    
    def setUp(self):
        """הכנה לפני כל בדיקה"""
        self.context = ConversationContext()
        
        # עדכון הקשר עם מוצר והזמנה
        self.context.update_context(
            "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח",
            "update_product",
            {"product_name": "חולצה כחולה", "price": 99}
        )
        
        self.context.update_context(
            "תבדוק את הסטטוס של הזמנה 12345",
            "get_order",
            {"order_id": "12345"}
        )
    
    def test_understand_context(self):
        """בדיקת הבנת הקשר"""
        # יצירת היסטוריית שיחה
        conversation_history = [
            {"user": "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח", "assistant": "עדכנתי את המחיר של חולצה כחולה ל-99 ש\"ח"},
            {"user": "תבדוק את הסטטוס של הזמנה 12345", "assistant": "סטטוס ההזמנה 12345 הוא: בטיפול"}
        ]
        
        # בדיקת הבנת הקשר עם כינוי גוף זכר (מתייחס למוצר)
        context_info = understand_context("מה המחיר שלו?", conversation_history, self.context)
        self.assertIn("referenced_product", context_info)
        self.assertEqual(context_info["referenced_product"], "חולצה כחולה")
        
        # בדיקת הבנת הקשר עם כינוי גוף נקבה (מתייחס להזמנה)
        context_info = understand_context("מתי היא תגיע?", conversation_history, self.context)
        self.assertIn("referenced_order", context_info)
        self.assertEqual(context_info["referenced_order"], "12345")
        
        # בדיקת הבנת הקשר עם ביטוי עדכון
        context_info = understand_context("תעדכן אותו ל-149 ש\"ח", conversation_history, self.context)
        self.assertIn("update_product", context_info)
        self.assertEqual(context_info["update_product"], "חולצה כחולה")
    
    def test_resolve_pronouns(self):
        """בדיקת פתרון כינויי גוף"""
        # בדיקת פתרון כינוי גוף זכר
        resolved_text = resolve_pronouns("מה המחיר שלו?", self.context)
        self.assertEqual(resolved_text, "מה המחיר של חולצה כחולה?")
        
        # בדיקת פתרון כינוי גוף נקבה
        resolved_text = resolve_pronouns("מתי היא תגיע?", self.context)
        self.assertEqual(resolved_text, "מתי הזמנה 12345 תגיע?")
    
    def test_extract_context_from_history(self):
        """בדיקת חילוץ הקשר מהיסטוריה"""
        # יצירת היסטוריית שיחה
        conversation_history = [
            {"user": "תעדכן את המחיר של חולצה כחולה ל-99 ש\"ח", "assistant": "עדכנתי את המחיר של חולצה כחולה ל-99 ש\"ח"},
            {"user": "תבדוק את הסטטוס של הזמנה 12345", "assistant": "סטטוס ההזמנה 12345 הוא: בטיפול"}
        ]
        
        # חילוץ הקשר מההיסטוריה
        context_data = extract_context_from_history(conversation_history)
        
        # בדיקה שהמוצר זוהה
        self.assertIn("חולצה כחולה", context_data["products"])
        
        # בדיקה שההזמנה זוהתה
        self.assertIn("12345", context_data["orders"])
        
        # בדיקה שהנושאים זוהו
        self.assertIn("מוצרים", context_data["topics"])
        self.assertIn("הזמנות", context_data["topics"])


if __name__ == "__main__":
    unittest.main() 