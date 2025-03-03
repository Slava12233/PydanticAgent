import unittest
from src.tools.managers.query_parser import (
    parse_complex_query,
    split_by_logical_connectors,
    is_comparative_query,
    parse_comparative_query,
    extract_comparison_objects,
    is_hypothetical_query,
    parse_hypothetical_query,
    extract_hypothetical_parts
)


class TestQueryParser(unittest.TestCase):
    """בדיקות יחידה למודול query_parser"""

    def test_split_by_logical_connectors(self):
        """בדיקת פיצול טקסט לפי מחברים לוגיים"""
        # בדיקת פיצול עם מחבר "ו"
        text1 = "תראה לי את המוצרים ו תבדוק את המלאי"
        result1 = split_by_logical_connectors(text1)
        self.assertEqual(len(result1), 2)
        self.assertEqual(result1[0], "תראה לי את המוצרים")
        self.assertEqual(result1[1], "תבדוק את המלאי")

        # בדיקת פיצול עם מחבר "או"
        text2 = "תראה לי את המוצרים או תבדוק את המלאי"
        result2 = split_by_logical_connectors(text2)
        self.assertEqual(len(result2), 2)
        self.assertEqual(result2[0], "תראה לי את המוצרים")
        self.assertEqual(result2[1], "תבדוק את המלאי")

        # בדיקת פיצול עם מספר מחברים
        text3 = "תראה לי את המוצרים ו תבדוק את המלאי וגם תעדכן את המחירים"
        result3 = split_by_logical_connectors(text3)
        self.assertEqual(len(result3), 3)
        self.assertEqual(result3[0], "תראה לי את המוצרים")
        self.assertEqual(result3[1], "תבדוק את המלאי")
        self.assertEqual(result3[2], "תעדכן את המחירים")

        # בדיקת טקסט ללא מחברים
        text4 = "תראה לי את המוצרים"
        result4 = split_by_logical_connectors(text4)
        self.assertEqual(len(result4), 1)
        self.assertEqual(result4[0], "תראה לי את המוצרים")

    def test_is_comparative_query(self):
        """בדיקת זיהוי שאלות השוואתיות"""
        # בדיקת ביטויים השוואתיים
        self.assertTrue(is_comparative_query("מה ההבדל בין חולצה כחולה לחולצה אדומה"))
        self.assertTrue(is_comparative_query("השוואה בין מכנסיים וחולצות"))
        self.assertTrue(is_comparative_query("תשווה בין המוצרים החדשים לישנים"))
        
        # בדיקת דפוס "או"
        self.assertTrue(is_comparative_query("חולצה כחולה או חולצה אדומה"))
        
        # בדיקת דפוס "לעומת"
        self.assertTrue(is_comparative_query("חולצה כחולה לעומת חולצה אדומה"))
        
        # בדיקת שאלות שאינן השוואתיות
        self.assertFalse(is_comparative_query("מה המחיר של חולצה כחולה"))
        self.assertFalse(is_comparative_query("תראה לי את המוצרים"))

    def test_extract_comparison_objects(self):
        """בדיקת חילוץ אובייקטים להשוואה"""
        # בדיקת דפוס "מה ההבדל בין X ל-Y"
        text1 = "מה ההבדל בין חולצה כחולה לחולצה אדומה"
        result1 = extract_comparison_objects(text1)
        self.assertEqual(len(result1), 2)
        self.assertEqual(result1[0], "חולצה כחולה")
        self.assertEqual(result1[1], "חולצה אדומה")
        
        # בדיקת דפוס "X או Y"
        text2 = "חולצה כחולה או חולצה אדומה"
        result2 = extract_comparison_objects(text2)
        self.assertEqual(len(result2), 2)
        self.assertEqual(result2[0], "חולצה כחולה")
        self.assertEqual(result2[1], "חולצה אדומה")
        
        # בדיקת דפוס "X לעומת Y"
        text3 = "חולצה כחולה לעומת חולצה אדומה"
        result3 = extract_comparison_objects(text3)
        self.assertEqual(len(result3), 2)
        self.assertEqual(result3[0], "חולצה כחולה")
        self.assertEqual(result3[1], "חולצה אדומה")
        
        # בדיקת טקסט ללא דפוס מתאים
        text4 = "מה המחיר של חולצה כחולה"
        result4 = extract_comparison_objects(text4)
        self.assertEqual(len(result4), 0)

    def test_parse_comparative_query(self):
        """בדיקת פירוק שאלה השוואתית למשימות"""
        text = "מה ההבדל בין חולצה כחולה לחולצה אדומה"
        result = parse_comparative_query(text)
        
        # בדיקת מספר המשימות
        self.assertEqual(len(result), 3)
        
        # בדיקת המשימה הראשונה
        self.assertEqual(result[0]["task_type"], "comparison")
        self.assertEqual(result[0]["intent_type"], "get_info")
        self.assertEqual(result[0]["object"], "חולצה כחולה")
        self.assertEqual(result[0]["order"], 0)
        
        # בדיקת המשימה השנייה
        self.assertEqual(result[1]["task_type"], "comparison")
        self.assertEqual(result[1]["intent_type"], "get_info")
        self.assertEqual(result[1]["object"], "חולצה אדומה")
        self.assertEqual(result[1]["order"], 1)
        
        # בדיקת המשימה השלישית
        self.assertEqual(result[2]["task_type"], "comparison")
        self.assertEqual(result[2]["intent_type"], "compare")
        self.assertEqual(result[2]["objects"], ["חולצה כחולה", "חולצה אדומה"])
        self.assertEqual(result[2]["order"], 2)

    def test_is_hypothetical_query(self):
        """בדיקת זיהוי שאלות היפותטיות"""
        # בדיקת ביטויים היפותטיים
        self.assertTrue(is_hypothetical_query("מה יקרה אם אזמין 100 חולצות"))
        self.assertTrue(is_hypothetical_query("מה יהיה אם אשנה את המחיר"))
        self.assertTrue(is_hypothetical_query("אם אני מוסיף מוצר חדש, איך זה ישפיע על המלאי"))
        self.assertTrue(is_hypothetical_query("במידה ואבטל את ההזמנה, האם אקבל החזר"))
        
        # בדיקת שאלות שאינן היפותטיות
        self.assertFalse(is_hypothetical_query("מה המחיר של חולצה כחולה"))
        self.assertFalse(is_hypothetical_query("תראה לי את המוצרים"))

    def test_extract_hypothetical_parts(self):
        """בדיקת חילוץ התנאי והתוצאה משאלה היפותטית"""
        # בדיקת דפוס "מה יקרה אם X"
        text1 = "מה יקרה אם אזמין 100 חולצות"
        condition1, action1 = extract_hypothetical_parts(text1)
        self.assertEqual(condition1, "אזמין 100 חולצות")
        self.assertEqual(action1, "התוצאה של אזמין 100 חולצות")
        
        # בדיקת דפוס "אם X אז Y"
        text2 = "אם אני מוסיף מוצר חדש אז המלאי יגדל"
        condition2, action2 = extract_hypothetical_parts(text2)
        self.assertEqual(condition2, "אני מוסיף מוצר חדש")
        self.assertEqual(action2, "המלאי יגדל")
        
        # בדיקת טקסט ללא דפוס מתאים
        text3 = "מה המחיר של חולצה כחולה"
        condition3, action3 = extract_hypothetical_parts(text3)
        self.assertEqual(condition3, "מה המחיר של חולצה כחולה")
        self.assertEqual(action3, "")

    def test_parse_hypothetical_query(self):
        """בדיקת פירוק שאלה היפותטית למשימות"""
        text = "מה יקרה אם אזמין 100 חולצות"
        result = parse_hypothetical_query(text)
        
        # בדיקת מספר המשימות
        self.assertEqual(len(result), 3)
        
        # בדיקת המשימה הראשונה
        self.assertEqual(result[0]["task_type"], "hypothetical")
        self.assertEqual(result[0]["intent_type"], "check_condition")
        self.assertEqual(result[0]["condition"], "אזמין 100 חולצות")
        self.assertEqual(result[0]["order"], 0)
        
        # בדיקת המשימה השנייה
        self.assertEqual(result[1]["task_type"], "hypothetical")
        self.assertEqual(result[1]["intent_type"], "simulate_result")
        self.assertEqual(result[1]["action"], "התוצאה של אזמין 100 חולצות")
        self.assertEqual(result[1]["order"], 1)
        
        # בדיקת המשימה השלישית
        self.assertEqual(result[2]["task_type"], "hypothetical")
        self.assertEqual(result[2]["intent_type"], "analyze_result")
        self.assertEqual(result[2]["condition"], "אזמין 100 חולצות")
        self.assertEqual(result[2]["action"], "התוצאה של אזמין 100 חולצות")
        self.assertEqual(result[2]["order"], 2)

    def test_parse_complex_query(self):
        """בדיקת פירוק שאילתה מורכבת למשימות"""
        # בדיקת שאלה השוואתית
        text1 = "מה ההבדל בין חולצה כחולה לחולצה אדומה"
        result1 = parse_complex_query(text1)
        self.assertEqual(len(result1), 3)
        self.assertEqual(result1[0]["task_type"], "comparison")
        
        # בדיקת שאלה היפותטית
        text2 = "מה יקרה אם אזמין 100 חולצות"
        result2 = parse_complex_query(text2)
        self.assertEqual(len(result2), 3)
        self.assertEqual(result2[0]["task_type"], "hypothetical")
        
        # בדיקת שאילתה עם מחברים לוגיים
        # הערה: כאן אנחנו מניחים שהפונקציה identify_specific_intent קיימת ומחזירה ערכים כלשהם
        # במציאות, נצטרך להשתמש ב-mock או לבדוק את התוצאה בצורה אחרת
        text3 = "תראה לי את המוצרים ו תבדוק את המלאי"
        result3 = parse_complex_query(text3)
        self.assertEqual(len(result3), 2)
        self.assertEqual(result3[0]["query"], "תראה לי את המוצרים")
        self.assertEqual(result3[1]["query"], "תבדוק את המלאי")


if __name__ == "__main__":
    unittest.main() 