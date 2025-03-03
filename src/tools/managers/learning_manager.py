"""
מודול ללמידה והשתפרות מתמדת (Learning Manager)

מודול זה מכיל פונקציות וכלים לתיעוד אינטראקציות עם המשתמש,
זיהוי אינטראקציות בעייתיות, ויצירת דוחות תקופתיים על ביצועי הסוכן.
המודול גם מאפשר עדכון אוטומטי של מילות מפתח בהתבסס על אינטראקציות מוצלחות.
"""
import logging
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
import csv
import sqlite3
from pathlib import Path

# הגדרת לוגר
logger = logging.getLogger(__name__)

# נתיב לתיקיית הלוגים
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# נתיב לקובץ מסד הנתונים של הלמידה
LEARNING_DB = LOGS_DIR / "learning.db"

class LearningManager:
    """מחלקה לניהול למידה והשתפרות מתמדת"""
    
    def __init__(self):
        """אתחול מנהל הלמידה"""
        self.interactions = []
        self.problematic_interactions = []
        self.successful_interactions = []
        self.keyword_suggestions = {}
        
        # הגדרת נתיב מסד הנתונים
        self.LEARNING_DB = LEARNING_DB
        
        # יצירת מסד נתונים אם לא קיים
        self._init_db()
    
    def _init_db(self):
        """יצירת מסד נתונים אם לא קיים"""
        conn = sqlite3.connect(str(self.LEARNING_DB))
        cursor = conn.cursor()
        
        # יצירת טבלת אינטראקציות
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            intent_type TEXT,
            confidence REAL,
            response TEXT,
            timestamp DATETIME,
            success INTEGER,
            feedback TEXT
        )
        ''')
        
        # יצירת טבלת הצעות מילות מפתח
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_type TEXT,
            keyword TEXT,
            score REAL,
            source_message TEXT,
            timestamp DATETIME
        )
        ''')
        
        # יצירת טבלת דוחות
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT,
            content TEXT,
            timestamp DATETIME
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"מסד נתונים למידה אותחל בהצלחה: {self.LEARNING_DB}")
    
    def log_interaction(self, user_id: int, message: str, intent_type: str, 
                       confidence: float, response: str, success: bool = True,
                       feedback: str = None) -> int:
        """
        תיעוד אינטראקציה עם המשתמש
        
        Args:
            user_id: מזהה המשתמש
            message: הודעת המשתמש
            intent_type: סוג הכוונה שזוהתה
            confidence: רמת הביטחון בזיהוי הכוונה
            response: התשובה שניתנה למשתמש
            success: האם האינטראקציה הייתה מוצלחת
            feedback: משוב מהמשתמש (אם יש)
            
        Returns:
            מזהה האינטראקציה במסד הנתונים
        """
        timestamp = datetime.now()
        
        # שמירה במסד הנתונים
        conn = sqlite3.connect(str(self.LEARNING_DB))
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO interactions 
        (user_id, message, intent_type, confidence, response, timestamp, success, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, message, intent_type, confidence, response, timestamp, 
              1 if success else 0, feedback))
        
        interaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # שמירה ברשימות המקומיות
        interaction_data = {
            "id": interaction_id,
            "user_id": user_id,
            "message": message,
            "intent_type": intent_type,
            "confidence": confidence,
            "response": response,
            "timestamp": timestamp,
            "success": success,
            "feedback": feedback
        }
        
        self.interactions.append(interaction_data)
        
        # בדיקה אם האינטראקציה בעייתית
        if not success or confidence < 0.7:
            self.problematic_interactions.append(interaction_data)
            logger.warning(f"אינטראקציה בעייתית זוהתה: {interaction_id}")
        
        # בדיקה אם האינטראקציה מוצלחת במיוחד
        if success and confidence > 0.9:
            self.successful_interactions.append(interaction_data)
            # ניתוח האינטראקציה לחילוץ מילות מפתח פוטנציאליות
            self._analyze_successful_interaction(interaction_data)
        
        return interaction_id
    
    def _analyze_successful_interaction(self, interaction: Dict[str, Any]):
        """
        ניתוח אינטראקציה מוצלחת לחילוץ מילות מפתח פוטנציאליות
        
        Args:
            interaction: נתוני האינטראקציה
        """
        message = interaction["message"]
        intent_type = interaction["intent_type"]
        
        # חילוץ ביטויים פוטנציאליים (3-5 מילים רצופות)
        words = re.findall(r'\b\w+\b', message)
        
        for i in range(len(words)):
            # יצירת ביטויים באורכים שונים
            for length in range(2, min(6, len(words) - i + 1)):
                phrase = " ".join(words[i:i+length])
                
                # בדיקה אם הביטוי כבר קיים במילון
                if intent_type not in self.keyword_suggestions:
                    self.keyword_suggestions[intent_type] = {}
                
                if phrase in self.keyword_suggestions[intent_type]:
                    # עדכון ציון הביטוי
                    self.keyword_suggestions[intent_type][phrase] += 0.1
                else:
                    # הוספת ביטוי חדש
                    self.keyword_suggestions[intent_type][phrase] = 0.1
                
                # שמירת ההצעה במסד הנתונים
                conn = sqlite3.connect(str(self.LEARNING_DB))
                cursor = conn.cursor()
                
                # בדיקה אם הביטוי כבר קיים
                cursor.execute('''
                SELECT id, score FROM keyword_suggestions 
                WHERE intent_type = ? AND keyword = ?
                ''', (intent_type, phrase))
                
                result = cursor.fetchone()
                
                if result:
                    # עדכון ציון קיים
                    keyword_id, current_score = result
                    new_score = current_score + 0.1
                    cursor.execute('''
                    UPDATE keyword_suggestions 
                    SET score = ?, timestamp = ?
                    WHERE id = ?
                    ''', (new_score, datetime.now(), keyword_id))
                else:
                    # הוספת ביטוי חדש
                    cursor.execute('''
                    INSERT INTO keyword_suggestions 
                    (intent_type, keyword, score, source_message, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (intent_type, phrase, 0.1, message, datetime.now()))
                
                conn.commit()
                conn.close()
    
    def identify_problematic_interactions(self, min_confidence: float = 0.7, 
                                         days: int = 7) -> List[Dict[str, Any]]:
        """
        זיהוי אינטראקציות בעייתיות
        
        Args:
            min_confidence: רמת הביטחון המינימלית הנדרשת
            days: מספר הימים האחרונים לבדיקה
            
        Returns:
            רשימת אינטראקציות בעייתיות
        """
        since_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(str(self.LEARNING_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM interactions 
        WHERE (confidence < ? OR success = 0) AND timestamp > ?
        ORDER BY timestamp DESC
        ''', (min_confidence, since_date))
        
        problematic = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return problematic
    
    def generate_periodic_report(self, report_type: str = "weekly") -> Dict[str, Any]:
        """
        יצירת דוח תקופתי על ביצועי הסוכן
        
        Args:
            report_type: סוג הדוח (daily, weekly, monthly)
            
        Returns:
            דוח ביצועים
        """
        # קביעת טווח התאריכים לדוח
        now = datetime.now()
        if report_type == "daily":
            since_date = now - timedelta(days=1)
            title = f"דוח יומי - {now.strftime('%Y-%m-%d')}"
        elif report_type == "weekly":
            since_date = now - timedelta(days=7)
            title = f"דוח שבועי - {(now - timedelta(days=7)).strftime('%Y-%m-%d')} עד {now.strftime('%Y-%m-%d')}"
        elif report_type == "monthly":
            since_date = now - timedelta(days=30)
            title = f"דוח חודשי - {(now - timedelta(days=30)).strftime('%Y-%m-%d')} עד {now.strftime('%Y-%m-%d')}"
        else:
            raise ValueError(f"סוג דוח לא תקין: {report_type}")
        
        conn = sqlite3.connect(str(self.LEARNING_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # סך כל האינטראקציות
        cursor.execute('''
        SELECT COUNT(*) as total FROM interactions 
        WHERE timestamp > ?
        ''', (since_date,))
        total_interactions = cursor.fetchone()["total"]
        
        # אינטראקציות מוצלחות
        cursor.execute('''
        SELECT COUNT(*) as successful FROM interactions 
        WHERE success = 1 AND timestamp > ?
        ''', (since_date,))
        successful_interactions = cursor.fetchone()["successful"]
        
        # אינטראקציות בעייתיות
        cursor.execute('''
        SELECT COUNT(*) as problematic FROM interactions 
        WHERE (confidence < 0.7 OR success = 0) AND timestamp > ?
        ''', (since_date,))
        problematic_interactions = cursor.fetchone()["problematic"]
        
        # התפלגות לפי סוגי כוונות
        cursor.execute('''
        SELECT intent_type, COUNT(*) as count FROM interactions 
        WHERE timestamp > ?
        GROUP BY intent_type
        ORDER BY count DESC
        ''', (since_date,))
        intent_distribution = [dict(row) for row in cursor.fetchall()]
        
        # ממוצע רמת ביטחון
        cursor.execute('''
        SELECT AVG(confidence) as avg_confidence FROM interactions 
        WHERE timestamp > ?
        ''', (since_date,))
        avg_confidence = cursor.fetchone()["avg_confidence"]
        
        # הצעות מילות מפתח חדשות
        cursor.execute('''
        SELECT intent_type, keyword, score FROM keyword_suggestions 
        WHERE timestamp > ? AND score > 0.3
        ORDER BY score DESC
        LIMIT 20
        ''', (since_date,))
        keyword_suggestions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # יצירת הדוח
        report = {
            "title": title,
            "generated_at": now,
            "period": {
                "start": since_date,
                "end": now
            },
            "statistics": {
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
                "problematic_interactions": problematic_interactions,
                "success_rate": (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0,
                "avg_confidence": avg_confidence
            },
            "intent_distribution": intent_distribution,
            "keyword_suggestions": keyword_suggestions
        }
        
        # שמירת הדוח במסד הנתונים
        conn = sqlite3.connect(str(self.LEARNING_DB))
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO reports 
        (report_type, content, timestamp)
        VALUES (?, ?, ?)
        ''', (report_type, json.dumps(report, default=str), now))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # שמירת הדוח כקובץ CSV
        self._save_report_to_csv(report, report_type)
        
        # הוספת מזהה הדוח
        report["id"] = report_id
        
        return report
    
    def _save_report_to_csv(self, report: Dict[str, Any], report_type: str):
        """
        שמירת דוח כקובץ CSV
        
        Args:
            report: הדוח לשמירה
            report_type: סוג הדוח
        """
        report_dir = Path(os.path.dirname(self.LEARNING_DB)) / "reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.csv"
        filepath = report_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # כותרת הדוח
            writer.writerow([report["title"]])
            writer.writerow([f"נוצר בתאריך: {report['generated_at']}"])
            writer.writerow([])
            
            # סטטיסטיקות
            writer.writerow(["סטטיסטיקות"])
            writer.writerow(["מדד", "ערך"])
            for key, value in report["statistics"].items():
                if key == "success_rate" or key == "avg_confidence":
                    writer.writerow([key, f"{value:.2f}%"])
                else:
                    writer.writerow([key, value])
            writer.writerow([])
            
            # התפלגות לפי סוגי כוונות
            writer.writerow(["התפלגות לפי סוגי כוונות"])
            writer.writerow(["סוג כוונה", "מספר אינטראקציות"])
            for item in report["intent_distribution"]:
                writer.writerow([item["intent_type"], item["count"]])
            writer.writerow([])
            
            # הצעות מילות מפתח
            writer.writerow(["הצעות מילות מפתח חדשות"])
            writer.writerow(["סוג כוונה", "מילת מפתח", "ציון"])
            for item in report["keyword_suggestions"]:
                writer.writerow([item["intent_type"], item["keyword"], f"{item['score']:.2f}"])
        
        logger.info(f"דוח {report_type} נשמר בהצלחה: {filepath}")
    
    def update_keywords_automatically(self, min_score: float = 0.5) -> Dict[str, List[str]]:
        """
        עדכון אוטומטי של מילות מפתח בהתבסס על אינטראקציות מוצלחות
        
        Args:
            min_score: ציון מינימלי נדרש להוספת מילת מפתח
            
        Returns:
            מילון של מילות מפתח חדשות לפי סוג כוונה
        """
        conn = sqlite3.connect(str(self.LEARNING_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT intent_type, keyword, score FROM keyword_suggestions 
        WHERE score >= ?
        ORDER BY intent_type, score DESC
        ''', (min_score,))
        
        suggestions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # ארגון ההצעות לפי סוג כוונה
        new_keywords = {}
        for suggestion in suggestions:
            intent_type = suggestion["intent_type"]
            keyword = suggestion["keyword"]
            
            if intent_type not in new_keywords:
                new_keywords[intent_type] = []
            
            new_keywords[intent_type].append(keyword)
        
        return new_keywords
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        קבלת סטטיסטיקות למידה
        
        Returns:
            סטטיסטיקות למידה
        """
        conn = sqlite3.connect(str(self.LEARNING_DB))
        cursor = conn.cursor()
        
        # סך כל האינטראקציות
        cursor.execute('SELECT COUNT(*) FROM interactions')
        total_interactions = cursor.fetchone()[0]
        
        # מספר האינטראקציות המוצלחות
        cursor.execute('SELECT COUNT(*) FROM interactions WHERE success = 1')
        successful_interactions = cursor.fetchone()[0]
        
        # מספר האינטראקציות הבעייתיות
        cursor.execute('SELECT COUNT(*) FROM interactions WHERE success = 0')
        failed_interactions = cursor.fetchone()[0]
        
        # מספר הצעות מילות המפתח
        cursor.execute('SELECT COUNT(*) FROM keyword_suggestions')
        total_suggestions = cursor.fetchone()[0]
        
        # מספר הדוחות
        cursor.execute('SELECT COUNT(*) FROM reports')
        total_reports = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "failed_interactions": failed_interactions,
            "success_rate": (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0,
            "total_keyword_suggestions": total_suggestions,
            "total_reports": total_reports,
            "last_updated": datetime.now()
        }

# יצירת מופע גלובלי של מנהל הלמידה
learning_manager = LearningManager() 