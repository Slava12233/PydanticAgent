"""
קובץ אתחול לחבילת בדיקות זיהוי משימות
"""
import os
import sys

# הוספת נתיב הפרויקט ל-PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root) 