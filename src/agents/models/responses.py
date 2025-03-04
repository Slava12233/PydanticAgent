"""
מודלים לתגובות מהסוכן
"""

from typing import List, Optional
from pydantic import BaseModel

class ChatResponse(BaseModel):
    """מודל לתגובת הצ'אט המובנית"""
    text: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None

class TaskIdentification(BaseModel):
    """מודל לזיהוי סוג המשימה"""
    task_type: str
    specific_intent: str
    confidence_score: float

class AgentContext(BaseModel):
    """מודל להקשר השיחה"""
    conversation_id: str
    user_id: str
    last_message_timestamp: Optional[str] = None
    current_task_type: Optional[str] = None
    current_intent: Optional[str] = None
    metadata: Optional[dict] = None 