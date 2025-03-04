"""
מודול למדידת ביצועים וניטור המערכת.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """נקודת מדידה של מטריקה"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """אוסף ומנהל מטריקות ביצועים"""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        הוספת נקודת מדידה למטריקה.
        
        Args:
            name: שם המטריקה
            value: ערך המדידה
            labels: תוויות נוספות למטריקה
        """
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(point)
        logger.debug(f"Recorded metric {name}: {value} with labels {labels}")

    def start_timer(self, name: str):
        """
        התחלת מדידת זמן לפעולה.
        
        Args:
            name: שם הפעולה
        """
        self.start_times[name] = time.time()

    def stop_timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        סיום מדידת זמן לפעולה ושמירת התוצאה.
        
        Args:
            name: שם הפעולה
            labels: תוויות נוספות למטריקה
        """
        if name in self.start_times:
            duration = time.time() - self.start_times[name]
            self.record_metric(f"{name}_duration", duration, labels)
            del self.start_times[name]

    def get_metrics(self, name: str, start_time: Optional[datetime] = None) -> List[MetricPoint]:
        """
        קבלת נקודות מדידה למטריקה.
        
        Args:
            name: שם המטריקה
            start_time: זמן התחלה לסינון (אופציונלי)
            
        Returns:
            רשימת נקודות מדידה
        """
        points = self.metrics.get(name, [])
        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        return points

    def get_average(self, name: str, start_time: Optional[datetime] = None) -> float:
        """
        חישוב ממוצע למטריקה.
        
        Args:
            name: שם המטריקה
            start_time: זמן התחלה לסינון (אופציונלי)
            
        Returns:
            ערך ממוצע
        """
        points = self.get_metrics(name, start_time)
        if not points:
            return 0.0
        return sum(p.value for p in points) / len(points)

    def get_percentile(self, name: str, percentile: float, start_time: Optional[datetime] = None) -> float:
        """
        חישוב אחוזון למטריקה.
        
        Args:
            name: שם המטריקה
            percentile: אחוזון (0-100)
            start_time: זמן התחלה לסינון (אופציונלי)
            
        Returns:
            ערך האחוזון
        """
        points = self.get_metrics(name, start_time)
        if not points:
            return 0.0
        sorted_values = sorted(p.value for p in points)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[index]

    def get_summary(self, start_time: Optional[datetime] = None) -> Dict[str, Dict[str, float]]:
        """
        קבלת סיכום סטטיסטי לכל המטריקות.
        
        Args:
            start_time: זמן התחלה לסינון (אופציונלי)
            
        Returns:
            מילון עם סיכום לכל מטריקה
        """
        summary = {}
        for name in self.metrics:
            points = self.get_metrics(name, start_time)
            if points:
                values = [p.value for p in points]
                summary[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self.get_percentile(name, 50, start_time),
                    "p90": self.get_percentile(name, 90, start_time),
                    "p95": self.get_percentile(name, 95, start_time),
                    "p99": self.get_percentile(name, 99, start_time)
                }
        return summary

# יצירת אובייקט גלובלי לאיסוף מטריקות
metrics = MetricsCollector() 