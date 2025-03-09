"""
מודלים לזיהוי משימות
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class TaskIdentification(BaseModel):
    """מודל לתוצאות זיהוי משימה"""
    task_type: str
    confidence: float
    params: Dict[str, Any] = {}
    context: Optional[str] = None

class IntentRecognitionResult(BaseModel):
    """מודל לתוצאות זיהוי כוונה"""
    intent_type: str
    confidence: float
    params: Dict[str, Any] = {}
    source: str = "general"
    
class TaskContext(BaseModel):
    """מודל להקשר המשימה"""
    previous_tasks: List[TaskIdentification] = []
    conversation_history: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = {}
    session_data: Dict[str, Any] = {} 