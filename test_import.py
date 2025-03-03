"""
קובץ בדיקה פשוט לייבוא הפונקציה identify_specific_intent
"""

try:
    from src.tools.intent import identify_specific_intent
    print("ייבוא הצליח!")
    
    # בדיקת משפט 3 בלבד
    print("\n=== בדיקת משפט 3 ===")
    print("משפט: 'הצג לי את ההזמנות האחרונות'")
    
    # בדיקה עם try-except
    try:
        result = identify_specific_intent("הצג לי את ההזמנות האחרונות")
        print(f"תוצאה: {result}")
    except Exception as e:
        print(f"שגיאה בזיהוי כוונה: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"שגיאה בייבוא: {e}")
    import traceback
    traceback.print_exc() 