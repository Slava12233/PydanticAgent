"""
מודולים של מודלים לזיהוי משימות
"""
import enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class IntentType(enum.Enum):
    """סוגי כוונות במערכת"""
    GENERAL = "general"
    PRODUCT = "product"
    ORDER = "order"
    CUSTOMER = "customer"

class TaskParameters:
    """פרמטרים של משימה"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

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
    """הקשר למשימה"""
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    language: str = "he"
