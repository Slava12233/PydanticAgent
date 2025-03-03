"""
סקריפט להרצת בדיקות למערכת
"""
import os
import sys
import argparse
from run_comprehensive_tests import run_tests

def main():
    """
    פונקציה ראשית להרצת בדיקות
    """
    parser = argparse.ArgumentParser(description='הרצת בדיקות למערכת')
    parser.add_argument('--type', choices=['integration', 'user', 'performance', 'intent', 'manager', 'all'], 
                        default='all', help='סוג הבדיקות להרצה')
    parser.add_argument('--verbose', action='store_true', help='הצגת פלט מפורט')
    parser.add_argument('--file', type=str, help='הרצת קובץ בדיקה ספציפי')
    
    args = parser.parse_args()
    
    if args.file:
        # הרצת קובץ בדיקה ספציפי
        if not os.path.exists(args.file):
            # בדיקה אם הקובץ קיים בתיקיית הבדיקות
            test_file = os.path.join('tests', args.file)
            if not os.path.exists(test_file):
                print(f"❌ קובץ הבדיקה {args.file} לא נמצא")
                return 1
            args.file = test_file
            
        print(f"🧪 מריץ בדיקה מקובץ: {args.file}")
        os.system(f'python {args.file}')
    else:
        # הרצת בדיקות לפי סוג
        run_tests(args.type, args.verbose)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 