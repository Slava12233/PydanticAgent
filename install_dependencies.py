"""
סקריפט להתקנת כל החבילות הדרושות לפרויקט
"""
import subprocess
import sys
import os
import pkg_resources

def check_and_install_dependencies():
    """בדיקה והתקנה של כל החבילות הדרושות"""
    print("בודק חבילות חסרות...")
    
    # קריאת קובץ requirements.txt
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    with open(requirements_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            # דילוג על הערות וקווים ריקים
            if not line or line.startswith('#'):
                continue
            # טיפול בחבילות עם תוספות כמו logfire[httpx]
            if '[' in line and ']' in line:
                package_name = line.split('[')[0]
                requirements.append(line)
                # הוספת החבילה הבסיסית גם כן
                if package_name not in requirements:
                    requirements.append(package_name)
            else:
                requirements.append(line)
    
    # בדיקה אילו חבילות חסרות
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = []
    
    for requirement in requirements:
        # התעלמות מגרסאות ספציפיות לצורך הבדיקה
        if '==' in requirement:
            package_name = requirement.split('==')[0]
        elif '[' in requirement and ']' in requirement:
            package_name = requirement.split('[')[0]
        else:
            package_name = requirement
            
        # המרה לאותיות קטנות לצורך השוואה
        package_name = package_name.lower()
        
        if package_name not in installed:
            missing.append(requirement)
    
    # התקנת חבילות חסרות
    if missing:
        print(f"מתקין {len(missing)} חבילות חסרות:")
        for pkg in missing:
            print(f"  - {pkg}")
        
        # התקנה באמצעות pip
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("כל החבילות הותקנו בהצלחה!")
    else:
        print("כל החבילות כבר מותקנות!")
    
    # בדיקה ספציפית לחבילות לטיפול בקבצים
    file_packages = [
        "pypdf", "python-docx", "openpyxl", "python-pptx", 
        "beautifulsoup4", "html2text"
    ]
    
    print("\nבודק חבילות לטיפול בקבצים:")
    for package in file_packages:
        try:
            __import__(package.replace('-', '_').split('[')[0])
            print(f"  ✓ {package} מותקן")
        except ImportError:
            print(f"  ✗ {package} לא מותקן כראוי! מנסה להתקין שוב...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--force-reinstall"])

if __name__ == "__main__":
    check_and_install_dependencies() 