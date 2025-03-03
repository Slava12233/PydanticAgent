"""
סקריפט להרצת בדיקות מקיפות למערכת
"""
import os
import sys
import unittest
import argparse
import time
from datetime import datetime

# הוספת תיקיית הפרויקט הראשית ל-PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests(test_type=None, verbose=False):
    """
    מריץ את הבדיקות המבוקשות
    
    Args:
        test_type (str): סוג הבדיקות להרצה ('integration', 'user', 'performance', 'intent', 'manager', 'all')
        verbose (bool): האם להציג פלט מפורט
    """
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    start_time = time.time()
    print("=" * 80)
    print(f"🧪 הרצת בדיקות מקיפות - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # בדיקות אינטגרציה
    if test_type in ['integration', 'all']:
        print("\n📋 מריץ בדיקות אינטגרציה...")
        try:
            integration_tests = loader.loadTestsFromName('test_woocommerce_api_integration')
            product_creation_tests = loader.loadTestsFromName('test_product_creation_integration')
            
            print("\n🔍 בדיקות אינטגרציה עם WooCommerce API:")
            runner.run(integration_tests)
            
            print("\n🔍 בדיקות אינטגרציה ליצירת מוצרים:")
            runner.run(product_creation_tests)
        except Exception as e:
            print(f"❌ שגיאה בטעינת בדיקות אינטגרציה: {str(e)}")
    
    # בדיקות תרחישי משתמש
    if test_type in ['user', 'all']:
        print("\n📋 מריץ בדיקות תרחישי משתמש...")
        try:
            user_tests = loader.loadTestsFromName('test_user_scenarios')
            
            print("\n🔍 בדיקות תרחישי משתמש:")
            runner.run(user_tests)
        except Exception as e:
            print(f"❌ שגיאה בטעינת בדיקות תרחישי משתמש: {str(e)}")
    
    # בדיקות ביצועים
    if test_type in ['performance', 'all']:
        print("\n📋 מריץ בדיקות ביצועים...")
        try:
            performance_tests = loader.loadTestsFromName('test_performance_hebrew')
            
            print("\n🔍 בדיקות ביצועים בעברית:")
            runner.run(performance_tests)
        except Exception as e:
            print(f"❌ שגיאה בטעינת בדיקות ביצועים: {str(e)}")
    
    # בדיקות זיהוי כוונות
    if test_type in ['intent', 'all']:
        print("\n📋 מריץ בדיקות זיהוי כוונות...")
        try:
            intent_tests = loader.loadTestsFromName('test_intent_recognizer')
            
            print("\n🔍 בדיקות זיהוי כוונות:")
            runner.run(intent_tests)
        except Exception as e:
            print(f"❌ שגיאה בטעינת בדיקות זיהוי כוונות: {str(e)}")
    
    # בדיקות מנהלים
    if test_type in ['manager', 'all']:
        print("\n📋 מריץ בדיקות מנהלים...")
        try:
            product_manager_tests = loader.loadTestsFromName('test_product_manager')
            order_manager_tests = loader.loadTestsFromName('test_order_manager')
            customer_manager_tests = loader.loadTestsFromName('test_customer_manager')
            context_manager_tests = loader.loadTestsFromName('test_context_manager')
            query_parser_tests = loader.loadTestsFromName('test_query_parser')
            response_generator_tests = loader.loadTestsFromName('test_response_generator')
            
            print("\n🔍 בדיקות מנהל מוצרים:")
            runner.run(product_manager_tests)
            
            print("\n🔍 בדיקות מנהל הזמנות:")
            runner.run(order_manager_tests)
            
            print("\n🔍 בדיקות מנהל לקוחות:")
            runner.run(customer_manager_tests)
            
            print("\n🔍 בדיקות מנהל הקשר:")
            runner.run(context_manager_tests)
            
            print("\n🔍 בדיקות מנהל פירוק שאילתות:")
            runner.run(query_parser_tests)
            
            print("\n🔍 בדיקות מחולל תשובות:")
            runner.run(response_generator_tests)
        except Exception as e:
            print(f"❌ שגיאה בטעינת בדיקות מנהלים: {str(e)}")
    
    end_time = time.time()
    print("\n" + "=" * 80)
    print(f"✅ הבדיקות הסתיימו בהצלחה - זמן ריצה: {end_time - start_time:.2f} שניות")
    print("=" * 80)

def main():
    """
    פונקציה ראשית
    """
    parser = argparse.ArgumentParser(description='הרצת בדיקות מקיפות למערכת')
    parser.add_argument('--type', choices=['integration', 'user', 'performance', 'intent', 'manager', 'all'], 
                        default='all', help='סוג הבדיקות להרצה')
    parser.add_argument('--verbose', action='store_true', help='הצגת פלט מפורט')
    
    args = parser.parse_args()
    run_tests(args.type, args.verbose)

if __name__ == "__main__":
    main() 