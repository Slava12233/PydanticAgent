"""
מודול להתראות וניטור המערכת.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """רמות חומרה להתראות"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """התראת מערכת"""
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_message: Optional[str] = None

class AlertRule:
    """כלל להפקת התראות"""
    
    def __init__(self, name: str, check_func: Callable[[], bool], 
                 message: str, severity: AlertSeverity = AlertSeverity.WARNING,
                 cooldown: Optional[timedelta] = None):
        self.name = name
        self.check_func = check_func
        self.message = message
        self.severity = severity
        self.cooldown = cooldown
        self.last_alert: Optional[datetime] = None

    def should_alert(self) -> bool:
        """בדיקה האם צריך להפיק התראה"""
        if self.cooldown and self.last_alert:
            if datetime.now() - self.last_alert < self.cooldown:
                return False
        return self.check_func()

class AlertManager:
    """מנהל התראות המערכת"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self.handlers: Dict[AlertSeverity, List[Callable[[Alert], None]]] = {
            severity: [] for severity in AlertSeverity
        }

    def add_rule(self, rule: AlertRule):
        """
        הוספת כלל התראה.
        
        Args:
            rule: כלל ההתראה להוספה
        """
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def add_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]):
        """
        הוספת מטפל להתראות.
        
        Args:
            severity: רמת החומרה לטיפול
            handler: פונקציית הטיפול
        """
        self.handlers[severity].append(handler)
        logger.info(f"Added alert handler for severity {severity.value}")

    def check_rules(self):
        """בדיקת כל כללי ההתראה"""
        for rule in self.rules.values():
            if rule.should_alert():
                alert = Alert(
                    severity=rule.severity,
                    message=rule.message
                )
                self.handle_alert(alert)
                rule.last_alert = datetime.now()

    def handle_alert(self, alert: Alert):
        """
        טיפול בהתראה.
        
        Args:
            alert: ההתראה לטיפול
        """
        self.alerts.append(alert)
        logger.warning(f"New alert: [{alert.severity.value}] {alert.message}")
        
        # הפעלת כל המטפלים המתאימים
        for handler in self.handlers[alert.severity]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def resolve_alert(self, alert: Alert, resolution_message: Optional[str] = None):
        """
        סימון התראה כפתורה.
        
        Args:
            alert: ההתראה לסימון
            resolution_message: הודעת פתרון (אופציונלי)
        """
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.resolution_message = resolution_message
        logger.info(f"Resolved alert: [{alert.severity.value}] {alert.message}")

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        קבלת התראות פעילות.
        
        Args:
            severity: סינון לפי רמת חומרה (אופציונלי)
            
        Returns:
            רשימת התראות פעילות
        """
        alerts = [a for a in self.alerts if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alerts_history(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        קבלת היסטוריית התראות.
        
        Args:
            start_time: זמן התחלה (אופציונלי)
            end_time: זמן סיום (אופציונלי)
            severity: סינון לפי רמת חומרה (אופציונלי)
            
        Returns:
            רשימת התראות
        """
        alerts = self.alerts[:]
        
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        if end_time:
            alerts = [a for a in alerts if a.timestamp <= end_time]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
            
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

# יצירת אובייקט גלובלי לניהול התראות
alert_manager = AlertManager() 