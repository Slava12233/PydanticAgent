"""
מודול לניהול הקשר שיחה
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Message:
    """מחלקה לייצוג הודעה בשיחה"""
    role: str
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class ConversationContext:
    """מחלקה לניהול הקשר שיחה"""
    
    def __init__(self):
        """אתחול הקשר שיחה"""
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """הוספת הודעה להקשר"""
        self.messages.append(Message(role=role, content=content))
    
    def get_last_messages(self, count: int) -> List[Message]:
        """קבלת ההודעות האחרונות"""
        return self.messages[-count:] if count > 0 else []
    
    def clear(self):
        """ניקוי הקשר השיחה"""
        self.messages.clear()
        self.metadata.clear()

def understand_context(message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """הבנת הקשר מהודעה והיסטוריה"""
    context = {
        "intent": None,
        "entities": [],
        "sentiment": "neutral",
        "is_question": "?" in message,
        "history_length": len(history)
    }
    return context

def resolve_pronouns(message: str, history: List[Dict[str, str]]) -> str:
    """פתרון כינויי גוף בהודעה"""
    return message

def extract_context_from_history(history: List[Dict[str, str]]) -> Dict[str, Any]:
    """חילוץ הקשר מהיסטוריית שיחה"""
    context = {
        "topics": [],
        "entities": [],
        "last_intent": None,
        "message_count": len(history)
    }
    return context

__all__ = [
    'Message',
    'ConversationContext',
    'understand_context',
    'resolve_pronouns',
    'extract_context_from_history'
] 