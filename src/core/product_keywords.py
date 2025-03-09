"""
מילות מפתח לזיהוי משימות הקשורות למוצרים
"""

# מילות מפתח לזיהוי משימות ניהול מוצרים
PRODUCT_KEYWORDS = [
    # מילות מפתח פורמליות
    'מוצר', 'מוצרים', 'הוסף מוצר', 'ערוך מוצר', 'מחק מוצר', 'קטגוריה', 'תגית',
    'תמונה', 'תיאור מוצר', 'מק"ט', 'sku', 'product', 'add product', 'edit product',
    
    # ביטויים טבעיים בעברית
    'תוסיף מוצר', 'להוסיף מוצר', 'ליצור מוצר', 'רוצה להוסיף', 'רוצה ליצור',
    'תעדכן מוצר', 'לעדכן מוצר', 'לשנות מוצר', 'תשנה מוצר', 'תמחק מוצר', 'למחוק מוצר',
    'להעלות תמונה', 'תעלה תמונה', 'להוסיף תמונה', 'תוסיף תמונה',
    'לשנות מחיר', 'תשנה מחיר', 'לעדכן מחיר', 'תעדכן מחיר',
    'להוסיף לחנות', 'תוסיף לחנות', 'למכור', 'אני רוצה למכור',
    'איך מוסיפים', 'איך יוצרים', 'איך מעדכנים', 'איך מוחקים',
    'המוצר לא מופיע', 'המוצר נעלם', 'לא רואים את המוצר',
    'תיאור המוצר', 'לכתוב תיאור', 'לשנות תיאור',
    'קטגוריות', 'לשייך לקטגוריה', 'להוסיף קטגוריה',
    'מוצר חדש', 'פריט חדש', 'להוסיף פריט'
]

# מילות מפתח לזיהוי משימות ניהול מלאי
INVENTORY_KEYWORDS = [
    # מילות מפתח פורמליות
    'מלאי', 'כמות', 'מחסן', 'אזל המלאי', 'מלאי נמוך', 'עדכון מלאי',
    'inventory', 'stock', 'warehouse', 'out of stock', 'low stock',
    
    # ביטויים טבעיים בעברית
    'לעדכן מלאי', 'תעדכן מלאי', 'לשנות מלאי', 'תשנה מלאי',
    'לבדוק מלאי', 'תבדוק מלאי', 'לראות מלאי', 'תראה מלאי',
    'אזל', 'נגמר', 'לא במלאי', 'חסר', 'חסר במלאי',
    'להוסיף למלאי', 'תוסיף למלאי', 'להגדיל מלאי', 'תגדיל מלאי',
    'להפחית מלאי', 'תפחית מלאי', 'להוריד מהמלאי', 'תוריד מהמלאי',
    'כמה יש במלאי', 'כמה נשאר', 'כמה יחידות', 'כמה פריטים',
    'מוצרים שאזלו', 'מוצרים שנגמרו', 'מוצרים במלאי נמוך',
    'התראות מלאי', 'התראה על מלאי', 'להתריע כשנגמר',
    'ניהול מלאי', 'לנהל מלאי', 'מעקב מלאי', 'לעקוב אחרי מלאי',
    'ספירת מלאי', 'לספור מלאי', 'תספור מלאי'
]

# מילות מפתח לזיהוי משימות ניהול קטגוריות
CATEGORY_KEYWORDS = [
    # מילות מפתח פורמליות
    'קטגוריה', 'קטגוריות', 'תגית', 'תגיות', 'סיווג', 'סיווגים',
    'category', 'categories', 'tag', 'tags', 'classification',
    
    # ביטויים טבעיים בעברית
    'להוסיף קטגוריה', 'תוסיף קטגוריה', 'ליצור קטגוריה', 'תיצור קטגוריה',
    'לערוך קטגוריה', 'תערוך קטגוריה', 'לשנות קטגוריה', 'תשנה קטגוריה',
    'למחוק קטגוריה', 'תמחק קטגוריה', 'להסיר קטגוריה', 'תסיר קטגוריה',
    'לשייך מוצר', 'תשייך מוצר', 'להוסיף מוצר לקטגוריה', 'תוסיף מוצר לקטגוריה',
    'להסיר מוצר מקטגוריה', 'תסיר מוצר מקטגוריה',
    'לראות קטגוריות', 'תראה קטגוריות', 'להציג קטגוריות', 'תציג קטגוריות',
    'אילו קטגוריות יש', 'איזה קטגוריות יש', 'מה הקטגוריות',
    'לארגן מוצרים', 'תארגן מוצרים', 'לסדר מוצרים', 'תסדר מוצרים',
    'מבנה קטגוריות', 'עץ קטגוריות', 'היררכיה של קטגוריות'
] 