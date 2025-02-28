"""
סקריפט להרצת כל הבדיקות
"""
import unittest
import sys
import os

# הוספת תיקיית הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_tests():
    """הרצת כל הבדיקות"""
    # גילוי אוטומטי של כל הבדיקות
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # הרצת הבדיקות
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # החזרת קוד יציאה מתאים
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    # וידוא שתיקיית הבדיקות קיימת
    if not os.path.exists('tests'):
        os.makedirs('tests')
        # יצירת קובץ __init__.py ריק
        with open(os.path.join('tests', '__init__.py'), 'w') as f:
            pass
    
    # הרצת הבדיקות
    sys.exit(run_tests()) 