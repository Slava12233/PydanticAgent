"""
מודול לניטור ביצועים של המערכת.
"""

import psutil
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from .metrics import metrics
from .alerts import alert_manager, AlertRule, AlertSeverity

logger = logging.getLogger(__name__)

class SystemMonitor:
    """מנטר משאבי מערכת"""

    def __init__(self):
        self.setup_alert_rules()

    def setup_alert_rules(self):
        """הגדרת כללי התראה למשאבי מערכת"""
        # התראה על שימוש גבוה ב-CPU
        alert_manager.add_rule(AlertRule(
            name="high_cpu",
            check_func=lambda: self.get_cpu_usage() > 80,
            message="שימוש גבוה ב-CPU",
            severity=AlertSeverity.WARNING,
            cooldown=timedelta(minutes=5)
        ))

        # התראה על שימוש גבוה בזיכרון
        alert_manager.add_rule(AlertRule(
            name="high_memory",
            check_func=lambda: self.get_memory_usage() > 85,
            message="שימוש גבוה בזיכרון",
            severity=AlertSeverity.WARNING,
            cooldown=timedelta(minutes=5)
        ))

        # התראה על שימוש גבוה בדיסק
        alert_manager.add_rule(AlertRule(
            name="high_disk",
            check_func=lambda: self.get_disk_usage() > 90,
            message="שימוש גבוה בדיסק",
            severity=AlertSeverity.WARNING,
            cooldown=timedelta(hours=1)
        ))

    def get_cpu_usage(self) -> float:
        """
        קבלת אחוז שימוש ב-CPU.
        
        Returns:
            אחוז שימוש ב-CPU
        """
        usage = psutil.cpu_percent(interval=1)
        metrics.record_metric("cpu_usage", usage)
        return usage

    def get_memory_usage(self) -> float:
        """
        קבלת אחוז שימוש בזיכרון.
        
        Returns:
            אחוז שימוש בזיכרון
        """
        memory = psutil.virtual_memory()
        usage = memory.percent
        metrics.record_metric("memory_usage", usage)
        return usage

    def get_disk_usage(self) -> float:
        """
        קבלת אחוז שימוש בדיסק.
        
        Returns:
            אחוז שימוש בדיסק
        """
        disk = psutil.disk_usage('/')
        usage = disk.percent
        metrics.record_metric("disk_usage", usage)
        return usage

    def get_system_stats(self) -> Dict[str, float]:
        """
        קבלת סטטיסטיקות מערכת.
        
        Returns:
            מילון עם סטטיסטיקות מערכת
        """
        return {
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage()
        }

class APIMonitor:
    """מנטר קריאות API"""

    def __init__(self):
        self.setup_alert_rules()

    def setup_alert_rules(self):
        """הגדרת כללי התראה לקריאות API"""
        # התראה על זמן תגובה גבוה
        alert_manager.add_rule(AlertRule(
            name="high_response_time",
            check_func=lambda: self.get_average_response_time() > 2000,  # 2 שניות
            message="זמן תגובה גבוה לקריאות API",
            severity=AlertSeverity.WARNING,
            cooldown=timedelta(minutes=5)
        ))

        # התראה על אחוז שגיאות גבוה
        alert_manager.add_rule(AlertRule(
            name="high_error_rate",
            check_func=lambda: self.get_error_rate() > 0.05,  # 5%
            message="אחוז שגיאות גבוה בקריאות API",
            severity=AlertSeverity.ERROR,
            cooldown=timedelta(minutes=5)
        ))

    def record_request(self, endpoint: str, duration: float, success: bool):
        """
        תיעוד קריאת API.
        
        Args:
            endpoint: נקודת הקצה
            duration: זמן התגובה במילישניות
            success: האם הקריאה הצליחה
        """
        metrics.record_metric("api_request_duration", duration, {"endpoint": endpoint})
        if not success:
            metrics.record_metric("api_request_error", 1, {"endpoint": endpoint})

    def get_average_response_time(self, window: Optional[timedelta] = None) -> float:
        """
        חישוב זמן תגובה ממוצע.
        
        Args:
            window: חלון זמן לחישוב (אופציונלי)
            
        Returns:
            זמן תגובה ממוצע במילישניות
        """
        start_time = datetime.now() - window if window else None
        return metrics.get_average("api_request_duration", start_time)

    def get_error_rate(self, window: Optional[timedelta] = None) -> float:
        """
        חישוב אחוז שגיאות.
        
        Args:
            window: חלון זמן לחישוב (אופציונלי)
            
        Returns:
            אחוז השגיאות
        """
        start_time = datetime.now() - window if window else None
        error_points = metrics.get_metrics("api_request_error", start_time)
        total_points = metrics.get_metrics("api_request_duration", start_time)
        
        if not total_points:
            return 0.0
            
        return len(error_points) / len(total_points)

    def get_endpoint_stats(self, window: Optional[timedelta] = None) -> Dict[str, Dict[str, float]]:
        """
        קבלת סטטיסטיקות לפי נקודת קצה.
        
        Args:
            window: חלון זמן לחישוב (אופציונלי)
            
        Returns:
            מילון עם סטטיסטיקות לכל נקודת קצה
        """
        start_time = datetime.now() - window if window else None
        points = metrics.get_metrics("api_request_duration", start_time)
        
        stats = {}
        for point in points:
            endpoint = point.labels.get("endpoint", "unknown")
            if endpoint not in stats:
                stats[endpoint] = {
                    "count": 0,
                    "total_duration": 0,
                    "errors": 0
                }
            stats[endpoint]["count"] += 1
            stats[endpoint]["total_duration"] += point.value
        
        # הוספת מידע על שגיאות
        error_points = metrics.get_metrics("api_request_error", start_time)
        for point in error_points:
            endpoint = point.labels.get("endpoint", "unknown")
            if endpoint in stats:
                stats[endpoint]["errors"] += 1
        
        # חישוב ממוצעים ואחוזים
        for endpoint in stats:
            count = stats[endpoint]["count"]
            stats[endpoint]["avg_duration"] = stats[endpoint]["total_duration"] / count
            stats[endpoint]["error_rate"] = stats[endpoint]["errors"] / count
            
        return stats

# יצירת אובייקטים גלובליים לניטור
system_monitor = SystemMonitor()
api_monitor = APIMonitor() 